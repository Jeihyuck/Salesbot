import sys

sys.path.append("/www/alpha/")

import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "alpha.settings")
django.setup()

import logging
import re
import json

from apps.rubicon_v3.__function.__django_cache import DjangoCacheClient, CacheKey
from apps.rubicon_v3.__function.__aho_corasick import AhoCorasickAutomaton
from apps.rubicon_data.models import plaza_base, uk_store_plaza

# Set up logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("django_cache_initialization")

cache = DjangoCacheClient()

BASE_PROHIBITED_WORDS_DIR = (
    "/www/alpha/apps/rubicon_v3/__data/prohibited_words_by_language"
)
BASE_PII_PATTERNS_DIR = "/www/alpha/apps/rubicon_v3/__data/pii_patterns_by_country"
BASE_PROHIBITED_PATTERNS_DIR = (
    "/www/alpha/apps/rubicon_v3/__data/prohibited_patterns_by_language"
)


def load_input_validation_words(base_directory_path) -> tuple:
    """
    Load words from all language directories.

    Args:
        base_directory_path: Base directory containing language subdirectories

    Returns:
        tuple: A tuple containing:
            - Set of words (lowercased)
            - List of language directories
    """
    words = set()

    # Check if base directory exists
    if not os.path.isdir(base_directory_path):
        logger.warning(f"Base directory not found: {base_directory_path}")
        return words, []

    # Get all language directories
    language_dirs = [
        os.path.join(base_directory_path, d)
        for d in os.listdir(base_directory_path)
        if os.path.isdir(os.path.join(base_directory_path, d))
    ]

    # Iterate through each language directory
    for language_dir in language_dirs:
        # Find all text files in this language directory
        text_files = [f for f in os.listdir(language_dir) if f.endswith(".txt")]

        # Process each text file
        for file_name in text_files:
            file_path = os.path.join(language_dir, file_name)
            try:
                with open(file_path, "r") as f:
                    for line in f:
                        line = line.strip()

                        # Skip empty lines and comments
                        if not line or line.startswith("#"):
                            continue

                        # Add word to set (no longer checking for REGEX prefix)
                        words.add(line.lower())

            except Exception as e:
                logger.error(f"Error loading word file {file_path}: {str(e)}")

    return words, language_dirs


def load_moderator_words_of_language(
    language_dir: str,
    level: str,
    common_dir: str,
) -> set:
    """
    Load words from a specific language directory.
    Args:
        language_dir (str): Path to the language directory.
        level (str): Validation level ('single' or 'second').
        common_dir (str): Path to the common directory.
    Returns:
        set: Set of words (lowercased)
    """
    words = set()

    # Check if the language directory exists as well as the common directory
    if not os.path.isdir(language_dir) or not os.path.isdir(common_dir):
        logger.warning(
            f"Language directory not found: {language_dir} or common directory not found: {common_dir}"
        )
        return words

    # Depending on the level, get the directory to load words from
    language_text_files = []
    common_text_files = []
    if level == "single":
        # Load words from the text files in the language directory
        language_text_files = [
            f for f in os.listdir(language_dir) if f.endswith(".txt")
        ]
        common_text_files = [f for f in os.listdir(common_dir) if f.endswith(".txt")]
    elif level == "second":
        # Load words from the second_validation_needed subdirectory
        language_dir = os.path.join(language_dir, "second_validation_needed")
        common_dir = os.path.join(common_dir, "second_validation_needed")
        if not os.path.isdir(language_dir) or not os.path.isdir(common_dir):
            logger.warning(
                f"Second validation directories not found: {language_dir} or {common_dir}"
            )
            return words
        language_text_files = [
            f for f in os.listdir(language_dir) if f.endswith(".txt")
        ]
        common_text_files = [f for f in os.listdir(common_dir) if f.endswith(".txt")]
    else:
        logger.error(
            f"Invalid validation level: {level}. Must be 'single' or 'second'."
        )
        return words

    # Process each language text file
    for file_name in language_text_files:
        file_path = os.path.join(language_dir, file_name)
        try:
            with open(file_path, "r") as f:
                for line in f:
                    line = line.strip()

                    # Skip empty lines and comments
                    if not line or line.startswith("#"):
                        continue

                    # Add word to set (no longer checking for REGEX prefix)
                    words.add(line.lower())

        except Exception as e:
            logger.error(f"Error loading word file {file_path}: {str(e)}")

    # Process each common text file
    for file_name in common_text_files:
        file_path = os.path.join(common_dir, file_name)
        try:
            with open(file_path, "r") as f:
                for line in f:
                    line = line.strip()

                    # Skip empty lines and comments
                    if not line or line.startswith("#"):
                        continue

                    # Add word to set (no longer checking for REGEX prefix)
                    words.add(line.lower())

        except Exception as e:
            logger.error(f"Error loading common word file {file_path}: {str(e)}")

    return words


