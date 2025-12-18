import sys

sys.path.append("/www/alpha/")

from pydantic import BaseModel

from apps.rubicon_v3.__function.__prompts import phatic_expression_detection_prompt
from apps.rubicon_v3.__function import __llm_call


class PhaticExpressionDetection(BaseModel):
    is_phatic_expression: bool


def phatic_expression_detection(
    user_query: str,
    model_name: str = "gpt-4.1-mini",
):
    """
    Detects if the user query contains phatic expressions.
    """
    prompt = phatic_expression_detection_prompt.PROMPT

    messages = [{"role": "system", "content": prompt}]

    user_content = [{"type": "text", "text": f"User Query: {user_query}"}]

    messages.append({"role": "user", "content": user_content})

    response = __llm_call.open_ai_call_structured(
        model_name, messages, PhaticExpressionDetection, 0.01, 0.1, 42
    )

    return response.get("is_phatic_expression", False)  # Default to False if not found
