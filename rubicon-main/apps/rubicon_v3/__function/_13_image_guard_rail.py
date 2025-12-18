import sys

sys.path.append("/www/alpha/")

import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "alpha.settings")
django.setup()

from pydantic import BaseModel

from apps.rubicon_v3.__function import __llm_call, __utils
from typing import Literal

from apps.rubicon_v3.__function.definitions import response_types


class ImageGuardrail(BaseModel):
    image_guardrail_flag: Literal["Yes", "No"]
    reasoning: str


def image_guardrail(files, model_name="gpt-4.1-mini"):
    """
    이미지 가드레일을 처리하는 함수
    :param files: 이미지 파일 리스트
    :param model_name: 모델 이름 (기본값: gpt-4o-mini)
    :return: 응답 객체
    """
    # Grab the prompt from db
    prompt = __utils.get_prompt_from_obj(
        category_lv1="image_guardrail", response_type=response_types.GUARDRAIL
    )

    # Initialize the prompt
    messages = [{"role": "system", "content": [{"type": "text", "text": prompt}]}]

    # Process each image file
    processed_images = []
    for file in files:
        try:
            image_dict = __utils.process_image_file(file)
            processed_images.append(image_dict)
        except Exception as e:
            print(f"Error processing image {file.name}: {str(e)}")
            continue

    # Add processed images to messages
    if processed_images:
        messages.append({"role": "user", "content": processed_images})

    response = __llm_call.open_ai_call_structured(
        model_name, messages, ImageGuardrail, 0.01, 0.1, 42
    )

    return response
