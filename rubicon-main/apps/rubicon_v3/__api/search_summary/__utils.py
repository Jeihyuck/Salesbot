import sys

sys.path.append("/www/alpha/")

import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "alpha.settings")
django.setup()

from django.db.models import F

from apps.rubicon_data.models import product_category, uk_product_spec_basics


def codes_to_product_dict_list(
    model_codes: list[str], country_code: str, site_cd: str
) -> list[dict]:
    """
    Convert a product category code to a dictionary with product details.
    """
    # Iterate through the model codes and fetch product category data
    product_infos = []
    for model_code in model_codes:
        product_category_data = {}
        # Get the product category data depending on the country code
        if country_code == "KR":
            product_category_data = (
                product_category.objects.filter(mdl_code=model_code, site_cd=site_cd)
                .values(
                    model_code=F("mdl_code"),
                    display_name=F("goods_nm"),
                    category_lv1=F("product_category_lv1"),
                    category_lv2=F("product_category_lv2"),
                    category_lv3=F("product_category_lv3"),
                )
                .first()
            )

        # For other countries (meaning GB)
        else:
            product_category_data = (
                uk_product_spec_basics.objects.filter(
                    model_code=model_code, site_cd=site_cd
                )
                .values(
                    "model_code",
                    "display_name",
                    "category_lv1",
                    "category_lv2",
                    "category_lv3",
                )
                .first()
            )

        # Make sure we have a valid product category data
        if not product_category_data:
            continue

        # Convert the product category data to the desired format
        product_dict = {
            "mapping_code": product_category_data.get("display_name"),
            "category_lv1": product_category_data.get("category_lv1"),
            "category_lv2": product_category_data.get("category_lv2"),
            "category_lv3": product_category_data.get("category_lv3"),
            "extended_info": [model_code],
        }

        # Add the product dictionary to the list
        product_infos.append(product_dict)

    return product_infos


if __name__ == "__main__":
    # Example usage
    model_codes = ["SM-R960NZKDWEU"]
    country_code = "GB"
    site_cd = "B2C"
    product_list = codes_to_product_dict_list(model_codes, country_code, site_cd)
    print(product_list)
