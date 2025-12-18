import sys

sys.path.append("/www/alpha/")
import os
import django
from django.db.models import F

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "alpha.settings")
django.setup()

import enum
import time
import traceback

from uuid import uuid4
from datetime import date
from dateutil.relativedelta import relativedelta
from bson.objectid import ObjectId

from azure.search.documents import SearchClient
from azure.core.credentials import AzureKeyCredential
from azure.search.documents.models import VectorizedQuery

from apps.rubicon_v3.__function import (
    __django_cache,
    __rubicon_log as rubicon_log,
    __django_rq as django_rq,
    __embedding_rerank as embedding_rerank,
)
from apps.rubicon_v3.__function.__django_cache import MessageFlags, DjangoCacheClient
from apps.rubicon_v3.__function.ai_search.ai_search_index_definitions import (
    AiSearchIndexDefinitions,
)
from apps.rubicon_v3.__api.__utils import update_corresponding_collection_log_by_field
from apps.rubicon_v3.__external_api._14_azure_email_alert import (
    send_process_error_alert,
)
from apps.rubicon_v3.models import Unstructured_Index
from apps.rubicon_data.models import (
    product_category,
    product_images,
    product_card,
    uk_product_visual_contents,
    uk_product_card,
)
from apps.rubicon_v3.__function.definitions import site_cds
from alpha import settings, __log
from alpha.settings import (
    VITE_OP_TYPE,
)

cache = DjangoCacheClient()


class IndexName(str, enum.Enum):
    MEDIA = "MEDIA_IMAGE"
    INTEGRATION = "INTEGRATION"
    MEDIA_VIDEO = "MEDIA_VIDEO"


def media_store(
    object_id: ObjectId,
    product_data,
    country_code,
    message_id,
    session_expiry,
    threshold=1.0,
    k=1,
):
    """
    Function to run image search and store the results in django redis cache
    This function is run using django rq worker
    """
    try:
        media_contents, success, message = media_search(
            product_data, country_code, threshold, k
        )

        cache.store(
            __django_cache.CacheKey.media(message_id),
            {"success": success, "data": media_contents, "message": message},
            session_expiry,
        )
    except Exception as e:
        __log.error(f"Error in image_store: {e}")

        # Alert the error
        if VITE_OP_TYPE in ["STG", "PRD"]:
            context_data = {
                "Module": "Media Store",
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
            __django_cache.CacheKey.media(message_id),
            {"success": False, "data": [], "message": str(e)},
            session_expiry,
        )


