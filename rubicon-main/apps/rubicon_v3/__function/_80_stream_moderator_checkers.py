import sys

sys.path.append("/www/alpha/")

import re
import os
import json
import logging

from datetime import datetime
from dateutil import parser as date_parser
from typing import Dict
from pydantic import BaseModel

from apps.rubicon_v3.__function.__aho_corasick import AhoCorasickAutomaton
from apps.rubicon_v3.__function.__django_cache import CacheKey, DjangoCacheClient
from apps.rubicon_v3.__function.__django_cache_init import (
    create_validation_automaton,
    store_pii_patterns_in_cache,
    store_prohibited_patterns_in_cache,
)
from apps.rubicon_v3.__function.definitions import response_types
from apps.rubicon_v3.__function.__llm_call import open_ai_call_structured

from apps.rubicon_v3.models import Prompt_Template

# Set up logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("stream_moderator_checkers")

cache = DjangoCacheClient()


class ApprovedContent(BaseModel):
    safe: bool


class BaseChecker:
    """Base class for different types of content checkers"""

    # Class property to indicate if this checker should run in the fast tier
    fast_tier = True

    def check(self, content: str) -> Dict[str, any]:
        """Check content for violations"""
        raise NotImplementedError("Subclasses must implement this")


class ProhibitedWordsChecker(BaseChecker):
    fast_tier = True  # Run in fast tier (frequent checks)

    def __init__(self, language: str, debug: bool = False):
        self.language = language.upper()
        self.debug = debug
        self.automaton: AhoCorasickAutomaton = self._load_language_automaton()

    def _load_language_automaton(self):
        """Load the Aho-Corasick automaton for the specified language"""
        cache_key = CacheKey.aho_corasick_automaton(
            f"single_validation_words.{self.language}"
        )
        cached_automaton = cache.get(cache_key)
        if cached_automaton:
            # Touch the cache to extend its expiry
            cache.touch_exists(cache_key, 60 * 60 * 24 * 14)  # 14 days
            return cached_automaton
        else:
            # If no automaton found, try to create a new one and then check again
            create_validation_automaton()
            cached_automaton = cache.get(cache_key)
            if cached_automaton:
                return cached_automaton
            # If still no automaton found, log a warning and return None
            if self.debug:
                logger.warning(
                    f"No single validation automaton found for language: '{self.language}'"
                )
            return None

    def check(self, content: str) -> Dict[str, any]:
        """Check content for prohibited words"""
        if not self.automaton:
            if self.debug:
                logger.warning(
                    f"Automaton not loaded for language: '{self.language}'. Cannot perform check."
                )
            return {
                "safe": True,
            }

        # Use the automaton to find matches
        matches = self.automaton.search(content)

        if not matches:
            return {"safe": True}

        # If matches found, return the first one
        match = matches[0]  # Get the first match
        match_start_pos = match["start_pos"]
        match_end_pos = match["end_pos"]
        match_content = content[max(0, match_start_pos - 10) : match_end_pos + 10]
        reason = None
        if self.debug:
            reason = f"Prohibited word detected: '{match['matched_text']}' for regex pattern '{match['pattern']}'"
        else:
            reason = f"Prohibited content detected"

        return {
            "safe": False,
            "reason": reason,
            "match_context": match_content,
        }


