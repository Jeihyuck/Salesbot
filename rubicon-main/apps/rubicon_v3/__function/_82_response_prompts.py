import sys

sys.path.append("/www/alpha/")

import os
import django
from django.db.models import Q

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "alpha.settings")
django.setup()

import enum

from types import MappingProxyType

from apps.rubicon_v3.__function.__prompts.guardrails import (
    image_answer_prompt,
    malicious_answer_prompt_common,
)
from apps.rubicon_v3.__function.__prompts import (
    response_modification_prompt,
)
from apps.rubicon_v3.__function.definitions import response_types
from apps.rubicon_v3.models import Prompt_Template, Exception_Msg
from datetime import datetime


class Prompts(enum.Enum):
    PERSONA = MappingProxyType(
        {"source": "db", "name": "persona", "response_type": response_types.PERSONA}
    )
    SIMPLE_PERSONA = MappingProxyType(
        {
            "source": "db",
            "name": "simple_persona",
            "response_type": response_types.SIMPLE_PERSONA,
        }
    )
    INFORMATIVE_BASE = MappingProxyType(
        {
            "source": "db",
            "name": "informative_base",
            "response_type": response_types.INFORMATIVE_BASE,
        }
    )
    ORIGINAL_QUERY_BASE = MappingProxyType(
        {
            "source": "db",
            "name": "original_query_base",
            "response_type": response_types.ORIGINAL_QUERY_BASE,
        }
    )
    SIMPLE_BASE = MappingProxyType(
        {
            "source": "db",
            "name": "simple_base",
            "response_type": response_types.SIMPLE_BASE,
        }
    )
    SEARCH_SUMMARY_BASE = MappingProxyType(
        {
            "source": "db",
            "name": "search_summary",
            "response_type": response_types.SEARCH_SUMMARY_BASE,
        }
    )
    EXCEPTION_AI_SUBSCRIPTION = MappingProxyType(
        {
            "source": "db",
            "name": "exception_ai_subscription",
            "response_type": response_types.EXCEPTION,
            "category_lv1": "ai subscription",
        }
    )
    EXCEPTION_CODE_MAPPING_ERROR = MappingProxyType(
        {
            "source": "db",
            "name": "exception_code_mapping_error",
            "response_type": response_types.EXCEPTION,
            "category_lv1": "code mapping error",
        }
    )
    EXCEPTION_INVALID_MODEL_NAME = MappingProxyType(
        {
            "source": "db",
            "name": "exception_invalid_model_name",
            "response_type": response_types.EXCEPTION,
            "category_lv1": "invalid model name",
        }
    )
    EXCEPTION_EMPTY_ORIGINAL_QUERY = MappingProxyType(
        {
            "source": "db",
            "name": "exception_empty_original_query",
            "response_type": response_types.EXCEPTION,
            "category_lv1": "empty original query",
        }
    )
    EXCEPTION_EMPTY_STREAM_DATA = MappingProxyType(
        {
            "source": "db",
            "name": "exception_empty_stream_data",
            "response_type": response_types.EXCEPTION,
            "category_lv1": "empty stream data",
        }
    )
    EXCEPTION_INFORMATION_RESTRICTED = MappingProxyType(
        {
            "source": "db",
            "name": "exception_information_restricted",
            "response_type": response_types.EXCEPTION,
            "category_lv1": "information restricted",
        }
    )
    EXCEPTION_PRE_EMBARGO_QUERY = MappingProxyType(
        {
            "source": "db",
            "name": "exception_pre_embargo_query",
            "response_type": response_types.EXCEPTION,
            "category_lv1": "pre embargo query",
        }
    )
    EXCEPTION_PROCESS_ERROR = MappingProxyType(
        {
            "source": "db",
            "name": "exception_process_error",
            "response_type": response_types.EXCEPTION,
            "category_lv1": "process error",
        }
    )
    EXCEPTION_REDIRECT_REQUEST = MappingProxyType(
        {
            "source": "db",
            "name": "exception_redirect_request",
            "response_type": response_types.EXCEPTION,
            "category_lv1": "redirect request",
        }
    )
    EXCEPTION_TIMEOUT = MappingProxyType(
        {
            "source": "db",
            "name": "exception_timeout",
            "response_type": response_types.EXCEPTION,
            "category_lv1": "timeout",
        }
    )
    EXCEPTION_UNHANDLED_REQUEST = MappingProxyType(
        {
            "source": "db",
            "name": "exception_unhandled_request",
            "response_type": response_types.EXCEPTION,
            "category_lv1": "unhandled request",
        }
    )
    EXCEPTION_STORE_MAPPING_ERROR = MappingProxyType(
        {
            "source": "db",
            "name": "exception_store_mapping_error",
            "response_type": response_types.EXCEPTION,
            "category_lv1": "store mapping error",
        }
    )
    EXCEPTION_NO_DATA_FOUND = MappingProxyType(
        {
            "source": "db",
            "name": "exception_no_data_found",
            "response_type": response_types.EXCEPTION,
            "category_lv1": "no data found",
        }
    )
    EXCEPTION_REWRITE_CORRECTION_FAILURE = MappingProxyType(
        {
            "source": "db",
            "name": "exception_rewrite_correction_failure",
            "response_type": response_types.EXCEPTION,
            "category_lv1": "rewrite correction failure",
        }
    )
    GENERAL_INFORMATION = MappingProxyType(
        {
            "source": "db",
            "name": "general_information",
            "response_type": response_types.EXCEPTION,
            "category_lv1": "general information",
        }
    )
    GENERAL_BASE = MappingProxyType(
        {
            "source": "db",
            "name": "general_base",
            "response_type": response_types.EXCEPTION,
            "category_lv1": "general base",
        }
    )
    RE_ASKING = MappingProxyType(
        {"source": "db", "name": "re_asking", "response_type": response_types.REASKING}
    )
    PREDEFINED = MappingProxyType(
        {
            "source": "db",
            "name": "predefined",
            "response_type": response_types.PREDEFINED,
        }
    )
    MALICIOUS_IMAGE_ANSWER = MappingProxyType(
        {
            "source": "local",
            "name": "malicious_image_answer",
            "response_type": response_types.MALICIOUS_IMAGE_ANSWER,
            "prompt": image_answer_prompt.PROMPT,
        }
    )
    MALICIOUS_ANSWER_COMMON = MappingProxyType(
        {
            "source": "local",
            "name": "malicious_answer_common",
            "response_type": response_types.MALICIOUS_ANSWER_COMMON,
            "prompt": malicious_answer_prompt_common.PROMPT,
        }
    )


