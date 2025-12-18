import sys

sys.path.append("/www/alpha/")

import math
import json
import copy
import time
import asyncio
import hashlib
import traceback
import numpy as np
import pandas as pd

from uuid import UUID, uuid4
from datetime import datetime, timezone, date
from datetime import time as datetime_time
from decimal import Decimal
from bson.objectid import ObjectId
from typing import Any, Dict, List, Union, Optional

from apps.rubicon_v3.__function.__encryption_utils import (
    retry_function,
    recursive_encrypt_strings,
)
from apps.rubicon_v3.__api._02_log_check import sanitize_for_json
from apps.rubicon_v3.__external_api._11_user_info import IndivInfo, getGuid
from apps.rubicon_v3.__external_api._14_azure_email_alert import (
    send_process_error_alert,
)
from apps.rubicon_v3.__external_api.__dkms_encode import DKMS_Encoder

from alpha.settings import VITE_OP_TYPE, VITE_COUNTRY
from alpha._db import (
    chat_log_collection,
    debug_log_collection,
    appraisal_log_collection,
    action_log_collection,
)

dkms_encoder = DKMS_Encoder()


def sanitize_for_mongo(obj: Any) -> Any:
    """
    Recursively convert objects to MongoDB-compatible formats.

    This function handles:
    - datetime.date -> datetime.datetime
    - Decimal -> float
    - sets -> lists
    - custom objects with __dict__ -> dict
    - UUID -> str
    - pandas DataFrame -> markdown
    - NaN values -> None
    - Large integers -> str (if exceeding 64-bit range)
    - Non-serializable types -> str representation

    Args:
        obj: Any Python object to sanitize

    Returns:
        MongoDB-compatible version of the object
    """
    # Handle None
    if obj is None:
        return None

    # Handle NaN values - both Python float NaN and numpy NaN
    if isinstance(obj, float) and math.isnan(obj):
        return None
    if isinstance(obj, np.number) and np.isnan(obj):
        return None

    # Handle datetime.date but not datetime.datetime
    if isinstance(obj, date) and not isinstance(obj, datetime):
        return datetime.combine(obj, datetime_time.min).replace(tzinfo=timezone.utc)

    # Handle Decimal
    if isinstance(obj, Decimal):
        return float(obj)

    # Handle sets
    if isinstance(obj, set):
        return list(obj)

    # Handle UUIDs
    if isinstance(obj, UUID):
        return str(obj)

    # Handle ObjectId - keep as ObjectId (MongoDB native type)
    if isinstance(obj, ObjectId):
        return obj

    # Handle large integers (beyond 64-bit signed integer range)
    if isinstance(obj, int):
        # MongoDB's integer range: -2^63 to 2^63-1
        if obj < -9223372036854775808 or obj > 9223372036854775807:
            return str(obj)  # Convert to string if too large
        return obj

    # Handle dictionaries - recursively sanitize each value
    if isinstance(obj, dict):
        return {k: sanitize_for_mongo(v) for k, v in obj.items()}

    # Handle lists/tuples - recursively sanitize each item
    if isinstance(obj, (list, tuple)):
        return [sanitize_for_mongo(item) for item in obj]

    # Handle pandas DataFrame
    if isinstance(obj, pd.DataFrame):
        return obj.to_markdown()

    # Handle pandas Series
    if isinstance(obj, pd.Series):
        return sanitize_for_mongo(obj.to_dict())

    # Handle numpy arrays
    if isinstance(obj, np.ndarray):
        return sanitize_for_mongo(obj.tolist())
    if isinstance(
        obj,
        (
            np.int_,
            np.intc,
            np.intp,
            np.int8,
            np.int16,
            np.int32,
            np.int64,
            np.uint8,
            np.uint16,
            np.uint32,
            np.uint64,
        ),
    ):
        # Convert numpy integer to Python int, then check range
        int_val = int(obj)
        if int_val < -9223372036854775808 or int_val > 9223372036854775807:
            return str(int_val)
        return int_val
    if isinstance(obj, (np.float_, np.float16, np.float32, np.float64)):
        return float(obj)
    if isinstance(obj, (np.bool_)):
        return bool(obj)

    # Handle custom objects with __dict__
    if hasattr(obj, "__dict__") and not isinstance(obj, type):
        return sanitize_for_mongo(obj.__dict__)

    # Check if object is a basic type that MongoDB can handle
    if isinstance(obj, (str, float, bool)):
        return obj

    # Pass datetime.datetime as is
    if isinstance(obj, datetime):
        return obj

    # For any other types, convert to string
    try:
        return str(obj)
    except Exception:
        return f"Unconvertible object: {type(obj).__name__}"