class SecondValidationProhibitedWordsChecker(BaseChecker):
    fast_tier = True  # Run in fast tier since validation only happens on match

    def __init__(self, language: str, debug: bool = False):
        self.language = language.upper()
        self.debug = debug
        self.expiry_seconds = 60 * 60 * 24 * 1  # 1 day expiry for cache
        self.automaton: AhoCorasickAutomaton = self._load_language_automaton()

    def _load_language_automaton(self):
        """Load the Aho-Corasick automaton for the specified language"""
        cache_key = CacheKey.aho_corasick_automaton(
            f"second_validation_words.{self.language}"
        )
        cached_automaton = cache.get(cache_key)
        if cached_automaton:
            # Touch the cache to extend its expiry
            cache.touch_exists(cache_key, 60 * 60 * 24 * 14)  # 14 days
            return cached_automaton
        else:
            # If no automaton found, try to create a new one and then check again
            create_validation_automaton()
            cached_automaton = cache.get(cache_key)
            if cached_automaton:
                return cached_automaton
            # If still no automaton found, log a warning and return None
            if self.debug:
                logger.warning(
                    f"No second validation automaton found for language: '{self.language}'"
                )
            return None

    def _extract_word_from_match(
        self, content: str, match: str, start_pos: int, end_pos: int
    ) -> str:
        """Extract the actual word that contains the regex match."""
        # Expand backwards to find word start
        while (
            start_pos > 0
            and not content[start_pos - 1].isspace()
            and content[start_pos - 1] not in ".,!?;:()[]{}\"'-"
        ):
            start_pos -= 1

        # Expand forwards to find word end
        while (
            end_pos < len(content)
            and not content[end_pos].isspace()
            and content[end_pos] not in ".,!?;:()[]{}\"'-"
        ):
            end_pos += 1

        # Extract the full word
        word = content[start_pos:end_pos].strip()
        return word

    def _second_validation(self, word: str, context: str, pattern: str) -> bool:
        """
        LLM-based second validation for prohibited words.

        Args:
            word: The actual word that triggered the match
            context: The surrounding context
            pattern: The pattern that was matched

        Returns:
            True if the word is safe (false positive), False if it's actually prohibited
        """
        # Get the prompt from db
        prompt_obj = Prompt_Template.objects.filter(
            category_lv1="prohibited_word_second_validation",
            response_type=response_types.GUARDRAIL,
        ).first()
        prompt = prompt_obj.prompt

        # Initialize the messages for the OpenAI API call
        messages = [
            {"role": "system", "content": prompt},
            {
                "role": "user",
                "content": f"Is the word '{word}' safe to use in this context: '{context}'? The pattern that was matched was: '{pattern}'. Please answer with True or False.",
            },
        ]

        # Call the LLM to validate the word
        response = open_ai_call_structured(
            model_name="gpt-4.1-mini",
            messages=messages,
            temperature=0.01,
            top_p=1.0,
            seed=42,
            response_format=ApprovedContent,
        )

        # Check if the response is valid
        if response and response.get("safe"):
            return True

        return False  # If response is None or not safe, consider it prohibited

    def check(self, content: str) -> Dict[str, any]:
        """Check content for prohibited words that need second validation."""
        if not self.automaton:
            if self.debug:
                logger.warning(
                    f"Automaton not loaded for language: '{self.language}'. Cannot perform secondary check."
                )
            return {"safe": True}

        # Use the automaton to find matches
        matches = self.automaton.search(content)

        if not matches:
            return {"safe": True}

        # If matches found, validate each one
        # Check the redis cache for previously validated words
        for match in matches:
            # Extract the actual word that triggered the match
            word = self._extract_word_from_match(
                content, match["matched_text"], match["start_pos"], match["end_pos"]
            )

            # Check cache first (use touch exist to refresh expiry if found)
            if cache.touch_exists(
                CacheKey.moderator_validated_patterns(word), self.expiry_seconds
            ):
                if self.debug:
                    logger.info(
                        f"Word '{word}' found in cache, skipping second validation"
                    )
                continue

            # Not in cache, need to validate
            if self.debug:
                logger.info(f"Word '{word}' not in cache, performing second validation")

            # OPTIMIZATION: Only cache words that contain prohibited patterns as substrings
            # Don't cache exact matches with prohibited patterns, as these require contextual validation
            # (exact matches may be inappropriate in some contexts but appropriate in others)
            if word.strip().lower() != match["pattern"].strip().lower():
                cache.store(
                    CacheKey.moderator_validated_patterns(word),
                    True,
                    self.expiry_seconds,
                )

            # Get context for validation
            match_start_pos = match["start_pos"]
            match_end_pos = match["end_pos"]
            context = content[max(0, match_start_pos - 50) : match_end_pos + 50]

            # Perform second validation
            is_safe = self._second_validation(word, context, match["pattern"])

            # Second validation confirmed it's prohibited
            if not is_safe:
                # Delete the pre-emptively cached word
                cache.delete(CacheKey.moderator_validated_patterns(word))

                if self.debug:
                    reason = f"Prohibited word detected (after validation): '{word}'"
                else:
                    reason = f"Prohibited content detected"

                return {
                    "safe": False,
                    "reason": reason,
                    "match_context": content[
                        max(0, match_start_pos - 10) : match_end_pos + 10
                    ],
                }

        # If all matches are safe, return True
        return {"safe": True}


