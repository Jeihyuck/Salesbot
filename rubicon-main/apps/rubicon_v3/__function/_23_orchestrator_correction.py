import sys

sys.path.append("/www/alpha/")

import django
import os

import re
import pandas as pd
from django.db import connection as conn

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "alpha.settings")
django.setup()

from apps.rubicon_v3.models import Managed_Word
from alpha.settings import VITE_OP_TYPE
from django.core.cache import cache

from apps.rubicon_v3.__function import (
    _20_orchestrator_NER_init,
    _21_orchestrator_query_analyzer,
    _22_orchestrator_intelligence,
)
from apps.rubicon_v3.__function.definitions import (
    intelligences,
    channels,
    ner_fields as field_names,
)


def regex_pattern(word):
    """
    Create a regex pattern for word matching with wildcard support.

    Args:
        word (str): Input word that may contain wildcards (*)

    Returns:
        str: Regex pattern with word boundaries and wildcard expansion
    """
    escaped = re.escape(word).replace("\\*", ".*")
    return f"\\b{escaped}\\b"


# NER (Named Entity Recognition) Functions
def managed_word_ner(initial_ner_values):
    """
    Apply managed word filtering to NER results.
    Processes deletion, field replacement, and partial deletion of words based on database rules.

    Args:
        initial_ner_values (list): List of NER entities with expression, field, and operator

    Returns:
        list: Filtered NER results after applying managed word rules
    """

    # Fetch deletion words from database
    df_filtering_word = pd.DataFrame(
        list(
            Managed_Word.objects.filter(active=True)
            .filter(module="NER")
            .filter(processing="delete")
            .all()
            .values("word", "type")
        )
    )

    # Fetch field replacement words from database
    df_replace_field = pd.DataFrame(
        list(
            Managed_Word.objects.filter(active=True)
            .filter(module="NER")
            .filter(processing="replace_field")
            .all()
            .values("word", "type", "replace_word")
        )
    )

    # Fetch partial deletion words from database
    df_part_filtering_word = pd.DataFrame(
        list(
            Managed_Word.objects.filter(active=True)
            .filter(module="NER")
            .filter(processing="part_delete")
            .all()
            .values("word", "type")
        )
    )

    # Sort by word length (longest first) to prevent substring conflicts
    df_part_filtering_word = (
        df_part_filtering_word.assign(
            word_length=df_part_filtering_word["word"].str.len()
        )
        .sort_values(by="word_length", ascending=False)
        .drop(columns=["word_length"])
    )

    # Process each NER entity through filtering pipeline
    filtered_response = []
    for index, item in enumerate(initial_ner_values):
        expression = item["expression"]
        field = item["field"]

        # Initialize processing flags
        should_delete = False
        should_replace_field = False
        new_field = None

        # Step 1: Check for complete deletion
        for _, row in df_filtering_word.iterrows():
            word_pattern = row["word"]

            # Handle wildcard patterns
            if "*" in word_pattern and field == row["type"]:
                pattern = regex_pattern(word_pattern)
                if re.match(f"^{pattern}$", expression):
                    should_delete = True
                    break
            # Handle exact matches
            elif expression == row["word"] and field == row["type"]:
                should_delete = True
                break

        # Step 2: Check for field replacement (only if not marked for deletion)
        if not should_delete:
            for _, row in df_replace_field.iterrows():
                if row["word"] in expression and field == row["type"]:
                    should_replace_field = True
                    new_field = row["replace_word"]
                    break

        # Step 3: Apply partial deletion (only if not marked for complete deletion)
        if not should_delete:
            modified_expression = expression

            for _, row in df_part_filtering_word.iterrows():
                part_word = row["word"]
                part_type = row["type"]

                if field == part_type:
                    # Skip if expression exactly matches the part word
                    if expression == part_word:
                        pass
                    else:
                        # Handle wildcard patterns for partial removal
                        if "*" in part_word:
                            pattern = regex_pattern(part_word)
                            matches = re.finditer(pattern, modified_expression)

                            # Remove matches in reverse order to preserve indices
                            for match in reversed(list(matches)):
                                start, end = match.span()
                                modified_expression = (
                                    modified_expression[:start]
                                    + modified_expression[end:]
                                ).strip()
                        elif part_word.startswith("^"):
                            if modified_expression.startswith(part_word.lstrip("^")):
                                modified_expression = modified_expression.replace(
                                    part_word.lstrip("^"), ""
                                ).strip()
                            else:
                                pass
                        else:
                            # Simple string replacement for exact matches
                            if part_word in modified_expression:
                                modified_expression = modified_expression.replace(
                                    part_word, ""
                                ).strip()

            # Update the expression with modifications
            item["expression"] = modified_expression

            # Apply field replacement if needed
            if should_replace_field:
                item["field"] = new_field

            # Only include items with non-empty expressions
            if modified_expression:
                filtered_response.append(item)

    return filtered_response


