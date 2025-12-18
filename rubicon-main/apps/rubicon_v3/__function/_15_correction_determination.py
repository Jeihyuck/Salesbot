import sys

sys.path.append("/www/alpha/")

import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "alpha.settings")
django.setup()

from typing import Literal
from pydantic import BaseModel

from apps.rubicon_v3.__function import __llm_call as llm_call, __utils as utils
from apps.rubicon_v3.__function.definitions import response_types


class CorrectionDetermination(BaseModel):
    determination: Literal["true", "false", "recommendation"]
    reasoning: str


def correction_determination(
    main_query,
    message_history,
    files,
    country_code,
    model_name="gpt-4.1-mini",
):
    """
    Context Determination Function
    """
    # Get the prompt from the prompt template db
    prompt = utils.get_prompt_from_obj(
        country_code=country_code, response_type=response_types.CORRECTION_DETERMINATION
    )

    if not prompt:
        raise ValueError("Prompt for correction determination not found.")

    # 시스템 프롬프트로 메시지 초기화
    messages = [{"role": "system", "content": [{"type": "text", "text": prompt}]}]

    # 메시지 히스토리 추가
    for message in message_history:
        messages.append(message)

    # 성공적으로 처리된 모든 이미지를 수집
    processed_images = []
    for file in files:
        try:
            image_dict = utils.process_image_file(file)
            processed_images.append(image_dict)
        except Exception as e:
            print(f"Error processing image {file.name}: {str(e)}")
            continue

    # 이미지와 텍스트를 포함한 사용자 메시지 생성
    user_content = []

    # 이미지가 있는 경우 먼저 추가
    if processed_images:
        user_content.extend(processed_images)

    user_content.append({"type": "text", "text": main_query})

    # 완성된 사용자 메시지 추가
    messages.append({"role": "user", "content": user_content})

    response = llm_call.open_ai_call_structured(
        model_name, messages, CorrectionDetermination, 0.01, 0.1, 42
    )

    return response


if __name__ == "__main__":

    original_query = "내 핸드폰 모델 알려줘"
    message_history = []
    files = []
    country_code = "KR"

    determination = correction_determination(
        original_query,
        message_history,
        files,
        country_code,
        model_name="gpt-4.1-mini",
    )

    print("Determination:", determination)
