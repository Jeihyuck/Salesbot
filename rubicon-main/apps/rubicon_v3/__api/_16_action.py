import sys

sys.path.append("/www/alpha/")

import pycountry

from datetime import datetime, timezone
from dataclasses import dataclass
from pydantic import BaseModel

from apps.rubicon_v3.__function import __llm_call as llm_call
from apps.rubicon_v3.__function.definitions import channels
from apps.rubicon_v3.__function.__prompts import session_summary_prompt
from apps.rubicon_v3.__api._13_chat_history import ChatHistory
from apps.rubicon_v3.__api.__utils import validate_channel
from apps.rubicon_v3.__external_api._15_sprinklr_add_comment import add_comment

from alpha._db import chat_log_collection
from alpha.settings import VITE_OP_TYPE


class Summary(BaseModel):
    session_summary: str


class Action:
    @dataclass
    class ActionParams:
        action_type: str
        action_info: dict

    def __init__(self, input_params: ActionParams):
        self.input_params = input_params

    def action_api_mux(self):
        """
        Main function to handle different action types.
        """
        if self.input_params.action_type == "hide_chat_log":
            return self.hide_chat_log()
        elif self.input_params.action_type == "rename_session_title":
            return self.rename_session_title()
        elif self.input_params.action_type == "generate_conversation_summary":
            return self.generate_conversation_summary()
        else:
            return {
                "success": False,
                "data": {},
                "message": "Invalid action type.",
            }

    def hide_chat_log(self):
        """
        Hide a chat log entry based on the provided message_id and session_id.
        """
        message_id = self.input_params.action_info.get("messageId")
        session_id = self.input_params.action_info.get("sessionId")

        # Make sure one of the parameters is provided
        if not message_id and not session_id:
            return {
                "success": False,
                "data": {},
                "message": "Either messageId or sessionId is required.",
            }

        # Create the filter criteria
        filter_criteria = {}
        if message_id:
            filter_criteria["message_id"] = message_id
        if session_id:
            filter_criteria["session_id"] = session_id

        # Check how many records match the filter criteria
        count = chat_log_collection.count_documents(filter_criteria)
        if count == 0:
            return {
                "success": False,
                "data": {},
                "message": "No records found matching the criteria.",
            }

        # Update the chat log entry to hide it
        result = chat_log_collection.update_many(
            filter_criteria,
            {
                "$set": {
                    "message_status.is_hidden": True,
                    "message_status.hidden_on": datetime.now(timezone.utc),
                }
            },
        )

        update_log = {
            "message_id": message_id,
            "session_id": session_id,
            "matched_count": result.matched_count,
            "updated_count": result.modified_count,
        }

        if result.modified_count > 0:
            return {
                "success": True,
                "data": update_log,
                "message": "Chat log entry successfully hidden.",
            }
        else:
            return {
                "success": False,
                "data": update_log,
                "message": "No chat log entry was updated.",
            }

    def rename_session_title(self):
        """
        Rename the session title based on the provided message_id and new title.
        """
        session_id = self.input_params.action_info.get("sessionId")
        new_title = self.input_params.action_info.get("newTitle")

        # Make sure both parameters are provided
        if not session_id or not new_title:
            return {
                "success": False,
                "data": {},
                "message": "Both sessionId and newTitle are required.",
            }

        # Create the filter criteria
        filter_criteria = {"session_id": session_id}

        # Check how many records match the filter criteria
        count = chat_log_collection.count_documents(filter_criteria)
        if count == 0:
            return {
                "success": False,
                "data": {},
                "message": "No records found matching the criteria.",
            }

        # Update the session title
        result = chat_log_collection.update_many(
            filter_criteria,
            {"$set": {"session_title": new_title}},
        )
        update_log = {
            "session_id": session_id,
            "new_title": new_title,
            "matched_count": result.matched_count,
            "updated_count": result.modified_count,
        }
        if result.modified_count > 0:
            return {
                "success": True,
                "data": update_log,
                "message": "Session title successfully updated.",
            }
        else:
            return {
                "success": False,
                "data": update_log,
                "message": "No session title was updated.",
            }

    def generate_session_summary(self, chat_history, language):
        """
        Generate a session summary based on the chat history.
        """
        prompt = session_summary_prompt.PROMPT.format(language=language)

        # 시스템 프롬프트로 메시지 초기화
        messages = [{"role": "system", "content": prompt}]

        # Add chat history to messages
        for message in chat_history:
            messages.append(message)

        response = llm_call.open_ai_call_structured(
            "gpt-4.1-mini", messages, Summary, 0.01, 0.1, 42
        )

        return response.get("session_summary", "")

    def generate_conversation_summary(self):
        """
        Generate a summary of the conversation based on the provided session_id.
        """
        user_id = self.input_params.action_info.get("userId")
        session_id = self.input_params.action_info.get("sessionId")
        channel = self.input_params.action_info.get("channel")
        message_count = self.input_params.action_info.get("messageCount", 10)
        language_code = self.input_params.action_info.get("lng", "en")

        # Make sure the language code is valid
        if not pycountry.languages.get(alpha_2=language_code):
            return {
                "success": False,
                "data": {},
                "message": "Invalid language code.",
            }

        # Make sure session_id is provided
        if not session_id or not user_id:
            return {
                "success": False,
                "data": {},
                "message": "sessionId and userId are required.",
            }

        # Make sure the channel is valid
        if not channel or not validate_channel(channel):
            return {
                "success": False,
                "data": {},
                "message": "Invalid channel.",
            }

        # First grab the session message history
        chat_history_obj = ChatHistory(
            ChatHistory.ChatHistoryParams(
                user_id=user_id,
                channel=channel,
                message_count=message_count,
                page=1,
                items_per_page=15,
                session_id=session_id,
            )
        )
        chat_history_response = chat_history_obj.get_chat_messages()

        # Grab the chat history data
        chat_history = chat_history_response.get("data", [])
        if not chat_history:
            return {"success": False, "data": {}, "message": "No chat history found."}

        # Grab the english name of the language code (we know it is valid)
        language = pycountry.languages.get(alpha_2=language_code)
        language_name = language.name

        # Generate the session summary
        summary = self.generate_session_summary(chat_history, language_name)

        # Make sure the summary is not empty
        if not summary:
            return {
                "success": False,
                "data": {},
                "message": "Failed to generate summary.",
            }

        # If the channel is DotcomChat, we send the summary to Sprinklr Agent Page
        if channel == channels.DOTCOMCHAT and VITE_OP_TYPE in ["STG", "PRD"]:
            # Add the comment to Sprinklr
            success, response = add_comment(session_id, summary)
            if not success:
                return {
                    "success": False,
                    "data": {},
                    "message": f"Failed to add comment to Sprinklr: {response.get('error', 'Unknown error')}",
                }

            return {
                "success": True,
                "data": {
                    "summary": summary,
                    "sprinklr_response": response,
                },
                "message": "Session summary generated and added to Sprinklr successfully.",
            }

        return {
            "success": True,
            "data": {
                "summary": summary,
            },
            "message": "Session summary generated successfully.",
        }