def load_pre_embargo_automaton():
    """Initialize pre-embargo automaton in common directory"""
    pre_embargo_words = set()

    common_dir = os.path.join(BASE_PROHIBITED_WORDS_DIR, "COMMON")
    if not os.path.isdir(common_dir):
        logger.error(f"Common directory does not exist: {common_dir}")
        return pre_embargo_words

    # Load pre-embargo words from file
    file_path = os.path.join(common_dir, "pre_embargo.txt")
    try:
        with open(file_path, "r") as f:
            for line in f:
                line = line.strip()

                # Skip empty lines and comments
                if not line or line.startswith("#"):
                    continue

                # Add word to set (no longer checking for REGEX prefix)
                pre_embargo_words.add(line.lower())
    except Exception as e:
        logger.error(f"Error loading pre-embargo words from {file_path}: {str(e)}")
        return pre_embargo_words

    return pre_embargo_words


def store_prohibited_words_in_cache(base_dir: str) -> None:
    """
    Store input validation words and moderator words in the cache.
    Args:
        base_dir (str): Base directory containing language subdirectories.
    Returns:
        None
    """
    # Load words from all languages for input validation
    input_words, language_dirs = load_input_validation_words(base_dir)
    if not input_words:
        logger.warning("No words loaded for input validation. Skipping cache storage.")
        return

    language_single_validation_words = {}
    # Load words for each language for moderator (with common words)
    for language_dir in language_dirs:
        lang_name = os.path.basename(language_dir)

        # If the lang name is COMMON, skip it
        if lang_name == "COMMON":
            continue

        # Load words for the specific language
        single_validation_words = load_moderator_words_of_language(
            language_dir, "single", os.path.join(base_dir, "COMMON")
        )

        # Store words directly under language name
        language_single_validation_words[lang_name] = single_validation_words

    language_second_validation_words = {}
    # Load second validation words for each language
    for language_dir in language_dirs:
        lang_name = os.path.basename(language_dir)

        # If the lang name is COMMON, skip it
        if lang_name == "COMMON":
            continue

        # Load second validation words for the specific language
        second_validation_words = load_moderator_words_of_language(
            language_dir, "second", os.path.join(base_dir, "COMMON")
        )

        # Store words directly under language name
        language_second_validation_words[lang_name] = second_validation_words

    # Load the pre-embargo words from the common directory
    pre_embargo_words = load_pre_embargo_automaton()

    # Store words in cache
    cache_key = CacheKey.moderator_prohibited_words_data()
    cache.store(
        cache_key,
        {
            "input_words": input_words,
            "single_validation_words": language_single_validation_words,
            "second_validation_words": language_second_validation_words,
            "pre_embargo_words": pre_embargo_words,
        },
        expiry_seconds=60 * 60 * 24 * 14,  # Store for 2 weeks (14 days)
    )