RESPONSE_PATH_PROMPT_LIST = MappingProxyType(
    {
        response_types.TEXT_GUARDRAIL_RESPONSE: [Prompts.MALICIOUS_ANSWER_COMMON],
        response_types.IMAGE_GUARDRAIL_RESPONSE: [Prompts.MALICIOUS_IMAGE_ANSWER],
        response_types.INFORMATIVE_RESPONSE: [
            Prompts.PERSONA,
            Prompts.INFORMATIVE_BASE,
        ],
        response_types.ORIGINAL_QUERY_RESPONSE: [
            Prompts.PERSONA,
            Prompts.ORIGINAL_QUERY_BASE,
        ],
        response_types.GENERAL_RESPONSE: [
            Prompts.PERSONA,
            Prompts.GENERAL_BASE,
        ],
        response_types.REASKING_RESPONSE: [Prompts.RE_ASKING],
        response_types.TIMEOUT_RESPONSE: [Prompts.EXCEPTION_TIMEOUT],
        response_types.PROCESS_ERROR_RESPONSE: [Prompts.EXCEPTION_PROCESS_ERROR],
        response_types.PRE_EMBARGO_QUERY_RESPONSE: [
            Prompts.EXCEPTION_PRE_EMBARGO_QUERY
        ],
        response_types.PREDEFINED_RESPONSE: [
            Prompts.PERSONA,
            Prompts.PREDEFINED,
        ],
        response_types.REDIRECT_REQUEST_RESPONSE: [Prompts.EXCEPTION_REDIRECT_REQUEST],
        response_types.EMPTY_STREAM_DATA_RESPONSE: [
            Prompts.EXCEPTION_EMPTY_STREAM_DATA
        ],
        response_types.EMPTY_ORIGINAL_QUERY_RESPONSE: [
            Prompts.EXCEPTION_EMPTY_ORIGINAL_QUERY
        ],
        response_types.INFORMATION_RESTRICTED_RESPONSE: [
            Prompts.EXCEPTION_INFORMATION_RESTRICTED
        ],
        response_types.CODE_MAPPING_ERROR_RESPONSE: [
            Prompts.EXCEPTION_CODE_MAPPING_ERROR
        ],
        response_types.INVALID_MODEL_NAME_RESPONSE: [
            Prompts.PERSONA,
            Prompts.EXCEPTION_INVALID_MODEL_NAME,
        ],
        response_types.STORE_MAPPING_ERROR_RESPONSE: [
            Prompts.EXCEPTION_STORE_MAPPING_ERROR,
        ],
        response_types.AI_SUBSCRIPTION_RESPONSE: [Prompts.EXCEPTION_AI_SUBSCRIPTION],
        response_types.NO_DATA_FOUND_RESPONSE: [Prompts.EXCEPTION_NO_DATA_FOUND],
        response_types.REWRITE_CORRECTION_FAILURE_RESPONSE: [
            Prompts.EXCEPTION_REWRITE_CORRECTION_FAILURE,
        ],
        response_types.PERSONA: [Prompts.PERSONA],
        response_types.SIMPLE_RESPONSE: [Prompts.SIMPLE_PERSONA, Prompts.SIMPLE_BASE],
        response_types.SEARCH_SUMMARY_RESPONSE: [Prompts.SEARCH_SUMMARY_BASE],
        response_types.CS_RESPONSE: [],
    }
)


