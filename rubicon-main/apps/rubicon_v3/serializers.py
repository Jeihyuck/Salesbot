import pycountry
import os
import io
import tiktoken

from PIL import Image

from rest_framework import serializers
from django.db.models import Q
from django.core.files.uploadedfile import InMemoryUploadedFile

from apps.rubicon_v3.__function.definitions import channels
from apps.rubicon_v3.__function.__rubicon_log import check_log_exists
from apps.rubicon_v3.models import Channel
from apps.rubicon_v3.exceptions import (
    PayloadTooLargeException,
    TooManyFilesException,
    TotalSizeTooLargeException,
    InvalidImageResolutionException,
    InvalidFileTypeException,
)
from apps.rubicon_v3.__api._07_supplementary_info import SupplementaryTypes

from alpha.settings import VITE_COUNTRY, VITE_OP_TYPE
from alpha._db import chat_log_collection, search_log_collection

encoding = tiktoken.encoding_for_model("gpt-4o")


# Defined constants for validation
MAX_USER_ID_LENGTH = 50
MAX_SESSION_ID_LENGTH = 50
MAX_MESSAGE_ID_LENGTH = 50
MAX_GU_ID_LENGTH = 100
MAX_SA_ID_LENGTH = 800
MAX_JWT_TOKEN_LENGTH = 4000
MAX_ESTORE_SITECODE_LENGTH = 30
MAX_DEPARTMENT_LENGTH = 20
MAX_CREATED_ON_LENGTH = 40
MAX_MESSAGE_HISTORY_LENGTH = 20
MAX_MESSAGE_LENGTH = 10
MAX_USER_CONTENT_LENGTH = 1000
MAX_MESSAGE_HISTORY_USER_CONTENT_LENGTH = 5000
MAX_AGENT_ID_LENGTH = 50
MAX_AGENT_NAME_LENGTH = 100
MAX_NEW_TITLE_LENGTH = 100

MAX_CONTENT_TOKENS = 2500  # Max tokens for all contents


def validate_mongo_integer(value):
    """
    Custom validator to ensure a value fits within MongoDB's 8-byte integer range.
    """
    try:
        # An 8-byte signed integer (long) in MongoDB.
        min_val = -9223372036854775808
        max_val = 9223372036854775807
        if not min_val <= int(value) <= max_val:
            raise serializers.ValidationError(
                f"ID '{value}' is outside the storable 8-byte integer range."
            )
    except (ValueError, TypeError):
        # Pass if the value is not a valid integer string (e.g., a UUID).
        # It won't be stored as an integer type in MongoDB.
        pass
    return value


def validate_channel(value):
    """Custom validator for channel field"""
    query = Q(active=True)

    # Add locale filter only for staging and production environments
    if VITE_OP_TYPE in ["STG", "PRD"]:
        locale = VITE_COUNTRY
        # If the vite country is set to UK, we use GB as the locale
        if VITE_COUNTRY == "UK":
            locale = "GB"

        query &= Q(locale=locale)

    valid_channels = list(
        Channel.objects.filter(query).values_list("channel", flat=True).distinct()
    )
    if value not in valid_channels:
        raise serializers.ValidationError(f"Invalid channel: '{value}'")
    return value


def validate_country_code(value):
    """Validate country code using pycountry library"""
    query = Q(active=True)

    # Add locale filter only for staging and production environments
    if VITE_OP_TYPE in ["STG", "PRD"]:
        locale = VITE_COUNTRY
        # If the vite country is set to UK, we use GB as the locale
        if VITE_COUNTRY == "UK":
            locale = "GB"

        query &= Q(locale=locale)

    valid_country_codes = list(
        Channel.objects.filter(query).values_list("country_code", flat=True).distinct()
    )
    if value not in valid_country_codes:
        raise serializers.ValidationError(f"Invalid country code: '{value}'")
    return value