def correct_ner(ner_result, intelligence_result, country_code):
    """
    Apply business logic corrections to NER results.

    Args:
        ner_result (list): List of NER entities
        intelligence_result (str): Detected intelligence type
        country_code (str): Country code for localization

    Returns:
        list: Corrected NER results
    """

    corrected_ner_result = ner_result

    # Requirement #1 - Change to product_model if intelligence is not product_recommendation
    # Currently commented out - would change product_accessory to product_model
    # if intelligence_result != intelligences.PRODUCT_RECOMMENDATION:
    #    for item in corrected_ner_result:
    #        if item["field"] == field_names.PRODUCT_ACCESSORY:
    #            item["field"] = field_names.PRODUCT_MODEL

    # Requirement #2 - Change to product_model only accessory is present
    # Currently commented out - would change lonely accessories to models
    # if intelligence_result == intelligences.PRODUCT_RECOMMENDATION:
    #    has_product_model = any(
    #        item["field"] == field_names.PRODUCT_MODEL for item in corrected_ner_result
    #    )
    #    if not has_product_model:
    #        for item in corrected_ner_result:
    #            if item["field"] == field_names.PRODUCT_ACCESSORY:
    #                item["field"] = field_names.PRODUCT_MODEL

    # Requirement #3 - Fix product_model / product_option division for high level products
    # Define high-level Samsung product model names (Korean)
    high_level_model_list = [
        "The Frame",
        "The Frame pro",
        "OLED",
        "Crystal UHD",
        "The Sero",
        "The Serif",
        "The Premiere",
        "무빙스타일",
        "Q시리즈 사운드바",
        "슈퍼 슬림 사운드바",
        "S시리즈 사운드바",
        "사운드바",
        "뮤직 프레임",
        "Bespoke AI 하이브리드",
        "Bespoke AI 패밀리허브",
        "Bespoke 냉장고",
        "Infinite AI 냉장고",
        "Infinite AI 냉동고",
        "Infinite Line 와인냉장고",
        "Bespoke AI 스팀",
        "Bespoke 스팀",
        "Bespoke AI 제트",
        "Bespoke AI 제트 Lite",
        "Bespoke 슬림",
        "파워모션",
        "Infinite AI 공기청정기",
        "Bespoke AI 무풍콤보 갤러리",
        "Bespoke AI 무풍 갤러리",
        "Bespoke AI 무풍 클래식",
        "무풍 클래식",
        "AI Q9000",
        "Q9000",
        "AI 무풍콤보",
        "윈도우핏",
        "통버블 세탁기",
        "아기사랑",
        "Bespoke AI 세탁기",
        "AI 세탁기",
        "Bespoke AI 건조기",
        "AI 건조기",
        "Bespoke AI 원바디",
        "Bespoke AI 콤보",
        "Bespoke 인덕션",
        "Bespoke AI 인덕션",
        "전기레인지 올 인덕션",
        "The Plate",
        "Infinite AI 인덕션",
        "Infinite Line 인덕션",
        "Bespoke TV",
    ]

    # Brand name mapping from Korean to English
    brand_mapping = {
        "비스포크": "Bespoke",
        "인피니트": "Infinite",
        "인피니트 라인": "Infinite Line",
        "Infinite 라인": "Infinite Line",
        "더 프레임": "The Frame",
        "더 세로": "The Sero",
        "더 세리프": "The Serif",
        "더 프리미어": "The Premiere",
        "더 플레이트": "The Plate",
    }

    # Create normalized versions for comparison (lowercase, no spaces)
    brand_mapping_no_space = {
        k.lower().replace(" ", ""): v.lower().replace(" ", "")
        for k, v in brand_mapping.items()
    }
    high_level_model_list_no_space = [
        model.lower().replace(" ", "") for model in high_level_model_list
    ]

    def normalize_expression(expr):
        """
        Normalize expression by removing spaces and applying brand mapping.

        Args:
            expr (str): Expression to normalize

        Returns:
            str: Normalized expression
        """
        # Remove spaces and convert to lowercase
        expr_no_space = expr.lower().replace(" ", "")

        # Check if it starts with any Korean brand name and replace with English
        for korean_no_space, english_no_space in brand_mapping_no_space.items():
            if expr_no_space.startswith(korean_no_space):
                # Replace Korean brand with English equivalent
                return english_no_space + expr_no_space[len(korean_no_space) :]

        # If no mapping found, return as is
        return expr_no_space

    # Find product_option items that might need to be changed to product_model
    option_indices = [
        i
        for i, item in enumerate(corrected_ner_result)
        if item["field"] == field_names.PRODUCT_OPTION
    ]
    items_to_change = []

    # Process each product_option
    for idx in option_indices:
        option_expr = corrected_ner_result[idx]["expression"]
        option_operator = corrected_ner_result[idx].get("operator", "in")
        normalized_option = normalize_expression(option_expr)

        # Check if the option itself is a high-level model
        if normalized_option in high_level_model_list_no_space:
            # Change to product_model without removing
            items_to_change.append((idx, "CHANGE_TO_MODEL", None))
            continue

        # Only proceed with combinations if the option operator is 'in'
        if option_operator != "in":
            continue

        # Check combinations with existing product_models
        model_indices = [
            i
            for i, item in enumerate(corrected_ner_result)
            if item["field"] == field_names.PRODUCT_MODEL
        ]
        combination_found = False

        for model_idx in model_indices:
            model_expr = corrected_ner_result[model_idx]["expression"]
            model_operator = corrected_ner_result[model_idx].get("operator", "in")

            # Only combine if both operators are 'in'
            if model_operator != "in":
                continue

            # Try both order combinations: model+option and option+model
            combo1 = f"{model_expr} {option_expr}"
            combo2 = f"{option_expr} {model_expr}"

            normalized_combo1 = normalize_expression(combo1)
            normalized_combo2 = normalize_expression(combo2)

            # Check if either combination matches a high-level model
            if normalized_combo1 in high_level_model_list_no_space:
                items_to_change.append((model_idx, "UPDATE_MODEL", combo1))
                items_to_change.append((idx, "REMOVE", None))
                combination_found = True
                break
            elif normalized_combo2 in high_level_model_list_no_space:
                items_to_change.append((model_idx, "UPDATE_MODEL", combo2))
                items_to_change.append((idx, "REMOVE", None))
                combination_found = True
                break

        if combination_found:
            continue

    # Apply all the changes collected above
    indices_to_remove = []
    for idx, action, value in items_to_change:
        if action == "CHANGE_TO_MODEL":
            corrected_ner_result[idx]["field"] = field_names.PRODUCT_MODEL
        elif action == "UPDATE_MODEL":
            corrected_ner_result[idx]["expression"] = value
        elif action == "REMOVE":
            indices_to_remove.append(idx)

    # Remove marked items (do this last to preserve indices)
    if indices_to_remove:
        corrected_ner_result = [
            item
            for i, item in enumerate(corrected_ner_result)
            if i not in indices_to_remove
        ]

    # Requirement #4 - Change short product_code to product_model
    # If product code is less than 8 characters, it's likely a model name instead
    for item in corrected_ner_result:
        if item["field"] == field_names.PRODUCT_CODE and len(item["expression"]) < 8:
            item["field"] = field_names.PRODUCT_MODEL

    # Requirement #5 - Clean up expressions for 'about' operator
    # Remove uncertainty indicators from approximate queries
    operator_partial_remove_words = [
        "대",  # "about" (Korean)
        "정도",  # "approximately" (Korean)
        "정도 되는",  # "around that much" (Korean)
        "정도 하는",  # "about that much" (Korean)
        "about",  # "about" (English)
        "around",  # "around" (English)
    ]

    # Clean expressions for product specs and prices with 'about' operator
    for item in corrected_ner_result:
        if item["operator"] == "about" and item["field"] in [
            field_names.PRODUCT_SPEC,
            field_names.PRODUCT_PRICE,
        ]:
            original_expression = item["expression"]
            modified_expression = original_expression

            # Remove uncertainty words
            for remove_word in operator_partial_remove_words:
                if remove_word in modified_expression:
                    modified_expression = modified_expression.replace(
                        remove_word, ""
                    ).strip()

                    # Clean up extra spaces
                    modified_expression = " ".join(modified_expression.split())

            # Update the expression if it was modified and is not empty
            if modified_expression and modified_expression != original_expression:
                item["expression"] = modified_expression

    # Requirement #6 - Normalize product codes to uppercase
    for item in corrected_ner_result:
        if item["field"] == field_names.PRODUCT_CODE:
            item["expression"] = item["expression"].upper()

    # Requirement #7 - Add wall mount information for Korean QLED/UHD TVs
    # For Korean market, automatically add wall mount options to TV models
    if country_code == "KR":
        # Wall mount expressions (Korean)
        wall_mount_expressions = [
            "벽걸이",  # "wall mount"
            "벽걸이형",  # "wall mount type"
            "풀 모션",  # "full motion"
            "풀 모션 슬림핏",  # "full motion slim fit"
            "풀 모션 슬림핏 벽걸이형",  # "full motion slim fit wall mount type"
        ]
        TV_expressions = ["QLED", "UHD"]  # TV type indicators

        # Find product_option items that contain wall mount expressions
        wall_mount_options = []
        product_options = []

        # Collect all product_option expressions
        for item in corrected_ner_result:
            if item["field"] == field_names.PRODUCT_OPTION:
                product_options.append(item["expression"])

        # Check individual options for wall mount expressions
        for item in corrected_ner_result:
            if item["field"] == field_names.PRODUCT_OPTION:
                for wall_mount_expr in wall_mount_expressions:
                    if wall_mount_expr in item["expression"]:
                        wall_mount_options.append(item["expression"])
                        break

        # Check combined options for wall mount expressions
        if len(product_options) > 1:
            combined_options = " ".join(product_options)
            for wall_mount_expr in wall_mount_expressions:
                if (
                    wall_mount_expr in combined_options
                    and combined_options not in wall_mount_options
                ):
                    wall_mount_options.append(combined_options)
                    break

        # Process product_model items for TV enhancement
        for item in corrected_ner_result:
            if item["field"] == field_names.PRODUCT_MODEL:
                model_expression = item["expression"]
                model_expression_lower = model_expression.lower()

                # Check if model contains TV expressions (case insensitive)
                has_tv_expression = any(
                    tv_expr.lower() in model_expression_lower
                    for tv_expr in TV_expressions
                )

                if has_tv_expression:
                    # Skip if it's a bundle/set product (contains '+')
                    if "+" in model_expression:
                        continue

                    # Check if model already contains wall mount expressions
                    already_has_wall_mount = any(
                        wall_mount_expr in model_expression
                        for wall_mount_expr in wall_mount_expressions
                    )

                    # Add wall mount expression if not already present
                    if not already_has_wall_mount:
                        # Add wall mount expression from product_option if available
                        for option_expr in wall_mount_options:
                            # Check if option expression is not already in model
                            if option_expr not in model_expression:
                                item["expression"] = f"{model_expression} {option_expr}"
                                break

    return corrected_ner_result