def media_search(product_data, country_code, site_cd, threshold, k):
    media_contents = []
    success = False

    # Validate that product_data is a list of dicts with 'query' key
    if all(not value or not value.get("query") for value in product_data):
        return media_contents, success, "Product data is empty"

    # Get the Azure Search index name from Unstructured_Index table
    azure_integration_index_name = Unstructured_Index.objects.filter(
        country_code=country_code,
        op_type=VITE_OP_TYPE,
        name=IndexName.INTEGRATION.value,
    ).values_list("ai_search_index", flat=True)

    # The media and youtube index configs are determined based on country code
    if country_code == "KR":
        if site_cd == site_cds.FN:
            media_config = AiSearchIndexDefinitions.KR_FN_MEDIA_IMAGE()
        else:
            media_config = AiSearchIndexDefinitions.KR_MEDIA_IMAGE()
        video_config = AiSearchIndexDefinitions.KR_MEDIA_VIDEO()
    elif country_code == "GB":
        media_config = AiSearchIndexDefinitions.GB_MEDIA_IMAGE()
        video_config = AiSearchIndexDefinitions.GB_MEDIA_VIDEO()

    # Grab the index system names and versions from the configs
    azure_media_info = media_config.integration_index_system_name
    azure_media_video_info = video_config.integration_index_system_name

    # Validate that the index names are found
    if not azure_media_info[0] or not azure_media_video_info[0]:
        return (
            media_contents,
            success,
            f"Index {azure_media_info[0] if not azure_media_info[0] else azure_media_video_info[0]} not found",
        )

    success = True

    # For DEV environment, override the azure search env variables to point the correct locale index
    settings.override_azure_search_env(country_code)
    AZURE_SEARCH_ENDPOINT = settings.AZURE_SEARCH_ENDPOINT
    AZURE_SEARCH_API_KEY = settings.AZURE_SEARCH_API_KEY

    # Media Search Client
    media_client = SearchClient(
        endpoint=AZURE_SEARCH_ENDPOINT,
        index_name=azure_integration_index_name[0],
        credential=AzureKeyCredential(AZURE_SEARCH_API_KEY),
    )

    # Iterate through the product data and prepare filter conditions
    for value in product_data:
        filter_condition_data = {"category": [], "code": []}

        # Collect the model code filter condition data
        if value.get("code"):
            filter_condition_data["code"].append(
                {
                    "model_code": value["code"],
                }
            )

        # Collect the category filter condition data
        if (
            value.get("category_lv1")
            and value.get("category_lv2")
            and value.get("category_lv3")
        ):
            filter_condition_data["category"].append(
                {
                    "category_lv1": value["category_lv1"],
                    "category_lv2": value["category_lv2"],
                    "category_lv3": value["category_lv3"],
                }
            )

        # If no filter conditions, skip this iteration
        if not filter_condition_data:
            continue

        # Prepare the filter conditions
        code_filter_data = filter_condition_data.get("code")
        category_filter_data = filter_condition_data.get("category")

        ai_media_results = None
        code_filter_conditions = []
        category_filter_conditions = []
        youtube_filter_conditions = []
        media_filter_condition = None
        youtube_filter_condition = None

        # Set up code filter
        if code_filter_data:
            # Find all information for the model codes
            code_filter_conditions.append(
                " or ".join(
                    [
                        f"model_code/any(c: c eq '{code["model_code"]}')"
                        for code in code_filter_data
                    ]
                )
            )
            # Grab only the displayable items
            code_filter_conditions.append("is_display eq 1")

            # Combine the above filters to form the final filter condition
            media_filter_condition = (
                " and ".join(f"({condition})" for condition in code_filter_conditions)
                if code_filter_conditions
                else None
            )

        # Set up category filter
        if category_filter_data:
            # Find all information with category lv1 as defined
            category_filter_conditions.append(
                " or ".join(
                    list(
                        set(
                            [
                                f"category1 eq '{cat["category_lv1"]}'"
                                for cat in category_filter_data
                            ]
                        )
                    )
                )
            )
            # Find all information with category lv2 as defined
            category_filter_conditions.append(
                " or ".join(
                    list(
                        set(
                            [
                                f"category2 eq '{cat["category_lv2"]}'"
                                for cat in category_filter_data
                            ]
                        )
                    )
                )
            )
            # Find all information with category lv3 as defined
            category_filter_conditions.append(
                " or ".join(
                    list(
                        set(
                            [
                                f"category3 eq '{cat["category_lv3"]}'"
                                for cat in category_filter_data
                            ]
                        )
                    )
                )
            )
            # Make a copy for youtube filter conditions
            youtube_filter_conditions = category_filter_conditions.copy()

            # Overwrite the media filter condition only if there is no code filter
            if not code_filter_data:
                # Grab only the displayable items
                category_filter_conditions.append("is_display eq 1")

                # Combine the above filters to form the final filter condition
                media_filter_condition = (
                    " and ".join(
                        f"({condition})" for condition in category_filter_conditions
                    )
                    if category_filter_conditions
                    else None
                )

            # Add the system name and version to the filter condition
            if media_filter_condition:
                media_filter_condition += f" and (system_name eq '{azure_media_info[0]}' and version eq '{azure_media_info[1]}')"
            # If no filter conditions, just set the system name and version
            else:
                media_filter_condition = f"(system_name eq '{azure_media_info[0]}' and version eq '{azure_media_info[1]}')"

            # Add the system name and version to the youtube filter condition
            youtube_filter_conditions.append(
                f"system_name eq '{azure_media_video_info[0]}' and version eq '{azure_media_video_info[1]}'"
            )
            # Combine the above filters to form the final filter condition
            youtube_filter_condition = (
                " and ".join(
                    f"({condition})" for condition in youtube_filter_conditions
                )
                if youtube_filter_conditions
                else None
            )

        # If no filter conditions, skip this iteration
        if not media_filter_condition and not youtube_filter_condition:
            continue

        # Run the search query
        ai_media_results = media_client.search(
            search_text=value["query"],
            filter=media_filter_condition,
            vector_queries=[
                VectorizedQuery(
                    vector=embedding_rerank.baai_embedding(value["query"], None)[0],
                    fields="embedding_semantic_bgechunk",
                    k_nearest_neighbors=k * 3,
                    weight=1.0,
                )
            ],
            top=k * 3,
            query_type="semantic",
            semantic_configuration_name="my-semantic-config",
            query_caption="extractive",
        )
        ai_media_ytb_results = media_client.search(
            search_text=value["query"],
            filter=youtube_filter_condition,
            vector_queries=[
                VectorizedQuery(
                    vector=embedding_rerank.baai_embedding(value["query"], None)[0],
                    fields="embedding_semantic_bgechunk",
                    k_nearest_neighbors=k * 3,
                    weight=1.0,
                )
            ],
            top=k * 3,
            query_type="semantic",
            semantic_configuration_name="my-semantic-config",
            query_caption="extractive",
        )

        score = "@search.score"
        reranker_score = "@search.reranker_score"

        all_media_results = [result for result in ai_media_results]

        # Process the results
        for result in all_media_results:
            relevance_score = result[reranker_score]

            months_difference = None
            release_date = None

            # Generate time weighted relevance score
            time_weighted_relevance_score = relevance_score
            goods_id_list = result.get("goods_id")
            if not goods_id_list:
                time_weighted_relevance_score -= 0.1 * 12 * 2  # 2 years of deduction
            else:
                release_date_data = product_category.objects.filter(
                    goods_id__in=goods_id_list
                ).values_list("release_date", flat=True)
                if release_date_data:
                    release_date = release_date_data[0]

                    # Calculate the time difference in months
                    today = date.today()
                    time_difference = relativedelta(today, release_date)
                    months_difference = (
                        time_difference.years * 12 + time_difference.months
                    )
                    # Deduct 0.1 for each month
                    time_weighted_relevance_score -= 0.1 * months_difference
                else:
                    # If no release date is found, apply a default deduction
                    time_weighted_relevance_score -= (
                        0.1 * 12 * 2
                    )  # 2 years of deduction

            # Apply threshold
            if result[reranker_score] > threshold:
                media_contents.append(
                    {
                        "question": value["query"],
                        "title": result.get("title"),
                        "chunk": result.get("chunk"),
                        "semantic_chunk": result.get("semantic_chunk"),
                        "media_type": result.get("type"),
                        "score": result[score],
                        "reranker_score": result[reranker_score],
                        "time_weighted_relevance_score": time_weighted_relevance_score,
                        "months_difference": months_difference,
                        "release_date": release_date,
                        "id": result["id"],
                        "source": result.get("blob_path"),
                        "media_urls": result.get("img_data"),
                        "version": azure_media_info[1],
                        "system_name": azure_media_info[0],
                        "index_name": azure_integration_index_name[0],
                        "category1": result.get("category1"),
                        "category2": result.get("category2"),
                        "category3": result.get("category3"),
                        "model_code": result.get("model_code"),
                        "goods_id": result.get("goods_id"),
                        "display_seq": result.get("display_seq"),
                        "media_filter_condition": media_filter_condition,
                        "youtube_filter_condition": youtube_filter_condition,
                        "threshold": threshold,
                        "source_type": "ai_index",
                    }
                )

        # Grab the Gallery Contents from DB
        if code_filter_data:
            if country_code == "KR":
                gallery_contents = product_images.objects.filter(
                    mdl_code__in=[code["model_code"] for code in code_filter_data],
                    type="image",
                ).values(
                    "show_seq",
                    url=F("img_url"),
                    description=F("img_content"),
                    model_code=F("mdl_code"),
                )
            else:
                gallery_contents = uk_product_visual_contents.objects.filter(
                    model_code__in=[code["model_code"] for code in code_filter_data],
                    img_type="Gallery",
                    type="image",
                    size_type="XXLarge",
                ).values(
                    "url",
                    "model_code",
                    description=F("short_desc"),
                    show_seq=F("sorting_no"),
                )

            for result in gallery_contents:
                if result.get("url") and result.get("description"):
                    display_name, description_text = get_display_name_and_description(
                        result.get("model_code"), country_code
                    )
                    media_contents.append(
                        {
                            "question": value["query"],
                            "title": display_name,
                            "chunk": description_text,
                            "semantic_chunk": None,
                            "media_type": "image",
                            "score": 0,
                            "reranker_score": 0,
                            "time_weighted_relevance_score": 0,
                            "months_difference": None,
                            "release_date": None,
                            "id": None,
                            "source": None,
                            "media_urls": [result.get("url")],
                            "version": None,
                            "system_name": None,
                            "index_name": None,
                            "category1": None,
                            "category2": None,
                            "category3": None,
                            "model_code": result.get("model_code"),
                            "goods_id": None,
                            "display_seq": result.get("show_seq"),
                            "media_filter_condition": media_filter_condition,
                            "youtube_filter_condition": youtube_filter_condition,
                            "threshold": threshold,
                            "source_type": "gallery",
                        }
                    )

        all_media_ytb_results = [result for result in ai_media_ytb_results]

        for result in all_media_ytb_results:
            if result[reranker_score] > threshold:
                media_contents.append(
                    {
                        "question": value["query"],
                        "title": result.get("title"),
                        "chunk": result.get("chunk"),
                        "semantic_chunk": result.get("semantic_chunk"),
                        "media_type": "youtube",
                        "score": result[score],
                        "reranker_score": result[reranker_score],
                        "time_weighted_relevance_score": result[reranker_score],
                        "months_difference": None,
                        "release_date": None,
                        "id": result["id"],
                        "source": result.get("blob_path"),
                        "media_urls": result.get("img_data"),
                        "version": azure_media_video_info[1],
                        "system_name": azure_media_video_info[0],
                        "index_name": azure_integration_index_name[0],
                        "category1": result.get("category1"),
                        "category2": result.get("category2"),
                        "category3": result.get("category3"),
                        "model_code": result.get("model_code"),
                        "goods_id": result.get("goods_id"),
                        "display_seq": result.get("display_seq"),
                        "media_filter_condition": media_filter_condition,
                        "youtube_filter_condition": youtube_filter_condition,
                        "threshold": threshold,
                        "source_type": "ai_index",
                    }
                )

    return media_contents, success, ""