def create_validation_automaton(force_refresh: bool = False) -> None:
    """
    Initialize validation automaton for each language from base patterns directory.
    Args:
        force_refresh (bool): If True, forces reloading patterns into cache. Defaults to False.
    Returns:
        None
    """
    # Check if base directory exists
    if not os.path.isdir(BASE_PROHIBITED_WORDS_DIR):
        logger.error(
            f"Base patterns directory does not exist: {BASE_PROHIBITED_WORDS_DIR}"
        )
        return

    # Check if the pattern data cache exists
    if not cache.get(CacheKey.moderator_prohibited_words_data()) or force_refresh:
        logger.info("No cached pattern data found, initializing from base directory")
        # Initialize cache with patterns from base directory
        store_prohibited_words_in_cache(BASE_PROHIBITED_WORDS_DIR)

    # Create the pre-embargo automaton
    pattern_location = "pre_embargo_words"
    automaton = AhoCorasickAutomaton(pattern_location=pattern_location)
    cache.store(
        CacheKey.aho_corasick_automaton(pattern_location),
        automaton,
        60 * 60 * 24 * 14,  # Cache for 14 days
    )  # Store pre-embargo words automaton

    # Create the input validation automaton
    pattern_location = "input_words"
    automaton = AhoCorasickAutomaton(pattern_location=pattern_location)
    cache.store(
        CacheKey.aho_corasick_automaton(pattern_location),
        automaton,
        60 * 60 * 24 * 14,  # Cache for 14 days
    )  # Store input validation words automaton

    # Get all the language names
    languages = [
        os.path.basename(lang_dir)
        for lang_dir in os.listdir(BASE_PROHIBITED_WORDS_DIR)
        if os.path.isdir(os.path.join(BASE_PROHIBITED_WORDS_DIR, lang_dir))
        and os.path.basename(lang_dir) != "COMMON"
    ]

    # Initialize automaton for each language
    for language in languages:
        # Single validation automaton
        try:
            pattern_location = f"single_validation_words.{language}"
            # Create automaton instance for the language
            automaton = AhoCorasickAutomaton(pattern_location=pattern_location)
            cache.store(
                CacheKey.aho_corasick_automaton(pattern_location),
                automaton,
                60 * 60 * 24 * 14,
            )  # Cache for 14 days
        except Exception as e:
            logger.error(
                f"Failed to initialize single validation automaton for {language}: {str(e)}"
            )

        # Second validation automaton
        try:
            pattern_location = f"second_validation_words.{language}"
            # Create automaton instance for second validation
            automaton = AhoCorasickAutomaton(pattern_location=pattern_location)
            cache.store(
                CacheKey.aho_corasick_automaton(pattern_location),
                automaton,
                60 * 60 * 24 * 14,
            )  # Cache for 14 days
        except Exception as e:
            logger.error(
                f"Failed to initialize second validation automaton for {language}: {str(e)}"
            )


############################################################################################


def load_phone_numbers_from_db(country: str) -> set:
    """
    Load all distinct phone numbers from the store database.
    Returns:
        set: Set of phone numbers as strings
    """
    phone_numbers = set()
    if country == "KR":
        phone_numbers = set(
            plaza_base.objects.filter(show_yn="Y", close_yn="N")
            .exclude(tel__isnull=True)
            .values_list("tel", flat=True)
            .distinct()
        )
    else:
        phone_numbers = set(
            uk_store_plaza.objects.filter(status="active")
            .exclude(telephone__isnull=True)
            .values_list("telephone", flat=True)
            .distinct()
        )

    return phone_numbers


def load_patterns_from_directory(directory_path: str) -> list:
    """
    Load patterns from a directory and return pattern metadata.

    Returns:
        list: List of pattern dictionaries with metadata
    """
    if not os.path.isdir(directory_path):
        return []

    patterns = []
    whitelist = set()
    pattern_files = [f for f in os.listdir(directory_path) if f.endswith(".json")]

    for file_name in pattern_files:
        file_path = os.path.join(directory_path, file_name)
        try:
            with open(file_path, "r") as f:
                pattern_data = json.loads(f.read())

            for pattern in pattern_data:
                if not isinstance(pattern, dict) or "pattern" not in pattern:
                    logger.warning(
                        f"Skipping invalid pattern in {file_path}: {pattern}"
                    )
                    continue

                # Add pattern with metadata
                patterns.append(
                    {
                        "pattern_str": pattern["pattern"],
                        "name": pattern.get("name", "Unknown Pattern"),
                        "whitelist": set(pattern.get("whitelist", [])),
                        "specificity": pattern.get("specificity", 10),  # Default to 10
                        "context_validation": pattern.get(
                            "context_validation", "none"
                        ),  # Default to 'none'
                    }
                )

                # Add whitelist entries to the global whitelist set for the country/language config
                whitelist.update(pattern.get("whitelist", []))

        except Exception as e:
            logger.error(f"Error loading pattern file {file_path}: {str(e)}")

    return patterns, whitelist