def validate_language_code(value):
    """Validate language code using pycountry library"""
    if not pycountry.languages.get(alpha_2=value):
        raise serializers.ValidationError(f"Invalid language code: '{value}'")
    return value


def validate_boolean(value):
    """Custom validator for boolean fields"""
    if not isinstance(value, bool):
        raise serializers.ValidationError(
            f"Invalid boolean value (true or false): '{value}'"
        )
    return value


def validate_selected_list(value):
    """Validate that list items are either string integers or integers"""
    if not isinstance(value, list):
        raise serializers.ValidationError("Expected a list")

    for item in value:
        if not isinstance(item, (str, int)):
            raise serializers.ValidationError(
                f"List items must be strings or integers, got {type(item).__name__}: {item}"
            )
        # Validate that string items can be converted to integers
        if isinstance(item, str):
            try:
                int(item)
            except ValueError:
                raise serializers.ValidationError(
                    f"String item '{item}' cannot be converted to an integer"
                )
    return value


############################################################################


class CharFieldTruncationMixin:
    """
    Mixin to normalize and truncate CharField values.
    - Converts int/float to string (mimicking CharField behavior)
    - Truncates to max_length if exceeded
    - Works for both valid and invalid data

    Access normalized data via: serializer.normalized_data
    """

    def get_normalized_data(self):
        """
        Get data with CharFields converted to strings and truncated to max_length.
        This mimics what CharField validation does internally.
        """
        if not hasattr(self, "initial_data"):
            return {}

        def normalize_by_fields(data, fields, rules):
            """Recursively normalize data based on field definitions"""
            if not isinstance(data, dict):
                return data

            normalized = data.copy()

            for field_name, field in fields.items():
                if field_name not in data:
                    continue

                value = data[field_name]

                # Handle CharField - convert to string and truncate if needed
                if isinstance(field, serializers.CharField):
                    if value is not None and not isinstance(value, bool):
                        # Convert to string just like CharField does
                        str_value = str(value)

                        # Check for custom truncation rules first in the current level
                        if field_name in rules:
                            max_len = rules[field_name]
                            if len(str_value) > max_len:
                                normalized[field_name] = str_value[:max_len] + "..."
                            else:
                                normalized[field_name] = str_value

                        # Apply max_length if it exists
                        elif hasattr(field, "max_length") and field.max_length:
                            if len(str_value) > field.max_length:
                                normalized[field_name] = (
                                    str_value[: field.max_length] + "..."
                                )
                            else:
                                normalized[field_name] = str_value
                        else:
                            # No max_length, just convert to string
                            normalized[field_name] = str_value

                # Handle nested serializer
                elif isinstance(field, serializers.Serializer):
                    if isinstance(value, dict):
                        # Check for child custom truncation rules
                        child_rules = getattr(field, "_truncation_rules", {})
                        normalized[field_name] = normalize_by_fields(
                            value, field.fields, child_rules
                        )

                # Handle many=True (list of nested serializers)
                elif isinstance(field, serializers.ListSerializer):
                    if isinstance(value, list):
                        # Handle list of nested serializers
                        if isinstance(field.child, serializers.Serializer):
                            # Check if child serializer has truncation rules
                            child_truncation_rules = getattr(
                                field.child, "_truncation_rules", {}
                            )
                            normalized[field_name] = [
                                (
                                    normalize_by_fields(
                                        item, field.child.fields, child_truncation_rules
                                    )
                                    if isinstance(item, dict)
                                    else item
                                )
                                for item in value
                            ]
                        # Handle list of CharFields
                        elif isinstance(field.child, serializers.CharField):
                            # Check for custom truncation rules for list items. If not found, use child CharField's max_length
                            item_max = rules.get(field_name) or getattr(
                                field.child, "max_length", None
                            )

                            normalized_list = []
                            for item in value:
                                if item is not None and not isinstance(item, bool):
                                    str_item = str(item)
                                    # Truncate if item_max is defined and exceeded
                                    if item_max and len(str_item) > item_max:
                                        normalized_list.append(
                                            str_item[:item_max] + "..."
                                        )
                                    else:
                                        normalized_list.append(str_item)
                                else:
                                    normalized_list.append(item)
                            normalized[field_name] = normalized_list

                # Handle ListField with CharField child
                elif isinstance(field, serializers.ListField):
                    if isinstance(value, list):
                        if isinstance(field.child, serializers.CharField):
                            # Check for custom truncation rules for list items. If not found, use child CharField's max_length
                            item_max = rules.get(field_name) or getattr(
                                field.child, "max_length", None
                            )

                            normalized_list = []
                            for item in value:
                                if item is not None and not isinstance(item, bool):
                                    str_item = str(item)
                                    # Truncate if item_max is defined and exceeded
                                    if item_max and len(str_item) > item_max:
                                        normalized_list.append(
                                            str_item[:item_max] + "..."
                                        )
                                    else:
                                        normalized_list.append(str_item)
                                else:
                                    normalized_list.append(item)
                            normalized[field_name] = normalized_list

            return normalized

        # Get the root truncation rules if defined
        root_rules = getattr(self, "_truncation_rules", {})
        return normalize_by_fields(self.initial_data, self.fields, root_rules)

    def is_valid(self, raise_exception=False):
        """
        Override is_valid to always generate normalized data.
        Available via self.normalized_data whether validation passes or fails.
        """
        # Always generate normalized data before validation
        self.normalized_data = self.get_normalized_data()

        # Call parent's is_valid
        is_valid = super().is_valid(raise_exception=raise_exception)

        return is_valid