def get_media_data(message_id, count, gallery_count, timeout):
    """
    Function to get the image data from django redis cache
    and return the sorted, limited data
    """
    message_flags_cache_key = __django_cache.CacheKey.message_flags(message_id)
    message_flags_dict: dict = cache.get(message_flags_cache_key, {})
    show_supplement = message_flags_dict.get(MessageFlags.SHOW_SUPPLEMENT.value, False)
    show_media = message_flags_dict.get(MessageFlags.SHOW_MEDIA.value, False)

    if not show_supplement or not show_media:
        return {
            "success": True,
            "data": [],
            "message": f"Show supplementary info data: {show_supplement}, Show media data: {show_media}",
        }

    media_cached_data = {}
    iteration = 0
    while iteration < timeout * 2:
        media_cached_data = cache.get(__django_cache.CacheKey.media(message_id), {})
        if media_cached_data:
            break
        iteration += 1
        time.sleep(0.5)

    if not media_cached_data:
        return {
            "success": True,
            "data": [],
            "message": "No media data found",
        }

    media_contents: list = media_cached_data.get("data", [])
    success = media_cached_data.get("success", False)
    message = media_cached_data.get("message", "")

    # Grab the Gallery Contents before sorting
    media_contents_copy = media_contents.copy()
    gallery_contents = []
    for item in media_contents_copy:
        if item.get("source_type") == "gallery":
            gallery_contents.append(item)
            media_contents.remove(item)

    # Grab only the top N gallery contents of each model code group
    filtered_gallery_contents = []
    if gallery_contents:
        # Group gallery contents by model_code
        model_code_groups = {}
        for item in gallery_contents:
            model_code = item.get("model_code")
            if model_code not in model_code_groups:
                model_code_groups[model_code] = []
            model_code_groups[model_code].append(item)

        # Take only top gallery_count items from each model code group
        filtered_gallery_contents = []
        for model_code, items in model_code_groups.items():
            # Sort by time_weighted_relevance_score or any other appropriate field
            # For gallery items this might be 0, so you could add other sorting criteria
            items_sorted = items[:gallery_count]  # Take only top N items
            filtered_gallery_contents.extend(items_sorted)

    # Order all the results by score
    media_contents_sorted = sorted(
        media_contents, key=lambda x: x["time_weighted_relevance_score"], reverse=True
    )

    # Add the filtered gallery contents to the sorted media contents
    media_contents_sorted = filtered_gallery_contents + media_contents_sorted

    # Remove duplicates while preserving highest-scoring items for each unique URL
    seen_urls = set()
    unique_media_contents = []

    for item in media_contents_sorted:
        urls = item["media_urls"] if item["media_urls"] else [item["source"]]
        # Check if any URL of this item is new
        new_urls = [url for url in urls if url not in seen_urls]
        if new_urls:
            # Add all new URLs to seen set
            seen_urls.update(new_urls)
            unique_media_contents.append(item)

    # Only include one youtube video (the top scored one)
    youtube_content_found = False
    filtered_media_contents = []

    for item in unique_media_contents:
        if item["media_type"] == "youtube":
            if not youtube_content_found:
                youtube_content_found = True
                filtered_media_contents.append(item)
        else:
            filtered_media_contents.append(item)

    unique_media_contents = filtered_media_contents

    # Take the top N items
    top_contents = unique_media_contents[:count]

    # Format the output
    media_data = [
        {
            "title": item_dict["title"],
            "chunk": item_dict["chunk"],
            "img": url,
            "link": item_dict["source"],
            "media_type": item_dict["media_type"],
        }
        for item_dict in top_contents
        for url in (
            item_dict["media_urls"]
            if item_dict["media_urls"]
            else [item_dict["source"]]
        )
    ]

    # Make sure if there is Youtube media type, it is at the end
    media_data.sort(key=lambda x: x["media_type"] == "youtube")

    # Store the image data to chat log
    django_rq.run_job_high(
        update_corresponding_collection_log_by_field,
        (
            message_id,
            "supplementary_log.media",
            media_data,
        ),
        {},
    )

    return {
        "success": success,
        "data": media_data,
        "message": message,
    }


