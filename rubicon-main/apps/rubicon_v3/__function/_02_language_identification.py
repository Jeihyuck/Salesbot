import sys

sys.path.append("/www/alpha")

import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "alpha.settings")
django.setup()

from pydantic import BaseModel

from apps.rubicon_v3.__function.__prompts import query_translation_prompt
from apps.rubicon_v3.__function import __llm_call, __utils
from apps.rubicon_v3.__function.definitions import response_types


class QueryTranslation(BaseModel):
    translated_query: str


class LanguageIdentification(BaseModel):
    language_english_name: str
    reasoning: str


def lang_detect_with_gpt(
    original_query,
    message_history,
    default_language,
    gpt_model_name="gpt-4.1-mini",
    temperature=0.01,
    top_p=1.0,
):
    """
    GPT 모델을 사용하여 언어를 감지하는 함수
    :param original_query: 원본 질의
    :param message_id: 메시지 ID
    :param gpt_model_name: GPT 모델 이름 (기본값: gpt-4o-mini)
    :return: 감지된 언어
    """
    # Get the prompt from db
    prompt = __utils.get_prompt_from_obj(
        response_type=response_types.LANGUAGE_IDENTIFICATION
    )
    prompt = prompt.replace("{default_language}", default_language)

    messages = [{"role": "system", "content": [{"type": "text", "text": prompt}]}]

    # Add message history to the messages
    for message in message_history:
        messages.append(message)

    user_content = []
    user_content.append({"type": "text", "text": original_query})
    messages.append({"role": "user", "content": user_content})

    # Call the OpenAI API to identify the language
    response = __llm_call.open_ai_call_structured(
        gpt_model_name, messages, LanguageIdentification, temperature, top_p, 42
    )

    return response["language_english_name"], response["reasoning"]


def translate_queries(
    query: str,
    language: str,
    country_code: str,
    gpt_model_name="gpt-4.1-mini",
    temperature=0.01,
    top_p=1.0,
):
    # Translate the rewritten queries if needed
    if (country_code == "KR" and language.upper() == "KOREAN") or (
        country_code != "KR" and language.upper() == "ENGLISH"
    ):
        # No translation needed, return the original queries
        return query

    # Get the query translation prompt
    prompt = query_translation_prompt.PROMPT

    # Replace the input queries and target language in the prompt
    prompt = prompt.replace("{INPUT_QUERY}", query)
    prompt = prompt.replace("{TARGET_LANGUAGE}", language)

    messages = [{"role": "system", "content": prompt}]

    response = __llm_call.open_ai_call_structured(
        gpt_model_name, messages, QueryTranslation, temperature, top_p, 42
    )

    return response["translated_query"]
