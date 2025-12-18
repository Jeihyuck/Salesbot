import sys

sys.path.append("/www/alpha/")

import asyncio
import hashlib
import pytz
import traceback
import re

from datetime import datetime
from dataclasses import dataclass
from bson.objectid import ObjectId

from apps.rubicon_v3.models import Channel
from apps.rubicon_v3.__function.__llm_call import open_ai_call_stream
from apps.rubicon_v3.__function.__simulate_stream import stream_markdown
from apps.rubicon_v3.__function.__prompts import welcome_message_prompt
from apps.rubicon_v3.__function.__django_rq import run_job_high
from apps.rubicon_v3.__function.__django_cache import DjangoCacheClient, CacheKey
from apps.rubicon_v3.__function.__utils import (
    format_response_content,
    get_language_name,
    get_prompt_from_obj,
)
from apps.rubicon_v3.__function.__exceptions import HttpStatus
from apps.rubicon_v3.__function._82_response_prompts import (
    dict_to_multiline_comment,
    Prompts,
)
from apps.rubicon_v3.__external_api._11_user_info import (
    IndivInfo,
    getFirstName,
    getBirthDay,
)
from apps.rubicon_v3.__external_api._14_azure_email_alert import (
    send_process_error_alert,
)
from apps.rubicon_v3.__api._09_related_query import greeting_query_store
from alpha.settings import VITE_OP_TYPE


cache = DjangoCacheClient()


DEFAULT_WELCOME_MESSAGE = """
안녕하세요{first_name}! {birth_day}삼성전자 제품에 대한 정보가 필요하신가요?

아래 주제로 질문을 해보세요.  
    - **제품 설명/비교** : 관심 제품의 특장점, 기능, 스펙에 대해 설명하거나 제품 간 비교해드려요.  
    - **제품 추천**: 원하는 제품을 찾을 수 있도록 도와드려요.  
    - **가격/프로모션**: 제품의 가격과 진행 중인 프로모션을 확인할 수 있어요.  
    - **사용법**: 제품 및 서비스의 사용법이 궁금하시다면 설명드릴 수 있어요.
"""

DEFAULT_BIRTHDAY_MESSAGE = {
    "KR": "{first_name}님의 생일 축하드려요! 오늘 하루 기쁨이 가득하시길 바랍니다.\n\n",
    "GB": "Wishing you a very happy birthday, {first_name}! May your day be filled with happiness and joy.\n\n",
}


def is_birthday_today(birth_day, timezone):
    """
    Check if the user's birthday is today in the given timezone.
    """
    # Check if birth_day and timezone are provided
    if not birth_day or not isinstance(birth_day, dict) or not timezone:
        return False

    # Grab the local timezone and compare the current date with the user's birthday
    local_tz = None
    try:
        local_tz = pytz.timezone(timezone)
    except pytz.UnknownTimeZoneError:
        return False

    # Get the user's birth month and day
    birth_month = birth_day.get("month")
    birth_day = birth_day.get("day")

    # Make sure both month and day are provided
    if not birth_month or not birth_day:
        return False

    today = datetime.now(local_tz).date()
    return today.month == int(birth_month) and today.day == int(birth_day)


def get_greeting_message(channel, country_code, first_name, birth_day):
    """
    Get the greeting message for the user based on the channel and country code.
    If no specific message is found, a default welcome message is returned.
    """
    # Get the welcome message for the channel and country code
    channel_data = (
        Channel.objects.filter(channel=channel, country_code=country_code)
        .values("welcome_msg", "timezone")
        .first()
    )
    welcome_message = (
        channel_data.get("welcome_msg", "").strip() if channel_data else ""
    )
    timezone = channel_data.get("timezone") if channel_data else None

    # If no welcome message is found, use a default message
    if not welcome_message:
        welcome_message = DEFAULT_WELCOME_MESSAGE

    # Format the welcome message with the user's first name if available
    if first_name:
        welcome_message = welcome_message.replace("{first_name}", f" {first_name}님")
        # Check if it is the user's birthday
        if is_birthday_today(birth_day, timezone):
            welcome_message = welcome_message.replace(
                "{birth_day}",
                DEFAULT_BIRTHDAY_MESSAGE.get(
                    country_code,
                    "{first_name}님의 생일 축하드려요! 오늘 하루 기쁨이 가득하시길 바랍니다.\n\n",
                ).replace("{first_name}", first_name),
            )
        # If it is not the user's birthday, remove the birthday placeholder
        else:
            welcome_message = welcome_message.replace("{birth_day}", "")

    # If no first name is provided, remove the first name placeholder and birthday placeholder
    else:
        welcome_message = welcome_message.replace("{first_name}", "").replace(
            "{birth_day}", ""
        )

    # Remove any extra spaces
    return welcome_message.strip()


