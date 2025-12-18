import sys

sys.path.append("/www/alpha/")

import django
import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "alpha.settings")
django.setup()

import json
import pandas as pd

from typing import Literal, List
from pydantic import create_model
from django.db import connection as conn

from apps.rubicon_v3.__function.__embedding_rerank import rerank_db_results
from apps.rubicon_v3.__function import __llm_call
from apps.rubicon_v3.models import Ner_Expression_Field, NER_Ref
from apps.rubicon_v3.__function.__prompts import ner_prompt
from alpha import __log
from alpha.settings import VITE_OP_TYPE
from django.core.cache import cache


def create_ner_item_model(country_code=None):
    """
    Creates a dynamic NER Pydantic model with field names constrained to values from Ner_Expression_Field.

    Args:
        country_code (str, optional): Filter by country code if provided

    Returns:
        A complete NER model with validated field names
    """
    # Get valid field names from database
    query = Ner_Expression_Field.objects.filter(active=True)
    if country_code:
        query = query.filter(country_code=country_code)

    field_names = list(query.values_list("field_name", flat=True).distinct())
    field_names_tuple = tuple(field_names) if field_names else ()

    # Create the NERItem model with constrained field
    if field_names:
        NERItem = create_model(
            "NERItem",
            expression=(str, ...),
            field=(Literal[field_names_tuple], ...),
            operator=(str, ...),
        )
    else:
        # Fallback if no field names found
        NERItem = create_model(
            "NERItem",
            expression=(str, ...),
            field=(str, ...),
            operator=(str, ...),
        )

    return NERItem


def create_ner_model(country_code=None):
    """
    Creates a dynamic NER Pydantic model with field names constrained to values from Ner_Expression_Field.

    Args:
        country_code (str, optional): Filter by country code if provided

    Returns:
        A complete NER model with validated field names
    """

    NERItem = create_ner_item_model(country_code)

    # Create the NER model with a list of NERItem
    NER = create_model("NER", items=(List[NERItem], ...))

    return NER


def _retrieve_ner_few_shot(top_query, top_query_embedding, country_code):
    """
    Generates NER few-shot examples by finding similar queries in the database.

    Retrieves the most similar NER examples from the database using vector similarity search,
    then reranks them to provide relevant few-shot examples for NER training.

    Args:
        top_query (str): The input query to find similar examples for
        top_query_embedding (list): Vector embedding of the input query
        country_code (str): Country code to filter examples by region

    Returns:
        tuple: (fewshot_examples_text, fewshot_examples_list)
            - fewshot_examples_text (str): Formatted text of examples for prompt
            - fewshot_examples_list (list): List of example dictionaries
    """
    try:
        top_query_embedding = list(top_query_embedding)

        # Extract top 10 similar examples using vector similarity
        similarity_sql = f"""SELECT
                            {NER_Ref.query.field.name},
                            {NER_Ref.measure_dimension.field.name}::text,
                            1 - ({NER_Ref.embedding.field.name} <=> ARRAY{str(top_query_embedding)}::vector) AS similarity_score
                            FROM {NER_Ref._meta.db_table}
                            WHERE {NER_Ref.country_code.field.name} = '{country_code}'
                            AND {NER_Ref.active.field.name} is TRUE
                            ORDER BY similarity_score DESC
                            LIMIT 10;"""

        with conn.cursor() as curs:
            curs.execute(similarity_sql)
            results = curs.fetchall()
            df = pd.DataFrame(results, columns=[c.name for c in curs.description])
        curs.close()

        if not df.empty:
            # Rerank to get top 3 most relevant examples
            actual_top_k = min(len(df), 3)
            df_reranked = rerank_db_results(
                top_query,
                df,
                text_column="query",
                top_k=actual_top_k,
                skip_threshold=True,
            )
        else:
            return "", []

        # Format examples for prompt and store as list
        fewshot_examples_text = ""
        fewshot_examples_list = []
        for _, row in df_reranked.iterrows():
            query = row["query"]
            measure_dimension = row["measure_dimension"]
            fewshot_examples_list.append(
                {"query": query, "measure_dimension": measure_dimension}
            )
            example = f"""
Input: {query}
Answer: {measure_dimension}
"""
            fewshot_examples_text += example

        return fewshot_examples_text, fewshot_examples_list

    except Exception as e:
        raise Exception(f"Error performing similarity search and reranking: {str(e)}")


def _retrieve_ner_field_info(country_code):
    """
    Retrieves NER field names and descriptions from the rubicon_v3_ner_expression_field table.

    Args:
        country_code (str): Country code to filter fields by region.

    Returns:
        list: List of dictionaries containing NER field names and descriptions
              [{"field_name": str, "field_description": str}, ...]
    """
    fields = Ner_Expression_Field.objects.filter(
        country_code=country_code, active=True
    ).order_by("id")

    if fields.exists():
        ner_field_info = [
            {
                "field_name": field.field_name,
                "field_description": field.field_description,
            }
            for field in fields
        ]
    else:
        ner_field_info = []

    return ner_field_info