class PII_Checker(BaseChecker):
    fast_tier = True

    def __init__(self, country_code: str, debug: bool = False):
        self.country_code = country_code.upper()
        self.debug = debug
        self.pattern_data = self._load_country_patterns()

        # Extract the combined regex and mapping
        self.combined_regex: re.Pattern[str] | None = self.pattern_data.get(
            "combined_regex"
        )
        self.group_mapping = self.pattern_data.get("group_mapping", {})
        self.whitelist = self.pattern_data.get("whitelist", set())

    def _load_country_patterns(self) -> dict:
        """Load the combined PII patterns for the country."""
        cache_key = CacheKey.pii_patterns(self.country_code)
        cached_patterns = cache.get(cache_key)

        if cached_patterns is not None:
            # Touch the cache to extend its expiry
            cache.touch_exists(cache_key, 60 * 60 * 24 * 14)  # 14 days
            return cached_patterns
        else:
            # If no patterns found, try to load and then check again
            store_pii_patterns_in_cache()
            cached_patterns = cache.get(cache_key)
            if cached_patterns:
                return cached_patterns
            # If still no patterns found, log a warning and return empty list
            if self.debug:
                logger.warning(
                    f"No PII patterns found for country code: '{self.country_code}'"
                )
            return {"combined_regex": None, "group_mapping": {}, "whitelist": set()}

    def is_date(self, text: str) -> bool:
        """Check if the text is a valid date using dateutil parser."""
        text = text.strip()

        # Quick reject non-numeric patterns
        # Pre-check to see if text contains only digits or digits with common date separators
        if not re.match(r"^[\d\-/.]+$", text):
            return False

        try:
            # Try to parse the date
            parsed_date = date_parser.parse(text, fuzzy=False)

            # Basic sanity check for reasonable year range
            return 1900 <= parsed_date.year <= 2100

        except (ValueError, TypeError, OverflowError):
            return False

    def _has_valid_context(
        self, content: str, match: re.Match, pattern_info: dict
    ) -> bool:
        """
        Validate if the match has valid context (is actual PII) based on surrounding characters.

        A match has INVALID context (and thus is NOT PII) if:
        1. It has an alphanumeric character immediately before or after
        2. BEFORE: It has a digit followed by a separator (suggests version/ID number)
        3. AFTER: It has a separator followed by any alphanumeric (suggests continued identifier)

        Args:
            content: The full text being checked
            match: The regex match object
            pattern_info: Pattern metadata including context_validation setting

        Returns:
            True if context is valid (is PII), False if invalid (not PII)
        """
        # Check if this pattern requires context validation
        validation_type = pattern_info.get("context_validation")

        if validation_type != "strict":
            return True  # No validation needed or unknown type, accept the match

        start_pos = match.start()
        end_pos = match.end()

        # Common separators used in PII formats (besides whitespace)
        # Dot for IPs, dash/underscore for various formats, colon for MACs
        common_separators = "._-:"

        # Check what comes BEFORE the match
        if start_pos > 0:
            char_before = content[start_pos - 1]

            # Direct alphanumeric = invalid context
            if char_before.isalnum():
                return False  # "abc192.168.1.1" or "3192.168.1.1"

            # Check for digit + separator (including ANY whitespace)
            if (
                char_before.isspace() or char_before in common_separators
            ) and start_pos > 1:
                char_before_separator = content[start_pos - 2]
                if char_before_separator.isdigit():
                    return False  # "3 1234...", "3\t1234...", "3-192...", "3:AA:BB..."

        # Check what comes AFTER the match
        if end_pos < len(content):
            char_after = content[end_pos]

            # Direct alphanumeric = invalid context
            if char_after.isalnum():
                return False  # "192.168.1.1abc" or "192.168.1.123"

            # Check for separator + alphanumeric (including ANY whitespace)
            if (
                char_after.isspace() or char_after in common_separators
            ) and end_pos + 1 < len(content):
                char_after_separator = content[end_pos + 1]
                if char_after_separator.isdigit():  # ONLY DIGITS, not all alphanumeric
                    return False  # "192.168.1.100.5", "...3456 7", "...100-2"

        # Context is valid - this is actual PII
        return True

    def check(self, content: str) -> Dict[str, any]:
        """Check for PII using the combined regex - single pass through content."""
        if not self.combined_regex:
            return {"safe": True}

        for match in self.combined_regex.finditer(content):
            group_name = match.lastgroup
            pattern_info = self.group_mapping[group_name]
            matched_text = match.group()

            # Check whitelist
            if matched_text in self.whitelist:
                continue

            # Check for date patterns
            if self.is_date(matched_text):
                continue

            # Validate context if required
            if not self._has_valid_context(content, match, pattern_info):
                continue

            # Get context around the match
            match_pos = match.start()
            match_context = content[
                max(0, match_pos - 10) : match_pos + len(matched_text) + 10
            ]

            if self.debug:
                reason = f"PII detected: '{matched_text}' for pattern '{pattern_info['name']}'"
            else:
                reason = "PII detected"

            return {
                "safe": False,
                "reason": reason,
                "match_context": match_context,
            }

        return {"safe": True}

    def mask(self, content: str) -> str:
        """
        Mask all PII in content by replacing with [REDACTED].

        Args:
            content (str): Text to mask

        Returns:
            str: Masked text with PII replaced by [REDACTED]
        """
        if not self.combined_regex:
            return content

        def replacer(match: re.Match[str]) -> str:
            group_name = match.lastgroup
            pattern_info = self.group_mapping[group_name]
            matched_text = match.group()

            # Check whitelist
            if matched_text in self.whitelist:
                return matched_text

            # Check for date patterns
            if self.is_date(matched_text):
                return matched_text

            # Validate context if required - same as detection logic
            if not self._has_valid_context(content, match, pattern_info):
                return matched_text  # Don't mask if context is invalid

            # Only mask if all checks pass (meaning it's actual PII)
            return "[REDACTED]"

        # Single pass replacement with the replacer function
        return self.combined_regex.sub(replacer, content)


