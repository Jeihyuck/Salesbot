import sys

sys.path.append("/www/alpha/")
import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "alpha.settings")
django.setup()

import random
import time
import pandas as pd
import asyncio
import hashlib
import traceback

from uuid import uuid4
from pydantic import BaseModel
from bson.objectid import ObjectId

from alpha import __log

from apps.rubicon_v3.__function import (
    __django_rq as django_rq,
    __django_cache as django_cache,
    __llm_call,
    __rubicon_log as rubicon_log,
)
from apps.rubicon_v3.__function.__django_cache import (
    MessageFlags,
    DjangoCacheClient,
    CacheKey,
)
from apps.rubicon_v3.__function.__prompts import (
    related_query_v2_prompt,
    greeting_query_translation_prompt,
)
from apps.rubicon_v3.__function._82_response_prompts import dict_to_multiline_comment
from apps.rubicon_v3.__function.definitions import (
    intelligences,
    sub_intelligences,
    channels,
)
from apps.rubicon_v3.__api.__utils import update_corresponding_collection_log_by_field
from apps.rubicon_v3.__external_api._11_user_info import getGuid
from apps.rubicon_v3.__external_api._05_product_recommend import ProductRecommend
from apps.rubicon_v3.__external_api._14_azure_email_alert import (
    send_process_error_alert,
)
from apps.rubicon_data.models import product_category, uk_product_spec_basics
from apps.rubicon_v3.models import Representative_Query
from apps.rubicon_v3.__function.__utils import get_product_line_product_name

from alpha.settings import VITE_OP_TYPE

cache = DjangoCacheClient()


class RelatedQuery(BaseModel):
    related_query: list[str]


class SuggestiveQuery(BaseModel):
    translated_suggestive_query: list[str]


def related_question_store(
    object_id: ObjectId,
    complement_data,
    language_data,
    message_id,
    session_expiry,
):
    try:
        related_query, success, message = related_question_generation(
            complement_data, language_data
        )

        cache.store(
            CacheKey.related_query(message_id),
            {"related_query": related_query, "success": success, "message": message},
            session_expiry,
        )
    except Exception as e:
        __log.error(f"Error in related_question_store: {e}")

        # Alert the error
        if VITE_OP_TYPE in ["STG", "PRD"]:
            context_data = {
                "Module": "Related Query Store",
                "Object ID": str(object_id),
                "Message ID": message_id,
            }
            send_process_error_alert(
                str(e),
                "process_error",
                error_traceback=traceback.format_exc(),
                context_data=context_data,
            )

        cache.store(
            CacheKey.related_query(message_id),
            {"related_query": [], "success": False, "message": str(e)},
            session_expiry,
        )


def related_question_generation(complement_data, language_data, query_count=3):
    success = False

    if all(
        not value or not value.get("top_query") for value in complement_data.values()
    ):
        return [], success, "Top query not found in complement data"

    success = True

    query_string = " | ".join(
        [value.get("top_query") for value in complement_data.values()]
    )

    prompt = f"""
[Task]
- user is asking about Samsung products, specifications, and functionalities.
- Guess what additional questions to ask and come up with {query_count}.

[Rules]
- Do not include the question asking drawbacks or negative aspects of the product.
- Do not include the question asking other company's products.
- Write these questions in {language_data}.

"""

    user_prompt = f"Input Query: {query_string}"

    messages = [
        {"role": "system", "content": [{"type": "text", "text": prompt}]},
        {"role": "user", "content": [{"type": "text", "text": user_prompt}]},
    ]

    related_questions = __llm_call.open_ai_call_structured(
        "gpt-4.1-mini", messages, RelatedQuery, 0.7, 0.4
    )
    return related_questions["related_query"], success, ""


