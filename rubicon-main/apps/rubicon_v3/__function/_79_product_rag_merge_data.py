import sys

sys.path.append("/www/alpha/")

import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "alpha.settings")
django.setup()

import pandas as pd

from collections import OrderedDict, defaultdict
from dataclasses import fields
from typing import TYPE_CHECKING, List

from apps.rubicon_v3.__function import __embedding_rerank
from apps.rubicon_v3.__function._39_rag_confirmation import RagConfirmationStatus
from apps.rubicon_v3.__function.definitions import (
    response_types,
    intelligences,
    sub_intelligences,
    ner_fields,
    channels,
)
from apps.rubicon_v3.__function.ai_search.ai_search_index_definitions import (
    AiSearchIndexDefinitions,
)
from apps.rubicon_v3.__function.__prompts.guardrails.malicious_answer_prompt_by_type_dict import (
    get_guardrail_response_instructions,
)
from apps.rubicon_v3.__function.__embedding_rerank import rerank_db_results
from apps.rubicon_v3.__function.__django_cache import (
    SessionFlags,
    DjangoCacheClient,
    CacheKey,
)

if TYPE_CHECKING:
    from apps.rubicon_v3.__function._00_rubicon import RubiconChatFlow

from apps.rubicon_v3.__function.ai_search import parse_card_benefits, uk_benefits
from apps.rubicon_v3.__function.__utils import run_retrieval_evaluation_parallel

cache = DjangoCacheClient()