def load_pii_patterns_of_country(country_dir: str, common_dir: str) -> dict:
    """
    Load PII patterns from a specific country directory with combined regex.
    Patterns are sorted by specificity (longest first).
    """
    all_patterns = []
    whitelist = set()

    # Load common patterns
    if os.path.isdir(common_dir):
        patterns, common_whitelist = load_patterns_from_directory(common_dir)
        all_patterns.extend(patterns)
        whitelist.update(common_whitelist)

    # Load country-specific patterns
    if os.path.isdir(country_dir):
        patterns, country_whitelist = load_patterns_from_directory(country_dir)
        all_patterns.extend(patterns)
        whitelist.update(country_whitelist)

    # Phone number whitelist
    # Load all the distinct phone numbers from store db and add to whitelist
    whitelist.update(load_phone_numbers_from_db(os.path.basename(country_dir)))

    # If no patterns were loaded, use hardcoded fallback patterns
    if not all_patterns:
        logger.warning(
            f"No PII patterns found for {os.path.basename(country_dir)}, using fallback patterns"
        )
        all_patterns = [
            {
                "name": "Credit Card Number",
                "whitelist": set(),
                "pattern_str": r"\d{16}",
                "specificity": 16,
                "context_validation": "none",
            }
        ]

    # Sort all patterns by specificity (longest first)
    all_patterns.sort(key=lambda x: x.get("specificity", 10), reverse=True)

    # Build the combined regex with sorted patterns
    group_patterns = []
    group_mapping = {}

    for i, pattern_info in enumerate(all_patterns):
        group_name = f"g{i}"
        group_mapping[group_name] = pattern_info
        group_patterns.append(f"(?P<{group_name}>{pattern_info['pattern_str']})")

    # Compile the final combined regex
    combined_regex = None
    if group_patterns:
        try:
            combined_pattern_str = "|".join(group_patterns)
            combined_regex = re.compile(combined_pattern_str, re.IGNORECASE)
        except re.error as e:
            logger.error(
                f"Failed to compile combined PII regex for {os.path.basename(country_dir)}: {e}"
            )

    return {
        "combined_regex": combined_regex,
        "group_mapping": group_mapping,
        "whitelist": whitelist,
    }


def load_prohibited_patterns_of_language(language_dir: str, common_dir: str) -> dict:
    """
    Load prohibited patterns from a specific language directory with combined regex.
    Patterns are sorted by specificity (longest first).
    """
    all_patterns = []
    whitelist = set()

    # Load common patterns
    if os.path.isdir(common_dir):
        patterns, common_whitelist = load_patterns_from_directory(common_dir)
        all_patterns.extend(patterns)
        whitelist.update(common_whitelist)

    # Load language-specific patterns
    if os.path.isdir(language_dir):
        patterns, language_whitelist = load_patterns_from_directory(language_dir)
        all_patterns.extend(patterns)
        whitelist.update(language_whitelist)

    if not all_patterns:
        logger.warning(
            f"No prohibited patterns found for {os.path.basename(language_dir)}"
        )
        return {"combined_regex": None, "group_mapping": {}}

    # Sort all patterns by specificity (longest first)
    all_patterns.sort(key=lambda x: x.get("specificity", 10), reverse=True)

    # Build the combined regex with sorted patterns
    group_patterns = []
    group_mapping = {}

    for i, pattern_info in enumerate(all_patterns):
        group_name = f"g{i}"
        group_mapping[group_name] = pattern_info
        group_patterns.append(f"(?P<{group_name}>{pattern_info['pattern_str']})")

    # Compile the final combined regex
    combined_regex = None
    if group_patterns:
        try:
            combined_pattern_str = "|".join(group_patterns)
            combined_regex = re.compile(combined_pattern_str, re.IGNORECASE)
        except re.error as e:
            logger.error(
                f"Failed to compile combined prohibited regex for {os.path.basename(language_dir)}: {e}"
            )

    return {
        "combined_regex": combined_regex,
        "group_mapping": group_mapping,
        "whitelist": whitelist,
    }