def get_related_query_data(message_id, query_count, timeout):
    """
    Function to get related query data from django redis cache
    and return the limited number of related queries
    """
    message_flags_cache_key = CacheKey.message_flags(message_id)
    message_flags_dict: dict = cache.get(message_flags_cache_key, {})
    show_supplement = message_flags_dict.get(MessageFlags.SHOW_SUPPLEMENT.value, False)
    show_related_query = message_flags_dict.get(
        MessageFlags.SHOW_RELATED_QUERY.value, False
    )

    if not show_supplement or not show_related_query:
        return {
            "success": True,
            "data": [],
            "message": f"Show supplementary info data: {show_supplement}, Show related query data: {show_related_query}",
        }

    related_query_cached_data = {}
    iteration = 0
    while iteration < timeout * 2:
        related_query_cached_data = cache.get(CacheKey.related_query(message_id), {})
        if related_query_cached_data:
            break
        iteration += 1
        time.sleep(0.5)

    if not related_query_cached_data:
        return {"success": True, "data": [], "message": "No related query data found"}

    related_query = related_query_cached_data.get("related_query", [])
    success = related_query_cached_data.get("success", False)
    message = related_query_cached_data.get("message", "")

    top_related_query = related_query[:query_count]
    related_query_data = [
        {
            "related_query": query,
        }
        for query in top_related_query
    ]

    # Store the related query data to chat log
    django_rq.run_job_high(
        update_corresponding_collection_log_by_field,
        (
            message_id,
            "supplementary_log.related_query",
            related_query_data,
        ),
        {},
    )

    return {
        "success": success,
        "data": related_query_data,
        "message": message,
    }


############################ RELATED QUERY V2 ############################


def related_question_store_v2(
    object_id: ObjectId,
    original_query: str,
    rewritten_queries: list[str],
    full_response: str,
    product_info: list,
    message_history: list,
    intelligence_data: dict,
    sub_intelligence_data: dict,
    channel: str,
    country_code: str,
    user_info: dict,
    language_data: str,
    message_id: str,
    session_expiry: int,
):
    try:
        related_query, success, message = related_question_generation_v2(
            original_query,
            rewritten_queries,
            full_response,
            product_info,
            message_history,
            intelligence_data,
            sub_intelligence_data,
            channel,
            country_code,
            user_info,
            language_data,
        )

        cache.store(
            CacheKey.related_query_v2(message_id),
            {"related_query": related_query, "success": success, "message": message},
            session_expiry,
        )
    except Exception as e:
        __log.error(f"Error in related_question_store: {e}")

        # Alert the error
        if VITE_OP_TYPE in ["STG", "PRD"]:
            context_data = {
                "Module": "Related Query Store V2",
                "Channel": channel,
                "Country Code": country_code,
                "Object ID": str(object_id),
                "Message ID": message_id,
            }
            send_process_error_alert(
                str(e),
                "process_error",
                error_traceback=traceback.format_exc(),
                context_data=context_data,
            )

        cache.store(
            CacheKey.related_query_v2(message_id),
            {"related_query": [], "success": False, "message": str(e)},
            session_expiry,
        )


####################################################################################
# NOTE: THIS FUNCTION IS DISABLED AS THE PERSONALIZED RECOMMENDATION API HAS CHANGED
####################################################################################
# def personalized_recommendation(guid, country_code):
#     new_product_info = []
#     recommender = ProductRecommend(country_code)
#     guid_base_rec = asyncio.run(
#         recommender.getRecommendedProduct(
#             "guid_based_recommendation", None, None, None, None, None, None, guid
#         )
#     )
#     compatible_rec = asyncio.run(
#         recommender.getRecommendedProduct(
#             "compatible_to_own_products", None, None, None, None, None, None, guid
#         )
#     )

#     guid_base_list = [item["model"] for item in guid_base_rec if item["rank"] <= 3]
#     compatible_list = [item["model"] for item in compatible_rec if item["rank"] <= 3]

#     if guid_base_list or compatible_list:
#         model_list = guid_base_list + compatible_list

#         if country_code == "KR":
#             results = list(
#                 product_category.objects.filter(mdl_code__in=model_list).values(
#                     "mdl_code",
#                     "product_category_lv1",
#                     "product_category_lv2",
#                     "product_category_lv3",
#                 )
#             )
#         elif country_code == "GB":
#             results = list(
#                 uk_product_spec_basics.objects.filter(model_code__in=model_list).values(
#                     "model_code", "category_lv1", "category_lv2", "category_lv3"
#                 )
#             )
#         else:
#             __log.error(f"Unsupported country code: {country_code}")
#             return new_product_info

#         results_df = pd.DataFrame(results)
#         if not results_df.empty:
#             results_df.columns = [
#                 "code",
#                 "category_lv1",
#                 "category_lv2",
#                 "category_lv3",
#             ]
#             results_df["mapping_code"] = ["personalized recommended"] * len(results_df)
#             results_dict_list = results_df.to_dict(orient="records")
#             for results_dict in results_dict_list:
#                 get_product_line_product_name(results_dict, country_code)
#                 new_product_info.append(results_dict)
#     return new_product_info