class MergeRag:
    def __init__(
        self,
        original_query: str,
        channel: str,
        rewritten_queries: List[str],
        data_packed: "RubiconChatFlow.IntermediateData",
        orchestrator_data_packed: "RubiconChatFlow.OrchestratorData",
        rag_confirmation_status: str,
        unprocessed_queries: list,
        no_rag_queries: list,
        deep_rag_queries: list,
        no_cache_queries: set,
        error_queries: set,
        image_guardrail: dict,
        rubicon_text_guardrail: dict,
        moderation_text_guardrail: dict,
        injection_text_guardrail: dict,
        message_id: str,
        session_id: str,
        country_code: str,
        session_expiry: int,
        all_predefined: bool,
        all_cs: bool,
        guardrail_bypass: bool = False,
    ):
        self.original_query = original_query
        self.channel = channel
        self.rewritten_queries: List[str] = rewritten_queries
        self.data_packed: "RubiconChatFlow.IntermediateData" = data_packed
        self.orchestrator_data_packed: "RubiconChatFlow.OrchestratorData" = (
            orchestrator_data_packed
        )
        self.rag_confirmation_status: str = rag_confirmation_status
        self.unprocessed_queries: list = unprocessed_queries
        self.no_rag_queries: list = no_rag_queries
        self.deep_rag_queries: list = deep_rag_queries
        self.no_cache_queries: set = no_cache_queries
        self.error_queries: set = error_queries
        self.image_guardrail: dict = image_guardrail
        self.rubicon_text_guardrail: dict = rubicon_text_guardrail
        self.moderation_text_guardrail: dict = moderation_text_guardrail
        self.injection_text_guardrail: dict = injection_text_guardrail
        self.message_id: str = message_id
        self.country_code: str = country_code
        self.session_expiry: int = session_expiry

        self.guardrail_type = None

        self.cached = data_packed.cached_data
        self.predefined = data_packed.predefined_data
        self.ner = data_packed.ner_data
        self.assistant = data_packed.assistant_data
        self.intelligence = data_packed.intelligence_data
        self.sub_intelligence = data_packed.sub_intelligence_data
        self.structured = data_packed.structured_data
        self.complement = data_packed.complement_data
        self.web_search = data_packed.web_search_data
        self.ai_search = data_packed.ai_search_data
        self.specification_check = data_packed.specification_check_data
        self.high_level_specification_check = (
            data_packed.high_level_specification_check_data
        )
        self.high_level_price_check = data_packed.high_level_price_check_data
        self.response_layout = data_packed.response_layout_data
        self.translated_query = data_packed.translated_query_data

        self.query_analyzer_data = orchestrator_data_packed.query_analyzer_data
        self.orch_use_search_gpt_flag = (
            orchestrator_data_packed.orch_use_search_gpt_flag
        )

        self.predefined_sample_response_set = set()
        self.predefined_reference_data_set = set()
        self.managed_response_data_list = []
        self.exception_response_data_list = []
        self.about_operator_flag_list = []
        self.unstructured_data_list = []
        self.structured_data_list = []
        self.other_company_expression = []
        self.product_model_info = []
        self.product_common_spec_info = []
        self.product_spec_info = []
        self.set_product_spec_info = []
        self.high_level_product_spec_info = []
        self.high_level_price_info = []
        self.product_price_info = []
        self.promotion_info = []
        self.review_statistics_info = []
        self.review_summary_info = []
        self.review_category_info = []
        self.add_on_info = []

        self.ai_search_meta_data = []

        self.guardrail_bypass = guardrail_bypass
        self.all_predefined = all_predefined
        self.all_cs = all_cs

        self.invalid_model_name_flag = False

        self.response_path = None
        self.to_cache_data = {}

        self._session_flags_cache_key = CacheKey.session_flags(session_id)
        self.cached_session_flags = cache.get(
            self._session_flags_cache_key,
            {
                SessionFlags.TURNS_SINCE_RE_ASKED.value: 5,
                SessionFlags.STORE_RE_ASKED.value: False,
            },  # Default values
        )

        self.early_return = False

    def return_data(self):
        return (
            {
                "sample_response_data": list(self.predefined_sample_response_set),
                "reference_data": list(self.predefined_reference_data_set),
                "managed_data": self.managed_response_data_list,
                "exception_response_data": self.exception_response_data_list,
                "out_of_range_flag": self.about_operator_flag_list,
                "structured_relevant_data": self.structured_data_list,
                "unstructured_relevant_data": self.unstructured_data_list,
                "other_company_expression": self.other_company_expression,
                "product_model_info": self.product_model_info,
                "product_common_spec_info": self.product_common_spec_info,
                "product_spec_info": self.product_spec_info,
                "set_product_spec_info": self.set_product_spec_info,
                "high_level_product_spec_info": self.high_level_product_spec_info,
                "product_lineup_price_info": self.high_level_price_info,
                "product_price_info": self.product_price_info,
                "promotion_info": self.promotion_info,
                "review_statistics_info": self.review_statistics_info,
                "review_summary_info": self.review_summary_info,
                "review_category_info": self.review_category_info,
                "guardrail_response_instructions": self.guardrail_type,
                "add_on_info": self.add_on_info,
                "response_format": self.response_layout,
                "ai_search_meta_data": self.ai_search_meta_data,
                "intelligence_info": list(self.intelligence.values()),
                "sub_intelligence_info": list(self.sub_intelligence.values()),
                "translated_query": self.translated_query,
            },
            self.response_path,
            self.to_cache_data,
            self.no_cache_queries,
            self.error_queries,
        )

    def update_early_return(self, early_return: bool):
        self.early_return = early_return
        return self

    def validate_inputs(self) -> "MergeRag":
        if (
            self.cached == {}
            and self.predefined == {}
            and self.ner == {}
            and self.assistant == {}
            and self.intelligence == {}
            and self.sub_intelligence == {}
            and self.structured == {}
            and self.complement == {}
            and self.web_search == {}
            and self.ai_search == {}
            and self.specification_check == {}
            and self.high_level_specification_check == {}
            and self.high_level_price_check == {}
            and self.response_layout == {}
            and self.query_analyzer_data == {}
            and self.rag_confirmation_status == "success"
        ):
            raise ValueError(f"No data found in merge rag")

        return self

    def check_early_response_exit(self) -> "MergeRag":
        # Check if guardrail bypass is enabled
        if self.guardrail_bypass:
            return self

        # Check if any of the queries are flagged by the rubicon text guardrail
        for value in self.rubicon_text_guardrail.values():
            if value.get("decision") and value.get("decision").lower() == "attack":
                # Set response path to text guardrail response
                self.response_path = response_types.TEXT_GUARDRAIL_RESPONSE
                # Get the appropriate guardrail response instructions
                category = value.get("category")
                self.guardrail_type = get_guardrail_response_instructions(
                    category, self.country_code, self.channel
                )
                return self.update_early_return(True)

        # Check if any of the queries are flagged by the moderation text guardrail
        for value in self.moderation_text_guardrail.values():
            if value.get("flagged"):
                # Set response path to text guardrail response
                self.response_path = response_types.TEXT_GUARDRAIL_RESPONSE
                # Get the appropriate guardrail response instructions
                self.guardrail_type = get_guardrail_response_instructions(
                    "S6", self.country_code, self.channel
                )
                return self.update_early_return(True)

        # Check if any of the queries are flagged by the injection text guardrail
        for value in self.injection_text_guardrail.values():
            if value.get("flagged"):
                # Set response path to text guardrail response
                self.response_path = response_types.TEXT_GUARDRAIL_RESPONSE
                # Get the appropriate guardrail response instructions
                self.guardrail_type = get_guardrail_response_instructions(
                    "S2", self.country_code, self.channel
                )
                return self.update_early_return(True)

        # Check if any of the queries are flagged by the image guardrail
        if (
            self.image_guardrail.get("image_guardrail_flag")
            and self.image_guardrail.get("image_guardrail_flag").lower() == "yes"
        ):
            self.response_path = response_types.IMAGE_GUARDRAIL_RESPONSE
            return self.update_early_return(True)

        # Check if all predefined flag is True
        if self.all_predefined:
            for predefined_item in self.predefined.values():
                # If predefined item has a sample response, add it to the list
                if predefined_item.get("sample_response"):
                    self.predefined_sample_response_set.add(
                        predefined_item["sample_response"]
                    )
                # If predefined item has reference data, add it to the list
                if predefined_item.get("reference_data"):
                    self.predefined_reference_data_set.update(
                        predefined_item["reference_data"]
                    )
            self.response_path = response_types.PREDEFINED_RESPONSE
            return self.update_early_return(True)

        # Check if all cs flag is True
        if self.all_cs:
            self.response_path = response_types.CS_RESPONSE
            return self.update_early_return(True)

        # Check Re Ask Distributer Status
        if (
            self.rag_confirmation_status
            == RagConfirmationStatus.RE_ASKING_REQUIRED.value
        ):
            # Update the session flags for re-asking
            self.cached_session_flags[SessionFlags.TURNS_SINCE_RE_ASKED.value] = 0
            self.cached_session_flags[SessionFlags.STORE_RE_ASKED.value] = False

            # Update the session flags cache
            cache.store(
                self._session_flags_cache_key,
                self.cached_session_flags,
                self.session_expiry,
            )
            self.response_path = response_types.REASKING_RESPONSE
            return self.update_early_return(True)

        # Check if any of the queries are ai subscription responses
        if self.rag_confirmation_status == RagConfirmationStatus.AI_SUBSCRIPTION.value:
            self.response_path = response_types.AI_SUBSCRIPTION_RESPONSE
            return self.update_early_return(True)

        # Check if any of structured data requires re-asking
        if any(
            data.get("re_asking") for data in self.structured.values()
        ) and not self.cached_session_flags.get(SessionFlags.STORE_RE_ASKED.value):
            # Update the session flags for re-asking
            self.cached_session_flags[SessionFlags.TURNS_SINCE_RE_ASKED.value] += 1
            self.cached_session_flags[SessionFlags.STORE_RE_ASKED.value] = True

            # Update the session flags cache
            cache.store(
                self._session_flags_cache_key,
                self.cached_session_flags,
                self.session_expiry,
            )
            self.response_path = response_types.REASKING_RESPONSE
            return self.update_early_return(True)

        # If no early return conditions are met, update the session flags
        self.cached_session_flags[SessionFlags.TURNS_SINCE_RE_ASKED.value] += 1
        self.cached_session_flags[SessionFlags.STORE_RE_ASKED.value] = False
        cache.store(
            self._session_flags_cache_key,
            self.cached_session_flags,
            self.session_expiry,
        )

        return self

    def data_validation_and_cleaning(self) -> "MergeRag":
        if self.early_return:
            return self

        # Add validation if needed

        return self

    def get_to_cache_data(self) -> "MergeRag":
        if self.early_return:
            return self

        for query in self.rewritten_queries:
            if query not in self.no_cache_queries:
                self.to_cache_data[query] = {
                    "ner_data": self.ner.get(query),
                    "assistant_data": self.assistant.get(query),
                    "intelligence_data": self.intelligence.get(query),
                    "sub_intelligence_data": self.sub_intelligence.get(query),
                    "structured_data": self.structured.get(query),
                    "complement_data": self.complement.get(query),
                    "web_search_data": self.web_search.get(query),
                    "ai_search_data": self.ai_search.get(query),
                    "specification_check_data": self.specification_check.get(query),
                    "high_level_specification_check_data": self.high_level_specification_check.get(
                        query
                    ),
                    "high_level_price_check_data": self.high_level_price_check.get(
                        query
                    ),
                    "query_analyzer_data": self.query_analyzer_data.get(query),
                    "translated_query_data": self.translated_query.get(query),
                }

        return self

    def merge_cached_data(self) -> "MergeRag":
        # Map cache item names to their corresponding instance attributes
        attribute_map = {
            "ner_data": self.ner,
            "assistant_data": self.assistant,
            "intelligence_data": self.intelligence,
            "sub_intelligence_data": self.sub_intelligence,
            "structured_data": self.structured,
            "complement_data": self.complement,
            "web_search_data": self.web_search,
            "ai_search_data": self.ai_search,
            "specification_check_data": self.specification_check,
            "high_level_specification_check_data": self.high_level_specification_check,
            "high_level_price_check_data": self.high_level_price_check,
            "query_analyzer_data": self.query_analyzer_data,
            "translated_query_data": self.translated_query,
        }

        cache_items = [f.name for f in fields(self.data_packed)] + [
            "query_analyzer_data",
        ]

        for key, value in self.cached.items():
            for cache_item in cache_items:
                if value.get(cache_item):
                    target_dict = attribute_map.get(cache_item)
                    if isinstance(target_dict, dict) and key not in target_dict:
                        target_dict[key] = value.get(cache_item)

        return self

    def modify_data_dicts(self) -> "MergeRag":
        if self.early_return:
            return self

        # Predefined response data
        for query, predefined_item in self.predefined.items():
            # If predefined item has a sample response, add it to the list
            if predefined_item.get("sample_response"):
                self.predefined_sample_response_set.add(
                    predefined_item["sample_response"]
                )
            # If predefined item has reference data, add it to the list
            if predefined_item.get("reference_data"):
                self.predefined_reference_data_set.update(
                    predefined_item["reference_data"]
                )

        # Grab high level specification check data
        for key, value in self.high_level_specification_check.items():
            self.high_level_product_spec_info.append(value)

        # Grab high level price check data
        for key, value in self.high_level_price_check.items():
            self.high_level_price_info.append(value)

        # Grab additional data from structured and unstructured
        for query, value in self.specification_check.items():
            # If high level product specification check data is present, do not use specification data
            if (
                query not in self.high_level_specification_check
                or not self.high_level_specification_check[query]
            ):
                if value and len(value) == 5:
                    self.other_company_expression.extend(value[0])
                    if self.sub_intelligence.get(query) not in [
                        sub_intelligences.PRICE_EXPLANATION,
                        sub_intelligences.PAYMENT_BENEFIT_EXPLANATION,
                        sub_intelligences.EVENT_PROMOTION,
                        sub_intelligences.BUNDLE_DISCOUNT,
                        sub_intelligences.PRODUCT_LINEUP_COMPARISON,
                        sub_intelligences.PRODUCT_LINEUP_DESCRIPTION,
                        sub_intelligences.PRODUCT_LINEUP_RECOMMENDATION,
                    ]:
                        self.product_model_info.extend(value[1])

                    if self.sub_intelligence.get(query) not in [
                        sub_intelligences.PRODUCT_LINEUP_COMPARISON,
                        sub_intelligences.PRODUCT_LINEUP_DESCRIPTION,
                        sub_intelligences.PRODUCT_LINEUP_RECOMMENDATION,
                        sub_intelligences.SMARTTHINGS_EXPLANATION,
                    ]:
                        self.product_common_spec_info.extend(value[2])
                        self.product_spec_info.extend(value[3])

                    if self.intelligence.get(
                        query
                    ) == intelligences.PRODUCT_DESCRIPTION and self.sub_intelligence.get(
                        query
                    ) not in [
                        sub_intelligences.PRODUCT_LINEUP_COMPARISON,
                        sub_intelligences.PRODUCT_LINEUP_DESCRIPTION,
                        sub_intelligences.PRODUCT_LINEUP_RECOMMENDATION,
                    ]:
                        self.set_product_spec_info.extend(value[4])

                else:
                    print("Specification check data not in correct format")

        # clean data dictionaries
        for query, value in self.structured.items():
            if value.get("structured_rag"):
                self.structured_data_list.append(value["structured_rag"])

        # Complement Data Processing
        managed_response_data_set = set()
        exception_response_data_set = set()
        about_operator_flag_set = set()
        for query, value in self.complement.items():
            # Managed response
            # Manged response db values
            for managed_response in value.get("managed_response", []):
                for managed_item in managed_response.get("managed_response", []):
                    if managed_item.startswith(
                        "!!Important!!"
                    ) and self.sub_intelligence.get(query) not in [
                        sub_intelligences.PRODUCT_SPECIFICATION,
                        sub_intelligences.SAMSUNG_COMPARISON,
                        sub_intelligences.CONSUMABLES_ACCESSORIES_RECOMMENDATION,
                        sub_intelligences.SAMSUNG_STORE_INFORMATION,
                        sub_intelligences.PRICE_EXPLANATION,
                        sub_intelligences.PAYMENT_BENEFIT_EXPLANATION,
                        sub_intelligences.EVENT_PROMOTION,
                        sub_intelligences.BUNDLE_DISCOUNT,
                        sub_intelligences.PAYMENT_BENEFIT,
                        sub_intelligences.PAYMENT_METHOD_INFORMATION,
                        sub_intelligences.PRODUCT_INVENTORY_AND_RESTOCKING,
                        sub_intelligences.BUYING_POLICY,
                        sub_intelligences.EXCHANGE_RETURN_POLICY,
                        sub_intelligences.DELIVERY_POLICY,
                        sub_intelligences.ORDER_DELIVERY_TRACKING,
                        sub_intelligences.INSTALLATION_CONDITIONS_AND_STANDARDS,
                        sub_intelligences.IN_STORE_GUIDE,
                        sub_intelligences.SMARTTHINGS_EXPLANATION,
                    ]:
                        managed_response_data_set.add(managed_item)

            # Complement code managed response values
            for exception_response in value.get("exception_response_data", []):
                for exception_item in exception_response.get("managed_response", []):
                    if self.channel in [
                        channels.SMARTTHINGS
                    ] and self.sub_intelligence.get(query) in [
                        sub_intelligences.SMARTTHINGS_EXPLANATION
                    ]:
                        continue  # Skip SmartThings explanation for exception response
                    exception_response_data_set.add(exception_item)

            if value.get("about_operator_flag_list"):
                for about_operator_flag in value["about_operator_flag_list"]:
                    for key in about_operator_flag.keys():
                        about_operator_flag_set.add(
                            f"삼성전자에서 출시된 제품 중에는 {key} 제품은 없다고 언급한 뒤 $Product Model Info$에 있는 제품을 대신 추천/설명합니다"
                        )

            if self.sub_intelligence.get(query) in [
                sub_intelligences.PRICE_EXPLANATION,
                sub_intelligences.PAYMENT_BENEFIT_EXPLANATION,
                sub_intelligences.EVENT_PROMOTION,
                sub_intelligences.BUNDLE_DISCOUNT,
                sub_intelligences.PRODUCT_INVENTORY_AND_RESTOCKING,
            ]:
                if value.get("price_table"):
                    self.product_price_info.append(value.get("price_table")[0])
                if value.get("promotion_table"):
                    self.promotion_info.extend(value.get("promotion_table"))
            # Separate condition for product recommendation with price NER
            elif self.intelligence.get(query) in [
                intelligences.PRODUCT_RECOMMENDATION
            ] and any(
                ner_item.get("field") in [ner_fields.PRODUCT_PRICE]
                for ner_item in self.ner.get(query)
            ):
                if value.get("price_table"):
                    self.product_price_info.append(value.get("price_table")[0])
                # Do not add promotion info for product recommendation with price NER

            if value.get("review_statistics") and self.sub_intelligence.get(
                query
            ) not in [
                sub_intelligences.PRODUCT_LINEUP_COMPARISON,
                sub_intelligences.PRODUCT_LINEUP_DESCRIPTION,
                sub_intelligences.PRODUCT_LINEUP_RECOMMENDATION,
            ]:
                self.review_statistics_info.append(value.get("review_statistics"))
            if value.get("review_summary") and self.sub_intelligence.get(query) not in [
                sub_intelligences.PRODUCT_LINEUP_COMPARISON,
                sub_intelligences.PRODUCT_LINEUP_DESCRIPTION,
                sub_intelligences.PRODUCT_LINEUP_RECOMMENDATION,
            ]:
                self.review_summary_info.append(value.get("review_summary"))
            if value.get("review_category") and self.sub_intelligence.get(
                query
            ) not in [
                sub_intelligences.PRODUCT_LINEUP_COMPARISON,
                sub_intelligences.PRODUCT_LINEUP_DESCRIPTION,
                sub_intelligences.PRODUCT_LINEUP_RECOMMENDATION,
            ]:
                self.review_category_info.append(value.get("review_category"))
            if value.get("add_on_table"):
                self.add_on_info.extend(value.get("add_on_table", []))

            # Confirm if there was an invalid model name error
            if value.get("code_mapping_error_list") and isinstance(
                value["code_mapping_error_list"], list
            ):
                if any(
                    error["error_type"] == "invalid model name"
                    for error in value["code_mapping_error_list"]
                    if "error_type" in error
                ):
                    self.invalid_model_name_flag = True

        # Convert managed and exception response to a list
        self.managed_response_data_list = list(managed_response_data_set)
        self.exception_response_data_list = list(exception_response_data_set)
        self.about_operator_flag_list = list(about_operator_flag_set)

        priority_data_ls = []
        priority_title_ls = []
        combined_unstructured_data_list = []
        combined_unstructured_title_list = []
        always_use_in_response_data_ls = []
        ai_search_blob_path_set = []

        # AI search response
        # 설치 질의에서 설치 인덱스 문서 상위 노출
        for query, value in self.ai_search.items():
            for search_item in value:
                if self._is_priority_unstructured_doc(
                    self.intelligence.get(query), search_item
                ):
                    if search_item["text_data"] not in priority_data_ls:
                        title = search_item.get("title") or ""
                        text = search_item.get("text_data") or ""
                        priority_data_ls.append(text)
                        priority_title_ls.append(title)
                        if search_item.get("blob_path") != "":
                            self.ai_search_meta_data.append(
                                {
                                    "hyperlink": search_item.get("blob_path", ""),
                                    "label": "priority",  # TODO: label should be dynamic
                                    "type": "",  # TODO: type should be dynamic
                                    "description": search_item.get(
                                        "title", ""
                                    ),  # TODO: description should be dynamic
                                }
                            )

            # 카드 혜택 정보 추가
            if (
                self.intelligence.get(query) == intelligences.BUY_INFORMATION
                and self.sub_intelligence.get(query)
                == sub_intelligences.PAYMENT_BENEFIT
            ):
                if self.country_code == "KR":
                    always_use_in_response_data_ls.append(
                        "KR card benefits information: "
                        + parse_card_benefits.parse_card_info()
                    )
                else:
                    chunk_list = uk_benefits.benefits_chunk_list()

                    for c in chunk_list:
                        combined_unstructured_data_list.append(c)
                        combined_unstructured_title_list.append(
                            "GB card benefits information"
                        )

        # Web search response
        for query, value in self.web_search.items():
            doc_limit = (
                1
                if self.complement.get(query, {}).get("extended_info_result", [])
                else 5
            )
            for search_item in value:
                if (
                    search_item["priority"] == "high"
                    and search_item["text_data"] not in priority_data_ls
                ):
                    title = search_item.get("title") or ""
                    text = search_item.get("text_data") or ""
                    priority_data_ls.append(text)
                    priority_title_ls.append(title)
                    if search_item.get("blob_path") != "":
                        self.ai_search_meta_data.append(
                            {
                                "hyperlink": search_item.get("blob_path", ""),
                                "label": "priority",  # TODO: label should be dynamic
                                "type": "",  # TODO: type should be dynamic
                                "description": search_item.get(
                                    "title", ""
                                ),  # TODO: description should be dynamic
                            }
                        )

                elif (
                    search_item["text_data"] not in combined_unstructured_data_list
                    and len(combined_unstructured_data_list) < doc_limit
                ):
                    title = search_item.get("title") or ""
                    text = search_item.get("text_data") or ""
                    combined_unstructured_data_list.append(text)
                    combined_unstructured_title_list.append(title)
                    blob_path = search_item.get("blob_path") or ""
                    if "https" in blob_path:
                        self.ai_search_meta_data.append(
                            {
                                "hyperlink": search_item.get("blob_path", ""),
                                "label": "web",  # TODO: label should be dynamic
                                "type": search_item.get(
                                    "index_name", ""
                                ),  # TODO: type should be dynamic
                                "description": search_item.get(
                                    "title", ""
                                ),  # TODO: description should be dynamic
                            }
                        )

        for query, value in self.ai_search.items():
            for search_item in value:

                if search_item["text_data"] in priority_data_ls:
                    continue

                if (
                    search_item["always_use_in_response"]
                    and search_item["text_data"] not in always_use_in_response_data_ls
                    and len(always_use_in_response_data_ls)
                    <= 4  # Limit to 4 always use items
                ):
                    title = search_item.get("title") or ""
                    text = search_item.get("text_data") or ""
                    always_use_in_response_data_ls.append(f"{title}: {text}")
                    if search_item.get("blob_path") != "":
                        self.ai_search_meta_data.append(
                            {
                                "hyperlink": search_item.get("blob_path", ""),
                                "label": "always",
                                "type": "",
                                "description": search_item.get("title", ""),
                            }
                        )
                    continue
                if search_item["text_data"] not in combined_unstructured_data_list:
                    title = search_item.get("title") or ""
                    text = search_item.get("text_data") or ""
                    combined_unstructured_data_list.append(text)
                    combined_unstructured_title_list.append(title)
                    if (
                        search_item.get("blob_path")
                        and search_item.get("blob_path") != ""
                        and search_item.get("blob_path") not in ai_search_blob_path_set
                    ):
                        self.ai_search_meta_data.append(
                            {
                                "hyperlink": search_item.get("blob_path", ""),
                                "label": "AI search",
                                "type": search_item.get("system_name", ""),
                                "description": search_item.get("title", ""),
                            }
                        )
                        ai_search_blob_path_set.append(search_item.get("blob_path", ""))

        eliminate_chunk_idx = []
        if self.channel == "Custom Timeout":
            chunk_llm_evaluation = run_retrieval_evaluation_parallel(
                query, combined_unstructured_data_list
            )
            eliminate_chunk_idx = [x[0] for x in chunk_llm_evaluation if int(x[1]) < 3]

            keep = set(eliminate_chunk_idx)
            combined_unstructured_data_list = [
                v
                for idx, v in enumerate(combined_unstructured_data_list)
                if idx not in keep
            ]
            combined_unstructured_title_list = [
                v
                for idx, v in enumerate(iterable=combined_unstructured_title_list)
                if idx not in keep
            ]

        # # 각 chunk 의
        # new_data = combined_unstructured_data_list.copy()
        # new_titles = combined_unstructured_title_list.copy()
        # for data, title in zip(new_data, new_titles):
        #     # only append if this title is fresh
        #     if title not in combined_unstructured_title_list:
        #         combined_unstructured_data_list.append(data)
        #         combined_unstructured_title_list.append(title)

        # Rerank the data if there are data
        # priority, alway는 rerank 하지 않음
        combined_unstructured_data_fin_ls = []
        if combined_unstructured_data_list:
            rewritten_query = ". ".join(self.rewritten_queries)
            df = pd.DataFrame(
                {
                    "text_data": combined_unstructured_data_list,
                    "title": combined_unstructured_title_list,
                }
            )
            # df['length'] = [len(x) for x in df['text_data']]
            rerank_df = rerank_db_results(
                rewritten_query,
                df,
                "text_data",
                12,
                -1,
                skip_threshold=True,
                multiple_cols=True,
            )
            combined_unstructured_data_fin_ls = list(
                set(rerank_df["text_data"].tolist())
            )

        # Group by title and concatenate content
        try:
            priority_data_ls = [
                ":".join(item) for item in zip(priority_title_ls, priority_data_ls)
            ]
            grouped = defaultdict(list)
            for chunk in priority_data_ls:
                title, rest = chunk.split(":", 1)  # split at first colon
                grouped[title].append(rest)
            # 2) Build the output list
            grouped_priority_data_ls = [
                f"""Title: {title}, Content: {"".join(parts)}"""
                for title, parts in grouped.items()
            ]

            non_priority_data_ls = (
                always_use_in_response_data_ls + combined_unstructured_data_fin_ls
            )
            # 1) avoid duplicates: if a title appears in the "always" list, drop it from combined
            always_titles = {
                chunk.split(":", 1)[0] for chunk in always_use_in_response_data_ls
            }
            filtered_combined = [
                chunk
                for chunk in combined_unstructured_data_fin_ls
                if chunk.split(":", 1)[0] not in always_titles
            ]
            non_priority_data_ls = always_use_in_response_data_ls + filtered_combined
            grouped = defaultdict(list)
            for chunk in non_priority_data_ls:
                title, rest = chunk.split(":", 1)  # split at first colon
                grouped[title].append(rest)
            # 2) Build the output list
            grouped_non_priority_data_ls = [
                f"""Title: {title}, Content: {"".join(parts)}"""
                for title, parts in grouped.items()
            ]

            # Combine the managed response to the reranked unstructured data
            self.unstructured_data_list = (
                grouped_priority_data_ls + grouped_non_priority_data_ls
            )
        except Exception as e:
            print(e)
            self.unstructured_data_list = (
                priority_data_ls
                + always_use_in_response_data_ls
                + combined_unstructured_data_fin_ls
            )

        return self

    def _is_priority_unstructured_doc(self, intelligence, doc: dict):
        alias_name = doc["alias_name"]
        system_name = doc["system_name"]

        kr_installation_config = AiSearchIndexDefinitions.KR_INSTALLATION()
        gb_installation_config = AiSearchIndexDefinitions.GB_INSTALLATION()

        index_def_kr_installation = kr_installation_config
        index_def_uk_installation = gb_installation_config
        if (
            intelligence == intelligences.INSTALLATION_INQUIRY
            # and doc["always_use_in_response"]
            and (
                (
                    self.country_code == "KR"
                    and system_name
                    == index_def_kr_installation.integration_index_system_name[0]
                )
                or (
                    self.country_code == "GB"
                    and system_name
                    == index_def_uk_installation.integration_index_system_name[0]
                )
            )
        ) or doc.get("priority", "") == "high":
            return True

        return False

    def response_path_determination(self) -> "MergeRag":
        if self.early_return:
            return self

        # Check if the use search gpt flag is true
        if self.orch_use_search_gpt_flag:
            self.response_path = response_types.ORIGINAL_QUERY_RESPONSE
            return self.update_early_return(True)

        # Check Rag Distributer Status
        if self.rag_confirmation_status == RagConfirmationStatus.NO_RAG_REQUIRED.value:
            self.response_path = response_types.GENERAL_RESPONSE
            return self.update_early_return(True)

        # Check if invalid model name flag is true
        # If it is, set the response path to invalid model name response
        if self.invalid_model_name_flag:
            self.response_path = response_types.INVALID_MODEL_NAME_RESPONSE
            return self.update_early_return(True)

        self.response_path = response_types.INFORMATIVE_RESPONSE
        return self.update_early_return(True)

    def merge_rag(self):
        return (
            self.validate_inputs()
            .check_early_response_exit()
            .data_validation_and_cleaning()
            .get_to_cache_data()
            .merge_cached_data()
            .modify_data_dicts()
            .response_path_determination()
            .return_data()
        )
