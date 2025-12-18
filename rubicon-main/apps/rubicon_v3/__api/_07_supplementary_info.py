import sys

sys.path.append("/www/alpha/")
import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "alpha.settings")
django.setup()

import time
import enum
import traceback
import concurrent.futures

from dataclasses import dataclass
from bson.objectid import ObjectId

from apps.rubicon_v3.__function import (
    __utils as utils,
    __django_rq as django_rq,
    __rubicon_log as rubicon_log,
    _84_product_extraction,
    _85_extend_request_info,
)
from apps.rubicon_v3.__function.__django_cache import (
    MessageFlags,
    DjangoCacheClient,
    CacheKey,
)
from apps.rubicon_v3.__function.definitions import intelligences, sub_intelligences
from apps.rubicon_v3.__api import (
    __utils as api_utils,
    _08_media,
    _09_related_query,
    _11_product_card,
)
from apps.rubicon_v3.__external_api._14_azure_email_alert import (
    send_process_error_alert,
)

from alpha.settings import VITE_OP_TYPE

cache = DjangoCacheClient()


class SupplementaryTypes(enum.Enum):
    MEDIA = "media"
    MEDIA_V2 = "media_v2"
    RELATED_QUERY = "related_query"
    RELATED_QUERY_V2 = "related_query_v2"
    GREETING_QUERY = "greeting_query"
    PRODUCT_CARD = "product_card"
    PRODUCT_CARD_V2 = "product_card_v2"
    LOADING_MESSAGE = "loading_message"
    HYPERLINK = "hyperlink"