def store_pii_patterns_in_cache(force_refresh: bool = False) -> None:
    """
    Store PII Patterns in Cache with combined regex optimization.
    """
    # Check if base directories exist
    if not os.path.isdir(BASE_PII_PATTERNS_DIR):
        logger.error(
            f"Base PII patterns directory does not exist: {BASE_PII_PATTERNS_DIR}"
        )
        return

    # Get all the country codes
    countries = [
        os.path.basename(country_dir)
        for country_dir in os.listdir(BASE_PII_PATTERNS_DIR)
        if os.path.isdir(os.path.join(BASE_PII_PATTERNS_DIR, country_dir))
        and os.path.basename(country_dir) != "COMMON"
    ]

    # Load and cache patterns for each country
    for country_code in countries:
        try:
            country_dir = os.path.join(BASE_PII_PATTERNS_DIR, country_code)
            common_dir = os.path.join(BASE_PII_PATTERNS_DIR, "COMMON")

            # Check if initialization is needed for this country
            cache_key = CacheKey.pii_patterns(country_code)
            if cache.touch_exists(cache_key) and not force_refresh:
                logger.info(
                    f"PII patterns for {country_code} already initialized in cache. Skipping re-initialization."
                )
                continue

            # Load patterns for the specific country (now returns dict with combined_regex)
            pattern_data = load_pii_patterns_of_country(country_dir, common_dir)

            # Log info about what was loaded
            pattern_count = len(pattern_data.get("group_mapping", {}))
            logger.info(
                f"Loaded {pattern_count} PII patterns for country: {country_code}"
            )

            # Update the cache for this country with the new structure
            cache.store(
                cache_key,
                pattern_data,  # Now storing dict with combined_regex and group_mapping
                expiry_seconds=60 * 60 * 24 * 14,  # Store for 2 weeks (14 days)
            )
        except Exception as e:
            logger.error(
                f"Failed to load/store PII patterns for {country_code}: {str(e)}"
            )

    return


def store_prohibited_patterns_in_cache(force_refresh: bool = False) -> None:
    """
    Store Prohibited Patterns in Cache with combined regex optimization.
    """
    # Check if base directories exist
    if not os.path.isdir(BASE_PROHIBITED_PATTERNS_DIR):
        logger.error(
            f"Base prohibited patterns directory does not exist: {BASE_PROHIBITED_PATTERNS_DIR}"
        )
        return

    # Get all the language names
    languages = [
        os.path.basename(lang_dir)
        for lang_dir in os.listdir(BASE_PROHIBITED_PATTERNS_DIR)
        if os.path.isdir(os.path.join(BASE_PROHIBITED_PATTERNS_DIR, lang_dir))
        and os.path.basename(lang_dir) != "COMMON"
    ]

    # Load and cache patterns for each language
    for language in languages:
        try:
            language_dir = os.path.join(BASE_PROHIBITED_PATTERNS_DIR, language)
            common_dir = os.path.join(BASE_PROHIBITED_PATTERNS_DIR, "COMMON")

            # Check if initialization is needed for this language
            cache_key = CacheKey.prohibited_patterns(language)
            if cache.touch_exists(cache_key) and not force_refresh:
                logger.info(
                    f"Prohibited patterns for {language} already initialized in cache. Skipping re-initialization."
                )
                continue

            # Load patterns for the specific language (now returns dict with combined_regex)
            pattern_data = load_prohibited_patterns_of_language(
                language_dir, common_dir
            )

            # Log info about what was loaded
            pattern_count = len(pattern_data.get("group_mapping", {}))
            logger.info(
                f"Loaded {pattern_count} prohibited patterns for language: {language}"
            )

            # Update the cache for this language with the new structure
            cache.store(
                cache_key,
                pattern_data,  # Now storing dict with combined_regex and group_mapping
                expiry_seconds=60 * 60 * 24 * 14,  # Store for 2 weeks (14 days)
            )
        except Exception as e:
            logger.error(
                f"Failed to load/store prohibited patterns for {language}: {str(e)}"
            )

    return


def store_validation_patterns_in_cache(force_refresh: bool = False) -> None:
    """
    Store both PII and Prohibited Patterns in Cache.
    """
    store_pii_patterns_in_cache(force_refresh)
    store_prohibited_patterns_in_cache(force_refresh)


if __name__ == "__main__":
    # Create the validation automaton

    import sys

    sys.path.append("/www/alpha/")

    import os
    import django

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "alpha.settings")
    django.setup()

    create_validation_automaton()

    # DEV delete cache key
    # cache.delete(CacheKey.moderator_pattern_data())