##############################################################################


class MetaSerializer(serializers.Serializer):
    """Serializer for the meta object"""

    countryCode = serializers.CharField(
        validators=[validate_country_code], trim_whitespace=False
    )
    agentId = serializers.CharField(
        required=False,
        max_length=MAX_AGENT_ID_LENGTH,
        validators=[validate_mongo_integer],
    )
    agentName = serializers.CharField(required=False, max_length=MAX_AGENT_NAME_LENGTH)


class MessageHistoryItemSerializer(serializers.Serializer):
    """Serializer for items in the messageHistory array"""

    # Custom attribute to hint truncation
    _truncation_rules = {
        "content": MAX_MESSAGE_HISTORY_USER_CONTENT_LENGTH,
    }

    type = serializers.ChoiceField(choices=["text"])
    messageId = serializers.CharField(
        max_length=MAX_MESSAGE_ID_LENGTH, validators=[validate_mongo_integer]
    )
    content = serializers.CharField()
    role = serializers.ChoiceField(choices=["user", "assistant", "agent", "card"])
    createdOn = serializers.CharField(required=False, max_length=MAX_CREATED_ON_LENGTH)

    def validate_content(self, value):
        """Validate content length for all roles"""
        if (
            len(value) > MAX_MESSAGE_HISTORY_USER_CONTENT_LENGTH
            and len(encoding.encode(str(value))) > MAX_CONTENT_TOKENS
        ):
            raise serializers.ValidationError(
                f"Content cannot exceed {MAX_CONTENT_TOKENS} tokens (gpt-4o limit)"
            )

        return value