def _format_ner_field_info(field_info):
    """
    Formats NER field information into a readable string for prompt formatting.

    Args:
        field_info (list): List of field information dictionaries

    Returns:
        str: Formatted field descriptions as a single string
    """
    formatted_fields = []
    for item in field_info:
        formatted_fields.append(
            f"Field: {item['field_name']}\n" f"Description: {item['field_description']}"
        )
    return "\n".join(formatted_fields)


def ner(top_query, embedding, country_code, model_name="gpt-4.1"):
    """
    Performs Named Entity Recognition (NER) processing on the input query.

    This function orchestrates the complete NER pipeline:
    1. Retrieves relevant field information for the country
    2. Gets few-shot examples from similar queries
    3. Constructs a structured prompt with instructions, field info, and examples
    4. Calls the LLM with structured output to extract entities

    Args:
        top_query (str): The input query to analyze
        embedding (list): Vector embedding of the query
        country_code (str): Country code for region-specific processing
        model_name (str, optional): LLM model to use. Defaults to "gpt-4.1"

    Returns:
        tuple: (initial_ner_values, metadata)
            - initial_ner_values (list): List of extracted NER items
            - metadata (dict): Dictionary containing few-shot examples used
    """
    # Retrieve field information for the specified country
    ner_field_info = _retrieve_ner_field_info(country_code)

    # Retrieve few-shot examples based on query similarity
    fewshot_examples_text, fewshot_examples_list = _retrieve_ner_few_shot(
        top_query, embedding, country_code
    )

    # Get the base NER instruction prompt
    instruction_prompt = ner_prompt.PROMPT

    # Construct the message structure for the LLM
    messages = [
        {"role": "system", "content": [{"type": "text", "text": instruction_prompt}]},
        {
            "role": "system",
            "content": [
                {
                    "type": "text",
                    "text": f"[Field Information]\n{_format_ner_field_info(ner_field_info)}",
                }
            ],
        },
        {
            "role": "system",
            "content": [
                {
                    "type": "text",
                    "text": f"[Examples]\n{fewshot_examples_text}\n\nNote: Always verify field names against [Field Information].",
                }
            ],
        },
        {
            "role": "user",
            "content": [{"type": "text", "text": f"Query to analyze: {top_query}"}],
        },
    ]

    # Create the dynamic NER model for structured output
    NER = create_ner_model(country_code)

    try:
        # Call LLM with structured output constraints
        # Parameters: model, messages, schema, temperature=0.01, top_p=0.1, seed=42
        initial_ner_values = __llm_call.open_ai_call_structured(
            "gpt-4.1", # Hardcoded to avoid conflicts in main pipeline
            messages,
            NER,
            0.01,
            0.1,
            42,  # Low temperature for consistent results
        )

        # Extract the items from the structured response
        initial_ner_values = initial_ner_values["items"]

        return initial_ner_values, {
            "fewshot_examples": fewshot_examples_list,
        }

    except Exception as e:
        __log.error(f"Error in NER init: {str(e)}")
        return [], {
            "fewshot_examples": [],
        }


# Test and development section
if __name__ == "__main__":
    from apps.rubicon_v3.__function import _10_rewrite
    from apps.rubicon_v3.__function.__embedding_rerank import baai_embedding
    from rich import print as rich_print

    def retrieve_rewritten_queries(test_query_list):
        rewritten_query_list = []
        for query in test_query_list:
            rewritten_results = _10_rewrite.re_write_history(
                query,
                files,
                message_history,
                mentioned_products,
                gpt_model_name="gpt-4.1",
                country_code=country_code,
            )
            rewritten_query = rewritten_results.get("re_write_query_list")[0]
            rewritten_query_list.append(rewritten_query)

        return rewritten_query_list

    def test_ner_init(message_id, country_code, test_query_list):
        embeddings = baai_embedding(test_query_list, message_id)

        for q, v in zip(test_query_list, embeddings):
            fewshot, _ = _retrieve_ner_few_shot(q, v, country_code)
            ner_result, _ = ner(q, v, country_code)

            ner_json = json.dumps(ner_result, indent=2, ensure_ascii=False)

            rich_print(f"\nQuery: \n[green]{q}\n")
            # rich_print(f"Fewshot: \n {fewshot}\n")
            rich_print(f"NER Result: \n {ner_json}\n")

    message_id = "init_ner"
    files = ""
    message_history = []
    mentioned_products = []

    country_code = "KR"

    test_query_list = [
        "200만원 이하 16인치 갤럭시 북 추천해줘",
    ]

    # Run tests
    rewritten_list = retrieve_rewritten_queries(test_query_list)
    test_ner_init(message_id, country_code, test_query_list)

    # Note: Managed Word processing moved to _23_orchestrator_correction
    # Note: NER Standardization moved to _30_orchestrator_NER_standardization
    # Note: Results here are for debug purposes (init_ner)