def check_log_exists(collection, message_id: str):
    """
    Check if a log with the given message_id exists in the collection.

    Args:
        collection: MongoDB collection to check
        message_id (str): Message ID to look up

    Returns:
        dict or None: The existing log document if found, None otherwise
    """
    existing_log = collection.find_one({"message_id": message_id})

    return existing_log


def create_message_log(
    form_data: Dict[str, Any],
    object_id: ObjectId,
    error: Optional[Union[str, Dict[str, Any]]] = None,
) -> None:
    """
    Create a message log in the chat_log_collection.

    Args:
        form_data (dict): The form data containing message details.
        object_id (ObjectId): MongoDB Object ID.
        error (Optional[Union[str, Dict[str, Any]]]): Error information as a string or dictionary. Defaults to None.
    """
    print("create_message_log")
    channel = None
    country_code = None
    user_id = None
    session_id = None
    message_id = None
    query = None

    try:
        # Extract data from form_data
        channel = form_data.get("channel")
        meta = form_data.get("meta")
        user_id = form_data.get("userId")
        session_id = form_data.get("sessionId")
        message_history = form_data.get("messageHistory")
        message = form_data.get("message")
        lng = form_data.get("lng")
        gu_id = "default_gu_id"  # Currently not supported
        sa_id = form_data.get("saId")

        # Set the guId to default value as it is not supported currently
        form_data["guId"] = gu_id

        # Get other metadata for logging
        country_code = None
        if isinstance(meta, dict):
            country_code = meta.get("countryCode")
        department = form_data.get("department")
        message_id = None
        query = None
        if isinstance(message, list):
            message_id = str(
                next(
                    (
                        item
                        for item in message
                        if isinstance(item, dict) and item.get("type") == "text"
                    ),
                    {},  # Default value if no matching item found
                ).get("messageId")
            )
            query = str(
                next(
                    (
                        item
                        for item in message
                        if isinstance(item, dict) and item.get("type") == "text"
                    ),
                    {},  # Default value if no matching item found
                ).get("content")
            )

        # Get the user data
        user_data_gu_id = None
        if sa_id and channel:
            indiv_class = IndivInfo(
                "KR" if VITE_COUNTRY == "KR" else "GB", sa_id, gu_id, channel
            )
            user_data = asyncio.run(indiv_class.getUserInfo())
            # Get the gu_id from the user data
            user_data_gu_id = getGuid(user_data)
        # If gu_id from the user data exists and is different from the provided gu_id, use it
        if (
            user_data_gu_id
            and isinstance(user_data_gu_id, str)
            and user_data_gu_id != gu_id
        ):
            gu_id = user_data_gu_id

        # Check if the log already exists
        existing_log = check_log_exists(chat_log_collection, message_id)
        if existing_log:
            message_id = str(message_id) + "__dup__" + str(uuid4())

        # Encode the sensitive data using DKMS
        encrypted_user_id = None
        if user_id is not None:
            encrypted_user_id = retry_function(
                dkms_encoder.getEncryptedValue, json.dumps(user_id)
            )
            # Update the user_id in the form_data
            form_data["userId"] = encrypted_user_id

        encrypted_message_history = None
        if message_history is not None:
            encrypted_message_history = retry_function(
                dkms_encoder.getEncryptedValue, json.dumps(message_history)
            )
            # Update the message_history in the form_data
            form_data["messageHistory"] = encrypted_message_history

        encrypted_message = None
        if message is not None:
            encrypted_message = retry_function(
                dkms_encoder.getEncryptedValue, json.dumps(message)
            )
            # Update the message in the form_data
            form_data["message"] = encrypted_message

        encrypted_query = None
        if query is not None:
            encrypted_query = retry_function(
                dkms_encoder.getEncryptedValue, json.dumps(query)
            )
            # No need to update the query as the whole message is encrypted

        encrypted_error = None
        if error is not None:
            encrypted_error = retry_function(
                dkms_encoder.getEncryptedValue, json.dumps(error)
            )

        # Make sure gu_id value is decrypted if it is encrypted
        if (
            gu_id
            and isinstance(gu_id, str)
            and retry_function(dkms_encoder.isEncrypted, gu_id)
        ):
            # Decrypt the gu_id using DKMS encoder
            gu_id = retry_function(dkms_encoder.getDecryptedValue, gu_id)

        # Update the gu_id in the form_data
        form_data["guId"] = gu_id

        # Generate the user hash
        user_hash = None
        if user_id is not None:
            user_hash = hashlib.sha256(str(user_id).encode("utf-8")).hexdigest()

        # Log the entire form data to maintain context
        input_dict = copy.deepcopy(form_data)

        # Log the error and initialize message status
        message_status = {
            "multi_input": False,
            "is_hidden": False,
            "hidden_on": None,
            "completed": False,
            "error": encrypted_error,
        }

        # Set up the initial message log structure
        message_init_log = {
            "_id": object_id,
            "channel": channel,
            "country_code": country_code,
            "language_code": lng,
            "user_id": encrypted_user_id,
            "user_hash": user_hash,
            "department": department,
            "subsidiary": None,
            "session_id": session_id,
            "message_id": message_id,
            "message": encrypted_query,
            "session_title": None,
            "log": {},
            "appraisal": {},
            "dashboard_log": {},
            "supplementary_log": {},
            "product_log": [],
            "timing_log": [],
            "input_log": input_dict,
            "message_status": message_status,
            "continuation_log": {},
            "elapsed_time": 0,
            "created_on": datetime.now(timezone.utc),
        }

        # Sanitize the message_init_log for MongoDB
        message_init_log = sanitize_for_mongo(message_init_log)

        # Insert using upsert for idempotency
        result = chat_log_collection.update_one(
            {"_id": object_id}, {"$setOnInsert": message_init_log}, upsert=True
        )

        if result.matched_count > 0:
            print(f"Chat log with _id {object_id} already exists (retry scenario)")
        else:
            print(f"Chat log with _id {object_id} created successfully")
    except Exception as e:
        print(f"Error creating message log: {e}")

        # Alert the error
        if VITE_OP_TYPE in ["STG", "PRD"]:
            context_data = {
                "Module": "create_message_log",
                "Channel": channel,
                "Country Code": country_code,
                "Object ID": str(object_id),
                "User ID": user_id,
                "Session ID": session_id,
                "Message ID": message_id,
                "Original Query": query,
            }
            send_process_error_alert(
                str(e),
                "process_error",
                error_traceback=traceback.format_exc(),
                context_data=context_data,
            )


