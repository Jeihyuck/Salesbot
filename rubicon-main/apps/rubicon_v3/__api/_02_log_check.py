import sys

sys.path.append("/www/alpha/")
import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "alpha.settings")
django.setup()

import time
import uuid
import math
import subprocess
import asyncio
import numpy as np
import pandas as pd

from decimal import Decimal
from typing import Any, Dict
from bson.objectid import ObjectId
from datetime import datetime, date
from dataclasses import dataclass

from apps.rubicon_v3.__function.__encryption_utils import recursive_decrypt_strings
from apps.rubicon_v3.__function.__utils import parse_timing_logs

from alpha._db import debug_log_collection, chat_log_collection, search_log_collection


class LogCheck:
    @dataclass
    class LogCheckParams:
        lookup_id: str

    def __init__(self, input_params: LogCheckParams):
        self.input_params = input_params

    def convert_to_markdown_table(self, timing_logs):
        table = "| Process | Elapsed Time |\n"
        table += "|:--------|-----:|\n"
        for item in timing_logs:
            table += f"| {item['process']} | {item['time']} |\n"
        return table

    def get_last_commit_info(self):
        # Get the last commit hash
        commit_hash = (
            subprocess.check_output(["git", "rev-parse", "HEAD"])
            .strip()
            .decode("utf-8")
        )

        # Get the last commit date
        commit_date = (
            subprocess.check_output(["git", "log", "-1", "--format=%cd"])
            .strip()
            .decode("utf-8")
        )

        # Get the last commit message
        commit_message = (
            subprocess.check_output(["git", "log", "-1", "--format=%B"])
            .strip()
            .decode("utf-8")
        )

        # Get the current branch name
        branch_name = (
            subprocess.check_output(["git", "rev-parse", "--abbrev-ref", "HEAD"])
            .strip()
            .decode("utf-8")
        )

        status = (
            subprocess.check_output(["git", "status"])
            .strip()
            .decode("utf-8")
            .split("\n")
        )

        return commit_hash, commit_date, commit_message, branch_name, status

    def get_markdown_timing_logs(self, timing_logs):
        timing_logs_dict_list = []
        for item in timing_logs:
            time_value = item[1]

            if time_value is None:
                formatted_time = "None"
            elif isinstance(time_value, (int, float)):
                # For numeric values, round and add "Sec"
                formatted_time = str(round(time_value, 4)) + " Sec"
            else:
                # For strings (like datetime), use as is
                formatted_time = str(time_value)

            timing_logs_dict_list.append({"process": item[0], "time": formatted_time})
        return self.convert_to_markdown_table(timing_logs_dict_list)

    def get_debug_log_sync(self):
        """
        Get debug log synchronously - just the database queries, no timeout here.
        """
        # First try to find by message_id (string search)
        doc = debug_log_collection.find_one({"message_id": self.input_params.lookup_id})

        # If not found and lookup_id is a valid ObjectId, try searching by _id
        if not doc and ObjectId.is_valid(self.input_params.lookup_id):
            doc = debug_log_collection.find_one(
                {"_id": ObjectId(self.input_params.lookup_id)}
            )

        if not doc:
            return {}

        decrypted_doc = recursive_decrypt_strings(doc)
        return sanitize_for_json(decrypted_doc)

    def get_chat_or_search_sync(self):
        """
        Sequential chat/search with early exit - just the database queries, no timeout here.
        Since chat and search are mutually exclusive, return as soon as we find one.
        """
        # Try chat first
        doc = chat_log_collection.find_one({"message_id": self.input_params.lookup_id})

        # If not found and lookup_id is a valid ObjectId, try searching by _id
        if not doc and ObjectId.is_valid(self.input_params.lookup_id):
            doc = chat_log_collection.find_one(
                {"_id": ObjectId(self.input_params.lookup_id)}
            )

        if doc:
            # Found chat log, return it and empty search log
            decrypted_doc = recursive_decrypt_strings(doc)
            chat_log = sanitize_for_json(decrypted_doc)
            return chat_log, {}

        # Chat not found, try search
        doc = search_log_collection.find_one(
            {"message_id": self.input_params.lookup_id}
        )

        if not doc and ObjectId.is_valid(self.input_params.lookup_id):
            doc = search_log_collection.find_one(
                {"_id": ObjectId(self.input_params.lookup_id)}
            )

        if doc:
            # Found search log
            decrypted_doc = recursive_decrypt_strings(doc)
            search_log = sanitize_for_json(decrypted_doc)
            return {}, search_log

        # Neither chat nor search found
        return {}, {}

    async def get_logs_parallel_with_timeout(self):
        """
        Run debug and chat/search functions in parallel, each with their own timeout.
        The timeout wraps the entire function execution, not individual database calls.
        """
        loop = asyncio.get_event_loop()

        # Create tasks for both functions
        debug_task = loop.run_in_executor(None, self.get_debug_log_sync)
        chat_search_task = loop.run_in_executor(None, self.get_chat_or_search_sync)

        # Apply timeout to each function execution
        try:
            debug_log = await asyncio.wait_for(
                debug_task, timeout=1.0
            )  # 1 second timeout for debug function
        except (asyncio.TimeoutError, Exception):
            debug_log = {}

        try:
            chat_log, search_log = await asyncio.wait_for(
                chat_search_task, timeout=1.0
            )  # 1 second timeout for chat/search function
        except (asyncio.TimeoutError, Exception):
            chat_log, search_log = {}, {}

        return self._process_results(debug_log, chat_log, search_log)

    def _process_results(self, debug_log: Dict, chat_log: Dict, search_log: Dict):
        """Process the results from debug, chat, and search logs."""
        if not debug_log and not chat_log and not search_log:
            return {
                "success": False,
                "data": {},
                "message": f"No logs found for lookup_id: {self.input_params.lookup_id}",
            }

        # Check for missing logs
        missing_logs = []
        if not debug_log:
            missing_logs.append("debug")
        if not chat_log:
            missing_logs.append("chat")
        if not search_log:
            missing_logs.append("search")

        missing_log_message = None
        if missing_logs:
            missing_log_message = f"{', '.join(missing_logs).title()} logs not found for lookup_id: {self.input_params.lookup_id}"

        debug_content = debug_log.get("debug_log", [])
        timing_log = debug_log.get("timing_log", [])

        # Attach Git information
        commit_hash, commit_date, commit_message, branch_name, status = (
            self.get_last_commit_info()
        )
        if debug_content:
            debug_content.insert(
                0,
                {
                    "section_name": "Git",
                    "commit_hash": commit_hash,
                    "commit_date": commit_date,
                    "commit_message": commit_message,
                    "branch_name": branch_name,
                    "status": status,
                },
            )

        # Convert timing logs to markdown table
        markdown_timing_logs = self.get_markdown_timing_logs(timing_log)

        # Parse timing logs with execution info
        parsed_timing_logs = parse_timing_logs(timing_log)

        return {
            "success": True,
            "data": {
                "debug_content": debug_content,
                "timing_logs": markdown_timing_logs,
                "parsed_timing_logs": parsed_timing_logs,
                "start_of_stream": next(
                    (
                        execution["duration"]
                        for item in parsed_timing_logs
                        for execution in item["executions"]
                        if item["name"] == "Start of Stream"
                    ),
                    "N/A",
                ),
                "chat_log": chat_log or search_log,
            },
            "message": (
                "Logs retrieved successfully"
                if not missing_log_message
                else missing_log_message
            ),
        }

    def get_logs(self):
        """
        Main method using parallel functions with timeout.

        - get_debug_log_sync: Does debug database queries
        - get_chat_or_search_sync: Does chat/search database queries with early exit
        - Both functions run in parallel with asyncio.wait_for timeout
        """
        return asyncio.run(self.get_logs_parallel_with_timeout())