class SupplementaryInfoV2:
    @dataclass
    class SupplementaryParams:
        message_id: str
        supplement_info: dict

    def __init__(self, input_params: SupplementaryParams):
        self.input_params = input_params

    def supplementary_info_api_mux(self):
        # Function to process multiple supplements concurrently
        def process_supplement(supplement_meta):
            """Worker function to process a single supplement"""
            supplement_type = supplement_meta.get("supplementType")
            supplement_count = supplement_meta.get("supplementCount", 1)
            timeout = supplement_meta.get("timeout", 5)

            if supplement_type == SupplementaryTypes.MEDIA.value:
                response = _08_media.get_media_data(
                    self.input_params.message_id,
                    supplement_count,
                    supplement_meta.get("supplementGalleryCount", 2),
                    timeout,
                )
                return SupplementaryTypes.MEDIA.value, response

            elif supplement_type == SupplementaryTypes.MEDIA_V2.value:
                response = _08_media.get_media_data_v2(
                    self.input_params.message_id,
                    supplement_count,
                    supplement_meta.get("supplementGalleryCount", 2),
                    timeout,
                )
                return SupplementaryTypes.MEDIA_V2.value, response

            elif supplement_type == SupplementaryTypes.RELATED_QUERY.value:
                response = _09_related_query.get_related_query_data(
                    self.input_params.message_id,
                    supplement_count,
                    timeout,
                )
                return SupplementaryTypes.RELATED_QUERY.value, response

            elif supplement_type == SupplementaryTypes.RELATED_QUERY_V2.value:
                response = _09_related_query.get_related_query_data_v2(
                    self.input_params.message_id,
                    supplement_count,
                    timeout,
                )
                return SupplementaryTypes.RELATED_QUERY_V2.value, response

            elif supplement_type == SupplementaryTypes.GREETING_QUERY.value:
                response = _09_related_query.get_greeting_query_data(
                    self.input_params.message_id,
                    supplement_count,
                    timeout,
                )
                return SupplementaryTypes.GREETING_QUERY.value, response

            elif supplement_type == SupplementaryTypes.PRODUCT_CARD.value:
                response = _11_product_card.get_product_card_data(
                    self.input_params.message_id,
                    supplement_count,
                    timeout,
                )
                return SupplementaryTypes.PRODUCT_CARD.value, response

            elif supplement_type == SupplementaryTypes.PRODUCT_CARD_V2.value:
                response = _11_product_card.get_product_card_data_v2(
                    self.input_params.message_id,
                    supplement_count,
                    timeout,
                )
                return SupplementaryTypes.PRODUCT_CARD_V2.value, response

            elif supplement_type == SupplementaryTypes.LOADING_MESSAGE.value:
                response = self.get_loading_message(
                    supplement_count,
                    timeout,
                )
                return SupplementaryTypes.LOADING_MESSAGE.value, response

            elif supplement_type == SupplementaryTypes.HYPERLINK.value:
                response = self.get_hyperlink_data(
                    supplement_count,
                    timeout,
                )
                return SupplementaryTypes.HYPERLINK.value, response

            else:
                return None, {
                    "success": False,
                    "data": [],
                    "message": f"Invalid supplement type {supplement_type}",
                }

        # Check if there are any supplements to process
        if not self.input_params.supplement_info:
            return {
                "success": True,
                "data": [],
                "message": "",
            }

        combined_supplement_data = []
        success_messages = {}
        failure_messages = {}
        success = False

        # Process all supplements concurrently
        with concurrent.futures.ThreadPoolExecutor() as executor:
            # Submit all tasks
            future_list = [
                executor.submit(process_supplement, supplement_meta)
                for supplement_meta in self.input_params.supplement_info
            ]

            # Process the results as they complete
            for future in concurrent.futures.as_completed(future_list):
                supplement_type, response = future.result()

                # Handle invalid supplement types
                if supplement_type is None:
                    return response  # Return error message for invalid supplement type

                # Handle success and failure messages
                if response.get("success"):
                    success = True
                    success_messages[supplement_type] = response.get("message", "")
                else:
                    failure_messages[supplement_type] = response.get("message", "")

                combined_supplement_data.append(
                    {
                        "supplement_type": supplement_type,
                        "data": response.get("data", []),
                    }
                )

        if not combined_supplement_data and self.input_params.supplement_info:
            return {
                "success": False,
                "data": [],
                "message": "Supplementary info api mux failed to get data",
            }

        # Combine success and failure messages
        combined_message = ""
        if any(message for message in success_messages.values()):
            combined_message += "[INFO] "
            for supplement_type, message in success_messages.items():
                if message:
                    combined_message += f"({supplement_type}) {message} | "

            combined_message = combined_message.removesuffix(" | ")

        if any(message for message in failure_messages.values()):
            if combined_message:
                combined_message += " -- "
            combined_message += "[ERROR] "
            for supplement_type, message in failure_messages.items():
                if message:
                    combined_message += f"({supplement_type}) {message} | "

            combined_message = combined_message.removesuffix(" | ")

        return {
            "success": success,
            "data": combined_supplement_data,
            "message": combined_message,
        }

    def get_loading_message(self, supplement_count, timeout):
        """
        Function to get the loading message data from django redis cache
        and return the data
        """
        loading_message_cached_data = None
        iteration = 0
        while iteration < timeout * 2:
            loading_message_cached_data = cache.get(
                CacheKey.loading_message(self.input_params.message_id)
            )
            if loading_message_cached_data:
                break
            iteration += 1
            time.sleep(0.5)

        if not loading_message_cached_data:
            return {
                "success": True,
                "data": [],
                "message": "No loading message data found",
            }

        return {
            "success": True,
            "data": [loading_message_cached_data],
            "message": "",
        }

    def get_hyperlink_data(self, supplement_count, timeout):
        """
        Function to get the hyperlink data from django redis cache
        and return the data
        """
        message_flags_cache_key = CacheKey.message_flags(self.input_params.message_id)
        message_flags_dict: dict = cache.get(message_flags_cache_key, {})
        show_supplement = message_flags_dict.get(
            MessageFlags.SHOW_SUPPLEMENT.value, False
        )
        show_hyperlink = message_flags_dict.get(
            MessageFlags.SHOW_HYPERLINK.value, False
        )

        if not show_supplement or not show_hyperlink:
            return {
                "success": True,
                "data": [],
                "message": f"Show supplementary info data: {show_supplement}, Show hyperlink data: {show_hyperlink}",
            }

        hyperlink_cached_data = None
        iteration = 0
        while iteration < timeout * 2:
            hyperlink_cached_data = cache.get(
                CacheKey.hyperlink(self.input_params.message_id)
            )
            if hyperlink_cached_data:
                break
            iteration += 1
            time.sleep(0.5)

        if not hyperlink_cached_data:
            return {
                "success": True,
                "data": [],
                "message": "No hyperlink data found",
            }

        if not isinstance(hyperlink_cached_data, list):
            return {
                "success": False,
                "data": [],
                "message": "Hyperlink data is not in the expected format",
            }

        # Grab the first (count number of items) from the hyperlink data
        top_hyperlink = hyperlink_cached_data[:supplement_count]

        return {
            "success": True,
            "data": top_hyperlink,
            "message": "",
        }