def get_display_name_and_description(model_code, country_code):
    """
    Function to get the display name and description of the product
    based on the model code and country code
    """
    if not model_code:
        return None, None

    product_info = None
    if country_code == "KR":
        product_info = (
            product_card.objects.filter(mdl_code=model_code)
            .values(display_name=F("goods_nm"), usp_text=F("usp_desc"))
            .order_by("display_name")
            .first()
        )
    else:
        product_info = (
            uk_product_card.objects.filter(model_code=model_code)
            .values("display_name", "usp_text")
            .order_by("display_name")
            .first()
        )

    if product_info:
        # Get string value for usp_text
        usp_text_data = product_info.get("usp_text") or []
        # Ensure we have a list to iterate over
        if not isinstance(usp_text_data, list):
            usp_text_data = [usp_text_data] if usp_text_data else []

        usp_text = "\n".join(
            [text for text in usp_text_data if text and isinstance(text, str)]
        )
        return product_info.get("display_name"), usp_text

    return None, None


############################# Media V2 #############################


def media_store_v2(
    object_id: ObjectId,
    product_data,
    country_code,
    site_cd,
    message_id,
    session_expiry,
    threshold=1.0,
    k=1,
):
    """
    Function to run image search and store the results in django redis cache
    This function is run using django rq worker
    """
    try:
        media_contents, success, message = media_search(
            product_data, country_code, site_cd, threshold, k
        )

        cache.store(
            __django_cache.CacheKey.media_v2(message_id),
            {"success": success, "data": media_contents, "message": message},
            session_expiry,
        )
    except Exception as e:
        __log.error(f"Error in media_store_v2: {e}")

        # Alert the error
        if VITE_OP_TYPE in ["STG", "PRD"]:
            context_data = {
                "Module": "Media Store V2",
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
            __django_cache.CacheKey.media_v2(message_id),
            {"success": False, "data": [], "message": str(e)},
            session_expiry,
        )


