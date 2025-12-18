from typing import Dict, Any, List, Union


ALLOWED_FIELDS_COMPLETION = {
    "root": {
        "channel",
        "model",
        "meta",
        "userId",
        "sessionId",
        "messageHistory",
        "message",
        "lng",
        "guId",
        "saId",
        "jwtToken",
        "estoreSitecode",
        "department",
        "backendCache",
        "simple",
        "updateHttpStatus",
        "stream",
        "showLoading",
    },
    "meta": {"countryCode", "agentId", "agentName"},
    "messageHistory_item": {"type", "messageId", "content", "role", "createdOn"},
    "message_item": {"type", "messageId", "content", "role", "createdOn"},
}


ALLOWED_FIELDS_SEARCH = {
    "root": {
        "messageId",
        "model",
        "params",
        "searchData",
        "backendCache",
        "updateHttpStatus",
        "stream",
    },
    "params": {
        "channel",
        "countryCode",
        "department",
        "userId",
        "message",
        "lng",
        "guId",
        "saId",
        "jwtToken",
        "estoreSitecode",
    },
    "searchData": {"searchResults", "searchKeywords", "searchType"},
}


ALLOWED_FIELDS_APPRAISAL = {
    "root": {
        "action",
        "query",
    },
    "query": {
        "message_id",
        "thumb_up",
        "selected_list",
        "comment",
    },
}


ALLOWED_FIELDS_APPRAISAL_REGISTRY = {
    "root": {
        "messageId",
        "channel",
        "countryCode",
        "thumbUp",
        "selectedList",
        "comment",
    }
}


ALLOWED_FIELDS_ACTION = {
    "root": {
        "actionType",
        "actionInfo",
    },
    "actionInfo": {
        "messageId",
        "sessionId",
        "userId",
        "channel",
        "countryCode",
        "lng",
        "guId",
        "saId",
        "newTitle",
        "messageCount",
    },
}


ALLOWED_FIELDS_SUPPLEMENTARY = {
    "root": {
        "messageId",
        "supplementInfo",
    },
    "supplementInfo": {
        "supplementType",
        "supplementCount",
        "supplementGalleryCount",
        "timeout",
    },
}


def validate_no_multiple_values(data: Dict[str, Any], api_name: str) -> Dict[str, Any]:
    """
    Validate that no field has multiple values (i.e., is not a list with multiple items)
    Returns dictionary of fields with multiple values
    """
    multiple_values = {}

    for key, value in data.items():
        if isinstance(value, list) and len(value) > 1:
            # For fields that should be single values
            if api_name == "completion" and key not in ["messageHistory", "message"]:
                multiple_values[key] = (
                    f"Multiple values found: {len(value)} values provided"
                )
            else:
                multiple_values[key] = (
                    f"Multiple values found: {len(value)} values provided"
                )

    return multiple_values