class ProhibitedPatternsChecker(BaseChecker):
    fast_tier = True  # Run in fast tier (frequent checks)

    def __init__(self, language: str, debug: bool = False):
        self.language = language.upper()
        self.debug = debug
        self.pattern_data = self._load_language_patterns()

        # Extract the combined regex and mapping
        self.combined_regex: re.Pattern[str] | None = self.pattern_data.get(
            "combined_regex"
        )
        self.group_mapping = self.pattern_data.get("group_mapping", {})
        self.whitelist = self.pattern_data.get("whitelist", set())

    def _load_language_patterns(self) -> dict:
        """Load the combined prohibited patterns for the language."""
        cache_key = CacheKey.prohibited_patterns(self.language)
        cached_patterns = cache.get(cache_key)

        if cached_patterns is not None:
            # Touch the cache to extend its expiry
            cache.touch_exists(cache_key, 60 * 60 * 24 * 14)  # 14 days
            return cached_patterns
        else:
            # If no patterns found, try to load and then check again
            store_prohibited_patterns_in_cache()
            cached_patterns = cache.get(cache_key)
            if cached_patterns:
                return cached_patterns
            # If still no patterns found, log a warning and return empty list
            if self.debug:
                logger.warning(
                    f"No prohibited patterns found for language: '{self.language}'"
                )
            return {"combined_regex": None, "group_mapping": {}, "whitelist": set()}

    def check(self, content: str) -> Dict[str, any]:
        """Check for Prohibited Patterns using the combined regex - single pass through content."""
        if not self.combined_regex:
            return {"safe": True}

        for match in self.combined_regex.finditer(content):
            group_name = match.lastgroup
            pattern_info = self.group_mapping[group_name]
            matched_text = match.group()
            pattern_name = pattern_info.get("name", "Unknown Pattern")

            # Check whitelist
            if matched_text in self.whitelist:
                continue

            # Get context around the match
            match_pos = match.start()
            match_context = content[
                max(0, match_pos - 10) : match_pos + len(matched_text) + 10
            ]

            if self.debug:
                reason = f"Prohibited Pattern Detected: '{matched_text}' for pattern '{pattern_info['name']}'"
            else:
                reason = "Prohibited Pattern Detected"

            return {
                "safe": False,
                "reason": reason,
                "match_context": match_context,
                "pattern_name": pattern_name,
            }

        return {"safe": True}
