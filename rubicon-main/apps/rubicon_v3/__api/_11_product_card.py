import sys

sys.path.append("/www/alpha/")
import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "alpha.settings")
django.setup()

import time
import traceback

from uuid import uuid4
from bson.objectid import ObjectId

from apps.rubicon_v3.__function import __django_rq as django_rq
from apps.rubicon_v3.__function.__django_cache import (
    MessageFlags,
    DjangoCacheClient,
    CacheKey,
)
from apps.rubicon_v3.__function.definitions import channels
from apps.rubicon_v3.__api.__utils import update_corresponding_collection_log_by_field
from apps.rubicon_v3.__external_api._14_azure_email_alert import (
    send_process_error_alert,
)
from apps.rubicon_data.models import uk_product_card, product_card as kr_product_card
from alpha import __log
from alpha.settings import VITE_OP_TYPE

cache = DjangoCacheClient()


def product_card_store(
    object_id: ObjectId,
    product_card_list,
    country_code,
    channel,
    site_cd,
    message_id,
    session_expiry,
):
    """
    Function to run image search and store the results in django redis cache
    This function is run using django rq worker
    """
    try:
        product_card, success, message = product_card_search(
            product_card_list, country_code, channel, site_cd
        )

        cache.store(
            CacheKey.product_card(message_id),
            {"product_card": product_card, "success": success, "message": message},
            session_expiry,
        )
    except Exception as e:
        __log.error(f"Error in product_card_store: {e}")

        # Alert the error
        if VITE_OP_TYPE in ["STG", "PRD"]:
            context_data = {
                "Module": "Product Card",
                "Country Code": country_code,
                "Site Code": site_cd,
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
            CacheKey.product_card(message_id),
            {"product_card": [], "success": False, "message": str(e)},
            session_expiry,
        )


def get_product_info_gb(model_codes: list, channel: str, site_cd: str):
    # Message to show when not available
    not_available_message = "Unavailable Product"

    # Get the product info from the UK product card
    product_data = list(
        uk_product_card.objects.filter(
            model_code__in=model_codes, display="yes", site_cd=site_cd
        ).values()
    )

    def format_gbp(amount):
        """
        Format a numeric value as Great British Pounds (GBP) currency.

        Args:
            amount: A numeric value (int or float) or None

        Returns:
            A string formatted as GBP with comma as thousands separator and 2 decimal places,
            or None if the input is None

        Example:
            >>> format_gbp(1349)
            '£1,349.00'
            >>> format_gbp(None)
            None
        """
        if amount is None:
            return None

        return f"£{amount:,.2f}"

    required_fields = [
        "model_code",
        "display_name",
        "image_url",
        "pd_url",
    ]

    # Add to the required fields for specific channels
    if channel not in [channels.DOTCOMSEARCH]:
        required_fields.append("usp_text")
        required_fields.append("price")

    results = []
    seen_products = set()  # To avoid duplicates

    for item in product_data:
        if (
            all(item.get(field) for field in required_fields)
            and item.get("model_code") not in seen_products
        ):
            # Track seen products to avoid duplicates
            seen_products.add(item.get("model_code"))
            results.append(
                {
                    "id": item.get("model_code"),
                    "category": item.get("category_lv1"),
                    "sub_category": item.get("category_lv2"),
                    "sub_genre": item.get("category_lv3"),
                    "groupedProducts": item.get("grouped_products"),
                    "productLaunchDate": item.get("launch_date"),
                    "numberOfReviews": item.get("review_num"),
                    "productDisplayName": item.get("display_name").replace("<br>", ""),
                    "images": {
                        "largeImage": {
                            "type": "image",
                            "url": item.get("image_url"),
                            "desc": None,
                        },
                        "laImage": item.get("image_url"),
                    },
                    "msrp_price": item.get("price"),
                    "sale_price": item.get("promotion_price"),
                    "reviewRating": item.get("avg_score"),
                    "modelCode": item.get("model_code"),
                    "modelName": item.get("model_name"),
                    "pdpURL": item.get("pd_url"),
                    "uspDesc": item.get("usp_text"),
                    "msrp_price_currency": (
                        format_gbp(item.get("price"))
                        if item.get("salesstatus") == "PURCHASABLE"
                        else not_available_message
                    ),
                    "msrp_price_currency_code": "GBP",
                    "sale_price_currency": (
                        format_gbp(item.get("promotion_price"))
                        if item.get("salesstatus") == "PURCHASABLE"
                        else not_available_message
                    ),
                    "sale_price_currency_code": "GBP",
                }
            )

    return results


