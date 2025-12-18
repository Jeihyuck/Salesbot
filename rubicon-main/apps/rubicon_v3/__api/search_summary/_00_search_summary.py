import sys

sys.path.append("/www/alpha/")

import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "alpha.settings")
django.setup()

import copy
import inspect
import functools
import time
import traceback
import re
import asyncio

from dataclasses import dataclass, field
from typing import Optional
from bson.objectid import ObjectId

from apps.rubicon_v3.__function.__django_cache import (
    DjangoCacheClient,
    CacheKey,
    MessageFlags,
)
from apps.rubicon_v3.__function import (
    __utils as utils,
    __django_rq as django_rq,
    __rubicon_log as rubicon_log,
    _02_language_identification,
    _12_text_guard_rail,
    _20_orchestrator_predefined,
    _22_orchestrator_intelligence,
    # _73_product_rag_specification_check,
)
from apps.rubicon_v3.__api.search_summary import (
    __response_handler as response_handler,
    __utils as search_utils,
    __search_log as search_log,
    _05_query_expansion,
    _10_simple_ai_search,
    _15_specification_check,
    _20_response_layout,
)
from apps.rubicon_v3.__api import _07_supplementary_info
from apps.rubicon_v3.__external_api import _11_user_info, _14_azure_email_alert
from apps.rubicon_v3.__function.definitions import channels, response_types
from apps.rubicon_v3.__function.__exceptions import (
    HttpStatus,
    InvalidOriginalQuery,
    EmptyStreamData,
    EmptyOriginalQuery,
    ProcessTimeout,
    ProcessError,
    PreEmbargoQueryException,
    RedirectRequestException,
    InformationRestrictedException,
    NoDataFoundException,
)
from alpha.settings import VITE_OP_TYPE


cache = DjangoCacheClient()


SECTION_NAME = "section_name"


def camel_to_snake(name):
    """Convert camelCase to snake_case."""
    return re.sub(r"(?<!^)(?=[A-Z])", "_", name).lower()


def create_dataclass_from_dict(data_dict, dataclass_type):
    """
    Create a dataclass instance from a dictionary with camelCase to snake_case conversion.

    Args:
        data_dict (dict): Dictionary with camelCase keys
        dataclass_type (type): The dataclass type to create

    Returns:
        An instance of the specified dataclass
    """
    # Get valid field names from the dataclass
    valid_fields = {
        field.name for field in dataclass_type.__dataclass_fields__.values()
    }

    # Create kwargs with converted field names, filtering to valid fields only
    kwargs = {}
    for key, value in data_dict.items():
        field_name = camel_to_snake(key)
        if field_name in valid_fields:
            kwargs[field_name] = value

    return dataclass_type(**kwargs)


class SearchFlowSectionNames:

    DEBUG_PARAMS_ARGUMENTS = "debug_input_arguments"
    DEBUG_SEARCH_DATA_ARGUMENTS = "debug_search_data_arguments"
    VARIABLE_SETUP = "variable_setup"
    CHECK_ORIGINAL_QUERY = "check_original_query"
    ENQUEUE_LANGUAGE_IDENTIFICATION = "enqueue_language_identification"
    LOAD_QUERY_CACHE = "load_query_cache"
    PARALLEL_QUERY_EXPANSION_AI_SEARCH_SPEC_CHECK = (
        "parallel_query_expansion_ai_search_spec_check"
    )
    PARALLEL_PREDEFINED_INTELLIGENCE_GUARDRAILS = "parallel_intelligence_guardrails"
    RESPONSE_LAYOUT = "response_layout"
    BACKGROUND_JOBS = "background_jobs"
    MERGE_RAG_DATA = "merge_rag_data"
    SEARCH_SUMMARY_RESPONSE_HANDLER = "search_summary"
    RESPONSE_GENERATION = "response_generation"
    EXCEPTION_HANDLING = "exception_handling"