class MessageItemSerializer(serializers.Serializer):
    """Serializer for items in the message array"""

    type = serializers.ChoiceField(choices=["text", "image", "audio"])
    messageId = serializers.CharField(
        max_length=MAX_MESSAGE_ID_LENGTH, validators=[validate_mongo_integer]
    )
    content = serializers.CharField(
        allow_blank=True, max_length=MAX_MESSAGE_HISTORY_USER_CONTENT_LENGTH
    )
    role = serializers.ChoiceField(choices=["user"])
    createdOn = serializers.CharField(required=False, max_length=MAX_CREATED_ON_LENGTH)

    def validate_messageId(self, value):
        """
        Validate message ID uniqueness
        """
        # Check if messageId already exists in the database
        existing_log = check_log_exists(chat_log_collection, value)
        if existing_log:
            raise serializers.ValidationError(
                f"Message ID '{value}' already exists in the system"
            )

        return value

    def validate_content(self, value):
        """
        Validate content length for user messages
        """
        # The max value here is MAX_USER_CONTENT_LENGTH for actual input limit
        # Whereas the MAX_MESSAGE_HISTORY_USER_CONTENT_LENGTH is used for truncation
        # During normalization in the mixin
        if len(value) > MAX_USER_CONTENT_LENGTH:
            raise serializers.ValidationError(
                f"Content for user role cannot exceed {MAX_USER_CONTENT_LENGTH} characters"
            )

        return value


class CompletionSerializer(CharFieldTruncationMixin, serializers.Serializer):
    """Main serializer for API input validation"""

    channel = serializers.CharField(
        validators=[validate_channel], trim_whitespace=False
    )
    model = serializers.ChoiceField(
        choices=["rubicon", "default_greeting"],
    )
    meta = MetaSerializer()
    userId = serializers.CharField(
        max_length=MAX_USER_ID_LENGTH, validators=[validate_mongo_integer]
    )
    sessionId = serializers.CharField(
        max_length=MAX_SESSION_ID_LENGTH, validators=[validate_mongo_integer]
    )
    messageHistory = MessageHistoryItemSerializer(many=True)
    message = MessageItemSerializer(many=True)
    lng = serializers.CharField(
        validators=[validate_language_code], trim_whitespace=False
    )
    guId = serializers.CharField(required=False, max_length=MAX_GU_ID_LENGTH)
    saId = serializers.CharField(required=False, max_length=MAX_SA_ID_LENGTH)
    jwtToken = serializers.CharField(required=False, max_length=MAX_JWT_TOKEN_LENGTH)
    estoreSitecode = serializers.CharField(
        required=False, max_length=MAX_ESTORE_SITECODE_LENGTH
    )

    department = serializers.CharField(
        required=False, allow_null=True, max_length=MAX_DEPARTMENT_LENGTH
    )
    backendCache = serializers.BooleanField(
        validators=[validate_boolean], required=False
    )
    simple = serializers.BooleanField(validators=[validate_boolean], required=False)
    updateHttpStatus = serializers.BooleanField(
        validators=[validate_boolean], required=False
    )
    stream = serializers.BooleanField(validators=[validate_boolean], required=False)
    showLoading = serializers.BooleanField(
        validators=[validate_boolean], required=False
    )

    def validate_messageHistory(self, value):
        """
        Custom validation for messageHistory array:
        - Ensure no more than 20 messages
        """
        if len(value) > MAX_MESSAGE_HISTORY_LENGTH:
            raise serializers.ValidationError(
                "MessageHistory cannot contain more than 20 items"
            )

        return value

    def validate_message(self, value):
        """
        Custom validation for message array:
        - Ensure at least one message
        - If text type is present, ensure only one text message
        """
        if not value or len(value) < 1:
            raise serializers.ValidationError("At least one message is required")

        if len(value) > MAX_MESSAGE_LENGTH:
            raise serializers.ValidationError(
                "Message array cannot contain more than 10 items"
            )

        # Check for text type limitations
        text_messages = [msg for msg in value if msg["type"] == "text"]
        if text_messages and len(text_messages) > 1:
            raise serializers.ValidationError("Only one text message is allowed")

        return value

    def validate(self, data):
        """
        Additional cross-field validation if needed
        """
        # Example: could add additional validation rules here
        # that involve multiple fields

        return data


#############################################################################