# Intelligence Triage Corrections
def correct_intelligence_triage(ner_result, intelligence_result, country_code):
    """
    Apply corrections to intelligence classification based on NER results.

    Args:
        ner_result (list): Corrected NER results
        intelligence_result (str): Original intelligence classification
        country_code (str): Country code for localization

    Returns:
        str: Corrected intelligence classification
    """
    ner_result = ner_result
    intelligence_result = intelligence_result

    # Extract fields and expressions for analysis
    ner_fields = [item["field"] for item in ner_result]
    ner_expressions = [item["expression"] for item in ner_result]

    # Requirement #1 - Promotions trigger buy information intelligence
    if field_names.PROMOTION_NAME in ner_fields:
        intelligence_result = intelligences.BUY_INFORMATION

    # Requirement #2 - Split payment triggers buy information intelligence
    if field_names.SPLIT_PAY in ner_fields:
        intelligence_result = intelligences.BUY_INFORMATION

    # Requirement #3 - Payment methods for GB market trigger buy information
    if country_code == "GB":
        payment_methods = ["klarna", "paypal", "samsung finance"]
        for payment in payment_methods:
            if any(payment.lower() in expr.lower() for expr in ner_expressions):
                intelligence_result = intelligences.BUY_INFORMATION
                break

    # Requirement #4 - Service centers trigger service and repair (DEPRECATED)
    # This requirement is temporarily disabled
    # Service center queries now go to store information with service center sub-intelligence
    # Example: "How much does Galaxy S24 repair cost at service center?" -> Service and repair

    # Temporarily DEPRECATED, send to intelligence: store information / sub_intelligence: service center
    # if country_code == "KR" and field_names.SERVICE_CENTER in ner_fields:
    #    intelligence_result = intelligences.SERVICE_AND_REPAIR_GUIDE

    # Requirement #5 - Return/exchange/refund policies trigger purchase policy (DEPRECATED)
    # This requirement is currently commented out
    # Korean terms: 환불(refund), 교환(exchange), 반품(return)
    # if any(word in expr for expr in ner_expressions for word in ["환불", "교환", "반품"]):
    #    intelligence_result = intelligences.PURCHASE_POLICY

    return intelligence_result


