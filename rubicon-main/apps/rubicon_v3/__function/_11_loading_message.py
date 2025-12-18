import sys
from unittest.mock import DEFAULT

from apps.rubicon_v3.__function.__prompts import loading_message_prompt
import json

from typing import List, Dict, Any
from pydantic import BaseModel
from django.core.files.uploadedfile import InMemoryUploadedFile

from apps.rubicon_v3.__function import __llm_call, __utils


class LoadingMessage(BaseModel):
    loading_message: str


def loading_message_generation(
    main_query,
    files,
    message_history,
    language,
    country_code,
    model_name="gpt-4.1-mini",
):
    """
    로딩 메시지를 생성하는 함수
    :param main_query: 메인 질의
    :param files: 파일 리스트
    :param message_history: 메시지 히스토리 리스트
    :param message_id: 메시지 ID
    :param model_name: 모델 이름 (기본값: gpt-4o-mini)
    :return: 응답 객체
    """
    prompt = loading_message_prompt.PROMPT.format(language=language)

    print(prompt)

    # 시스템 프롬프트로 메시지 초기화
    messages = [{"role": "system", "content": [{"type": "text", "text": prompt}]}]

    # 메시지 히스토리 추가
    for message in message_history:
        if message.get("role") == "user":
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
    user_prompt = f"User: {main_query}"
    user_content.append({"type": "text", "text": user_prompt})

    # 완성된 사용자 메시지 추가
    messages.append({"role": "user", "content": user_content})

    response = __llm_call.open_ai_call_structured(
        model_name, messages, LoadingMessage, 0.4, 0.1, 42
    )

    return response
