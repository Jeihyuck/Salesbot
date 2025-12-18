import sys

sys.path.append("/www/alpha/")

import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "alpha.settings")
django.setup()

from typing import Literal
from pydantic import BaseModel

from apps.rubicon_v3.__function import __llm_call, __utils
from apps.rubicon_v3.__function.definitions import response_types
from apps.rubicon_v3.__function._82_response_prompts import dict_to_multiline_comment


class Determination(BaseModel):
    determination: Literal["original", "rewritten"]
    reasoning: str


def context_determination(
    main_query,
    rewrite_queries,
    message_history,
    files,
    model_name="gpt-4.1-mini",
):
    """
    Context Determination Function
    """
    # Get the prompt from the prompt template db
    prompt = __utils.get_prompt_from_obj(
        response_type=response_types.CONTEXT_DETERMINATION
    )

    if not prompt:
        raise ValueError("Prompt for context determination not found.")

    # 시스템 프롬프트로 메시지 초기화
    messages = [{"role": "system", "content": [{"type": "text", "text": prompt}]}]

    # 메시지 히스토리 추가
    for message in message_history:
        messages.append(message)

    # 성공적으로 처리된 모든 이미지를 수집
    processed_images = []
    for file in files:
        try:
            image_dict = __utils.process_image_file(file)
            processed_images.append(image_dict)
        except Exception as e:
            print(f"Error processing image {file.name}: {str(e)}")
            continue

    # 이미지와 텍스트를 포함한 사용자 메시지 생성
    user_content = []

    # 이미지가 있는 경우 먼저 추가
    if processed_images:
        user_content.extend(processed_images)

    # 텍스트 콘텐츠 추가
    input_prompt = dict_to_multiline_comment(
        {"Original Query": main_query, "ReWrite Queries": rewrite_queries}
    )
    user_content.append({"type": "text", "text": input_prompt})

    # 완성된 사용자 메시지 추가
    messages.append({"role": "user", "content": user_content})

    response = __llm_call.open_ai_call_structured(
        model_name, messages, Determination, 0.01, 0.1, 42
    )

    return response


if __name__ == "__main__":
    from apps.rubicon_v3.__function._10_rewrite import re_write_history
    from uuid import uuid4

    original_query = "나 TV하나 사고 싶은데 추천좀"
    message_history = []
    mentioned_products = []
    files = []
    message_id = str(uuid4())
    rewrite_queries = re_write_history(
        original_query,
        files,
        message_history,
        message_id,
        mentioned_products,
    )

    print("Main Query:", original_query)
    print("Rewrite Queries:", rewrite_queries.get("re_write_query_list"))

    determination = context_determination(
        original_query,
        rewrite_queries,
        message_history,
        files,
        message_id,
    )

    print("Determination:", determination)
