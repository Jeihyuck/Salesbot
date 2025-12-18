import sys

sys.path.append("/www/alpha/")

import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "alpha.settings")
django.setup()

from typing import Literal
from pydantic import create_model

from apps.rubicon_v3.models import Intelligence_V2
from apps.rubicon_v3.__function import __llm_call
from apps.rubicon_v3.__function.__utils import get_prompt_from_obj
from apps.rubicon_v3.__function._81_response_layout import ResponseLayoutTypes
from apps.rubicon_v3.__function.definitions import (
    intelligences,
    sub_intelligences,
)


def create_sub_intelligence_type_model(intelligence):
    # Get categories from database
    categories = list(
        Intelligence_V2.objects.filter(intelligence=intelligence)
        .values_list("sub_intelligence", flat=True)
        .distinct()
    )

    # Convert to tuple for unpacking into Literal
    categories_tuple = tuple(categories)

    # Create dynamic model with Literal from database values
    if categories:
        SubIntelligenceDataType = create_model(
            "SubIntelligenceDataType", sub_intelligence=(Literal[categories_tuple], ...)
        )
    else:
        # Fallback if no categories found
        SubIntelligenceDataType = create_model(
            "SubIntelligenceDataType", sub_intelligence=(str, ...)
        )

    return SubIntelligenceDataType


sub_intelligence_mapping_dict = {
    intelligences.INSTALLATION_INQUIRY: sub_intelligences.INSTALLATION_CONDITIONS_AND_STANDARDS,
    intelligences.ERROR_AND_FAILURE_RESPONSE: sub_intelligences.PROBLEM_SOLVING,
    intelligences.GENERAL_INFORMATION: sub_intelligences.GENERAL_INFORMATION,
}


def get_sub_intelligence(query, intelligence, country_code):
    # Check if defined in the mapping dictionary
    sub_intelligence = sub_intelligence_mapping_dict.get(intelligence)
    if sub_intelligence:
        return sub_intelligence

    # If not defined, use grab the sub intelligence prompt
    prompt = get_prompt_from_obj(
        category_lv1=intelligence,
        country_code=country_code,
        response_type=ResponseLayoutTypes.SUBDIVIDE_INTELLIGENCE.value,
    )

    # If prompt is None raise error
    if not prompt:
        raise ValueError(
            f"Sub intelligence generation prompt not found for intelligence: {intelligence}"
        )

    prompt = prompt.format(user_question=query)

    # Call the LLM
    messages = [{"role": "system", "content": [{"type": "text", "text": prompt}]}]

    # Create dynamic model for SubIntelligenceDataType
    _SubIntelligenceDataType = create_sub_intelligence_type_model(intelligence)

    result = __llm_call.open_ai_call_structured(
        "gpt-4.1-mini", messages, _SubIntelligenceDataType, 0.01, 0.1, 42
    )
    sub_intelligence = result.get("sub_intelligence")

    # To JJW: Sorry...
    if (
        country_code == "GB"
        and sub_intelligence == sub_intelligences.SET_PRODUCT_RECOMMENDATION
    ):
        sub_intelligence = sub_intelligences.CONDITIONAL_RECOMMENDATION
    elif (
        country_code == "GB"
        and sub_intelligence == sub_intelligences.SET_PRODUCT_DESCRIPTION
    ):
        sub_intelligence = sub_intelligences.PRODUCT_FEATURE

    return sub_intelligence