class FileSerializer(serializers.Serializer):
    """Serializer for file uploads

    Limitations:
    - Images:
        - Maximum 500 images
        - Maximum 20MB per image
        - Total size limit of 50MB for all images
        - Resolution must be either 512x512 or no more than 768px on the short side and 2000px on the long side
    - Audio:
        - Maximum 25MB per audio file
        - Supported formats: mp3, mp4, wav, webm
    - File types:
        - Images: png, jpeg, jpg, webp, gif
        - Audio: mp3, mp4, wav, webm
    - Invalid file types will raise an exception

    - Based on ChatGPT API file upload validation
    """

    files = serializers.ListField(child=serializers.FileField(), required=False)

    def validate_files(self, files):
        if not files:
            return files

        # File type validation constants
        VALID_IMAGE_TYPES = [
            "image/png",
            "image/jpeg",
            "image/jpg",
            "image/webp",
            "image/gif",
        ]

        VALID_IMAGE_EXTENSIONS = [".png", ".jpeg", ".jpg", ".webp", ".gif"]

        VALID_AUDIO_TYPES = [
            "audio/mpeg",  # mp3, mpeg
            "audio/mp4",  # mp4, m4a
            "audio/wav",  # wav
            "audio/webm",  # webm
        ]

        VALID_AUDIO_EXTENSIONS = [
            ".mp3",
            ".mp4",
            ".mpeg",
            ".mpga",
            ".m4a",
            ".wav",
            ".webm",
        ]

        # Size limits
        MAX_IMAGE_SIZE = 20 * 1024 * 1024  # 20MB per image
        MAX_AUDIO_SIZE = 25 * 1024 * 1024  # 25MB per audio
        MAX_TOTAL_IMAGE_SIZE = 50 * 1024 * 1024  # 50MB total images
        MAX_IMAGE_COUNT = 500  # Maximum 500 images
        MAX_AUDIO_COUNT = 1  # Maximum 1 audio file

        # Initialize counters
        image_count = 0
        audio_count = 0
        total_image_size = 0

        for file in files:
            if not isinstance(file, InMemoryUploadedFile):
                raise InvalidFileTypeException(f"Invalid file type: {file}")

            # Get file extension and verify against content type
            file_name, file_ext = os.path.splitext(file.name.lower())
            content_type = file.content_type.lower()

            # Validate image files
            if content_type in VALID_IMAGE_TYPES or file_ext in VALID_IMAGE_EXTENSIONS:
                image_count += 1

                # Check image count
                if image_count > MAX_IMAGE_COUNT:
                    raise TooManyFilesException(
                        f"Maximum of {MAX_IMAGE_COUNT} images exceeded"
                    )

                # Check individual image size
                if file.size > MAX_IMAGE_SIZE:
                    raise PayloadTooLargeException(
                        f"Image file size too large: {file.name} ({file.size} bytes)"
                    )

                total_image_size += file.size

                # Check total image size
                if total_image_size > MAX_TOTAL_IMAGE_SIZE:
                    raise TotalSizeTooLargeException(
                        f"Total image size exceeds {MAX_TOTAL_IMAGE_SIZE/1024/1024}MB limit"
                    )

                # Validate image resolution
                try:
                    img = Image.open(io.BytesIO(file.read()))
                    file.seek(0)  # Reset file pointer after reading
                    width, height = img.size

                    # Determine short and long sides
                    short_side = min(width, height)
                    long_side = max(width, height)

                    # Check if resolution meets requirements
                    is_low_res = width == 512 and height == 512
                    is_high_res = short_side <= 768 and long_side <= 2000

                    if not (is_low_res or is_high_res):
                        raise InvalidImageResolutionException(
                            f"Image resolution invalid: {width}x{height}. Must be either 512x512 or no more than 768px on the short side and 2000px on the long side."
                        )

                except Exception as e:
                    # If we can't open the image, it might be corrupted
                    raise InvalidFileTypeException(
                        f"Cannot process image file: {file.name} - {str(e)}"
                    )

            # Validate audio files
            elif (
                content_type in VALID_AUDIO_TYPES or file_ext in VALID_AUDIO_EXTENSIONS
            ):
                audio_count += 1

                # Check audio count
                if audio_count > MAX_AUDIO_COUNT:
                    raise TooManyFilesException(
                        "Maximum of {MAX_AUDIO_COUNT} audio files exceeded"
                    )

                # Check individual audio size
                if file.size > MAX_AUDIO_SIZE:
                    raise PayloadTooLargeException(
                        f"Audio file size too large: {file.name} ({file.size} bytes)"
                    )

            # Invalid file type
            else:
                raise InvalidFileTypeException(
                    f"Unsupported file type for {file.name}. Supported formats: "
                    f"Images: {', '.join(VALID_IMAGE_EXTENSIONS)}, "
                    f"Audio: {', '.join(VALID_AUDIO_EXTENSIONS)}"
                )

        return files

    def validate(self, data):
        """Additional cross-field validations if needed"""
        return data


