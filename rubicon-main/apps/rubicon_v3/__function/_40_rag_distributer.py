import sys

sys.path.append("/www/alpha/")

import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "alpha.settings")
django.setup()

import enum

from typing import List, Dict, Tuple, Any

from apps.rubicon_v3.__function.definitions import intelligences, sub_intelligences
from apps.rubicon_v3.models import Ner_Expression_Field


class RagType(str, enum.Enum):
    STRUCTURED = "structured"
    COMPLEMENT = "complement"
    MIXED = "mixed"
    NAN = "nan"


def _process_single_record(ner_output_list, ner_field_info_dict):
    """
    1) Validate all fields exist in the DB.
    2) Determine the target (RAG type).
    3) If target is "unstructured", ensure we have at least one of:
       'product_model', 'product_function', 'product_spec', 'product_code', 'product_option'.
    4) First pass: map each item to final fields (using standard_name, add_fields).
       - Collect distinct structured_view in a set (for returning separately).
       - Accumulate items in an in-memory dictionary: final_field -> list of expressions.
    5) Generate the final output list from the dictionary.
    6) Return { target, transformed_ner, structured_views }.
    """

    # ---------------------
    # Step 1) Validate fields exist
    # ---------------------
    for item in ner_output_list:
        fld = item["field"]
        if fld not in ner_field_info_dict:
            print(f"[SKIP] Field '{fld}' not found in DB.")
            return None

    # ---------------------
    # Step 2) Determine RAG type
    # ---------------------
    rag_types = set()
    for item in ner_output_list:
        fld = item["field"]
        rt = ner_field_info_dict[fld].get("rag_type", "")
        if rt and rt.lower() != RagType.NAN.value:
            rag_types.add(rt.lower())

    if not rag_types:
        # If no rag type found -> Default to unstructured
        target = RagType.COMPLEMENT.value
    elif len(rag_types) > 1:
        target = RagType.MIXED.value
    else:
        # Exactly one
        if RagType.STRUCTURED.value in rag_types:
            target = RagType.STRUCTURED.value
        elif RagType.COMPLEMENT.value in rag_types:
            target = RagType.COMPLEMENT.value
        elif RagType.MIXED.value in rag_types:
            target = RagType.MIXED.value
        else:
            raise ValueError(f"Unknown rag types found: {list(rag_types)}")

    # ---------------------
    # Step 3) If target is unstructured, check must-have fields
    # ---------------------
    if target == RagType.COMPLEMENT.value:
        must_have_any = {
            "product_model",
            "product_function",
            "product_option",
            "product_spec",
            "product_code",
            "error_failure",
            "promotion_name",
        }
        # Gather all fields from the NER list (the original fields, *not* standard_name)
        all_ner_fields = {item["field"] for item in ner_output_list}
        # If the intersection is empty, return None
        if not must_have_any.intersection(all_ner_fields):
            print("[SKIP] 'unstructured' type but missing one of the required fields.")
            return None

    # ---------------------
    # Step 4) First pass: map each item to final fields
    # ---------------------
    # We also collect structured_view values, but do not embed them in the final items yet.
    # We'll return them distinctly.
    structured_views = set()

    # Track mappings with original position to maintain order
    position_mappings = []

    for idx, item in enumerate(ner_output_list):
        ner_field_name = item["field"]
        expression = item["expression"]  # 질의 내 텍스트

        # Grab the standard_name, field_meta, etc.
        standard_name = ner_field_info_dict[ner_field_name]["standard_name"]
        field_meta = ner_field_info_dict[ner_field_name].get("field_meta", {})
        structured_view = field_meta.get("structured_view")
        add_fields = field_meta.get("add_fields", [])

        # Collect the structured_view in a set
        if structured_view:
            structured_views.add(structured_view)

        # Determine which "final" fields we should map to
        if standard_name == "nan":
            if add_fields:
                # Expand out all add_fields
                mapped_fields = add_fields  # e.g., ["weekday_open_time", ...]
            else:
                # Keep the original field
                mapped_fields = [ner_field_name]
        else:
            mapped_fields = [standard_name]  # single mapped field

        # Store mappings with original position
        for mf in mapped_fields:
            position_mappings.append(
                {
                    "original_position": idx,
                    "field": mf,
                    "expression": expression,
                    "operator": item["operator"],
                }
            )

    # ---------------------
    # Step 5) Build the final transformed_ner maintaining original order
    # ---------------------
    # Sort by original position to maintain order
    position_mappings.sort(key=lambda x: x["original_position"])

    transformed_ner = []
    for mapping in position_mappings:
        transformed_ner.append(
            {
                "field": mapping["field"],
                "expression": mapping["expression"],
                "operator": mapping["operator"],
            }
        )

    # ---------------------
    # Step 6) Return final result
    # ---------------------

    # If we get this far, record is valid
    return target, transformed_ner, list(structured_views)


