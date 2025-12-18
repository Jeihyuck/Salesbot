import sys

sys.path.append("/www/alpha/")

import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "alpha.settings")
django.setup()

import re
import functools
import inspect
import asyncio
import time
import traceback
import copy
import types

from typing import Optional
from dataclasses import dataclass, field
from bson.objectid import ObjectId

from apps.rubicon_v3.__function import (
    _02_language_identification,
    _10_rewrite,
    _11_loading_message,
    _12_text_guard_rail,
    _13_image_guard_rail,
    _14_session_title,
    _15_correction_determination,
    _16_rewrite_correction,
    _20_orchestrator_NER_init,
    _20_orchestrator_predefined,
    _21_orchestrator_context_determination,
    _21_orchestrator_query_analyzer,
    _22_orchestrator_intelligence,
    _23_orchestrator_correction,
    _30_orchestrator_NER_standardization,
    _31_orchestrator_assistant,
    _32_sub_intelligence,
    _33_phatic_expression_detection,
    _39_rag_confirmation,
    _40_rag_distributer,
    _44_date_match,
    _50_structured,
    _55_personalized_rag,
    _60_complement,
    _71_product_rag_web_search,
    _72_product_rag_ai_search,
    _73_product_rag_specification_check,
    _75_product_rag_high_level_specification_check,
    _77_product_rag_high_level_price_check,
    _79_product_rag_merge_data,
    _81_response_layout,
    _82_response_prompts,
    __django_rq as django_rq,
    __embedding_rerank as embedding_rerank,
    __rubicon_log as rubicon_log,
    __utils as utils,
    __response_handler as response_handler,
)
from apps.rubicon_v3.__function.__django_cache_init import (
    create_validation_automaton,
    store_validation_patterns_in_cache,
)
from apps.rubicon_v3.__function.__django_cache import (
    DjangoCacheClient,
    SessionFlags,
    MessageFlags,
    CacheKey,
)
from apps.rubicon_v3.__function.__exceptions import (
    HttpStatus,
    EmptyStreamData,
    EmptyOriginalQuery,
    PreEmbargoQueryException,
    ProcessTimeout,
    ProcessError,
    RedirectRequestException,
    MultipleInputException,
    InformationRestrictedException,
    InvalidOriginalQuery,
    InvalidCodeMapping,
    InvalidStore,
    RewriteCorrectionFailureException,
)
from apps.rubicon_v3.__function.definitions import (
    channels,
    intelligences,
    sub_intelligences,
    response_types,
    ner_fields,
    site_cds,
)
from apps.rubicon_v3.__api import (
    _07_supplementary_info,
    _08_media,
    _09_related_query,
    _11_product_card,
    _13_chat_history,
)
from apps.rubicon_v3.__external_api._11_user_info import IndivInfo, getGuid
from apps.rubicon_v3.__external_api import _04_cs_ai_agent, _14_azure_email_alert
from alpha.settings import VITE_OP_TYPE, RQ_MAX_TIMEOUT

cache = DjangoCacheClient()


SECTION_NAME = "section_name"
MAX_STRUCTURED_DATA_SIZE = 20

create_validation_automaton(force_refresh=True)
store_validation_patterns_in_cache(force_refresh=True)


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


class ChatFlowSectionNames:

    @staticmethod
    def _to_name(obj):
        if isinstance(obj, types.ModuleType):
            return obj.__name__.split(".")[-1].replace("_", " ").strip().title()
        return str(obj)

    SESSION_INITIALIZATION = "Session Initialization"
    DEBUG_INPUT_ARGUMENTS = "Debug Input Arguments"
    VARIABLE_SETUP = "Variable Setup"
    MULTI_INPUT_CHECK = "Multi Input Check"
    MESSAGE_CANCEL_CHECK = "Message Cancel Check"
    LOGGING = "Logging"
    MASK_PII = "Mask PII"
    CHECK_ORIGINAL_QUERY = "Check Original Query"
    ENQUEUE_IMAGE_GUARDRAIL_SESSION_TITLE = (
        "Enqueue: Image Guardrail + Session Title Generation"
    )
    PARALLEL_REWRITE_LOADING_MESSAGE_TEXT_CLEANUP_LANGUAGE_DETECT_CORRECTION_DETERMINATION = "Parallel: Rewrite + Loading Message + Text Cleanup + Language Detect + Correction Determination"
    REWRITE_CORRECTION = "Rewrite Correction"
    EMBEDDING = "Embedding"
    CHECK_PREDEFINED_QUERY_CACHE = "Check Predefined + Query Cache"
    ENQUEUE_QUERY_REWRITE_TRANSLATION = "Enqueue: Query Rewrite Translation"
    PARALLEL_QUERY_ANALYZER_INTELLIGENCE_NER_CONTEXT_DETERMINATION = (
        "Parallel: Query Analyzer + Intelligence + NER + Context Determination"
    )
    CORRECTION = "Correction"
    ENQUEUE_CS_INTENTION_TEXT_GUARDRAIL = "Enqueue: Query Expansion Translation"
    PARALLEL_STANDARD_NER_ASSISTANT_SUB_INTELLIGENCE = (
        "Parallel: Standard NER + Assistant + Sub Intelligence"
    )
    RAG_CONFIRMATION = "RAG Confirmation"
    RAG_DISTRIBUTER = "RAG Distributer"
    PARALLEL_STRUCTURED_COMPLEMENT = "Parallel: Structured + Complement"
    PARALLEL_WEB_SEARCH_AI_SEARCH_SPECIFICATION_CHECK_HIGH_LEVEL_SPECIFICATION_CHECK = "Parallel: Web Search + AI Search + Specification Check + High Level Specification Check"
    BACKGROUND_JOBS = "Background Jobs"
    SUPPLEMENTARY_INFO = "Supplementary Info"
    RESPONSE_LAYOUT = "Response Layout"
    MERGE_DATA = "Merge Data"
    RESPONSE_HANDLER = "Response Handler"
    RESPONSE_GENERATION = "Response Generation"
    EXCEPTION_HANDLING = "Exception Handling"
    MESSAGE_HISTORY_UPDATE = "Message History Update"