#############################################################################


class ParamsSearchSerializer(serializers.Serializer):
    """Serializer for the params object in search api"""

    channel = serializers.CharField(
        validators=[validate_channel], trim_whitespace=False
    )
    countryCode = serializers.CharField(
        validators=[validate_country_code], trim_whitespace=False
    )
    department = serializers.CharField(
        required=False, allow_null=True, max_length=MAX_DEPARTMENT_LENGTH
    )
    userId = serializers.CharField(
        max_length=MAX_USER_ID_LENGTH, validators=[validate_mongo_integer]
    )
    message = serializers.CharField(max_length=MAX_USER_CONTENT_LENGTH)
    lng = serializers.CharField(
        validators=[validate_language_code], trim_whitespace=False
    )
    guId = serializers.CharField(required=False, max_length=MAX_GU_ID_LENGTH)
    saId = serializers.CharField(required=False, max_length=MAX_SA_ID_LENGTH)
    jwtToken = serializers.CharField(required=False, max_length=MAX_JWT_TOKEN_LENGTH)
    estoreSitecode = serializers.CharField(
        required=False, max_length=MAX_ESTORE_SITECODE_LENGTH
    )


class SearchResultsSerializer(serializers.Serializer):
    """Serializer for the search results in search api"""

    id = serializers.CharField()


class SearchDataSerializer(serializers.Serializer):
    """Serializer for the meta object for search api"""

    searchResults = SearchResultsSerializer(many=True)
    searchKeywords = serializers.ListField(
        child=serializers.CharField(), required=False
    )
    searchType = serializers.CharField(required=False)


class SearchSerializer(CharFieldTruncationMixin, serializers.Serializer):
    """Serializer for search queries"""

    messageId = serializers.CharField(
        max_length=MAX_MESSAGE_ID_LENGTH, validators=[validate_mongo_integer]
    )
    model = serializers.ChoiceField(
        choices=[
            "rubicon_search",
        ],
    )
    params = ParamsSearchSerializer()
    searchData = SearchDataSerializer()
    backendCache = serializers.BooleanField(
        validators=[validate_boolean], required=False
    )
    updateHttpStatus = serializers.BooleanField(
        validators=[validate_boolean], required=False
    )
    stream = serializers.BooleanField(validators=[validate_boolean], required=False)

    def validate_messageId(self, value):
        """
        Validate message ID uniqueness
        """
        # Check if messageId already exists in the search log collection
        existing_log = check_log_exists(search_log_collection, value)
        if existing_log:
            raise serializers.ValidationError(
                f"Message ID '{value}' already exists in the system. DB: S"
            )
        # Check if messageId already exists in the chat log collection
        existing_log = check_log_exists(chat_log_collection, value)
        if existing_log:
            raise serializers.ValidationError(
                f"Message ID '{value}' already exists in the system. DB: C"
            )

        return value


############################################################################