def camel_to_snake(name):
    """Convert camelCase to snake_case."""
    return re.sub(r"(?<!^)(?=[A-Z])", "_", name).lower()


def create_dataclass_from_dict(data_dict, dataclass_type):
    """
    Create a dataclass instance from a dictionary with camelCase to snake_case conversion.

    Args:
        data_dict (dict): Dictionary with camelCase keys
        dataclass_type (type): The dataclass type to create

    Returns:
        An instance of the specified dataclass
    """
    # Get valid field names from the dataclass
    valid_fields = {
        field.name for field in dataclass_type.__dataclass_fields__.values()
    }

    # Create kwargs with converted field names, filtering to valid fields only
    kwargs = {}
    for key, value in data_dict.items():
        field_name = camel_to_snake(key)
        if field_name in valid_fields:
            kwargs[field_name] = value

    return dataclass_type(**kwargs)


class ResponseHandler:
    def __init__(
        self,
        greeting_flow: "DefaultGreeting",
        stream: bool,
        error: bool,
        cached_response: str = None,
    ):
        self.greeting_flow = greeting_flow
        self.stream = stream
        self.error = error
        self.full_response = ""
        self.cached_response = cached_response

    def _call_response(self, messages):
        # Generate the greeting message
        for chunk in open_ai_call_stream(
            model_name=self.greeting_flow.gpt_model,
            messages=messages,
            temperature=0.1,
            seed=42,
            stream=True,
        ):
            if chunk.startswith("### LLM CALL META") == False:
                yield chunk

    def _stream_simulator(self):
        """
        Simulate the streaming of the greeting message.
        """
        for chunk in stream_markdown(self.cached_response.strip()):
            yield chunk

    def _get_content_generator(self):
        """
        Get the content generator based on whether an error occurred or not.
        Or if a cached response is provided.
        Or if the content hash is different (signifying the greeting message has changed).
        """
        # Prepare the messages for the OpenAI call
        input_prompt = dict_to_multiline_comment(
            {"welcome_message": self.greeting_flow.greeting_message}
        )

        prompt = welcome_message_prompt.PROMPT.format(
            language=self.greeting_flow.language
        )
        messages = [
            {"role": "system", "content": prompt},
            {"role": "assistant", "content": input_prompt},
        ]

        # If an error occurred, return the error response generator
        # And update messages to have the error prompt
        if self.error:
            error_prompt = get_prompt_from_obj(
                category_lv1=Prompts.EXCEPTION_PROCESS_ERROR["category_lv1"],
                country_code=self.greeting_flow.input_args.country_code,
                response_type=Prompts.EXCEPTION_PROCESS_ERROR["response_type"],
            )
            messages[0]["content"] = error_prompt
            input_prompt = dict_to_multiline_comment(
                {"output_language": self.greeting_flow.language}
            )
            messages[1]["content"] = input_prompt

            return self._call_response(messages)

        # If a cached response is provided, return the stream simulator
        if self.cached_response:
            return self._stream_simulator()

        # Otherwise, return the OpenAI call response generator
        return self._call_response(messages)

    async def stream_response(self):
        """
        Stream the response based on the input data
        Return a generator that yields the response content.
        """
        # Ensure the markdown tag is opened
        yield "data: ```markdown<br>\n\n"
        try:
            # Get the content generator
            for chunk in self._get_content_generator():
                self.full_response += chunk
                yield f"data: {format_response_content(chunk)}\n\n"

        except Exception as e:
            # Yield an error message if an exception occurs
            yield f"data: [STREAM ERROR: {str(e)}]\n\n"

            # If there is an error, send an alert
            print(f"Error in get_stream_search_summary: {e}")
            traceback_message = traceback.format_exc()
            print(traceback_message)

            # Alert Email
            if VITE_OP_TYPE in ["STG", "PRD"]:
                context_data = {
                    "Module": "Rubicon Default Greeting Response Handler",
                    "Channel": self.greeting_flow.input_args.channel,
                    "Country Code": self.greeting_flow.input_args.country_code,
                    "Object ID": str(self.greeting_flow.object_id),
                    "User ID": self.greeting_flow.input_args.user_id,
                    "Message ID": self.greeting_flow.input_args.message_id,
                }

                run_job_high(
                    send_process_error_alert,
                    (str(e), "pipeline_error"),
                    {
                        "error_traceback": traceback_message,
                        "context_data": context_data,
                    },
                )

        finally:
            # Ensure to send the end of stream tag
            yield "data: ```<EOS>\n\n"

            # Ensure to log the full response
            self._log_response()

    def build_response(self):
        """
        Build the response based on the input data
        This method is used when streaming is disabled.
        """
        try:
            # First check if the response is cached
            if self.cached_response and not self.error:
                # Set the full response to the cached response
                self.full_response = self.cached_response
                # Log the response
                self._log_response()
                # Return the cached response (after cleaning)
                return {
                    "success": True,
                    "data": self.greeting_flow.full_response,
                    "message": "Cached greeting message",
                }

            # If no cached response, generate a new greeting message
            for chunk in self._get_content_generator():
                self.full_response += chunk

            # Log the response
            self._log_response()

            # Return the full response
            return {
                "success": True,
                "data": self.greeting_flow.full_response,
                "message": "Generated greeting message",
            }

        except Exception as e:
            # If an error occurs, return an error response
            traceback_message = traceback.format_exc()
            print(f"Error in build_response: {e}")
            print(traceback_message)

            # Alert Email
            if VITE_OP_TYPE in ["STG", "PRD"]:
                context_data = {
                    "Module": "Rubicon Default Greeting Response Handler",
                    "Channel": self.greeting_flow.input_args.channel,
                    "Country Code": self.greeting_flow.input_args.country_code,
                    "Object ID": str(self.greeting_flow.object_id),
                    "User ID": self.greeting_flow.input_args.user_id,
                    "Message ID": self.greeting_flow.input_args.message_id,
                }

                run_job_high(
                    send_process_error_alert,
                    (str(e), "pipeline_error"),
                    {
                        "error_traceback": traceback_message,
                        "context_data": context_data,
                    },
                )

            # Return the error response
            return {
                "success": False,
                "data": "[STREAM ERROR: Error generating response]",
                "message": str(e),
            }

    def _log_response(self):
        # Clean the full response
        self.full_response = (
            self.full_response.replace("```markdown<br>", "")
            .replace("```<EOS>", "")
            .strip()
        )

        # Update the full response in greeting flow
        self.greeting_flow.full_response = self.full_response