def get_product_info_kr(model_codes: list, channel: str, site_cd: str):
    # Message to show when not available
    not_available_message = "판매중인 제품이 아닙니다"

    # Get the product info from the KR product card
    product_data = list(
        kr_product_card.objects.filter(
            mdl_code__in=model_codes,
            goods_stat_cd__in=["20", "30"],
            show_yn="Y",
            site_cd=site_cd,
        ).values()
    )

    def format_krw(amount):
        """
        Format a numeric value as Korean Won (KRW) currency.

        Args:
            amount: A numeric value (int or float) or None

        Returns:
            A string formatted as Korean Won with comma as thousands separator,
            or None if the input is None

        Example:
            >>> format_krw(2249500)
            '2,249,500원'
            >>> format_krw(None)
            None
        """
        if amount is None:
            return None

        # Format with commas as thousand separators and add the won symbol
        return f"{amount:,}원"

    required_fields = [
        "mdl_code",
        "goods_nm",
        "img_url",
        "pd_url",
    ]

    # Add to the required fields for specific channels
    if channel not in [channels.DOTCOMSEARCH]:
        required_fields.append("usp_desc")
        required_fields.append("sale_prc1")

    results = []
    seen_products = set()  # To avoid duplicates

    for item in product_data:
        if (
            all(item.get(field) for field in required_fields)
            and item.get("mdl_code") not in seen_products
        ):
            # Track seen products to avoid duplicates
            seen_products.add(item.get("mdl_code"))
            results.append(
                {
                    "id": item.get("mdl_code"),
                    "category": item.get("disp_lv1"),
                    "sub_category": item.get("disp_lv2"),
                    "sub_genre": item.get("disp_lv3"),
                    "groupedProducts": item.get("grouped_products"),
                    "productLaunchDate": item.get("release_date"),
                    "numberOfReviews": item.get("review_num"),
                    "productDisplayName": item.get("goods_nm").replace("<br>", ""),
                    "images": {
                        "largeImage": {
                            "type": "image",
                            "url": item.get("img_url"),
                            "desc": None,
                        },
                        "laImage": item.get("img_url"),
                    },
                    "msrp_price": item.get("sale_prc1"),
                    "sale_price": item.get("sale_prc3"),
                    "reviewRating": item.get("estm_score"),
                    "modelCode": item.get("mdl_code"),
                    "modelName": item.get("model_name"),
                    "pdpURL": item.get("pd_url"),
                    "uspDesc": item.get("usp_desc"),
                    "msrp_price_currency": (
                        format_krw(item.get("sale_prc1"))
                        if item.get("goods_stat_cd") == "30"
                        else not_available_message
                    ),
                    "msrp_price_currency_code": "KRW",
                    "sale_price_currency": (
                        format_krw(item.get("sale_prc3"))
                        if item.get("goods_stat_cd") == "30"
                        else not_available_message
                    ),
                    "sale_price_currency_code": "KRW",
                }
            )

    return results


def product_card_search(product_card_list, country_code, channel, site_cd):
    """
    Function to search for the product card images
    """
    product_codes = [
        product_card["code"]
        for product_card in product_card_list
        if product_card.get("code")
    ]

    # If product codes are not present, return empty list
    if not product_codes:
        return [], True, "No product codes found"

    # Get the product info
    product_infos = None
    if country_code == "KR":
        product_infos = get_product_info_kr(product_codes, channel, site_cd)
    else:
        product_infos = get_product_info_gb(product_codes, channel, site_cd)

    if not product_infos:
        return [], True, "No product info found"

    # Order the product infos based on the input product card list
    product_infos_ordered = []
    for product_code in product_codes:
        # Find the product info with the matching model code
        matching_product = next(
            (product for product in product_infos if product["id"] == product_code),
            None,
        )
        if matching_product:
            product_infos_ordered.append(matching_product)

    return product_infos_ordered, True, ""


