import sys

sys.path.append("/www/alpha/")
import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "alpha.settings")
django.setup()

from uuid import uuid4
from dataclasses import dataclass

from apps.rubicon_v3.__function import (
    _12_text_guard_rail,
    _82_response_prompts,
    __utils as utils,
)
from apps.rubicon_v3.__function.definitions import channels
from apps.rubicon_v3.__function.__llm_call import open_ai_call
from apps.rubicon_v3.__function.__prompts.guardrails.malicious_answer_prompt_by_type_dict import (
    get_guardrail_response_instructions,
)
from apps.rubicon_v3.__function.__prompts.guardrails import (
    malicious_answer_prompt_common,
)


class Guardrail:
    @dataclass
    class GuardrailParams:
        message: str
        language_code: str
        country_code: str

    def __init__(self, input_params: GuardrailParams):
        self.input_params = input_params

    def generate_guardrail_response(self, category: str, message_id: str):
        response_instructions = get_guardrail_response_instructions(
            category, self.input_params.country_code, channels.DEV_DEBUG
        )
        if not response_instructions:
            return {
                "success": False,
                "data": "",
                "message": "Invalid category for guardrail response",
            }

        prompt_input_data = {
            "guardrail_response_instructions": [
                {"response_instructions": response_instructions}
            ],
            "output_language": utils.get_language_name(
                self.input_params.language_code,
                self.input_params.country_code,
                channels.DEV_DEBUG,
            ),
        }

        # Generate Input Prompt
        input_prompt = _82_response_prompts.dict_to_multiline_comment(prompt_input_data)

        # Initialize messages with system prompt
        messages = [
            {
                "role": "system",
                "content": [
                    {"type": "text", "text": malicious_answer_prompt_common.PROMPT}
                ],
            }
        ]

        messages.append(
            {
                "role": "system",
                "content": [{"type": "text", "text": input_prompt + "\n[DATA-END]"}],
            }
        )

        guardrail_response = open_ai_call(
            model_name="gpt-4.1-mini",
            messages=messages,
            temperature=0.4,
            seed=42,
            stream=False,
            message_id=message_id,
        )

        return {"success": True, "data": guardrail_response, "message": ""}

    def get_guardrail_data(self):
        """
        Get the guardrail data for input message
        """
        message_history = []
        message_id = str(uuid4())

        text_guardrail_response = _12_text_guard_rail.rubicon_text_guardrail(
            query=self.input_params.message,
            message_history=message_history,
        )

        if not text_guardrail_response:
            return {
                "success": False,
                "data": {},
                "message": "Failed to get guardrail data",
            }

        # Grab the guardrail response if decision is ATTACK
        if text_guardrail_response.get("decision") == "ATTACK":
            category = text_guardrail_response.get("category")
            response_dict = self.generate_guardrail_response(
                category=category, message_id=message_id
            )
            if response_dict.get("success") is False:
                return {
                    "success": False,
                    "data": {},
                    "message": f"Failed to generate guardrail response. Message: {response_dict.get('message')}",
                }
            text_guardrail_response["response"] = response_dict.get("data")
        else:
            text_guardrail_response["response"] = ""

        return {
            "success": True,
            "data": text_guardrail_response,
            "message": "Guardrail data retrieved successfully",
        }