class PromptLoader:
    def __init__(
        self,
        response_type: str,
        channel: str,
        country_code: str,
        is_simple_answer: bool,
        filter_tag: str = None,
        use_informative_base: bool = True,
        intelligence_info: list = None,
        sub_intelligence_info: list = None,
    ):
        self.response_type = (
            response_types.SIMPLE_RESPONSE
            if is_simple_answer and response_type == response_types.INFORMATIVE_RESPONSE
            else response_type
        )
        self.channel = channel
        self.country_code = country_code
        self.is_simple_answer = is_simple_answer
        self.filter_tag = (
            "simple"
            if is_simple_answer
            and response_type
            in [
                response_types.GENERAL_RESPONSE,
                response_types.INVALID_MODEL_NAME_RESPONSE,
                response_types.ORIGINAL_QUERY_RESPONSE,
            ]
            else filter_tag
        )
        self.use_informative_base = use_informative_base
        self.intelligence_info = intelligence_info or []
        self.sub_intelligence_info = sub_intelligence_info or []

    def modify_prompt(self, prompt: str, dict_response_type: str):
        if dict_response_type not in [
            response_types.PERSONA,
            response_types.INFORMATIVE_BASE,
            response_types.SIMPLE_BASE,
            response_types.SEARCH_SUMMARY_BASE,
            response_types.EXCEPTION,
        ]:
            return prompt

        # If the response type is an exception, replace the {EXCEPTION_MSG} tag
        if dict_response_type == response_types.EXCEPTION:
            replacement_text = get_exception_message(
                self.response_type,
                self.channel,
                self.country_code,
                self.intelligence_info,
                self.sub_intelligence_info,
            )
            if replacement_text:
                prompt = prompt.replace("{EXCEPTION_MSG}", replacement_text)
            else:
                prompt = prompt.replace(
                    "{EXCEPTION_MSG}",
                    """문의해 주셔서 감사합니다.
아쉽게도 안내드릴 수 있는 범위를 벗어난 내용이라 정확한 답변을 드리기 어려운 점 양해 부탁드려요.
현재 관련 내용을 준비 중이니, 조금만 기다려 주시면 감사하겠습니다.""",
                )
            return prompt

        # Add current datetime to the prompt
        current_datetime = datetime.now().isoformat()
        prompt = prompt.replace("{CURRENT_DATETIME}", current_datetime)

        # Modify the prompt to remove the replace tag
        if not self.is_simple_answer or self.country_code != "GB":
            prompt = prompt.replace("{BRITISH_ENGLISH_INSTRUCTION}", "")
            return prompt

        # Modify the prompt
        if dict_response_type == response_types.SIMPLE_BASE:
            replacement_text = response_modification_prompt.BRITISH_ENGLISH_INSTRUCTION
            prompt = prompt.replace("{BRITISH_ENGLISH_INSTRUCTION}", replacement_text)
            return prompt

        # If no modifications are needed, return the original prompt
        return prompt

    def get_prompt_from_obj(self, prompt_template_filter_criteria):
        prompt_obj = Prompt_Template.objects.filter(
            prompt_template_filter_criteria
        ).first()

        if not prompt_obj:
            return None

        if not prompt_obj.prompt:
            raise ValueError(
                f"Prompt is empty for Response Type: {self.response_type}, Channel: {self.channel}, Country Code: {self.country_code}"
            )

        prompt = prompt_obj.prompt
        return prompt

    def load_prompts(self):
        prompt_list = []
        prompt_name_list = []

        prompt_dict_list = RESPONSE_PATH_PROMPT_LIST.get(self.response_type, [])
        if not prompt_dict_list:
            return prompt_list, prompt_name_list

        for prompt_dict in prompt_dict_list:
            if prompt_dict.value["source"] == "db":
                prompt_template_filter_criteria = Q(active=True)
                prompt_template_filter_criteria &= Q(country_code=self.country_code)
                prompt_template_filter_criteria &= Q(
                    response_type=prompt_dict.value["response_type"]
                )
                if self.filter_tag and prompt_dict.value.get("check_tag", False):
                    prompt_template_filter_criteria &= Q(tag=self.filter_tag)
                else:
                    prompt_template_filter_criteria &= Q(tag__isnull=True)

                if (
                    "category_lv1" in prompt_dict.value
                    and prompt_dict.value["category_lv1"]
                ):
                    prompt_template_filter_criteria &= Q(
                        category_lv1=prompt_dict.value["category_lv1"]
                    )

                # If informative base, filter by channel and check for dynamic flag
                dynamic_flag = False
                prompt = None
                if (
                    prompt_dict.value["response_type"]
                    == response_types.INFORMATIVE_BASE
                ):
                    # First try to see if the dynamic flag is set
                    dynamic_filter_criteria = prompt_template_filter_criteria.copy()
                    dynamic_filter_criteria &= Q(
                        channel_filter__contains=[self.channel + "_dynamic"]
                    )
                    prompt = self.get_prompt_from_obj(dynamic_filter_criteria)
                    if prompt:
                        dynamic_flag = True

                # If no dynamic flag or prompt not found, use the regular filter criteria
                if not prompt or not dynamic_flag:
                    # Add channel filter if informative base, simple base, or persona (simple persona as well)
                    if prompt_dict.value["response_type"] in [
                        response_types.INFORMATIVE_BASE,
                        response_types.SIMPLE_BASE,
                        response_types.PERSONA,
                        response_types.SIMPLE_PERSONA,
                    ]:
                        prompt_template_filter_criteria &= Q(
                            channel_filter__contains=[self.channel]
                        )

                    # Get the prompt from the database
                    prompt = self.get_prompt_from_obj(prompt_template_filter_criteria)

                # If informative base and dynamic flag is True, check if we should skip
                # based on the use_informative_base flag
                if (
                    (
                        prompt_dict.value["response_type"]
                        == response_types.INFORMATIVE_BASE
                    )
                    and dynamic_flag
                    and not self.use_informative_base
                ):
                    continue

                # Modify prompts
                prompt = self.modify_prompt(prompt, prompt_dict.value["response_type"])

                prompt_list.append(prompt)
                prompt_name_list.append(prompt_dict.value["name"])

            elif prompt_dict.value["source"] == "local":
                # Modify prompts
                prompt = self.modify_prompt(
                    prompt_dict.value["prompt"], prompt_dict.value["response_type"]
                )

                prompt_list.append(prompt)
                prompt_name_list.append(prompt_dict.value["name"])

            else:
                raise ValueError(
                    f"Invalid prompt source: {prompt_dict.value['source']}"
                )

        return prompt_list, prompt_name_list

    def get_prompts(self):
        """
        Load the prompts based on the response type and channel.
        """
        prompt_list, prompt_name_list = self.load_prompts()

        if prompt_list is None:
            raise ValueError(
                f"No prompts found for Response Type: {self.response_type}, Channel: {self.channel}, Country Code: {self.country_code}"
            )

        return "\n".join([prompt for prompt in prompt_list]), prompt_name_list


