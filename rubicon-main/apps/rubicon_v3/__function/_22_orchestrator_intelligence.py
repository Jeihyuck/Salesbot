import sys

sys.path.append("/www/alpha/")
import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "alpha.settings")
django.setup()

from uuid import uuid4
from typing import Literal
from pydantic import create_model

from apps.rubicon_v3.__function import __llm_call, __utils
from apps.rubicon_v3.__function.definitions import intelligences, response_types
from apps.rubicon_v3.models import Intelligence_V2


def create_intelligence_type_model():
    # Get categories from database
    categories = list(
        Intelligence_V2.objects.values_list("intelligence", flat=True).distinct()
    )

    # Remove General Information category
    categories = [
        category
        for category in categories
        if category not in [intelligences.GENERAL_INFORMATION]
    ]

    # Convert to tuple for unpacking into Literal
    categories_tuple = tuple(categories)

    # Create dynamic model with Literal from database values
    if categories:
        IntelligenceDataType = create_model(
            "IntelligenceDataType", category=(Literal[categories_tuple], ...)
        )
    else:
        # Fallback if no categories found
        IntelligenceDataType = create_model("IntelligenceDataType", category=(str, ...))

    return IntelligenceDataType


class MetaColumns:
    CACHE = "cache"  # TODO: 사용안하는중. 테이블의 메타값 삭제 필요
    CLARIFICATION_REF = (
        "clarification_ref"  # TODO: 사용안하는중. 테이블의 메타값 삭제 필요
    )
    UNSTRUCTURED_INDEX_PRIORITY = "unstructred_index_priority"  # TODO: 오타가 있는게 맞음. 테이블 내용과 코드 내용 모두 수정해야함.
    WEB_SEARCH = "web_search"


def intelligence(
    top_query,
    gpt_model_name="gpt-4.1-mini",
    country_code="KR",
    temperature=0.01,
    top_p=1.0,
):
    # Get the prompt from db
    prompt = __utils.get_prompt_from_obj(
        country_code=country_code,
        response_type=response_types.INTELLIGENCE,
    )

    # 시스템 프롬프트로 메시지 초기화
    messages = [{"role": "system", "content": [{"type": "text", "text": prompt}]}]
    # 완성된 사용자 메시지 추가
    messages.append(
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": f"Classify the following user query: {top_query}",
                }
            ],
        }
    )

    # Create dynamic model for IntelligenceDataType
    _IntelligenceDataType = create_intelligence_type_model()

    response = __llm_call.open_ai_call_structured(
        gpt_model_name, messages, _IntelligenceDataType, temperature, top_p, 42
    )

    return response.get("category")


if __name__ == "__main__":
    query = "그랑데 세탁기 AI 구매 시 KB카드 포인트 적립 이벤트 있나요?"
    message_id = str(uuid4())

    intelligence_result = intelligence(query, message_id)
    print(intelligence_result)