class AppraisalQuerySerializer(serializers.Serializer):
    """Serializer for appraisal query data"""

    message_id = serializers.CharField(
        max_length=MAX_MESSAGE_ID_LENGTH, validators=[validate_mongo_integer]
    )
    thumb_up = serializers.BooleanField(validators=[validate_boolean])
    selected_list = serializers.ListField(
        validators=[validate_selected_list], required=False, allow_empty=True
    )
    comment = serializers.CharField(
        max_length=MAX_USER_CONTENT_LENGTH, required=False, allow_blank=True
    )

    def validate_message_id(self, value):
        """
        Validate message ID exists
        """
        # Check if message_id exists in the database
        existing_log = check_log_exists(chat_log_collection, value)
        if not existing_log:
            raise serializers.ValidationError(
                f"Message ID '{value}' does not exist in the system"
            )

        return value


class AppraisalSerializer(CharFieldTruncationMixin, serializers.Serializer):
    """Serializer for appraisal data"""

    action = serializers.ChoiceField(choices=["ut_appraisal"])
    query = AppraisalQuerySerializer()


###############################################################################


class AppraisalRegistrySerializer(CharFieldTruncationMixin, serializers.Serializer):
    """Serializer for appraisal registry data"""

    messageId = serializers.CharField(
        max_length=MAX_MESSAGE_ID_LENGTH, validators=[validate_mongo_integer]
    )
    channel = serializers.CharField(
        validators=[validate_channel], trim_whitespace=False
    )
    countryCode = serializers.CharField(
        validators=[validate_country_code], trim_whitespace=False
    )
    thumbUp = serializers.BooleanField(validators=[validate_boolean])
    selectedList = serializers.ListField(
        validators=[validate_selected_list], required=False, allow_empty=True
    )
    comment = serializers.CharField(
        max_length=MAX_USER_CONTENT_LENGTH, required=False, allow_blank=True
    )

    def validate(self, data):
        """
        Validate message ID exists
        """
        message_id = data.get("messageId")
        channel = data.get("channel")

        # For all the channels that uses search log collection,
        # Make sure the messageId exists in the search log collection
        if channel in [channels.DOTCOMSEARCH]:
            existing_log = check_log_exists(search_log_collection, message_id)
            if not existing_log:
                raise serializers.ValidationError(
                    f"Message ID '{message_id}' does not exist in the search log collection"
                )
        else:
            # For all other channels, check the chat log collection
            existing_log = check_log_exists(chat_log_collection, message_id)
            if not existing_log:
                raise serializers.ValidationError(
                    f"Message ID '{message_id}' does not exist in the chat log collection"
                )

        return data


###############################################################################


class HideChatLogActionSerializer(serializers.Serializer):
    """Serializer for hide_chat_log action"""

    messageId = serializers.CharField(
        max_length=MAX_MESSAGE_ID_LENGTH,
        required=False,
        validators=[validate_mongo_integer],
    )
    sessionId = serializers.CharField(
        max_length=MAX_SESSION_ID_LENGTH,
        required=False,
        validators=[validate_mongo_integer],
    )

    def validate(self, data):
        """
        Validate that at least one of messageId or sessionId is provided
        """
        message_id = data.get("messageId")
        session_id = data.get("sessionId")

        if not message_id and not session_id:
            raise serializers.ValidationError(
                "At least one of messageId or sessionId must be provided"
            )

        return data


class RenameSessionTitleActionSerializer(serializers.Serializer):
    """Serializer for rename_session_title action"""

    sessionId = serializers.CharField(
        max_length=MAX_SESSION_ID_LENGTH, validators=[validate_mongo_integer]
    )
    newTitle = serializers.CharField(max_length=MAX_NEW_TITLE_LENGTH)


class GenerateConversationSummaryActionSerializer(serializers.Serializer):
    """Serializer for generate_conversation_summary action"""

    sessionId = serializers.CharField(
        max_length=MAX_SESSION_ID_LENGTH, validators=[validate_mongo_integer]
    )
    userId = serializers.CharField(
        max_length=MAX_USER_ID_LENGTH, validators=[validate_mongo_integer]
    )
    channel = serializers.CharField(
        validators=[validate_channel], trim_whitespace=False
    )
    lng = serializers.CharField(
        validators=[validate_language_code], trim_whitespace=False
    )
    messageCount = serializers.IntegerField(
        required=False, help_text="Number of messages to include in the summary"
    )