def update_message_log(
    object_id: ObjectId,
    message_id: str,
    response_log: dict,
    dashboard_log: dict,
    product_log: list,
    timing_log: list,
    elapsed_time: float,
    session_title: str,
    subsidiary: str,
    continuation_log: dict,
) -> None:
    """
    Update the message log in the chat_log_collection.

    Args:
        object_id (ObjectId): MongoDB Object ID.
        message_id (str): Message ID to update.
        response_log (dict): Updated response log.
        dashboard_log (dict): Updated dashboard log.
        product_log (list): Updated product log.
        timing_log (list): Updated timing log.
        elapsed_time (float): Elapsed time.
        session_title (str): Session title.
    """
    print("update_message_log")

    try:
        # Sanitize all inputs for MongoDB
        response_log = sanitize_for_mongo(response_log)
        dashboard_log = sanitize_for_mongo(dashboard_log)
        product_log = sanitize_for_mongo(product_log)
        timing_log = sanitize_for_mongo(timing_log)
        continuation_log = sanitize_for_mongo(continuation_log)

        # Remove the query from the product_log
        cleaned_product_log = []
        for item in product_log:
            cleaned_product_log.append({k: v for k, v in item.items() if k != "query"})

        # Encrypt sensitive data using DKMS
        encrypted_response_log = recursive_encrypt_strings(response_log)

        # Combine all $set operations
        set_operations = {}
        if encrypted_response_log:
            set_operations["log"] = encrypted_response_log
        if dashboard_log:
            set_operations["dashboard_log"] = dashboard_log
        if cleaned_product_log:
            set_operations["product_log"] = cleaned_product_log
        if timing_log:
            set_operations["timing_log"] = timing_log
        if elapsed_time:
            set_operations["elapsed_time"] = elapsed_time
        if session_title:
            set_operations["session_title"] = session_title
        if subsidiary:
            set_operations["subsidiary"] = subsidiary
        if continuation_log:
            set_operations["continuation_log"] = continuation_log

        # Update the completed status
        set_operations["message_status.completed"] = True

        update_operations = {}
        # Only add $set if there are operations to perform
        if set_operations:
            update_operations["$set"] = set_operations

        chat_log_collection.update_one({"_id": object_id}, update_operations)
    except Exception as e:
        print(f"Error updating log: {e}")

        # Alert the error
        if VITE_OP_TYPE in ["STG", "PRD"]:
            context_data = {
                "Module": "update_message_log",
                "Object ID": str(object_id),
                "Message ID": message_id,
            }
            send_process_error_alert(
                str(e),
                "process_error",
                error_traceback=traceback.format_exc(),
                context_data=context_data,
            )