# Query Analyzer Corrections
def correct_query_analyzer(
    ner_result, intelligence_result, analyzer_result, country_code
):
    """
    Apply corrections to query analysis based on NER and intelligence results.

    Args:
        ner_result (list): Corrected NER results
        intelligence_result (str): Corrected intelligence classification
        analyzer_result (dict): Original query analysis results
        country_code (str): Country code for localization

    Returns:
        dict: Corrected query analysis results
    """
    ner_result = ner_result
    intelligence_result = intelligence_result
    analyzer_result = analyzer_result

    # Extract fields and expressions for analysis
    ner_fields = [item["field"] for item in ner_result]
    ner_expressions = [item["expression"] for item in ner_result]

    # Requirement #1 - Promotion queries require deep RAG processing
    if (
        intelligence_result == intelligences.BUY_INFORMATION
        and field_names.PROMOTION_NAME in ner_fields
    ):
        analyzer_result["RAG_depth"] = (
            _21_orchestrator_query_analyzer.RAGDepth.DEEP.value
        )

    # Requirement #2 - Product model queries require deep processing
    # Based on intelligence classification
    product_intelligences = [
        intelligences.PRODUCT_DESCRIPTION,  # Product description queries
        intelligences.PRODUCT_RECOMMENDATION,  # Product recommendation queries
        intelligences.PRODUCT_COMPARISON,  # Product comparison queries
    ]

    # Both product_model and product_code trigger deep processing
    if intelligence_result in product_intelligences:
        if (
            field_names.PRODUCT_MODEL in ner_fields
            or field_names.PRODUCT_CODE in ner_fields
        ):
            analyzer_result["RAG_depth"] = (
                _21_orchestrator_query_analyzer.RAGDepth.DEEP.value
            )

    # Requirement #3 - Accessories/consumables queries require deep processing (DEPRECATED)
    # It was previously used to set deep RAG depth for accessories/consumables queries
    # NER does not support product_accessory anymore, so this is commented out
    # if (
    #    analyzer_result["query_type"]
    #    == _21_orchestrator_query_analyzer.QueryType.ACCESSORIES_CONSUMABLES.value
    # ):
    #    analyzer_result["RAG_depth"] = (
    #        _21_orchestrator_query_analyzer.RAGDepth.DEEP.value
    #    )

    return analyzer_result