def sanitize_for_json(obj: Any) -> Any:
    """
    Recursively convert objects to JSON-compatible formats.

    This function handles:
    - ObjectId -> str
    - datetime objects -> ISO format strings
    - date objects -> ISO format strings
    - Decimal -> float
    - sets -> lists
    - UUID -> str
    - pandas DataFrame -> list of records
    - NaN values -> None
    - Non-serializable types -> str representation

    Args:
        obj: Any Python object to sanitize

    Returns:
        JSON-compatible version of the object
    """
    # Handle None
    if obj is None:
        return None

    # Handle NaN values - both Python float NaN and numpy NaN
    if isinstance(obj, float) and math.isnan(obj):
        return None
    if hasattr(np, "number") and isinstance(obj, np.number) and np.isnan(obj):
        return None

    # Handle MongoDB ObjectId (must be before string check)
    if isinstance(obj, ObjectId):
        return str(obj)

    # Handle datetime objects
    if isinstance(obj, datetime):
        return obj.isoformat()

    # Handle date objects
    if isinstance(obj, date) and not isinstance(obj, datetime):
        return obj.isoformat()

    # Handle Decimal
    if isinstance(obj, Decimal):
        return float(obj)

    # Handle sets
    if isinstance(obj, set):
        return list(obj)

    # Handle UUIDs
    if isinstance(obj, uuid.UUID):
        return str(obj)

    # Handle dictionaries - recursively sanitize each value
    if isinstance(obj, dict):
        return {k: sanitize_for_json(v) for k, v in obj.items()}

    # Handle lists/tuples - recursively sanitize each item
    if isinstance(obj, (list, tuple)):
        return [sanitize_for_json(item) for item in obj]

    # Handle pandas DataFrame - convert to list of records for JSON
    if hasattr(pd, "DataFrame") and isinstance(obj, pd.DataFrame):
        return sanitize_for_json(obj.to_dict("records"))

    # Handle pandas Series
    if hasattr(pd, "Series") and isinstance(obj, pd.Series):
        return sanitize_for_json(obj.to_dict())

    # Handle numpy arrays
    if hasattr(np, "ndarray") and isinstance(obj, np.ndarray):
        return sanitize_for_json(obj.tolist())

    # Handle numpy number types
    if hasattr(np, "integer") and isinstance(obj, np.integer):
        return int(obj)
    if hasattr(np, "floating") and isinstance(obj, np.floating):
        return float(obj)
    if hasattr(np, "bool_") and isinstance(obj, np.bool_):
        return bool(obj)

    # Handle custom objects with __dict__
    if hasattr(obj, "__dict__") and not isinstance(obj, type):
        return sanitize_for_json(obj.__dict__)

    # Check if object is a basic type that JSON can handle
    if isinstance(obj, (str, int, float, bool)):
        return obj

    # For any other types, convert to string
    try:
        return str(obj)
    except Exception:
        return f"Unconvertible object: {type(obj).__name__}"