# Input Prompt Data Mapping Dictionary
# ====================================
input_prompt_data_mapping = {
    response_types.TEXT_GUARDRAIL_RESPONSE: {
        "prompt_inputs": ["guardrail_response_instructions", "output_language"]
    },
    response_types.PREDEFINED_RESPONSE: {
        "open_ai_inputs": ["user_query"],
        "prompt_inputs": ["sample_response_data", "reference_data", "output_language"],
    },
    response_types.IMAGE_GUARDRAIL_RESPONSE: {"prompt_inputs": ["output_language"]},
    response_types.INFORMATIVE_RESPONSE: {
        "open_ai_inputs": [
            "image_files",
            "user_query",
            "message_history",
        ],
        "prompt_inputs": [
            "response_format",
            "other_company_expression",
            "product_model_info",
            "product_common_spec_info",
            "product_spec_info",
            "set_product_spec_info",
            "high_level_product_spec_info",
            "product_lineup_price_info",
            "product_price_info",
            "promotion_info",
            "add_on_info",
            "review_statistics_info",
            "review_summary_info",
            "review_category_info",
            "sample_response_data",
            "reference_data",
            "exception_response_data",
            "out_of_range_flag",
            "managed_data",
            "structured_relevant_data",
            "unstructured_relevant_data",
            "output_language",
            "country_code",
        ],
    },
    response_types.ORIGINAL_QUERY_RESPONSE: {
        "open_ai_inputs": [
            "original_query",
            "message_history",
        ],
        "prompt_inputs": [
            "output_language",
            "unstructured_relevant_data",
        ],
    },
    response_types.TIMEOUT_RESPONSE: {"prompt_inputs": ["output_language"]},
    response_types.PRE_EMBARGO_QUERY_RESPONSE: {"prompt_inputs": ["output_language"]},
    response_types.PROCESS_ERROR_RESPONSE: {"prompt_inputs": ["output_language"]},
    response_types.REDIRECT_REQUEST_RESPONSE: {"prompt_inputs": ["output_language"]},
    response_types.EMPTY_STREAM_DATA_RESPONSE: {"prompt_inputs": ["output_language"]},
    response_types.EMPTY_ORIGINAL_QUERY_RESPONSE: {
        "prompt_inputs": ["output_language"]
    },
    response_types.INFORMATION_RESTRICTED_RESPONSE: {
        "prompt_inputs": ["output_language"]
    },
    response_types.CODE_MAPPING_ERROR_RESPONSE: {
        "prompt_inputs": ["output_language", "complement_code_mapping_error"]
    },
    response_types.INVALID_MODEL_NAME_RESPONSE: {
        "open_ai_inputs": ["user_query", "message_history"],
        "prompt_inputs": [
            "output_language",
            "managed_data",
            "unstructured_relevant_data",
        ],
    },
    response_types.STORE_MAPPING_ERROR_RESPONSE: {
        "prompt_inputs": ["output_language", "store_mapping_error_data"]
    },
    response_types.AI_SUBSCRIPTION_RESPONSE: {"prompt_inputs": ["output_language"]},
    response_types.NO_DATA_FOUND_RESPONSE: {"prompt_inputs": ["output_language"]},
    response_types.REWRITE_CORRECTION_FAILURE_RESPONSE: {
        "prompt_inputs": ["output_language"]
    },
    response_types.GENERAL_RESPONSE: {
        "open_ai_inputs": ["user_query", "message_history"],
        "prompt_inputs": [
            "output_language",
            "unstructured_relevant_data",
        ],
    },
    response_types.REASKING_RESPONSE: {
        "open_ai_inputs": ["user_query", "message_history"],
        "prompt_inputs": ["output_language"],
    },
    # Search SUmmary Response Types
    response_types.SEARCH_SUMMARY_RESPONSE: {
        "open_ai_inputs": ["user_query"],
        "prompt_inputs": [
            "output_language",
            "system_suggestion",
            "other_company_expression",
            "set_product_model_info",
            "product_model_info",
            "product_common_spec_info",
            "product_spec_info",
            "set_product_spec_info",
            "unstructured_relevant_data",
            "response_format",
        ],
    },
}


