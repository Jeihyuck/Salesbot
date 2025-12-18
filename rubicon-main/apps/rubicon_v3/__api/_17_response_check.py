import sys

sys.path.append("/www/alpha/")

import copy
import asyncio
import threading

from uuid import uuid4
from dataclasses import dataclass
from datetime import datetime
from bson.objectid import ObjectId

from apps.rubicon_v3.__function import __utils as utils
from apps.rubicon_v3.__function.definitions import (
    response_types,
    channels,
)
from apps.rubicon_v3.__function.__django_cache import CacheKey, DjangoCacheClient
from apps.rubicon_v3.__function._00_rubicon import (
    RubiconChatFlow,
    ChatFlowSectionNames,
    create_dataclass_from_dict,
)
from apps.rubicon_v3.__function.__exceptions import HttpStatus
from apps.rubicon_v3.__function._81_response_layout import get_response_layout
from apps.rubicon_v3.__function._80_response import response
from apps.rubicon_v3.__function._82_response_prompts import PromptLoader
from apps.rubicon_v3.__function.__prompts.guardrails.malicious_answer_prompt_by_type_dict import (
    get_guardrail_response_instructions,
)
from apps.rubicon_v3.__api._02_log_check import LogCheck


class ResponseCheck:
    @dataclass
    class ResponseCheckParams:
        type: str
        message: str
        message_history: list
        session_id: str
        country_code: str
        response_style: str
        retry: bool

    def __init__(self, input_params: ResponseCheckParams):
        self.input_params = input_params
        self.object_id = ObjectId()
        self.status = HttpStatus()
        self.channel = "DEV Debug"
        self.model = "rubicon"
        self.meta = {}
        self.user_id = "RESPONSE_CHECK"
        self.session_id = (
            str(uuid4()) if not input_params.session_id else input_params.session_id
        )
        self.message_id = str(uuid4())
        self.message_history = []
        self.language_code = "en"
        self.files = []
        self.department = "-"
        self.gpt_model_name = "gpt-4.1-mini"
        self.django_cache_client = DjangoCacheClient()
        self.use_cache = False
        self.gu_id = "default_gu_id"
        self.sa_id = "default_sa_id"
        self.jwt_token = "default_jwt_token"
        self.estore_sitecode = "default_estore_sitecode"
        self.session_expiry = 60 * 60 * 1  # 1 hour
        self.cache_expiry = 60 * 60 * 1  # 1 hour
        self.is_simple_answer = (
            True if input_params.response_style == "simple" else False
        )

    def response_check_mux(self):
        # Determine which function to call based on the input parameters
        if self.input_params.type == "gpt_compare":
            return self.gpt_response_check()
        elif self.input_params.type == "layout_compare":
            return self.layout_compare_check()
        elif self.input_params.type == "persona_no_layout":
            return self.layout_compare_check(remove_response_a=True)
        else:
            raise ValueError("Invalid type specified in input parameters")

    async def run_rubicon_pipeline(self):
        input_arguments = create_dataclass_from_dict(
            {
                "channel": self.channel,
                "country_code": self.input_params.country_code,
                "model": self.model,
                "meta": self.meta,
                "user_id": self.user_id,
                "session_id": self.session_id,
                "message_id": self.message_id,
                "message_history": self.message_history,
                "message": [
                    {
                        "type": "text",
                        "content": self.input_params.message,
                        "role": "user",
                        "message_id": self.message_id,
                        "created_on": datetime.now().isoformat(),
                    }
                ],
                "lng": self.language_code,
                "gu_id": self.gu_id,
                "sa_id": self.sa_id,
                "jwt_token": self.jwt_token,
                "estore_sitecode": self.estore_sitecode,
                "department": self.department,
            },
            RubiconChatFlow.InputArguments,
        )
        input_files = create_dataclass_from_dict(
            {"files": self.files}, RubiconChatFlow.InputFiles
        )

        chat_flow = RubiconChatFlow(
            input_arguments=input_arguments,
            input_files=input_files,
            object_id=self.object_id,
            use_cache=self.use_cache,
            stream=True,
            simple=self.is_simple_answer,
            status=self.status,
        )

        # Run the chat flow
        chat_flow.enqueue_chat_flow()

        async for chunk in chat_flow.get_stream_response():
            pass

        return

    def get_combined_data(self):
        # Initialize the Django session
        utils.init_django_cache_session(
            self.session_id,
            self.message_id,
            self.user_id,
            self.channel,
            utils.get_language_name(
                self.language_code, self.input_params.country_code, self.channel
            ),
            self.session_expiry,
        )

        # If message history is provided in input parameters, use it
        if self.input_params.message_history:
            self.django_cache_client.update(
                CacheKey.message_history(self.session_id),
                self.input_params.message_history,
                self.session_expiry,
            )

        # Run the Rubicon pipeline to get the merge rag data
        asyncio.run(self.run_rubicon_pipeline())

        # Get the debug log
        log_check = LogCheck(LogCheck.LogCheckParams(lookup_id=self.message_id))
        debug_log = log_check.get_logs()

        # Get the merge rag data from the debug log
        if not debug_log:
            raise ValueError(
                f"No debug log found for the given message_id: '{self.message_id}'"
            )

        if "data" not in debug_log or "debug_content" not in debug_log["data"]:
            raise ValueError(
                f"No debug content found in the debug log for message_id: '{self.message_id}'"
            )

        combined_data = {}
        for debug_content in debug_log["data"]["debug_content"]:
            if (
                debug_content.get("section_name")
                == ChatFlowSectionNames.PARALLEL_QUERY_ANALYZER_INTELLIGENCE_NER_CONTEXT_DETERMINATION
            ):
                if not debug_content.get("intelligence_data"):
                    raise ValueError("No intelligence data found in the debug content")
                combined_data["intelligence_data"] = debug_content["intelligence_data"]
            elif (
                debug_content.get("section_name")
                == ChatFlowSectionNames.PARALLEL_STANDARD_NER_ASSISTANT_SUB_INTELLIGENCE
            ):
                if not debug_content.get("sub_intelligence_data"):
                    raise ValueError(
                        "No sub intelligence data found in the debug content"
                    )
                combined_data["sub_intelligence_data"] = debug_content[
                    "sub_intelligence_data"
                ]
            elif (
                debug_content.get("section_name")
                == ChatFlowSectionNames.RESPONSE_LAYOUT
            ):
                if not debug_content.get("response_layout_debug"):
                    raise ValueError(
                        "No response layout debug data found in the debug content"
                    )
                combined_data["response_layout_debug"] = debug_content[
                    "response_layout_debug"
                ]
            elif debug_content.get("section_name") == ChatFlowSectionNames.MERGE_DATA:
                if debug_content.get("response_input_data") is None:
                    raise ValueError(
                        "No response input data found in the debug content"
                    )
                combined_data["merge_rag_data"] = debug_content["response_input_data"]
            elif (
                debug_content.get("section_name")
                == ChatFlowSectionNames.RESPONSE_GENERATION
            ):
                if not debug_content.get("response_path"):
                    raise ValueError("No response path found in the debug content")
                if not debug_content.get("gpt_model_name"):
                    raise ValueError("No GPT model name found in the debug content")
                if not debug_content.get("user_content"):
                    raise ValueError("No user query found in the debug content")
                if not debug_content.get("output_language"):
                    raise ValueError("No output language found in the debug content")
                if not debug_content.get("full_response"):
                    raise ValueError("No full response found in the debug content")
                combined_data["response_path"] = debug_content["response_path"]
                combined_data["full_response"] = debug_content["full_response"]
                combined_data["gpt_model_name"] = debug_content["gpt_model_name"]
                combined_data["user_query"] = debug_content["user_content"]
                combined_data["output_language"] = debug_content["output_language"]
            elif (
                debug_content.get("section_name")
                == ChatFlowSectionNames.EXCEPTION_HANDLING
            ):
                if not debug_content.get("gpt_model_name"):
                    raise ValueError(
                        "No GPT model name found in the exception handling"
                    )
                if not debug_content.get("output_language"):
                    raise ValueError(
                        "No output language found in the exception handling"
                    )
                if not debug_content.get("full_response"):
                    raise ValueError("No full response found in the exception handling")
                if not debug_content.get("response_path"):
                    raise ValueError("No response path found in the exception handling")
                if not debug_content.get("guardrail_type"):
                    raise ValueError(
                        "No guardrail type found in the exception handling"
                    )
                if not debug_content.get("exception_type"):
                    raise ValueError(
                        "No exception type found in the exception handling"
                    )
                if not debug_content.get("exception_message"):
                    raise ValueError(
                        "No exception message found in the exception handling"
                    )
                combined_data["response_path"] = debug_content["response_path"]
                combined_data["full_response"] = debug_content["full_response"]
                combined_data["gpt_model_name"] = debug_content["gpt_model_name"]
                combined_data["output_language"] = debug_content["output_language"]
                combined_data["guardrail_type"] = debug_content["guardrail_type"]
                combined_data["exception_type"] = debug_content["exception_type"]
                combined_data["exception_message"] = debug_content["exception_message"]

        return combined_data

    def get_input_data(self, combined_data):
        input_data = {}

        # Grab the most up to date response format from db
        # If the response path is INFORMATIVE_RESPONSE, we need to generate the response format
        if combined_data["response_path"] == response_types.INFORMATIVE_RESPONSE:
            new_response_format = {}
            # Check if the response format is present in the combined data
            if "response_format" not in combined_data["merge_rag_data"]:
                raise ValueError(
                    "No response format found in the combined data for Informative Response"
                )

            for response_format_query in combined_data["merge_rag_data"][
                "response_format"
            ].keys():
                response_layout = get_response_layout(
                    intelligence=combined_data["intelligence_data"][
                        response_format_query
                    ],
                    sub_intelligence=combined_data["sub_intelligence_data"][
                        response_format_query
                    ],
                    channel=self.channel,
                    country_code=self.input_params.country_code,
                    data_presence_dict=combined_data["response_layout_debug"][
                        response_format_query
                    ],
                    is_simple_answer=self.is_simple_answer,
                )
                if response_layout:
                    new_response_format[response_format_query] = response_layout

            # Update the merge rag data with the new response format
            combined_data["merge_rag_data"]["response_format"] = new_response_format

        # If the response path is one of the exception handling paths,
        # Grab the exception handling data from the combined data
        if combined_data["response_path"] in [
            response_types.EMPTY_STREAM_DATA_RESPONSE,
            response_types.TIMEOUT_RESPONSE,
            response_types.PROCESS_ERROR_RESPONSE,
            response_types.INFORMATION_RESTRICTED_RESPONSE,
            response_types.TEXT_GUARDRAIL_RESPONSE,
            response_types.CODE_MAPPING_ERROR_RESPONSE,
            response_types.STORE_MAPPING_ERROR_RESPONSE,
        ]:
            input_data.update(
                {
                    "output_language": combined_data["output_language"],
                    "guardrail_response_instructions": get_guardrail_response_instructions(
                        combined_data["guardrail_type"],
                        self.input_params.country_code,
                        self.channel,
                    ),
                    "complement_code_mapping_error": combined_data["exception_message"],
                    "store_mapping_error_data": combined_data["exception_message"],
                    "original_country_code": self.input_params.country_code,
                }
            )

        # If the response path is not an exception handling path,
        # Update input data with the merge rag data
        else:
            # Get the input data for the successful pipeline run
            input_data.update(combined_data["merge_rag_data"])
            input_data.update(
                {
                    "output_language": combined_data["output_language"],
                    "country_code": (
                        "KR" if self.input_params.country_code == "KR" else "GB"
                    ),
                    "original_country_code": self.input_params.country_code,
                    "message_history": self.input_params.message_history,
                    "image_files": self.files,
                    "original_query": self.input_params.message,
                    "user_query": combined_data["user_query"],
                }
            )

        return input_data

    def get_parallel_responses(self, *generators):
        """
        Process multiple generators in parallel and return their results.

        Args:
            *generators: Variable number of generators to process (max 3)

        Returns:
            Tuple of responses in the same order as the input generators
        """
        if len(generators) > 3:
            raise ValueError("Maximum of 3 generators supported")

        def run_response_generator(generator):
            if generator is None:
                return ""

            full_response = ""
            start_of_stream_flag = True
            is_markdown_yield = True
            skip_iteration = 0
            for chunk in generator:
                if chunk.startswith("### LLM CALL META"):
                    continue

                if start_of_stream_flag:
                    if is_markdown_yield:
                        is_markdown_yield = False
                    elif skip_iteration > 1:
                        start_of_stream_flag = False
                    skip_iteration += 1

                full_response += chunk

            _, full_response = utils.clean_final_response(full_response)

            return full_response

        # Create container to store the results
        results = {i: None for i in range(len(generators))}

        # Define thread function
        def process_response(index):
            results[index] = run_response_generator(generators[index])

        # Create and start threads
        threads = []
        for i in range(len(generators)):
            thread = threading.Thread(target=process_response, args=(i,))
            threads.append(thread)
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        # Return responses as a tuple in the same order as input generators
        return tuple(results[i] for i in range(len(generators)))

    def gpt_response_check(self):
        # Get the combined data of past pipeline run if available
        cache_key = CacheKey.response_format_check(
            self.input_params.message,
            self.input_params.session_id,
            self.input_params.country_code,
            self.input_params.type,
        )
        combined_data = self.django_cache_client.get(cache_key)
        if combined_data is None:
            combined_data = self.get_combined_data()

            # Store the merge rag data in the cache
            self.django_cache_client.store(cache_key, combined_data, self.cache_expiry)

        # Get the input data for the response generation
        input_data = self.get_input_data(combined_data)

        # If the response path is Predefined Response, return the full response for all
        if combined_data["response_path"] == response_types.PREDEFINED_RESPONSE:
            # Regardless of retry, we return the full response
            _, response_a = utils.clean_final_response(combined_data["full_response"])
            response_b = response_a  # For consistency, we can return the same response
            return {
                "success": True,
                "data": {
                    "response_a": response_a,
                    "response_a_model": combined_data["gpt_model_name"],
                    "response_b": response_b,
                    "response_b_model": "gpt-4.1-mini",
                },
                "input_data": {
                    "intelligence_data": combined_data.get("intelligence_data"),
                    "sub_intelligence_data": combined_data.get("sub_intelligence_data"),
                    "response_path": combined_data.get("response_path"),
                },
                "message": "",
            }

        # Check if the informative base prompt needs to be used
        use_informative_base = combined_data[
            "response_path"
        ] == response_types.INFORMATIVE_RESPONSE and any(
            utils.should_use_base(sub_intelligence)
            for sub_intelligence in combined_data["sub_intelligence_data"].values()
        )

        # Get the system prompt
        prompt_loader = PromptLoader(
            combined_data["response_path"],
            self.channel,
            self.input_params.country_code,
            self.is_simple_answer,
            use_informative_base=use_informative_base,
        )
        response_base_prompt, _ = prompt_loader.get_prompts()

        # Generate response a if retry is True, otherwise use the cached response
        response_a_generator = None
        if self.input_params.retry:
            response_a_generator = response(
                input_data,
                response_base_prompt,
                combined_data["response_path"],
                combined_data["gpt_model_name"],
                0.4,
                42,
            )

        response_b_generator = response(
            input_data,
            response_base_prompt,
            combined_data["response_path"],
            "gpt-4.1-mini",
            0.4,
            42,
        )

        response_a, response_b = self.get_parallel_responses(
            response_a_generator, response_b_generator
        )

        # If retry is false, use the full response in combined_data for response_a
        if not self.input_params.retry:
            _, response_a = utils.clean_final_response(combined_data["full_response"])

        return {
            "success": True,
            "data": {
                "response_a": response_a,
                "response_a_model": combined_data["gpt_model_name"],
                "response_b": response_b,
                "response_b_model": "gpt-4.1-mini",
            },
            "input_data": {
                "intelligence_data": combined_data.get("intelligence_data"),
                "sub_intelligence_data": combined_data.get("sub_intelligence_data"),
                "response_path": combined_data.get("response_path"),
            },
            "message": "",
        }

    ###################### Layout Compare Check ######################

    def get_all_response_layouts(self, combined_data):
        response_layouts = {}
        for response_format_query, response_layout_debug in combined_data[
            "response_layout_debug"
        ].items():
            response_layout = get_response_layout(
                intelligence=combined_data["intelligence_data"][response_format_query],
                sub_intelligence=combined_data["sub_intelligence_data"][
                    response_format_query
                ],
                channel=channels.SPRINKLR,
                country_code=self.input_params.country_code,
                data_presence_dict=response_layout_debug,
                is_simple_answer=self.is_simple_answer,
            )
            if response_layout:
                response_layouts[response_format_query] = response_layout
        return response_layouts

    def layout_compare_check(self, remove_response_a=False):
        # Get the combined data of past pipeline run if available
        cache_key = CacheKey.response_format_check(
            self.input_params.message,
            self.input_params.session_id,
            self.input_params.country_code,
            self.input_params.type,
        )
        combined_data = self.django_cache_client.get(cache_key)
        if combined_data is None:
            combined_data = self.get_combined_data()

            # Store the merge rag data in the cache
            self.django_cache_client.store(cache_key, combined_data, self.cache_expiry)

        # Get the input data for the response generation
        input_data_a = self.get_input_data(combined_data)

        # If the response path is Predefined Response, return the full response for all
        if combined_data["response_path"] == response_types.PREDEFINED_RESPONSE:
            # Regardless of retry, we return the full response
            _, response_a = utils.clean_final_response(combined_data["full_response"])
            response_b = response_a
            response_c = response_a  # For consistency, we can return the same response

            # Remove response_a if remove_response_a is True
            if remove_response_a:
                return {
                    "success": True,
                    "data": {
                        "response_a": response_b,
                        "response_a_model": "All Layouts",
                        "response_b": response_c,
                        "response_b_model": "Persona | No Layout",
                    },
                    "input_data": {
                        "intelligence_data": combined_data.get("intelligence_data"),
                        "sub_intelligence_data": combined_data.get(
                            "sub_intelligence_data"
                        ),
                        "response_path": combined_data.get("response_path"),
                    },
                    "message": "",
                }
            # Else return all responses
            return {
                "success": True,
                "data": {
                    "response_a": response_a,
                    "response_a_model": "Dynamic Layouts",
                    "response_b": response_b,
                    "response_b_model": "All Layouts",
                    "response_c": response_c,
                    "response_c_model": "Persona | No Layout",
                },
                "input_data": {
                    "intelligence_data": combined_data.get("intelligence_data"),
                    "sub_intelligence_data": combined_data.get("sub_intelligence_data"),
                    "response_path": combined_data.get("response_path"),
                },
                "message": "",
            }

        # Check if the informative base prompt needs to be used
        use_informative_base = combined_data[
            "response_path"
        ] == response_types.INFORMATIVE_RESPONSE and any(
            utils.should_use_base(sub_intelligence)
            for sub_intelligence in combined_data["sub_intelligence_data"].values()
        )

        # Get the system prompt
        prompt_loader = PromptLoader(
            combined_data["response_path"],
            self.channel,
            self.input_params.country_code,
            self.is_simple_answer,
            use_informative_base=use_informative_base,
        )
        response_base_prompt_a, _ = prompt_loader.get_prompts()

        # Generate response a if retry is True, otherwise use the cached response
        response_a_generator = None
        if self.input_params.retry:
            response_a_generator = response(
                input_data_a,
                response_base_prompt_a,
                combined_data["response_path"],
                combined_data["gpt_model_name"],
                0.4,
                42,
            )

        # All layout version
        input_data_b = copy.deepcopy(input_data_a)
        response_base_prompt_b = response_base_prompt_a
        # If the response path is informative response, get the persona and informative base prompts
        if combined_data["response_path"] == response_types.INFORMATIVE_RESPONSE:
            # Get all the response format data from combined_data
            input_data_b["response_format"] = self.get_all_response_layouts(
                combined_data
            )

            # Load the full informative prompt
            prompt_loader = PromptLoader(
                response_types.INFORMATIVE_RESPONSE,
                self.channel,
                self.input_params.country_code,
                self.is_simple_answer,
                use_informative_base=True,
            )
            response_base_prompt_b, _ = prompt_loader.get_prompts()

        response_b_generator = response(
            input_data_b,
            response_base_prompt_b,
            combined_data["response_path"],
            combined_data["gpt_model_name"],
            0.4,
            42,
        )

        # Persona Only version
        input_data_c = copy.deepcopy(input_data_b)
        response_base_prompt_c = response_base_prompt_a
        if combined_data["response_path"] == response_types.INFORMATIVE_RESPONSE:
            # Remove all the response format data from input_data
            input_data_c["response_format"] = {}

            # Load the persona prompt
            prompt_loader = PromptLoader(
                response_types.PERSONA,
                self.channel,
                self.input_params.country_code,
                self.is_simple_answer,
            )
            response_base_prompt_c, _ = prompt_loader.get_prompts()

        response_c_generator = response(
            input_data_c,
            response_base_prompt_c,
            combined_data["response_path"],
            combined_data["gpt_model_name"],
            0.4,
            42,
        )

        # Get the parallel responses but handle the case where response_b is not needed
        response_a, response_b, response_c = None, None, None
        if remove_response_a:
            response_b, response_c = self.get_parallel_responses(
                response_b_generator, response_c_generator
            )
        else:
            response_a, response_b, response_c = self.get_parallel_responses(
                response_a_generator, response_b_generator, response_c_generator
            )

        # If retry is false, use the full response in combined_data for response_a
        if not self.input_params.retry:
            _, response_a = utils.clean_final_response(combined_data["full_response"])

        data = {}
        if not remove_response_a:
            data["response_a"] = response_a
            data["response_a_model"] = "Dynamic Layouts"
            data["response_b"] = response_b
            data["response_b_model"] = "All Layouts"
            data["response_c"] = response_c
            data["response_c_model"] = "Persona | No Layout"
        else:
            data["response_a"] = response_b
            data["response_a_model"] = "All Layouts"
            data["response_b"] = response_c
            data["response_b_model"] = "Persona | No Layout"

        return {
            "success": True,
            "data": data,
            "message": "",
        }