class DefaultGreeting:
    @dataclass
    class InputArguments:
        channel: str
        country_code: str
        user_id: str
        session_id: str
        message_id: str
        lng: str = "en"
        gu_id: str = "default_gu_id"
        sa_id: str = "default_sa_id"

    def __init__(
        self,
        input_args: InputArguments,
        object_id: ObjectId,
        stream: bool,
        status: HttpStatus,
    ):
        self.input_args = input_args
        self.object_id = object_id
        self.stream = stream
        self.status = status
        self.gpt_model = "gpt-4.1-mini"
        self.session_expiry = 60 * 60 * 1  # 1 hour'
        self.cached_welcome_message = None
        self.cache_key = None
        self.full_response = ""
        self.response_handler = None
        self.update_cache = False

    def _variable_setup(self):
        # Get the language data
        self.language = get_language_name(
            self.input_args.lng, self.input_args.country_code, self.input_args.channel
        )

        # Prepare the greeting query
        run_job_high(
            greeting_query_store,
            (
                self.input_args.channel,
                self.input_args.country_code,
                self.language,
                self.input_args.message_id,
                self.session_expiry,
            ),
            {},
        )

    def _get_user_info(self):
        # Check if user info is in cache
        user_info_cache_key = CacheKey.user_info(
            self.input_args.sa_id, self.input_args.country_code
        )
        user_info_data = cache.get(user_info_cache_key, {})
        # If user info is not in cache, fetch it
        if (
            not user_info_data
            and self.input_args.sa_id
            and self.input_args.sa_id != "default_sa_id"
        ):
            # Grab user info data
            user_info_class = IndivInfo(
                self.input_args.country_code,
                self.input_args.sa_id,
                "default_gu_id",
                self.input_args.channel,
            )
            user_info_data = asyncio.run(user_info_class.getUserInfo())
            # Store the user info in cache
            if user_info_data:
                cache.store(user_info_cache_key, user_info_data, 60 * 30)  # 30 minutes

        # Get the user name
        self.first_name = getFirstName(user_info_data)

        # Get the user's birthday
        self.birth_day = getBirthDay(user_info_data)

    def _get_greeting_message(self):
        # Check if the non-personalized greeting message is available in cache
        if not self.first_name:
            self.cache_key = CacheKey.welcome_message(
                channel=self.input_args.channel,
                country_code=self.input_args.country_code,
                language=self.language,
            )
            self.cached_welcome_message = cache.get(self.cache_key)

        # Get the greeting message
        self.greeting_message = get_greeting_message(
            self.input_args.channel,
            self.input_args.country_code,
            self.first_name,
            self.birth_day,
        )

        # Get the greeting message hash
        self.content_hash = hashlib.md5(self.greeting_message.encode()).hexdigest()[:8]

    def _response_handler(self):
        # If a cached welcome message is available, check if the content hash matches
        if (
            self.cached_welcome_message
            and self.cached_welcome_message.get("content_hash") == self.content_hash
        ):
            # Content hash matches, return the response handler with cached response
            self.response_handler = ResponseHandler(
                greeting_flow=self,
                stream=self.stream,
                error=False,  # False for no error
                cached_response=self.cached_welcome_message.get("welcome_message"),
            )
            return  # Exit early as response handler is set

        # Otherwise, create the non-cached response handler
        self.response_handler = ResponseHandler(
            greeting_flow=self,
            stream=self.stream,
            error=False,  # False for no error
            cached_response=None,
        )

        # Update the update_cache flag
        self.update_cache = True
        return

    def _update_greeting_cache(self):
        # Cache the generated welcome message if it is not personalized
        # And if the content hash is different (signifying the greeting message has changed)
        if self.update_cache and not self.first_name and self.cache_key:
            # Make sure the full welcome message does not have any "'" at the start or end
            # Or any " at the start or end
            full_welcome_message = self.full_response.strip().strip('"').strip("'")

            # Update the cache
            cache.store(
                self.cache_key,
                {
                    "welcome_message": full_welcome_message.strip(),
                    "content_hash": self.content_hash,
                },
                60 * 60 * 24 * 1,  # 1 day cache timeout
            )

        # Otherwise, update the cache TTL by using touch
        elif self.cache_key:
            cache.touch_exists(self.cache_key, 60 * 60 * 24 * 1)  # 1 day cache timeout

    def run(self):
        # Variable initialization
        self._variable_setup()

        # Get User Info
        self._get_user_info()

        # Get the greeting message
        self._get_greeting_message()

        # Prepare the response handler
        self._response_handler()

    def enqueue_greeting_flow(self):
        """
        Run the Default Greeting flow and handle exceptions.
        """
        try:
            self.run()

        except Exception as e:
            print(f"{type(e).__name__} in Default Greeting: {e}")
            traceback_message = traceback.format_exc()
            print(traceback_message)

            # Alert Email
            if VITE_OP_TYPE in ["STG", "PRD"]:
                context_data = {
                    "API": "Default Greeting",
                    "Channel": self.input_args.channel,
                    "Country Code": self.input_args.country_code,
                    "Object ID": self.object_id,
                    "User ID": self.input_args.user_id,
                    "Session ID": self.input_args.session_id,
                    "Message ID": self.input_args.message_id,
                }

                run_job_high(
                    send_process_error_alert,
                    (str(e), "pipeline_error"),
                    {
                        "error_traceback": traceback_message,
                        "context_data": context_data,
                    },
                )

            # Update the status code
            self.status.status = e.status_code if hasattr(e, "status_code") else 500

            # Create the error response handler
            self.response_handler = ResponseHandler(
                greeting_flow=self,
                stream=self.stream,
                error=True,  # True for error
                cached_response=None,
            )

    def get_non_stream_response(self):
        """
        Get the non-streaming response.
        """
        # Retrieve the response
        response_result = self.response_handler.build_response()

        # Update the greeting cache
        self._update_greeting_cache()

        return response_result

    async def get_stream_response(self):
        """
        Get the streaming response.
        """
        # Retrieve the response
        async for chunk in self.response_handler.stream_response():
            yield chunk
            await asyncio.sleep(0.0001)  # Force yield to event loop

        # Update the greeting cache
        self._update_greeting_cache()
