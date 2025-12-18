import random
import enum

from django.core.cache import cache

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from apps.rubicon_v3.__function._00_rubicon import RubiconChatFlow
from typing import Union, List


class SessionFlags(enum.Enum):
    TURNS_SINCE_RE_ASKED = "turns_since_re_asked"
    STORE_RE_ASKED = "store_re_asked"


class MessageFlags(enum.Enum):
    SHOW_SUPPLEMENT = "show_supplementary_info"
    SHOW_MEDIA = "show_media"
    SHOW_RELATED_QUERY = "show_related_query"
    SHOW_PRODUCT_CARD = "show_product_card"
    SHOW_HYPERLINK = "show_hyperlink"


class DjangoCacheClient:
    def __init__(self):
        self.client = cache

    def store(self, key, value, expiry_seconds=None):
        """
        캐시에 값을 저장합니다.

        Args:
            key (str): 캐시 키
            value (any): 저장할 값
            expiry_seconds (int, optional): 만료 시간(초)

        Returns:
            bool: 성공 여부
        """
        try:
            self.client.set(key, value, timeout=expiry_seconds)
            return True
        except Exception as e:
            raise ValueError(f"Error storing data in cache for key '{key}': {str(e)}")

    def get(self, key, default=None):
        """
        캐시에서 값을 가져옵니다.

        Args:
            key (str): 캐시 키
            default (any): 키가 없을 경우 반환할 기본값

        Returns:
            any: 저장된 값 또는 기본값
        """
        try:
            value = self.client.get(key)
            return value if value is not None else default
        except Exception as e:
            raise ValueError(f"Error accessing cache for key '{key}': {str(e)}")

    def update(self, key, value, expiry_seconds=None):
        """
        캐시의 값을 업데이트합니다.

        Args:
            key (str): 캐시 키
            value (any): 업데이트할 값

        Returns:
            bool: 성공 여부
        """
        try:
            # Attempt to replace the existing key-value pair
            if not self.client.touch(key):
                print(f"Key '{key}' not found, creating a new entry.")

            self.client.set(key, value, timeout=expiry_seconds)
            return True
        except Exception as e:
            raise ValueError(f"Error updating cache for key '{key}': {str(e)}")

    def exists(self, key):
        """
        캐시에 키가 존재하는지 확인합니다.

        Args:
            key (str): 캐시 키

        Returns:
            bool: 존재 여부
        """
        return self.client.get(key) is not None

    def touch_exists(self, key, expiry_seconds=None):
        """
        캐시의 키가 존재하는지 확인하고, 존재하면 만료 시간을 갱신합니다.

        Args:
            key (str): 캐시 키
            expiry_seconds (int, optional): 만료 시간(초)

        Returns:
            bool: 성공 여부
        """
        try:
            return self.client.touch(key, timeout=expiry_seconds)
        except Exception as e:
            raise ValueError(f"Error touching cache for key '{key}': {str(e)}")

    def delete(self, key):
        """
        캐시에서 키를 삭제합니다.

        Args:
            key (str): 캐시 키

        Returns:
            bool: 성공 여부
        """
        try:
            self.client.delete(key)
            return True
        except Exception as e:
            raise ValueError(f"Error deleting cache for key '{key}': {str(e)}")