def get_media_data_v2(message_id, count, gallery_count, timeout):
    """
    Function to get the image data from django redis cache
    and return the sorted, limited data
    """
    message_flags_cache_key = __django_cache.CacheKey.message_flags(message_id)
    message_flags_dict: dict = cache.get(message_flags_cache_key, {})
    show_supplement = message_flags_dict.get(MessageFlags.SHOW_SUPPLEMENT.value, False)
    show_media = message_flags_dict.get(MessageFlags.SHOW_MEDIA.value, False)

    if not show_supplement or not show_media:
        return {
            "success": True,
            "data": [],
            "message": f"Show supplementary info data: {show_supplement}, Show media data: {show_media}",
        }

    media_cached_data = {}
    iteration = 0
    while iteration < timeout * 2:
        media_cached_data = cache.get(__django_cache.CacheKey.media_v2(message_id), {})
        if media_cached_data:
            break
        iteration += 1
        time.sleep(0.5)

    if not media_cached_data:
        return {
            "success": True,
            "data": [],
            "message": "No media data found",
        }

    media_contents: list = media_cached_data.get("data", [])
    success = media_cached_data.get("success", False)
    message = media_cached_data.get("message", "")

    # Grab the Gallery Contents before sorting
    media_contents_copy = media_contents.copy()
    gallery_contents = []
    for item in media_contents_copy:
        if item.get("source_type") == "gallery":
            gallery_contents.append(item)
            media_contents.remove(item)

    # Grab only the top N gallery contents of each model code group
    filtered_gallery_contents = []
    if gallery_contents:
        # Group gallery contents by model_code
        model_code_groups = {}
        for item in gallery_contents:
            model_code = item.get("model_code")
            if model_code not in model_code_groups:
                model_code_groups[model_code] = []
            model_code_groups[model_code].append(item)

        # Take only top gallery_count items from each model code group
        filtered_gallery_contents = []
        for model_code, items in model_code_groups.items():
            # Sort by time_weighted_relevance_score or any other appropriate field
            # For gallery items this might be 0, so you could add other sorting criteria
            items_sorted = items[:gallery_count]  # Take only top N items
            filtered_gallery_contents.extend(items_sorted)

    # Order all the results by score
    media_contents_sorted = sorted(
        media_contents, key=lambda x: x["time_weighted_relevance_score"], reverse=True
    )

    # Add the filtered gallery contents to the sorted media contents
    media_contents_sorted = filtered_gallery_contents + media_contents_sorted

    # Remove duplicates while preserving highest-scoring items for each unique URL
    seen_urls = set()
    unique_media_contents = []

    for item in media_contents_sorted:
        urls = item["media_urls"] if item["media_urls"] else [item["source"]]
        # Check if any URL of this item is new
        new_urls = [url for url in urls if url not in seen_urls]
        if new_urls:
            # Add all new URLs to seen set
            seen_urls.update(new_urls)
            unique_media_contents.append(item)

    # Only include one youtube video (the top scored one)
    youtube_content_found = False
    filtered_media_contents = []

    for item in unique_media_contents:
        if item["media_type"] == "youtube":
            if not youtube_content_found:
                youtube_content_found = True
                filtered_media_contents.append(item)
        else:
            filtered_media_contents.append(item)

    unique_media_contents = filtered_media_contents

    # Take the top N items
    top_contents = unique_media_contents[:count]

    # Format the output
    media_data = [
        {
            "title": item_dict["title"],
            "chunk": item_dict["chunk"],
            "img": url,
            "link": item_dict["source"],
            "media_type": item_dict["media_type"],
        }
        for item_dict in top_contents
        for url in (
            item_dict["media_urls"]
            if item_dict["media_urls"]
            else [item_dict["source"]]
        )
    ]

    # Make sure if there is Youtube media type, it is at the end
    media_data.sort(key=lambda x: x["media_type"] == "youtube")

    # Store the image data to chat log
    django_rq.run_job_high(
        update_corresponding_collection_log_by_field,
        (
            message_id,
            "supplementary_log.media",
            media_data,
        ),
        {},
    )

    return {
        "success": success,
        "data": media_data,
        "message": message,
    }