def validate_no_extra_fields_completion(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Check for extra fields and return a structured error dictionary
    """
    extra_fields = {}

    # Check root level fields
    for key in data:
        if key not in ALLOWED_FIELDS_COMPLETION["root"]:
            extra_fields[key] = "Unsupported field"

    # Check meta object
    if "meta" in data and isinstance(data["meta"], dict):
        meta_errors = {}
        for key in data["meta"]:
            if key not in ALLOWED_FIELDS_COMPLETION["meta"]:
                meta_errors[key] = "Unsupported field"
        if meta_errors:
            extra_fields["meta"] = meta_errors

    # Check messageHistory array
    if "messageHistory" in data and isinstance(data["messageHistory"], list):
        history_errors = []
        for i, item in enumerate(data["messageHistory"]):
            if isinstance(item, dict):
                item_errors = {}
                for key in item:
                    if key not in ALLOWED_FIELDS_COMPLETION["messageHistory_item"]:
                        item_errors[key] = "Unsupported field"
                if item_errors:
                    history_errors.append({"index": i, "errors": item_errors})
        if history_errors:
            extra_fields["messageHistory"] = history_errors

    # Check message array
    if "message" in data and isinstance(data["message"], list):
        message_errors = []
        for i, item in enumerate(data["message"]):
            if isinstance(item, dict):
                item_errors = {}
                for key in item:
                    if key not in ALLOWED_FIELDS_COMPLETION["message_item"]:
                        item_errors[key] = "Unsupported field"
                if item_errors:
                    message_errors.append({"index": i, "errors": item_errors})
        if message_errors:
            extra_fields["message"] = message_errors

    return extra_fields


def validate_no_extra_fields_search(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Check for extra fields in search API and return a structured error dictionary
    """
    extra_fields = {}

    # Check root level fields
    for key in data:
        if key not in ALLOWED_FIELDS_SEARCH["root"]:
            extra_fields[key] = "Unsupported field"

    # Check params object
    if "params" in data and isinstance(data["params"], dict):
        params_errors = {}
        for key in data["params"]:
            if key not in ALLOWED_FIELDS_SEARCH["params"]:
                params_errors[key] = "Unsupported field"
        if params_errors:
            extra_fields["params"] = params_errors

    # Check meta object
    if "meta" in data and isinstance(data["meta"], dict):
        meta_errors = {}
        for key in data["meta"]:
            if key not in ALLOWED_FIELDS_SEARCH["meta"]:
                meta_errors[key] = "Unsupported field"
        if meta_errors:
            extra_fields["meta"] = meta_errors

    return extra_fields


def validate_no_extra_fields_appraisal(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Check for extra fields in appraisal API and return a structured error dictionary
    """
    extra_fields = {}

    # Check root level fields
    for key in data:
        if key not in ALLOWED_FIELDS_APPRAISAL["root"]:
            extra_fields[key] = "Unsupported field"

    # Check query object
    if "query" in data and isinstance(data["query"], dict):
        query_errors = {}
        for key in data["query"]:
            if key not in ALLOWED_FIELDS_APPRAISAL["query"]:
                query_errors[key] = "Unsupported field"
        if query_errors:
            extra_fields["query"] = query_errors

    return extra_fields


def validate_no_extra_fields_appraisal_registry(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Check for extra fields in appraisal registry API and return a structured error dictionary
    """
    extra_fields = {}

    # Check root level fields
    for key in data:
        if key not in ALLOWED_FIELDS_APPRAISAL_REGISTRY["root"]:
            extra_fields[key] = "Unsupported field"

    return extra_fields


def validate_no_extra_fields_action(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Check for extra fields in action API and return a structured error dictionary
    """
    extra_fields = {}

    # Check root level fields
    for key in data:
        if key not in ALLOWED_FIELDS_ACTION["root"]:
            extra_fields[key] = "Unsupported field"

    # Check actionInfo object
    if "actionInfo" in data and isinstance(data["actionInfo"], dict):
        action_info_errors = {}
        for key in data["actionInfo"]:
            if key not in ALLOWED_FIELDS_ACTION["actionInfo"]:
                action_info_errors[key] = "Unsupported field"
        if action_info_errors:
            extra_fields["actionInfo"] = action_info_errors

    return extra_fields


def validate_no_extra_fields_supplementary(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Check for extra fields in supplementary API and return a structured error dictionary
    """
    extra_fields = {}

    # Check root level fields
    for key in data:
        if key not in ALLOWED_FIELDS_SUPPLEMENTARY["root"]:
            extra_fields[key] = "Unsupported field"

    # Check supplementInfo object
    if "supplementInfo" in data and isinstance(data["supplementInfo"], dict):
        supplement_info_errors = {}
        for key in data["supplementInfo"]:
            if key not in ALLOWED_FIELDS_SUPPLEMENTARY["supplementInfo"]:
                supplement_info_errors[key] = "Unsupported field"
        if supplement_info_errors:
            extra_fields["supplementInfo"] = supplement_info_errors

    return extra_fields


def extract_error_message(error: Any) -> str:
    """
    Extract error message from various error types including Django's ErrorDetail
    """
    # Check if it's a Django ErrorDetail object
    if hasattr(error, "message"):
        # ErrorDetail objects have a message attribute
        return str(error.message)
    elif hasattr(error, "__str__"):
        # Fall back to string representation
        error_str = str(error)
        # If it looks like an ErrorDetail string representation, extract the message
        if "ErrorDetail(string=" in error_str:
            # Extract the string content between quotes
            import re

            match = re.search(r"string=['\"]([^'\"]*)['\"]", error_str)
            if match:
                return match.group(1)
        return error_str
    else:
        return str(error)


def clean_list_errors(errors: List[Union[Dict, str]]) -> List[Any]:
    """
    Clean list errors by removing empty dictionaries and reformatting
    """
    cleaned = []
    for i, error in enumerate(errors):
        if isinstance(error, dict) and error:  # Non-empty dict
            # Clean the error dict to extract actual messages
            cleaned_error = {}
            for field, field_errors in error.items():
                if isinstance(field_errors, list):
                    cleaned_error[field] = [
                        extract_error_message(e) for e in field_errors
                    ]
                else:
                    cleaned_error[field] = extract_error_message(field_errors)

            # Add index information for better clarity
            error_with_index = {"index": i, "errors": cleaned_error}
            cleaned.append(error_with_index)
        elif hasattr(error, "message") or hasattr(error, "code"):
            # Handle ErrorDetail objects BEFORE checking isinstance(error, str)
            # because ErrorDetail inherits from str
            cleaned.append(extract_error_message(error))
        elif isinstance(error, str):
            cleaned.append(error)
        else:
            # Handle any other error types
            cleaned.append(extract_error_message(error))
    return cleaned


def normalize_error_value(value: Any) -> List[str]:
    """
    Normalize any error value to a list of strings
    """
    if isinstance(value, list):
        # Flatten nested lists and convert to strings
        result = []
        for item in value:
            if isinstance(item, list):
                result.extend([extract_error_message(v) for v in item])
            else:
                result.append(extract_error_message(item))
        return result
    elif isinstance(value, dict):
        # For dict errors, process each field
        error_messages = []
        for field, errors in value.items():
            if isinstance(errors, list):
                for e in errors:
                    error_messages.append(f"{field}: {extract_error_message(e)}")
            else:
                error_messages.append(f"{field}: {extract_error_message(errors)}")
        return error_messages
    else:
        return [extract_error_message(value)]


def merge_error_lists(existing: List[Any], new: List[Any]) -> List[Any]:
    """
    Merge two error lists, avoiding duplicates
    """
    # Convert to strings for comparison
    existing_strs = {str(e) for e in existing}
    merged = existing.copy()

    for error in new:
        if str(error) not in existing_strs:
            merged.append(error)

    return merged


def process_nested_errors(
    errors: Dict[str, Any], preserve_list_structure: bool = False
) -> Dict[str, Any]:
    """
    Process nested error structures, extracting ErrorDetail messages

    Args:
        errors: The error dictionary to process
        preserve_list_structure: If True, preserves the list structure for messageHistory/message fields
    """
    processed = {}
    for field, field_errors in errors.items():
        if (
            field in ["messageHistory", "message"]
            and isinstance(field_errors, list)
            and preserve_list_structure
        ):
            # For list fields, preserve the original structure (list of dicts per index)
            processed[field] = []
            for item in field_errors:
                if (
                    isinstance(item, dict) and item
                ):  # Non-empty dict means errors at this index
                    processed_item = {}
                    for sub_field, sub_errors in item.items():
                        if isinstance(sub_errors, list):
                            processed_item[sub_field] = [
                                extract_error_message(e) for e in sub_errors
                            ]
                        else:
                            processed_item[sub_field] = [
                                extract_error_message(sub_errors)
                            ]
                    processed[field].append(processed_item)
                else:
                    # Empty dict or non-dict item
                    processed[field].append(item)
        elif isinstance(field_errors, dict):
            # Recursively process nested dicts
            processed[field] = process_nested_errors(field_errors)
        elif isinstance(field_errors, list):
            # Extract messages from list of errors
            processed[field] = [extract_error_message(e) for e in field_errors]
        else:
            # Single error
            processed[field] = [extract_error_message(field_errors)]
    return processed


def combine_errors(
    serializer_errors: Dict[str, Any],
    multiple_values: Dict[str, Any],
    extra_fields: Dict[str, Any],
    files_errors: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Combine all error sources into a unified error structure
    """
    combined_errors = {}

    # Process serializer errors to extract ErrorDetail messages
    # Use preserve_list_structure=True to maintain the Django list error format
    processed_serializer_errors = process_nested_errors(
        serializer_errors, preserve_list_structure=True
    )

    # Process serializer errors
    for field, errors in processed_serializer_errors.items():
        if field in ["messageHistory", "message"] and isinstance(errors, list):
            # Clean list errors by formatting with index
            cleaned_errors = clean_list_errors(errors)
            if cleaned_errors:
                combined_errors[field] = cleaned_errors
        elif field == "meta" and isinstance(errors, dict):
            # Keep meta as nested structure
            combined_errors[field] = errors
        else:
            # For non-list fields, ensure it's a list of strings
            if isinstance(errors, list):
                combined_errors[field] = errors
            else:
                combined_errors[field] = (
                    [errors]
                    if isinstance(errors, str)
                    else normalize_error_value(errors)
                )

    # Process multiple values errors (already clean strings)
    for field, error in multiple_values.items():
        if field in combined_errors:
            combined_errors[field] = merge_error_lists(combined_errors[field], [error])
        else:
            combined_errors[field] = [error]

    # Process extra fields errors (already clean strings)
    for field, error in extra_fields.items():
        if field in ["messageHistory", "message"] and isinstance(error, list):
            # Handle list field extra field errors - these are already structured correctly
            if field in combined_errors:
                # Merge with existing list errors
                combined_errors[field].extend(error)
            else:
                combined_errors[field] = error
        elif field == "meta" and isinstance(error, dict):
            # Handle nested meta errors
            if "meta" not in combined_errors:
                combined_errors["meta"] = {}
            for meta_field, meta_error in error.items():
                combined_errors["meta"][meta_field] = [meta_error]
        else:
            # Handle simple field errors
            if field in combined_errors:
                combined_errors[field] = merge_error_lists(
                    combined_errors[field], [error]
                )
            else:
                combined_errors[field] = [error]

    # Process file errors (from Django, needs ErrorDetail extraction)
    processed_file_errors = {}
    for field, errors in files_errors.items():
        processed_file_errors[field] = normalize_error_value(errors)

    for field, errors in processed_file_errors.items():
        if field in combined_errors:
            combined_errors[field] = merge_error_lists(combined_errors[field], errors)
        else:
            combined_errors[field] = errors

    return combined_errors