# Input Prompt Generation
# =======================
def dict_to_multiline_comment(input_dict):
    """
    Convert a dictionary into a multi-line comment string with formatted keys and values.

    Args:
        input_dict (dict): Dictionary with keys in snake_case and values.

    Returns:
        str: Multi-line formatted string.
    """
    formatted_lines = []

    for key, value in input_dict.items():
        if value:
            # Convert snake_case to Title Case with spaces
            formatted_key = key.replace("_", " ").title()
            # Add the formatted line
            formatted_lines.append(f"${formatted_key}$ \n{value}")

    # Join lines into a multi-line string
    return f'"""\n' + "\n".join(formatted_lines) + '\n"""'


# Exception Message Retrieval
# ============================
def get_exception_message(
    exception_type, channel, country_code, intelligence_info, sub_intelligence_info
):
    """
    Retrieve the exception message based on the exception type, channel, and country code.

    Args:
        exception_type (str): Type of the exception.
        channel (str): Channel for which the exception message is needed.
        country_code (str): Country code for localization.
        intelligence_info (list): List of intelligence information.
        sub_intelligence_info (list): List of sub-intelligence information.

    Returns:
        str: Exception message.
    """
    # Get the disclaimer message
    exception_msg = (
        Exception_Msg.objects.filter(
            channel__contains=[channel],
            intelligence__contains=intelligence_info,
            sub_intelligence__contains=sub_intelligence_info,
            country_code=country_code,
            type=exception_type,
        )
        .values_list("message", flat=True)
        .first()
    )

    # If no disclaimer message is found, use the default one (This may still be None)
    if not exception_msg:
        exception_msg = (
            Exception_Msg.objects.filter(
                channel__isnull=True,
                intelligence__isnull=True,
                sub_intelligence__isnull=True,
                country_code__isnull=True,
                type=exception_type,
            )
            .values_list("message", flat=True)
            .first()
        )

    return exception_msg


if __name__ == "__main__":

    prompt_loader = PromptLoader(
        response_type="informative_response",
        channel="DEV_DEBUG",
        country_code="KR",
        is_simple_answer=False,
    )

    prompt, prompt_name_list = prompt_loader.get_prompts()
    print(prompt)
    print(prompt_name_list)

#
