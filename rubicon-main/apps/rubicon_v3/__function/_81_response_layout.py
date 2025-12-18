import sys

sys.path.append("/www/alpha/")

import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "alpha.settings")
django.setup()

import enum
import uuid

from apps.rubicon_v3.__function.__utils import get_prompt_from_obj
from apps.rubicon_v3.__function.definitions import (
    intelligences,
    sub_intelligences,
)


class ResponseLayoutTypes(enum.Enum):
    SUBDIVIDE_INTELLIGENCE = "subdivide_intelligence"
    INFORMATIVE_LAYOUT = "informative_layout"
    SIMPLE_LAYOUT = "simple_layout"


def get_response_layout(
    intelligence: str,
    sub_intelligence: str,
    channel: str,
    country_code: str,
    data_presence_dict: dict,
    is_simple_answer: bool,
):
    has_extended_info = None
    has_bundle_spec_info = None
    has_highlevel_spec_info = None
    has_review_info = None

    has_extended_info = data_presence_dict.get("has_extended_info", False)
    has_bundle_spec_info = data_presence_dict.get("has_bundle_spec_info", False)
    has_highlevel_spec_info = data_presence_dict.get("has_highlevel_spec_info", False)
    has_review_info = data_presence_dict.get("has_review_info", False)

    layout_type = (
        ResponseLayoutTypes.SIMPLE_LAYOUT.value
        if is_simple_answer
        else ResponseLayoutTypes.INFORMATIVE_LAYOUT.value
    )

    response_layout = None

    tag = None
    if intelligence == intelligences.PRODUCT_DESCRIPTION:
        if has_highlevel_spec_info and sub_intelligence not in [
            sub_intelligences.PRODUCT_REVIEW,
            sub_intelligences.PRODUCT_LINEUP_DESCRIPTION,
            sub_intelligences.SET_PRODUCT_DESCRIPTION,
        ]:
            tag = "highlevel"
        elif has_bundle_spec_info and sub_intelligence not in [
            sub_intelligences.PRODUCT_REVIEW,
            sub_intelligences.PRODUCT_LINEUP_DESCRIPTION,
            sub_intelligences.SET_PRODUCT_DESCRIPTION,
        ]:
            tag = "bundle"
        elif sub_intelligence == "Product Review":
            if has_review_info:
                tag = "review"
            else:
                tag = "no_review"
        else:
            tag = "null"
    elif intelligence == intelligences.PRODUCT_RECOMMENDATION:
        if sub_intelligence not in [
            sub_intelligences.CONSUMABLES_ACCESSORIES_RECOMMENDATION,
            sub_intelligences.PERSONALIZED_RECOMMENDATION,
            sub_intelligences.PRODUCT_LINEUP_RECOMMENDATION,
            sub_intelligences.SET_PRODUCT_RECOMMENDATION,
        ]:
            if has_extended_info:
                tag = "extended_info"
            else:
                tag = "no_extended_info"
    else:
        tag = "null"

    response_layout = get_prompt_from_obj(
        category_lv1=intelligence,
        category_lv2=sub_intelligence,
        channel=channel,
        country_code=country_code,
        response_type=layout_type,
        tag=tag,
    )

    return response_layout


if __name__ == "__main__":
    intelligence = intelligences.SERVICE_AND_REPAIR_GUIDE
    country_code = "KR"
    query = "갤럭시 S24 액정 교체 비용을 알고 싶어요. S25 구매가능한 곳도 알려주세요."
    message_id = uuid.uuid4()

    from apps.rubicon_v3.__function._32_sub_intelligence import get_sub_intelligence

    sub_intelligence = get_sub_intelligence(
        query=query,
        intelligence=intelligence,
        country_code=country_code,
        message_id=message_id,
    )

    response_layout = get_response_layout(
        intelligence, sub_intelligence, country_code, {}, False
    )
    print(f"Sub Intelligence: {sub_intelligence}")
    print(f"Response Layout: {response_layout}")
