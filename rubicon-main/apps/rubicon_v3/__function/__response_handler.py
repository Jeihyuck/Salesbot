import sys

sys.path.append("/www/alpha/")

import time
import copy
import traceback

from datetime import datetime
from typing import TYPE_CHECKING

from apps.rubicon_v3.__function import __utils as utils, __django_rq as django_rq
from apps.rubicon_v3.__function.__simulate_stream import stream_markdown
from apps.rubicon_v3.__function._80_response import response
from apps.rubicon_v3.__function._82_response_prompts import PromptLoader
from apps.rubicon_v3.__function._83_cs_response import (
    cs_mixed_response,
    cs_stream_response,
)
from apps.rubicon_v3.__function.definitions import response_types
from apps.rubicon_v3.__function.__exceptions import (
    InvalidCodeMapping,
    InvalidStore,
    ResponseGenerationFailureException,
    EmptyStreamData,
)
from apps.rubicon_v3.__function.__prompts.guardrails.malicious_answer_prompt_by_type_dict import (
    get_guardrail_response_instructions,
)
from apps.rubicon_v3.__external_api._14_azure_email_alert import (
    send_process_error_alert,
)
from alpha.settings import VITE_OP_TYPE

if TYPE_CHECKING:
    from apps.rubicon_v3.__function._00_rubicon import RubiconChatFlow


