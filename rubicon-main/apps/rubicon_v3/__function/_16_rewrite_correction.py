import sys

sys.path.append("/www/alpha/")

import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "alpha.settings")
django.setup()

import datetime

from typing import List
from pydantic import create_model

from apps.rubicon_v3.__function import __llm_call as llm_call
from apps.rubicon_v3.models import Prompt_Template
from apps.rubicon_v3.__external_api._11_user_info import getMyProducts
from apps.rubicon_data.models import product_category, uk_product_spec_basics


def create_corrected_query_model(input_query_list):
    """
    Creates a Pydantic model that matches the exact length of the input query list.

    Args:
        input_query_list (list): The original query list to be corrected

    Returns:
        A Pydantic model with fixed structure matching input length
    """
    if not input_query_list:
        raise ValueError("Input query list cannot be empty.")

    # Create individual query models for each input query
    query_models = []

    for i, _ in enumerate(input_query_list):
        # Create a model for this specific query item
        query_model = create_model(
            f"CorrectedQueryItem_{i}",
            corrected_query=(str, ...),
        )
        query_models.append(query_model)

    # Create field definitions for the main model
    field_definitions = {}
    for i, query_model in enumerate(query_models):
        field_definitions[f"query_{i}"] = (query_model, ...)

    # Add the keyword list field (no length restriction)
    field_definitions["re_write_keyword_list"] = (List[str], ...)
    field_definitions["no_rewrite_flag"] = (bool, ...)

    CorrectedQueryModel = create_model("CorrectedQuery", **field_definitions)

    return CorrectedQueryModel


def convert_corrected_query_result_to_original_format(corrected_result, original_count):
    """
    Converts the structured corrected result back to the original format.

    Args:
        corrected_result: The structured result from OpenAI
        original_count: Number of original queries

    Returns:
        Dict with re_write_query_list and re_write_keyword_list in original format
    """
    corrected_queries = []

    for i in range(original_count):
        query_key = f"query_{i}"
        query_item = corrected_result[query_key]
        corrected_queries.append(query_item["corrected_query"])

    return {
        "re_write_query_list": corrected_queries,
        "re_write_keyword_list": corrected_result["re_write_keyword_list"],
        "no_rewrite_flag": corrected_result["no_rewrite_flag"],
    }


def add_model_info(df, country_code, site_cd):
    model_name_result = []
    model_info_dict = {}
    product_codes = df["Model Code"].tolist()
    if country_code == "KR":
        model_name_result = list(
            product_category.objects.filter(
                mdl_code__in=product_codes, site_cd=site_cd
            ).values(
                "goods_nm",
                "mdl_code",
                "product_category_lv1",
                "product_category_lv2",
                "product_category_lv3",
            )
        )

    elif country_code == "GB":
        model_name_result = list(
            uk_product_spec_basics.objects.filter(
                model_code__in=product_codes,
                site_cd=site_cd,
            ).values(
                "display_name",
                "model_code",
                "category_lv1",
                "category_lv2",
                "category_lv3",
            )
        )

    if model_name_result:
        for item in model_name_result:
            code = item.get("mdl_code") or item.get("model_code")
            name = item.get("goods_nm") or item.get("display_name")
            category_lv1 = item.get("product_category_lv1") or item.get("category_lv1")
            category_lv2 = item.get("product_category_lv2") or item.get("category_lv2")
            category_lv3 = item.get("product_category_lv3") or item.get("category_lv3")
            model_info_dict[code] = {
                "Model Name": name,
                "category_lv1": category_lv1,
                "category_lv2": category_lv2,
                "category_lv3": category_lv3,
            }

        df["Model Name"] = df["Model Code"].map(
            lambda x: model_info_dict.get(x, {}).get("Model Name", "")
        )
        df["category_lv1"] = df["Model Code"].map(
            lambda x: model_info_dict.get(x, {}).get("category_lv1", "")
        )
        df["category_lv2"] = df["Model Code"].map(
            lambda x: model_info_dict.get(x, {}).get("category_lv2", "")
        )
        df["category_lv3"] = df["Model Code"].map(
            lambda x: model_info_dict.get(x, {}).get("category_lv3", "")
        )

    return df


