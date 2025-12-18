import sys

sys.path.append("/www/alpha/")
import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "alpha.settings")
django.setup()

import hashlib

from datetime import datetime, timezone
from dataclasses import dataclass

from apps.rubicon_v3.__function.__encryption_utils import recursive_decrypt_strings
from apps.rubicon_v3.__function.__django_cache import DjangoCacheClient, CacheKey
from alpha._db import chat_log_collection

cache = DjangoCacheClient()


class ChatHistory:
    @dataclass
    class ChatHistoryParams:
        user_id: str
        channel: str
        message_count: int
        page: int
        items_per_page: int
        session_id: str

    def __init__(self, input_params: ChatHistoryParams):
        self.input_params = input_params
        self.user_hash = hashlib.sha256(
            self.input_params.user_id.encode("utf-8")
        ).hexdigest()

    def _get_messages_projection(self):
        """Helper method to determine messages projection based on message_count"""
        if self.input_params.message_count is None:
            # Return all messages if message_count is None
            return "$messages"
        elif self.input_params.message_count > 0:
            # Apply slice if message_count is positive
            return {"$slice": ["$messages", self.input_params.message_count]}
        else:
            # Empty array if message_count is 0
            return []

    def get_chat_history(self):
        """
        Get chat history for the specified user_id and session_id.
        """
        # Validate required parameters
        if not self.input_params.user_id:
            raise ValueError("user_id is required.")

        if not self.input_params.channel:
            raise ValueError("channel is required.")

        # Define the filter criteria based on the presence of session_id
        filter_criteria = {
            "user_hash": self.user_hash,
            "channel": self.input_params.channel,
            "message_status.completed": True,
            "message_status.is_hidden": {"$ne": True},
        }
        if self.input_params.session_id:
            filter_criteria["session_id"] = self.input_params.session_id

        # Calculate the skip value for pagination
        skip = (self.input_params.page - 1) * self.input_params.items_per_page

        # Define the base aggregation pipeline
        pipeline_initial = [
            # Match documents for the specific user id and session if provided
            {"$match": filter_criteria},
            # First sort all documents by created_on (newest first) to identify recent sessions
            {"$sort": {"created_on": -1}},
            # Group by session_id
            {
                "$group": {
                    "_id": "$session_id",
                    "session_created_on": {"$first": "$created_on"},
                    "messages": {
                        "$push": {
                            "title": {"$ifNull": ["$session_title", "$message"]},
                            "message_id": "$message_id",
                            "message": "$message",
                            "response": "$log.full_response",
                            "supplementary_log": {
                                "$ifNull": ["$supplementary_log", {}]
                            },
                            "created_on": "$created_on",
                        }
                    },
                }
            },
            # Sort sessions by most recent activity
            {"$sort": {"session_created_on": -1}},
        ]

        # Create a paginated pipeline using $facet
        pipeline = pipeline_initial + [
            {
                "$facet": {
                    "metadata": [{"$count": "total"}],
                    "data": [
                        # Skip and limit for pagination
                        # If session_id is provided, we don't paginate (we want just that session)
                        {"$skip": 0 if self.input_params.session_id else skip},
                        {
                            "$limit": (
                                1
                                if self.input_params.session_id
                                else self.input_params.items_per_page
                            )
                        },
                        # Sort messages within each session (oldest first for proper conversation flow)
                        {
                            "$addFields": {
                                "messages": {
                                    "$sortArray": {
                                        "input": "$messages",
                                        "sortBy": {
                                            "created_on": 1
                                        },  # Ascending order (oldest first)
                                    }
                                }
                            }
                        },
                        # Project stage to format the output
                        {
                            "$project": {
                                "session_id": "$_id",
                                "_id": 0,  # Exclude the original _id field
                                "session_created_on": 1,
                                "first_message": {
                                    "$arrayElemAt": ["$messages", 0]
                                },  # Always get first message for title
                                "messages": self._get_messages_projection(),
                            }
                        },
                    ],
                }
            },
        ]

        # Execute the aggregation pipeline
        faceted_result = list(chat_log_collection.aggregate(pipeline))

        # Extract the data and metadata from the faceted result
        result_data = faceted_result[0]["data"] if faceted_result else []
        total_count = (
            faceted_result[0]["metadata"][0]["total"]
            if faceted_result and faceted_result[0]["metadata"]
            else 0
        )

        # Decrypt the result data
        decrypted_result_data = recursive_decrypt_strings(result_data)

        # Process the data
        for session in decrypted_result_data:
            # Get the first message and remove it from session object
            first_message = session.pop("first_message", None)

            # Set the title from the first message if it exists
            if first_message:
                session["title"] = (
                    first_message.get("title")
                    if first_message.get("title")
                    else first_message.get("message", "")
                )
            else:
                session["title"] = "New Chat"

            # Process messages (will be empty if message_count=0)
            for message in session["messages"]:
                # Extract the supplementary information and delete the supplementary log
                message["media"] = message["supplementary_log"].get("media", [])
                message["product_card"] = message["supplementary_log"].get(
                    "product_card", []
                )
                del message["supplementary_log"]

                # Delete the title from the message
                del message["title"]

        # Return with pagination metadata
        return {
            "success": True,
            "data": decrypted_result_data,
            "pagination": {
                "total_items": total_count,
                "total_pages": (total_count + self.input_params.items_per_page - 1)
                // self.input_params.items_per_page,
                "page": self.input_params.page,
                "items_per_page": self.input_params.items_per_page,
            },
            "message": "",
        }

    def get_chat_messages(self):
        """
        Get simplified chat history for the specified user_id and session_id.
        Returns only message and response fields.
        """
        # Validate required parameters
        if not self.input_params.user_id:
            raise ValueError("user_id is required.")
        if not self.input_params.channel:
            raise ValueError("channel is required.")
        if not self.input_params.session_id:
            raise ValueError("session_id is required.")

        # Define the filter criteria
        filter_criteria = {
            "user_hash": self.user_hash,
            "channel": self.input_params.channel,
            "session_id": self.input_params.session_id,
            "message_status.completed": True,
            "message_status.is_hidden": {"$ne": True},
        }

        # Define the aggregation pipeline
        pipeline = [
            # Match documents for the specific user and session
            {"$match": filter_criteria},
            # Sort by created_on (oldest first for proper conversation flow)
            {"$sort": {"created_on": 1}},
            # Project only the fields we need
            {
                "$project": {
                    "_id": 0,
                    "message": 1,
                    "response": "$log.full_response",
                }
            },
            # Apply message count limit
            {"$limit": self.input_params.message_count},
        ]

        # Execute the aggregation pipeline
        result_data = list(chat_log_collection.aggregate(pipeline))

        # Decrypt the result data
        decrypted_result_data = recursive_decrypt_strings(result_data)

        # Process the data to extract response from log
        # Format it to be in the open ai message format
        chat_messages = []
        for message in decrypted_result_data:
            # Append the user message
            chat_messages.append(
                {
                    "role": "user",
                    "content": [{"type": "text", "text": message["message"]}],
                }
            )

            # Append the assistant response
            chat_messages.append(
                {
                    "role": "assistant",
                    "content": message["response"],
                }
            )

        return {"success": True, "data": chat_messages, "message": ""}

    def get_mentioned_products(self):
        """
        Get mentioned products for the specified user_id and session_id.
        Returns aggregated product_log values.
        """
        # Validate required parameters
        if not self.input_params.user_id:
            raise ValueError("user_id is required.")
        if not self.input_params.channel:
            raise ValueError("channel is required.")
        if not self.input_params.session_id:
            raise ValueError("session_id is required.")

        # Define the filter criteria
        filter_criteria = {
            "user_hash": self.user_hash,
            "channel": self.input_params.channel,
            "session_id": self.input_params.session_id,
            "message_status.completed": True,
            "message_status.is_hidden": {"$ne": True},
        }

        # Define the aggregation pipeline
        pipeline = [
            # Match documents for the specific user and session
            {"$match": filter_criteria},
            # Sort by created_on (oldest first for proper conversation flow)
            {"$sort": {"created_on": 1}},
            # Project only the product_log field
            {
                "$project": {
                    "_id": 0,
                    "product_log": {"$ifNull": ["$product_log", []]},
                }
            },
            # Apply message count limit
            {"$limit": self.input_params.message_count},
        ]

        # Execute the aggregation pipeline
        result_data = list(chat_log_collection.aggregate(pipeline))

        # Decrypt the result data
        decrypted_result_data = recursive_decrypt_strings(result_data)

        # Process the data to aggregate product_log values
        product_logs = []
        for message in decrypted_result_data:
            product_logs.append(message["product_log"])

        return {"success": True, "data": product_logs, "message": ""}


