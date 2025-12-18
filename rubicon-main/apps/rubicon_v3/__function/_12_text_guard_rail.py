import sys

sys.path.append("/www/alpha/")
import os
import django
import openai

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "alpha.settings")
django.setup()
from typing import List, Literal
from pydantic import BaseModel
from apps.rubicon_v3.__function import __llm_call, __utils
from apps.rubicon_v3.__function.definitions import response_types


class InputGuardrailAnalysis(BaseModel):
    decision: Literal["ATTACK", "BENIGN"]
    category: Literal["S4", "S5", "S6", "S7", "S8", "S9", "S10", "None"]
    reasoning: str


class ModerationGuardrail(BaseModel):
    flagged: bool
    confidence: float
    reason: str


def execute_guardrail(messages, response_format, model_name):
    """
    Guardrail execution function to call the LLM with the provided messages and response format.

    Args:
        messages (list): The list of messages to send to the LLM.
        response_format (BaseModel): The expected response format.
        model_name (str): The name of the model to use for analysis.

    Returns:
        dict: The result of the guardrail analysis.
    """
    return __llm_call.open_ai_call_structured(
        model_name, messages, response_format, 0.01, 0.1, 42
    )


def rubicon_text_guardrail(query: str, message_history: list, model_name="gpt-4.1"):
    """
    텍스트 가드레일을 처리하는 함수
    Args:
        query (str): 사용자 질의
        message_history (list): 메시지 히스토리 리스트
        model_name (str): 모델 이름 (기본값: gpt-4.1)
        prompt (str): 프롬프트 텍스트
    """
    # Grab the prompt from db
    prompt = __utils.get_prompt_from_obj(
        category_lv1="rubicon_text_guardrail", response_type=response_types.GUARDRAIL
    )

    # Initialize messages with the system prompt
    messages = [{"role": "system", "content": prompt}]

    if message_history:
        # Add message history
        for message in message_history[-4:]:
            messages.append(message)

    # Create user message
    messages.append({"role": "user", "content": query})
    response = execute_guardrail(messages, InputGuardrailAnalysis, model_name)
    return response


def moderation_text_guardrail(
    query: str, message_history: List[dict], model_name="gpt-4.1"
):
    """
    Moderation guardrail function to analyze text content for harmful or inappropriate material.

    Args:
        query (str): The user query to be analyzed.
        message_history (List[dict]): The history of messages in the conversation.
        model_name (str): The name of the model to use for analysis.
        prompt (str): The prompt to use for the moderation analysis.

    Returns:
        dict: The result of the moderation analysis.
    """
    # Grab the prompt from db
    prompt = __utils.get_prompt_from_obj(
        category_lv1="moderation_text_guardrail", response_type=response_types.GUARDRAIL
    )

    # Initialize messages with the system prompt
    messages = [{"role": "system", "content": prompt}]

    if message_history:
        # Add message history
        for message in message_history:
            messages.append(message)

    # Create user message
    messages.append({"role": "user", "content": query})

    # Execute the guardrail analysis
    try:
        response = execute_guardrail(messages, ModerationGuardrail, model_name)
    except openai.BadRequestError as e:
        response = {
            "flagged": True,  # Default to flagged if there's a bad request error (it could signify the content filter was triggered)
            "confidence": 1.0,
            "reason": str(e),  # Capture the error message for debugging
        }
    return response


def injection_text_guardrail(
    query: str, message_history: List[dict], model_name="gpt-4.1"
):
    """
    Injection guardrail function to analyze text content for potential injection attacks.
    Args:
        query (str): The user query to be analyzed.
        message_history (List[dict]): The history of messages in the conversation.
        model_name (str): The name of the model to use for analysis.
        prompt (str): The prompt to use for the injection analysis.

    Returns:
        dict: The result of the injection analysis.
    """
    # Grab the prompt from db
    prompt = __utils.get_prompt_from_obj(
        category_lv1="injection_text_guardrail", response_type=response_types.GUARDRAIL
    )

    # Initialize messages with the system prompt
    messages = [{"role": "system", "content": prompt}]

    if message_history:
        # Add message history
        for message in message_history:
            messages.append(message)

    # Create user message
    messages.append({"role": "user", "content": query})

    # Execute the guardrail analysis
    try:
        response = execute_guardrail(messages, ModerationGuardrail, model_name)
    except openai.BadRequestError as e:
        response = {
            "flagged": True,  # Default to flagged if there's a bad request error (it could signify the content filter was triggered)
            "confidence": 1.0,
            "reason": str(e),  # Capture the error message for debugging
        }
    return response