class ResponseHandler:
    def __init__(
        self,
        chat_flow: "RubiconChatFlow",
        stream: bool,
        error: bool,
        cached_response: str = None,
    ):
        self.chat_flow = chat_flow
        self.stream = stream
        self.error = error
        self.full_response = ""
        self.cached_response = cached_response
        self.input_data = {
            "object_id": str(self.chat_flow.object_id),
            "output_language": (self.chat_flow.orchestrator.language),
            "original_country_code": self.chat_flow.log_data.country_code,
        }
        self.prompt_name_list = []

    def _call_response(self, response_base_prompt: str, web_links: list = None):
        """
        Prepare the data and call the response method.
        """
        # Initialize flags and counters
        start_of_stream_flag = True
        skip_iteration = 0
        first_response = True
        processing_time_start = time.time()

        # Get the stream iterator
        stream_iterator = response(
            self.input_data,
            response_base_prompt,
            self.chat_flow.log_data.response_path,
            self.chat_flow.gpt_model_name,
            0.01,
            42,
            web_links=web_links,
        )

        # For CS related scenarios, use the CS response iterator
        if not self.error and self.chat_flow.orchestrator.all_cs_hit:
            stream_iterator = cs_stream_response(self.input_data)

        # For CS mixed scenarios, use the CS mixed response iterator
        elif not self.error and self.chat_flow.orchestrator.cs_queries:
            stream_iterator = cs_mixed_response(
                self.chat_flow.log_data.cs_data,
                self.input_data,
                response_base_prompt,
                self.chat_flow.log_data.response_path,
                self.chat_flow.gpt_model_name,
                0.4,
                42,
                web_links=web_links,
            )

        # If error scenario:
        # Show the environment type for ProcessError and ProcessTimeout in DEV and STG
        if self.chat_flow.log_data.response_path in [
            response_types.PROCESS_ERROR_RESPONSE,
            response_types.TIMEOUT_RESPONSE,
        ]:
            if VITE_OP_TYPE in ["DEV", "STG"]:
                yield f"data: {VITE_OP_TYPE} Environment<br>\n\n"

        # Generate the response
        for chunk in stream_iterator:
            if chunk.startswith("### LLM CALL META"):
                # Logging the LLM call metadata
                if first_response:
                    elapsed_time = round(time.time() - self.chat_flow.start_time, 4)
                    self.chat_flow.timing_logs.append(
                        (
                            f"200 Response {chunk.replace('### LLM CALL META : ', '')}",
                            elapsed_time,
                        )
                    )
                    self.chat_flow.timing_logs.append(
                        (
                            "200 Response Time Stamp",
                            datetime.now().strftime("%H:%M:%S.%f")[:-3],
                        )
                    )
                first_response = False
            else:
                if start_of_stream_flag:
                    # If the first response is received, log the start of the stream
                    if skip_iteration > 0:
                        elapsed_time = round(time.time() - self.chat_flow.start_time, 4)
                        self.chat_flow.pipeline_elapsed_time = elapsed_time
                        self.chat_flow.timing_logs.append(
                            (
                                "LLM Processing Time",
                                round(time.time() - processing_time_start, 4),
                            )
                        )
                        self.chat_flow.timing_logs.append(
                            (
                                "Start of Stream",
                                elapsed_time,
                            )
                        )
                        self.chat_flow.timing_logs.append(
                            (
                                "Start of Stream Time Stamp",
                                datetime.now().strftime("%H:%M:%S.%f")[:-3],
                            )
                        )
                        start_of_stream_flag = False
                    skip_iteration += 1
                yield chunk

    def _stream_simulator(self):
        """
        Simulate the streaming of the response.
        """
        # Initialize flags
        start_of_stream_flag = True
        for chunk in stream_markdown(self.cached_response.strip()):
            if start_of_stream_flag:
                elapsed_time = round(time.time() - self.chat_flow.start_time, 4)
                self.chat_flow.pipeline_elapsed_time = elapsed_time
                self.chat_flow.timing_logs.append(
                    (
                        "LLM Processing Time",
                        round(0.0, 4),
                    )
                )
                self.chat_flow.timing_logs.append(
                    (
                        "Start of Stream",
                        elapsed_time,
                    )
                )
                start_of_stream_flag = False
            yield chunk

    def _get_content_generator(self):
        """
        Get the content generator based on whether an error occurred or not.
        Or if a cached response is provided.
        """
        # Log the start of response generation
        self.chat_flow.timing_logs.append(
            (
                "RAG Completion Time",
                round(time.time() - self.chat_flow.start_time, 4),
            )
        )

        # Check if the informative base prompt needs to be used
        use_informative_base = (
            self.chat_flow.log_data.response_path == response_types.INFORMATIVE_RESPONSE
            and any(
                utils.should_use_base(sub_intelligence)
                for sub_intelligence in self.chat_flow.intermediate.sub_intelligence_data.values()
            )
        )

        # Load the response base prompt
        prompt_loader = PromptLoader(
            self.chat_flow.log_data.response_path,
            self.chat_flow.input.channel,
            "KR" if self.chat_flow.input.country_code == "KR" else "GB",
            self.chat_flow.simple,  # False for informative, True for simple
            use_informative_base=use_informative_base,
            intelligence_info=[self.chat_flow.log_data.intelligence],
            sub_intelligence_info=[self.chat_flow.log_data.sub_intelligence],
        )
        response_base_prompt, self.prompt_name_list = prompt_loader.get_prompts()

        # If an error occurred, log the start of error response generation
        # And return the error response generator
        if self.error:
            self.chat_flow.timing_logs.append(
                (
                    "Exception Response Call Time Stamp",
                    datetime.now().strftime("%H:%M:%S.%f")[:-3],
                )
            )

            # Set the input data for the error response
            self.input_data.update(
                {
                    "guardrail_response_instructions": get_guardrail_response_instructions(
                        self.chat_flow.log_data.guardrail_type,
                        self.chat_flow.log_data.country_code,
                        self.chat_flow.input.channel,
                    ),
                    "complement_code_mapping_error": (
                        self.chat_flow.log_data.exception_message
                        if self.chat_flow.log_data.exception_type
                        == InvalidCodeMapping.__name__
                        else ""
                    ),
                    "store_mapping_error_data": (
                        self.chat_flow.log_data.exception_message
                        if self.chat_flow.log_data.exception_type
                        == InvalidStore.__name__
                        else ""
                    ),
                }
            )

            return self._call_response(response_base_prompt)

        # Otherwise, log the start of normal response generation
        self.chat_flow.timing_logs.append(
            (
                "Final Response Call Time Stamp",
                datetime.now().strftime("%H:%M:%S.%f")[:-3],
            )
        )

        # If a cached response is provided, process it
        # And return the stream simulator
        if self.cached_response:
            return self._stream_simulator()

        # Get the web links
        web_links = utils.get_web_link(
            self.chat_flow.orchestrator.rewritten_queries,
            self.chat_flow.log_data.product,
            self.chat_flow.input.channel,
            self.chat_flow.input.country_code,
            self.chat_flow.log_data.intelligence,
            self.chat_flow.log_data.sub_intelligence,
            self.chat_flow.log_data.ner,
        )

        # Prepare the input data for the response
        self.input_data.update(self.chat_flow.log_data.merged_data)
        self.input_data.update(
            {
                "channel": self.chat_flow.input.channel,
                "country_code": self.chat_flow.input.country_code,
                "message_history": copy.deepcopy(
                    self.chat_flow.message_history_data.messages
                ),
                "image_files": self.chat_flow.input_files.image_files,
                "original_query": self.chat_flow.message_history_data.combined_query,
                "user_query": self.chat_flow.log_data.user_query,
            }
        )

        # Otherwise, call the response method
        return self._call_response(response_base_prompt, web_links=web_links)

    def get_error_response(self, error_e):
        # Determine the type of error and set the full response accordingly
        self.chat_flow.log_data.response_path = {
            EmptyStreamData: response_types.EMPTY_STREAM_DATA_RESPONSE,
            ResponseGenerationFailureException: response_types.PROCESS_ERROR_RESPONSE,
        }.get(type(error_e), response_types.PROCESS_ERROR_RESPONSE)

        prompt_loader = PromptLoader(
            self.chat_flow.log_data.response_path,
            self.chat_flow.input.channel,
            "KR" if self.chat_flow.input.country_code == "KR" else "GB",
            self.chat_flow.simple,  # False for informative, True for simple
        )
        response_base_prompt, self.prompt_name_list = prompt_loader.get_prompts()

        # Get the stream iterator
        stream_iterator = response(
            self.input_data,
            response_base_prompt,
            self.chat_flow.log_data.response_path,
            self.chat_flow.gpt_model_name,
            0.01,
            42,
        )

        # Generate the response
        for chunk in stream_iterator:
            if not chunk.startswith("### LLM CALL META"):
                yield chunk

    def stream_response(self):
        """
        Stream the response based on the input data and response base prompt.
        Return a generator that yields the response content.
        """
        # Ensure the markdown tag is opened
        yield "data: ```markdown<br>\n\n"
        try:
            # Get the content generator
            for chunk in self._get_content_generator():
                self.full_response += chunk
                yield f"data: {utils.format_response_content(chunk)}\n\n"

            # If the full response is empty, raise an EmptyStreamData exception
            if not self.full_response.strip():
                raise EmptyStreamData("The response is empty.")

        except (ResponseGenerationFailureException, EmptyStreamData, Exception) as e:
            # Yield an error message if an exception occurs
            yield f"data: [STREAM ERROR: {str(e)}]\n\n"

            # If there is an error, send an alert
            print(f"Error in response handler (chat) stream response: {e}")
            traceback_message = traceback.format_exc()
            print(traceback_message)

            # Update the chat flow log data with the exception details
            self.chat_flow.log_data.exception_type = type(e).__name__
            self.chat_flow.log_data.exception_message = str(e)
            self.chat_flow.log_data.traceback_message = (
                traceback_message.split("\n") if traceback_message else ""
            )

            # Alert Email
            if VITE_OP_TYPE in ["STG", "PRD"]:
                context_data = {
                    "Module": "Rubicon Chat Completion Response Handler",
                    "Channel": self.chat_flow.input.channel,
                    "Country Code": self.chat_flow.input.country_code,
                    "Object ID": str(self.chat_flow.object_id),
                    "User ID": self.chat_flow.input.user_id,
                    "Message ID": self.chat_flow.input.message_id,
                    "Original Query": self.chat_flow.message_history_data.combined_query,
                }

                django_rq.run_job_high(
                    send_process_error_alert,
                    (str(e), "pipeline_error"),
                    {
                        "error_traceback": traceback_message,
                        "context_data": context_data,
                    },
                )

            # Get the error response
            for chunk in self.get_error_response(e):
                self.full_response += chunk
                yield f"data: {utils.format_response_content(chunk)}\n\n"

        finally:
            # Ensure to send the end of stream tag
            yield "data: ```<EOS>\n\n"

            # Ensure all the logging is done
            self._log_response()

    def build_response(self):
        """
        Build the response based on the input data and response base prompt.
        This method is used when streaming is not required.
        """
        try:
            # First check if the response is cached
            if self.cached_response and not self.error:
                # Set the full response to the cached response
                self.full_response = self.cached_response
                # Update the elapsed time
                elapsed_time = round(time.time() - self.chat_flow.start_time, 4)
                self.chat_flow.pipeline_elapsed_time = elapsed_time
                # Log the response details
                self._log_response()
                # Return the cached response (after cleaning)
                return {
                    "success": True,
                    "data": self.chat_flow.log_data.full_response,
                    "message": "Cached response",
                }

            # If no cached response, call the response method
            for chunk in self._get_content_generator():
                self.full_response += chunk

            # If the full response is empty, raise an EmptyStreamData exception
            if not self.full_response.strip():
                raise EmptyStreamData("The response is empty.")

            # Log the response details
            self._log_response()

            # Return the final response
            return {
                "success": True,
                "data": self.chat_flow.log_data.full_response,
                "message": "Response generated successfully",
            }

        except (ResponseGenerationFailureException, EmptyStreamData, Exception) as e:
            # If an error occurs, return an error response
            traceback_message = traceback.format_exc()
            print(f"Error in build_response: {e}")
            print(traceback_message)

            # Update the chat flow log data with the exception details
            self.chat_flow.log_data.exception_type = type(e).__name__
            self.chat_flow.log_data.exception_message = str(e)
            self.chat_flow.log_data.traceback_message = (
                traceback_message.split("\n") if traceback_message else ""
            )

            # Alert Email
            if VITE_OP_TYPE in ["STG", "PRD"]:
                context_data = {
                    "Module": "Rubicon Chat Completion Response Handler",
                    "Channel": self.chat_flow.input.channel,
                    "Country Code": self.chat_flow.input.country_code,
                    "Object ID": str(self.chat_flow.object_id),
                    "User ID": self.chat_flow.input.user_id,
                    "Message ID": self.chat_flow.input.message_id,
                    "Original Query": self.chat_flow.message_history_data.combined_query,
                }

                django_rq.run_job_high(
                    send_process_error_alert,
                    (str(e), "pipeline_error"),
                    {
                        "error_traceback": traceback_message,
                        "context_data": context_data,
                    },
                )

            # Get the error response
            for chunk in self.get_error_response(e):
                self.full_response += chunk

            # Log the response details
            self._log_response()

            # Return the error response
            return {
                "success": False,
                "data": self.chat_flow.log_data.full_response,
                "message": str(e),
            }

    def _log_response(self):
        """
        Log the response details.
        This method is used to log the response details after the response is built.
        """
        # Log the end of stream and timestamp
        self.chat_flow.timing_logs.append(
            (
                "End of Stream",
                round(time.time() - self.chat_flow.start_time, 4),
            )
        )
        self.chat_flow.timing_logs.append(
            (
                "End of Stream Time Stamp",
                datetime.now().strftime("%H:%M:%S.%f")[:-3],
            )
        )

        self.chat_flow.debug(
            gpt_model_name=self.chat_flow.gpt_model_name,
            full_response=self.full_response,
            prompt_name_list=self.prompt_name_list,
            response_path=self.chat_flow.log_data.response_path,
            original_query=self.chat_flow.message_history_data.combined_query,
            user_content=utils.get_user_content(
                self.chat_flow.log_data.response_path,
                self.chat_flow.log_data.user_query,
                self.chat_flow.message_history_data.combined_query,
            ),
            output_language=self.chat_flow.orchestrator.language,
            all_cache_hit=self.chat_flow.orchestrator.all_cache_hit,
            all_predefined_hit=self.chat_flow.orchestrator.all_predefined_hit,
            all_cs_hit=self.chat_flow.orchestrator.all_cs_hit,
            response_cache_hit=bool(self.cached_response),
            exception_type=self.chat_flow.log_data.exception_type,
            exception_message=self.chat_flow.log_data.exception_message,
            traceback_message=self.chat_flow.log_data.traceback_message,
            **{
                "section_name": (
                    "Exception Handling" if self.error else "Response Generation"
                )
            },
        )

        # Update the log data with the full response
        stream_termination_flag, self.chat_flow.log_data.full_response = (
            utils.clean_final_response(self.full_response)
        )
        if stream_termination_flag:
            self.chat_flow.log_data.guardrail_detected = True
