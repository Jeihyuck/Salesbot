import sys

sys.path.append("/www/alpha/")

import django
import os

from django.db import connection as conn

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "alpha.settings")
django.setup()

from typing import List, Literal
from pydantic import BaseModel, create_model, Field

from apps.rubicon_v3.__function.__prompts import standardization_prompt
from apps.rubicon_v3.__function import __llm_call
from apps.rubicon_v3.__function._20_orchestrator_NER_init import create_ner_model


def create_standardization_model(input_ner_result, country_code=None):
    """
    Creates a Pydantic model that matches the exact structure of the input NER result,
    preserving order and fields while allowing expression updates.

    Args:
        input_ner_result (list): The original NER result to be standardized
        country_code (str, optional): Country code for field validation

    Returns:
        A Pydantic model with fixed structure matching input
    """
    if not input_ner_result:
        # Fallback to original model if no input
        return create_ner_model(country_code)

    # Create individual item models for each input item
    item_models = []

    for i, item in enumerate(input_ner_result):
        field_name = item["field"]
        operator = item["operator"]

        # Create a model for this specific item with fixed field and operator
        item_model = create_model(
            f"StandardizationItem_{i}",
            expression=(str, ...),  # Only this can be updated
            field=(Literal[field_name], field_name),  # Fixed to original field
            operator=(Literal[operator], operator),  # Fixed to original operator
        )

        item_models.append(item_model)

    # Create the main standardization model with ordered items
    field_definitions = {}
    for i, item_model in enumerate(item_models):
        field_definitions[f"item_{i}"] = (item_model, ...)

    StandardizationModel = create_model("StandardizationNER", **field_definitions)

    return StandardizationModel


def convert_standardization_result_to_list(standardization_result, original_count):
    """
    Converts the structured standardization result back to the original list format.

    Args:
        standardization_result: The structured result from OpenAI
        original_count: Number of original items

    Returns:
        List of standardized NER items in original format
    """
    standardized_items = []

    for i in range(original_count):
        item_key = f"item_{i}"
        item = standardization_result[item_key]
        standardized_items.append(
            {
                "expression": item["expression"],
                "field": item["field"],
                "operator": item["operator"],
            }
        )

    return standardized_items


def compose_standardization_prompt(field_types, country_code):
    """
    Composes the standardization prompt based on field types and country code.
    Adds specific modules for product specifications, pricing, and release dates.

    Args:
        field_types (set): Set of field types found in the NER result
        country_code (str): Country code for localization

    Returns:
        str: Complete standardization prompt
    """
    final_prompt = standardization_prompt.BASE_PROMPT

    # Check for standardization need - determines if specialized modules are required
    pass_flag = not any(
        field_type in field_types
        for field_type in ["product_spec", "product_price", "product_release_date"]
    )

    # Check for field modules and add them to the prompt
    if not pass_flag:
        # Add product specification standardization module if needed
        if "product_spec" in field_types:
            product_spec_module = standardization_prompt.MODULE_PROMPTS[
                "product_spec_module"
            ][country_code]
            final_prompt += "\n" + product_spec_module

        # Add product price standardization module if needed
        if "product_price" in field_types:
            product_price_module = standardization_prompt.MODULE_PROMPTS[
                "product_price_module"
            ][country_code]
            final_prompt += "\n" + product_price_module

        # Add product release date standardization module if needed
        if "product_release_date" in field_types:
            date_module = standardization_prompt.MODULE_PROMPTS[
                "product_release_date_module"
            ][country_code]
            final_prompt += "\n" + date_module

        # Add examples and validation modules
        example_module = standardization_prompt.EXAMPLE_MODULE
        final_prompt += "\n" + example_module

        validation_module = standardization_prompt.VALIDATION_PROMPT
        final_prompt += "\n" + validation_module

    # Pass standardization - use simple pass-through module
    else:
        pass_module = standardization_prompt.PASS_MODULE
        final_prompt += "\n" + pass_module

    return final_prompt


def standardize_ner_expression(ner_result, country_code, model_name="gpt-4.1-mini"):
    """
    Standardizes NER expressions while preserving structure and order.
    Uses OpenAI's structured output to ensure consistent formatting.

    Args:
        ner_result (list): List of NER items to standardize
        country_code (str): Country code for localization
        model_name (str): OpenAI model to use for standardization

    Returns:
        list: Standardized NER result with same structure as input
    """
    if not ner_result:
        return []

    # Extract unique field types for prompt composition
    field_types = set(item["field"] for item in ner_result)
    prompt = compose_standardization_prompt(field_types, country_code)

    # Prepare prompt messages for API call
    messages = [
        {"role": "system", "content": prompt},
        {
            "role": "user",
            "content": [
                {"type": "text", "text": f"NER Result to standardize: {ner_result}"}
            ],
        },
    ]

    # Create standardization model based on input structure
    StandardizationModel = create_standardization_model(ner_result, country_code)

    # Call LLM with structured output constraints
    response = __llm_call.open_ai_call_structured(
        model_name, messages, StandardizationModel, 0.01, 0.1, 42
    )

    # Convert back to list format
    standardized_items = convert_standardization_result_to_list(
        response, len(ner_result)
    )

    # Validate standardization results
    if not standardized_items or len(standardized_items) != len(ner_result):
        raise ValueError(
            "Standardization failed: No items returned or length mismatch."
        )

    return standardized_items


if __name__ == "__main__":
    from rich import print as rich_print
    import json

    def test_ner_standardization(ner_result, country_code):
        standardized_ner_values = standardize_ner_expression(ner_result, country_code)
        ner_json = json.dumps(ner_result, indent=2, ensure_ascii=False)

        standard_json = json.dumps(
            standardized_ner_values, indent=2, ensure_ascii=False
        )

        rich_print(f"NER Result: \n {ner_json}\n")
        rich_print(f"Standardized NER Result: \n {standard_json}\n")

    # Test data
    message_id = "init_ner"
    files = ""
    message_history = []
    mentioned_products = []

    # Country code for Korean localization
    country_code = "KR"

    # Example NER results for testing different field types
    example_ner_results = [
        [
            {
                "expression": "2025년1월",
                "field": "product_release_date",
                "operator": "in",
            },
            {"expression": "TV", "field": "product_model", "operator": "in"},
            {
                "expression": "2025년 4월",
                "field": "product_release_date",
                "operator": "in",
            },
            {"expression": "TV", "field": "product_model", "operator": "in"},
        ],  # date
        [
            {"expression": "Neo QLED", "field": "product_model", "operator": "in"},
            {"expression": "75인치", "field": "product_spec", "operator": "in"},
            {"expression": "가격", "field": "product_price", "operator": "in"},
        ],  # spec
        [
            {
                "expression": "10 0 만 원",
                "field": "product_price",
                "operator": "less_than",
            },
            {"expression": "핸드폰", "field": "product_model", "operator": "in"},
        ],  # price
        [
            {
                "expression": "Chromebook 2 360",
                "field": "product_model",
                "operator": "in",
            }
        ],  # model
    ]

    for ner_result in example_ner_results:
        test_ner_standardization(ner_result, country_code)