if __name__ == "__main__":
    product_data = [
        {
            "query": """아래 표는 갤럭시 S25 울트라와 갤럭시 S24 울트라의 핵심 사양과 특징을 한눈에 비교할 수 있도록 정리한 내용입니다. 각 항목마다 실제 체감되는 차이와 고객님께 도움이 될 만한 포인트를 함께 설명드릴게요.

<br><br>

| 구분                  | 갤럭시 S25 울트라                                      | 갤럭시 S24 울트라                                    |
|---------------------|---------------------------------------------------|---------------------------------------------------|
| 컬러                 | 티타늄 실버블루, 티타늄 그레이, 티타늄 화이트실버, 티타늄 블랙, (삼성닷컴/강남 전용: 티타늄 제트블랙, 제이드그린, 핑크골드) | 티타늄 실버블루, 티타늄 그레이, 티타늄 화이트실버, 티타늄 블랙, (삼성닷컴/강남 전용: 티타늄 제트블랙, 제이드그린, 핑크골드) |
| 크기/무게            | 162.8 x 77.6 x 8.2mm, 218g, 더 얇고 가벼움, 곡선형 모서리 | 162.8 x 77.6 x 8.2mm, 232g, 각진 모서리, 플랫 디스플레이 |
| 디스플레이           | 174.2mm(6.9형) QHD+ Dynamic AMOLED 2X, 3,120x1,440, 2,600nits, 1~120Hz, 코닝® 고릴라® 아머 2, 더 얇은 베젤 | 174.2mm(6.8형) QHD+ Dynamic AMOLED 2X, 3,120x1,440, 2,600nits, 1~120Hz, 코닝® 고릴라® 아머 2 |
| 프로세서(AP)         | 갤럭시용 스냅드래곤 8 Elite, Octa-Core, One UI 7, Android 15 | 갤럭시용 스냅드래곤 8 Elite, Octa-Core, One UI, Android 14 |
| 메모리/스토리지       | 12GB/16GB, 256GB/512GB/1TB (16GB+1TB는 제트블랙 한정)    | 12GB/16GB, 256GB/512GB/1TB                        |
| 배터리/충전          | 5,000mAh, 비디오 재생 최대 31시간, 65W 유선/25W 무선 초고속 충전, 효율성 개선 | 5,000mAh, 비디오 재생 최대 30시간, 45W 유선/15W 무선 충전 |
| 카메라(후면/전면)     | 광각 200MP, 초광각 50MP, 망원 50/10MP, 전면 12MP, 3/5배 광학줌, 2/10배 광학 수준 줌, 최대 100배 디지털 줌, AI ProVisual Engine, Object-aware Engine, Expert RAW | 광각 200MP, 초광각 50MP, 망원 50/10MP, 전면 12MP, 3/5배 광학줌, 2/10배 광학 수준 줌, 최대 100배 디지털 줌, AI 엔진 |
| AI 기능              | Gemini Live, Now Brief, 서클 투 서치, 노트/텍스트/통역/통화/글쓰기/포토/드로잉 어시스트, 오디오 지우개, 맞춤형 필터, 프로스케일러, One UI 7, 개인정보 보호 강화 | Gemini Live, Now Brief, 서클 투 서치, 노트/텍스트/통역/통화/글쓰기/포토/드로잉 어시스트, One UI, Knox Matrix |
| 내구성/방수          | 티타늄 프레임, 코닝® 고릴라® 아머 2, IP68, 더 향상된 내구성 | 티타늄 프레임, 코닝® 고릴라® 아머 2, IP68              |
| S펜                  | 내장, 다양한 생산성 기능, 블루투스 미지원                 | 내장, 다양한 생산성 기능, 블루투스 지원                |
| 연결성               | 5G, Wi-Fi 7, UWB 등 최신 무선 기술 지원                  | 5G, Wi-Fi 6E, UWB                                    |

---

### 세부 비교 및 고객 경험 포인트

#### 1. 디자인 & 휴대성
- **S25 울트라**는 곡선형 모서리와 얇아진 베젤, 14g 더 가벼운 무게(218g)로 장시간 사용 시 손에 감기는 느낌이 한층 부드럽고 세련됩니다. 한 손에 쏙 들어오는 그립감과 다양한 티타늄 컬러로, 스타일과 실용성을 모두 만족시켜줍니다.
- **S24 울트라**는 각진 플랫 디자인으로 S펜 사용 시 안정감이 좋으며, 묵직한 프리미엄 감성을 선호하는 분께 추천드립니다.

#### 2. 디스플레이
- **S25 울트라**는 6.9형(174.2mm)로 0.1형 더 커졌고, 베젤이 0.2mm 얇아져 몰입감이 극대화됩니다. 고릴라 아머 2와 저반사 기능으로 실내외 어디서나 선명한 화질을 경험할 수 있습니다.
- **S24 울트라**도 QHD+ 해상도와 높은 밝기를 제공해 영화, 게임, 사진 감상에 탁월합니다.

#### 3. 성능 & 저장공간
- **S25 울트라**는 최신 스냅드래곤 8 Elite 칩셋, 최대 16GB RAM, 1TB 저장공간(특정 컬러 한정)으로 멀티태스킹, 고화질 영상 편집, 대용량 데이터 관리까지 완벽하게 지원합니다.
- **S24 울트라**도 강력한 성능을 자랑하지만, 메모리 옵션과 소프트웨어 최적화 부분에서 S25 울트라가 한층 더 진화했습니다.

#### 4. 카메라 & AI
- **S25 울트라**는 업그레이드된 AI ProVisual Engine, 50MP 초광각, Object-aware Engine, Expert RAW 등으로 전문가급 사진과 영상을 손쉽게 촬영할 수 있습니다. 맞춤형 필터, 오디오 지우개 등 AI 기반 편집 기능도 대폭 강화되었습니다.
- **S24 울트라**도 2억 화소 메인 카메라와 AI 엔진, 100배 줌 등 강력한 촬영 성능을 제공합니다.

#### 5. 배터리 & 충전
- **S25 울트라**는 5,000mAh 배터리, 최대 31시간 비디오 재생, 65W 유선/25W 무선 초고속 충전으로 하루 종일 걱정 없이 사용할 수 있습니다. 전력 효율성도 한층 개선되어 더 오래, 더 빠르게 충전됩니다.
- **S24 울트라**는 5,000mAh, 최대 30시간 비디오 재생, 45W 유선/15W 무선 충전으로 충분한 사용시간을 보장합니다.

#### 6. AI & 소프트웨어
- **S25 울트라**는 One UI 7, Android 15, Gemini Live, Now Brief 등 한 단계 진화한 AI 기능과 맞춤형 브리핑, 개인정보 보호 강화로 더 똑똑하고 안전한 모바일 경험을 제공합니다.
- **S24 울트라**도 다양한 AI 어시스트와 Knox Matrix로 강력한 보안과 편의성을 갖췄습니다.

#### 7. 연결성 & 내구성
- **S25 울트라**는 Wi-Fi 7, UWB 등 최신 무선 기술로 미래지향적 환경에 최적화되어 있습니다.
- 두 모델 모두 티타늄 프레임, IP68 방수방진, 고릴라 아머 2로 뛰어난 내구성을 자랑합니다.

---

### 이런 고객님께 추천드려요

- **갤럭시 S25 울트라**: 최신 AI 기능, 더 강력한 성능, 가벼운 무게, 진화된 디자인, 전문가급 카메라와 대화면을 모두 누리고 싶은 하이엔드 사용자, 크리에이터, 비즈니스 전문가, 장기간 소프트웨어 지원을 중시하는 분
- **갤럭시 S24 울트라**: 검증된 프리미엄 성능, 플랫 디자인의 안정감, 강력한 카메라와 S펜 생산성을 원하는 분

---

두 모델 모두 프리미엄 경험을 제공하지만, S25 울트라는 한층 더 진화된 AI, 디자인, 성능, 편의성에서 특별한 만족을 선사합니다. 라이프스타일에 맞춰 선택해 보시고, 더 궁금한 점이 있다면 언제든 문의해 주세요!""",
            "category_lv1": "HHP",
            "category_lv2": "NEW RADIO MOBILE (5G SMARTPHONE)",
            "category_lv3": "Galaxy S25 Ultra",
            "code": "SM-S938NAKFKOO",
            "mapping_code": "갤럭시 S25 울트라",
            "product_division": "MX",
            "product_line": "갤럭시 스마트폰",
            "product_name": "Galaxy S25 Ultra",
        },
        {
            "query": """아래 표는 갤럭시 S25 울트라와 갤럭시 S24 울트라의 핵심 사양과 특징을 한눈에 비교할 수 있도록 정리한 내용입니다. 각 항목마다 실제 체감되는 차이와 고객님께 도움이 될 만한 포인트를 함께 설명드릴게요.

<br><br>

| 구분                  | 갤럭시 S25 울트라                                      | 갤럭시 S24 울트라                                    |
|---------------------|---------------------------------------------------|---------------------------------------------------|
| 컬러                 | 티타늄 실버블루, 티타늄 그레이, 티타늄 화이트실버, 티타늄 블랙, (삼성닷컴/강남 전용: 티타늄 제트블랙, 제이드그린, 핑크골드) | 티타늄 실버블루, 티타늄 그레이, 티타늄 화이트실버, 티타늄 블랙, (삼성닷컴/강남 전용: 티타늄 제트블랙, 제이드그린, 핑크골드) |
| 크기/무게            | 162.8 x 77.6 x 8.2mm, 218g, 더 얇고 가벼움, 곡선형 모서리 | 162.8 x 77.6 x 8.2mm, 232g, 각진 모서리, 플랫 디스플레이 |
| 디스플레이           | 174.2mm(6.9형) QHD+ Dynamic AMOLED 2X, 3,120x1,440, 2,600nits, 1~120Hz, 코닝® 고릴라® 아머 2, 더 얇은 베젤 | 174.2mm(6.8형) QHD+ Dynamic AMOLED 2X, 3,120x1,440, 2,600nits, 1~120Hz, 코닝® 고릴라® 아머 2 |
| 프로세서(AP)         | 갤럭시용 스냅드래곤 8 Elite, Octa-Core, One UI 7, Android 15 | 갤럭시용 스냅드래곤 8 Elite, Octa-Core, One UI, Android 14 |
| 메모리/스토리지       | 12GB/16GB, 256GB/512GB/1TB (16GB+1TB는 제트블랙 한정)    | 12GB/16GB, 256GB/512GB/1TB                        |
| 배터리/충전          | 5,000mAh, 비디오 재생 최대 31시간, 65W 유선/25W 무선 초고속 충전, 효율성 개선 | 5,000mAh, 비디오 재생 최대 30시간, 45W 유선/15W 무선 충전 |
| 카메라(후면/전면)     | 광각 200MP, 초광각 50MP, 망원 50/10MP, 전면 12MP, 3/5배 광학줌, 2/10배 광학 수준 줌, 최대 100배 디지털 줌, AI ProVisual Engine, Object-aware Engine, Expert RAW | 광각 200MP, 초광각 50MP, 망원 50/10MP, 전면 12MP, 3/5배 광학줌, 2/10배 광학 수준 줌, 최대 100배 디지털 줌, AI 엔진 |
| AI 기능              | Gemini Live, Now Brief, 서클 투 서치, 노트/텍스트/통역/통화/글쓰기/포토/드로잉 어시스트, 오디오 지우개, 맞춤형 필터, 프로스케일러, One UI 7, 개인정보 보호 강화 | Gemini Live, Now Brief, 서클 투 서치, 노트/텍스트/통역/통화/글쓰기/포토/드로잉 어시스트, One UI, Knox Matrix |
| 내구성/방수          | 티타늄 프레임, 코닝® 고릴라® 아머 2, IP68, 더 향상된 내구성 | 티타늄 프레임, 코닝® 고릴라® 아머 2, IP68              |
| S펜                  | 내장, 다양한 생산성 기능, 블루투스 미지원                 | 내장, 다양한 생산성 기능, 블루투스 지원                |
| 연결성               | 5G, Wi-Fi 7, UWB 등 최신 무선 기술 지원                  | 5G, Wi-Fi 6E, UWB                                    |

---

### 세부 비교 및 고객 경험 포인트

#### 1. 디자인 & 휴대성
- **S25 울트라**는 곡선형 모서리와 얇아진 베젤, 14g 더 가벼운 무게(218g)로 장시간 사용 시 손에 감기는 느낌이 한층 부드럽고 세련됩니다. 한 손에 쏙 들어오는 그립감과 다양한 티타늄 컬러로, 스타일과 실용성을 모두 만족시켜줍니다.
- **S24 울트라**는 각진 플랫 디자인으로 S펜 사용 시 안정감이 좋으며, 묵직한 프리미엄 감성을 선호하는 분께 추천드립니다.

#### 2. 디스플레이
- **S25 울트라**는 6.9형(174.2mm)로 0.1형 더 커졌고, 베젤이 0.2mm 얇아져 몰입감이 극대화됩니다. 고릴라 아머 2와 저반사 기능으로 실내외 어디서나 선명한 화질을 경험할 수 있습니다.
- **S24 울트라**도 QHD+ 해상도와 높은 밝기를 제공해 영화, 게임, 사진 감상에 탁월합니다.

#### 3. 성능 & 저장공간
- **S25 울트라**는 최신 스냅드래곤 8 Elite 칩셋, 최대 16GB RAM, 1TB 저장공간(특정 컬러 한정)으로 멀티태스킹, 고화질 영상 편집, 대용량 데이터 관리까지 완벽하게 지원합니다.
- **S24 울트라**도 강력한 성능을 자랑하지만, 메모리 옵션과 소프트웨어 최적화 부분에서 S25 울트라가 한층 더 진화했습니다.

#### 4. 카메라 & AI
- **S25 울트라**는 업그레이드된 AI ProVisual Engine, 50MP 초광각, Object-aware Engine, Expert RAW 등으로 전문가급 사진과 영상을 손쉽게 촬영할 수 있습니다. 맞춤형 필터, 오디오 지우개 등 AI 기반 편집 기능도 대폭 강화되었습니다.
- **S24 울트라**도 2억 화소 메인 카메라와 AI 엔진, 100배 줌 등 강력한 촬영 성능을 제공합니다.

#### 5. 배터리 & 충전
- **S25 울트라**는 5,000mAh 배터리, 최대 31시간 비디오 재생, 65W 유선/25W 무선 초고속 충전으로 하루 종일 걱정 없이 사용할 수 있습니다. 전력 효율성도 한층 개선되어 더 오래, 더 빠르게 충전됩니다.
- **S24 울트라**는 5,000mAh, 최대 30시간 비디오 재생, 45W 유선/15W 무선 충전으로 충분한 사용시간을 보장합니다.

#### 6. AI & 소프트웨어
- **S25 울트라**는 One UI 7, Android 15, Gemini Live, Now Brief 등 한 단계 진화한 AI 기능과 맞춤형 브리핑, 개인정보 보호 강화로 더 똑똑하고 안전한 모바일 경험을 제공합니다.
- **S24 울트라**도 다양한 AI 어시스트와 Knox Matrix로 강력한 보안과 편의성을 갖췄습니다.

#### 7. 연결성 & 내구성
- **S25 울트라**는 Wi-Fi 7, UWB 등 최신 무선 기술로 미래지향적 환경에 최적화되어 있습니다.
- 두 모델 모두 티타늄 프레임, IP68 방수방진, 고릴라 아머 2로 뛰어난 내구성을 자랑합니다.

---

### 이런 고객님께 추천드려요

- **갤럭시 S25 울트라**: 최신 AI 기능, 더 강력한 성능, 가벼운 무게, 진화된 디자인, 전문가급 카메라와 대화면을 모두 누리고 싶은 하이엔드 사용자, 크리에이터, 비즈니스 전문가, 장기간 소프트웨어 지원을 중시하는 분
- **갤럭시 S24 울트라**: 검증된 프리미엄 성능, 플랫 디자인의 안정감, 강력한 카메라와 S펜 생산성을 원하는 분

---

두 모델 모두 프리미엄 경험을 제공하지만, S25 울트라는 한층 더 진화된 AI, 디자인, 성능, 편의성에서 특별한 만족을 선사합니다. 라이프스타일에 맞춰 선택해 보시고, 더 궁금한 점이 있다면 언제든 문의해 주세요!""",
            "category_lv1": "HHP",
            "category_lv2": "NEW RADIO MOBILE (5G SMARTPHONE)",
            "category_lv3": "Galaxy S24 Ultra",
            "code": "SM5S928NLBEKOO",
            "mapping_code": "갤럭시 S24 울트라",
            "product_division": "MX",
            "product_line": "갤럭시 인증중고폰",
            "product_name": "Galaxy S24 Ultra",
        },
    ]

    message_id = str(uuid4())
    print(f"Message ID: {message_id}")
    session_expiry = 30
    country_code = "KR"
    show_supplementary_info_cache_key = __django_cache.CacheKey.message_flags(
        message_id
    )
    cache.store(
        show_supplementary_info_cache_key,
        {
            MessageFlags.SHOW_SUPPLEMENT.value: True,
            MessageFlags.SHOW_MEDIA.value: True,
        },
        session_expiry,
    )

    # Run the media store function to store the results in django redis cache
    media_store_v2(
        ObjectId(),
        product_data,
        country_code,
        "FN",
        message_id,
        session_expiry,
    )

    # Get the media data from django redis cache
    media_data = get_media_data_v2(message_id, count=10, gallery_count=2, timeout=10)

    print(f"Media Data: {media_data}")
