import sys
sys.path.append('/www/alpha')

import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "alpha.settings")
django.setup()

from apps.rubicon_v3.__function import __django_cache

from django.core.cache import cache

def clear_all_cache():
    """
    Deletes all keys from the cache.
    """
    try:
        cache.clear()
        print("All cache cleared successfully.")
    except Exception as e:
        print(f"Error clearing cache: {e}")


def check_cache(key: str) -> bool:
    """
    Check if the key exists in the cache.

    Args:
        key (str): The key to check in the cache.

    Returns:
        bool: True if the key exists in the cache, False otherwise.
    """
    return cache.get(key) is not None


if __name__ == "__main__":
    # pass
    # cache_key = "비스포크 TV의 성능은 어떤가요?" + "cache"
    # cache_client = __django_cache.DjangoCacheClient()
    # cache_client.delete(cache_key)
    # print("Cache cleared successfully")

    # clear all cache
    clear_all_cache()

    # check if key exists in cache
    # key = "Circle to Search라는 기능이 있던데, 어떤 기능이야?" + "cache" + "DEV Debug" + "KR"
    # print(check_cache(key))