class CacheKey:

    @classmethod
    def query_cache_key(cls, query, flow: "RubiconChatFlow"):
        return f"{query}__cache__{flow.input.channel}__{flow.input.country_code}"

    @classmethod
    def message_history(
        cls, flow_or_session_id: Union["RubiconChatFlow", str, int, float]
    ):
        if hasattr(flow_or_session_id, "input"):
            return f"{flow_or_session_id.input.session_id}__message_history"

        return f"{flow_or_session_id}__message_history"

    @classmethod
    def language(cls, flow_or_session_id: Union["RubiconChatFlow", str, int, float]):
        if hasattr(flow_or_session_id, "input"):
            return f"{flow_or_session_id.input.session_id}__language"

        return f"{flow_or_session_id}__language"

    @classmethod
    def debug_content(
        cls, flow_or_message_id: Union["RubiconChatFlow", str, int, float]
    ):
        if hasattr(flow_or_message_id, "input"):
            return f"{flow_or_message_id.input.message_id}__debug_content"

        return f"{flow_or_message_id}__debug_content"

    @classmethod
    def debug_unstructured_content(cls, flow: "RubiconChatFlow"):
        return f"{flow.input.message_id}__unstructured_content"

    @classmethod
    def debug_product_card(cls, flow: "RubiconChatFlow"):
        return f"{flow.input.message_id}__target_product"

    @classmethod
    def debug_timing_logs(
        cls, flow_or_message_id: Union["RubiconChatFlow", str, int, float]
    ):
        if hasattr(flow_or_message_id, "input"):
            return f"{flow_or_message_id.input.message_id}__timing_logs"

        return f"{flow_or_message_id}__timing_logs"

    @classmethod
    def media(cls, flow_or_message_id: Union["RubiconChatFlow", str, int, float]):
        if hasattr(flow_or_message_id, "input"):
            return f"{flow_or_message_id.input.message_id}__media"

        return f"{flow_or_message_id}__media"

    @classmethod
    def media_v2(cls, message_id: str):
        return f"{message_id}__media_v2"

    @classmethod
    def related_query(
        cls, flow_or_message_id: Union["RubiconChatFlow", str, int, float]
    ):
        if hasattr(flow_or_message_id, "input"):
            return f"{flow_or_message_id.input.message_id}__related_query"

        return f"{flow_or_message_id}__related_query"

    @classmethod
    def related_query_v2(cls, message_id: str):
        return f"{message_id}__related_query_v2"

    @classmethod
    def greeting_query(
        cls,
        channel: str = None,
        country_code: str = None,
        language: str = None,
        message_id: str = None,
    ):
        """
        Returns the cache key for greeting query based on channel, country code, language, and optional message_id.
        """
        if message_id:
            return f"greeting_query__{message_id}"

        return f"greeting_query__{channel}__{country_code}__{language}"

    @classmethod
    def product_card(
        cls, flow_or_message_id: Union["RubiconChatFlow", str, int, float]
    ):
        if hasattr(flow_or_message_id, "input"):
            return f"{flow_or_message_id.input.message_id}__product_card"

        return f"{flow_or_message_id}__product_card"

    @classmethod
    def product_card_v2(cls, message_id: str):
        return f"{message_id}__product_card_v2"

    @classmethod
    def response(
        cls,
        flow: "RubiconChatFlow",
        random_int_range: tuple = (0, 1),
    ):
        return f"response__{'__'.join(flow.orchestrator.rewritten_queries)}__{'simple' if flow.simple else 'informative'}__{random.randint(*random_int_range)}__{flow.orchestrator.language}__{flow.input.channel}__{flow.input.country_code}"

    @classmethod
    def loading_message(
        cls, flow_or_message_id: Union["RubiconChatFlow", str, int, float]
    ):
        if hasattr(flow_or_message_id, "input"):
            return f"{flow_or_message_id.input.message_id}__loading_message"

        return f"{flow_or_message_id}__loading_message"

    @classmethod
    def evaluation(cls, flow_or_message_id: Union["RubiconChatFlow", str, int, float]):
        if hasattr(flow_or_message_id, "input"):
            return f"{flow_or_message_id.input.message_id}__evaluation"

        return f"{flow_or_message_id}__evaluation"

    @classmethod
    def mentioned_products(
        cls, flow_or_session_id: Union["RubiconChatFlow", str, int, float]
    ):
        if hasattr(flow_or_session_id, "input"):
            return f"{flow_or_session_id.input.session_id}__mentioned_products"

        return f"{flow_or_session_id}__mentioned_products"

    @classmethod
    def session_title(
        cls, flow_or_session_id: Union["RubiconChatFlow", str, int, float]
    ):
        if hasattr(flow_or_session_id, "input"):
            return f"{flow_or_session_id.input.session_id}__session_title"

        return f"{flow_or_session_id}__session_title"

    @classmethod
    def multi_input(cls, flow_or_message_id: Union["RubiconChatFlow", str, int, float]):
        if hasattr(flow_or_message_id, "input"):
            return f"{flow_or_message_id.input.message_id}__multi_input"

        return f"{flow_or_message_id}__multi_input"

    @classmethod
    def goods_id_price(cls, country_code: str, id_list: List[str]):
        return f"{':'.join(id_list)}__{country_code}__price"

    @classmethod
    def siis_api_key(cls, country_code: str, op_type: str):
        return f"{country_code.upper()}__{op_type.upper()}__SiiS_API_KEY"

    @classmethod
    def siis_rubicon_uk_api_key(cls, country_code: str, op_type: str):
        return f"{country_code.upper()}__{op_type.upper()}__SiiS_Rubicon_UK_API_KEY"

    @classmethod
    def siis_rubicon_svc_api_key(cls, country_code: str, op_type: str):
        return f"{country_code.upper()}__{op_type.upper()}__SiiS_Rubicon_SVC_API_KEY"

    @classmethod
    def hyperlink(cls, flow_or_message_id: Union["RubiconChatFlow", str, int, float]):
        if hasattr(flow_or_message_id, "input"):
            return f"{flow_or_message_id.input.message_id}__hyperlink"

        return f"{flow_or_message_id}__hyperlink"

    @classmethod
    def user_info(
        cls,
        sa_id: str,
        country_code: str,
    ):
        return f"user_info__{sa_id}__{country_code}"

    @classmethod
    def user_product_info(cls, sa_id: str, country_code: str):
        return f"user_product_info__{sa_id}__{country_code}"

    @classmethod
    def session_flags(
        cls, flow_or_session_id: Union["RubiconChatFlow", str, int, float]
    ):
        if hasattr(flow_or_session_id, "input"):
            return f"{flow_or_session_id.input.session_id}__session_flags"

        return f"{flow_or_session_id}__session_flags"

    @classmethod
    def message_flags(
        cls, flow_or_message_id: Union["RubiconChatFlow", str, int, float]
    ):
        if hasattr(flow_or_message_id, "input"):
            return f"{flow_or_message_id.input.message_id}__message_flags"

        return f"{flow_or_message_id}__message_flags"

    @classmethod
    def moderator_prohibited_words_data(cls):
        """
        Returns the cache key for storing moderator patterns.
        """
        return "moderator_pattern_data"

    @classmethod
    def moderator_validated_patterns(cls, word: str):
        """
        Returns the cache key for storing validated patterns for a specific word.
        """
        return f"moderator_validated_patterns__{word.lower()}"

    @classmethod
    def prohibited_patterns(cls, language: str):
        """
        Returns the cache key for storing prohibited patterns based on language.
        """
        return f"prohibited_patterns__{language}"

    @classmethod
    def pii_patterns(cls, country_code: str):
        """
        Returns the cache key for storing PII patterns based on country code.
        """
        return f"pii_patterns__{country_code}"

    @classmethod
    def session_initial_message_id(
        cls, flow_or_session_id: Union["RubiconChatFlow", str, int, float]
    ):
        if hasattr(flow_or_session_id, "input"):
            return f"{flow_or_session_id.input.session_id}__initial_message_id"

        return f"{flow_or_session_id}__initial_message_id"

    @classmethod
    def response_format_check(
        cls, query: str, session_id: str, country_code: str, test_type: str
    ):
        """
        Returns the cache key for response format check.
        """
        return (
            f"response_format_check__{query}__{test_type}__{country_code}__{session_id}"
        )

    @classmethod
    def welcome_message(cls, channel: str, country_code: str, language: str):
        """
        Returns the cache key for the welcome message based on channel, country code, and language.
        """
        return f"welcome_message__{channel}__{country_code}__{language}"

    @classmethod
    def ai_bot_chat_history(cls, user_id: str, session_id: str):
        """
        Returns the cache key for AI bot chat history based on user ID and session ID.
        """
        return f"ai_bot_chat_history__{user_id}__{session_id}"

    @classmethod
    def aho_corasick_automaton(cls, location: str):
        """
        Returns the cache key for Aho-Corasick automaton patterns based on the specified location.
        """
        return f"aho_corasick_automaton__{location}"

    @classmethod
    def search_summary(
        cls, query: str, sku_codes: List[str], channel: str, country_code: str
    ):
        """
        Returns the cache key for search summary based on query, SKU codes, channel, and country code.
        """
        sku_codes_str = "_".join(sku_codes)
        return f"search_summary__{query}__{sku_codes_str}__{channel}__{country_code}"

    @classmethod
    def search_summary_response(
        cls, search_summary_key: str, language: str, random_int_range: tuple = (0, 1)
    ):
        """
        Returns the cache key for search summary response based on search summary key, language, and random integer range.
        """
        return f"search_summary_response__{search_summary_key}__{random.randint(*random_int_range)}__{language}"