def related_question_generation_v2(
    original_query: str,
    rewritten_queries: list[str],
    full_response: str,
    product_info: list,
    message_history: list,
    intelligence_data: dict,
    sub_intelligence_data: dict,
    channel: str,
    country_code: str,
    user_info: dict,
    language_data: str,
    query_count=3,
):
    # channels.UT_FNET, channels.FAMILYNET
    if not rewritten_queries or not intelligence_data:
        return [], True, "Insufficient data for related query generation"

    intelligence = list(intelligence_data.values())[0]
    sub_intelligence = (
        list(sub_intelligence_data.values())[0] if sub_intelligence_data else None
    )

    guid = getGuid(user_info)

    prompt = related_query_v2_prompt.BASE_PROMPT

    if channel in [channels.UT_FNET, channels.FAMILYNET]:
        task = get_FNET_task(intelligence, sub_intelligence, product_info)
    else:
        task = get_task(
            intelligence, sub_intelligence, product_info, guid, country_code
        )

    task = task.replace("{language}", language_data).replace(
        "{number_of_queries}", str(query_count)
    )

    prompt = prompt.format(
        task=task, language=language_data, number_of_queries=query_count
    )

    messages = [{"role": "system", "content": [{"type": "text", "text": prompt}]}]

    # Add message history
    for message in message_history:
        messages.append(message)

    user_content = []
    input_prompt = dict_to_multiline_comment(
        {
            "Original Query": original_query,
            "ReWrite Queries": rewritten_queries,
            "Assistant's Response": full_response,
            "Product Info": product_info,
            "Scenario": intelligence,
            "Sub-scenario": sub_intelligence,
            "User Info": user_info,
        }
    )
    user_content.append({"type": "text", "text": input_prompt})
    messages.append({"role": "user", "content": user_content})

    related_questions = __llm_call.open_ai_call_structured(
        "gpt-4.1-mini", messages, RelatedQuery, 0.7, 0.4
    )
    return related_questions["related_query"], True, ""


def get_task(intelligence, sub_intelligence, product_info, guid, country_code):
    task = related_query_v2_prompt.GENERAL_TASK
    if intelligence == intelligences.PURCHASE_POLICY:
        task = related_query_v2_prompt.PURCHASE_POLICY_TASK

    elif intelligence == intelligences.PRODUCT_DESCRIPTION:
        if (
            len(product_info) >= 2
            or sub_intelligence == sub_intelligences.PRODUCT_LINEUP_DESCRIPTION
        ):
            task = related_query_v2_prompt.PRODUCT_DESCRIPTION_TASK_MULTIPLE
        else:
            task = related_query_v2_prompt.PRODUCT_DESCRIPTION_TASK_ONE

    elif intelligence == intelligences.PRODUCT_COMPARISON:
        if len(product_info) >= 2:
            task = related_query_v2_prompt.PRODUCT_DESCRIPTION_TASK_MULTIPLE
        else:
            task = related_query_v2_prompt.PRODUCT_DESCRIPTION_TASK_ONE

        if sub_intelligence in [
            sub_intelligences.SAMSUNG_COMPARISON,
            sub_intelligences.PRODUCT_LINEUP_COMPARISON,
        ]:
            task = related_query_v2_prompt.SAMSUNG_COMPARISON_TASK

    elif intelligence == intelligences.PRODUCT_RECOMMENDATION:
        if len(product_info) >= 2:
            task = related_query_v2_prompt.PRODUCT_RECOMMENDATION_TASK_MULTIPLE
        else:
            task = related_query_v2_prompt.PRODUCT_RECOMMENDATION_TASK_ONE

        if sub_intelligence in [
            sub_intelligences.CONSUMABLES_ACCESSORIES_RECOMMENDATION,
            sub_intelligences.SET_PRODUCT_RECOMMENDATION,
        ]:
            task = related_query_v2_prompt.CONSUMABLE_RECOMMENDATION_TASK
        # NOTE: THE BELOW CODE IS DISABLED AS THE PERSONALIZED RECOMMENDATION API HAS CHANGED
        # if guid:
        #     new_product_info = personalized_recommendation(guid, country_code)
        #     product_info.append(new_product_info)
        #     if new_product_info:
        #         task = related_query_v2_prompt.PERSONALIZED_RECOMMENDATION_TASK

    elif intelligence == intelligences.INSTALLATION_INQUIRY:
        task = related_query_v2_prompt.INSTALLATION_TASK

    elif intelligence == intelligences.BUY_INFORMATION:
        task = related_query_v2_prompt.PRICE_PROMOTION_TASK

    elif sub_intelligence == sub_intelligences.USAGE_EXPLANATION:
        task = related_query_v2_prompt.USAGE_EXPLANATION_TASK

    elif sub_intelligence == sub_intelligences.SAMSUNG_CARE_PLUS_EXPLANATION:
        task = related_query_v2_prompt.CARE_PLUS_TASK

    return task


