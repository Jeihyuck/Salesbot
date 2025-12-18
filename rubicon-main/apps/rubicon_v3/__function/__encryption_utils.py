import sys

sys.path.append("/www/alpha/")

import time
import json
from typing import Any

from apps.rubicon_v3.__external_api.__dkms_encode import DKMS_Encoder

dkms_encoder = DKMS_Encoder()


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


def recursive_encrypt_strings(obj: Any) -> Any:
    """
    Recursively traverse data structures and encrypt all string values (not keys)
    using DKMS encoder.

    This function handles:
    - Dictionaries: encrypts string values but preserves keys
    - Lists/tuples: encrypts string items
    - Sets: converts to list and encrypts string items
    - String values: encrypts them
    - Other types: returns as-is

    Args:
        obj: Any Python object to traverse and encrypt strings in

    Returns:
        Object with all string values encrypted
    """
    # Handle None
    if obj is None:
        return None

    # Handle dictionaries - encrypt values but preserve keys
    if isinstance(obj, dict):
        return {k: recursive_encrypt_strings(v) for k, v in obj.items()}

    # Handle lists - recursively process each item
    if isinstance(obj, list):
        return [recursive_encrypt_strings(item) for item in obj]

    # Handle tuples - recursively process each item and return as tuple
    if isinstance(obj, tuple):
        return tuple(recursive_encrypt_strings(item) for item in obj)

    # Handle sets - convert to list, process, and return as list
    if isinstance(obj, set):
        return [recursive_encrypt_strings(item) for item in obj]

    # Handle string values - encrypt them
    if isinstance(obj, str):
        try:
            return retry_function(dkms_encoder.getEncryptedValue, obj)
        except Exception as e:
            print(f"Error encrypting string: obj: {obj}, error: {e}")
            return "Error encrypting string"

    # For all other types (int, float, bool, datetime, etc.), return as-is
    return obj


def recursive_decrypt_strings(obj: Any) -> Any:
    """
    Recursively traverse data structures and decrypt all string values that start with "SE::"
    using DKMS encoder.

    This function handles:
    - Dictionaries: decrypts encrypted string values but preserves keys
    - Lists/tuples: decrypts encrypted string items
    - Sets: converts to list and decrypts encrypted string items
    - String values starting with "SE::": decrypts them
    - Other types: returns as-is

    Args:
        obj: Any Python object to traverse and decrypt strings in

    Returns:
        Object with all encrypted string values decrypted
    """
    # Handle None
    if obj is None:
        return None

    # Handle dictionaries - decrypt values but preserve keys
    if isinstance(obj, dict):
        return {k: recursive_decrypt_strings(v) for k, v in obj.items()}

    # Handle lists - recursively process each item
    if isinstance(obj, list):
        return [recursive_decrypt_strings(item) for item in obj]

    # Handle tuples - recursively process each item and return as tuple
    if isinstance(obj, tuple):
        return tuple(recursive_decrypt_strings(item) for item in obj)

    # Handle sets - convert to list, process, and return as list
    if isinstance(obj, set):
        return [recursive_decrypt_strings(item) for item in obj]

    # Handle string values that start with "SE::" - decrypt them
    if isinstance(obj, str) and retry_function(dkms_encoder.isEncrypted, obj):
        # Decrypt the value using DKMS encoder
        decrypted_value = retry_function(dkms_encoder.getDecryptedValue, obj)
        # Json parse the decrypted value if it is a valid JSON string
        try:
            return json.loads(decrypted_value)
        except json.JSONDecodeError:
            # If it's not a valid JSON string, return the decrypted value as-is
            return decrypted_value

    # For all other types (int, float, bool, datetime, non-encrypted strings, etc.), return as-is
    return obj
