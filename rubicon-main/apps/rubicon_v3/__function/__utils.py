import sys

sys.path.append("/www/alpha/")

import base64
import mimetypes
import re
import pycountry
import urllib.parse
import unicodedata
import emoji
import json
import asyncio
import logging
import time
import nest_asyncio
import calendar
import datetime

from enum import Enum
from typing import Any, Dict, List, Tuple

from django.core.files.uploadedfile import InMemoryUploadedFile
from django.db.models import Q

from apps.rubicon_v3.models import (
    Intelligence_V2,
    Channel,
    Prompt_Template,
    Web_Link,
    uk_product_division_map,
)
from apps.rubicon_data.models import (
    product_category,
    goods_cstrt_info,
    uk_product_cstrt_info,
)
from apps.rubicon_v3.__function.__django_cache import (
    DjangoCacheClient,
    CacheKey,
    SessionFlags,
)
from apps.rubicon_v3.__function.__aho_corasick import AhoCorasickAutomaton
from apps.rubicon_v3.__function.__django_cache_init import create_validation_automaton
from apps.rubicon_v3.__function.definitions import (
    intelligences,
    sub_intelligences,
    response_types,
    channels,
)
from apps.rubicon_v3.__function.__llm_call import _eval_chunk
from apps.rubicon_v3.__function._80_stream_moderator_checkers import (
    ProhibitedPatternsChecker,
    PII_Checker,
)
from apps.rubicon_v3.__function._82_response_prompts import input_prompt_data_mapping
from apps.rubicon_v3.__api._13_chat_history import ChatHistory
from apps.rubicon_v3.__external_api.__dkms_encode import DKMS_Encoder

from alpha._db import chat_log_collection

cache = DjangoCacheClient()
dkms_encoder = DKMS_Encoder()

# Set up logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("rubicon_v3_utils")

MAX_QUERY_LENGTH_IN_BYTE = 512


class FileType(Enum):
    """Enum for different supported file types"""

    IMAGE = "image"
    AUDIO = "audio"
    VIDEO = "video"
    DOCUMENT = "document"
    UNKNOWN = "unknown"


class OriginalQueryInvalidTypes(Enum):
    EMPTY = "empty"
    HYPERLINK = "hyperlink"
    WORD = "word"
    PRE_EMBARGO = "pre_embargo"
    PATTERN = "pattern"
    REDIRECT = "redirect"


def get_language_name(language_code: str, country_code: str, channel: str) -> str:
    language = pycountry.languages.get(alpha_2=language_code)
    if language:
        return language.name
    else:
        # Get the default language name based on the country code and channel
        return get_default_language(channel, country_code)


def get_session_title_from_chat_log(session_id: str) -> str:
    """
    Retrieves the session title from the chat log based on the session ID.

    Args:
        session_id (str): The session ID to search for in the chat log.

    Returns:
        str: The session title if found, otherwise an empty string.
    """
    # Query the chat log collection for the session title
    result = chat_log_collection.find_one(
        {
            "session_id": session_id,
            "input_log.model": "rubicon",
            "message_status.completed": True,
            "message_status.is_hidden": {"$ne": True},
            "message_status.multi_input": {"$ne": True},
        },
        {"session_title": 1},
    )
    if result and "session_title" in result:
        return result["session_title"]
    return ""


def get_session_initial_message_id_from_chat_log(session_id: str) -> str:
    """
    Retrieves the message ID from the earliest chat log entry for a given session.

    Args:
        session_id (str): The session ID to search for in the chat log.

    Returns:
        str: The message ID of the earliest log entry if found, otherwise None.
    """
    # Query the chat log collection for documents with this session_id
    # Sort by created_on in ascending order to get the earliest document
    result = chat_log_collection.find_one(
        {
            "session_id": session_id,
            "input_log.model": "rubicon",
            "message_status.completed": True,
        },
        {"message_id": 1},
        sort=[("created_on", 1)],  # Sort by created_on in ascending order
    )

    if result and "message_id" in result:
        return result["message_id"]
    return None


def get_latest_language(session_id: str) -> str:
    """
    Retrieves the latest language used in the session from the chat log.
    Args:
        session_id (str): The session ID to search for in the chat log.
    Returns:
        str: The language code if found, otherwise None.
    """
    # Query the chat log for the latest language used in the session
    result = chat_log_collection.find_one(
        {
            "session_id": session_id,
            "input_log.model": "rubicon",
            "message_status.completed": True,
            "message_status.is_hidden": {"$ne": True},
        },
        {"dashboard_log.language": 1},
        sort=[("created_on", -1)],  # Sort by created_on in descending order
    )

    if result and "dashboard_log" in result and "language" in result["dashboard_log"]:
        return result["dashboard_log"]["language"]
    return None


def get_latest_session_flags(session_id: str) -> Dict[str, Any]:
    """
    Retrieves the latest session flags from the chat log for a given session ID.

    Args:
        session_id (str): The session ID to search for in the chat log.

    Returns:
        Dict[str, Any]: The session flags if found, otherwise None.
    """
    # Query the chat log for the latest session flags
    result = chat_log_collection.find_one(
        {
            "session_id": session_id,
            "input_log.model": "rubicon",
            "message_status.completed": True,
            "message_status.is_hidden": {"$ne": True},
        },
        {"continuation_log": 1},
        sort=[("created_on", -1)],  # Sort by created_on in descending order
    )

    if (
        result
        and "continuation_log" in result
        and "session_flags" in result["continuation_log"]
    ):
        return result["continuation_log"]["session_flags"]
    return None


def init_django_cache_session(
    session_id,
    message_id,
    user_id,
    channel,
    country_code,
    lng,
    expire,
):
    """
    Initializes the Django cache for a session with the provided parameters.
    For certain keys, if it does not exist, the data will be fetched from the chat log.
    These keys include:
    - message_history
    - language
    - mentioned_products
    - session_title
    - session_flags
    """
    # Define the cache keys
    message_history_cache_key = CacheKey.message_history(session_id)
    language_cache_key = CacheKey.language(session_id)
    mentioned_products_cache_key = CacheKey.mentioned_products(session_id)
    session_title_cache_key = CacheKey.session_title(session_id)
    session_flags_cache_key = CacheKey.session_flags(session_id)
    session_initial_message_id_cache_key = CacheKey.session_initial_message_id(
        session_id
    )

    # Get the language data using the country code and language code
    language_data = get_language_name(lng, country_code, channel)

    # Check if the session title cache key does not exists
    # If it exists, refresh the cache with the expire time
    if not cache.touch_exists(session_title_cache_key, expire):
        # Try to get the session title from the chat log
        session_title = get_session_title_from_chat_log(session_id)
        # Store session title in cache
        cache.store(session_title_cache_key, session_title, expire)

    # Check if the session initial message ID cache key does not exists
    # If it exists, refresh the cache with the expire time
    if not cache.touch_exists(session_initial_message_id_cache_key, expire):
        initial_message_id = message_id
        # Try to get the initial message ID from the chat log
        session_initial_message_id = get_session_initial_message_id_from_chat_log(
            session_id
        )
        if session_initial_message_id:
            initial_message_id = session_initial_message_id

        # Store session initial message ID in cache
        cache.store(session_initial_message_id_cache_key, initial_message_id, expire)

    # Chat History Class for message history, mentioned products, and session flags
    chat_history_class = ChatHistory(
        input_params=ChatHistory.ChatHistoryParams(
            user_id=user_id,
            channel=channel,
            message_count=20,
            page=1,
            items_per_page=10,
            session_id=session_id,
        )
    )

    # Check if the message history cache does not exist
    # If it exists, refresh the cache with the expire time
    if not cache.touch_exists(message_history_cache_key, expire):
        # If the message history is not in cache, fetch it from the chat log
        chat_history_data = chat_history_class.get_chat_messages()
        chat_history = chat_history_data.get("data", [])
        cache.store(message_history_cache_key, chat_history, expire)

    # Check if the mentioned products cache does not exist
    # If it exists, refresh the cache with the expire time
    if not cache.touch_exists(mentioned_products_cache_key, expire):
        # If the mentioned products are not in cache, fetch them from the chat log
        mentioned_products_data = chat_history_class.get_mentioned_products()
        mentioned_products = mentioned_products_data.get("data", [])
        cache.store(mentioned_products_cache_key, mentioned_products, expire)

    # Check if the language cache does not exist
    # If it exists, refresh the cache with the expire time
    if not cache.touch_exists(language_cache_key, expire):
        # If the language is not in cache, fetch it from the chat log
        latest_language = get_latest_language(session_id)
        if latest_language:
            language_data = latest_language
        cache.store(language_cache_key, language_data, expire)

    # Check if the session flags cache does not exist
    # If it exists, refresh the cache with the expire time
    if not cache.touch_exists(session_flags_cache_key, expire):
        # If the session flags are not in cache, fetch them from the chat log
        session_flags = {
            SessionFlags.TURNS_SINCE_RE_ASKED.value: 5,
            SessionFlags.STORE_RE_ASKED.value: False,
        }
        latest_session_flags = get_latest_session_flags(session_id)
        if latest_session_flags:
            session_flags = latest_session_flags
        cache.store(session_flags_cache_key, session_flags, expire)


