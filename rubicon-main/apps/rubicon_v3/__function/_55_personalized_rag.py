import sys

sys.path.append("/www/alpha/")

import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "alpha.settings")
django.setup()

import copy
import pandas as pd

from django.db.models import F
from datetime import datetime

from apps.rubicon_v3.__function.__utils import (
    get_product_line_product_name,
    get_first_or_string,
)
from apps.rubicon_v3.__external_api._11_user_info import getMyProducts
from apps.rubicon_v3.__external_api._05_product_recommend import ProductRecommend
from apps.rubicon_data.models import product_category, uk_product_spec_basics


def add_model_info(df, country_code, site_cd) -> pd.DataFrame:
    """
    Function to add model name and category information to the user product dataframe.
    """
    model_name_result = []
    model_info_dict = {}
    product_codes = df["code"].tolist()

    # Grab the appropriate model names and categories based on the country code
    if country_code == "KR":
        model_name_result = list(
            product_category.objects.filter(
                mdl_code__in=product_codes, site_cd=site_cd
            ).values(
                display_name=F("goods_nm"),
                model_code=F("mdl_code"),
                category_lv1=F("product_category_lv1"),
                category_lv2=F("product_category_lv2"),
                category_lv3=F("product_category_lv3"),
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

    # Map the model names and categories to the dataframe
    if model_name_result:
        for item in model_name_result:
            code = item.get("model_code")
            name = item.get("display_name")
            category_lv1 = item.get("category_lv1")
            category_lv2 = item.get("category_lv2")
            category_lv3 = item.get("category_lv3")
            model_info_dict[code] = {
                "model_name": name,
                "category_lv1": category_lv1,
                "category_lv2": category_lv2,
                "category_lv3": category_lv3,
            }

        df["model_name"] = df["code"].map(
            lambda x: model_info_dict.get(x, {}).get("model_name", "")
        )
        df["category_lv1"] = df["code"].map(
            lambda x: model_info_dict.get(x, {}).get("category_lv1", "")
        )
        df["category_lv2"] = df["code"].map(
            lambda x: model_info_dict.get(x, {}).get("category_lv2", "")
        )
        df["category_lv3"] = df["code"].map(
            lambda x: model_info_dict.get(x, {}).get("category_lv3", "")
        )

    return df


def check_user_product(user_product_info, country_code, site_cd, n_item=10) -> list:
    """
    Function to check and process user product information.
    """
    # Get the user product dataframe
    user_product_df = getMyProducts(user_product_info)

    if not user_product_df.empty:
        # Convert the registration timestamp to a readable date format
        user_product_df["registrationTimestamp"] = user_product_df[
            "registrationTimestamp"
        ].apply(lambda x: datetime.fromtimestamp(x / 1000).date().isoformat())

        # Rename columns for clarity
        user_product_df.columns = ["code", "model_name", "registered_date"]

        # Sort by the most recently registered products
        user_product_df = user_product_df.sort_values(
            ["registered_date"], ascending=False
        )

        # Add model information to each product
        user_product_df = add_model_info(user_product_df, country_code, site_cd)

        # Filter out products without model name again after adding model info
        user_product_df = user_product_df[
            user_product_df["model_name"].notnull()
            & (user_product_df["model_name"] != "")
        ]

        if user_product_df.empty:
            return []

        user_product_df = user_product_df.to_dict("records")[:n_item]
        return user_product_df

    else:
        return []


def process_personalized_rag(user_product_info: dict, country_code: str, site_cd: str):
    """
    Function to process personalized recommendation RAG.
    Using the latest user products of each category, get the recommendations.
    """
    import asyncio

    # Process the user product info to filter out the latest products per category
    user_product_list = check_user_product(user_product_info, country_code, site_cd)

    # If no user products, return empty list
    if not user_product_list:
        return []

    # Add product line and product name info to each user product
    for product in user_product_list:
        get_product_line_product_name(product, country_code)

    # Filter out the top products per product line
    filtered_products = []
    seen_product_lines = set()
    for product in user_product_list:
        product_line = product.get("product_line")
        if product_line and product_line not in seen_product_lines:
            filtered_products.append(product)
            seen_product_lines.add(product_line)

    # If no filtered products, return empty list
    if not filtered_products:
        return []

    # Initialize the product recommender
    recommender = ProductRecommend(country_code)

    async def fetch_recommendation(product_code):
        return await recommender.getRecommendedProduct(product_code)

    async def gather_recommendations(product_codes):
        tasks = [fetch_recommendation(code) for code in product_codes]
        return await asyncio.gather(*tasks)

    product_codes = [p["code"] for p in filtered_products]

    # If no product codes, return empty list
    if not product_codes:
        return []

    recommendations = asyncio.run(gather_recommendations(product_codes))

    # Process each recommendation
    final_recommendations = []
    for recommended_product_list in recommendations:
        # Get the list of product codes from the recommended products
        product_codes = [p["model"] for p in recommended_product_list if p.get("model")]

        # If no product codes, skip
        if not product_codes:
            continue

        # Attach model information
        recommendation_df = pd.DataFrame({"code": product_codes})
        recommendation_df = add_model_info(recommendation_df, country_code, site_cd)

        # Filter out products without model name again after adding model info
        recommendation_df = recommendation_df[
            recommendation_df["model_name"].notnull()
            & (recommendation_df["model_name"] != "")
        ]

        # If no valid recommendations, skip
        if recommendation_df.empty:
            continue

        # Get the top 3 recommendations
        processed_recommendations = recommendation_df.to_dict("records")[:3]

        # Attach the product line and product name to each recommended product
        for product in processed_recommendations:
            get_product_line_product_name(product, country_code)
            final_recommendations.append(product)

    return final_recommendations


def filter_personalized_rag(
    complement_dict: dict, personalized_rag: list, country_code: str
):
    """
    Function to filter the personalized RAG results based on the complement extended info result.
    The complement extended info result is based on ctg-rank and have the relevant product category.
    The personalized RAG results are based on all the user products.
    Personalized RAG needs to filter out the non-relevant product categories.
    """
    # Return empty list if either input is empty
    if (
        not complement_dict
        or not complement_dict.get("extended_info_result")
        or not personalized_rag
    ):
        return []

    # Figure out the product line of the extended info result
    extended_info_result_copy = copy.deepcopy(complement_dict["extended_info_result"])

    distinct_product_lines = set()
    for item in extended_info_result_copy:
        # Format the dict keys to match the expected format for product line function
        formatted_dict = {
            "code": get_first_or_string(item, "extended_info"),
            "category_lv1": get_first_or_string(item, "category_lv1"),
            "category_lv2": get_first_or_string(item, "category_lv2"),
            "category_lv3": get_first_or_string(item, "category_lv3"),
        }

        # If code is empty, skip
        if not formatted_dict["code"]:
            continue

        get_product_line_product_name(formatted_dict, country_code)
        product_line = formatted_dict.get("product_line")
        if product_line:
            distinct_product_lines.add(product_line)

    # Filter the personalized RAG results based on the product lines
    filtered_personalized_rag = [
        item
        for item in personalized_rag
        if item["product_line"] in distinct_product_lines
    ]

    # Finally format it back to the extended info result format to be replaced
    formatted_filtered_personalized_rag = [
        {
            "mapping_code": item["model_name"],
            "extended_info": [item["code"]],
            "category_lv1": item["category_lv1"],
            "category_lv2": item.get("category_lv2", ""),
            "category_lv3": item.get("category_lv3", ""),
        }
        for item in filtered_personalized_rag
    ]

    return formatted_filtered_personalized_rag


if __name__ == "__main__":
    # Example usage

    user_product_info = {
        "products": [
            {
                "serialNumber": "R3CX704TY3H",
                "productType": "Phone",
                "modelCode": "SM-F741NLGEKOO",
                "modelName": "Galaxy Z Flip6",
                "registrationTimestamp": 1750204144659,
                "category": "IMEI",
                "equipmentIds": ["350756230440516", "35105928044051"],
                "source": None,
            },
            {
                "serialNumber": "R54RB000QSY",
                "productType": "Tablet",
                "modelCode": "SM-T733NLGEKOO",
                "modelName": "Galaxy Tab S7 FE",
                "registrationTimestamp": 1748784199916,
                "category": "TWID",
                "equipmentIds": ["R54RB000QSY"],
                "source": None,
            },
            {
                "serialNumber": "RFAT72WN52R",
                "productType": "Watch",
                "modelCode": "SM-R920NZTAKOO",
                "modelName": "Galaxy Watch5 Pro",
                "registrationTimestamp": 1731394410470,
                "category": "TWID",
                "equipmentIds": ["RFAT72WN52R"],
                "source": None,
            },
            {
                "serialNumber": "0GQXPDBT300089K",
                "productType": "Air conditioner",
                "modelCode": "AR06T9170HEQ",
                "modelName": None,
                "registrationTimestamp": 1730421642362,
                "category": None,
                "equipmentIds": None,
                "source": None,
            },
            {
                "serialNumber": "RFAX80BMZGF",
                "productType": "Earbuds",
                "modelCode": "SM-R630NZAAKOO",
                "modelName": None,
                "registrationTimestamp": 1724879145250,
                "category": None,
                "equipmentIds": None,
                "source": None,
            },
            {
                "serialNumber": "R3CN808XWLE",
                "productType": "Phone",
                "modelCode": "SM-N986NZWEKOC",
                "modelName": "Samsung Galaxy Note20 Ultra 5G",
                "registrationTimestamp": 1702333166974,
                "category": "IMEI",
                "equipmentIds": ["355857113423804"],
                "source": None,
            },
            {
                "serialNumber": "BDMCP3EN601484J",
                "productType": "Air conditioner",
                "modelCode": "AF17TX772BFN",
                "modelName": None,
                "registrationTimestamp": 1651136122000,
                "category": None,
                "equipmentIds": None,
                "source": None,
            },
        ]
    }
    country_code = "KR"
    site_cd = "B2C"

    personalized_rag_results = process_personalized_rag(
        user_product_info, country_code, site_cd
    )
    print("Personalized RAG Results:", personalized_rag_results)