def correction(
    ner_result: list,
    intelligence_result: str,
    analyzer_result: dict,
    channel: str,
    country_code: str,
):
    """
    Main correction function that applies all correction steps in sequence.

    Args:
        ner_result (list): Original NER results
        intelligence_result (str): Original intelligence classification
        analyzer_result (dict): Original query analysis results
        channel (str): Channel type for specific corrections
        country_code (str): Country code for localization

    Returns:
        tuple: (corrected_ner_result, corrected_intelligence_result, corrected_analyzer_result)
    """

    # Step 1: Apply managed word filtering and NER corrections
    ner_result = managed_word_ner(ner_result)
    ner_result = correct_ner(ner_result, intelligence_result, country_code)

    # Step 2: Correct intelligence classification using corrected NER
    intelligence_result = correct_intelligence_triage(
        ner_result, intelligence_result, country_code
    )

    # Step 3: Correct query analysis using corrected NER and intelligence
    analyzer_result = correct_query_analyzer(
        ner_result, intelligence_result, analyzer_result, country_code
    )

    # TEMPORARY: SEND ALL RETAIL KX TO DEEP
    if channel == channels.RETAIL_KX:
        analyzer_result["RAG_depth"] = (
            _21_orchestrator_query_analyzer.RAGDepth.DEEP.value
        )

    # Note: Analyzer depends on intelligence, so intelligence correction must come first

    return ner_result, intelligence_result, analyzer_result