def get_product_card_data(message_id, count, timeout):
    """
    Function to get the product card data from the cache
    """
    message_flags_cache_key = CacheKey.message_flags(message_id)
    message_flags_dict: dict = cache.get(message_flags_cache_key, {})
    show_supplement = message_flags_dict.get(MessageFlags.SHOW_SUPPLEMENT.value, False)
    show_product_card = message_flags_dict.get(
        MessageFlags.SHOW_PRODUCT_CARD.value, False
    )

    if not show_supplement or not show_product_card:
        return {
            "success": True,
            "data": [],
            "message": f"Show supplementary info data: {show_supplement}, Show product card data: {show_product_card}",
        }

    product_card_cached_data = {}
    iteration = 0
    while iteration < timeout * 2:
        product_card_cached_data = cache.get(CacheKey.product_card(message_id), {})
        if product_card_cached_data:
            break
        iteration += 1
        time.sleep(0.5)

    if not product_card_cached_data:
        return {"success": True, "data": [], "message": "No product card data found"}

    product_card = product_card_cached_data.get("product_card", [])
    success = product_card_cached_data.get("success", False)
    message = product_card_cached_data.get("message", "")

    top_product_card = product_card[:count]

    # Store the product card data to chat log
    django_rq.run_job_high(
        update_corresponding_collection_log_by_field,
        (
            message_id,
            "supplementary_log.product_card",
            top_product_card,
        ),
        {},
    )

    return {
        "success": success,
        "data": top_product_card,
        "message": message,
    }


############################# Product Card V2 #############################


def product_card_store_v2(
    object_id: ObjectId,
    product_card_list,
    country_code,
    channel,
    site_cd,
    message_id,
    session_expiry,
):
    """
    Function to run product card search and store the results in django redis cache
    This function is run using django rq worker
    """
    try:
        product_card, success, message = product_card_search(
            product_card_list, country_code, channel, site_cd
        )

        __log.info(
            f"Product Card V2 Store: {len(product_card)} products found for message_id: {message_id}"
        )
        cache.store(
            CacheKey.product_card_v2(message_id),
            {"product_card": product_card, "success": success, "message": message},
            session_expiry,
        )
    except Exception as e:
        __log.error(f"Error in product_card_store_v2: {e}")

        # Alert the error
        if VITE_OP_TYPE in ["STG", "PRD"]:
            context_data = {
                "Module": "Product Card V2",
                "Country Code": country_code,
                "Site Code": site_cd,
                "Object ID": str(object_id),
                "Message ID": message_id,
            }
            send_process_error_alert(
                str(e),
                "process_error",
                error_traceback=traceback.format_exc(),
                context_data=context_data,
            )

        # Store the error message in the cache
        cache.store(
            CacheKey.product_card_v2(message_id),
            {"product_card": [], "success": False, "message": str(e)},
            session_expiry,
        )


def get_product_card_data_v2(message_id, count, timeout):
    """
    Function to get the product card data from the cache for version 2
    """
    message_flags_cache_key = CacheKey.message_flags(message_id)
    message_flags_dict: dict = cache.get(message_flags_cache_key, {})
    show_supplement = message_flags_dict.get(MessageFlags.SHOW_SUPPLEMENT.value, False)
    show_product_card = message_flags_dict.get(
        MessageFlags.SHOW_PRODUCT_CARD.value, False
    )

    if not show_supplement or not show_product_card:
        return {
            "success": True,
            "data": [],
            "message": f"Show supplementary info data: {show_supplement}, Show product card data: {show_product_card}",
        }

    product_card_cached_data = {}
    iteration = 0
    while iteration < timeout * 2:
        product_card_cached_data = cache.get(CacheKey.product_card_v2(message_id), {})
        if product_card_cached_data:
            break
        iteration += 1
        time.sleep(0.5)

    if not product_card_cached_data:
        return {"success": True, "data": [], "message": "No product card data found"}

    product_card = product_card_cached_data.get("product_card", [])
    success = product_card_cached_data.get("success", False)
    message = product_card_cached_data.get("message", "")

    top_product_card = product_card[:count]

    # Store the product card data to chat log
    django_rq.run_job_high(
        update_corresponding_collection_log_by_field,
        (
            message_id,
            "supplementary_log.product_card",
            top_product_card,
        ),
        {},
    )

    return {
        "success": success,
        "data": top_product_card,
        "message": message,
    }