def rag_distributer(
    query_list: List[str],
    no_rag_query_list: List[str],
    embedding_data: Dict[str, List[List[float]]],
    query_analyzer_data,
    intelligence_data,
    sub_intelligence_data,
    init_ner_data,
    ner_data,
    assistant_data,
    date_match_data,
    no_cache_queries: set,
    error_queries: set,
    country_code: str,
) -> Tuple[List[List[Any]], List[List[Any]]]:
    """
    This function is responsible for distributing the queries to the appropriate RAG type
    based on the NER output and intelligence data.

    Args:
    - query_list: List of queries
    - no_rag_query_list: List of queries that should not be processed with RAG
    - embedding_data: Dictionary of query to embeddings
    - query_analyzer_data: Query analyzer data
    - intelligence_data: Dictionary of query to intelligence data
    - sub_intelligence_data: Dictionary of query to sub-intelligence data
    - init_ner_data: Dictionary of query to initial NER data
    - ner_data: Dictionary of query to NER data
    - assistant_data: Dictionary of query to assistant data
    - date_match_data: Dictionary of query to date match data
    - no_cache_queries: Set of queries that should not be cached
    - error_queries: Set of queries that have errors
    - country_code: Country code

    Returns:
    - structured_outputs: List of structured outputs
    - complement_outputs: List of complement outputs
    - no_cache_queries: Set of queries that should not be cached
    - error_queries: Set of queries that have errors
    - good_queries: List of queries
    """
    # Filter and collect data
    filtered_data = []
    good_queries = []
    no_rag_queries = set()

    for query in query_list:
        ner_data_list = ner_data.get(query)
        int_data = intelligence_data.get(query)
        sub_int_data = sub_intelligence_data.get(query)

        # Skip queries that are erroneous
        if (
            not ner_data_list
            and int_data not in [intelligences.ACCOUNT_MANAGEMENT, intelligences.FAQ]
            and sub_int_data not in [sub_intelligences.ORDER_DELIVERY_TRACKING]
        ):
            no_rag_queries.add(query)
            continue

        # Grab the rest of the data
        query_analyzer_item = query_analyzer_data.get(query)
        init_ner_data_list = init_ner_data.get(query)
        assistant_data_item = assistant_data.get(query)
        date_match_data_item = date_match_data.get(query)
        embedding_item = embedding_data.get(query)

        # Add all items to a single tuple to keep them together
        filtered_data.append(
            (
                query,
                embedding_item,
                query_analyzer_item,
                int_data,
                sub_int_data,
                init_ner_data_list,
                ner_data_list,
                assistant_data_item,
                date_match_data_item,
            )
        )
        good_queries.append(query)

    # Get field information from database
    field_info = {
        field.field_name: {
            "rag_type": field.field_rag_type,
            "standard_name": field.field_standard_name,
            "field_meta": field.field_meta,  # This is a dict (possibly empty)
        }
        for field in Ner_Expression_Field.objects.filter(
            country_code=country_code, active=True
        )
    }

    no_rag_query_list = list(set(no_rag_query_list) | no_rag_queries)

    structured_outputs = []
    complement_outputs = []

    # ---------------------------------------------------
    # Process all records
    # ---------------------------------------------------
    for (
        query,
        embedding,
        query_analyzer,
        intel,
        sub_intel,
        init_ner_output_list,
        ner_output_list,
        assistant_output,
        date_match_list,
    ) in filtered_data:
        target = RagType.NAN.value  # Default target
        transformed_ner = []
        structured_view = []

        # Only process with NER output if intelligence and sub_intelligence conditions are met
        if (
            ner_output_list
            and intel not in [intelligences.ACCOUNT_MANAGEMENT]
            and sub_intel not in [sub_intelligences.ORDER_DELIVERY_TRACKING]
        ):
            result = _process_single_record(ner_output_list, field_info)
            if not result:
                no_cache_queries.add(query)
                continue

            target, transformed_ner, structured_view = result

        # Additional processing for intelligence and sub_intelligence
        # If intelligence is ACCOUNT_MANAGEMENT set target to STRUCTURED
        if intel == intelligences.ACCOUNT_MANAGEMENT:
            target = RagType.STRUCTURED.value

        # If sub_intelligence is ORDER_DELIVERY_TRACKING set target to STRUCTURED
        if sub_intel == sub_intelligences.ORDER_DELIVERY_TRACKING:
            target = RagType.STRUCTURED.value

        if target == RagType.STRUCTURED.value:
            structured_outputs.append(
                [query, embedding, intel, sub_intel, structured_view, transformed_ner]
            )
        elif target == RagType.MIXED.value:
            structured_outputs.append(
                [query, embedding, intel, sub_intel, structured_view, transformed_ner]
            )
            complement_outputs.append(
                [
                    query,
                    embedding,
                    query_analyzer,
                    intel,
                    sub_intel,
                    init_ner_output_list,
                    transformed_ner,
                    assistant_output,
                    date_match_list,
                ]
            )
        else:
            complement_outputs.append(
                [
                    query,
                    embedding,
                    query_analyzer,
                    intel,
                    sub_intel,
                    init_ner_output_list,
                    transformed_ner,
                    assistant_output,
                    date_match_list,
                ]
            )

    return (
        structured_outputs,
        complement_outputs,
        no_cache_queries,
        error_queries,
        good_queries,
        no_rag_query_list,
    )
