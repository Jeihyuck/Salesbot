import sys

sys.path.append("/www/alpha/")

import time
import traceback

from datetime import datetime
from typing import TYPE_CHECKING

from apps.rubicon_v3.__function import __utils as utils, __django_rq as django_rq
from apps.rubicon_v3.__function.__simulate_stream import stream_markdown
from apps.rubicon_v3.__function._80_response import response
from apps.rubicon_v3.__function._82_response_prompts import PromptLoader
from apps.rubicon_v3.__function.__exceptions import (
    EmptyStreamData,
    ResponseGenerationFailureException,
)
from apps.rubicon_v3.__function.__prompts.guardrails.malicious_answer_prompt_by_type_dict import (
    get_guardrail_response_instructions,
)
from apps.rubicon_v3.__function.definitions import response_types
from apps.rubicon_v3.__external_api._14_azure_email_alert import (
    send_process_error_alert,
)
from alpha.settings import VITE_OP_TYPE

if TYPE_CHECKING:
    from apps.rubicon_v3.__api.search_summary._00_search_summary import (
        RubiconSearchFlow,
    )


class ResponseHandler:
    def __init__(
        self,
        search_flow: "RubiconSearchFlow",
        stream: bool,
        error: bool,
        cached_response: str = None,
    ):
        self.search_flow = search_flow
        self.stream = stream
        self.error = error
        self.full_response = ""
        self.cached_response = cached_response
        self.input_data = {}
        self.prompt_name_list = []

    def _call_response(self, response_base_prompt: str):
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
            self.search_flow.log_data.response_path,
            self.search_flow.gpt_model_name,
            0.01,
            42,
        )

        # Generate the response
        for chunk in stream_iterator:
            if chunk.startswith("### LLM CALL META"):
                # Logging the LLM call metadata
                if first_response:
                    elapsed_time = round(time.time() - self.search_flow.start_time, 4)
                    self.search_flow.timing_logs.append(
                        (
                            f"200 Response {chunk.replace('### LLM CALL META : ', '')}",
                            elapsed_time,
                        )
                    )
                    self.search_flow.timing_logs.append(
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
                        elapsed_time = round(
                            time.time() - self.search_flow.start_time, 4
                        )
                        self.search_flow.pipeline_elapsed_time = elapsed_time
                        self.search_flow.timing_logs.append(
                            (
                                "LLM Processing Time",
                                round(time.time() - processing_time_start, 4),
                            )
                        )
                        self.search_flow.timing_logs.append(
                            (
                                "Start of Stream",
                                elapsed_time,
                            )
                        )
                        self.search_flow.timing_logs.append(
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
                elapsed_time = round(time.time() - self.search_flow.start_time, 4)
                self.search_flow.pipeline_elapsed_time = elapsed_time
                self.search_flow.timing_logs.append(
                    (
                        "LLM Processing Time",
                        round(0.0, 4),
                    )
                )
                self.search_flow.timing_logs.append(
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
        self.search_flow.timing_logs.append(
            (
                "RAG Completion Time",
                round(time.time() - self.search_flow.start_time, 4),
            )
        )

        # Load the response base prompt
        prompt_loader = PromptLoader(
            self.search_flow.log_data.response_path,
            self.search_flow.params.channel,
            "KR" if self.search_flow.params.country_code == "KR" else "GB",
            self.search_flow.simple,  # False for informative, True for simple
            intelligence_info=[self.search_flow.rag_data.intelligence_data],
        )
        response_base_prompt, self.prompt_name_list = prompt_loader.get_prompts()

        # If an error occurred, log the start of error response generation
        # And return the error response generator
        if self.error:
            self.search_flow.timing_logs.append(
                (
                    "Exception Response Call Time Stamp",
                    datetime.now().strftime("%H:%M:%S.%f")[:-3],
                )
            )

            # Set the input data for the error response
            self.input_data.update(
                {
                    "output_language": (
                        self.search_flow.rag_data.identified_language
                        if self.search_flow.rag_data.identified_language
                        else self.search_flow.user_content.default_language
                    ),
                    "guardrail_response_instructions": get_guardrail_response_instructions(
                        self.search_flow.log_data.guardrail_type,
                        self.search_flow.log_data.country_code,
                        self.search_flow.params.channel,
                    ),
                    "original_country_code": self.search_flow.log_data.country_code,
                }
            )

            return self._call_response(response_base_prompt)

        # Otherwise, log the start of normal response generation
        self.search_flow.timing_logs.append(
            (
                "Final Response Call Time Stamp",
                datetime.now().strftime("%H:%M:%S.%f")[:-3],
            )
        )

        # If a cached response is provided, process it
        # And return the stream simulator
        if self.cached_response:
            return self._stream_simulator()

        # Prepare the input data for the response
        self.input_data.update(self.search_flow.rag_data.merged_data)
        self.input_data.update(
            {
                "original_country_code": self.search_flow.log_data.country_code,
                "guardrail_response_instructions": get_guardrail_response_instructions(
                    self.search_flow.log_data.guardrail_type,
                    self.search_flow.log_data.country_code,
                    self.search_flow.params.channel,
                ),
            }
        )

        # Otherwise, call the response method
        return self._call_response(response_base_prompt)

    def get_error_response(self, error_e):
        # Determine the type of error and set the full response accordingly
        self.search_flow.log_data.response_path = {
            EmptyStreamData: response_types.EMPTY_STREAM_DATA_RESPONSE,
            ResponseGenerationFailureException: response_types.PROCESS_ERROR_RESPONSE,
        }.get(type(error_e), response_types.PROCESS_ERROR_RESPONSE)

        prompt_loader = PromptLoader(
            self.search_flow.log_data.response_path,
            self.search_flow.params.channel,
            "KR" if self.search_flow.params.country_code == "KR" else "GB",
            self.search_flow.simple,  # False for informative, True for simple
        )
        response_base_prompt, self.prompt_name_list = prompt_loader.get_prompts()

        # Get the stream iterator
        stream_iterator = response(
            self.input_data,
            response_base_prompt,
            self.search_flow.log_data.response_path,
            self.search_flow.gpt_model_name,
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
            print(f"Error in response handler (search) stream response: {e}")
            traceback_message = traceback.format_exc()
            print(traceback_message)

            # Update the search flow log data with the exception details
            self.search_flow.log_data.exception_type = type(e).__name__
            self.search_flow.log_data.exception_message = str(e)
            self.search_flow.log_data.traceback_message = (
                traceback_message.split("\n") if traceback_message else ""
            )

            # Alert Email
            if VITE_OP_TYPE in ["STG", "PRD"]:
                context_data = {
                    "Module": "Rubicon Search Summary Response Handler",
                    "Channel": self.search_flow.params.channel,
                    "Country Code": self.search_flow.params.country_code,
                    "Object ID": str(self.search_flow.object_id),
                    "User ID": self.search_flow.params.user_id,
                    "Message ID": self.search_flow.message_id,
                    "Original Query": self.search_flow.user_content.combined_query,
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
                elapsed_time = round(time.time() - self.search_flow.start_time, 4)
                self.search_flow.pipeline_elapsed_time = elapsed_time
                # Log the response details
                self._log_response()
                # Return the cached response (after cleaning)
                return {
                    "success": True,
                    "data": self.search_flow.log_data.full_response,
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
                "data": self.search_flow.log_data.full_response,
                "message": "Response generated successfully",
            }

        except (ResponseGenerationFailureException, EmptyStreamData, Exception) as e:
            # If an error occurs, return an error response
            traceback_message = traceback.format_exc()
            print(f"Error in build_response: {e}")
            print(traceback_message)

            # Update the search flow log data with the exception details
            self.search_flow.log_data.exception_type = type(e).__name__
            self.search_flow.log_data.exception_message = str(e)
            self.search_flow.log_data.traceback_message = (
                traceback_message.split("\n") if traceback_message else ""
            )

            # Alert Email
            if VITE_OP_TYPE in ["STG", "PRD"]:
                context_data = {
                    "Module": "Rubicon Search Summary Response Handler",
                    "Channel": self.search_flow.params.channel,
                    "Country Code": self.search_flow.params.country_code,
                    "Object ID": str(self.search_flow.object_id),
                    "User ID": self.search_flow.params.user_id,
                    "Message ID": self.search_flow.message_id,
                    "Original Query": self.search_flow.user_content.combined_query,
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
                "data": self.search_flow.log_data.full_response,
                "message": str(e),
            }

    def _log_response(self):
        """
        Log the response details.
        This method is used to log the response details after the response is built.
        """
        # Log the end of stream and timestamp
        self.search_flow.timing_logs.append(
            (
                "End of Stream",
                round(time.time() - self.search_flow.start_time, 4),
            )
        )
        self.search_flow.timing_logs.append(
            (
                "End of Stream Time Stamp",
                datetime.now().strftime("%H:%M:%S.%f")[:-3],
            )
        )

        self.search_flow.debug(
            gpt_model_name=self.search_flow.gpt_model_name,
            full_response=self.full_response,
            prompt_name_list=self.prompt_name_list,
            response_path=self.search_flow.log_data.response_path,
            original_query=self.search_flow.user_content.combined_query,
            expanded_query=self.search_flow.rag_data.expanded_query,
            output_language=self.search_flow.rag_data.identified_language,
            cache_hit=self.search_flow.log_data.cache_hit,
            response_cache_hit=bool(self.cached_response),
            exception_type=self.search_flow.log_data.exception_type,
            exception_message=self.search_flow.log_data.exception_message,
            traceback_message=self.search_flow.log_data.traceback_message,
            **{
                "section_name": (
                    "Exception Handling" if self.error else "Response Generation"
                )
            },
        )

        # Update the log data with the full response
        stream_termination_flag, self.search_flow.log_data.full_response = (
            utils.clean_final_response(self.full_response)
        )
        if stream_termination_flag:
            self.search_flow.log_data.guardrail_detected = True