class AIBotChatHistory:
    @dataclass
    class AIBotChatHistoryParams:
        type: str
        user_id: str
        session_id: str
        message_count: int
        meta_data: dict

    def __init__(self, input_params: AIBotChatHistoryParams):
        self.input_params = input_params
        self.cache_expiry = 60 * 60 * 1  # 1 hour

    def aibot_chat_history_mux(self):
        if self.input_params.type == "get_chat_history":
            return self.get_aibot_chat_history()
        elif self.input_params.type == "update_chat_history":
            return self.update_aibot_chat_history()
        else:
            raise ValueError(f"Invalid type: {self.input_params.type}")

    def get_aibot_chat_history(self):
        ai_bot_chat_history_cache_key = CacheKey.ai_bot_chat_history(
            self.input_params.user_id, self.input_params.session_id
        )
        ai_bot_chat_history_cached_data = cache.get(ai_bot_chat_history_cache_key)

        # If cached data exists, order by timestamp and return it
        if ai_bot_chat_history_cached_data:
            # Sort the cached data by timestamp in ascending order
            # This ensures that the most recent messages are at the end of the list
            ai_bot_chat_history_cached_data.sort(
                key=lambda x: x["timestamp"],
                reverse=False,  # Sort in ascending order
            )

            # Limit the number of messages if message_count is specified and is an integer
            if self.input_params.message_count and isinstance(
                self.input_params.message_count, int
            ):
                ai_bot_chat_history_cached_data = ai_bot_chat_history_cached_data[
                    -self.input_params.message_count :
                ]

            # If message count is invalid or not specified, return all messages
            return {
                "success": True,
                "data": ai_bot_chat_history_cached_data,
                "message": "Chat history retrieved successfully.",
            }

        # If no cached data exists, return an empty list
        return {
            "success": True,
            "data": [],
            "message": "No chat history found.",
        }

    def update_aibot_chat_history(self):
        # Make sure the query and responses are provided
        if not self.input_params.meta_data.get("input"):
            raise ValueError("Query is required to update chat history.")
        if not self.input_params.meta_data.get("output"):
            raise ValueError("Response is required to update chat history.")

        # Extract query, response, and product_category from meta_data
        query = self.input_params.meta_data["input"]
        response = self.input_params.meta_data["output"]
        product_category = self.input_params.meta_data.get("product_category")

        # Update the chat history in the cache
        update_aibot_chat_history(
            user_id=self.input_params.user_id,
            session_id=self.input_params.session_id,
            query=query,
            response=response,
            product_category=product_category,
            cache_expiry=self.cache_expiry,
        )

        return {
            "success": True,
            "data": None,
            "message": "Chat history updated successfully.",
        }


def update_aibot_chat_history(
    user_id: str,
    session_id: str,
    query: str,
    response: str,
    product_category: str = None,
    product_log: list = None,
    cache_expiry: int = 60 * 60 * 1,  # 1 hour
):
    ai_bot_chat_history_cache_key = CacheKey.ai_bot_chat_history(user_id, session_id)
    ai_bot_chat_history_cached_data = cache.get(ai_bot_chat_history_cache_key)

    # Build to cache data
    to_cache_data = {
        "input": query,
        "output": response,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    if product_category:
        to_cache_data["product_category"] = product_category
    if product_log:
        to_cache_data["product_log"] = product_log

    # If cached data exists, update it
    if ai_bot_chat_history_cached_data:
        ai_bot_chat_history_cached_data.append(to_cache_data)

    # If no cached data exists, create a new list
    else:
        ai_bot_chat_history_cached_data = [to_cache_data]

    # Store the updated chat history in the cache
    cache.store(
        ai_bot_chat_history_cache_key,
        ai_bot_chat_history_cached_data,
        cache_expiry,
    )