def categorize_files(
    files: List[InMemoryUploadedFile],
) -> Dict[FileType, List[Tuple[InMemoryUploadedFile, str]]]:
    """
    주어진 파일 목록을 파일 유형별로 분류합니다.

    Args:
        files (List[InMemoryUploadedFile]): 분류할 업로드된 파일 목록.

    Returns:
        Dict[FileType, List[Tuple[InMemoryUploadedFile, str]]]: 파일 유형을 파일 객체와 MIME 유형의 튜플 목록으로 매핑한 사전.
    """
    if not files:
        return {}

    categorized_files: Dict[FileType, List[Tuple[InMemoryUploadedFile, str]]] = {
        file_type: [] for file_type in FileType
    }

    for file in files:
        # Get MIME type from the file
        mime_type = file.content_type

        # If MIME type isn't available, try to guess from filename
        if not mime_type:
            mime_type, _ = mimetypes.guess_type(file.name)
            if not mime_type:
                # Add to unknown category if we can't determine the type
                categorized_files[FileType.UNKNOWN].append(
                    (file, "application/octet-stream")
                )
                continue

        # Get the main type from the MIME type (e.g., "image" from "image/jpeg")
        main_type = mime_type.split("/")[0]

        # Categorize based on main type
        if main_type == "image":
            categorized_files[FileType.IMAGE].append((file, mime_type))
        elif main_type == "audio":
            categorized_files[FileType.AUDIO].append((file, mime_type))
        elif main_type == "video":
            categorized_files[FileType.VIDEO].append((file, mime_type))
        elif main_type in ["text", "application"]:
            categorized_files[FileType.DOCUMENT].append((file, mime_type))
        else:
            categorized_files[FileType.UNKNOWN].append((file, mime_type))

    # Remove empty categories
    return {k: v for k, v in categorized_files.items() if v}


def check_original_query(
    original_query: str, channel: str, language: str
) -> tuple[bool, str]:
    # Check if the original query is empty
    if not original_query:
        return False, OriginalQueryInvalidTypes.EMPTY, "The query cannot be empty."

    # Check if the query matches any of the redirect request patterns
    redirect_request_patterns = [
        "상담원 연결",
        "상담사 연결",
        "Connect To Agent",
        "Connect to live agent",
        "Transfer to agent",
        "Transfer to live agent",
        "Speak to agent",
        "Speak to live agent",
    ]
    # Case-insensitive check for redirect patterns (only for certain channels)
    if channel in channels.DOTCOMCHAT:
        for pattern in redirect_request_patterns:
            if re.search(pattern, original_query, re.IGNORECASE):
                return (
                    False,
                    OriginalQueryInvalidTypes.REDIRECT,
                    f"Redirect request detected: '{pattern}'",
                )

    # Use (?:...) for non-capturing groups to avoid returning the TLD separately
    hyperlink_pattern = r"(https?://\S+|www\.\S+|\S+\.(?:com|org|net|io|co|gov|edu|app|dev|ai|xyz|info|biz|me|uk|ca|eu|jp|de|fr|au|ru|ch|it|nl|se|no|fi|dk|pl)\b)"

    # Find all hyperlinks in the query
    hyperlinks = re.findall(hyperlink_pattern, original_query)

    if hyperlinks:
        for link in hyperlinks:
            try:
                # Prepare the URL for parsing
                if link.startswith("www."):
                    url_to_parse = "http://" + link
                elif not (link.startswith("http://") or link.startswith("https://")):
                    url_to_parse = "http://" + link
                else:
                    url_to_parse = link

                # Parse the URL to extract the domain
                parsed_url = urllib.parse.urlparse(url_to_parse)
                domain = parsed_url.netloc.lower()

                # If parsing resulted in empty netloc, the domain might be in the path
                if not domain and parsed_url.path:
                    domain = parsed_url.path.lower()

                # Check if it's a samsung.com domain or subdomain
                if not (domain == "samsung.com" or domain.endswith("samsung.com")):
                    return (
                        False,
                        OriginalQueryInvalidTypes.HYPERLINK,
                        "Only samsung.com hyperlinks are allowed.",
                    )
            except Exception as e:
                # If URL parsing fails, reject the link
                return (
                    False,
                    OriginalQueryInvalidTypes.HYPERLINK,
                    "Invalid hyperlink format detected.",
                )

    # Check the pre-embargo words
    cache_key = CacheKey.aho_corasick_automaton("pre_embargo_words")
    automaton: AhoCorasickAutomaton = cache.get(cache_key)
    if not automaton:
        # If the automaton is not in cache, create it
        create_validation_automaton()
        # If the automaton is still not created after trying to create it, pass
        automaton = cache.get(cache_key)
        if not automaton:
            pass
    # Only check for pre-embargo words if the automaton is available
    if automaton:
        pre_embargo_matches = automaton.search(original_query)
        if pre_embargo_matches:
            # If any pre-embargo patterns are found, return False with the first match
            first_match = pre_embargo_matches[0]
            return (
                False,
                OriginalQueryInvalidTypes.PRE_EMBARGO,
                f"Pre-embargo pattern detected: '{first_match['matched_text']}'",
            )

    # Check the original query for any matches of prohibited patterns
    prohibited_patterns_checker = ProhibitedPatternsChecker(language)
    checker_flag = prohibited_patterns_checker.check(original_query)
    if checker_flag and not checker_flag.get("safe"):
        # If any prohibited patterns are found, return False with the first match
        reason = checker_flag.get("reason", "Prohibited pattern detected.")
        pattern_name = checker_flag.get("pattern_name", "Unknown pattern")
        if pattern_name.startswith("Pre-embargo:"):
            return (
                False,
                OriginalQueryInvalidTypes.PRE_EMBARGO,
                f"Pre-embargo pattern detected: '{reason}'",
            )
        else:
            return (
                False,
                OriginalQueryInvalidTypes.PATTERN,
                f"Prohibited pattern detected: '{reason}'",
            )

    # Check if the original query includes any prohibited words using Aho-Corasick Automaton
    cache_key = CacheKey.aho_corasick_automaton("input_words")
    automaton: AhoCorasickAutomaton = cache.get(cache_key)
    if not automaton:
        # If the automaton is not in cache, create it
        create_validation_automaton()
        # If the automaton is still not created, pass
        automaton = cache.get(cache_key)
        if not automaton:
            pass
    # Only check for prohibited words if the automaton is available
    if automaton:
        matches = automaton.search(original_query)
        if matches:
            # If any prohibited patterns are found, return False with the first match
            first_match = matches[0]
            return (
                False,
                OriginalQueryInvalidTypes.WORD,
                f"Prohibited pattern detected: '{first_match['matched_text']}'",
            )

    return True, None, "All Good"