def get_FNET_task(intelligence, sub_intelligence, product_info):
    task = related_query_v2_prompt.FN_GENERAL_TASK

    if intelligence == intelligences.PRODUCT_DESCRIPTION:
        if sub_intelligence == sub_intelligences.PRODUCT_FEATURE:
            task = related_query_v2_prompt.FN_PRODUCT_FEATURE_TASK

        elif sub_intelligence == sub_intelligences.PRODUCT_SPECIFICATION:
            task = related_query_v2_prompt.FN_PRODUCT_SPECIFICATION_TASK

        elif sub_intelligence == sub_intelligences.PRODUCT_FUNCTION:
            task = related_query_v2_prompt.FN_PRODUCT_FUNCTION_TASK

        elif sub_intelligence == sub_intelligences.PRODUCT_REVIEW:
            task = related_query_v2_prompt.FN_PRODUCT_DESCRIPTION_TASK

    elif intelligence == intelligences.PRODUCT_COMPARISON:
        task = related_query_v2_prompt.FN_PRODUCT_DESCRIPTION_TASK

    elif intelligence == intelligences.PRODUCT_RECOMMENDATION:
        if len(product_info) >= 2:
            task = related_query_v2_prompt.FN_PRODUCT_RECOMMENDATION_TASK_MULTIPLE
        else:
            task = related_query_v2_prompt.FN_PRODUCT_RECOMMENDATION_TASK_ONE

        if sub_intelligence in [
            sub_intelligences.CONSUMABLES_ACCESSORIES_RECOMMENDATION,
            sub_intelligences.SET_PRODUCT_RECOMMENDATION,
        ]:
            task = related_query_v2_prompt.FN_CONSUMABLE_RECOMMENDATION_TASK

    elif intelligence == intelligences.INSTALLATION_INQUIRY:
        task = related_query_v2_prompt.INSTALLATION_TASK

    elif sub_intelligence == sub_intelligences.USAGE_EXPLANATION:
        task = related_query_v2_prompt.USAGE_EXPLANATION_TASK

    elif sub_intelligence == sub_intelligences.SAMSUNG_CARE_PLUS_EXPLANATION:
        task = related_query_v2_prompt.CARE_PLUS_TASK

    return task


def get_related_query_data_v2(message_id, query_count, timeout):
    """
    Function to get related query data from django redis cache
    and return the limited number of related queries
    """
    message_flags_cache_key = CacheKey.message_flags(message_id)
    message_flags_dict: dict = cache.get(message_flags_cache_key, {})
    show_supplement = message_flags_dict.get(MessageFlags.SHOW_SUPPLEMENT.value, False)
    show_related_query = message_flags_dict.get(
        MessageFlags.SHOW_RELATED_QUERY.value, False
    )
    if not show_supplement or not show_related_query:
        return {
            "success": True,
            "data": [],
            "message": f"Show supplementary info data: {show_supplement}, Show related query data: {show_related_query}",
        }

    related_query_cached_data = {}
    iteration = 0
    while iteration < timeout * 2:
        related_query_cached_data = cache.get(CacheKey.related_query_v2(message_id), {})
        if related_query_cached_data:
            break
        iteration += 1
        time.sleep(0.5)

    if not related_query_cached_data:
        return {"success": True, "data": [], "message": "No related query data found"}

    related_query = related_query_cached_data.get("related_query", [])
    success = related_query_cached_data.get("success", False)
    message = related_query_cached_data.get("message", "")

    top_related_query = related_query[:query_count]
    related_query_data = [
        {
            "related_query": query,
        }
        for query in top_related_query
    ]

    # Store the related query data to chat log
    django_rq.run_job_high(
        update_corresponding_collection_log_by_field,
        (
            message_id,
            "supplementary_log.related_query",
            related_query_data,
        ),
        {},
    )

    return {
        "success": success,
        "data": related_query_data,
        "message": message,
    }