class RubiconChatFlow:
    # Background Functions
    FUNC_QUERY_TRANSLATION = _02_language_identification.translate_queries
    FUNC_IMAGE_GUARDRAIL = _13_image_guard_rail.image_guardrail
    FUNC_RUBICON_TEXT_GUARDRAIL = _12_text_guard_rail.rubicon_text_guardrail
    FUNC_MODERATION_TEXT_GUARDRAIL = _12_text_guard_rail.moderation_text_guardrail
    FUNC_INJECTION_TEXT_GUARDRAIL = _12_text_guard_rail.injection_text_guardrail
    FUNC_SESSION_TITLE_GENERATION = _14_session_title.session_title_generation
    FUNC_CS_INTENTION = _04_cs_ai_agent.cs_ai_agent

    NUM_MESSAGE_HISTORY = 6

    @dataclass
    class InputArguments:
        channel: str
        country_code: str
        model: str
        meta: dict
        user_id: str
        session_id: str
        message_id: str
        message_history: list
        message: list
        lng: str = "en"
        gu_id: str = "default_gu_id"
        sa_id: str = "default_sa_id"
        jwt_token: str = "default_jwt_token"
        estore_sitecode: str = "default_estore_sitecode"
        department: str = "-"

    @dataclass
    class InputFiles:
        files: list = field(default_factory=list)
        image_files: list = field(default_factory=list)
        audio_files: list = field(default_factory=list)

    @dataclass
    class IntermediateData:
        cached_data: dict = field(default_factory=dict)
        predefined_data: dict = field(default_factory=dict)
        ner_data: dict = field(default_factory=dict)
        assistant_data: dict = field(default_factory=dict)
        intelligence_data: dict = field(default_factory=dict)
        sub_intelligence_data: dict = field(default_factory=dict)
        structured_data: dict = field(default_factory=dict)
        complement_data: dict = field(default_factory=dict)
        web_search_data: dict = field(default_factory=dict)
        ai_search_data: dict = field(default_factory=dict)
        shallow_ai_search_data: dict = field(default_factory=dict)
        specification_check_data: dict = field(default_factory=dict)
        high_level_specification_check_data: dict = field(default_factory=dict)
        high_level_price_check_data: dict = field(default_factory=dict)
        response_layout_data: dict = field(default_factory=dict)
        translated_query_data: dict = field(default_factory=dict)

    @dataclass
    class OrchestratorData:
        language: str = None
        query_analyzer_data: dict = field(default_factory=dict)
        orch_init_ner_data: dict = field(default_factory=dict)
        orch_gpt_determination_data: dict = field(default_factory=dict)
        orch_use_search_gpt_flag: bool = False
        correct_rewritten_queries: bool = False
        personalization_required: bool = False
        rewritten_queries: list = field(default_factory=list)
        rewritten_keywords: list = field(default_factory=list)
        unprocessed_queries: list = field(default_factory=list)
        unprocessed_embeddings: list = field(default_factory=list)
        embedding_data: dict = field(default_factory=dict)
        no_rag_queries: list = field(default_factory=list)
        deep_rag_queries: list = field(default_factory=list)
        cs_queries: list = field(default_factory=list)
        rag_confirmation_status: str = (
            _39_rag_confirmation.RagConfirmationStatus.SUCCESS.value
        )
        date_match_data: dict = field(default_factory=dict)
        all_cache_hit: bool = False
        all_predefined_hit: bool = False
        all_cs_hit: bool = False

    @dataclass
    class MessageHistoryData:
        messages: list = field(default_factory=list)
        combined_query: str = ""
        mentioned_products: list = field(default_factory=list)

    @dataclass
    class LogData:
        no_cache_queries: set = field(default_factory=set)
        error_queries: set = field(default_factory=set)
        timeout: list = field(default_factory=list)
        error: list = field(default_factory=list)
        product: list = field(default_factory=list)
        intelligence: dict = field(default_factory=dict)
        sub_intelligence: dict = field(default_factory=dict)
        ner: dict = field(default_factory=dict)
        query_analyzer: dict = field(default_factory=dict)
        complement: dict = field(default_factory=dict)
        response_cache_hit: bool = False
        query_cache: set = field(default_factory=set)
        country_code: str = ""
        subsidiary: str = ""
        site_cd: str = ""
        show_supplement: bool = True
        show_media: bool = False
        show_product_card: bool = False
        show_related_query: bool = False
        show_hyperlink: bool = False
        guardrail_detected: bool = False
        restricted: bool = False
        exception_detected: bool = False
        should_delete_session_cache: bool = False
        session_title: str = ""
        session_initial_message_id: str = ""
        invalid_original_query_reason: str = ""
        invalid_original_query_type: str = ""
        updated_message_history: list = field(default_factory=list)
        cs_data: dict = field(default_factory=dict)
        merged_data: dict = field(default_factory=dict)
        to_cache_data: dict = field(default_factory=dict)
        guardrail_type: str = "S1"
        user_query: str = ""
        response_path: str = ""
        full_response: str = ""
        exception_type: str = ""
        exception_message: str = ""
        traceback_message: str = ""

    @dataclass
    class UserData:
        user_info: dict = field(default_factory=dict)
        user_product_info: dict = field(default_factory=dict)
        user_recommendation_data: dict = field(default_factory=dict)
        user_recommendation_used: dict = field(default_factory=dict)

    @dataclass
    class EvaluationData:
        informative_data: dict = field(default_factory=dict)

    def __init__(
        self,
        input_arguments: InputArguments,
        input_files: InputFiles,
        object_id: ObjectId,
        use_cache: bool,
        stream: bool,
        simple: bool,
        status: HttpStatus,
    ):
        self.input = input_arguments
        self.input_files = input_files
        self.use_cache = use_cache
        self.stream = stream
        self.simple = simple
        self.object_id = object_id
        self.status = status
        self.intermediate = RubiconChatFlow.IntermediateData()
        self.orchestrator = RubiconChatFlow.OrchestratorData()
        self.message_history_data = RubiconChatFlow.MessageHistoryData()
        self.log_data = RubiconChatFlow.LogData()
        self.user_data = RubiconChatFlow.UserData()
        self.evaluation_data = RubiconChatFlow.EvaluationData()
        self.start_time = time.time()
        self.pipeline_elapsed_time = 0
        self.gpt_model_name = "gpt-4.1-mini"
        self.session_expiry = 60 * 60 * 1  # 1 hour
        self.cache_expiry = 60 * 60 * 24 * 14  # 2 weeks
        self.master_debug_messages = []
        self._timeout = 10
        self.timing_logs = []
        self._response_cache_key = None
        self._session_flags_cache_key = CacheKey.session_flags(self)
        self._message_flags_cache_key = CacheKey.message_flags(self)
        self.response_handler = None

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
            def wrapper(self: "RubiconChatFlow", *args, **kwargs):
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

    @debug_sync_timer(ChatFlowSectionNames.SESSION_INITIALIZATION)
    def _initialize_session(self):
        """
        Initialize the session by setting up necessary cache keys and flags.
        """
        utils.init_django_cache_session(
            self.input.session_id,
            self.input.message_id,
            self.input.user_id,
            self.input.channel,
            self.input.country_code,
            self.input.lng,
            self.session_expiry,
        )

    @debug_sync_timer(ChatFlowSectionNames.DEBUG_INPUT_ARGUMENTS)
    def _00_debug_input_arguments(self):
        """
        Debug the input arguments of the rubicon_debug function.

        rubicon_debug 함수의 입력 인수를 디버그합니다.
        입력 인수 중 특정 키를 제외하고 필터링하여 디버그 함수에 전달합니다.
        제외할 키:
        - "cache_client"
        - "files"
        """
        # Define the keys to exclude
        disallowed_keys = {"cache_client", "files", "status"}

        # Include all keys except those in disallowed_keys
        d = {k: v for k, v in self.input.__dict__.items() if k not in disallowed_keys}

        # Pass the filtered dictionary to __debug
        self.debug(**d)

    @debug_sync_timer(ChatFlowSectionNames.VARIABLE_SETUP)
    def _00_variable_setup(self):
        """
        Set up the initial variables and configurations for the chat flow.
        """
        # Get the subsidiary based on channel and country code
        self.log_data.subsidiary = utils.get_subsidiary(
            self.input.channel, self.input.country_code
        )

        # Get the site_cd based on channel and country code
        self.log_data.site_cd = utils.get_site_cd(
            self.input.channel, self.input.country_code
        )

        # Save the original country code to log and update it
        self.log_data.country_code = self.input.country_code
        if self.input.country_code != "KR":
            self.input.country_code = "GB"

        # Set the original query to the combined query as default
        self.message_history_data.combined_query = str(
            next(item for item in self.input.message if item["type"] == "text")[
                "content"
            ]
        ).strip()

        # Get the last 6 message history items from the cache
        django_cache_message_history = cache.get(CacheKey.message_history(self), [])
        if django_cache_message_history:
            django_cache_message_history = django_cache_message_history[
                -self.NUM_MESSAGE_HISTORY :
            ]
        else:
            django_cache_message_history = []
        self.message_history_data.messages = django_cache_message_history

        # Get the last 6 mentioned products from the cache
        mentioned_products = cache.get(CacheKey.mentioned_products(self), [])
        if mentioned_products:
            mentioned_products = mentioned_products[-self.NUM_MESSAGE_HISTORY :]
        else:
            mentioned_products = []
        self.message_history_data.mentioned_products = mentioned_products

        # Get the session title from the cache
        self.log_data.session_title = cache.get(CacheKey.session_title(self))

        # Get the session initial message id from the cache
        self.log_data.session_initial_message_id = cache.get(
            CacheKey.session_initial_message_id(self)
        )

        # File categorization
        categorized_files = utils.categorize_files(self.input_files.files)
        image_files = [
            file for file, _ in categorized_files.get(utils.FileType.IMAGE, [])
        ]
        audio_files = [
            file for file, _ in categorized_files.get(utils.FileType.AUDIO, [])
        ]
        self.input_files.image_files = image_files
        self.input_files.audio_files = audio_files

        # Check if channel is Custom Timeout
        if self.input.channel == channels.CUSTOM_TIMEOUT:
            self._timeout = (
                RQ_MAX_TIMEOUT  # Use the maximum timeout defined in settings
            )

        # Get the language from cache
        self.orchestrator.language = cache.get(CacheKey.language(self))

        # Initialize the user info class
        user_info_class = IndivInfo(
            self.input.country_code,
            self.input.sa_id,
            self.input.gu_id,
            self.input.channel,
        )

        # Check if user info is in cache
        user_info_cache_key = CacheKey.user_info(
            self.input.sa_id, self.input.country_code
        )
        self.user_data.user_info = cache.get(user_info_cache_key, {})
        # If user info is not in cache, fetch it
        if (
            not self.user_data.user_info
            and self.input.sa_id
            and self.input.sa_id != "default_sa_id"
        ):
            # Grab user info data
            if user_info_class:
                self.user_data.user_info = asyncio.run(user_info_class.getUserInfo())
            # Store the user info in cache
            if self.user_data.user_info:
                cache.store(
                    user_info_cache_key, self.user_data.user_info, 60 * 30
                )  # 30 minutes

        # Check if user product info is in cache
        user_product_info_cache_key = CacheKey.user_product_info(
            self.input.sa_id, self.input.country_code
        )
        self.user_data.user_product_info = cache.get(user_product_info_cache_key, {})
        # If user product info is not in cache, fetch it
        if (
            not self.user_data.user_product_info
            and self.input.sa_id
            and self.input.sa_id != "default_sa_id"
        ):
            # Grab user product info data
            if user_info_class:
                # If guid in user info class is default, update it
                if not user_info_class.guid or user_info_class.guid == "default_gu_id":
                    _ = asyncio.run(user_info_class.getUserInfo())
                self.user_data.user_product_info = asyncio.run(
                    user_info_class.getUserProducts()
                )
            # Store the user product info in cache
            if self.user_data.user_product_info:
                cache.store(
                    user_product_info_cache_key,
                    self.user_data.user_product_info,
                    60 * 30,  # 30 minutes
                )

        # For Sprinklr channel, force the simple flag to True
        if self.input.channel == channels.SPRINKLR:
            self.simple = True

        self.debug(
            django_cache_message_history,
            mentioned_products=self.message_history_data.mentioned_products,
            subsidiary=self.log_data.subsidiary,
            site_cd=self.log_data.site_cd,
            country_code=self.input.country_code,
            combined_query=self.message_history_data.combined_query,
            session_title=self.log_data.session_title,
            session_initial_message_id=self.log_data.session_initial_message_id,
            timeout_value=self._timeout,
            simple_answer=self.simple,
        )

    @debug_sync_timer(ChatFlowSectionNames.MULTI_INPUT_CHECK)
    def _multi_input_check(self):
        """
        Check if the input is a multi-input query.
        """
        is_multi_input = None
        multi_input_combined_query = None
        multi_input_message_history = None
        consecutive_message_ids = None

        # If it is a multi-input query, need to combine the user messages and cancel the other requests
        is_multi_input = utils.check_multi_input(self.input.message_history)
        if is_multi_input:
            (
                multi_input_combined_query,
                multi_input_message_history,
                consecutive_message_ids,
            ) = utils.get_multi_input_combined_query_message_history_cancel_message_ids(
                self.message_history_data.combined_query, self.input.message_history
            )
            print("Multi-input query detected. Cancelling other requests.")
            for message_id in consecutive_message_ids:
                cache.store(
                    CacheKey.multi_input(message_id),
                    True,
                    self.cache_expiry,
                )
            # Update the mongo documents of the other requests
            django_rq.run_job_high(
                rubicon_log.update_message_log_multi_input,
                (self.object_id, consecutive_message_ids),
                {},
            )

            self.message_history_data.combined_query = multi_input_combined_query
            self.message_history_data.messages = multi_input_message_history[
                -self.NUM_MESSAGE_HISTORY :
            ]
        else:
            # If not multi-input, fix the message history if it is not empty
            if self.input.message_history:
                multi_input_message_history = utils.get_multi_input_message_history(
                    self.input.message_history
                )
                self.message_history_data.messages = multi_input_message_history[
                    -self.NUM_MESSAGE_HISTORY :
                ]

        self.debug(
            is_multi_input,
            consecutive_message_ids,
            consolidated_message_history=self.message_history_data.messages,
            consolidated_original_query=self.message_history_data.combined_query,
        )

    @debug_sync_timer(ChatFlowSectionNames.MESSAGE_CANCEL_CHECK)
    def _message_cancel_check(self):
        """
        Check if the message is cancelled.
        """
        is_cancelled = None
        if self.input.channel in [channels.SPRINKLR]:
            # Check if the message is cancelled
            is_cancelled = cache.get(CacheKey.multi_input(self), False)
            if is_cancelled:
                self.debug(is_cancelled)
                raise MultipleInputException(
                    "Message has been cancelled due to multi-input."
                )

    @debug_sync_timer(ChatFlowSectionNames.MASK_PII)
    def _00_mask_pii(self):
        # Mask PII in the original query and message history
        self.message_history_data.combined_query, self.message_history_data.messages = (
            utils.mask_pii(
                self.message_history_data.combined_query,
                self.message_history_data.messages,
                self.input.country_code,
            )
        )

        self.debug(
            masked_original_query=self.message_history_data.combined_query,
            masked_message_history=self.message_history_data.messages,
        )

    @debug_sync_timer(ChatFlowSectionNames.CHECK_ORIGINAL_QUERY)
    def _00_check_original_query(self):
        """
        원본 쿼리를
        """
        flag, invalid_type, message = utils.check_original_query(
            self.message_history_data.combined_query,
            self.input.channel,
            self.orchestrator.language,
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
            and self.input.channel != channels.GUARDRAIL_BYPASS
        ):
            raise InvalidOriginalQuery(f"Original query is invalid. Reason: {message}")
        elif (
            not flag
            and invalid_type == utils.OriginalQueryInvalidTypes.PRE_EMBARGO
            and self.input.channel != channels.GUARDRAIL_BYPASS
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

    @debug_sync_timer(ChatFlowSectionNames.ENQUEUE_IMAGE_GUARDRAIL_SESSION_TITLE)
    def _enqueue_image_guardrail_session_title(self):
        # Prepare the function parameters
        # Only enqueue image guardrail if there are image files
        if self.input_files.image_files:
            image_guardrail_params = [
                (
                    self.FUNC_IMAGE_GUARDRAIL,
                    (
                        self.input_files.image_files,
                        self.gpt_model_name,
                    ),
                    {},
                    None,
                    None,
                )
            ]
        else:
            image_guardrail_params = []

        # Only enqueue session title if not already set
        if not self.log_data.session_title:
            session_title_params = [
                (
                    self.FUNC_SESSION_TITLE_GENERATION,
                    (
                        self.message_history_data.combined_query,
                        self.input_files.image_files,
                        self.orchestrator.language,
                        self.gpt_model_name,
                    ),
                    {},
                    None,
                    None,
                )
            ]
        else:
            session_title_params = []

        side_job_mapping = django_rq.enqueue_dynamic_jobs(
            image_guardrail_params + session_title_params
        )

        return side_job_mapping

    @debug_sync_timer(
        ChatFlowSectionNames.PARALLEL_REWRITE_LOADING_MESSAGE_TEXT_CLEANUP_LANGUAGE_DETECT_CORRECTION_DETERMINATION
    )
    def _parallel_rewrite_loading_message_lang_detect_correction_determination(
        self, gpt_model_name
    ):
        REWRITE_FUNC = _10_rewrite.re_write_history
        LOADING_MSG_FUNC = _11_loading_message.loading_message_generation
        LANGUAGE_DETECT_FUNC = _02_language_identification.lang_detect_with_gpt
        CORRECTION_DETERMINATION = _15_correction_determination.correction_determination

        # Prepare the function parameters
        function_params = [
            (
                REWRITE_FUNC,
                (
                    self.message_history_data.combined_query,
                    self.input_files.image_files,
                    self.message_history_data.messages,
                    (
                        self.message_history_data.mentioned_products[-1]
                        if len(self.message_history_data.mentioned_products) > 0
                        else []
                    ),
                    self.input.channel,
                    self.input.country_code,
                    gpt_model_name,
                ),
                {},
                None,
                None,
            ),
            (
                LOADING_MSG_FUNC,
                (
                    self.message_history_data.combined_query,
                    self.input_files.image_files,
                    self.message_history_data.messages,
                    self.orchestrator.language,
                    self.input.country_code,
                    self.gpt_model_name,
                ),
                {},
                None,
                None,
            ),
            (
                LANGUAGE_DETECT_FUNC,
                (
                    self.message_history_data.combined_query,
                    self.message_history_data.messages,
                    self.orchestrator.language,
                ),
                {},
                None,
                None,
            ),
        ]

        # Add the correction determination function if there is user product info
        if self.user_data.user_product_info:
            function_params.append(
                (
                    CORRECTION_DETERMINATION,
                    (
                        self.message_history_data.combined_query,
                        self.message_history_data.messages,
                        self.input_files.image_files,
                        self.input.country_code,
                    ),
                    {},
                    None,
                    None,
                ),
            )

        job_mapping = django_rq.enqueue_dynamic_jobs(function_params)  # Enqueue jobs
        results = django_rq.get_all_results(job_mapping)  # Get results

        # Process results
        language_data = None
        language_debug_data = None
        rewritten_queries_raw = {}
        loading_message_data = None
        correction_determination_data = None
        timeout_message_data = {}
        error_message_data = {}

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

            if result.status == django_rq.Status.SUCCESS:
                if job_name == REWRITE_FUNC.__name__:
                    rewritten_queries_raw = result.result
                elif job_name == LOADING_MSG_FUNC.__name__:
                    loading_message_data = result.result
                elif job_name == LANGUAGE_DETECT_FUNC.__name__:
                    language_data, language_debug_data = result.result
                    # Language Cache Update
                    if language_data and self.orchestrator.language != language_data:
                        cache.store(
                            CacheKey.language(self),
                            language_data.strip(),
                            self.session_expiry,
                        )
                        self.orchestrator.language = language_data.strip()
                elif job_name == CORRECTION_DETERMINATION.__name__:
                    correction_determination_data = result.result
                    if (
                        correction_determination_data
                        and "determination" in correction_determination_data
                    ):
                        if correction_determination_data["determination"] == "true":
                            self.orchestrator.correct_rewritten_queries = True
                        elif (
                            correction_determination_data["determination"]
                            == "recommendation"
                        ):
                            self.orchestrator.personalization_required = True
                else:
                    # Handle error
                    raise ValueError(f"Job not found: {job_name}")

            elif result.status == django_rq.Status.TIMEOUT:
                # Handle timeout
                timeout_message_data[job_name] = f"Timeout in {job_name}"
                self.log_data.no_cache_queries.add(q)
                self.log_data.timeout.append(
                    {"name": parts[0], "message": f"Timeout in {job_name}"}
                )
            else:
                # Handle error
                error_message_data[job_name] = f"Error in {job_name}: {result.error}"
                self.log_data.error_queries.add(q)
                self.log_data.error.append(
                    {
                        "name": parts[0],
                        "message": f"Error in {job_name}: {result.error}",
                    }
                )

        cleaned_rewritten_queries = []
        if isinstance(rewritten_queries_raw, dict):
            cleaned_rewritten_queries = [
                utils.clean_text(query)
                for query in rewritten_queries_raw.get("re_write_query_list", [])
                if query
            ]

            self.orchestrator.rewritten_queries = cleaned_rewritten_queries.copy()
            self.orchestrator.rewritten_keywords = rewritten_queries_raw.get(
                "re_write_keyword_list", []
            )

        # Store loading message in cache
        cache.store(
            CacheKey.loading_message(self),
            loading_message_data,
            self.session_expiry,
        )

        self.debug(
            timeout_message_data,
            error_message_data,
            language_data,
            language_debug_data,
            loading_message_data,
            correction_determination_data,
            rewritten_queries_raw,
            cleaned_rewritten_queries,
            keywords=self.orchestrator.rewritten_keywords,
            no_cache_queries=list(self.log_data.no_cache_queries),
            error_queries=list(self.log_data.error_queries),
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

    @debug_sync_timer(ChatFlowSectionNames.REWRITE_CORRECTION)
    def _rewrite_correction(self):
        """
        Correct the rewritten queries.
        """
        # Get the corrected rewritten queries
        rewrite_correction_data = _16_rewrite_correction.re_write_correction(
            self.orchestrator.rewritten_queries,
            self.input.country_code,
            self.log_data.site_cd,
            self.user_data.user_product_info,
        )

        # Update the rewritten queries and keywords
        self.orchestrator.rewritten_queries = [
            utils.clean_text(query)
            for query in rewrite_correction_data["re_write_query_list"]
        ]
        self.orchestrator.rewritten_keywords = rewrite_correction_data[
            "re_write_keyword_list"
        ]

        # Log the rewrite correction data
        self.debug(
            rewrite_correction_data,
            rewritten_queries=self.orchestrator.rewritten_queries,
            keywords=self.orchestrator.rewritten_keywords,
        )

        # Check if rewrite correction failed
        if rewrite_correction_data.get("rewrite_correction_failure"):
            raise RewriteCorrectionFailureException(
                "Rewrite correction failed. Correction needed but could not be applied."
            )

    @debug_sync_timer(ChatFlowSectionNames.EMBEDDING)
    def _embedding(self):
        embeddings = embedding_rerank.baai_embedding(
            self.orchestrator.rewritten_queries, self.input.message_id
        )
        for query, embed in zip(self.orchestrator.rewritten_queries, embeddings):
            self.orchestrator.embedding_data[query] = embed

    @debug_sync_timer(ChatFlowSectionNames.CHECK_PREDEFINED_QUERY_CACHE)
    def _check_predefined_query_cache(self):
        unprocessed_query_set = set()
        predefined_debug_data = {}

        # Load predefined data for each rewritten query
        for query in self.orchestrator.rewritten_queries:
            predefined_data, predefined_debug = (
                _20_orchestrator_predefined.check_predefined(
                    query,
                    self.orchestrator.embedding_data[query],
                    self.input.country_code,
                    self.input.channel,
                    self.log_data.site_cd,
                    self.input.message_id,
                )
            )
            if predefined_data:
                self.intermediate.predefined_data[query] = predefined_data
                predefined_debug_data[query] = predefined_debug
            else:
                unprocessed_query_set.add(query)

        unprocessed_queries = list(unprocessed_query_set)

        # Reset unprocessed query set
        unprocessed_query_set = set()

        # Load cached data for each rewritten query
        for query in unprocessed_queries:
            cached_item = cache.get(CacheKey.query_cache_key(query, self), {})

            if cached_item and self.use_cache:
                self.intermediate.cached_data[query] = cached_item
                self.log_data.query_cache.add(query)
            else:
                unprocessed_query_set.add(query)

        self.orchestrator.unprocessed_queries = list(unprocessed_query_set)
        self.orchestrator.unprocessed_embeddings = [
            self.orchestrator.embedding_data[query] for query in unprocessed_query_set
        ]

        self.debug(
            predefined_data=self.intermediate.predefined_data,
            predefined_debug_data=predefined_debug_data,
            cached_data=self.intermediate.cached_data,
            unprocessed_queries=self.orchestrator.unprocessed_queries,
        )

    @debug_sync_timer(ChatFlowSectionNames.ENQUEUE_QUERY_REWRITE_TRANSLATION)
    def _enqueue_query_rewrite_translation(self, side_job_mapping: dict):
        """
        Enqueue the query rewrite translation job.
        """
        # Prepare the function parameters
        query_translation_params = [
            (
                self.FUNC_QUERY_TRANSLATION,
                (
                    query,
                    self.orchestrator.language,
                    self.input.country_code,
                ),
                {},
                query,
                None,
            )
            for query in self.orchestrator.rewritten_queries
            if query not in self.intermediate.cached_data
        ]

        # Enqueue the query translation job
        side_job_mapping.update(
            django_rq.enqueue_dynamic_jobs(query_translation_params)
        )

        return side_job_mapping

    @debug_sync_timer(
        ChatFlowSectionNames.PARALLEL_QUERY_ANALYZER_INTELLIGENCE_NER_CONTEXT_DETERMINATION
    )
    def _parallel_query_analyzer_intelligence_ner_context_determination(
        self,
    ):
        QUERY_ANALYZER_FUNC = _21_orchestrator_query_analyzer.query_analyzer
        INTELLIGENCE_FUNC = _22_orchestrator_intelligence.intelligence
        NER_FUNC = _20_orchestrator_NER_init.ner
        CONTEXT_DETERMINATION_FUNC = (
            _21_orchestrator_context_determination.context_determination
        )

        query_analyzer_params = [
            (
                QUERY_ANALYZER_FUNC,
                (
                    query,
                    self.message_history_data.messages,
                ),
                {"country_code": self.input.country_code},
                query,
                None,
            )
            for query in self.orchestrator.unprocessed_queries
        ]
        intelligence_params = [
            (
                INTELLIGENCE_FUNC,
                (
                    query,
                    self.gpt_model_name,
                    self.input.country_code,
                ),
                {},
                query,
                None,
            )
            for query in self.orchestrator.unprocessed_queries
        ]
        ner_params = [
            (
                NER_FUNC,
                (
                    query,
                    embed,
                    self.input.country_code,
                    self.gpt_model_name,
                ),
                {},
                query,
                None,
            )
            for query, embed in zip(
                self.orchestrator.unprocessed_queries,
                self.orchestrator.unprocessed_embeddings,
            )
        ]

        # Only run context determination if the it is not the first message of the session
        # And the rewritten queries have not been corrected
        gpt_determination_params = []
        if (
            self.input.message_id != self.log_data.session_initial_message_id
            and not self.orchestrator.correct_rewritten_queries
        ):
            gpt_determination_params = [
                (
                    CONTEXT_DETERMINATION_FUNC,
                    (
                        self.message_history_data.combined_query,
                        self.orchestrator.rewritten_queries,
                        self.message_history_data.messages,
                        self.input_files.image_files,
                        "gpt-4.1",
                    ),
                    {},
                    None,
                    None,
                )
            ]

        # Enqueue jobs
        job_mapping = django_rq.enqueue_dynamic_jobs(
            function_params=query_analyzer_params
            + intelligence_params
            + ner_params
            + gpt_determination_params
        )
        results = django_rq.get_all_results(job_mapping)

        # Process results
        timeout_message_data = {}
        error_message_data = {}
        init_ner_debug = {}

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

            if result.status == django_rq.Status.SUCCESS:
                if job_name.startswith(QUERY_ANALYZER_FUNC.__name__):
                    self.orchestrator.query_analyzer_data[q] = result.result
                elif job_name.startswith(INTELLIGENCE_FUNC.__name__):
                    self.intermediate.intelligence_data[q] = result.result
                elif job_name.startswith(NER_FUNC.__name__):
                    self.orchestrator.orch_init_ner_data[q], init_ner_debug = (
                        result.result
                    )
                elif job_name.startswith(CONTEXT_DETERMINATION_FUNC.__name__):
                    self.orchestrator.orch_gpt_determination_data = result.result
                else:
                    # Handle error
                    raise ValueError(f"Job not found: {job_name}")
            elif result.status == django_rq.Status.TIMEOUT:
                # Handle timeout
                timeout_message_data[job_name] = f"Timeout in {job_name}"
                self.log_data.no_cache_queries.add(q)
                self.log_data.timeout.append(
                    {"name": parts[0], "message": f"Timeout in {job_name}"}
                )

            else:
                # Handle error
                error_message_data[job_name] = f"Error in {job_name}: {result.error}"
                self.log_data.error_queries.add(q)
                self.log_data.error.append(
                    {
                        "name": parts[0],
                        "message": f"Error in {job_name}: {result.error}",
                    }
                )

        self.debug(
            timeout_message_data,
            error_message_data,
            no_cache_queries=list(self.log_data.no_cache_queries),
            error_queries=list(self.log_data.error_queries),
            predefined_data=self.intermediate.predefined_data,
            query_analyzer_data=self.orchestrator.query_analyzer_data,
            intelligence_data=self.intermediate.intelligence_data,
            init_ner_data=self.orchestrator.orch_init_ner_data,
            init_ner_debug=init_ner_debug,
            context_determination_data=self.orchestrator.orch_gpt_determination_data,
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

    @debug_sync_timer(ChatFlowSectionNames.CORRECTION)
    def _correction(self):
        """
        Perform correction on Init NER, Intelligence, Query Analyzer
        """
        is_cs_intention_query = lambda query: self.intermediate.intelligence_data.get(
            query
        ) in [
            intelligences.ERROR_AND_FAILURE_RESPONSE,
            intelligences.SERVICE_AND_REPAIR_GUIDE,
        ]

        for query in self.orchestrator.unprocessed_queries:
            (
                self.orchestrator.orch_init_ner_data[query],
                self.intermediate.intelligence_data[query],
                self.orchestrator.query_analyzer_data[query],
            ) = _23_orchestrator_correction.correction(
                self.orchestrator.orch_init_ner_data[query],
                self.intermediate.intelligence_data[query],
                self.orchestrator.query_analyzer_data[query],
                self.input.channel,
                self.input.country_code,
            )

        # Find the first intelligence that fails the channel filter check
        for query, intelligence in self.intermediate.intelligence_data.items():
            # First check the must always check intelligences
            if intelligence in [
                intelligences.ERROR_AND_FAILURE_RESPONSE,
                intelligences.SERVICE_AND_REPAIR_GUIDE,
            ]:
                if not utils.channel_intelligence_check(
                    self.input.channel, intelligence
                ):
                    self.log_data.restricted = True
                    raise InformationRestrictedException(
                        f"Information restricted for channel: {self.input.channel}. Intelligence: {intelligence}"
                    )

            # Then check the rest of the intelligences depending on the RAG depth
            if self.orchestrator.query_analyzer_data.get(query) and (
                self.orchestrator.query_analyzer_data[query].get("RAG_depth")
                == _21_orchestrator_query_analyzer.RAGDepth.NONE.value
            ):
                if not utils.channel_intelligence_check(
                    self.input.channel, intelligence
                ):
                    # Do a second validation to check if the query is a phatic expression
                    if not _33_phatic_expression_detection.phatic_expression_detection(
                        query,
                        self.gpt_model_name,
                    ):
                        self.log_data.restricted = True
                        raise InformationRestrictedException(
                            f"Information restricted for channel: {self.input.channel}. Intelligence: {intelligence}"
                        )

        # Check if the gpt determination deems web search gpt is needed (also check ner for extend request)
        # If any of the intelligence data is purchase policy or error and failure, do not use web search gpt
        if (
            self.orchestrator.orch_gpt_determination_data
            and self.orchestrator.query_analyzer_data
            and self.intermediate.intelligence_data
        ):
            if (
                (
                    self.orchestrator.orch_gpt_determination_data.get("determination")
                    == "original"
                )
                and (
                    not any(
                        item
                        == _21_orchestrator_query_analyzer.QueryType.EXTENDED_REQUEST.value
                        for query_analyzer in self.orchestrator.query_analyzer_data.values()
                        for item in query_analyzer.get("query_type", [])
                    )
                )
            ) and (
                not any(
                    intelligence
                    in [
                        intelligences.BUY_INFORMATION,
                        intelligences.PURCHASE_POLICY,
                        intelligences.ERROR_AND_FAILURE_RESPONSE,
                        intelligences.SERVICE_AND_REPAIR_GUIDE,
                        intelligences.ORDERS_AND_DELIVERY,
                    ]
                    for intelligence in self.intermediate.intelligence_data.values()
                )
            ):
                # Update the determination flag
                self.orchestrator.orch_use_search_gpt_flag = True

        # Check if query should not be cached due to extended request
        for query, value in self.orchestrator.query_analyzer_data.items():
            if any(
                item == _21_orchestrator_query_analyzer.QueryType.EXTENDED_REQUEST.value
                for item in value.get("query_type", [])
            ):
                self.log_data.no_cache_queries.add(query)

        # Grab all the cs intention queries
        self.orchestrator.cs_queries = [
            query
            for query in self.intermediate.intelligence_data
            if is_cs_intention_query(query)
        ]

        # Grab the no RAG and deep RAG queries
        self.orchestrator.no_rag_queries = [
            query
            for query, value in self.orchestrator.query_analyzer_data.items()
            if value.get("RAG_depth")
            == _21_orchestrator_query_analyzer.RAGDepth.NONE.value
            and query in self.orchestrator.unprocessed_queries
            and not is_cs_intention_query(query)
        ]

        self.orchestrator.deep_rag_queries = [
            query
            for query, value in self.orchestrator.query_analyzer_data.items()
            if value.get("RAG_depth")
            == _21_orchestrator_query_analyzer.RAGDepth.DEEP.value
            and query in self.orchestrator.unprocessed_queries
            and not is_cs_intention_query(query)
        ]

        # Check if all the queries are CS intention queries
        if len(self.orchestrator.cs_queries) == len(
            self.orchestrator.unprocessed_queries
        ):
            self.orchestrator.all_cs_hit = True

        self.debug(
            corrected_init_ner_data=self.orchestrator.orch_init_ner_data,
            corrected_intelligence_data=self.intermediate.intelligence_data,
            corrected_query_analyzer_data=self.orchestrator.query_analyzer_data,
            no_rag_queries=self.orchestrator.no_rag_queries,
            deep_rag_queries=self.orchestrator.deep_rag_queries,
            cs_intention_queries=self.orchestrator.cs_queries,
            all_cs_intention_hit=self.orchestrator.all_cs_hit,
            use_search_gpt_flag=self.orchestrator.orch_use_search_gpt_flag,
            no_cache_queries=list(self.log_data.no_cache_queries),
            error_queries=list(self.log_data.error_queries),
        )

    @debug_sync_timer(ChatFlowSectionNames.ENQUEUE_CS_INTENTION_TEXT_GUARDRAIL)
    def _enqueue_cs_intention_text_guardrail(self, side_job_mapping: dict):
        """
        Enqueue the query translation job
        """
        # Prepare the function parameters
        cs_intention_params = [
            (
                self.FUNC_CS_INTENTION,
                (
                    query,
                    self.message_history_data.messages,
                ),
                {},
                query,
                None,
            )
            for query in self.orchestrator.cs_queries
            if self.input.country_code == "KR" and not self.orchestrator.all_cs_hit
        ]
        rubicon_text_guardrail_params = [
            (
                self.FUNC_RUBICON_TEXT_GUARDRAIL,
                (query, self.message_history_data.messages),
                {},
                query,
                None,
            )
            for query in self.orchestrator.unprocessed_queries
            + [self.message_history_data.combined_query]
        ]
        moderation_text_guardrail_params = [
            (
                self.FUNC_MODERATION_TEXT_GUARDRAIL,
                (
                    self.message_history_data.combined_query,
                    self.message_history_data.messages,
                ),
                {},
                self.message_history_data.combined_query,
                None,
            )
        ]
        injection_text_guardrail_params = [
            (
                self.FUNC_INJECTION_TEXT_GUARDRAIL,
                (
                    self.message_history_data.combined_query,
                    self.message_history_data.messages,
                ),
                {},
                self.message_history_data.combined_query,
                None,
            )
        ]

        # Enqueue the query translation job
        side_job_mapping.update(
            django_rq.enqueue_dynamic_jobs(
                cs_intention_params
                + rubicon_text_guardrail_params
                + moderation_text_guardrail_params
                + injection_text_guardrail_params
            )
        )

        return side_job_mapping

    @debug_sync_timer(
        ChatFlowSectionNames.PARALLEL_STANDARD_NER_ASSISTANT_SUB_INTELLIGENCE
    )
    def _parallel_standard_ner_assistant_sub_intelligence(self):
        STANDARD_NER_FUNC = (
            _30_orchestrator_NER_standardization.standardize_ner_expression
        )
        ASSISTANT_FUNC = _31_orchestrator_assistant.assistant
        SUB_INTELLIGENCE_FUNC = _32_sub_intelligence.get_sub_intelligence

        # Prepare the function parameters
        standard_ner_params = [
            (
                STANDARD_NER_FUNC,
                (
                    self.orchestrator.orch_init_ner_data.get(query, []),
                    self.input.country_code,
                    self.gpt_model_name,
                ),
                {},
                query,
                None,
            )
            for query in self.orchestrator.deep_rag_queries
        ]
        assistant_params = [
            (
                # _24_assistant.assistant,
                ASSISTANT_FUNC,
                (
                    query,
                    self.message_history_data.messages,
                    self.input.country_code,
                    self.orchestrator.query_analyzer_data.get(query, {}).get(
                        "RAG_depth", ""
                    ),
                    self.orchestrator.query_analyzer_data.get(query, {}).get(
                        "query_type", ""
                    ),
                    self.orchestrator.orch_init_ner_data.get(query, {}),
                    self.intermediate.intelligence_data.get(
                        query, intelligences.GENERAL_INFORMATION
                    ),
                    self.gpt_model_name,
                ),
                {},
                query,
                None,
            )
            for query in self.orchestrator.deep_rag_queries
        ]
        sub_intelligence_params = [
            (
                SUB_INTELLIGENCE_FUNC,
                (
                    query,
                    self.intermediate.intelligence_data.get(
                        query, intelligences.GENERAL_INFORMATION
                    ),
                    self.input.country_code,
                ),
                {},
                query,
                None,
            )
            for query in self.orchestrator.unprocessed_queries
        ]

        job_mapping = django_rq.enqueue_dynamic_jobs(
            standard_ner_params + assistant_params + sub_intelligence_params
        )
        results = django_rq.get_all_results(job_mapping)

        # Process results
        timeout_message_data = {}
        error_message_data = {}

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

            if result.status == django_rq.Status.SUCCESS:
                if job_name.startswith(STANDARD_NER_FUNC.__name__):
                    self.intermediate.ner_data[q] = result.result
                elif job_name.startswith(ASSISTANT_FUNC.__name__):
                    self.intermediate.assistant_data[q] = result.result
                elif job_name.startswith(SUB_INTELLIGENCE_FUNC.__name__):
                    self.intermediate.sub_intelligence_data[q] = result.result
                else:
                    # Handle error
                    raise ValueError(f"Job not found: {job_name}")
            elif result.status == django_rq.Status.TIMEOUT:
                # Handle timeout
                timeout_message_data[job_name] = f"Timeout in {job_name}"
                self.log_data.no_cache_queries.add(q)
                self.log_data.timeout.append(
                    {"name": parts[0], "message": f"Timeout in {job_name}"}
                )

            else:
                # Handle error
                error_message_data[job_name] = f"Error in {job_name}: {result.error}"
                self.log_data.error_queries.add(q)
                self.log_data.error.append(
                    {
                        "name": parts[0],
                        "message": f"Error in {job_name}: {result.error}",
                    }
                )

        # Grab Date Match List
        for query, ner_list in self.intermediate.ner_data.items():
            self.orchestrator.date_match_data[query] = (
                _44_date_match.match_and_parse_datetime(
                    ner_list, self.input.country_code, self.input.message_id
                )
            )

        self.debug(
            timeout_message_data,
            error_message_data,
            no_cache_queries=list(self.log_data.no_cache_queries),
            error_queries=list(self.log_data.error_queries),
            standardized_ner_data=self.intermediate.ner_data,
            assistant_data=self.intermediate.assistant_data,
            date_match_data=self.orchestrator.date_match_data,
            sub_intelligence_data=self.intermediate.sub_intelligence_data,
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

        # Find the first sub intelligence that failed the check
        for sub_intelligence in self.intermediate.sub_intelligence_data.values():
            if not utils.channel_sub_intelligence_check(
                self.input.channel, sub_intelligence
            ):
                self.log_data.restricted = True
                raise InformationRestrictedException(
                    f"Information restricted for channel: {self.input.channel}. Sub Intelligence: {sub_intelligence}"
                )

    @debug_sync_timer(ChatFlowSectionNames.RAG_CONFIRMATION)
    def _rag_confirmation(self):
        """
        Perform RAG confirmation
        """
        (
            self.orchestrator.deep_rag_queries,
            self.orchestrator.no_rag_queries,
            self.log_data.no_cache_queries,
            self.log_data.error_queries,
            self.orchestrator.rag_confirmation_status,
        ) = _39_rag_confirmation.rag_confirmation(
            self.orchestrator.deep_rag_queries,
            self.orchestrator.no_rag_queries,
            self.orchestrator.unprocessed_queries,
            self.orchestrator.rewritten_queries,
            self.intermediate.ner_data,
            self.intermediate.intelligence_data,
            self.intermediate.sub_intelligence_data,
            self.intermediate.assistant_data,
            cache.get(self._session_flags_cache_key, {}).get(
                SessionFlags.TURNS_SINCE_RE_ASKED.value, 5
            ),
            self.orchestrator.personalization_required,
            self.log_data.no_cache_queries,
            self.log_data.error_queries,
        )

        self.debug(
            deep_rag_queries=self.orchestrator.deep_rag_queries,
            no_rag_queries=self.orchestrator.no_rag_queries,
            no_cache_queries=list(self.log_data.no_cache_queries),
            error_queries=list(self.log_data.error_queries),
            rag_confirmation_status=self.orchestrator.rag_confirmation_status,
        )

    @debug_sync_timer(ChatFlowSectionNames.RAG_DISTRIBUTER)
    def _40_rag_distributer(self):
        (
            structured_distribution_data,
            complement_distribution_data,
            self.log_data.no_cache_queries,
            self.log_data.error_queries,
            self.orchestrator.deep_rag_queries,
            self.orchestrator.no_rag_queries,
        ) = _40_rag_distributer.rag_distributer(
            self.orchestrator.deep_rag_queries,
            self.orchestrator.no_rag_queries,
            self.orchestrator.embedding_data,
            self.orchestrator.query_analyzer_data,
            self.intermediate.intelligence_data,
            self.intermediate.sub_intelligence_data,
            self.orchestrator.orch_init_ner_data,
            self.intermediate.ner_data,
            self.intermediate.assistant_data,
            self.orchestrator.date_match_data,
            self.log_data.no_cache_queries,
            self.log_data.error_queries,
            self.input.country_code,
        )

        self.debug(
            no_cache_queries=list(self.log_data.no_cache_queries),
            error_queries=list(self.log_data.error_queries),
            deep_rag_queries=self.orchestrator.deep_rag_queries,
            no_rag_queries=self.orchestrator.no_rag_queries,
            structured_distribution_data=[
                {
                    "query": query,
                    "embedding": embedding[:5],
                    "intelligence": intel,
                    "sub_intelligence": sub_intel,
                    "structured_view": structured_view,
                    "transformed_ner": transformed_ner,
                }
                for query, embedding, intel, sub_intel, structured_view, transformed_ner in structured_distribution_data
            ],
            complement_distribution_data=[
                {
                    "query": query,
                    "embedding": embedding[:5],
                    "query_analyzer": query_analyzer,
                    "intel": intel,
                    "sub_intel": sub_intel,
                    "init_ner": init_ner,
                    "transformed_ner": transformed_ner,
                    "assistant_output_list": assistant_output,
                    "date_match_list": date_match_list,
                }
                for query, embedding, query_analyzer, intel, sub_intel, init_ner, transformed_ner, assistant_output, date_match_list in complement_distribution_data
            ],
        )
        return (structured_distribution_data, complement_distribution_data)

    @debug_sync_timer(ChatFlowSectionNames.PARALLEL_STRUCTURED_COMPLEMENT)
    def _parallel_50_structured_60_complement(
        self, structured_distribution_data, complement_distribution_data
    ):
        STRUCTURED_FUNC = _50_structured.process_structured_rag
        PERSONALIZED_FUNC = _55_personalized_rag.process_personalized_rag
        COMPLEMENT_FUNC = _60_complement.complement

        # Helper function to determine if the query is a personalized recommendation query
        is_personal_recommendation = (
            lambda query: self.intermediate.sub_intelligence_data.get(query)
            == sub_intelligences.PERSONALIZED_RECOMMENDATION
        )

        # Prepare the function parameters
        structured_rag_params = [
            # First function: _50_structured
            (
                STRUCTURED_FUNC,
                (
                    query,
                    embedding,
                    intel,
                    sub_intel,
                    structured_view,
                    transformed_ner,
                    getGuid(self.user_data.user_info),
                    self.input.sa_id,
                    self.input.country_code,
                    self.input.channel,
                    self.log_data.site_cd,
                    self.input.message_id,
                ),
                {},
                query,
                None,
            )
            for query, embedding, intel, sub_intel, structured_view, transformed_ner in structured_distribution_data
        ]
        complement_params = [
            # Second function: _60_complement
            (
                COMPLEMENT_FUNC,
                (
                    query,
                    embedding,
                    query_analyzer,
                    intel,
                    sub_intel,
                    init_ner,
                    transformed_ner,
                    assistant_output_list,
                    date_match_list,
                    self.input.country_code,
                    getGuid(self.user_data.user_info),
                    self.input.message_id,
                    self.input.session_id,
                    self.cache_expiry,
                    self.input.channel,
                    self.message_history_data.mentioned_products,
                    self.log_data.site_cd,
                ),
                {},
                query,
                None,
            )
            for query, embedding, query_analyzer, intel, sub_intel, init_ner, transformed_ner, assistant_output_list, date_match_list in complement_distribution_data
        ]

        # Add personalized RAG if required
        personalized_rag_params = []
        if self.orchestrator.personalization_required:
            personalized_rag_params = [
                (
                    PERSONALIZED_FUNC,
                    (
                        self.user_data.user_product_info,
                        self.input.country_code,
                        self.log_data.site_cd,
                    ),
                    {},
                    query,
                    None,
                )
                for query in self.orchestrator.deep_rag_queries
                if is_personal_recommendation(query)
            ]

        # Enqueue jobs
        job_mapping = django_rq.enqueue_dynamic_jobs(
            structured_rag_params + complement_params + personalized_rag_params
        )
        results = django_rq.get_all_results(job_mapping)

        # Process results
        timeout_message_data = {}
        error_message_data = {}
        structured_data_debug_list = []

        # Process results
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

            if result.status == django_rq.Status.SUCCESS:
                if job_name.startswith(STRUCTURED_FUNC.__name__):
                    self.intermediate.structured_data[q] = copy.deepcopy(result.result)
                    # Limit the structured rag size to the MAX_STRUCTURED_DATA_SIZE
                    if (
                        result.result
                        and isinstance(result.result, dict)
                        and result.result.get("structured_rag", [])
                    ):
                        if (
                            len(result.result["structured_rag"])
                            >= MAX_STRUCTURED_DATA_SIZE
                        ):
                            clipped_result = result.result["structured_rag"][
                                :MAX_STRUCTURED_DATA_SIZE
                            ]
                            self.intermediate.structured_data[q][
                                "structured_rag"
                            ] = clipped_result
                            structured_data_debug_list.append(
                                {
                                    "query": q,
                                    "structured_rag.length": len(
                                        result.result["structured_rag"]
                                    ),
                                    "structured_rag.clipped_length": len(
                                        clipped_result
                                    ),
                                }
                            )
                elif job_name.startswith(COMPLEMENT_FUNC.__name__):
                    self.intermediate.complement_data[q] = result.result
                elif job_name.startswith(PERSONALIZED_FUNC.__name__):
                    self.user_data.user_recommendation_data[q] = result.result

                else:
                    # Handle error
                    raise ValueError(f"Job not found: {job_name}")

            elif result.status == django_rq.Status.TIMEOUT:
                # Handle timeout
                timeout_message_data[job_name] = f"Timeout in {job_name}"
                self.log_data.no_cache_queries.add(q)
                self.log_data.timeout.append(
                    {"name": parts[0], "message": f"Timeout in {job_name}"}
                )

            else:
                # Handle error
                error_message_data[job_name] = f"Error in {job_name}: {result.error}"
                self.log_data.error_queries.add(q)
                self.log_data.error.append(
                    {
                        "name": parts[0],
                        "message": f"Error in {job_name}: {result.error}",
                    }
                )

        # If personalized recommendation is available, replace the complement data's extended info result
        for query, value in self.user_data.user_recommendation_data.items():
            # Filter out the personal recommendations that are non-relevant
            filtered_value = _55_personalized_rag.filter_personalized_rag(
                self.intermediate.complement_data.get(query, {}),
                value,
                self.input.country_code,
            )
            if filtered_value:
                self.intermediate.complement_data[query][
                    "extended_info_result"
                ] = filtered_value
                self.user_data.user_recommendation_used[query] = True

        # For certain sub intelligences, set the extended info result of complement data to empty
        # This is to prevent erroneous data from being used
        emptied_extended_info_queries = set()
        for query, data in self.intermediate.complement_data.items():
            if self.intermediate.sub_intelligence_data.get(query) in [
                sub_intelligences.PRODUCT_INVENTORY_AND_RESTOCKING,
                sub_intelligences.CONSUMABLES_ACCESSORIES_RECOMMENDATION,
                sub_intelligences.IN_STORE_GUIDE,
            ]:
                data["extended_info_result"] = []
                emptied_extended_info_queries.add(query)

        self.debug(
            timeout_message_data,
            error_message_data,
            no_cache_queries=list(self.log_data.no_cache_queries),
            error_queries=list(self.log_data.error_queries),
            structured_data=self.intermediate.structured_data,
            complement_data=self.intermediate.complement_data,
            user_recommendation_data=self.user_data.user_recommendation_data,
            user_recommendation_used=self.user_data.user_recommendation_used,
            emptied_extended_info_queries=list(emptied_extended_info_queries),
            structured_data_debug_list=structured_data_debug_list,
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

        # Raise exception if complement had error getting code map
        for data in self.intermediate.complement_data.values():
            if data.get("code_mapping_error_list"):
                for error in data.get("code_mapping_error_list"):
                    if error.get("error_type") in [
                        "invalid model code",
                        "code filter failed",
                        # "invalid model name",
                    ]:
                        raise InvalidCodeMapping(
                            f"Error in product mapping. {error.get("error_type")}: {error.get("expression")}"
                        )

        # Raise exception if structured had invalid store mapping
        for data in self.intermediate.structured_data.values():
            if data.get("invalid_store"):
                error_message = f"Error in store mapping. Query: {data.get("query")}"
                if data.get("debug_messages") and isinstance(
                    data["debug_messages"], list
                ):
                    error_message = ". ".join(data["debug_messages"])
                raise InvalidStore(error_message)

    @debug_sync_timer(
        ChatFlowSectionNames.PARALLEL_WEB_SEARCH_AI_SEARCH_SPECIFICATION_CHECK_HIGH_LEVEL_SPECIFICATION_CHECK
    )
    def _7x_web_search_ai_search_specification_check_high_level_specification_check(
        self,
    ):
        FUNC_WEB_SEARCH = _71_product_rag_web_search.get_google_search_results
        FUNC_AI_SEARCH = _72_product_rag_ai_search.execute_unstructured_rag
        FUNC_SPECIFICATION_CHECK = (
            _73_product_rag_specification_check.specification_check
        )
        FUNC_HIGH_LEVEL_SPECIFICATION_CHECK = (
            _75_product_rag_high_level_specification_check.high_level_specification_check
        )
        FUNC_HIGH_LEVEL_PRICE_CHECK = (
            _77_product_rag_high_level_price_check.high_level_price_check
        )

        is_product_description = (
            lambda query: self.intermediate.intelligence_data.get(query)
            == intelligences.PRODUCT_DESCRIPTION
        )

        is_product_lineup = lambda query: self.intermediate.sub_intelligence_data.get(
            query
        ) in [
            sub_intelligences.PRODUCT_LINEUP_COMPARISON,
            sub_intelligences.PRODUCT_LINEUP_DESCRIPTION,
            sub_intelligences.PRODUCT_LINEUP_RECOMMENDATION,
        ]

        # high level spec 적용 대상 판단
        is_proper_code_mapping_type = lambda query: any(
            (type_vals in ["p2p", "h2h"])
            & (isinstance(code_mapping.get("option", []), list))
            for code_mapping in self.intermediate.complement_data.get(query, {}).get(
                "code_mapping", []
            )
            for type_vals in code_mapping.get("type", [])
        ) and not any(
            (type_vals in ["e2e", "c2c"])
            & (isinstance(code_mapping.get("option", []), list))
            for code_mapping in self.intermediate.complement_data.get(query, {}).get(
                "code_mapping", []
            )
            for type_vals in code_mapping.get("type", [])
        )

        is_promotion = lambda query: self.intermediate.sub_intelligence_data.get(
            query
        ) in [
            sub_intelligences.PRICE_EXPLANATION,
            sub_intelligences.PAYMENT_BENEFIT_EXPLANATION,
            sub_intelligences.EVENT_PROMOTION,
            sub_intelligences.BUNDLE_DISCOUNT,
        ]

        no_more_info = lambda query: self.intermediate.complement_data.get(
            query, {}
        ).get("mentioned_stop_key", False)

        is_exchange = (
            lambda query: self.intermediate.intelligence_data.get(query)
            == intelligences.PURCHASE_POLICY
        )

        is_managed_only = lambda query: self.intermediate.complement_data.get(
            query, {}
        ).get("managed_only", False)

        is_invalid_code_mapping = lambda query: bool(
            self.intermediate.complement_data.get(query, {}).get(
                "code_mapping_error_list", []
            )
        )

        is_extended_request = lambda query: any(
            item == _21_orchestrator_query_analyzer.QueryType.EXTENDED_REQUEST.value
            for item in self.orchestrator.query_analyzer_data.get(query, {}).get(
                "query_type", []
            )
        )

        has_price_field = lambda query: any(
            ner_item.get("field") == ner_fields.PRODUCT_PRICE
            for ner_item in self.intermediate.ner_data.get(query, [])
        )

        has_personal_recommendation = (
            lambda query: self.user_data.user_recommendation_used.get(query)
        )

        # Determine which queries to use for web search and AI search
        use_queries = []
        if self.orchestrator.orch_use_search_gpt_flag:
            use_queries.extend([self.message_history_data.combined_query])
        else:
            if self.orchestrator.deep_rag_queries:
                use_queries = self.orchestrator.deep_rag_queries
            else:
                use_queries = self.orchestrator.no_rag_queries

        # 기존 50, 60번대에서 생성하던 web input을 self를 사용하여 생성하도록 변경
        web_search_input_data = {}
        for query in use_queries:
            web_search_input_data[query] = {
                "query": query,
                "intelligence": self.intermediate.intelligence_data.get(
                    query, "Shallow"
                ),
                "sub_intelligence": self.intermediate.sub_intelligence_data.get(
                    query, "Shallow"
                ),
                "type": "top_query",
            }

        ai_search_input_data = {}
        # for query in use_queries:
        #     ai_search_input_data[query] = {
        #         "query": query,
        #         "intelligence": self.intermediate.intelligence_data.get(
        #             query, "Shallow"
        #         ),
        #         "sub_intelligence": self.intermediate.sub_intelligence_data.get(
        #             query, "Shallow"
        #         ),
        #         "code_mapping": self.intermediate.complement_data.get(query, {}).get(
        #             "code_mapping", []
        #         ),
        #         "extended_info_result": self.intermediate.complement_data.get(
        #             query, {}
        #         ).get("extended_info_result", []),
        #         "ner": self.intermediate.ner_data.get(query, {}),
        #         "channel_id": self.input.channel,
        #     }

        for query in use_queries:
            group_list = []
            group_dict = {}
            base_data = {
                "query": query,
                "intelligence": self.intermediate.intelligence_data.get(
                    query, "Shallow"
                ),
                "sub_intelligence": self.intermediate.sub_intelligence_data.get(
                    query, "Shallow"
                ),
                "ner": self.intermediate.ner_data.get(query, {}),
                "channel_id": self.input.channel,
            }

            code_mapping = self.intermediate.complement_data.get(query, {}).get(
                "code_mapping", []
            )
            extended_info_result = self.intermediate.complement_data.get(query, {}).get(
                "extended_info_result", []
            )

            if not code_mapping:
                group_dict = {
                    **base_data,
                    "code_mapping": [],
                    "extended_info_result": extended_info_result,
                }
                group_list.append(group_dict)
            elif not extended_info_result:
                group_dict = {
                    **base_data,
                    "code_mapping": code_mapping,
                    "extended_info_result": [],
                }
                group_list.append(group_dict)
            else:
                # Group extended_info by id cycles
                from collections import defaultdict

                id_groups = defaultdict(list)

                current_group = 0
                last_id = None

                for item in extended_info_result:
                    item_id = item.get("id", 0)

                    # Detect when ID sequence resets (e.g., 2 -> 0)
                    if last_id is not None and item_id <= last_id:
                        current_group += 1

                    id_groups[current_group].append(item)
                    last_id = item_id

                # Create AI search input for each group
                for group_idx, group_items in id_groups.items():
                    if group_idx < len(code_mapping):
                        group_key = f"{query}_group_{group_idx}"
                        group_dict = {
                            **base_data,
                            "code_mapping": [code_mapping[group_idx]],
                            "extended_info_result": group_items,
                            "original_query": query,
                            "group_index": group_idx,
                        }
                        group_list.append(group_dict)

            if (
                self.intermediate.sub_intelligence_data.get(query, "")
                in [
                    sub_intelligences.SMARTTHINGS_EXPLANATION,
                ]
                and extended_info_result
            ):
                group_dict = {
                    **base_data,
                    "code_mapping": [],
                    "extended_info_result": extended_info_result,
                    "exact_search": True,
                }
                group_list.append(group_dict)

            ai_search_input_data[query] = group_list

        # product model & option이 존재하는 경우 model + option으로 bm25 검색
        # product model이 존재하는 경우는 model로만 검색
        # product option이 존재하는 경우는 option으로만 검색
        for query, group_list in ai_search_input_data.items():
            for query_object in group_list:
                new_keywords_list = []
                is_option: bool = False
                for ner in self.intermediate.ner_data.get(query, []):
                    # new_keywords_list.append(ner.get("expression", ""))
                    if ner.get("field") == "product_model" and ner.get("expression"):
                        new_keywords_list.append(ner["expression"])
                    elif ner.get("field") == "product_option" and ner.get("expression"):
                        is_option = True
                        new_keywords_list.append(ner["expression"])

                if is_option:
                    query_object["restricted_search_keyword"] = new_keywords_list

        # Prepare the function parameters
        web_search_params = [
            (
                FUNC_WEB_SEARCH,
                (
                    utils.modify_keyword_for_web_search(
                        self.orchestrator.rewritten_keywords, self.input.country_code
                    ),
                    item["query"],
                    item["intelligence"],
                    item["sub_intelligence"],
                    item["type"],
                    item,
                    self.input.country_code,
                ),
                {},
                query,
                None,
            )
            for query, item in web_search_input_data.items()
            if not is_promotion(query)
            and not no_more_info(query)
            and not is_exchange(query)
            and not is_managed_only(query)
            and not is_invalid_code_mapping(query)
            and item["sub_intelligence"]
            not in [
                sub_intelligences.SAMSUNG_STORE_INFORMATION,
                sub_intelligences.IN_STORE_GUIDE,
                sub_intelligences.SERVICE_CENTER_EXPLANATION,
                sub_intelligences.INSTALLATION_CONDITIONS_AND_STANDARDS,
                sub_intelligences.PRODUCT_INVENTORY_AND_RESTOCKING,
                sub_intelligences.ACCOUNT_ACTIVITY,
                sub_intelligences.ORDER_DELIVERY_TRACKING,
            ]
            and not (
                self.log_data.site_cd == site_cds.FN
                and item["sub_intelligence"] == sub_intelligences.FAQ_INFORMATION
            )
            and not is_extended_request(query)
            and not has_personal_recommendation(query)
        ]

        ai_search_vector_params = [
            (
                FUNC_AI_SEARCH,
                (
                    items["query"],
                    self.orchestrator.rewritten_keywords,
                    items["intelligence"],
                    items["sub_intelligence"],
                    items["code_mapping"],
                    items["extended_info_result"],
                    items["ner"],
                    items["channel_id"],
                    self.input.country_code,
                    self.log_data.site_cd,
                    max(2, 8 // len(lists)),
                ),
                {"vector_search": True},
                query,
                f"vector_{idx}",
            )
            for query, lists in ai_search_input_data.items()
            for idx, items in enumerate(lists)
            if not no_more_info(query)
            and not is_managed_only(query)
            and not items.get("exact_search", False)
            and not has_personal_recommendation(query)
        ]

        ai_search_bm25_params = [
            (
                FUNC_AI_SEARCH,
                (
                    items["query"],
                    items.get("restricted_search_keyword", ""),
                    items["intelligence"],
                    items["sub_intelligence"],
                    items["code_mapping"],
                    items["extended_info_result"],
                    items["ner"],
                    items["channel_id"],
                    self.input.country_code,
                    self.log_data.site_cd,
                    max(2, 8 // len(lists)),
                    items.get("exact_search", False),
                ),
                {"vector_search": False},
                query,
                f"bm25_{idx1}_{idx2}",
            )
            for idx1, (query, lists) in enumerate(ai_search_input_data.items())
            for idx2, items in enumerate(lists)
            if (
                not no_more_info(query)
                and not is_managed_only(query)
                and items["sub_intelligence"] is not None
                and not has_personal_recommendation(query)
            )
            or (
                items["intelligence"] in ["Installation Inquiry"]
                and items["extended_info_result"]
            )
        ]

        specification_check_params = [
            (
                FUNC_SPECIFICATION_CHECK,
                (
                    item["extended_info_result"],
                    self.input.country_code,
                    (
                        self.intermediate.intelligence_data.get(query)
                        == intelligences.PRODUCT_DESCRIPTION
                    ),
                    self.log_data.site_cd,
                ),
                {},
                query,
                None,
            )
            for query, item in self.intermediate.complement_data.items()
            if not no_more_info(query)
            and item.get("extended_info_result")
            and not is_managed_only(query)
            and not is_invalid_code_mapping(query)
            and not is_product_lineup(query)
        ]

        high_level_specification_check_params = [
            (
                FUNC_HIGH_LEVEL_SPECIFICATION_CHECK,
                (
                    query,
                    item["extended_info_result"],
                    item.get("l4_filter_list", []),
                    self.input.country_code,
                ),
                {},
                query,
                None,
            )
            for query, item in self.intermediate.complement_data.items()
            if is_product_description(query)
            and item.get("extended_info_result")
            and is_proper_code_mapping_type(query)
            and not no_more_info(query)
            and not is_managed_only(query)
            and not is_invalid_code_mapping(query)
            and not has_personal_recommendation(query)
        ]

        high_level_price_check_params = [
            (
                FUNC_HIGH_LEVEL_PRICE_CHECK,
                (
                    [
                        code
                        for code_mapping in value.get("code_mapping", [])
                        for code in code_mapping.get("mapping_code", [])
                        if code
                    ],
                    self.intermediate.complement_data.get(query, {}).get(
                        "initial_extended_info_result", []
                    ),
                    self.intermediate.complement_data.get(query, {}).get(
                        "extended_info_result", []
                    ),
                    self.input.country_code,
                    self.log_data.site_cd,
                ),
                {},
                query,
                None,
            )
            for query, value in self.intermediate.complement_data.items()
            if has_price_field(query) and not has_personal_recommendation(query)
        ]

        # Enqueue all jobs
        job_mapping = django_rq.enqueue_dynamic_jobs(
            web_search_params
            + ai_search_vector_params
            + ai_search_bm25_params
            + specification_check_params
            + high_level_specification_check_params
            + high_level_price_check_params
        )
        results = django_rq.get_all_results(job_mapping, timeout=RQ_MAX_TIMEOUT)

        # Process results
        timeout_message_data = {}
        error_message_data = {}
        debug_specification_check = []
        debug_high_level_specification_check = []
        bm25_ai_search_data = {}
        vector_ai_search_data = {}

        # Process results
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

            # web search data initializing
            if q not in self.intermediate.web_search_data.keys():
                self.intermediate.web_search_data[q] = []

            if result.status == django_rq.Status.SUCCESS:
                if job_name.startswith(FUNC_WEB_SEARCH.__name__):
                    self.intermediate.web_search_data[q].extend(result.result)
                elif job_name.startswith(FUNC_AI_SEARCH.__name__):
                    if isinstance(result.result, list):
                        add_ls = result.result
                    else:
                        add_ls = [result.result]
                    if "vector" in s:
                        if q in vector_ai_search_data:
                            vector_ai_search_data[q].extend(add_ls)
                        else:
                            vector_ai_search_data[q] = add_ls
                    elif "bm25" in s:
                        if q in bm25_ai_search_data:
                            bm25_ai_search_data[q].extend(add_ls)
                        else:
                            bm25_ai_search_data[q] = add_ls
                    else:
                        raise ValueError(f"Invalid suffix for AI search: {s}")

                    if q not in self.intermediate.ai_search_data:
                        self.intermediate.ai_search_data[q] = add_ls
                    else:
                        self.intermediate.ai_search_data[q].extend(add_ls)
                elif job_name.startswith(FUNC_SPECIFICATION_CHECK.__name__):
                    specification_result, debug_specification_check = result.result
                    self.intermediate.specification_check_data[q] = list(
                        specification_result
                    )
                elif job_name.startswith(FUNC_HIGH_LEVEL_SPECIFICATION_CHECK.__name__):
                    (
                        high_level_specification_result,
                        debug_high_level_specification_check,
                    ) = result.result
                    self.intermediate.high_level_specification_check_data[q] = (
                        high_level_specification_result
                    )
                elif job_name.startswith(FUNC_HIGH_LEVEL_PRICE_CHECK.__name__):
                    self.intermediate.high_level_price_check_data[q] = result.result
                else:
                    # Handle error
                    raise ValueError(f"Job not found: {job_name}")
            elif result.status == django_rq.Status.TIMEOUT:
                # Handle timeout
                timeout_message_data[job_name] = f"Timeout in {job_name}"
                self.log_data.no_cache_queries.add(q)
                self.log_data.timeout.append(
                    {"name": parts[0], "message": f"Timeout in {job_name}"}
                )

            else:
                # Handle error
                error_message_data[job_name] = f"Error in {job_name}: {result.error}"
                self.log_data.error_queries.add(q)
                self.log_data.error.append(
                    {
                        "name": parts[0],
                        "message": f"Error in {job_name}: {result.error}",
                    }
                )

        self.debug(
            timeout_message_data,
            error_message_data,
            use_queries,
            no_cache_queries=list(self.log_data.no_cache_queries),
            error_queries=list(self.log_data.error_queries),
            bm25_ai_search_data={
                q: utils.truncate_text_data_for_display(v)
                for q, v in bm25_ai_search_data.items()
            },
            vector_ai_search_data={
                q: utils.truncate_text_data_for_display(v)
                for q, v in vector_ai_search_data.items()
            },
            web_search_data={
                q: utils.truncate_text_data_for_display(v)
                for q, v in self.intermediate.web_search_data.items()
            },
            shallow_ai_search_data={
                q: utils.truncate_text_data_for_display(v, 100, "chunk")
                for q, v in self.intermediate.shallow_ai_search_data.items()
            },
            # bm25_ai_search_data,
            # vector_ai_search_data,
            # web_search_data=self.intermediate.web_search_data,
            # ai_search_data=self.intermediate.ai_search_data,
            specification_check_data=self.intermediate.specification_check_data,
            high_level_specification_check_data=self.intermediate.high_level_specification_check_data,
            debug_specification_check="\n".join(
                [
                    f"data: {item.get('data')}\n"
                    + f"sql_product: {item.get('sql_product')}\n"
                    + f"product_codes_result: {item.get('product_codes_result')}\n"
                    + f"sql: {item.get('sql')}\n"
                    for item in debug_specification_check
                ]
            ),
            debug_high_level_specification_check=debug_high_level_specification_check,
            high_level_price_check_data=self.intermediate.high_level_price_check_data,
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

    @debug_sync_timer(ChatFlowSectionNames.BACKGROUND_JOBS)
    def _background_jobs(self, side_job_mapping):
        results = django_rq.get_all_results(side_job_mapping)

        # Process results
        timeout_message_data = {}
        error_message_data = {}
        image_guardrail_data = {}
        rubicon_text_guardrail_data = {}
        moderation_text_guardrail_data = {}
        injection_text_guardrail_data = {}

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

            if result.status == django_rq.Status.SUCCESS:
                if job_name.startswith(self.FUNC_QUERY_TRANSLATION.__name__):
                    self.intermediate.translated_query_data[q] = result.result
                elif job_name.startswith(self.FUNC_IMAGE_GUARDRAIL.__name__):
                    image_guardrail_data = result.result
                    if result.result.get("image_guardrail_flag") == "Yes":
                        self.log_data.guardrail_detected = True
                elif job_name.startswith(self.FUNC_RUBICON_TEXT_GUARDRAIL.__name__):
                    rubicon_text_guardrail_data[q] = result.result
                    if result.result.get("decision") == "ATTACK":
                        self.log_data.guardrail_detected = True
                elif job_name.startswith(self.FUNC_MODERATION_TEXT_GUARDRAIL.__name__):
                    moderation_text_guardrail_data[q] = result.result
                    if result.result.get("flagged"):
                        self.log_data.guardrail_detected = True
                elif job_name.startswith(self.FUNC_INJECTION_TEXT_GUARDRAIL.__name__):
                    injection_text_guardrail_data[q] = result.result
                    if result.result.get("flagged"):
                        self.log_data.guardrail_detected = True
                elif job_name.startswith(self.FUNC_SESSION_TITLE_GENERATION.__name__):
                    session_title_dict = result.result
                    self.log_data.session_title = session_title_dict.get(
                        "session_title"
                    )
                elif job_name.startswith(self.FUNC_CS_INTENTION.__name__):
                    self.log_data.cs_data[q] = result.result
                else:
                    # Handle error
                    raise ValueError(f"Job not found: {job_name}")
            elif result.status == django_rq.Status.TIMEOUT:
                # Handle timeout
                timeout_message_data[job_name] = f"Timeout in {job_name}"
                self.log_data.no_cache_queries.add(q)
                self.log_data.timeout.append(
                    {"name": parts[0], "message": f"Timeout in {job_name}"}
                )

            else:
                # Handle error
                error_message_data[job_name] = f"Error in {job_name}: {result.error}"
                self.log_data.error_queries.add(q)
                self.log_data.error.append(
                    {
                        "name": parts[0],
                        "message": f"Error in {job_name}: {result.error}",
                    }
                )

        self.debug(
            timeout_message_data,
            error_message_data,
            image_guardrail_data,
            rubicon_text_guardrail_data,
            moderation_text_guardrail_data,
            injection_text_guardrail_data,
            cs_data=self.log_data.cs_data,
            translated_query_data=self.intermediate.translated_query_data,
            session_title=self.log_data.session_title,
            no_cache_queries=list(self.log_data.no_cache_queries),
            error_queries=list(self.log_data.error_queries),
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

        return (
            image_guardrail_data,
            rubicon_text_guardrail_data,
            moderation_text_guardrail_data,
            injection_text_guardrail_data,
        )

    @debug_sync_timer(ChatFlowSectionNames.SUPPLEMENTARY_INFO)
    def _supplementary_info(self):
        """
        image, video, related question 정보를 저장해서 프론트 엔드에서 노출할 수 있도록 장고 캐시에 저장(redis)
        """
        # Intelligence Data
        if self.intermediate.cached_data or self.intermediate.intelligence_data:
            # Extract intelligence data from cached
            intelligence_from_cached = {
                query: data["intelligence_data"]
                for query, data in self.intermediate.cached_data.items()
                if data.get("intelligence_data")
            }

            # Update with direct intelligence data to overwrite cached data if any differences
            self.log_data.intelligence.update(intelligence_from_cached)
            self.log_data.intelligence.update(self.intermediate.intelligence_data)

        # Sub Intelligence Data
        if self.intermediate.cached_data or self.intermediate.sub_intelligence_data:
            # Extract sub intelligence data from cached
            sub_intelligence_from_cached = {
                query: data["sub_intelligence_data"]
                for query, data in self.intermediate.cached_data.items()
                if data.get("sub_intelligence_data")
            }

            # Update with direct sub intelligence data to overwrite cached data if any differences
            self.log_data.sub_intelligence.update(sub_intelligence_from_cached)
            self.log_data.sub_intelligence.update(
                self.intermediate.sub_intelligence_data
            )

        # NER Data
        if self.intermediate.cached_data or self.intermediate.ner_data:
            # Extract NER data from cached
            ner_from_cached = {
                query: data["ner_data"]
                for query, data in self.intermediate.cached_data.items()
                if data.get("ner_data")
            }

            # Update with direct NER data to overwrite cached data if any differences
            self.log_data.ner.update(ner_from_cached)
            self.log_data.ner.update(self.intermediate.ner_data)

        # Complement Data
        if self.intermediate.cached_data or self.intermediate.complement_data:
            # Extract complement data from cached
            complement_from_cached = {
                query: data["complement_data"]
                for query, data in self.intermediate.cached_data.items()
                if data.get("complement_data")
            }

            # Update with direct complement data to overwrite cached data if any differences
            self.log_data.complement.update(complement_from_cached)
            self.log_data.complement.update(self.intermediate.complement_data)

        if self.intermediate.cached_data or self.orchestrator.query_analyzer_data:
            # Extract query analyzer data from cached
            query_analyzer_from_cached = {
                query: data["query_analyzer_data"]
                for query, data in self.intermediate.cached_data.items()
                if data.get("query_analyzer_data")
            }

            # Update with direct query analyzer data to overwrite cached data if any differences
            self.log_data.query_analyzer.update(query_analyzer_from_cached)
            self.log_data.query_analyzer.update(self.orchestrator.query_analyzer_data)

            if any(
                analysis.get("RAG_depth")
                == _21_orchestrator_query_analyzer.RAGDepth.NONE.value
                for analysis in self.log_data.query_analyzer.values()
            ):
                self.log_data.show_supplement = False

        # Product log
        for query, data in self.log_data.complement.items():
            # Skip grabbing the product log for certain sub_intelligences
            if self.log_data.sub_intelligence.get(query) in [
                sub_intelligences.PRODUCT_LINEUP_COMPARISON,
                sub_intelligences.PRODUCT_LINEUP_DESCRIPTION,
                sub_intelligences.PRODUCT_LINEUP_RECOMMENDATION,
                sub_intelligences.PRODUCT_INVENTORY_AND_RESTOCKING,
                sub_intelligences.CONSUMABLES_ACCESSORIES_RECOMMENDATION,
            ]:
                continue

            # If there is an extended info result, get the product log
            if data.get("extended_info_result"):
                self.log_data.product.extend(
                    utils.get_product_log(
                        query, data["extended_info_result"], self.input.country_code
                    )
                )

        # Check for each supplement type if they should be shown
        for query in self.orchestrator.rewritten_queries:
            # Product Card
            if utils.should_show_supplement_type(
                self.log_data.intelligence.get(query),
                self.log_data.sub_intelligence.get(query),
                _07_supplementary_info.SupplementaryTypes.PRODUCT_CARD.value,
            ):
                self.log_data.show_product_card = True

            # Media
            if utils.should_show_supplement_type(
                self.log_data.intelligence.get(query),
                self.log_data.sub_intelligence.get(query),
                _07_supplementary_info.SupplementaryTypes.MEDIA.value,
            ):
                self.log_data.show_media = True

            # Hyperlink
            if utils.should_show_supplement_type(
                self.log_data.intelligence.get(query),
                self.log_data.sub_intelligence.get(query),
                _07_supplementary_info.SupplementaryTypes.HYPERLINK.value,
            ):
                self.log_data.show_hyperlink = True

            # Related Query
            if utils.should_show_supplement_type(
                self.log_data.intelligence.get(query),
                self.log_data.sub_intelligence.get(query),
                _07_supplementary_info.SupplementaryTypes.RELATED_QUERY.value,
            ):
                self.log_data.show_related_query = True

        # Show media v2 and product card v2 if there is no extended info result in complement data
        if not any(
            data.get("extended_info_result")
            for data in self.log_data.complement.values()
        ):
            for query in self.orchestrator.rewritten_queries:
                # Media V2
                if utils.should_show_supplement_type_by_intelligence(
                    self.log_data.intelligence.get(query),
                    _07_supplementary_info.SupplementaryTypes.MEDIA.value,
                ):
                    self.log_data.show_media = True
                # Product Card V2
                if utils.should_show_supplement_type_by_intelligence(
                    self.log_data.intelligence.get(query),
                    _07_supplementary_info.SupplementaryTypes.PRODUCT_CARD.value,
                ):
                    self.log_data.show_product_card = True

        # If there is an error or timeout, do not show supplementary info
        if self.log_data.error or self.log_data.timeout:
            self.log_data.show_supplement = False

        if self.log_data.guardrail_detected:
            self.log_data.show_supplement = False

        if self.log_data.restricted:
            self.log_data.show_supplement = False

        # Store the data in cache
        message_flags = {
            MessageFlags.SHOW_SUPPLEMENT.value: self.log_data.show_supplement,
            MessageFlags.SHOW_MEDIA.value: self.log_data.show_media,
            MessageFlags.SHOW_PRODUCT_CARD.value: self.log_data.show_product_card,
            MessageFlags.SHOW_HYPERLINK.value: self.log_data.show_hyperlink,
            MessageFlags.SHOW_RELATED_QUERY.value: self.log_data.show_related_query,
        }
        cache.store(
            self._message_flags_cache_key,
            message_flags,
            self.session_expiry,
        )

        # For supplementary info background enqueue, only run if show supplement is True
        # if self.log_data.show_supplement:
        #     if self.log_data.show_media:
        #         django_rq.run_job_default(
        #             _08_media.media_store,
        #             (
        #                 self.object_id,
        #                 self.log_data.product,
        #                 self.input.country_code,
        #                 self.input.message_id,
        #                 self.session_expiry,
        #             ),
        #             {},
        #         )
        #     if self.log_data.show_related_query:
        #         django_rq.run_job_default(
        #             _09_related_query.related_question_store,
        #             (
        #                 self.object_id,
        #                 complement_data,
        #                 self.orchestrator.language,
        #                 self.input.message_id,
        #                 self.session_expiry,
        #             ),
        #             {},
        #         )
        #     if self.log_data.show_product_card:
        #         django_rq.run_job_default(
        #             _11_product_card.product_card_store,
        #             (
        #                 self.object_id,
        #                 self.log_data.product,
        #                 self.input.country_code,
        #                 self.input.channel,
        #                 self.log_data.site_cd,
        #                 self.input.message_id,
        #                 self.session_expiry,
        #             ),
        #             {},
        #         )

        self.debug(
            message_flags,
            product_card=self.log_data.product,
        )

    @debug_sync_timer(ChatFlowSectionNames.RESPONSE_LAYOUT)
    def _response_layout(self):
        """
        Grab the response layout for each query and store it in the intermediate data.
        Make sure to grab the data presence dictionary with cache in mind
        """
        # Combine the specification check from cache and from current run
        specification_data = {}
        if self.intermediate.cached_data or self.intermediate.specification_check_data:
            # Extract specification data from cached
            specification_from_cached = {
                query: data["specification_check_data"]
                for query, data in self.intermediate.cached_data.items()
                if data.get("specification_check_data")
            }

            # Update with direct specification data to overwrite cached data if any differences
            specification_data.update(specification_from_cached)
            specification_data.update(self.intermediate.specification_check_data)

        # Combine the high level specification check from cache and from current run
        high_level_specification_data = {}
        if (
            self.intermediate.cached_data
            or self.intermediate.high_level_specification_check_data
        ):
            # Extract high level specification data from cached
            high_level_specification_from_cached = {
                query: data["high_level_specification_check_data"]
                for query, data in self.intermediate.cached_data.items()
                if data.get("high_level_specification_check_data")
            }

            # Update with direct high level specification data to overwrite cached data if any differences
            high_level_specification_data.update(high_level_specification_from_cached)
            high_level_specification_data.update(
                self.intermediate.high_level_specification_check_data
            )

        response_layout_debug = {}
        for q in self.orchestrator.rewritten_queries:
            # Only process queries that have both intelligence and sub_intelligence
            if (
                q not in self.log_data.intelligence
                or q not in self.log_data.sub_intelligence
            ):
                continue

            # For managed_only queries, do not get response layout
            if self.log_data.complement.get(q, {}).get("managed_only", False):
                continue

            # Grab the data_presence_dict for the query
            data_presence_dict = {
                "has_extended_info": bool(
                    self.log_data.complement.get(q, {}).get("extended_info_result")
                ),
                "has_bundle_spec_info": bool(
                    specification_data.get(q, [])[4]
                    if len(specification_data.get(q, [])) == 5
                    else []
                ),
                "has_highlevel_spec_info": bool(
                    high_level_specification_data.get(q, {})
                ),
                "has_review_info": bool(
                    self.log_data.complement.get(q, {}).get("review_statistics")
                ),
            }
            response_layout_debug[q] = data_presence_dict
            response_layout = _81_response_layout.get_response_layout(
                self.log_data.intelligence.get(q, intelligences.GENERAL_INFORMATION),
                self.log_data.sub_intelligence.get(q),
                self.input.channel,
                self.input.country_code,
                data_presence_dict,
                self.simple,
            )
            if response_layout:
                self.intermediate.response_layout_data[q] = response_layout

        self.debug(
            response_layout_debug,
            response_layout_data=self.intermediate.response_layout_data,
        )

    @debug_sync_timer(ChatFlowSectionNames.MERGE_DATA)
    def _79_merge_data(
        self,
        image_guardrail_data,
        rubicon_text_guardrail_data,
        moderation_text_guardrail_data,
        injection_text_guardrail_data,
    ):
        # Merge Data
        MergeRag = _79_product_rag_merge_data.MergeRag(
            self.message_history_data.combined_query,
            self.input.channel,
            self.orchestrator.rewritten_queries,
            self.intermediate,
            self.orchestrator,
            self.orchestrator.rag_confirmation_status,
            self.orchestrator.unprocessed_queries,
            self.orchestrator.no_rag_queries,
            self.orchestrator.deep_rag_queries,
            self.log_data.no_cache_queries,
            self.log_data.error_queries,
            image_guardrail_data,
            rubicon_text_guardrail_data,
            moderation_text_guardrail_data,
            injection_text_guardrail_data,
            self.input.message_id,
            self.input.session_id,
            self.input.country_code,
            self.session_expiry,
            self.orchestrator.all_predefined_hit,
            self.orchestrator.all_cs_hit,
            True if self.input.channel == channels.GUARDRAIL_BYPASS else False,
        )
        (
            self.log_data.merged_data,
            self.log_data.response_path,
            self.log_data.to_cache_data,
            self.log_data.no_cache_queries,
            self.log_data.error_queries,
        ) = MergeRag.merge_rag()

        # Evaluation Data
        self.evaluation_data.informative_data = {
            k: v
            for k, v in self.log_data.merged_data.items()
            if k
            in [
                "predefined_data",
                "structured_data",
                "unstructured_data",
                "other_company_expression",
                "product_model_info",
                "product_common_spec_info",
                "product_spec_info",
                "set_product_spec_info",
                "high_level_product_spec_info",
                "product_price_info",
                "promotion_info",
                "review_statistics_info",
                "review_summary_info",
                "review_category_info",
                "corrected_query_list",
                "unknown_products",
                "response_layout_data",
            ]
        }

        # Update status if guardrail detected
        if self.log_data.guardrail_detected:
            self.status.status = 451

        # Save the ai blob path hyperlinks
        cache.store(
            CacheKey.hyperlink(self),
            self.log_data.merged_data["ai_search_meta_data"],
            self.session_expiry,
        )

        # Get the data used for response generation
        input_data_list = _82_response_prompts.input_prompt_data_mapping.get(
            self.log_data.response_path, {}
        ).get("prompt_inputs", [])
        response_input_data = {
            key: self.log_data.merged_data[key]
            for key in input_data_list
            if key in self.log_data.merged_data
        }

        # Get the user query
        self.log_data.user_query = utils.get_user_query(
            self.log_data.merged_data["translated_query"],
            self.orchestrator.rewritten_queries,
            self.orchestrator.cs_queries,
        )

        self.debug(
            response_path=self.log_data.response_path,
            response_input_data=response_input_data,
            user_query=self.log_data.user_query,
            no_cache_queries=list(self.log_data.no_cache_queries),
            error_queries=list(self.log_data.error_queries),
        )

    @debug_sync_timer(ChatFlowSectionNames.RESPONSE_HANDLER)
    def _response_handler(self):
        """
        Create the response handler that will generate the final response.
        """
        # If cache hit, check the response cache
        if (
            self.orchestrator.all_cache_hit
            and self.use_cache
            and self.log_data.response_path == response_types.INFORMATIVE_RESPONSE
        ):
            self._response_cache_key = CacheKey.response(self)
            cached_response = cache.get(self._response_cache_key)
            self.log_data.response_cache_hit = True
            self.log_data.full_response = cached_response

            self.response_handler = response_handler.ResponseHandler(
                self,
                self.stream,
                False,  # False for no error
                cached_response,  # Cached response
            )
            return  # Exit early as response is from cache

        # Otherwise, create the non-cached response handler
        self.response_handler = response_handler.ResponseHandler(
            self,
            self.stream,
            False,  # False for no error
            None,  # No cached response
        )
        return

    def _enqueue_post_response_supplementary(self):
        # Enqueue post response supplementary information if show supplement is True
        if self.log_data.show_supplement:
            # Product Extraction Supplementary Info (Product Card V2 & Media V2 & Related Query V2)
            django_rq.run_job_default(
                _07_supplementary_info.post_response_supplementary_info,
                (
                    self.object_id,
                    self.message_history_data.combined_query,
                    self.message_history_data.messages,
                    self.orchestrator.rewritten_queries,
                    self.log_data.full_response,
                    self.log_data.product,
                    self.log_data.intelligence,
                    self.log_data.sub_intelligence,
                    self.input.channel,
                    self.input.country_code,
                    self.log_data.site_cd,
                    self.user_data.user_info,
                    self.orchestrator.language,
                    self.input.message_id,
                    self.input.session_id,
                    self.session_expiry,
                ),
                {},
            )

    def _update_query_response_cache(self):
        """
        Update Django Cache with Query and Response Data
        """
        # Query Cache Update only for Informative Responses
        if self.log_data.response_path in [
            response_types.INFORMATIVE_RESPONSE,
        ]:
            for query, data in self.log_data.to_cache_data.items():
                if (
                    query in self.log_data.no_cache_queries
                    or query in self.log_data.query_cache
                    or all(
                        v == {}
                        for value in self.log_data.to_cache_data.values()
                        for v in value
                    )
                ):
                    continue

                cache_key_query = CacheKey.query_cache_key(query, self)
                if query in self.log_data.error_queries:
                    # Check if already in cache, if not store.
                    if not cache.exists(cache_key_query):
                        cache.store(
                            cache_key_query,
                            data,
                            60 * 60 * 1,  # 1 Hour for error queries
                        )
                        continue

                # Check if already in cache, if not store.
                if not cache.exists(cache_key_query):
                    cache.store(cache_key_query, data, self.cache_expiry)

            # Update response cache
            if (
                not self.log_data.no_cache_queries
                and not self.log_data.error_queries
                and self.log_data.full_response != ""
            ):
                # Check if already in cache, if not store.
                if not cache.exists(self._response_cache_key):
                    cache.store(
                        self._response_cache_key,
                        self.log_data.full_response,
                        self.cache_expiry,
                    )

    def _update_message_history(self):
        # Only update all the history information if guardrail is not detected
        if self.log_data.guardrail_detected:
            return

        # Make sure the response path was not Process Error or Process Timeout
        if self.log_data.response_path in [
            response_types.PROCESS_ERROR_RESPONSE,
            response_types.TIMEOUT_RESPONSE,
        ]:
            return

        # Message History Update
        user_content = []
        if self.input_files.image_files:
            process_images = []
            for image in self.input_files.image_files:
                image_dict = utils.process_image_file(image)
                process_images.append(image_dict)
            user_content.extend(process_images)

        user_content.append(
            {"type": "text", "text": self.message_history_data.combined_query}
        )

        self.log_data.updated_message_history = (
            self.message_history_data.messages.copy()
        )

        self.log_data.updated_message_history.append(
            {
                "role": "user",
                "content": user_content,
            }
        )

        # Update message history with assistant response
        self.log_data.updated_message_history.append(
            {
                "role": "assistant",
                "content": utils.remove_markdown_images(self.log_data.full_response),
            }
        )

        # Update django cache message history
        cache.update(
            CacheKey.message_history(self),
            self.log_data.updated_message_history,
            self.session_expiry,
        )

        # Update mentioned products for session cache
        # If there are no mentioned products, skip this step (product extraction will append)
        if self.log_data.product:
            self.message_history_data.mentioned_products.append(self.log_data.product)
            cache.update(
                CacheKey.mentioned_products(self),
                self.message_history_data.mentioned_products,
                self.session_expiry,
            )

        # Update the session title
        if self.log_data.session_title:
            cache.store(
                CacheKey.session_title(self),
                self.log_data.session_title,
                self.session_expiry,
            )

        # Clean up message history for debug
        for message in self.log_data.updated_message_history:
            if message.get("role") == "user" and isinstance(
                message.get("content"), list
            ):
                for item in message["content"]:
                    if (
                        isinstance(item, dict)
                        and item.get("type") == "image_url"
                        and "image_url" in item
                        and "url" in item.get("image_url", {})
                    ):
                        item["image_url"]["url"] = item["image_url"]["url"][:20]

        # AIBot Chat History Update
        if self.input.channel in [channels.AIBOT, channels.AIBOT2]:
            _13_chat_history.update_aibot_chat_history(
                self.input.user_id,
                self.input.session_id,
                self.message_history_data.combined_query,
                self.log_data.full_response,
                product_log=self.log_data.product,
            )

        self.debug(
            updated_message_history=self.log_data.updated_message_history,
            mentioned_products=self.message_history_data.mentioned_products,
            **{SECTION_NAME: ChatFlowSectionNames.MESSAGE_HISTORY_UPDATE},
        )

    def _update_debug_cache_and_log(self):
        # Debug Log Store
        django_rq.run_job_high(
            rubicon_log.create_debug_log,
            (
                self.object_id,
                self.input.channel,
                self.log_data.country_code,
                self.input.lng,
                self.input.user_id,
                self.input.department,
                self.log_data.subsidiary,
                self.input.session_id,
                self.input.message_id,
                self.message_history_data.combined_query,
                self.master_debug_messages,
                self.timing_logs,
            ),
            {},
        )

        cache.store(
            CacheKey.debug_content(self),
            self.master_debug_messages,
            self.session_expiry,
        )

        cache.store(
            CacheKey.evaluation(self),
            {
                "informative_data": self.evaluation_data.informative_data,
                "rewritten_queries": self.orchestrator.rewritten_queries,
                "query_analyzer_data": self.orchestrator.query_analyzer_data,
                "intelligence_data": self.intermediate.intelligence_data,
                "assistant_data": self.intermediate.assistant_data,
                "ner_data": self.intermediate.ner_data,
                "extended_info_data": next(
                    (
                        v.get("extended_info_result")
                        for v in self.intermediate.complement_data.values()
                        if "extended_info_result" in v
                    ),
                    [],
                ),
                "code_mapping_data": next(
                    (
                        v.get("code_mapping")
                        for v in self.intermediate.complement_data.values()
                        if "code_mapping" in v
                    ),
                    [],
                ),
                "timeout": self.log_data.timeout,
                "error": self.log_data.error,
                "guardrail_detected": self.log_data.guardrail_detected,
            },
            self.session_expiry,
        )

        cache.store(
            CacheKey.debug_timing_logs(self),
            self.timing_logs,
            self.session_expiry,
        )

    def _update_chat_log(self):
        # Grab intelligence and sub_intelligence
        intelligence, sub_intelligence = utils.get_log_intelligence(
            self.log_data.intelligence,
            self.log_data.sub_intelligence,
        )

        django_rq.run_job_high(
            rubicon_log.update_message_log,
            (
                self.object_id,
                self.input.message_id,
                {
                    "user_content": utils.get_user_content(
                        self.log_data.response_path,
                        self.log_data.user_query,
                        self.message_history_data.combined_query,
                    ),
                    "full_response": self.log_data.full_response,
                },
                {
                    "intelligence": intelligence,
                    "sub_intelligence": sub_intelligence,
                    "error": self.log_data.error != [],
                    "timeout": self.log_data.timeout != [],
                    "error_log": self.log_data.error,
                    "timeout_log": self.log_data.timeout,
                    "cache_hit_rate": (
                        round(
                            len(self.intermediate.cached_data)
                            / len(self.orchestrator.rewritten_queries),
                            4,
                        )
                        if self.orchestrator.rewritten_queries
                        else 0
                    ),  # Avoid division by zero
                    "cache_hit": len(self.intermediate.cached_data) > 0,
                    "response_cache_hit": self.log_data.response_cache_hit,
                    "guardrail": self.log_data.guardrail_detected,
                    "restricted": self.log_data.restricted,
                    "exception": self.log_data.exception_detected,
                    "language": self.orchestrator.language,
                    "response_path": self.log_data.response_path,
                    "user_logged_in": bool(self.user_data.user_info),
                },
                self.log_data.product,
                utils.parse_timing_logs(self.timing_logs),
                self.pipeline_elapsed_time,
                self.log_data.session_title,
                self.log_data.subsidiary,
                {"session_flags": cache.get(self._session_flags_cache_key)},
            ),
            {},
        )

    def run(self):
        # Initialize data
        image_guardrail_data = {}
        rubicon_text_guardrail_data = {}

        # Initialize session
        self._initialize_session()

        # Debugging Begin
        self._00_debug_input_arguments()

        # Variable setup
        # - Read message history from Django cache
        # - Set cache items
        # - categorize image and audio files from files
        self._00_variable_setup()

        # Multiple Input Check Only for Channel Sprinklr
        if self.input.channel in [channels.SPRINKLR]:
            self._multi_input_check()

        # Mask Sensitive Info
        self._00_mask_pii()

        # Checking Original Query
        self._00_check_original_query()

        # Parallel(enqueue): Image Guardrail + Session Title if first message
        side_job_mapping = self._enqueue_image_guardrail_session_title()

        # Parallel(blocking): Rewrite + Loading message generation + Language Detection + Correction Determination
        self._parallel_rewrite_loading_message_lang_detect_correction_determination(
            "gpt-4.1",
        )

        # If correction determination deems it necessary,
        # run the correction module
        if self.orchestrator.correct_rewritten_queries:
            self._rewrite_correction()

        # First message check
        self._message_cancel_check()

        # Text Cleanup + Embedding
        self._embedding()

        # Check Predefined and Cache
        self._check_predefined_query_cache()

        # Enqueue Query Rewrite Translation
        side_job_mapping = self._enqueue_query_rewrite_translation(side_job_mapping)

        try:
            # If there are any non-cached queries, continue the pipeline
            if self.orchestrator.unprocessed_queries:
                # Parallel: Query Analyzer + Intelligence + NER + Context Determination
                self._parallel_query_analyzer_intelligence_ner_context_determination()

                # Correction Module
                self._correction()

                # Enqueue CS Intention + Text Guardrail
                side_job_mapping = self._enqueue_cs_intention_text_guardrail(
                    side_job_mapping
                )

                # Orchestrator Rag + Product Rag
                # Run only if the gpt search flag is False
                if not self.orchestrator.orch_use_search_gpt_flag:
                    # Second message check
                    self._message_cancel_check()

                    # If there are any deep queries continue the pipeline
                    if self.orchestrator.deep_rag_queries:
                        # Standard NER + Assistant + Sub Intelligence
                        self._parallel_standard_ner_assistant_sub_intelligence()

                    # Third message check
                    self._message_cancel_check()

                    # Rag Confirmation
                    if (
                        self.orchestrator.deep_rag_queries
                        or self.orchestrator.no_rag_queries
                    ):
                        self._rag_confirmation()

                    # If there are any deep queries continue the pipeline
                    if self.orchestrator.deep_rag_queries:
                        # RAG Distributer
                        (
                            structured_distribution_data,
                            complement_distribution_data,
                        ) = self._40_rag_distributer()

                        # Parallel: Structured + Unstructured
                        self._parallel_50_structured_60_complement(
                            structured_distribution_data,
                            complement_distribution_data,
                        )

                # Web Search + AI Search + Specification Check + GPT Web Search
                # Run only if the RAG confirmation status is not re-asking required
                # and not all queries are cs intention hits
                if (
                    self.orchestrator.rag_confirmation_status
                    != _39_rag_confirmation.RagConfirmationStatus.RE_ASKING_REQUIRED.value
                    and not self.orchestrator.all_cs_hit
                ):
                    self._7x_web_search_ai_search_specification_check_high_level_specification_check()

                # Fourth message check
                self._message_cancel_check()

            # No unprocessed queries, all either cached or predefined
            else:
                # All cache hit
                if (
                    self.intermediate.cached_data
                    and not self.intermediate.predefined_data
                ):
                    self.orchestrator.all_cache_hit = True
                # All predefined data
                elif (
                    self.intermediate.predefined_data
                    and not self.intermediate.cached_data
                ):
                    self.orchestrator.all_predefined_hit = True
                # Mixed cache hit and predefined data ignore
                else:
                    pass

        finally:
            # Background Jobs
            (
                image_guardrail_data,
                rubicon_text_guardrail_data,
                moderation_text_guardrail_data,
                injection_text_guardrail_data,
            ) = self._background_jobs(side_job_mapping)

            # Grab the supplementary information
            self._supplementary_info()

            # Response layout
            if (
                self.orchestrator.rewritten_queries
                and not self.orchestrator.orch_use_search_gpt_flag
                and not self.orchestrator.all_cs_hit
            ):
                # Grab the response layouts
                self._response_layout()

        # Data Processing
        self._79_merge_data(
            image_guardrail_data,
            rubicon_text_guardrail_data,
            moderation_text_guardrail_data,
            injection_text_guardrail_data,
        )

        # Update show media data depending on the response path
        cached_message_flags: dict = cache.get(self._message_flags_cache_key, {})
        if self.log_data.response_path in [
            response_types.TEXT_GUARDRAIL_RESPONSE,
            response_types.IMAGE_GUARDRAIL_RESPONSE,
            response_types.GENERAL_RESPONSE,
            response_types.REASKING_RESPONSE,
            response_types.AI_SUBSCRIPTION_RESPONSE,
        ]:
            cache.store(
                self._message_flags_cache_key,
                cached_message_flags.update(
                    {
                        MessageFlags.SHOW_SUPPLEMENT.value: False,
                    }
                ),
                self.session_expiry,
            )

        # Helper function to determine if all product recommendations
        is_all_product_recommendation = all(
            v == intelligences.PRODUCT_RECOMMENDATION
            for v in self.intermediate.intelligence_data.values()
        )

        if (
            self.log_data.response_path == response_types.INFORMATIVE_RESPONSE
            and is_all_product_recommendation
        ):
            no_extended_info = all(
                not bool(
                    self.intermediate.complement_data.get(query, {}).get(
                        "extended_info_result", {}
                    )
                )
                for query in self.orchestrator.rewritten_queries
            )
            if no_extended_info:
                self.gpt_model_name = "gpt-4.1"
        elif self.log_data.response_path == response_types.INFORMATIVE_RESPONSE and any(
            sub_intelligence == sub_intelligences.PRODUCT_LINEUP_COMPARISON
            for sub_intelligence in self.intermediate.sub_intelligence_data.values()
        ):
            # If the response path is informative and the sub_intelligence is product lineup comparison, use gpt-4.1
            self.gpt_model_name = "gpt-4.1"

        # Final message check
        self._message_cancel_check()

        # Create the response handler
        self._response_handler()

    def enqueue_chat_flow(self):
        """
        Run the Rubicon Chat Completion flow and handle exceptions
        """
        try:
            self.run()

        except (
            EmptyStreamData,
            EmptyOriginalQuery,
            PreEmbargoQueryException,
            ProcessTimeout,
            ProcessError,
            RedirectRequestException,
            InformationRestrictedException,
            InvalidOriginalQuery,
            MultipleInputException,
            InvalidCodeMapping,
            InvalidStore,
            RewriteCorrectionFailureException,
            Exception,
        ) as e:
            print(f"{type(e).__name__} in Rubicon Chat: {e}")
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
                MultipleInputException,
                InvalidCodeMapping,
                InvalidStore,
                RewriteCorrectionFailureException,
            ]:
                context_data = {
                    "API": "Chat Completion",
                    "Channel": self.input.channel,
                    "Country Code": self.input.country_code,
                    "Object ID": str(self.object_id),
                    "User ID": self.input.user_id,
                    "Session ID": self.input.session_id,
                    "Message ID": self.input.message_id,
                    "Original Query": self.message_history_data.combined_query,
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

            # Map error types to response paths
            self.log_data.response_path = {
                EmptyStreamData: response_types.EMPTY_STREAM_DATA_RESPONSE,
                EmptyOriginalQuery: response_types.EMPTY_ORIGINAL_QUERY_RESPONSE,
                PreEmbargoQueryException: response_types.PRE_EMBARGO_QUERY_RESPONSE,
                ProcessTimeout: response_types.TIMEOUT_RESPONSE,
                ProcessError: response_types.PROCESS_ERROR_RESPONSE,
                RedirectRequestException: response_types.REDIRECT_REQUEST_RESPONSE,
                InformationRestrictedException: response_types.INFORMATION_RESTRICTED_RESPONSE,
                InvalidOriginalQuery: response_types.TEXT_GUARDRAIL_RESPONSE,
                InvalidCodeMapping: response_types.CODE_MAPPING_ERROR_RESPONSE,
                InvalidStore: response_types.STORE_MAPPING_ERROR_RESPONSE,
                RewriteCorrectionFailureException: response_types.REWRITE_CORRECTION_FAILURE_RESPONSE,
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

            # Create the error response handler
            self.response_handler = response_handler.ResponseHandler(
                self, self.stream, True, None
            )

            # Update the message flags cache
            cached_message_flags: dict = cache.get(self._message_flags_cache_key, {})
            cache.store(
                self._message_flags_cache_key,
                cached_message_flags.update(
                    {MessageFlags.SHOW_SUPPLEMENT.value: False}
                ),
                self.session_expiry,
            )

    def get_non_stream_response(self):
        """
        Get the non-stream response from the Rubicon Chat Completion flow
        """
        # Retrieve the response
        response_result = self.response_handler.build_response()

        # Enqueue the post response supplementary information
        self._enqueue_post_response_supplementary()

        # Update message history and cache
        self._update_query_response_cache()
        self._update_message_history()

        # Update the chat log and debug log
        self._update_chat_log()
        self._update_debug_cache_and_log()

        # Return the response result
        return response_result

    async def get_stream_response(self):
        """
        Get the stream response from the Rubicon Chat Completion flow
        """
        # Retrieve the response
        for chunk in self.response_handler.stream_response():
            yield chunk
            await asyncio.sleep(0.0001)  # Force yield to event loop

        # Enqueue the post response supplementary information
        self._enqueue_post_response_supplementary()

        # Update message history and cache
        self._update_query_response_cache()
        self._update_message_history()

        # Update the chat log and debug log
        self._update_chat_log()
        self._update_debug_cache_and_log()