def check_user_product(user_product_info, country_code, site_cd, n_item=10):
    user_product_df = getMyProducts(user_product_info)

    if not user_product_df.empty:
        user_product_result = user_product_df
        user_product_result["registrationTimestamp"] = user_product_result[
            "registrationTimestamp"
        ].apply(lambda x: datetime.datetime.fromtimestamp(x / 1000).date().isoformat())
        user_product_result.columns = ["Model Code", "Model Name", "Registered Date"]
        user_product_result = user_product_result.sort_values(
            ["Registered Date"], ascending=False
        )
        user_product_result = add_model_info(user_product_result, country_code, site_cd)
        user_product_result = user_product_result[
            user_product_result["Model Name"].notnull()
            & (user_product_result["Model Name"] != "")
        ]

        if user_product_result.empty:
            return ["no registered devices"]

        user_product_result = user_product_result.to_dict("records")[:n_item]
        return user_product_result

    else:
        return ["no registered devices"]


def re_write_correction(
    rewritten_queries: list,
    country_code: str,
    site_cd: str,
    user_product_info: dict,
    gpt_model_name: str = "gpt-4.1-mini",
    temperature: float = 0.0,
    top_p: float = 0.1,
):

    # Language mapping dictionary for prompt
    LANG_DICT = {"KR": "Korean", "GB": "English"}
    language = LANG_DICT.get(country_code, "English")

    # Get user's owned device data for prompt context
    user_owned_device_data = check_user_product(
        user_product_info, country_code, site_cd, n_item=10
    )

    # Prepare prompt template values for LLM
    load_prompt = Prompt_Template.objects.filter(
        response_type="rewrite_correction", active=True, country_code=country_code
    ).values_list("prompt", flat=True)[0]
    prompt_template_values = {
        "user_owned_device_data_placeholder": user_owned_device_data,
        "language_placeholder": language,
    }
    prompt = load_prompt % prompt_template_values

    # System message for LLM
    messages = [{"role": "system", "content": prompt}]

    user_content = []
    user_content.append({"type": "text", "text": f"{rewritten_queries}"})

    messages.append({"role": "user", "content": user_content})

    # Create the Pydantic model based on the rewritten query
    CorrectedQuery = create_corrected_query_model(rewritten_queries)

    # Call LLM and get response
    response = llm_call.open_ai_call_structured(
        gpt_model_name, messages, CorrectedQuery, temperature, top_p, 42
    )

    # Convert back to list format
    corrected_result = convert_corrected_query_result_to_original_format(
        response, len(rewritten_queries)
    )

    # Validate the length match
    if (
        not corrected_result
        or not corrected_result["re_write_query_list"]
        or len(corrected_result["re_write_query_list"]) != len(rewritten_queries)
    ):
        raise ValueError("Correction failed: No items returned or length mismatch.")

    # Confirm if rewrite failed (no rewrite happened when products existed)
    if corrected_result["no_rewrite_flag"] and user_owned_device_data != [
        "no registered devices"
    ]:
        corrected_result["rewrite_correction_failure"] = True

    return corrected_result


if __name__ == "__main__":
    rewritten_queries = ["내 핸드폰 모델 리뷰 알려줘", "내 냉장고 모델 리뷰 알려줘"]
    country_code = "KR"
    site_cd = "B2C"
    user_product_info = {
        "products": [
            {
                "serialNumber": "{enc}4AmVcYyFvu/p9qRmZMem0A==",
                "productType": "Phone",
                "modelCode": "SM-KU65UD8100FXKR",
                "modelName": "Samsung Galaxy A14 5G",
                "registrationTimestamp": 1719404221016,
                "category": "IMEI",
                "equipmentIds": ["355134280284181"],
                "source": None,
            },
            {
                "serialNumber": "{enc}H7Im4r0RXaAkFcniF/BrsA==",
                "productType": "Phone",
                "modelCode": "SM-RM70F63R2A",
                "modelName": "",
                "registrationTimestamp": 1718881342942,
                "category": "IMEI",
                "equipmentIds": ["357667080232569"],
                "source": None,
            },
        ]
    }

    corrected_rewritten_dict = re_write_correction(
        rewritten_queries,
        country_code,
        site_cd,
        user_product_info,
    )
    print(corrected_rewritten_dict)