############################ DEFAULT GREETING QUERIES ############################

DEFAULT_GREETING_QUERIES = [
    "갤럭시 S25 Ultra가 S24 Ultra에 비해 좋아진 부분이 뭔가요?",
    "Galaxy AI 기능에 대해 알려주세요.",
    "최신 스마트폰 추천해주세요.",
]


def greeting_query_store(
    channel: str,
    country_code: str,
    language_data: str,
    message_id: str,
    session_expiry: int,
):
    """
    Function to store default greeting queries in django redis cache
    """
    try:
        greeting_query_data, success, message = greeting_query_retrieval(
            channel, country_code, language_data
        )

        cache.store(
            CacheKey.greeting_query(message_id=message_id),
            {"success": success, "data": greeting_query_data, "message": message},
            session_expiry,
        )
    except Exception as e:
        __log.error(f"Error in greeting_query_store: {e}")

        # Alert the error
        if VITE_OP_TYPE in ["STG", "PRD"]:
            context_data = {
                "Module": "Greeting Query Store",
                "Country Code": country_code,
                "Channel": channel,
                "Message ID": message_id,
            }
            send_process_error_alert(
                str(e),
                "process_error",
                error_traceback=traceback.format_exc(),
                context_data=context_data,
            )

        cache.store(
            CacheKey.greeting_query(message_id=message_id),
            {"success": False, "data": {}, "message": str(e)},
            session_expiry,
        )


def greeting_query_retrieval(channel: str, country_code: str, language_data: str):
    """
    Function to get default greeting queries from pre-generated list of queries
    """
    # First get the top 2 distinct batch groups
    top_batch_groups = (
        Representative_Query.objects.filter(
            channel=channel,
            country_code=country_code,
            active=True,
        )
        .values_list("batch_group", flat=True)
        .distinct()
        .order_by("-batch_group")[:2]  # Get top 2 batch groups
    )

    # Then get the queries for only those top batch groups
    query_data = list(
        (
            Representative_Query.objects.filter(
                channel=channel,
                country_code=country_code,
                active=True,
                batch_group__in=top_batch_groups,  # Filter to only include top 2 batch groups
            )
            .values("query", "batch_group", "display_order")
            .order_by("-batch_group", "display_order")
            .distinct()
        )
    )

    # If no queries found, use the default greeting queries
    if not query_data:
        query_data = [
            {"query": query, "batch_group": "default", "display_order": i + 1}
            for i, query in enumerate(DEFAULT_GREETING_QUERIES)
        ]
        top_batch_groups = ["default"]

    # Translate the representative queries to the user's language
    query_list = [
        item["query"] for item in query_data if item["query"] and item["query"].strip()
    ]

    query_string = "|".join(query_list)
    content_hash = hashlib.md5(query_string.encode()).hexdigest()[:8]

    # Check if greeting queries are already cached
    greeting_query_cache_key = CacheKey.greeting_query(
        channel, country_code, language_data
    )
    cached_greeting_query = cache.get(greeting_query_cache_key, {})

    # Check if the cached greeting queries match the current content hash
    if cached_greeting_query.get("content_hash") == content_hash:
        # Content hash matches, return cached data
        top_batch_groups = cached_greeting_query.get("top_batch_groups", [])
        query_data = cached_greeting_query.get("query_data", [])
        return (
            {"top_batch_groups": top_batch_groups, "query_data": query_data},
            True,
            "Greeting queries retrieved from cache.",
        )

    # Content hash does not match, proceed with translation
    input_prompt = dict_to_multiline_comment({"suggestive_queries": query_list})

    # Prepare the messages for the OpenAI call
    prompt = greeting_query_translation_prompt.PROMPT.format(language=language_data)
    messages = [
        {"role": "system", "content": prompt},
        {"role": "assistant", "content": input_prompt},
    ]

    # Get the translated queries using OpenAI API
    translated_queries = __llm_call.open_ai_call_structured(
        "gpt-4.1-mini", messages, SuggestiveQuery, 0.01, 0.1, 42
    )

    # Extract the translated queries
    translated_query_list = translated_queries.get("translated_suggestive_query", [])
    if not translated_query_list:
        return ({}, True, "No translated suggestive queries generated.")

    # Make sure the translated queries have the same length as the original queries
    if len(translated_query_list) != len(query_list):
        return (
            {},
            True,
            "Mismatch in the number of translated queries and original queries.",
        )

    # Replace the original queries with the translated ones
    for i, item in enumerate(query_data):
        item["query"] = translated_query_list[i]

    # Cache the greeting queries
    cache.store(
        greeting_query_cache_key,
        {
            "top_batch_groups": top_batch_groups,
            "query_data": query_data,
            "content_hash": content_hash,
        },
        60 * 60 * 24 * 1,  # Cache for 1 day
    )

    # Return the top batch group and query data
    return (
        {"top_batch_groups": top_batch_groups, "query_data": query_data},
        True,
        "Default greeting queries retrieved successfully.",
    )