def post_response_supplementary_info(
    object_id: ObjectId,
    original_query: str,
    message_history: list,
    rewritten_queries: list,
    full_response: str,
    product_data: list,
    intelligence_data: dict,
    sub_intelligence_data: dict,
    channel: str,
    country_code: str,
    site_cd: str,
    user_info: dict,
    language: str,
    message_id: str,
    session_id: str = None,
    session_expiry: int = 60 * 60 * 1,  # 1 hour
):
    """
    Function to run the product extraction supplementary info
    """

    def send_alert(error_message, error_traceback):
        """
        Function to send process error alert
        """
        if VITE_OP_TYPE in ["STG", "PRD"]:
            context_data = {
                "Module": "Post Response Supplementary Info",
                "Channel": channel,
                "Country Code": country_code,
                "Object ID": str(object_id),
                "Session ID": session_id,
                "Message ID": message_id,
            }
            error_type = "process_error"

            send_process_error_alert(
                error_message,
                error_type,
                error_traceback=error_traceback,
                context_data=context_data,
            )

    def store_empty_data(cache_key, message):
        """
        Helper function to store empty data in cache
        """
        cache.store(
            cache_key,
            {
                "success": True,
                "data": [],
                "message": message,
            },
            session_expiry,
        )

    def clean_product_extraction_data(product_extraction_data):
        """
        Helper function to clean the product extraction data
        """
        cleaned_product_extraction_data = {
            "product_extraction": [],
        }
        for product_item in product_extraction_data.get("product_extraction", []):
            if (
                not product_item.get("product_model")
                or product_item["product_model"] == "None"
            ) and (
                not product_item.get("product_code")
                or product_item["product_code"] == "None"
            ):
                # Skip the product item if product_model is None or empty
                continue
            cleaned_product_extraction_data["product_extraction"].append(product_item)
        return cleaned_product_extraction_data

    try:
        # Check if the product data is available
        if product_data:
            # Enqueue the product card v2 store function
            django_rq.run_job_high(
                _11_product_card.product_card_store_v2,
                (
                    object_id,
                    product_data,
                    country_code,
                    channel,
                    site_cd,
                    message_id,
                    session_expiry,
                ),
                {},
            )

            # Enqueue the media v2 store function
            django_rq.run_job_high(
                _08_media.media_store_v2,
                (
                    object_id,
                    product_data,
                    country_code,
                    site_cd,
                    message_id,
                    session_expiry,
                ),
                {},
            )

            # Enqueue the related query v2 store function
            django_rq.run_job_high(
                _09_related_query.related_question_store_v2,
                (
                    object_id,
                    original_query,
                    rewritten_queries,
                    full_response,
                    product_data,
                    message_history,
                    intelligence_data,
                    sub_intelligence_data,
                    channel,
                    country_code,
                    user_info,
                    language,
                    message_id,
                    session_expiry,
                ),
                {},
            )

        # Check if the Sub Intelligence is SmartThings Explanation (If so, skip product extraction)
        elif sub_intelligence_data and any(
            sub_intelligence == sub_intelligences.SMARTTHINGS_EXPLANATION
            for sub_intelligence in sub_intelligence_data.values()
        ):
            pass

        # If product data is not available, proceed with product extraction
        else:
            # First try to get all the product info from the full response
            product_extraction_data = _84_product_extraction.product_extraction(
                full_response
            )

            # Clean the product extraction data to remove any items with empty or None product_model
            product_extraction_data = clean_product_extraction_data(
                product_extraction_data
            )

            # If product extraction data is empty, store empty data for product card and media
            if not product_extraction_data or not product_extraction_data.get(
                "product_extraction"
            ):
                store_empty_data(
                    CacheKey.product_card_v2(message_id),
                    "No product extraction data found",
                )
                store_empty_data(
                    CacheKey.media_v2(message_id),
                    "No product extraction data found",
                )
                return

            # Get the product info from the product extraction data
            product_infos = []
            mapped_product_infos = []
            for product_item in product_extraction_data.get("product_extraction", []):
                try:
                    mapped_info = _85_extend_request_info.extend_request_info(
                        {"product_extraction": [product_item]},
                        (
                            intelligences.PRODUCT_RECOMMENDATION
                            if any(
                                intelligence == intelligences.PRODUCT_RECOMMENDATION
                                for intelligence in intelligence_data.values()
                            )
                            else None
                        ),
                        country_code,
                        "B2C",
                        1,
                        "",
                    )
                    # If mapped products is a list, extend the mapped product info
                    if isinstance(mapped_info, list):
                        mapped_product_infos.extend(mapped_info)
                except Exception as e:
                    print(
                        f"Error extending request info for product item {product_item}: {str(e)}"
                    )
                    # If there is an error in extending the request info, log the error and pass
                    send_alert(str(e), traceback.format_exc())

            # If mapped product info is a list and not empty, process it
            if mapped_product_infos and isinstance(mapped_product_infos, list):
                # Sort the mapped product info by min_id (ctg rank)
                mapped_product_infos.sort(key=lambda x: x.get("id", float("inf")))

                # Format product infos to match the product data structure
                for item in mapped_product_infos:
                    product_dict = {
                        "query": full_response,
                        "code": utils.get_first_or_string(item, "extended_info"),
                        "mapping_code": utils.get_first_or_string(item, "mapping_code"),
                        "category_lv1": utils.get_first_or_string(item, "category_lv1"),
                        "category_lv2": utils.get_first_or_string(item, "category_lv2"),
                        "category_lv3": utils.get_first_or_string(item, "category_lv3"),
                    }
                    # Get the product name and product line based on the country code
                    utils.get_product_line_product_name(product_dict, country_code)
                    # Get the product division based on the product category and country code
                    utils.get_product_division(product_dict, country_code)

                    # Append the product dictionary to product infos
                    product_infos.append(product_dict)

            # If no product infos are found, store empty data for product card
            if not product_infos:
                store_empty_data(
                    CacheKey.product_card_v2(message_id),
                    "No product infos found from product extraction",
                )
            # Otherwise, enqueue the product card v2 store function
            else:
                django_rq.run_job_high(
                    _11_product_card.product_card_store_v2,
                    (
                        object_id,
                        product_infos,
                        country_code,
                        channel,
                        site_cd,
                        message_id,
                        session_expiry,
                    ),
                    {},
                )

            # If no product infos are found, store empty data for media
            if not product_infos:
                store_empty_data(
                    CacheKey.media_v2(message_id),
                    "No product infos found from product extraction",
                )
            # Otherwise, enqueue the media v2 store function
            else:
                django_rq.run_job_high(
                    _08_media.media_store_v2,
                    (
                        object_id,
                        product_infos,
                        country_code,
                        message_id,
                        session_expiry,
                    ),
                    {},
                )

            # Enqueue the related query v2 store function (regardless of the product extraction results)
            django_rq.run_job_high(
                _09_related_query.related_question_store_v2,
                (
                    object_id,
                    original_query,
                    rewritten_queries,
                    full_response,
                    product_infos,
                    message_history,
                    intelligence_data,
                    sub_intelligence_data,
                    channel,
                    country_code,
                    user_info,
                    language,
                    message_id,
                    session_expiry,
                ),
                {},
            )

            # Remove the query key from the product infos
            cleaned_product_infos = []
            for mapped_info in product_infos:
                cleaned_product_infos.append(
                    {k: v for k, v in mapped_info.items() if k != "query"}
                )

            # Update the product log
            django_rq.run_job_high(
                api_utils.update_corresponding_collection_log_by_field,
                (
                    message_id,
                    "product_log",
                    cleaned_product_infos,
                ),
                {},
            )

            # Append the new mentioned products to the cached mentioned products
            # Only update if session_id is provided
            if session_id:
                # Get the cached mentioned products
                mentioned_products_cache = cache.get(
                    CacheKey.mentioned_products(session_id), []
                )

                mentioned_products_cache.append(cleaned_product_infos)
                # Store the updated mentioned products in cache
                cache.store(
                    CacheKey.mentioned_products(session_id),
                    mentioned_products_cache,
                    session_expiry,
                )

            # Update the message id's debug cache and log
            debug_content_dict = {
                "section_name": "Product Extraction",
                "product_extraction_data": product_extraction_data,
                "mapped_product_info": mapped_product_infos,
                "product_log": [
                    {**product, "query": product["query"][:100] + ". . ."}
                    for product in product_infos
                ],
            }

            # Get the current debug cache
            debug_cache = cache.get(CacheKey.debug_content(message_id))
            # Only append if debug_cache is present
            if debug_cache and isinstance(debug_cache, list):
                debug_cache.append(debug_content_dict)
                # Store the updated debug cache
                cache.store(
                    CacheKey.debug_content(message_id),
                    debug_cache,
                    session_expiry,
                )

            # Run the debug log update job
            django_rq.run_job_high(
                rubicon_log.add_to_debug_log,
                (
                    object_id,
                    debug_content_dict,
                ),
                {},
            )

    except Exception as e:
        # Alert the error
        send_alert(str(e), traceback.format_exc())


