import sys

sys.path.append("/www/alpha/")

import enum

from apps.rubicon_v3.__function.__utils import get_prompt_from_obj


class SearchResponseLayoutTypes(enum.Enum):
    SEARCH_INFORMATIVE_LAYOUT = "search_informative_layout"
    SEARCH_SIMPLE_LAYOUT = "search_simple_layout"


def get_response_layout(
    intelligence: str,
    channel: str,
    country_code: str,
    data_presence_dict: dict,
    is_simple_answer: bool,
):
    """
    Determine the response layout based on the intelligence data, channel, country code, and simple flag.
    """
    # Determine the tag based on the data presence dict
    has_single_product = data_presence_dict.get("has_single_product", False)
    has_multiple_products = data_presence_dict.get("has_multiple_products", False)

    layout_type = (
        SearchResponseLayoutTypes.SEARCH_SIMPLE_LAYOUT.value
        if is_simple_answer
        else SearchResponseLayoutTypes.SEARCH_INFORMATIVE_LAYOUT.value
    )

    tag = None
    if has_single_product:
        tag = "single_product"
    elif has_multiple_products:
        tag = "multiple_products"
    else:
        tag = "null"

    response_layout = get_prompt_from_obj(
        category_lv1=intelligence,
        channel=channel,
        country_code=country_code,
        response_type=layout_type,
        tag=tag,
    )

    return response_layout