if __name__ == "__main__":
    # product_card_list = [
    #     {
    #         "code": "KQ43QF7A-NSW",
    #         "mapping_code": "2025 무빙스타일 QLED 화이트",
    #         "category_lv1": "Flat Panel Displayer",
    #         "category_lv2": "QLED TV",
    #         "category_lv3": "Moving Style",
    #         "product_name": "Moving Style",
    #         "product_line": "TV",
    #     },
    #     {
    #         "code": "KQ85QF8AAFXKR",
    #         "mapping_code": "2025 QLED 4K QF8A",
    #         "category_lv1": "Flat Panel Displayer",
    #         "category_lv2": "QLED TV",
    #         "category_lv3": "QLED",
    #         "product_name": "QLED",
    #         "product_line": "TV",
    #     },
    #     {
    #         "code": "KQ85LSF03-WT",
    #         "mapping_code": "2025 The Frame Pro 플랫 화이트 베젤",
    #         "category_lv1": "Flat Panel Displayer",
    #         "category_lv2": "QLED TV",
    #         "category_lv3": "The Frame Pro",
    #         "product_name": "The Frame Pro",
    #         "product_line": "TV",
    #     },
    # ]
    # message_id = str(uuid4())
    # print(f"Message ID: {message_id}")
    # session_expiry = 30
    # country_code = "KR"
    # show_supplementary_info_cache_key = CacheKey.message_flags(message_id)
    # cache.store(
    #     show_supplementary_info_cache_key,
    #     {
    #         MessageFlags.SHOW_SUPPLEMENT.value: True,
    #         MessageFlags.SHOW_PRODUCT_CARD.value: True,
    #     },
    #     session_expiry,
    # )
    # product_card_store(product_card_list, country_code, message_id, session_expiry)
    # product_card = get_product_card_data(message_id, 3, 5)
    # print(f"Product Card: {product_card}")

    ############## TEST PRODUCT CARD V2 ##############
    product_card_list = [
        {
            "query": "갤럭시 Z 플립 시리즈는 삼성의 프리미엄 폴더블 스마트폰 라인업으로, 자신만의 스타일과 개성을 중요시하는 고객님께 적극 추천드릴 수 있는 제품입니다. 특히 20~30대 여성 고객층. . .",
            "code": "SM-F766NLGAKOO",
            "mapping_code": "갤럭시 Z 플립7",
            "category_lv1": "HHP",
            "category_lv2": "NEW RADIO MOBILE (5G SMARTPHONE)",
            "category_lv3": "Galaxy Z Flip7",
            "product_name": "Galaxy Z Flip7",
            "product_line": "갤럭시 스마트폰",
            "product_division": ["MX"],
        }
    ]
    object_id = ObjectId()
    message_id = str(uuid4())
    print(f"Message ID: {message_id}")
    session_expiry = 30
    country_code = "KR"
    channel = channels.DOTCOMSEARCH
    site_cd = "B2C"
    show_supplementary_info_cache_key = CacheKey.message_flags(message_id)
    cache.store(
        show_supplementary_info_cache_key,
        {
            MessageFlags.SHOW_SUPPLEMENT.value: True,
            MessageFlags.SHOW_PRODUCT_CARD.value: True,
        },
        session_expiry,
    )
    product_card_store_v2(
        object_id,
        product_card_list,
        country_code,
        channel,
        site_cd,
        message_id,
        session_expiry,
    )
    product_card = get_product_card_data_v2(message_id, 3, 5)
    print(f"Product Card: {product_card}")