class ActionSerializer(CharFieldTruncationMixin, serializers.Serializer):
    """Serializer for action api"""

    actionType = serializers.ChoiceField(
        choices=[
            "hide_chat_log",
            "rename_session_title",
            "generate_conversation_summary",
        ]
    )
    actionInfo = serializers.DictField()

    def get_normalized_data(self):
        """
        Override to handle actionInfo normalization based on actionType.
        """
        if not hasattr(self, "initial_data"):
            return {}

        # Get base normalization from the mixin (handles actionType)
        normalized = super().get_normalized_data()

        # Handle actionInfo specially since it needs dynamic serializer selection
        if "actionType" in self.initial_data and "actionInfo" in self.initial_data:
            action_type = self.initial_data["actionType"]
            action_info = self.initial_data["actionInfo"]

            serializer_map = {
                "hide_chat_log": HideChatLogActionSerializer,
                "rename_session_title": RenameSessionTitleActionSerializer,
                "generate_conversation_summary": GenerateConversationSummaryActionSerializer,
            }

            if action_type in serializer_map and isinstance(action_info, dict):
                serializer_class = serializer_map[action_type]

                # Apply mixin dynamically to the nested serializer
                class TempSerializer(CharFieldTruncationMixin, serializer_class):
                    pass

                # Create instance and get its normalized data
                temp_serializer = TempSerializer(data=action_info)
                temp_serializer.initial_data = action_info
                normalized["actionInfo"] = temp_serializer.get_normalized_data()

        return normalized

    def validate(self, data):
        """Keep your existing validation logic unchanged"""
        action_type = data["actionType"]
        action_info = data["actionInfo"]

        # Choose the appropriate validation based on actionType
        serializer_map = {
            "hide_chat_log": HideChatLogActionSerializer,
            "rename_session_title": RenameSessionTitleActionSerializer,
            "generate_conversation_summary": GenerateConversationSummaryActionSerializer,
        }

        # Validate actionInfo using the appropriate serializer
        serializer_class = serializer_map[action_type]
        action_info_serializer = serializer_class(data=action_info)
        if not action_info_serializer.is_valid():
            raise serializers.ValidationError(
                {"actionInfo": action_info_serializer.errors}
            )

        return data


##############################################################################


class SupplementInfoSerializer(serializers.Serializer):
    """Serializer for supplementary info"""

    supplementType = serializers.ChoiceField(
        choices=[
            SupplementaryTypes.MEDIA.value,
            SupplementaryTypes.MEDIA_V2.value,
            SupplementaryTypes.RELATED_QUERY.value,
            SupplementaryTypes.RELATED_QUERY_V2.value,
            SupplementaryTypes.GREETING_QUERY.value,
            SupplementaryTypes.PRODUCT_CARD.value,
            SupplementaryTypes.PRODUCT_CARD_V2.value,
            SupplementaryTypes.LOADING_MESSAGE.value,
            SupplementaryTypes.HYPERLINK.value,
        ],
    )
    supplementCount = serializers.IntegerField()
    supplementGalleryCount = serializers.IntegerField(required=False)
    timeout = serializers.IntegerField()


class SupplementarySerializer(CharFieldTruncationMixin, serializers.Serializer):
    """Custom serializer for supplementary information"""

    messageId = serializers.CharField(
        max_length=MAX_MESSAGE_ID_LENGTH, validators=[validate_mongo_integer]
    )
    supplementInfo = SupplementInfoSerializer(many=True)

    def validate(self, data):
        """
        Additional cross-field validation if needed
        """
        # Example: could add additional validation rules here
        # that involve multiple fields

        return data
