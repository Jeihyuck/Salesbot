import sys

sys.path.append("/www/alpha/")
import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "alpha.settings")
django.setup()

from apps.rubicon_v3.models import Web_Cache

# Get the ID of the card info to parse
# TOBE : This should be dynamic in the future
ID = 70903


def parse_card_info() -> str:
    """Parse and retrieve card benefits information from Web_Cache.
    
    Fetches the latest card benefits information for KR from the cache.
    
    Returns:
        str: Card benefits content string, empty string if not found
    """
    instance = (
        Web_Cache.objects.filter(query="KR card benefits information")
        .order_by("-created_on")
        .values_list("content", flat=True)
        .first()
    )

    if instance:
        try:
            return instance
        except IndexError:
            return ""

    return ""


def main() -> None:
    """Main function to demonstrate card benefits parsing."""
    chunk = parse_card_info()

    print(chunk)


if __name__ == "__main__":
    main()