# Test and Debug Section
if __name__ == "__main__":

    from rich import print as rich_print
    from apps.rubicon_v3.__function.__embedding_rerank import baai_embedding
    from apps.rubicon_v3.__function import _10_rewrite
    import json

    # Test configuration
    message_id = "correction_test"
    files = ""
    message_history = []
    mentioned_products = []
    channel = "DEV Debug"

    country_code = "KR"

    test_query_list = ["What is Bespoke AI 스팀?"]

    def retrieve_rewritten_queries(test_query_list):
        rewritten_query_list = []
        for query in test_query_list:
            rewritten_results = _10_rewrite.re_write_history(
                query,
                files,
                message_history,
                mentioned_products,
                channel,
                gpt_model_name="gpt-4.1",
                country_code=country_code,
            )
            rewritten_query = rewritten_results.get("re_write_query_list")[0]
            rewritten_query_list.append(rewritten_query)

        return rewritten_query_list

    def test_function(test_query_list):
        # Get rewritten queries and embeddings
        rewritten_list = retrieve_rewritten_queries(test_query_list)
        embeddings = baai_embedding(rewritten_list, message_id)

        # Process each query through the pipeline
        for r, q, v in zip(rewritten_list, test_query_list, embeddings):

            # Step 1: Named Entity Recognition
            ner_result, _ = _20_orchestrator_NER_init.ner(
                r,
                v,
                country_code,
            )
            ner_json = json.dumps(ner_result, indent=2, ensure_ascii=False)

            # Step 2: Intelligence Classification
            intelligence_result = _22_orchestrator_intelligence.intelligence(
                r, "gpt-4.1-mini", country_code
            )

            # Step 3: Query Analysis
            analyzer_result = _21_orchestrator_query_analyzer.query_analyzer(
                r,
                message_history,
                gpt_model_name="gpt-4.1-mini",
                country_code=country_code,
            )

            # Display original query information
            rich_print(f"\nOriginal Query: \n[bold green]{q}\n")
            rich_print(f"\nRewritten Query: \n[bold green]{r}\n")

            # Display original pipeline results
            rich_print(f"\nOriginal NER: \n[bold green]{ner_json}\n")
            rich_print(
                f"\nOriginal Intelligence: \n[bold green]{intelligence_result}\n"
            )
            rich_print(f"\nOriginal Analyzer: \n[bold green]{analyzer_result}\n")

            # Apply corrections
            corr_ner_result, corr_intelligence_result, corr_analyzer_result = (
                correction(
                    ner_result, intelligence_result, analyzer_result, channel, country_code
                )
            )

            corr_ner_json = json.dumps(corr_ner_result, indent=2, ensure_ascii=False)

            # Display corrected results
            rich_print(f"\nCorrected NER: \n[bold green]{corr_ner_json}\n")
            rich_print(
                f"\nCorrected Intelligence: \n[bold green]{corr_intelligence_result}\n"
            )
            rich_print(f"\nCorrected Analyzer: \n[bold green]{corr_analyzer_result}\n")

    # Run the test
    test_function(test_query_list)
