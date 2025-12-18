import sys

sys.path.append("/www/alpha/")

import json
import copy
import asyncio
import hashlib
import traceback

from uuid import uuid4
from datetime import datetime, timezone
from bson.objectid import ObjectId
from typing import Any, Dict, List, Union, Optional

from apps.rubicon_v3.__function.__encryption_utils import (
    retry_function,
    recursive_encrypt_strings,
)
from apps.rubicon_v3.__function.__rubicon_log import (
    sanitize_for_mongo,
    check_log_exists,
)
from apps.rubicon_v3.__external_api._11_user_info import IndivInfo, getGuid
from apps.rubicon_v3.__external_api._14_azure_email_alert import (
    send_process_error_alert,
)
from apps.rubicon_v3.__external_api.__dkms_encode import DKMS_Encoder

from alpha.settings import VITE_OP_TYPE, VITE_COUNTRY
from alpha._db import search_log_collection

dkms_encoder = DKMS_Encoder()


def create_search_log(
    form_data: Dict[str, Any],
    object_id: ObjectId,
    error: Optional[Union[str, Dict[str, Any]]] = None,
) -> None:
    """
    Create a search log in the search_log_collection.

    Args:
        form_data (dict): The form data containing search details.
        object_id (ObjectId): MongoDB Object ID.
        error (Optional[Union[str, Dict[str, Any]]]): Error information as a string or dictionary. Defaults to None.
    """
    print("create_search_log")
    channel = None
    country_code = None
    user_id = None
    message_id = None
    query = None

    try:
        # Extract data from form_data
        message_id = form_data.get("messageId")
        params = form_data.get("params", {})
        lng = None
        sa_id = None
        gu_id = "default_gu_id"
        department = None
        if isinstance(params, dict):
            channel = params.get("channel")
            country_code = params.get("countryCode")
            lng = params.get("lng")
            user_id = params.get("userId")
            query = params.get("message")
            sa_id = params.get("saId")
            department = params.get("department")

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
        existing_log = check_log_exists(search_log_collection, message_id)
        if existing_log:
            message_id = str(message_id) + "__dup__" + str(uuid4())

        # Encode the sensitive data using DKMS
        encrypted_user_id = None
        if user_id is not None:
            encrypted_user_id = retry_function(
                dkms_encoder.getEncryptedValue, json.dumps(user_id)
            )
            # Update the user_id in the form_data
            if isinstance(form_data.get("params"), dict):
                form_data["params"]["userId"] = encrypted_user_id
            else:
                form_data["params"] = {"userId": encrypted_user_id}

        encrypted_query = None
        if query is not None:
            encrypted_query = retry_function(
                dkms_encoder.getEncryptedValue, json.dumps(query)
            )
            # Update the query in the form_data
            if isinstance(form_data.get("params"), dict):
                form_data["params"]["message"] = encrypted_query
            else:
                form_data["params"] = {"message": encrypted_query}

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
        if isinstance(form_data.get("params"), dict):
            form_data["params"]["guId"] = gu_id
        else:
            form_data["params"] = {"guId": gu_id}

        # Generate the user hash
        user_hash = None
        if user_id is not None:
            user_hash = hashlib.sha256(str(user_id).encode("utf-8")).hexdigest()

        # Log the entire form data to maintain context
        input_dict = copy.deepcopy(form_data)

        # Log the error and initialize message status
        message_status = {
            "is_hidden": False,
            "hidden_on": None,
            "completed": False,
            "error": encrypted_error,
        }

        # Set up the initial message log structure
        search_init_log = {
            "_id": object_id,
            "channel": channel,
            "country_code": country_code,
            "language_code": lng,
            "user_id": encrypted_user_id,
            "user_hash": user_hash,
            "department": department,
            "subsidiary": None,
            "message_id": message_id,
            "message": encrypted_query,
            "log": {},
            "appraisal": {},
            "dashboard_log": {},
            "supplementary_log": {},
            "product_log": [],
            "timing_log": [],
            "input_log": input_dict,
            "message_status": message_status,
            "elapsed_time": 0,
            "created_on": datetime.now(timezone.utc),
        }

        # Sanitize the search log for MongoDB
        search_init_log = sanitize_for_mongo(search_init_log)

        # Insert using upsert for idempotency
        result = search_log_collection.update_one(
            {"_id": object_id}, {"$setOnInsert": search_init_log}, upsert=True
        )

        if result.matched_count > 0:
            print(f"Search log with _id {object_id} already exists (retry scenario)")
        else:
            print(f"Search log with _id {object_id} created successfully")
    except Exception as e:
        print(f"Error creating search log: {e}")

        # Alert the error
        if VITE_OP_TYPE in ["STG", "PRD"]:
            context_data = {
                "Module": "create_search_log",
                "Channel": channel,
                "Country Code": country_code,
                "Object ID": str(object_id),
                "User ID": user_id,
                "Message ID": message_id,
                "Original Query": query,
            }
            send_process_error_alert(
                str(e),
                "process_error",
                error_traceback=traceback.format_exc(),
                context_data=context_data,
            )


def update_search_log(
    object_id: ObjectId,
    message_id: str,
    response_log: dict,
    dashboard_log: dict,
    product_log: List[dict],
    timing_log: List[dict],
    elapsed_time: float,
    subsidiary: str,
) -> None:
    """
    Update the search log with the response, dashboard, product, and timing logs.

    Args:
        object_id (ObjectId): MongoDB Object ID.
        message_id (str): Message ID to update.
        response_log (dict): Updated response log.
        dashboard_log (dict): Updated dashboard log.
        product_log (List[dict]): Updated product log.
        timing_log (List[dict]): Updated timing log.
        elapsed_time (float): Elapsed time.
        subsidiary (str): Subsidiary information.
    """
    print("update_search_log")

    try:
        # Sanitize all inputs for MongoDB
        response_log = sanitize_for_mongo(response_log)
        dashboard_log = sanitize_for_mongo(dashboard_log)
        product_log = [sanitize_for_mongo(product) for product in product_log]
        timing_log = [sanitize_for_mongo(timing) for timing in timing_log]

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
        if elapsed_time is not None:
            set_operations["elapsed_time"] = elapsed_time
        if subsidiary:
            set_operations["subsidiary"] = subsidiary

        # Update the completed status
        set_operations["message_status.completed"] = True

        update_operations = {}
        # Only add $set if there are operations to perform
        if set_operations:
            update_operations["$set"] = set_operations

        # Update the search log in the collection
        search_log_collection.update_one({"_id": object_id}, update_operations)
    except Exception as e:
        print(f"Error updating search log: {e}")

        # Alert the error
        if VITE_OP_TYPE in ["STG", "PRD"]:
            context_data = {
                "Module": "update_search_log",
                "Object ID": str(object_id),
                "Message ID": message_id,
            }
            send_process_error_alert(
                str(e),
                "process_error",
                error_traceback=traceback.format_exc(),
                context_data=context_data,
            )


def update_search_log_by_field(
    message_id: str,
    field: str,
    data,
) -> None:
    """
    Update a specific field in the search log by message_id.

    Args:
        message_id (str): Message ID to update.
        field (str): The field to update.
        data: The data to set for the field.
    """
    print("update_search_log_by_field")

    try:
        # Sanitize the data for MongoDB
        sanitized_data = sanitize_for_mongo(data)

        search_log_collection.update_one(
            {"message_id": message_id}, {"$set": {field: sanitized_data}}
        )
    except Exception as e:
        print(f"Error updating search log by field: {e}")

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