class RubiconSearchFlow:
    # Background Functions
    LANG_IDENT_FUNC = _02_language_identification.lang_detect_with_gpt

    @dataclass
    class Params:
        channel: str = ""
        country_code: str = ""
        department: str = ""
        user_id: str = ""
        message: str = ""
        lng: str = ""
        gu_id: str = ""
        sa_id: str = ""
        jwt_token: str = ""
        estore_sitecode: str = ""

    @dataclass
    class LogData:
        timeout: list = field(default_factory=list)
        error: list = field(default_factory=list)
        subsidiary: str = ""
        country_code: str = ""
        site_cd: str = ""
        guardrail_detected: bool = False
        exception_detected: bool = False
        invalid_original_query_reason: Optional[str] = None
        invalid_original_query_type: Optional[str] = None
        product: list = field(default_factory=list)
        show_supplement: bool = True
        show_media: bool = False
        show_product_card: bool = False
        show_related_query: bool = False
        show_hyperlink: bool = False
        cache_hit: bool = False
        response_cache_hit: bool = False
        guardrail_type: str = "S1"
        exception_type: str = ""
        exception_message: str = ""
        traceback_message: str = ""
        restricted: bool = False
        exception_detected: bool = False
        full_response: str = ""
        response_path: str = ""
        status_code: int = 200

    @dataclass
    class SearchData:
        search_results: list = field(default_factory=list)
        search_keywords: list = field(default_factory=list)
        search_type: list = field(default_factory=list)
        sku_codes: list = field(default_factory=list)
        product_list: list = field(default_factory=list)

    @dataclass
    class RagData:
        cache_key: str = ""
        cached_data: dict = field(default_factory=dict)
        identified_language: str = ""
        expanded_query: str = ""
        unstructured_data: list = field(default_factory=list)
        other_company_expression: list = field(default_factory=list)
        set_product_model_info: list = field(default_factory=list)
        product_model_info: list = field(default_factory=list)
        product_common_spec_info: list = field(default_factory=list)
        product_spec_info: list = field(default_factory=list)
        set_product_spec_info: list = field(default_factory=list)
        reference_data: list = field(default_factory=list)
        intelligence_data: str = ""
        rubicon_text_guardrail_data: dict = field(default_factory=dict)
        moderation_text_guardrail_data: dict = field(default_factory=dict)
        injection_text_guardrail_data: dict = field(default_factory=dict)
        response_layout_data: str = ""
        merged_data: dict = field(default_factory=dict)

    @dataclass
    class UserContent:
        user_info: dict = field(default_factory=dict)
        image_files: list = field(default_factory=list)
        audio_files: list = field(default_factory=list)
        combined_query: str = ""
        default_language: str = ""

    def __init__(
        self,
        message_id: str,
        object_id: ObjectId,
        params: Params,
        search_data: SearchData,
        use_cache: bool,
        stream: bool,
        status: HttpStatus,
    ):
        self.message_id = message_id
        self.object_id = object_id
        self.params = params
        self.search_data = search_data
        self.use_cache = use_cache
        self.stream = stream
        self.status = status
        self.log_data = RubiconSearchFlow.LogData()
        self.rag_data = RubiconSearchFlow.RagData()
        self.user_content = RubiconSearchFlow.UserContent()
        self.response_handler = None
        self.start_time = time.time()
        self.pipeline_elapsed_time = 0
        self.master_debug_messages = []
        self.timing_logs = []
        self.gpt_model_name = "gpt-4.1-mini"  # Default GPT model name
        self.cache_expiry = 60 * 60 * 24 * 14  # Default cache expiry time (2 weeks)
        self.session_expiry = 60 * 60 * 1  # Default session expiry time (1 hour)
        self.simple = True  # Default to simple mode

    def debug(self, *args, **kwargs):
        """
        Create a debug dictionary with variable names (in title form) as keys and
        their corresponding values. For positional arguments (`args`), variable
        names are inferred from the caller's local variables. For expressions or
        attribute chains, use `kwargs` to explicitly set the key-value pairs.

        RubiconChatFlow.debug_sync_timer()
        """
        # Initialize a new debug dictionary
        debug_dict = {}

        # Get the caller's frame and local variables
        caller_frame = inspect.currentframe().f_back
        if caller_frame is None:
            raise RuntimeError("Caller frame is not available.")
        caller_locals = caller_frame.f_locals

        wrapper_frame = caller_frame.f_back
        if wrapper_frame is None:
            raise RuntimeError("Wrapper frame is not available.")
        wrapper_locals = wrapper_frame.f_locals

        debug_dict[SECTION_NAME] = wrapper_locals.get("section_name")
        # Process positional arguments (`args`)
        for var in args:
            matched = False
            for name, value in caller_locals.items():
                if value is var:
                    # Use the variable name in title case as the key
                    formatted_name = name  # .replace("_", " ").title()
                    debug_dict[formatted_name] = copy.deepcopy(value)
                    matched = True
                    break

            # If no match is found (e.g., for expressions), raise an error
            if not matched:
                raise ValueError(
                    "Positional argument '{}' could not be resolved to a variable name. "
                    "Consider using a keyword argument.".format(var)
                )

        # Process keyword arguments (`kwargs`) and add them to the debug dictionary
        for key, value in kwargs.items():
            formatted_key = key  # .replace("_", " ").title()
            debug_dict[formatted_key] = copy.deepcopy(value)

        # Append to the master debug messages list
        self.master_debug_messages.append(debug_dict)

    @staticmethod
    def debug_sync_timer(section_name: Optional[str] = None):
        """A static method decorator for measuring execution time."""

        def decorator(func):
            @functools.wraps(func)
            def wrapper(self: "RubiconSearchFlow", *args, **kwargs):
                nonlocal section_name  # Ensure section_name is used from the outer scope

                start_time = time.time()  # Record start time
                try:
                    result = func(self, *args, **kwargs)  # Call the original function
                except Exception as e:
                    elapsed_time = time.time() - start_time  # Calculate elapsed time
                    if not section_name:
                        section_name = func.__name__
                    self.timing_logs.append((section_name, round(elapsed_time, 4)))
                    raise  # Re-raise the exception after logging
                else:
                    elapsed_time = time.time() - start_time  # Calculate elapsed time
                    if not section_name:
                        section_name = func.__name__
                    self.timing_logs.append((section_name, round(elapsed_time, 4)))
                    return result  # Return the result of the function

            return wrapper

        return decorator

    @debug_sync_timer(SearchFlowSectionNames.DEBUG_PARAMS_ARGUMENTS)
    def _debug_params_arguments(self):
        """
        Debug the params arguments of the Rubicon search flow.
        """
        # Define the keys to exclude
        disallowed_keys = {}

        # Include all keys except those in disallowed_keys
        d = {k: v for k, v in self.params.__dict__.items() if k not in disallowed_keys}

        # Pass the filtered dictionary to __debug
        self.debug(**d)

    @debug_sync_timer(SearchFlowSectionNames.DEBUG_SEARCH_DATA_ARGUMENTS)
    def _debug_search_data_arguments(self):
        """
        Debug the search data arguments of the Rubicon search flow.
        """
        # Define the keys to exclude
        disallowed_keys = {}

        # Include all keys except those in disallowed_keys
        d = {
            k: v
            for k, v in self.search_data.__dict__.items()
            if k not in disallowed_keys
        }

        # Pass the filtered dictionary to __debug
        self.debug(**d)

    @debug_sync_timer(SearchFlowSectionNames.VARIABLE_SETUP)
    def _variable_setup(self):
        """
        Set up variables for the Rubicon search flow.
        """
        # Get the subsidiary based on channel and country code
        self.log_data.subsidiary = utils.get_subsidiary(
            self.params.channel, self.params.country_code
        )

        # Get the site_cd based on channel and country code
        self.log_data.site_cd = utils.get_site_cd(
            self.params.channel, self.params.country_code
        )

        # Save the original country code to log and update it
        self.log_data.country_code = self.params.country_code
        if self.params.country_code != "KR":
            self.params.country_code = "GB"

        # Get the SKU codes from the search results
        self.search_data.sku_codes = [
            result.get("id")
            for result in self.search_data.search_results
            if result.get("id")
        ][:3]

        # Set the user content combined query
        self.user_content.combined_query = self.params.message

        # Get the language name from the language code and country code
        self.user_content.default_language = utils.get_language_name(
            self.params.lng, self.params.country_code, self.params.channel
        )

        # Get the product dict list from the SKU codes
        self.search_data.product_list = search_utils.codes_to_product_dict_list(
            self.search_data.sku_codes,
            self.params.country_code,
            self.log_data.site_cd,
        )

        # Get the user info
        # Check if user info is in cache
        user_info_cache_key = CacheKey.user_info(
            self.params.sa_id, self.params.country_code
        )
        user_info_data = cache.get(user_info_cache_key, {})
        # If user info is not in cache, fetch it
        if (
            not user_info_data
            and self.params.sa_id
            and self.params.sa_id != "default_sa_id"
        ):
            # Grab user info data
            user_info_class = _11_user_info.IndivInfo(
                self.params.country_code,
                self.params.sa_id,
                self.params.gu_id,
                self.params.channel,
            )
            user_info_data = asyncio.run(user_info_class.getUserInfo())
            # Store the user info in cache
            if user_info_data:
                cache.store(user_info_cache_key, user_info_data, 60 * 30)  # 30 minutes
        self.user_content.user_info = user_info_data

        self.debug(
            country_code=self.params.country_code,
            subsidiary=self.log_data.subsidiary,
            site_cd=self.log_data.site_cd,
            sku_codes=self.search_data.sku_codes,
            product_list=self.search_data.product_list,
        )

    @debug_sync_timer(SearchFlowSectionNames.CHECK_ORIGINAL_QUERY)
    def _check_original_query(self):
        """
        원본 쿼리를
        """
        flag, invalid_type, message = utils.check_original_query(
            self.user_content.combined_query,
            self.params.channel,
            self.user_content.default_language,
        )
        if not flag:
            self.log_data.guardrail_detected = True
        self.log_data.invalid_original_query_reason = message
        self.log_data.invalid_original_query_type = invalid_type

        self.debug(flag, message, invalid_type)

        if (
            not flag
            and invalid_type
            in [
                utils.OriginalQueryInvalidTypes.HYPERLINK,
                utils.OriginalQueryInvalidTypes.WORD,
                utils.OriginalQueryInvalidTypes.PATTERN,
            ]
            and self.params.channel != channels.GUARDRAIL_BYPASS
        ):
            raise InvalidOriginalQuery(f"Original query is invalid. Reason: {message}")
        elif (
            not flag
            and invalid_type == utils.OriginalQueryInvalidTypes.PRE_EMBARGO
            and self.params.channel != channels.GUARDRAIL_BYPASS
        ):
            raise PreEmbargoQueryException(
                f"Original query is requesting for unreleased products. Message: {message}"
            )
        elif not flag and invalid_type == utils.OriginalQueryInvalidTypes.EMPTY:
            raise EmptyOriginalQuery(
                "Original query is empty. Please provide a valid query."
            )
        elif not flag and invalid_type == utils.OriginalQueryInvalidTypes.REDIRECT:
            raise RedirectRequestException(
                "Original query is a redirect request. Redirecting to the appropriate page."
            )

    @debug_sync_timer(SearchFlowSectionNames.ENQUEUE_LANGUAGE_IDENTIFICATION)
    def _enqueue_language_identification(self):
        """
        Enqueue the language identification job in the background.
        """
        # Prepare the function parameters
        lang_identification_params = [
            (
                self.LANG_IDENT_FUNC,
                (
                    self.user_content.combined_query,
                    [],
                    self.user_content.default_language,
                    self.gpt_model_name,
                ),
                {},
                None,
                None,
            )
        ]

        # Enqueue the language identification job
        side_job_mapping = django_rq.enqueue_dynamic_jobs(lang_identification_params)

        # Return the side job mapping
        return side_job_mapping

    @debug_sync_timer(SearchFlowSectionNames.LOAD_QUERY_CACHE)
    def _load_query_cache(self):
        """
        Load the query cache if available.
        """
        self.rag_data.cache_key = CacheKey.search_summary(
            self.user_content.combined_query,
            self.search_data.sku_codes,
            self.params.channel,
            self.params.country_code,
        )
        cached_result = cache.get(self.rag_data.cache_key)
        # If cached result is found and use_cache is True, set the cached data
        if cached_result and self.use_cache:
            self.rag_data.cached_data = cached_result
            self.log_data.cache_hit = True

            # Process the cached data
            self.rag_data.expanded_query = self.rag_data.cached_data.get(
                "expanded_query", self.user_content.combined_query
            )
            self.rag_data.unstructured_data = self.rag_data.cached_data.get(
                "unstructured_data", {}
            )
            self.rag_data.other_company_expression = self.rag_data.cached_data.get(
                "other_company_expression", []
            )
            self.rag_data.product_model_info = self.rag_data.cached_data.get(
                "product_model_info", []
            )
            self.rag_data.product_common_spec_info = self.rag_data.cached_data.get(
                "product_common_spec_info", []
            )
            self.rag_data.product_spec_info = self.rag_data.cached_data.get(
                "product_spec_info", []
            )
            self.rag_data.set_product_spec_info = self.rag_data.cached_data.get(
                "set_product_spec_info", []
            )
            self.rag_data.reference_data = self.rag_data.cached_data.get(
                "reference_data", []
            )
            self.rag_data.intelligence_data = self.rag_data.cached_data.get(
                "intelligence_data", ""
            )
            self.rag_data.response_layout_data = self.rag_data.cached_data.get(
                "response_layout_data", ""
            )

        self.debug(
            cache_key=self.rag_data.cache_key,
            cached_result={
                k: (
                    utils.truncate_text_data_for_display(v)
                    if k == "unstructured_data"
                    else v
                )
                for k, v in self.rag_data.cached_data.items()
            },
            cache_hit=self.log_data.cache_hit,
        )

    @debug_sync_timer(
        SearchFlowSectionNames.PARALLEL_QUERY_EXPANSION_AI_SEARCH_SPEC_CHECK
    )
    def _parallel_query_expansion_ai_search_spec_check(self):
        """
        Run the query expansion, ai search, and specification check jobs in parallel.
        """
        QUERY_EXPANSION_FUNC = _05_query_expansion.query_expansion
        AI_CPT_SEARCH_FUNC = _10_simple_ai_search.execute_cpt_rag
        SPEC_CHECK_FUNC = _15_specification_check.specification_check

        # Prepare the function parameters
        query_expansion_params = [
            (
                QUERY_EXPANSION_FUNC,
                (
                    self.user_content.combined_query,
                    self.user_content.default_language,
                    self.params.country_code,
                    self.gpt_model_name,
                ),
                {},
                None,
                None,
            )
        ]
        ai_cpt_search_params = [
            (
                AI_CPT_SEARCH_FUNC,
                (
                    "*",
                    self.search_data.sku_codes,
                    self.params.country_code,
                ),
                {},
                None,
                None,
            )
        ]
        spec_check_params = [
            (
                SPEC_CHECK_FUNC,
                (
                    self.search_data.product_list,
                    self.params.country_code,
                    True,
                    self.log_data.site_cd,
                ),
                {},
                None,
                None,
            )
        ]

        # Enqueue jobs
        job_mapping = django_rq.enqueue_dynamic_jobs(
            query_expansion_params + ai_cpt_search_params + spec_check_params,
        )
        results = django_rq.get_all_results(job_mapping)

        # Process results
        timeout_message_data = {}
        error_message_data = {}
        debug_specification_check = []

        for job_name, result in results.items():

            self.timing_logs.append(
                (
                    f"{inspect.currentframe().f_back.f_locals.get("section_name")}<br> - {job_name}.{result.status}",
                    result.elapsed_time,
                )
            )

            parts = job_name.split("__")
            q, s = None, None  # Initialize q and s
            if len(parts) > 1:
                if len(parts) > 2:
                    q = parts[-2]
                    s = parts[-1]
                else:
                    q = parts[-1]
            else:
                q = parts[0]

            # Handle Job results according to their status
            if result.status == django_rq.Status.SUCCESS:
                if job_name.startswith(QUERY_EXPANSION_FUNC.__name__):
                    self.rag_data.expanded_query = result.result
                elif job_name.startswith(AI_CPT_SEARCH_FUNC.__name__):
                    cpt_data = result.result
                    self.rag_data.unstructured_data.extend(cpt_data)
                elif job_name.startswith(SPEC_CHECK_FUNC.__name__):
                    spec_data, debug_specification_check = result.result
                    # Make sure the spec_data is available
                    if not spec_data[2] or not all(
                        model_info for model_info in spec_data[2]
                    ):
                        raise NoDataFoundException(
                            "No product model information found for the given SKU codes."
                        )
                    self.rag_data.other_company_expression = spec_data[0]
                    self.rag_data.set_product_model_info = spec_data[1]
                    self.rag_data.product_model_info = spec_data[2]
                    self.rag_data.product_common_spec_info = spec_data[3]
                    self.rag_data.product_spec_info = spec_data[4]
                    self.rag_data.set_product_spec_info = spec_data[5]
                else:
                    raise ValueError(f"Job not found: {job_name}")

            elif result.status == django_rq.Status.TIMEOUT:
                # Handle timeout
                timeout_message_data[job_name] = f"Timeout in {job_name}"
                self.log_data.timeout.append(
                    {"name": parts[0], "message": f"Timeout in {job_name}"}
                )

            else:
                # Handle error
                error_message_data[job_name] = f"Error in {job_name}: {result.error}"
                self.log_data.error.append(
                    {
                        "name": parts[0],
                        "message": f"Error in {job_name}: {result.error}",
                    }
                )

        self.debug(
            timeout_message_data,
            error_message_data,
            expanded_query=self.rag_data.expanded_query,
            unstructured_data=utils.truncate_text_data_for_display(
                self.rag_data.unstructured_data
            ),
            other_company_expression=self.rag_data.other_company_expression,
            set_product_model_info=self.rag_data.set_product_model_info,
            product_model_info=self.rag_data.product_model_info,
            product_common_spec_info=self.rag_data.product_common_spec_info,
            product_spec_info=self.rag_data.product_spec_info,
            set_product_spec_info=self.rag_data.set_product_spec_info,
            debug_specification_check="\n".join(
                [
                    f"data: {item.get('data')}\n"
                    + f"sql_product: {item.get('sql_product')}\n"
                    + f"product_codes_result: {item.get('product_codes_result')}\n"
                    + f"sql: {item.get('sql')}\n"
                    for item in debug_specification_check
                ]
            ),
        )

        # Raise exceptions if there are any errors or timeouts
        if timeout_message_data:
            raise ProcessTimeout(
                f"Timeouts occurred during the parallel processing: {" | ".join(timeout_message_data.values())}"
            )
        if error_message_data:
            raise ProcessError(
                f"Errors occurred during the parallel processing: {" | ".join(error_message_data.values())}"
            )

    @debug_sync_timer(
        SearchFlowSectionNames.PARALLEL_PREDEFINED_INTELLIGENCE_GUARDRAILS
    )
    def _parallel_predefined_intelligence_guardrails(self):
        """
        Run the predefined check intelligence identification and guardrails jobs in parallel.
        """
        PREDEFINED_FUNC = _20_orchestrator_predefined.predefined_rag_retriever
        INTELLIGENCE_FUNC = _22_orchestrator_intelligence.intelligence
        RUBICON_TEXT_GUARDRAIL_FUNC = _12_text_guard_rail.rubicon_text_guardrail
        MODERATION_TEXT_GUARDRAIL_FUNC = _12_text_guard_rail.moderation_text_guardrail
        INJECTION_TEXT_GUARDRAIL_FUNC = _12_text_guard_rail.injection_text_guardrail

        # Prepare the function parameters
        predefined_params = [
            (
                PREDEFINED_FUNC,
                (
                    self.rag_data.expanded_query,
                    self.params.country_code,
                    self.params.channel,
                    self.log_data.site_cd,
                ),
                {},
                None,
                None,
            )
        ]
        intelligence_params = [
            (
                INTELLIGENCE_FUNC,
                (
                    self.rag_data.expanded_query,
                    self.gpt_model_name,
                    self.params.country_code,
                ),
                {},
                None,
                None,
            )
        ]
        rubicon_text_guardrail_params = [
            (
                RUBICON_TEXT_GUARDRAIL_FUNC,
                (query, []),
                {},
                query,
                None,
            )
            for query in [
                self.user_content.combined_query,
                self.rag_data.expanded_query,
            ]
        ]
        moderation_text_guardrail_params = [
            (
                MODERATION_TEXT_GUARDRAIL_FUNC,
                (self.user_content.combined_query, []),
                {},
                self.user_content.combined_query,
                None,
            )
        ]
        injection_text_guardrail_params = [
            (
                INJECTION_TEXT_GUARDRAIL_FUNC,
                (self.user_content.combined_query, []),
                {},
                self.user_content.combined_query,
                None,
            )
        ]

        # Enqueue jobs
        job_mapping = django_rq.enqueue_dynamic_jobs(
            predefined_params
            + intelligence_params
            + rubicon_text_guardrail_params
            + moderation_text_guardrail_params
            + injection_text_guardrail_params,
        )
        results = django_rq.get_all_results(job_mapping)

        # Process results
        timeout_message_data = {}
        error_message_data = {}
        predefined_rag_debug_data = []

        for job_name, result in results.items():

            self.timing_logs.append(
                (
                    f"{inspect.currentframe().f_back.f_locals.get('section_name')}<br> - {job_name}.{result.status}",
                    result.elapsed_time,
                )
            )

            parts = job_name.split("__")
            q, s = None, None  # Initialize q and s
            if len(parts) > 1:
                if len(parts) > 2:
                    q = parts[-2]
                    s = parts[-1]
                else:
                    q = parts[-1]
            else:
                q = parts[0]

            if result.status == django_rq.Status.SUCCESS:
                if job_name.startswith(PREDEFINED_FUNC.__name__):
                    self.rag_data.reference_data, predefined_rag_debug_data = (
                        result.result
                    )
                elif job_name.startswith(INTELLIGENCE_FUNC.__name__):
                    self.rag_data.intelligence_data = result.result
                elif job_name.startswith(RUBICON_TEXT_GUARDRAIL_FUNC.__name__):
                    self.rag_data.rubicon_text_guardrail_data[q] = result.result
                    if result.result.get("decision") == "ATTACK":
                        self.log_data.guardrail_detected = True
                elif job_name.startswith(MODERATION_TEXT_GUARDRAIL_FUNC.__name__):
                    self.rag_data.moderation_text_guardrail_data[q] = result.result
                    if result.result.get("flagged"):
                        self.log_data.guardrail_detected = True
                elif job_name.startswith(INJECTION_TEXT_GUARDRAIL_FUNC.__name__):
                    self.rag_data.injection_text_guardrail_data[q] = result.result
                    if result.result.get("flagged"):
                        self.log_data.guardrail_detected = True
                else:
                    raise ValueError(f"Job not found: {job_name}")

            elif result.status == django_rq.Status.TIMEOUT:
                # Handle timeout
                timeout_message_data[job_name] = f"Timeout in {job_name}"
                self.log_data.timeout.append(
                    {"name": parts[0], "message": f"Timeout in {job_name}"}
                )

            else:
                # Handle error
                error_message_data[job_name] = f"Error in {job_name}: {result.error}"
                self.log_data.error.append(
                    {
                        "name": parts[0],
                        "message": f"Error in {job_name}: {result.error}",
                    }
                )

        self.debug(
            timeout_message_data,
            error_message_data,
            predefined_rag_debug_data,
            reference_data=self.rag_data.reference_data,
            intelligence_data=self.rag_data.intelligence_data,
            rubicon_text_guardrail_data=self.rag_data.rubicon_text_guardrail_data,
            moderation_text_guardrail_data=self.rag_data.moderation_text_guardrail_data,
            injection_text_guardrail_data=self.rag_data.injection_text_guardrail_data,
            guardrail_detected=self.log_data.guardrail_detected,
        )

        # Raise exceptions if there are any errors or timeouts
        if timeout_message_data:
            raise ProcessTimeout(
                f"Timeouts occurred during the parallel processing: {" | ".join(timeout_message_data.values())}"
            )
        if error_message_data:
            raise ProcessError(
                f"Errors occurred during the parallel processing: {" | ".join(error_message_data.values())}"
            )

        # Check if the intelligence is restricted for the channel
        if not utils.channel_intelligence_check(
            self.params.channel, self.rag_data.intelligence_data
        ):
            self.log_data.restricted = True
            raise InformationRestrictedException(
                f"Information restricted for channel: {self.params.channel}. Intelligence: {self.rag_data.intelligence_data}"
            )

    @debug_sync_timer(SearchFlowSectionNames.RESPONSE_LAYOUT)
    def _response_layout(self):
        """
        Get the response layout based on the intelligence data, channel, country code, and simple flag."
        """
        # Organize the data presence dict
        data_presence = {
            "has_single_product": len(self.search_data.sku_codes) == 1,
            "has_multiple_products": len(self.search_data.sku_codes) > 1,
        }

        # Determine the response layout based on the intelligence data
        response_layout_data = _20_response_layout.get_response_layout(
            self.rag_data.intelligence_data,
            self.params.channel,
            self.params.country_code,
            data_presence,
            self.simple,  # True for simple mode, False for informative mode
        )

        # If the response layout data is present, set it in the rag_data
        if response_layout_data:
            self.rag_data.response_layout_data = response_layout_data

        self.debug(
            data_presence,
            response_layout_data=self.rag_data.response_layout_data,
        )

    @debug_sync_timer(SearchFlowSectionNames.BACKGROUND_JOBS)
    def _background_jobs(self, side_job_mapping):
        """
        Process the background jobs that were enqueued earlier.
        """
        # Get the results of the background jobs
        results = django_rq.get_all_results(side_job_mapping)

        # Process the results
        timeout_message_data = {}
        error_message_data = {}
        language_debug_data = None

        for job_name, result in results.items():
            self.timing_logs.append(
                (
                    f"{inspect.currentframe().f_back.f_locals.get("section_name")}<br> - {job_name}.{result.status}",
                    result.elapsed_time,
                )
            )

            parts = job_name.split("__")
            q, s = None, None  # Initialize q and s
            if len(parts) > 1:
                if len(parts) > 2:
                    q = parts[-2]
                    s = parts[-1]
                else:
                    q = parts[-1]
            else:
                q = parts[0]

            # Handle Job results according to their status
            if result.status == django_rq.Status.SUCCESS:
                if job_name.startswith(self.LANG_IDENT_FUNC.__name__):
                    self.rag_data.identified_language, language_debug_data = (
                        result.result
                    )
                else:
                    raise ValueError(f"Job not found: {job_name}")

            elif result.status == django_rq.Status.TIMEOUT:
                # Handle timeout
                timeout_message_data[job_name] = f"Timeout in {job_name}"
                self.log_data.timeout.append(
                    {"name": parts[0], "message": f"Timeout in {job_name}"}
                )

            else:
                # Handle error
                error_message_data[job_name] = f"Error in {job_name}: {result.error}"
                self.log_data.error.append(
                    {
                        "name": parts[0],
                        "message": f"Error in {job_name}: {result.error}",
                    }
                )

        self.debug(
            timeout_message_data,
            error_message_data,
            language_debug_data=language_debug_data,
            identified_language=self.rag_data.identified_language,
        )

        # Raise exceptions if there are any errors or timeouts
        if timeout_message_data:
            raise ProcessTimeout(
                f"Timeouts occurred during the parallel processing: {" | ".join(timeout_message_data.values())}"
            )
        if error_message_data:
            raise ProcessError(
                f"Errors occurred during the parallel processing: {" | ".join(error_message_data.values())}"
            )

    @debug_sync_timer(SearchFlowSectionNames.MERGE_RAG_DATA)
    def _04_merge_rag_data(self):
        """
        Merge the RAG data into an organized structure.
        """
        # Determine the response path
        # If guardrail is detected, set the response path to TEXT_GUARDRAIL_RESPONSE
        if self.log_data.guardrail_detected:
            # Update status
            self.status.status = 451

            self.log_data.response_path = response_types.TEXT_GUARDRAIL_RESPONSE

            # Get the guardrail type depending on the guardrail category
            for value in self.rag_data.rubicon_text_guardrail_data.values():
                if value.get("decision") == "ATTACK":
                    self.log_data.guardrail_type = value.get("category")
            if self.rag_data.moderation_text_guardrail_data.get("flagged"):
                self.log_data.guardrail_type = "S6"
            if self.rag_data.injection_text_guardrail_data.get("flagged"):
                self.log_data.guardrail_type = "S2"

        # If predefined rag is retrieved, set the response path to PREDEFINED_RESPONSE
        elif self.rag_data.reference_data:
            self.log_data.response_path = response_types.PREDEFINED_RESPONSE

        # If no guardrail is detected, set the response path to SEARCH_SUMMARY_RESPONSE
        else:
            self.log_data.response_path = response_types.SEARCH_SUMMARY_RESPONSE

        # Organize the RAG data into a merged structure
        unstructured_text_data = [
            result["chunk"]
            for result in self.rag_data.unstructured_data
            if "chunk" in result
        ]

        self.rag_data.merged_data = {
            "output_language": self.rag_data.identified_language,
            "system_suggestion": "The following products are the most relevant products determined by their relevancy to the query, launch date, stock status, and etc. Follow this order when generating the response: "
            + " | ".join(
                [f"{i+1}. {code}" for i, code in enumerate(self.search_data.sku_codes)]
            ),
            "unstructured_relevant_data": unstructured_text_data,
            "other_company_expression": self.rag_data.other_company_expression,
            "set_product_model_info": self.rag_data.set_product_model_info,
            "product_model_info": self.rag_data.product_model_info,
            "product_common_spec_info": self.rag_data.product_common_spec_info,
            "product_spec_info": self.rag_data.product_spec_info,
            "set_product_spec_info": self.rag_data.set_product_spec_info,
            "reference_data": self.rag_data.reference_data,
            "user_query": self.rag_data.expanded_query
            or self.user_content.combined_query,
            "response_format": self.rag_data.response_layout_data,
            "sample_response_data": "",  # Placeholder for sample response data
        }

        self.debug(merged_data=self.rag_data.merged_data)

    @debug_sync_timer(SearchFlowSectionNames.SEARCH_SUMMARY_RESPONSE_HANDLER)
    def _05_search_summary_response_handler(self):
        """
        Create the search summary response handler that will generate the final response.
        """
        # If cache hit, check the response cache
        if self.log_data.cache_hit:
            response_cache_key = CacheKey.search_summary_response(
                self.rag_data.cache_key, self.rag_data.identified_language
            )
            cached_response = cache.get(response_cache_key)
            if cached_response and self.use_cache:
                self.log_data.response_cache_hit = True
                self.log_data.full_response = cached_response

                # If the response cache hit, create the response handler
                self.response_handler = response_handler.ResponseHandler(
                    self,
                    self.stream,
                    False,  # False for no error
                    cached_response,  # Cached response
                )
                return  # Exit early if response cache hit

        # If no cache hit, proceed to creating the non-cached response handler
        self.response_handler = response_handler.ResponseHandler(
            self,
            self.stream,
            False,  # False for no error
            None,  # No cached response
        )
        return

    def _enqueue_post_response_supplementary(self):
        """
        Enqueue post response supplementary jobs.
        """
        # Create product log from product list
        self.log_data.product = utils.get_product_log(
            self.rag_data.expanded_query,
            self.search_data.product_list,
            self.params.country_code,
        )

        # Determine whether the supplementary should be shown
        # Media
        if utils.should_show_supplement_type_by_intelligence(
            self.rag_data.intelligence_data,
            _07_supplementary_info.SupplementaryTypes.MEDIA.value,
        ):
            self.log_data.show_media = True

        # Product Card
        if utils.should_show_supplement_type_by_intelligence(
            self.rag_data.intelligence_data,
            _07_supplementary_info.SupplementaryTypes.PRODUCT_CARD.value,
        ):
            self.log_data.show_product_card = True

        # Related Query
        if utils.should_show_supplement_type_by_intelligence(
            self.rag_data.intelligence_data,
            _07_supplementary_info.SupplementaryTypes.RELATED_QUERY.value,
        ):
            self.log_data.show_related_query = True

        # Hyperlink
        if utils.should_show_supplement_type_by_intelligence(
            self.rag_data.intelligence_data,
            _07_supplementary_info.SupplementaryTypes.HYPERLINK.value,
        ):
            self.log_data.show_hyperlink = True

        # Supplement
        if self.log_data.error or self.log_data.timeout:
            # If there are errors or timeouts, do not show the supplement
            self.log_data.show_supplement = False
        elif self.log_data.guardrail_detected:
            # If guardrail is detected, do not show the supplement
            self.log_data.show_supplement = False
        elif self.log_data.response_path != response_types.SEARCH_SUMMARY_RESPONSE:
            # If the response path is not SEARCH_SUMMARY_RESPONSE, do not show the supplement
            self.log_data.show_supplement = False

        # Store the flags in cache
        message_flags = {
            MessageFlags.SHOW_SUPPLEMENT.value: self.log_data.show_supplement,
            MessageFlags.SHOW_MEDIA.value: self.log_data.show_media,
            MessageFlags.SHOW_PRODUCT_CARD.value: self.log_data.show_product_card,
            MessageFlags.SHOW_HYPERLINK.value: self.log_data.show_hyperlink,
            MessageFlags.SHOW_RELATED_QUERY.value: self.log_data.show_related_query,
        }
        cache.store(
            CacheKey.message_flags(self.message_id), message_flags, self.session_expiry
        )

        # Enqueue the supplementary jobs
        if self.log_data.show_supplement:
            django_rq.run_job_default(
                _07_supplementary_info.post_response_supplementary_info,
                (
                    self.object_id,
                    self.user_content.combined_query,
                    [],  # No message history
                    self.rag_data.expanded_query,
                    self.log_data.full_response,
                    self.log_data.product,
                    {"intelligence": self.rag_data.intelligence_data},
                    None,  # No sub intelligence value
                    self.params.channel,
                    self.params.country_code,
                    self.log_data.site_cd,
                    self.user_content.user_info,
                    self.rag_data.identified_language,
                    self.message_id,
                ),
                {},
            )

    def _update_search_cache(self):
        """
        Update the cache with the final response and log the necessary data.
        """
        # If the response path is SEARCH_SUMMARY_RESPONSE and no guardrail is detected
        # Update the cache
        if (
            self.log_data.response_path == response_types.SEARCH_SUMMARY_RESPONSE
            and not self.log_data.guardrail_detected
        ):
            # Store the full response in the cache if it exists and was not a cache hit
            if self.log_data.full_response and not self.log_data.response_cache_hit:
                # Store the full response in the cache if it does not already exist
                cache_key_response = CacheKey.search_summary_response(
                    self.rag_data.cache_key,
                    self.rag_data.identified_language,
                )
                if not cache.exists(cache_key_response):
                    cache.store(
                        cache_key_response,
                        self.log_data.full_response,
                        self.cache_expiry,
                    )

            # Save the RAG data to the cache if it was not a cache hit
            if not self.log_data.cache_hit:
                # Store the RAG data in the cache if it does not already exist
                if not cache.exists(self.rag_data.cache_key):
                    cache.store(
                        self.rag_data.cache_key,
                        {
                            "expanded_query": self.rag_data.expanded_query,
                            "unstructured_data": self.rag_data.unstructured_data,
                            "other_company_expression": self.rag_data.other_company_expression,
                            "product_model_info": self.rag_data.product_model_info,
                            "product_common_spec_info": self.rag_data.product_common_spec_info,
                            "product_spec_info": self.rag_data.product_spec_info,
                            "set_product_spec_info": self.rag_data.set_product_spec_info,
                            "reference_data": self.rag_data.reference_data,
                            "intelligence_data": self.rag_data.intelligence_data,
                            "response_layout_data": self.rag_data.response_layout_data,
                        },
                        self.cache_expiry,
                    )

    def _create_debug_cache_and_log(self):
        """
        Create a debug cache and log the necessary data.
        """
        # Create the debug log entry
        django_rq.run_job_high(
            rubicon_log.create_debug_log,
            (
                self.object_id,
                self.params.channel,
                self.log_data.country_code,
                self.params.lng,
                self.params.user_id,
                self.params.department,
                self.log_data.subsidiary,
                None,  # No session ID
                self.message_id,
                self.user_content.combined_query,
                self.master_debug_messages,
                self.timing_logs,
            ),
            {},
        )

        # Store the debug log in the cache
        cache.store(
            CacheKey.debug_content(self.message_id),
            self.master_debug_messages,
            self.session_expiry,
        )

        # Store the timing logs in the cache
        cache.store(
            CacheKey.debug_timing_logs(self.message_id),
            self.timing_logs,
            self.session_expiry,
        )

    def _update_search_log(self):
        """
        Update the search log with the necessary data.
        """
        django_rq.run_job_high(
            search_log.update_search_log,
            (
                self.object_id,
                self.message_id,
                {
                    "user_content": self.rag_data.expanded_query,
                    "full_response": self.log_data.full_response,
                },
                {
                    "intelligence": self.rag_data.intelligence_data,
                    "error": self.log_data.error != [],
                    "timeout": self.log_data.timeout != [],
                    "error_log": self.log_data.error,
                    "timeout_log": self.log_data.timeout,
                    "cache_hit": self.log_data.cache_hit,
                    "response_cache_hit": self.log_data.response_cache_hit,
                    "guardrail_detected": self.log_data.guardrail_detected,
                    "restricted": self.log_data.restricted,
                    "exception_detected": self.log_data.exception_detected,
                    "language": self.rag_data.identified_language,
                    "response_path": self.log_data.response_path,
                    "user_logged_in": bool(self.user_content.user_info),
                },
                self.log_data.product,
                utils.parse_timing_logs(self.timing_logs),
                self.pipeline_elapsed_time,
                self.log_data.subsidiary,
            ),
            {},
        )

    def run(self):
        """
        Run the Rubicon search flow.
        """
        # Debugging input arguments
        self._debug_params_arguments()

        # Debugging search data arguments
        self._debug_search_data_arguments()

        # Variable setup
        self._variable_setup()

        # Check original query
        self._check_original_query()

        # Enqueue language identification in the background
        side_job_mapping = self._enqueue_language_identification()

        # Load query cache
        self._load_query_cache()

        # Use Try / Finally to ensure background jobs are processed
        try:
            # If cache hit, skip RAG
            if not self.log_data.cache_hit:
                # Parallel processing for language identification, query expansion, AI search, and specification check
                self._parallel_query_expansion_ai_search_spec_check()
                # Parallel processing for intelligence identification and guardrails
                self._parallel_predefined_intelligence_guardrails()
                # Response layout retrieval
                self._response_layout()
        finally:
            self._background_jobs(side_job_mapping)

        # Organize the rag data
        self._04_merge_rag_data()

        # Create the response handler
        self._05_search_summary_response_handler()

    def enqueue_search_flow(self):
        """
        Run the Rubicon search flow and handle exceptions
        """
        try:
            self.run()

        except (
            InformationRestrictedException,
            InvalidOriginalQuery,
            EmptyOriginalQuery,
            ProcessTimeout,
            ProcessError,
            PreEmbargoQueryException,
            RedirectRequestException,
            NoDataFoundException,
            Exception,
        ) as e:
            print(f"{type(e).__name__} in rubicon: {e}")
            traceback_message = traceback.format_exc()
            print(traceback_message)

            # Alert Email
            if VITE_OP_TYPE in ["STG", "PRD"] and type(e) not in [
                EmptyStreamData,
                EmptyOriginalQuery,
                PreEmbargoQueryException,
                ProcessTimeout,
                RedirectRequestException,
                InformationRestrictedException,
                InvalidOriginalQuery,
                NoDataFoundException,
            ]:
                context_data = {
                    "API": "Rubicon Search Summary",
                    "Channel": self.params.channel,
                    "Country Code": self.params.country_code,
                    "Object ID": str(self.object_id),
                    "User ID": self.params.user_id,
                    "Message ID": self.message_id,
                    "Original Query": self.user_content.combined_query,
                }

                django_rq.run_job_high(
                    _14_azure_email_alert.send_process_error_alert,
                    (str(e), "pipeline_error"),
                    {
                        "error_traceback": traceback_message,
                        "context_data": context_data,
                    },
                )

            # Update the status code
            self.status.status = e.status_code if hasattr(e, "status_code") else 500

            # Update the exception detected flag
            self.log_data.exception_detected = True

            # Update the exception information
            self.log_data.exception_type = type(e).__name__
            self.log_data.exception_message = str(e)
            self.log_data.traceback_message = (
                traceback_message.split("\n") if traceback_message else ""
            )

            # Determine the response path based on the exception type
            self.log_data.response_path = {
                EmptyStreamData: response_types.EMPTY_STREAM_DATA_RESPONSE,
                EmptyOriginalQuery: response_types.EMPTY_ORIGINAL_QUERY_RESPONSE,
                PreEmbargoQueryException: response_types.PRE_EMBARGO_QUERY_RESPONSE,
                ProcessTimeout: response_types.TIMEOUT_RESPONSE,
                ProcessError: response_types.PROCESS_ERROR_RESPONSE,
                RedirectRequestException: response_types.REDIRECT_REQUEST_RESPONSE,
                InformationRestrictedException: response_types.INFORMATION_RESTRICTED_RESPONSE,
                InvalidOriginalQuery: response_types.TEXT_GUARDRAIL_RESPONSE,
                NoDataFoundException: response_types.NO_DATA_FOUND_RESPONSE,
            }.get(
                type(e), response_types.PROCESS_ERROR_RESPONSE
            )  # Default to process_error_response

            # Update the guardrail type based on the exception type
            if type(e) == InvalidOriginalQuery:
                if self.log_data.invalid_original_query_type in [
                    utils.OriginalQueryInvalidTypes.WORD,
                    utils.OriginalQueryInvalidTypes.PATTERN,
                ]:
                    self.log_data.guardrail_type = "S7"

            self.response_handler = response_handler.ResponseHandler(
                self, self.stream, True, None
            )

            # Update the message flags cache to not show supplements
            cached_message_flags: dict = cache.get(
                CacheKey.message_flags(self.message_id), {}
            )
            cache.store(
                CacheKey.message_flags(self.message_id),
                cached_message_flags.update(
                    {MessageFlags.SHOW_SUPPLEMENT.value: False}
                ),
                self.session_expiry,
            )

    def get_non_stream_search_summary(self):
        """
        Get the search summary results without streaming.
        """
        # Retrieve the search summary response
        response_result = self.response_handler.build_response()

        # Enqueue the post response supplementary jobs
        self._enqueue_post_response_supplementary()

        # Update Search Cache
        self._update_search_cache()

        # Update the search log and debug log
        self._create_debug_cache_and_log()
        self._update_search_log()

        # Return the response result
        return response_result

    async def get_stream_search_summary(self):
        """
        Stream the search summary results.
        """
        # Retrieve the search summary response
        for chunk in self.response_handler.stream_response():
            yield chunk
            await asyncio.sleep(0.0001)  # Force yield to event loop

        # Enqueue the post response supplementary jobs
        self._enqueue_post_response_supplementary()

        # Update Search Cache
        self._update_search_cache()

        # Update the search log and debug log
        self._create_debug_cache_and_log()
        self._update_search_log()