def update_message_log_by_field(
    message_id: str,
    field: str,
    data,
) -> None:
    """
    Update a specific field in the chat log by message_id.

    Args:
        message_id (str): Message ID.
        field (str): Field to update.
        data: Data to update.
    """
    print("update_message_log_by_field")

    try:
        # Sanitize the data for MongoDB
        sanitized_data = sanitize_for_mongo(data)

        chat_log_collection.update_one(
            {"message_id": message_id},
            {"$set": {field: sanitized_data}},
        )
    except Exception as e:
        print(f"Error updating log: {e}")

        # Alert the error
        if VITE_OP_TYPE in ["STG", "PRD"]:
            context_data = {
                "Module": "update_message_log_by_field",
                "Message ID": message_id,
            }
            send_process_error_alert(
                str(e),
                "process_error",
                error_traceback=traceback.format_exc(),
                context_data=context_data,
            )


def update_message_log_multi_input(
    object_id: ObjectId, multi_input_message_ids: List[str]
) -> None:
    """
    Update the chat log for multiple input messages.
    Args:
        object_id (ObjectId): MongoDB Object ID.
        multi_input_message_ids (list): List of multi-input message IDs.
    """
    print("update_message_log_multi_input")

    try:
        for message_id in multi_input_message_ids:
            update_message_log_by_field(
                message_id=message_id,
                field="message_status.multi_input",
                data=True,
            )
    except Exception as e:
        print(f"Error updating multi-input log: {e}")

        # Alert the error
        if VITE_OP_TYPE in ["STG", "PRD"]:
            context_data = {
                "Module": "update_message_log_multi_input",
                "Object ID": str(object_id),
                "Message IDs": multi_input_message_ids,
            }
            send_process_error_alert(
                str(e),
                "process_error",
                error_traceback=traceback.format_exc(),
                context_data=context_data,
            )


def create_debug_log(
    object_id: ObjectId,
    channel: str,
    country_code: str,
    language_code: str,
    user_id: str,
    department: str,
    subsidiary: str,
    session_id: str,
    message_id: str,
    message: str,
    debug_log: list,
    timing_log: list,
) -> None:
    """
    Create a debug log in the debug_log_collection.

    Args:
        object_id (ObjectId): MongoDB Object ID.
        channel (str): Channel name.
        country_code (str): Country code.
        language_code (str): Language code.
        user_id (str): User ID.
        department (str): Department name.
        session_id (str): Session ID.
        message_id (str): Message ID.
        message (str): Message content.
        debug_log (list): Debug log.
        timing_log (list): Timing log.
    """
    print("create_debug_log")

    try:
        # Check if the log already exists
        existing_log = check_log_exists(debug_log_collection, message_id)
        if existing_log:
            message_id = str(message_id) + "__dup__" + str(uuid4())

        # Sanitize all inputs for MongoDB
        sanitized_debug_log = sanitize_for_json(debug_log)
        sanitized_timing_log = sanitize_for_json(timing_log)

        # Encrypt sensitive data using DKMS
        encrypted_user_id = retry_function(dkms_encoder.getEncryptedValue, user_id)
        encrypted_message = retry_function(dkms_encoder.getEncryptedValue, message)
        encrypted_sanitized_debug_log = retry_function(
            dkms_encoder.getEncryptedValue, json.dumps(sanitized_debug_log)
        )
        encrypted_sanitized_timing_log = retry_function(
            dkms_encoder.getEncryptedValue, json.dumps(sanitized_timing_log)
        )

        debug_log_init = {
            "_id": object_id,
            "channel": channel,
            "country_code": country_code,
            "language_code": language_code,
            "user_id": encrypted_user_id,
            "user_hash": hashlib.sha256(user_id.encode("utf-8")).hexdigest(),
            "department": department,
            "subsidiary": subsidiary,
            "session_id": session_id,
            "message_id": message_id,
            "message": encrypted_message,
            "debug_log": encrypted_sanitized_debug_log,
            "timing_log": encrypted_sanitized_timing_log,
            "created_on": datetime.now(timezone.utc),
        }

        # Insert using upsert for idempotency
        result = debug_log_collection.update_one(
            {"_id": object_id}, {"$setOnInsert": debug_log_init}, upsert=True
        )

        if result.matched_count > 0:
            print(f"Debug log with _id {object_id} already exists (retry scenario)")
        else:
            print(f"Debug log with _id {object_id} created successfully")
    except Exception as e:
        print(f"Error creating debug log: {e}")

        # Alert the error
        if VITE_OP_TYPE in ["STG", "PRD"]:
            context_data = {
                "Module": "create_debug_log",
                "Channel": channel,
                "Country Code": country_code,
                "Object ID": str(object_id),
                "User ID": user_id,
                "Session ID": session_id,
                "Message ID": message_id,
            }
            send_process_error_alert(
                str(e),
                "process_error",
                error_traceback=traceback.format_exc(),
                context_data=context_data,
            )