def mask_pii(
    original_query: str, message_history: list[Dict[str, Any]], country_code: str
):
    """
    Masks personally identifiable information (PII) in the given text.
    Args:
        original_query (str): The text to be checked for PII.
        message_history (list[Dict[str, Any]]): The message history to be checked for PII.
        country_code (str): The country code to determine the PII masking rules.

    Returns:
        tuple: A tuple containing the masked original query and the masked message history.
    """
    # Get the PII checker for the specified country
    pii_checker = PII_Checker(country_code)

    # Mask PII in the original query
    masked_original_query = pii_checker.mask(original_query)

    # Mask PII in the message history
    masked_message_history = []
    for message in message_history:
        masked_message = message.copy()
        if masked_message["role"] == "user":
            masked_content = []
            for content in masked_message["content"]:
                if content["type"] == "text":
                    masked_text = pii_checker.mask(content["text"])
                    masked_content.append({"type": "text", "text": masked_text})
                else:
                    masked_content.append(content)
        else:
            masked_message["content"] = pii_checker.mask(message["content"])
        masked_message_history.append(masked_message)

    return masked_original_query, masked_message_history


def cleanup_message_history(
    message_history: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """
    Cleans up the message history by removing unnecessary tags and formatting.

    Args:
        message_history (List[Dict[str, Any]]): List of message history items.

    Returns:
        List[Dict[str, Any]]: Cleaned up message history.
    """

    def clean_content(text: str) -> str:
        # Remove markdown images
        text = remove_markdown_images(text)
        # Remove ```markdown and ```<EOS> tags
        text = text.replace("```markdown", "").replace("```<EOS>", "")
        # Strip leading and trailing whitespace
        return text.strip()

    # Iterate through each message in the history
    for message in message_history:
        # For role "user", clean up the content list
        if message["role"] == "user":
            # Find the first text content item
            for content in message["content"]:
                if content["type"] == "text":
                    content["text"] = clean_content(content["text"])
                    break
        else:
            # For other roles, clean up the content string
            message["content"] = clean_content(message["content"])


def check_multi_input(message_history: List[Dict[str, Any]]) -> bool:
    """
    메시지 히스토리에서 다중 입력을 확인합니다.

    Args:
        message_history (List[Dict[str, Any]]): 메시지 히스토리 목록.

    Returns:
        bool: 다중 입력이 발견되면 True, 그렇지 않으면 False.
    """
    # If there is no message history, return False
    if not message_history:
        return False

    # Check if the last message is a text message not from the user (meaning it's a system message)
    last_message = message_history[-1]
    if last_message.get("type") == "text" and last_message.get("role") != "user":
        return False

    # Otherwise return True
    return True


def filter_messages(messages):
    """
    Filter messages by removing all messages with role="card"

    Args:
        messages (list): List of message dictionaries

    Returns:
        list: Filtered list with card roles removed
    """
    return [msg for msg in messages if msg["role"] != "card"]


def get_multi_input_message_history(
    message_history: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:

    if not message_history:
        return []

    # First, combine consecutive messages with same role (preserving original roles)
    modified_message_history = []
    consecutive_messages = [message_history[0]["content"]]
    consecutive_role = message_history[0]["role"]

    for message in message_history[1:]:
        if message["type"] == "text":
            if message["role"] == consecutive_role:
                consecutive_messages.append(message["content"])
            else:
                # Finalize the current consecutive group
                content = " ".join(consecutive_messages)
                if consecutive_role == "user":
                    content = [{"type": "text", "text": content}]

                modified_message_history.append(
                    {
                        "role": consecutive_role,
                        "content": content,
                    }
                )
                # Start new consecutive group
                consecutive_messages = [message["content"]]
                consecutive_role = message["role"]

    # Add the last set of consecutive messages
    content = " ".join(consecutive_messages)
    if consecutive_role == "user":
        content = [{"type": "text", "text": content}]

    modified_message_history.append({"role": consecutive_role, "content": content})

    # Second, filter out card roles
    modified_message_history = filter_messages(modified_message_history)

    # Finally, convert remaining non-user roles to assistant
    def get_message_role(role):
        if role != "user":
            return "assistant"
        return role

    # Update roles in the modified message history
    for message in modified_message_history:
        message["role"] = get_message_role(message["role"])

    # Clean up the message history
    cleanup_message_history(modified_message_history)

    return modified_message_history


def get_multi_input_combined_query_message_history_cancel_message_ids(
    original_query: str,
    message_history: List[Dict[str, Any]],
) -> Tuple[str, List[Dict[str, Any]], List[str]]:
    """
    Gets the combined query from consecutive user messages in the message history,
    along with the modified message history and a list of consecutive user message IDs to cancel.
    Args:
        original_query (str): The original query to append to the combined user messages.
        message_history (List[Dict[str, Any]]): Message history containing user and assistant messages.

    Returns:
        Tuple[str, List[Dict[str, Any]], List[str]]: Combined query, modified message history, and list of consecutive user message IDs.
    """
    # Start from the end and collect consecutive user messages
    consecutive_user_messages = []
    consecutive_user_message_ids = []
    consecutive_user_count = 0

    # Iterate through messages in reverse order
    for message in reversed(message_history):
        # If it's a user text message, add it to our list
        if message["type"] == "text" and message["role"] == "user":
            consecutive_user_messages.append(message["content"])
            consecutive_user_message_ids.append(message["messageId"])
            consecutive_user_count += 1
        else:
            # Stop once we hit a non-user message
            break

    # Reverse the list to maintain chronological order
    consecutive_user_messages.reverse()

    # Combine the consecutive user messages into a single query
    combined_query = " ".join(consecutive_user_messages) + " " + original_query

    # Remove the consecutive user messages from the end of message history
    trimmed_message_history = (
        message_history[:-consecutive_user_count]
        if consecutive_user_count > 0
        else message_history
    )

    # Grab the fixed message history (without the consecutive user messages we already processed)
    modified_message_history = get_multi_input_message_history(trimmed_message_history)

    return combined_query, modified_message_history, consecutive_user_message_ids


def clean_text(input_text: str) -> str:
    """
    입력 텍스트를 정리하여 특정 패턴을 제거하고 반복되는 자연어 구두점을 축소합니다.

    Args:
        input_text (str): 원본 입력 텍스트.

    Returns:
        str: 파이프라인에서 추가 처리를 위해 적합한 정리된 텍스트.
    """
    # List of patterns to replace
    not_allowed_patterns = [
        (r"__+", ""),  # Replace multiple underscores with an empty string
    ]

    cleaned_text = input_text

    # Apply each pattern replacement
    for pattern, replacement in not_allowed_patterns:
        cleaned_text = re.sub(pattern, replacement, cleaned_text)

    # Collapse repeated occurrences of natural language punctuation only
    cleaned_text = re.sub(r"([?!.,]){2,}", r"\1", cleaned_text)

    # Collapse multiple spaces into a single space
    cleaned_text = re.sub(r"\s+", " ", cleaned_text)

    # Strip leading/trailing whitespace
    cleaned_text = cleaned_text.strip()

    return cleaned_text


def retry_function(func, *args, max_retries=3, delay=0.1, **kwargs):
    """
    Retries a function up to max_retries times if an exception is raised.

    Args:
        func (callable): The function to retry.
        *args: Positional arguments for the function.
        max_retries (int): Maximum number of retries.
        delay (float): Delay (in seconds) between retries.
        **kwargs: Keyword arguments for the function.

    Returns:
        The result of the function if successful.

    Raises:
        Exception: The last exception raised if the function fails after retries.
    """
    for attempt in range(1, max_retries + 1):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            print(f"Attempt {attempt} failed: {e}")
            if attempt == max_retries:
                raise
            time.sleep(delay)


def format_response_content(content: str) -> str:
    """
    브라우저 표시를 위해 콘텐츠를 형식화합니다.

    Args:
        content (str): 원본 콘텐츠.

    Returns:
        str: 형식화된 콘텐츠.
    """
    return content.replace("\r\n", "\n").replace("\r", "\n").replace("\n", "<br>")


def process_image_file(file: InMemoryUploadedFile) -> Dict[str, str | Dict[str, str]]:
    """
    업로드된 이미지 파일을 AI 모델에 필요한 형식으로 처리합니다.

    Args:
        file (InMemoryUploadedFile): 처리할 업로드된 이미지 파일.

    Returns:
        Dict[str, str]: 처리된 이미지 데이터가 포함된 사전.

    Raises:
        Exception: 이미지 처리 중 오류가 발생한 경우.
    """
    # Read the file content
    file.seek(0)  # Ensure we're at the start of the file
    image_data = base64.b64encode(file.read()).decode("utf-8")

    # Get the correct MIME type
    content_type = file.content_type
    if not content_type:
        # Fallback to guess from filename if content_type is not available
        content_type, _ = mimetypes.guess_type(file.name)
        if not content_type:
            content_type = "image/jpeg"  # Default fallback

    # Construct the data URI
    data_uri = f"data:{content_type};base64,{image_data}"

    return {"type": "image_url", "image_url": {"url": data_uri}}


def channel_intelligence_check(channel: str, intelligence: str) -> bool:
    """
    채널별 인텔리전스가 유효한지 확인합니다.

    Args:
        channel (str): 채널 이름.
        intelligence (str): 인텔리전스 이름.

    Returns:
        bool: 인텔리전스가 채널에 유효하면 True, 그렇지 않으면 False.
    """
    # Grab the allowed intelligence for the channel
    allowed_intelligences = Intelligence_V2.objects.filter(
        intelligence=intelligence, channel__contains=[channel]
    )
    if allowed_intelligences.exists():
        return True
    return False


def channel_sub_intelligence_check(channel: str, sub_intelligence: str) -> bool:
    """
    채널별 인텔리전스가 유효한지 확인합니다.

    Args:
        channel (str): 채널 이름.
        sub_intelligence (str): 서브 인텔리전스 이름.

    Returns:
        bool: 인텔리전스가 채널에 유효하면 True, 그렇지 않으면 False.
    """
    # Grab the allowed sub_intelligence for the channel
    allowed_sub_intelligences = Intelligence_V2.objects.filter(
        sub_intelligence=sub_intelligence, channel__contains=[channel]
    )
    if allowed_sub_intelligences.exists():
        return True
    return False


def remove_markdown_images(text):
    # Regular expression to match Markdown image syntax ![alt text](image_url)
    image_regex = r"!\[.*?\]\(.*?\)"
    # Replace all occurrences of the image syntax with an empty string
    cleaned_text = re.sub(image_regex, "", text)
    return cleaned_text


def parse_timing_logs(timing_logs):
    modules = {}

    for section_name, elapsed_time in timing_logs:
        # Check if section_name contains <br>
        if "<br>" in section_name:
            # Extract job_name from section_name
            match = re.search(r"<br> - ([^\.]+)\.", section_name)
            if match:
                job_name = match.group(1).split("__")[0]
            else:
                job_name = section_name
        else:
            job_name = section_name

        # Initialize module if not already present
        if job_name not in modules:
            modules[job_name] = {"name": job_name, "executions": []}

        # Append the execution duration
        modules[job_name]["executions"].append({"duration": elapsed_time})

    # Convert the modules dictionary to a list
    return list(modules.values())


def modify_keyword_for_web_search(keywords: list, country_code: str) -> list:
    """
    키워드 리스트를 수정합니다.
    """
    should_add_samsung = False
    keywords = keywords.copy()

    if country_code == "KR":
        if "삼성" in keywords:
            keywords.remove("삼성")
            keywords.insert(0, "삼성")
        else:
            for keyword in keywords:
                if "삼성" not in keyword.lower():
                    should_add_samsung = True
                    break
            if should_add_samsung:
                keywords.insert(0, "삼성")
    else:
        samsung_index = None
        for i, keyword in enumerate(keywords):
            if keyword.lower() == "samsung":
                samsung_index = i
                break

        if samsung_index is not None:
            keywords.pop(samsung_index)
            keywords.insert(0, "Samsung")
        else:
            for keyword in keywords:
                if "samsung" not in keyword.lower():
                    should_add_samsung = True
                    break
            if should_add_samsung:
                keywords.insert(0, "Samsung")

    return keywords


def get_log_intelligence(intelligence_data, sub_intelligence_data):
    """
    Determines the proper intelligence to store for log
    """
    if not intelligence_data:
        return None, None

    # Get the first intelligence that is not GENERAL_INFORMATION
    for query, value in intelligence_data.items():
        if value == intelligences.GENERAL_INFORMATION:
            continue
        return value, sub_intelligence_data.get(query)

    # If all are GENERAL_INFORMATION, return GENERAL_INFORMATION
    return intelligences.GENERAL_INFORMATION, sub_intelligences.GENERAL_INFORMATION


def get_first_or_string(item_dict, key, default=""):
    """Helper function to get the first item of a list or the value itself if it's not a list"""
    value = item_dict.get(key, default)
    if isinstance(value, list) and len(value) > 0:
        return str(value[0])
    elif value is None:
        return default
    else:
        return str(value)


def get_product_line_product_name(product_dict: dict, country_code: str):
    if country_code == "KR":
        DA_business_unit_list = ["R", "E", "W", "D", "NL", "P", "M3", "F", "M"]

        # Check if all category fields are available (1,2,3)
        if not all(product_dict.get(f"category_lv{i}") for i in range(1, 4)):
            product_dict["product_name"] = ""
            product_dict["product_line"] = ""
            return

        # Build filter dynamically
        filter_query = (
            Q(product_category_lv1=product_dict.get("category_lv1", ""))
            & Q(product_category_lv2=product_dict.get("category_lv2", ""))
            & Q(product_category_lv3=product_dict.get("category_lv3", ""))
        )

        # Only add mdl_code filter if code is available
        if "code" in product_dict and product_dict["code"]:
            filter_query &= Q(mdl_code=product_dict["code"])

        # Filter the Product Category table
        filtered_products = product_category.objects.filter(filter_query)

        if filtered_products.exists():
            first_product = filtered_products.first()

            # Check if the business_unit is in the provided list
            if first_product.business_unit in DA_business_unit_list:
                product_dict["product_name"] = first_product.disp_lv3
            else:
                product_dict["product_name"] = product_dict.get("category_lv3", "")

            # Update the input_dict with product_line
            product_dict["product_line"] = first_product.disp_lv2
        else:
            product_dict["product_name"] = ""
            product_dict["product_line"] = ""
    else:
        # For non-KR countries, use the provided product name
        product_dict["product_name"] = product_dict.get("category_lv3", "")
        product_dict["product_line"] = product_dict.get("category_lv2", "")


def get_product_division(product_dict: dict, country_code: str):
    """
    Get the product division based on the product category and country code.
    """
    # Initialize the product_division in the product_dict
    product_dict["product_division"] = []

    # Update the product_division based on the country code
    if country_code == "KR":
        # For KR, use the product_category table to get the division
        filter_query = (
            Q(product_category_lv1=product_dict.get("category_lv1", ""))
            & Q(product_category_lv2=product_dict.get("category_lv2", ""))
            & Q(product_category_lv3=product_dict.get("category_lv3", ""))
        )

        # Only add mdl_code filter if code is available
        if "code" in product_dict and product_dict["code"]:
            filter_query &= Q(mdl_code=product_dict["code"])

        # Filter the Product Category table
        filtered_products = product_category.objects.filter(filter_query)

        if filtered_products.exists():
            # Update the product_division value to be the default MD value
            product_dict["product_division"] = ["MD"]

            # Get the first product from the filtered results
            first_product = filtered_products.first()

            # Grab the goods id
            goods_id = first_product.goods_id

            # Check if the business_unit is in the provided list
            business_unit_mapping = {
                "DA": ["W", "E", "F", "M", "H", "R", "NL"],
                "PRINTING_SOLUTION": ["D"],
                "MX": ["Q", "L"],
                "VD": ["C"],
                "HARMON": ["HC", "HP"],
                "DS": ["U"],
                "LED": ["M3"],
            }

            # Check if the goods id is a set product
            goods_cstrt_data = goods_cstrt_info.objects.filter(
                goods_id=goods_id, goods_cstrt_gb_cd="10"
            )
            if goods_cstrt_data.exists():
                # If it is a set product, grab all the goods ids associated with the set
                goods_ids = goods_cstrt_data.values_list("cstrt_goods_id", flat=True)
                # Grab all the division for the goods ids
                product_items = product_category.objects.filter(goods_id__in=goods_ids)

                division_set = set()
                if product_items.exists():
                    for item in product_items:
                        for division, business_units in business_unit_mapping.items():
                            if item.business_unit in business_units:
                                division_set.add(division)
                                break

                if division_set:
                    # If there are multiple divisions, set the product_division to a list of divisions
                    product_dict["product_division"] = list(division_set)

            # If it is not a set product grab the division from the first product
            else:
                for division, business_units in business_unit_mapping.items():
                    if first_product.business_unit in business_units:
                        product_dict["product_division"] = [division]
                        break
    # For non-KR countries:
    else:
        # For non-KR countries, use the division table
        filter_query = (
            Q(category_lv1=product_dict.get("category_lv1", ""))
            & Q(category_lv2=product_dict.get("category_lv2", ""))
            & Q(category_lv3=product_dict.get("category_lv3", ""))
            & Q(country_code=country_code)
        )

        # Only add model_code filter if code is available
        if "code" in product_dict and product_dict["code"]:
            filter_query &= Q(model_code=product_dict["code"])

        # Filter the uk_product_division_map table
        filtered_products = uk_product_division_map.objects.filter(filter_query)

        if filtered_products.exists():
            # Update the product_division value to be the default MD value
            product_dict["product_division"] = ["MD"]

            first_product = filtered_products.first()

            # Grab the model code
            model_code = first_product.model_code

            # Check if the model code is a set product
            product_cstrt_data = uk_product_cstrt_info.objects.filter(
                model_code=model_code
            )

            if product_cstrt_data.exists():
                # If it is a set product, grab all the model codes associated with the set
                model_codes = product_cstrt_data.values_list(
                    "cstrt_model_code", flat=True
                )
                # Grab all the division for the model codes
                product_items = uk_product_division_map.objects.filter(
                    model_code__in=model_codes
                )

                division_set = set()
                if product_items.exists():
                    for item in product_items:
                        if item.division:
                            division_set.add(item.division)

                if division_set:
                    # If there are multiple divisions, set the product_division to a list of divisions
                    product_dict["product_division"] = list(division_set)

            # If it is not a set product, grab the division from the first product
            else:
                if first_product.division:
                    product_dict["product_division"] = [first_product.division]


def get_subsidiary(channel, country_code):
    """
    Get the subsidiary based on the channel and country
    """
    subsidiary = (
        Channel.objects.filter(channel=channel, country_code=country_code)
        .values_list("subsidiary", flat=True)
        .first()
    )
    return subsidiary or ""


def get_site_cd(channel, country_code):
    """
    Get the site_cd based on the channel and country
    """
    site_cd = (
        Channel.objects.filter(channel=channel, country_code=country_code)
        .values_list("site_cd", flat=True)
        .first()
    )
    return site_cd or ""


def get_default_language(channel, country_code):
    """
    Get the default language based on the channel and country
    """
    default_language = (
        Channel.objects.filter(channel=channel, country_code=country_code)
        .values_list("language", flat=True)
        .first()
    )
    return default_language or "en"  # Default to English if not found


def clean_chunk(chunk: str):
    """
    Clean the chunk by removing HTML tags, URLs, and email addresses
    """
    if not isinstance(chunk, str):
        return ""

    # 순서: 정규화 -> HTML/URL 제거 -> 이모지 제거 -> 반복 문자 축소 -> 기본 정제
    # 유니코드 정규화
    chunk = unicodedata.normalize("NFKC", chunk)

    # HTML 태그, URL, 이메일 제거, 마크다운 이미지 제거
    chunk = re.compile(r"<.*?>").sub("", chunk)
    chunk = re.compile(r"https?://\S+|www\.\S+").sub("", chunk)
    chunk = re.compile(r"\S+@\S+\.\S+").sub("", chunk)
    chunk = remove_markdown_images(chunk)

    # 이모지 제거
    chunk = emoji.replace_emoji(chunk, replace="")

    # 반복되는 문자 줄이기
    # Handle consecutive repeated characters
    chunk = re.sub(r"(.)\1{4,}", r"\1\1", chunk)
    # Handle spaced repeated characters
    chunk = re.sub(r"(.)(?:\s+\1){4,}", r"\1 \1", chunk)

    # Remove newline characters and replace them with spaces
    chunk = re.sub(r"[\n\r\t\f\v]", " ", chunk)

    # Collapse multiple spaces into a single space
    chunk = re.sub(r"\s+", " ", chunk)

    # Strip leading/trailing whitespace
    chunk = chunk.strip()

    return chunk


def unique_dicts_json(dicts):
    seen = set()
    unique = []
    for d in dicts:
        j = json.dumps(d, sort_keys=True)
        if j not in seen:
            seen.add(j)
            unique.append(d)
    return unique


def make_web_search_inputs(
    top_query, intelligence, sub_intelligence, filtered_selected_extended, field
):
    """_summary_

    Args:
        top_query (str)
        intelligence (str)
        sub_intelligence (str)
        filtered_selected_extended (object)
        field (str)

    Returns:
        list dictionary

    설명:
    complement기준 제품 코드를 웹검색에 활용하도록 추가, top query는 그대로 사용
    """
    bing_inputs = []
    n_item = 3 if len(filtered_selected_extended) == 1 else 1
    if intelligence == intelligences.ERROR_AND_FAILURE_RESPONSE:
        for item in filtered_selected_extended["extended_info_result"]:
            if (
                field == "product_option"
            ):  # _30_orchestrator_NER.NerField.PRODUCT_FUNCTION:
                # TODO: function 검색 후 무의미하면 제거
                bing_inputs.append(
                    {
                        "query": [top_query, ""],
                        "intelligence": intelligence,
                        "sub_intelligence": sub_intelligence,
                        "type": "CS API",
                    }
                )
            for product_code in item.get("extended_info", ""):
                if product_code:
                    if item.get("category_lv1", "") == "not_found":
                        bing_inputs.append(
                            {
                                "query": [top_query, ""],
                                "intelligence": intelligence,
                                "sub_intelligence": sub_intelligence,
                                "type": "CS API",
                            }
                        )
                    else:
                        bing_inputs.append(
                            {
                                "query": [top_query, item.get("category_lv3", "")],
                                "intelligence": intelligence,
                                "sub_intelligence": sub_intelligence,
                                "type": "CS API",
                            }
                        )
    else:
        for item in filtered_selected_extended["extended_info_result"]:
            if (
                field == "product_option"
            ):  # _30_orchestrator_NER.NerField.PRODUCT_FUNCTION:
                bing_inputs.append(
                    {
                        "query": (
                            item["mapping_code"][0]
                            if isinstance(item["mapping_code"], list)
                            else item["mapping_code"]
                        ),
                        "intelligence": intelligence,
                        "sub_intelligence": sub_intelligence,
                        "type": "function",
                    }
                )
            for product_code in item.get("extended_info", "")[:n_item]:
                if product_code:
                    if item.get("category_lv1", "") == "not_found":
                        bing_inputs.append(
                            {
                                "query": product_code,
                                "intelligence": intelligence,
                                "sub_intelligence": sub_intelligence,
                                "type": "product",
                            }
                        )
                    else:
                        bing_inputs.append(
                            {
                                "query": product_code,
                                "intelligence": intelligence,
                                "sub_intelligence": sub_intelligence,
                                "type": "code",
                            }
                        )

        bing_inputs.append(
            {
                "query": top_query,
                "intelligence": intelligence,
                "sub_intelligence": sub_intelligence,
                "type": "top_query",
            }
        )
    return bing_inputs


async def _evaluate_all(
    query: str, data: List[Dict], max_concurrency: int
) -> List[Dict]:
    sem = asyncio.Semaphore(max_concurrency)
    tasks = [_eval_chunk(sem, query, chunk, idx) for idx, chunk in enumerate(data)]
    results = await asyncio.gather(*tasks)
    return results


async def _evaluate_all_v2(
    query, data: List[Dict], max_concurrency: int, similarity_check: bool
) -> List[Dict]:
    sem = asyncio.Semaphore(max_concurrency)
    tasks = [
        _eval_chunk(sem, q, chunk, idx, similarity_check)
        for idx, (q, chunk) in enumerate(zip(query, data))
    ]
    results = await asyncio.gather(*tasks)
    return results


nest_asyncio.apply()


def run_retrieval_evaluation_parallel(
    query,
    data,
    max_concurrency: int = 5,
    list_compare: bool = False,
    similarity_check: bool = False,
) -> List[Dict]:
    """
    query: 사용자 질문
    data:  [{'rank':…, 'text_data':…}, …]
    returns: relevance==TRUE인 data 리스트
    """
    # asyncio.run will handle loop creation/teardown for you
    if not list_compare:
        return asyncio.run(_evaluate_all(query, data, max_concurrency))
    else:
        return asyncio.run(
            _evaluate_all_v2(query, data, max_concurrency, similarity_check)
        )


def should_show_supplement_type(intelligence, sub_intelligence, supplement_type):
    """
    Check if the supplement type should be shown based on intelligence and sub_intelligence.

    Args:
        intelligence (str): The intelligence type.
        sub_intelligence (str): The sub-intelligence type.
        supplement_type (str): The supplement type to check.
                              Valid values: "product_card", "related_query",
                              "hyperlink", "media", "map"

    Returns:
        bool: True if the supplement type should be shown, False otherwise.

    Raises:
        ValueError: If supplement_type is not valid.
        ObjectDoesNotExist: When no matching intelligence record is found.
    """
    # Validate the supplement_type
    valid_types = ["product_card", "related_query", "hyperlink", "media", "map"]
    if supplement_type not in valid_types:
        raise ValueError(
            f"Invalid supplement type: {supplement_type}. Valid types are: {valid_types}"
        )

    # Ensure intelligence and sub_intelligence are valid
    if not intelligence or not sub_intelligence:
        return False

    # Query the Intelligence_V2 model for the matching record
    intel_record = Intelligence_V2.objects.get(
        intelligence=intelligence, sub_intelligence=sub_intelligence
    )

    # Return the boolean value for the requested supplement type
    return getattr(intel_record, supplement_type, False)


def should_show_supplement_type_by_intelligence(
    intelligence: str, supplement_type: str
) -> bool:
    """
    Check if the supplement type should be shown based on intelligence.

    Args:
        intelligence (str): The intelligence type.
        supplement_type (str): The supplement type to check.
                              Valid values: "product_card", "media"

    Returns:
        bool: True if the supplement type should be shown, False otherwise.

    Raises:
        ValueError: If supplement_type is not valid.
        ObjectDoesNotExist: When no matching intelligence record is found.
    """
    # Validate the supplement_type
    valid_types = ["product_card", "media", "related_query", "hyperlink"]
    if supplement_type not in valid_types:
        raise ValueError(
            f"Invalid supplement type: {supplement_type}. Valid types are: {valid_types}"
        )

    # Ensure intelligence is valid
    if not intelligence:
        return False

    # Query the Intelligence_V2 model for the matching record
    intel_record = Intelligence_V2.objects.filter(
        intelligence=intelligence
    ).values_list(supplement_type, flat=True)

    # Return the boolean if all records have the supplement type set to True
    return all(intel_record) if intel_record else False


def get_prompt_from_obj(
    category_lv1: str | None = None,
    category_lv2: str | None = None,
    channel: str | None = None,
    country_code: str | None = None,
    response_type: str | None = None,
    tag: str | None = None,
):
    prompt_template_filter_criteria = Q(active=True)
    if category_lv1:
        prompt_template_filter_criteria &= Q(category_lv1=category_lv1)
    if category_lv2:
        if category_lv2 == "null":
            prompt_template_filter_criteria &= Q(category_lv2__isnull=True)
        else:
            prompt_template_filter_criteria &= Q(category_lv2=category_lv2)
    if country_code:
        prompt_template_filter_criteria &= Q(country_code=country_code)
    if response_type:
        prompt_template_filter_criteria &= Q(response_type=response_type)
    if tag:
        if tag == "null":
            prompt_template_filter_criteria &= Q(tag__isnull=True)
        else:
            prompt_template_filter_criteria &= Q(tag=tag)
    if channel:
        if channel == "null":
            prompt_template_filter_criteria &= Q(channel_filter__isnull=True)
        else:
            prompt_template_filter_criteria &= Q(channel_filter__contains=[channel])

    prompt_obj = Prompt_Template.objects.filter(prompt_template_filter_criteria).first()

    # Check if the prompt object is None or if the prompt is empty
    # If so, return None
    if not prompt_obj or not prompt_obj.prompt:
        return None

    prompt = prompt_obj.prompt
    return prompt


def truncate_text_data_for_display(
    dict_list,
    max_length=100,
    max_list_size=5,
    truncate_fields=None,
):
    """
    Creates a copy of each dictionary with truncated 'text_data' fields for display purposes.

    Args:
        dict_list: List of dictionaries containing 'text_data' field
        max_length: Maximum length of the truncated text (default: 100)

    Returns:
        A new list of dictionaries with truncated 'text_data' fields
    """
    # If truncate_fields is None, use default fields
    if truncate_fields is None:
        truncate_fields = ["text_data", "model_code"]

    truncated_list = []
    suffix = ". . . (more)"

    for d in dict_list:
        # Create a shallow copy of the dictionary
        truncated_dict = d.copy()

        # Check if the fields in truncate_field are present in the dictionary
        for truncate_field in truncate_fields:
            if truncate_field not in truncated_dict:
                continue

            # Check if the field is a string and truncate it if necessary
            if isinstance(truncated_dict[truncate_field], str):
                text = truncated_dict[truncate_field]

                # Truncate text if longer than max_length
                if len(text) > max_length:
                    truncated_dict[truncate_field] = text[:max_length] + suffix
            elif isinstance(truncated_dict[truncate_field], list):
                list_value = truncated_dict[truncate_field]

                # Truncate the list if it exceeds max_list_size
                if len(list_value) > max_list_size:
                    truncated_dict[truncate_field] = list_value[:max_list_size] + [
                        suffix
                    ]

        truncated_list.append(truncated_dict)

    return truncated_list


def get_user_query(
    translated_query_data: dict,
    rewritten_queries: List[str],
    cs_queries: List[str],
) -> str:
    """
    Get the user query based on the translated queries, rewritten queries,
    and CS intention queries.

    Args:
        translated_query_data (dict): The translated query data.
        rewritten_queries (List[str]): The rewritten queries.
        cs_intention_queries (List[str]): The CS intention queries.

    Returns:
        str: The user query.
    """
    # Make sure all the translations are in the translated_query_data
    if not all(query in translated_query_data for query in rewritten_queries):
        raise ValueError(
            "All rewritten queries and expanded queries must be in the translated query data."
        )

    # Helper function to just combine the translated rewritten queries
    def combine_translated_rewritten_queries():
        combined_queries = []
        for rewritten_query in rewritten_queries:
            # Append the translated rewritten query
            combined_queries.append(translated_query_data[rewritten_query])

        return combined_queries

    # If cs_intention_queries is empty, return translated queries joined
    if not cs_queries:
        combined_queries = combine_translated_rewritten_queries()
        return ". ".join(combined_queries)

    # If there are more CS intention queries than rewritten queries,
    # Raise an error
    if len(cs_queries) > len(rewritten_queries):
        raise ValueError("CS intention queries cannot be more than rewritten queries.")

    # If all cs_intention_queries are found in rewritten_queries,
    # Return empty string as the queries were not processed by Rubicon
    if set(rewritten_queries).issubset(set(cs_queries)):
        return ""

    # Find all the index of the cs_intention_queries in rewritten_queries
    cs_intention_indices = []
    for cs_query in cs_queries:
        try:
            index = rewritten_queries.index(cs_query)
            cs_intention_indices.append(index)
        except ValueError:
            # Query not found in rewritten_queries, raise an error
            raise ValueError(
                f"CS intention query '{cs_query}' not found in rewritten queries."
            )

    # Filter out the translated queries at the indices found
    rewritten_queries = [
        rewritten_queries[i]
        for i in range(len(rewritten_queries))
        if i not in cs_intention_indices
    ]

    # Return the combined translated queries of the remaining rewritten queries
    combined_queries = combine_translated_rewritten_queries()
    return ". ".join(combined_queries)


def get_user_content(response_path: str, user_query: str, original_query: str) -> str:
    """
    Determine which query was used for user content when generating the response.
    """
    # Get the input prompt data mapping
    input_info_dict = input_prompt_data_mapping.get(response_path, {})

    # Get the open_ai_input info from the input_info_dict
    open_ai_input_info = input_info_dict.get("open_ai_input", {})

    # Check if original query is in the open_ai_input_info
    if "original_query" in open_ai_input_info:
        # If original query is in the open_ai_input_info, return it
        return original_query
    # Otherwise, return the user query
    return user_query


def clean_final_response(full_response: str) -> Tuple[bool, str]:
    """
    Clean the final response by removing specific patterns and returning the cleaned response.
    Args:
        full_response (str): The full response string to be cleaned.
    Returns:
        str: The cleaned response string.
    """
    # First clean the markdown and EOS tags
    full_response = (
        full_response.replace("```markdown<br>", "").replace("```<EOS>", "").strip()
    )

    # Define the regex pattern to search for
    error_stream_termination_pattern = r"\[STREAM ERROR:.*?\]"
    moderation_stream_termination_pattern = r"\[STREAM TERMINATED:.*?\]"

    # Check for stream pattern
    error_stream_match = re.search(error_stream_termination_pattern, full_response)
    moderation_stream_match = re.search(
        moderation_stream_termination_pattern, full_response
    )
    if error_stream_match:
        # Extract everything after the pattern
        cleaned_response = full_response[error_stream_match.end() :]
        return False, cleaned_response
    elif moderation_stream_match:
        # Extract everything after the pattern
        cleaned_response = full_response[moderation_stream_match.end() :]
        return True, cleaned_response

    # If no pattern is found, return the original response
    return False, full_response


def should_use_base(sub_intelligence: str) -> bool:
    # Make sure sub_intelligence is not None or empty
    if not sub_intelligence:
        return True

    try:
        # Fetch the Intelligence_V2 object for the given sub_intelligence
        intelligence_data = Intelligence_V2.objects.filter(
            sub_intelligence=sub_intelligence
        ).first()
        return intelligence_data.base if intelligence_data else True
    except Exception:
        # If there's an error in fetching the intelligence data, return True
        # This ensures that the default behavior is to use the base prompt
        return True


def get_web_link(
    rewritten_queries: List[str],
    product_log: list,
    channel: str,
    country_code: str,
    intelligence_data: dict,
    sub_intelligence_data: dict,
    ner_data: dict,
):
    """
    Generate web links based on the product log, channel, country code, intelligence data,
    sub-intelligence data, and NER data.

    Args:
        rewritten_queries (List[str]): List of rewritten queries.
        product_log (list): List of product logs.
        channel (str): The channel name.
        country_code (str): The country code.
        intelligence_data (dict): The intelligence data.
        sub_intelligence_data (dict): The sub-intelligence data.
        ner_data (dict): The NER data.

    Returns:
        list: A list of web links.
    """
    web_links = []

    # Grab all the web links with the country code and channel
    web_link_objects = Web_Link.objects.filter(
        country_code=country_code,
        channel__contains=[channel],
    )

    # First check for the product line web links
    # Get all the product lines from the product log
    product_lines = set(
        [
            product_item["product_line"]
            for product_item in product_log
            if "product_line" in product_item
        ]
    )

    # Get the product line condition for the query
    product_line_condition = None
    if not product_lines:
        product_line_condition = Q(product_line__isnull=True)
    else:
        # If there are product lines, create a condition for them
        product_line_condition = Q(product_line__in=product_lines)

    # Iterate through the rewritten queries to make sure the dependency is met
    for query in rewritten_queries:
        # Skip if the query is not in intelligence_data or sub_intelligence_data
        if query not in intelligence_data or query not in sub_intelligence_data:
            continue

        # Get the intelligence and sub_intelligence conditions for the query
        intelligence_condition = Q(intelligence__contains=[intelligence_data[query]])
        sub_intelligence_condition = Q(
            sub_intelligence__contains=[sub_intelligence_data[query]]
        )

        # Check the web links for the product lines, intelligence, and sub_intelligence conditions (not NER)
        combined_conditions = (
            product_line_condition
            & (intelligence_condition | sub_intelligence_condition)
            & Q(ner_field__isnull=True)
        )

        # Filter the web links based on the combined conditions
        filtered_web_links = web_link_objects.filter(combined_conditions)

        # Get the link and description value from the filtered web links
        for web_link in filtered_web_links:
            # Append the web link as markdown format
            web_links.append(f"[{web_link.description}]({web_link.link})")

        # Check for ner and (sub) intelligence dependent web links
        if query not in ner_data:
            continue

        # Get the ner fields from the ner_data
        ner_fields = set(
            [ner_item["field"] for ner_item in ner_data[query] if "field" in ner_item]
        )

        # Create the ner condition for the query
        ner_field_condition = Q(ner_field__overlap=list(ner_fields))

        # Combine the ner condition with the intelligence and sub_intelligence conditions
        combined_conditions = ner_field_condition & (
            intelligence_condition | sub_intelligence_condition
        )

        # Filter the web links based on the combined conditions
        filtered_web_links = web_link_objects.filter(combined_conditions)

        # Get the link and description value from the filtered web links
        for web_link in filtered_web_links:
            # Append the web link as markdown format
            web_links.append(f"[{web_link.description}]({web_link.link})")

    # Remove duplicates from the web links
    web_links = list(set(web_links))

    # Return the web links
    return web_links


def get_product_log(query: str, extended_info_result: list, country_code: str) -> list:
    """
    Extract product log from the extended info result.
    General logic is to group by id (single item or series) and then depending on the size and number of the group(s),
    extract the products.
    If there is only one group and 1 item, extract 3 products.
    If there is only one group and more than 1 item, extract one product from each item.
    If there are more than one group, extract 1 product from each item in each group.
    The extracted products must have product code

    Args:
        extended_info_result (list): List of extended info results.

    Returns:
        list: A list of product logs.
    """
    product_log = []
    product_group = {}
    group_num = -1
    previous_id = 0

    # First group by id
    # A group is where the id starts from 0 and increments by 1
    # If the next id is 0, it means a new group starts
    for item in extended_info_result:
        item_id = item.get("id", 0)
        # If the item_id is 0, it means a new group starts
        if item_id == 0:
            group_num += 1
            previous_id = 0
        # If the item_id is 1 more than the previous id, it means the group continues
        elif item_id == previous_id + 1:
            previous_id = item_id
        # If the item_id is not 0 or 1 more than the previous id, it means a new group starts
        else:
            group_num += 1
            previous_id = item_id

        if group_num not in product_group:
            product_group[group_num] = []
        product_group[group_num].append(item)

    # Now we have the items by group, validate each items
    # Make sure the items have a product code
    for group_num, group_items in product_group.items():
        validated_product_dicts = []
        # Iterate through the group items and check if they have a product code
        for item in group_items:
            # Check if the item has an extended_info field and it is not empty
            if (
                "extended_info" in item
                and item["extended_info"]
                and isinstance(item["extended_info"], list)
            ):
                validated_product_dicts.append(item)

        # Update the group items with the validated product dicts
        product_group[group_num] = validated_product_dicts

    # Remove groups that have no items
    product_group = {k: v for k, v in product_group.items() if v}

    # If there are no groups, return an empty list
    if not product_group:
        return []

    # If there is only one group, extract the products from that group
    if len(product_group) == 1:
        # Get the first group
        group_items = list(product_group.values())[0]
        # If there is only one item in the group, extract 3 products
        if len(group_items) == 1:
            for product_code in group_items[0]["extended_info"][:3]:
                # Safely get the rest of the fields, converting any lists to their first item
                product_dict = {
                    "query": query,
                    "code": product_code,
                    "mapping_code": get_first_or_string(group_items[0], "mapping_code"),
                    "category_lv1": get_first_or_string(group_items[0], "category_lv1"),
                    "category_lv2": get_first_or_string(group_items[0], "category_lv2"),
                    "category_lv3": get_first_or_string(group_items[0], "category_lv3"),
                }
                # Get the product name and product line based on the country code
                get_product_line_product_name(product_dict, country_code)
                # Get the product division based on the product category and country code
                get_product_division(product_dict, country_code)
                # Append the product_dict to the product_log
                product_log.append(product_dict)

        # If there are more than one item in the group, extract one product from each item
        else:
            for item in group_items:
                # Safely get the rest of the fields, converting any lists to their first item
                product_dict = {
                    "query": query,
                    "code": get_first_or_string(item, "extended_info"),
                    "mapping_code": get_first_or_string(item, "mapping_code"),
                    "category_lv1": get_first_or_string(item, "category_lv1"),
                    "category_lv2": get_first_or_string(item, "category_lv2"),
                    "category_lv3": get_first_or_string(item, "category_lv3"),
                }
                # Get the product name and product line based on the country code
                get_product_line_product_name(product_dict, country_code)
                # Get the product division based on the product category and country code
                get_product_division(product_dict, country_code)
                # Append the product_dict to the product_log
                product_log.append(product_dict)

    # If there are more than one group, extract one product from each item in each group
    else:
        # Convert product_group values to a list for easier indexing
        group_lists = list(product_group.values())

        # Find the maximum number of items in any group
        max_items = max(len(group) for group in group_lists)

        # Iterate in a round-robin pattern
        for item_index in range(max_items):
            for group_items in group_lists:
                # Check if this group has an item at the current index
                if item_index < len(group_items):
                    item = group_items[item_index]
                    # Safely get the rest of the fields, converting any lists to their first item
                    product_dict = {
                        "query": query,
                        "code": get_first_or_string(item, "extended_info"),
                        "mapping_code": get_first_or_string(item, "mapping_code"),
                        "category_lv1": get_first_or_string(item, "category_lv1"),
                        "category_lv2": get_first_or_string(item, "category_lv2"),
                        "category_lv3": get_first_or_string(item, "category_lv3"),
                    }
                    # Get the product name and product line based on the country code
                    get_product_line_product_name(product_dict, country_code)
                    # Get the product division based on the product category and country code
                    get_product_division(product_dict, country_code)
                    # Append the product_dict to the product_log
                    product_log.append(product_dict)

    # Return the product log
    return product_log


def get_date_range_bounds(date_strings: list[str]) -> tuple[str, str]:
    """
    Given a list of date strings in one of:
      - 'YYYY'
      - 'YYYY-MM'
      - 'YYYY-MM-DD'
    Returns a tuple of (min_iso_utc, max_iso_utc) in "%Y-%m-%dT%H:%M:%SZ" format,
    where:
      'YYYY'      → range [YYYY-01-01T00:00:00Z, YYYY-12-31T23:59:59Z]
      'YYYY-MM'   → range [YYYY-MM-01T00:00:00Z, YYYY-MM-lastdayT23:59:59Z]
      'YYYY-MM-DD'→ range [that-dayT00:00:00Z, that-dayT23:59:59Z]
    """
    starts: list[datetime.datetime] = []
    ends: list[datetime.datetime] = []

    for s in date_strings:
        if not s:
            continue
        if re.fullmatch(r"\d{4}", s):
            year = int(s)
            start = datetime.datetime(year, 1, 1, 0, 0, 0, tzinfo=datetime.timezone.utc)
            end = datetime.datetime(
                year, 12, 31, 23, 59, 59, tzinfo=datetime.timezone.utc
            )
        elif re.fullmatch(r"\d{4}-\d{2}", s):
            year, month = map(int, s.split("-"))
            last_day = calendar.monthrange(year, month)[1]
            start = datetime.datetime(
                year, month, 1, 0, 0, 0, tzinfo=datetime.timezone.utc
            )
            end = datetime.datetime(
                year, month, last_day, 23, 59, 59, tzinfo=datetime.timezone.utc
            )
        elif re.fullmatch(r"\d{4}-\d{2}-\d{2}", s):
            year, month, day = map(int, s.split("-"))
            start = datetime.datetime(
                year, month, day, 0, 0, 0, tzinfo=datetime.timezone.utc
            )
            end = datetime.datetime(
                year, month, day, 23, 59, 59, tzinfo=datetime.timezone.utc
            )
        else:
            raise ValueError(f"Unrecognized date format: {s!r}")
        starts.append(start)
        ends.append(end)

    if not starts or not ends:
        raise ValueError("No valid dates provided")

    min_iso = min(starts).strftime("%Y-%m-%dT%H:%M:%SZ")
    max_iso = max(ends).strftime("%Y-%m-%dT%H:%M:%SZ")
    return min_iso, max_iso