if __name__ == "__main__":
    from icecream import ic

    full_response = """고객님, 삼성전자는 갤럭시 스마트폰 중 최신 모델로 Galaxy S25 시리즈, Galaxy Z Fold6, Galaxy Z Flip6 등을 판매합니다.  \n각 모델별 가격은 변동될 수 있으니, 정확한 가격 확인을 위해 고객님께서 원하시는 모델명을 알려주시면 상세 안내해 드리겠습니다.\n\n"""

    product_extraction_data = _84_product_extraction.product_extraction(full_response)

    ic("Product Extraction Data:", product_extraction_data)

    intelligence_data = {"query_key": "Product Description"}

    country_code = "KR"

    mapped_product_info = []
    for product_item in product_extraction_data.get("product_extraction", []):
        try:
            product_info = _85_extend_request_info.extend_request_info(
                {"product_extraction": [product_item]},
                (
                    intelligences.PRODUCT_RECOMMENDATION
                    if any(
                        intelligence == intelligences.PRODUCT_RECOMMENDATION
                        for intelligence in intelligence_data.values()
                    )
                    else None
                ),
                country_code,
                "B2C",
                1,
                "",
            )
            # If mapped products is a list, extend the mapped product info
            if isinstance(product_info, list):
                mapped_product_info.extend(product_info)
        except Exception as e:
            print(
                f"Error extending request info for product item {product_item}: {str(e)}"
            )
            print(traceback.format_exc())

    ic("Mapped Product Info:", mapped_product_info)

    product_infos = []
    if mapped_product_info and isinstance(mapped_product_info, list):
        # Sort the mapped product info by min_id (ctg rank)
        mapped_product_info.sort(key=lambda x: x.get("id", float("inf")))

        # Format product infos to match the product data structure
        for item in mapped_product_info:
            product_dict = {
                "query": full_response,
                "code": utils.get_first_or_string(item, "extended_info"),
                "mapping_code": utils.get_first_or_string(item, "mapping_code"),
                "category_lv1": utils.get_first_or_string(item, "category_lv1"),
                "category_lv2": utils.get_first_or_string(item, "category_lv2"),
                "category_lv3": utils.get_first_or_string(item, "category_lv3"),
            }
            # Get the product name and product line based on the country code
            utils.get_product_line_product_name(product_dict, country_code)
            # Get the product division based on the product category and country code
            utils.get_product_division(product_dict, country_code)

            # Append the product dictionary to product infos
            product_infos.append(product_dict)

    ic("Product Infos:", product_infos)

    ##################### TESTING POST RESPONSE SUPPLEMENTARY INFO #####################

    # post_response_supplementary_info(
    #     original_query="",
    #     message_history=[],
    #     rewritten_queries=[],
    #     full_response=full_response,
    #     product_data=[],
    #     intelligence_data={},
    #     sub_intelligence_data={},
    #     channel="DEV Debug",
    #     country_code="KR",
    #     user_info={},
    #     language="korean",
    #     message_id="test_message_id",
    #     session_id="test_session_id",
    #     session_expiry=3600,
    # )