def wait_for_document(collection, query, timeout=10, interval=0.1):
    """
    Wait for a document to appear in the collection.

    Args:
        collection: MongoDB collection
        query: Query dict to find the document
        timeout: Maximum time to wait in seconds
        interval: Time between checks in seconds

    Returns:
        dict or None: Found document or None if timeout
    """
    start_time = time.time()

    while time.time() - start_time < timeout:
        doc = collection.find_one(query)
        if doc:
            return doc
        time.sleep(interval)

    return None


def add_to_debug_log(object_id: ObjectId, debug_content: dict) -> None:
    """
    Add content to an existing debug log in the debug_log_collection.

    Args:
        object_id (ObjectId): MongoDB Object ID.
        debug_content (dict): Content to add to the debug log.
    """
    print("add_to_debug_log")

    try:
        # Wait for the document to be available
        debug_log = wait_for_document(debug_log_collection, {"_id": object_id})

        # If the document is not found, return
        if not debug_log:
            print(f"Debug log with _id {object_id} not found.")
            return

        # Sanitize the debug content for MongoDB
        sanitized_debug_content = sanitize_for_json(debug_content)

        # Get the existing debug content log
        existing_debug_log = debug_log.get("debug_log")

        # If the debug content in the log is not present, return
        if existing_debug_log is None:
            print(f"No existing debug content log found for _id {object_id}.")
            return

        # Decrypt the existing debug log
        decrypted_debug_log = retry_function(
            dkms_encoder.getDecryptedValue, existing_debug_log
        )
        # Json load the decrypted debug log
        try:
            decrypted_debug_log = json.loads(decrypted_debug_log)
        except json.JSONDecodeError:
            print(f"Decrypted debug content log for _id {object_id} is not valid JSON.")
            return

        # Make sure the decrypted debug log is a list
        if not isinstance(decrypted_debug_log, list):
            print(f"Decrypted debug content log for _id {object_id} is not a list.")
            return

        # Append the new debug content to the existing log
        decrypted_debug_log.append(sanitized_debug_content)

        # Encrypt the updated debug log
        encrypted_debug_log = retry_function(
            dkms_encoder.getEncryptedValue, json.dumps(decrypted_debug_log)
        )

        # Update the debug log in the collection
        debug_log_collection.update_one(
            {"_id": object_id},
            {"$set": {"debug_log": encrypted_debug_log}},
        )
    except Exception as e:
        print(f"Error adding to debug log: {e}")

        # Alert the error
        if VITE_OP_TYPE in ["STG", "PRD"]:
            context_data = {
                "Module": "add_to_debug_log",
                "Object ID": str(object_id),
            }
            send_process_error_alert(
                str(e),
                "process_error",
                error_traceback=traceback.format_exc(),
                context_data=context_data,
            )