def get_greeting_query_data(message_id: str, query_count: int, timeout: int) -> dict:
    greeting_query_cached_data = {}
    iteration = 0
    while iteration < timeout * 2:
        greeting_query_cached_data = cache.get(
            CacheKey.greeting_query(message_id=message_id), {}
        )
        if greeting_query_cached_data:
            break
        iteration += 1
        time.sleep(0.5)

    if not greeting_query_cached_data:
        return {
            "success": True,
            "data": [
                {"greeting_query": query}
                for query in DEFAULT_GREETING_QUERIES[:query_count]
            ],
            "message": "No greeting query data found. Returning default queries.",
        }

    greeting_query_data = greeting_query_cached_data.get("data", {})
    success = greeting_query_cached_data.get("success", True)
    message = greeting_query_cached_data.get("message", "")
    top_batch_groups = greeting_query_data.get("top_batch_groups", [])
    query_data = greeting_query_data.get("query_data", [])

    # Go through each batch group and get random queries
    limited_query_data = []
    for batch_group in top_batch_groups:
        # Filter queries for the current batch group
        batch_group_items = [
            item for item in query_data if item["batch_group"] == batch_group
        ]

        # If there are enough queries in the batch group, select random ones
        limited_query_data.extend(batch_group_items)
        if len(limited_query_data) >= query_count:
            # Get random queries from the limited set
            random_queries = random.sample(batch_group_items, query_count)

            # Order the random queries by display order
            random_queries.sort(key=lambda x: x["display_order"])

            greeting_queries = [
                {"greeting_query": item["query"]} for item in random_queries
            ]
            return {
                "success": success,
                "data": greeting_queries,
                "message": message,
            }

    # If there are queries but not enough to meet the query count,
    # Return the available queries
    if limited_query_data:
        return {
            "success": success,
            "data": [
                {"greeting_query": item["query"]}
                for item in limited_query_data[:query_count]
            ],
            "message": message
            or "Not enough greeting queries found, returning available queries.",
        }

    # If not enough queries, return an empty list with a message
    return {
        "success": True,
        "data": [],
        "message": "Not enough greeting queries found.",
    }


if __name__ == "__main__":
    # channel = "DEV Debug"
    # country_code = "KR"
    # language_data = "ko"
    # message_id = "test_message_id"
    # session_expiry = 60 * 30  # 30 minutes
    # greeting_query_store(
    #     channel, country_code, language_data, message_id, session_expiry
    # )
    # greeting_query_data = get_greeting_query_data(message_id, 3, 10)
    # print(greeting_query_data)

    ####################################################################

    # Test related question store v2
    message_id = str(uuid4())
    print(f"Message ID: {message_id}")
    session_expiry = 30
    country_code = "KR"
    show_supplementary_info_cache_key = django_cache.CacheKey.message_flags(message_id)
    cache.store(
        show_supplementary_info_cache_key,
        {
            MessageFlags.SHOW_SUPPLEMENT.value: True,
            MessageFlags.SHOW_RELATED_QUERY.value: True,
        },
        session_expiry,
    )

    original_query = "현재 진행 중인 오디오 시스템 관련 프로모션이 있나요?"
    rewritten_queries = ["현재 진행 중인 오디오 시스템 관련 프로모션이 있나요?"]
    full_response = ""