def create_appraisal_log(
    form_data: Dict[str, Any],
    object_id: ObjectId,
    error: Optional[Union[str, Dict[str, Any]]] = None,
) -> None:
    """
    Create an appraisal log based on the provided form data.
    """
    print("create_appraisal_log")
    channel = None
    country_code = None
    message_id = None

    try:
        # Extract data from form_data
        channel = form_data.get("channel")
        country_code = form_data.get("countryCode")
        message_id = form_data.get("messageId")
        thumb_up = form_data.get("thumbUp")
        selected_list = form_data.get("selectedList")
        comment = form_data.get("comment")

        # Encrypt sensitive data using DKMS
        encrypted_comment = None
        if comment is not None:
            encrypted_comment = retry_function(dkms_encoder.getEncryptedValue, comment)
            # Update the comment in the form_data
            form_data["comment"] = encrypted_comment
        encrypted_error = None
        if error is not None:
            encrypted_error = retry_function(
                dkms_encoder.getEncryptedValue, json.dumps(error)
            )

        # Log the entire form data to maintain context
        input_dict = copy.deepcopy(form_data)

        # Log the error
        message_status = {"error": encrypted_error}

        # Set up the appraisal log structure
        appraisal_init_log = {
            "_id": object_id,
            "channel": channel,
            "country_code": country_code,
            "message_id": message_id,
            "thumb_up": thumb_up,
            "selected_list": selected_list,
            "comment": encrypted_comment,
            "input_log": input_dict,
            "message_status": message_status,
            "created_on": datetime.now(timezone.utc),
        }

        # Sanitize the appraisal_init_log for MongoDB
        appraisal_init_log = sanitize_for_mongo(appraisal_init_log)

        # Insert using upsert for idempotency
        result = appraisal_log_collection.update_one(
            {"_id": object_id}, {"$setOnInsert": appraisal_init_log}, upsert=True
        )

        if result.matched_count > 0:
            print(f"Appraisal log with _id {object_id} already exists (retry scenario)")
        else:
            print(f"Appraisal log with _id {object_id} created successfully")
    except Exception as e:
        print(f"Error creating appraisal log: {e}")

        # Alert the error
        if VITE_OP_TYPE in ["STG", "PRD"]:
            context_data = {
                "Module": "create_appraisal_log",
                "Channel": channel,
                "Country Code": country_code,
                "Object ID": str(object_id),
                "Message ID": message_id,
            }
            send_process_error_alert(
                str(e),
                "process_error",
                error_traceback=traceback.format_exc(),
                context_data=context_data,
            )


def create_action_log(
    data: Dict[str, Any],
    object_id: ObjectId,
    error: Optional[Union[str, Dict[str, Any]]] = None,
) -> None:
    """
    Create an action log based on the provided data.
    """
    print("create_action_log")

    try:
        action_type = data.get("actionType")
        action_info = data.get("actionInfo")

        # Get the sensitive fields from action_info
        user_id = None
        gu_id = None
        if isinstance(action_info, dict):
            user_id = action_info.get("userId")
            gu_id = action_info.get("guId")

        # Encrypt sensitive data using DKMS
        encrypted_user_id = None
        if user_id is not None:
            encrypted_user_id = retry_function(dkms_encoder.getEncryptedValue, user_id)
            # Update the user_id in the action_info
            if isinstance(action_info, dict):
                data["actionInfo"]["userId"] = encrypted_user_id

        encrypted_error = None
        if error is not None:
            encrypted_error = retry_function(
                dkms_encoder.getEncryptedValue, json.dumps(error)
            )

        # Decrypt gu_id if it is encrypted
        if (
            gu_id
            and isinstance(gu_id, str)
            and retry_function(dkms_encoder.isEncrypted, gu_id)
        ):
            decrypted_gu_id = retry_function(dkms_encoder.getDecryptedValue, gu_id)
            # Update the gu_id in the action_info
            if isinstance(action_info, dict):
                data["actionInfo"]["guId"] = decrypted_gu_id

        # Log the entire data to maintain context
        input_dict = copy.deepcopy(data)

        # Log the error
        message_status = {"error": encrypted_error}

        # Set up the action log structure
        action_init_log = {
            "_id": object_id,
            "action_type": action_type,
            "action_info": action_info,
            "input_log": input_dict,
            "message_status": message_status,
            "created_on": datetime.now(timezone.utc),
        }

        # Sanitize the action_init_log for MongoDB
        action_init_log = sanitize_for_mongo(action_init_log)

        # #Insert using upsert for idempotency
        result = action_log_collection.update_one(
            {"_id": object_id}, {"$setOnInsert": action_init_log}, upsert=True
        )

        if result.matched_count > 0:
            print(f"Action log with _id {object_id} already exists (retry scenario)")
        else:
            print(f"Action log with _id {object_id} created successfully")
    except Exception as e:
        print(f"Error creating action log: {e}")

        # Alert the error
        if VITE_OP_TYPE in ["STG", "PRD"]:
            context_data = {
                "Module": "create_action_log",
                "Action Type": action_type,
                "Object ID": str(object_id),
            }
            send_process_error_alert(
                str(e),
                "process_error",
                error_traceback=traceback.format_exc(),
                context_data=context_data,
            )
