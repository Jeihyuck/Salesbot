# line 2 ~ 7 테스트 시 주석 해제
from sre_constants import IN
import sys

sys.path.append("/www/alpha/")
import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "alpha.settings")

import datetime
import json

from azure.search.documents.models import VectorizableTextQuery

from apps.rubicon_v3.__function.ai_search.ai_search_config import AiSearchConfig
from apps.rubicon_v3.__function.ai_search.index import index_category_type
from apps.rubicon_v3.__function.ai_search.query_filter.ai_search_filter_condition import (
    AiSearchFilterCondition,
)
from apps.rubicon_v3.__function.ai_search.index.index_info import IndexInfo
from apps.rubicon_v3.__function.definitions import channels, site_cds
from apps.rubicon_v3.__function.__utils import get_date_range_bounds
from django.db import connection

from alpha import settings

import re
import urllib
import numpy as np
from collections import OrderedDict
from azure.search.documents import SearchClient
from apps.rubicon_v3.__function.ai_search import ai_search_index_definitions
from apps.rubicon_v3.__function.ai_search.ai_search_document import AISearchDocument
from apps.rubicon_v3.__function.ai_search.azure_ai_search import AzureAiSearch
from apps.rubicon_v3.__function.ai_search.ai_search_index_definitions import (
    AiSearchIndexDefinitions,
)
from apps.rubicon_v3.__function.ai_search.query_filter.ai_search_filter_conditions import (
    AiSearchFilterConditions,
)


from azure.core.credentials import AzureKeyCredential
from apps.rubicon_v3.__function import _22_orchestrator_intelligence
from apps.rubicon_v3.__function.definitions import intelligences, sub_intelligences
from apps.rubicon_v3.models import (
    Intelligence_V2,
    Unstructured_Index,
)
from apps.rubicon_data.models import product_category, uk_product_filter
from alpha.settings import (
    VITE_OP_TYPE,
)
from apps.rubicon_v3.__function.ai_search.duplicate_checker import DuplicateChecker

from alpha import __log
from apps.rubicon_v3.__function.ai_search import ai_search_index_definitions

# Test Code
# python ___dev/KTH/ai_search/ai_search_test_taehoon.py
# TODO NEED REFACTORING

REGEX_IMAGE_URL_IN_MARKDOWN = re.compile(
    r"!\[.*?\]\((https?://[^\s]+?(?:\([^\s()]*\)[^\s]*)*?)\)"
)


def _get_index_priority(intelligence, sub_intelligence):
    """Bring unstructured index priority from Intelligence table

    Args:
        intelligence (str),
        sub_intelligence (str):
        --> Intelligence and sub-intelligence to filter the index priorities.

    Returns:
        list:
    """

    use_intelligence = sub_intelligence
    index_priorities = list(
        Intelligence_V2.objects.filter(sub_intelligence=use_intelligence).values_list(
            "intelligence_meta", flat=True
        )
    )[0].get(
        _22_orchestrator_intelligence.MetaColumns.UNSTRUCTURED_INDEX_PRIORITY,
        [],
    )

    index_priorities = [item for item in index_priorities]

    return index_priorities


def get_ai_search_result(
    top_query,
    intelligence,
    sub_intelligence,
    alias_list,
    unstructured_code_mapping_list: list,
    model_code_dict: dict[tuple, set],
    all_alias_index_dict,
    filter_conditions: "AiSearchFilterConditions",
    country_code,
    k: int = 5,
    reranker_threshold: int = 1,
    is_debug=False,
    is_vector_search=True,
    custom_filter=None,
    date_filter=[],
    channel_id="AIBot",
    site_cd="B2C",
):
    """Unstructured search results retrieval function

    Args:
        top_query (str),
        intelligence (str),
        sub_intelligence (str),
        alias_list (list): List of index aliases to search.
        unstructured_code_mapping_list (list): List of code mappings for unstructured search.
        model_code_dict (dict[tuple, set]),
        all_alias_index_dict (dict): Dictionary mapping aliases to index names.
        filter_conditions (AiSearchFilterConditions): Filter conditions for the search.
        country_code (str),
        k (int, optional): Number of results to return. Defaults to 5.
        reranker_threshold (int, optional): Threshold for reranker score. Defaults to 1.
        is_debug (bool, optional): Whether to run in debug mode. Defaults to False.
        is_vector_search (bool, optional): Whether to use vector search. Defaults to True.
        custom_filter (str, optional): Custom filter string. Defaults to None.
        date_filter (list, optional): Date filter conditions. Defaults to [].

    Returns:
        tuple[OrderedDict, dict]: A tuple containing:
            - ordered_content (OrderedDict): Ordered dictionary of search results.
            - unstructured_search_meta (dict): Metadata about the search results.
    """

    # rag_type, intelligence, virtual_view, top_query = unstructured_intelligence

    content = dict()
    duplicate_checker = DuplicateChecker(threshold=0.9)
    RESULT_COL_BLOB_PATH = "blob_path"
    RESULT_COL_PAGE_NUM = "page_num"
    RESULT_COL_CHUNK_TEXT = "chunk"
    RESULT_COL_CAPTION = "@search.captions"
    RESULT_COL_RERANKER_SCORE = "@search.reranker_score"
    RESULT_COL_SCORE = "@search.score"
    RESULT_COL_CHUNK_EMBEDDING = "embedding_chunk"

    # TODO : refactoring
    result_lengths = {}
    if alias_list:
        all_results = []
        azure_search = AzureAiSearch(
            country_code=country_code,
            alias_list=alias_list,
        )

        select_field_list = [
            "id",
            "system_name",
            "version",
            "model_code",
            "embedding_chunk",
            "chunk",
            "content",
            "goods_id",
            "display_seq",
            "disp_strt_dtm",
            "disp_end_dtm",
            "blob_path",
            "title",
            "category1",
            "category2",
            "category3",
            "reg_date",
            "type",
        ]
        if is_debug:
            select_field_list = []  # bring all results

        result_thread_list, config_list_dict = azure_search.search_multiple_indices(
            top_query,
            sub_intelligence,
            filter_conditions,
            country_code,
            select_field_list,
            k,
            is_vector_search=is_vector_search,
            custom_filter=custom_filter,
            date_filter=date_filter,
            channel_id=channel_id,
            site_cd=site_cd,
        )
        result_length = {}
        for i, (index_name, param_dict, results) in enumerate(result_thread_list):
            for o in results:
                all_results.append((index_name, param_dict, o))
                result_length.setdefault(index_name, 0)
                result_length[index_name] += 1

        doc_count_dict = {}
        for i, (index_name, param_dict, result) in enumerate(all_results):
            # __log.debug(f"{index_name}: {result[RESULT_COL_SCORE]}")

            # if is_vector_search and reranker score not exists, remove from results
            if is_vector_search and (
                not result[RESULT_COL_RERANKER_SCORE]
                or result[RESULT_COL_RERANKER_SCORE] <= reranker_threshold
            ):
                continue

            # Check if it is an integration index, search index alias
            is_integration_index = index_name == azure_search.integration_index_name
            if is_integration_index:
                alias = (
                    ai_search_index_definitions.AiSearchIndexDefinitions.ALIAS_INTEGRATION
                )
            else:
                alias = azure_search.index_name_to_alias_dict[index_name]

            index_def: IndexInfo | None = azure_search.alias_index_def_dict.get(alias)

            option_check = any(
                item.get("field") == "product_option"
                for item in unstructured_code_mapping_list
            )

            # Check if the result from the index should always be included in the response
            always_use_in_response = _check_always_use_in_response(
                is_integration_index,
                config_list_dict,
                result.get("system_name"),
                index_name,
                product_option=option_check,
            )

            # Remove duplicated results
            # if _is_duplicated_document(
            #     index_def, duplicate_checker, result["chunk"], result["embedding_chunk"]
            # ):
            #     continue

            # __log.debug(f"{index_name}: {result[RESULT_COL_SCORE]}")
            blob_path = result.get(RESULT_COL_BLOB_PATH)
            try:
                source = (
                    f"{urllib.parse.quote(blob_path, safe=':/?#&=%')}#page={result[RESULT_COL_PAGE_NUM]}"
                    if blob_path
                    else None
                )
            except:
                source = None

            # Create a list of unique tokens from multiple product names and add them to the first line
            text = ""
            goods_name_list = result.get("goods_nm", [])
            if goods_name_list:
                name_tokens = []
                for goods_name in goods_name_list:
                    name_tokens.extend(goods_name.split())
                text += " ".join(list(dict.fromkeys(name_tokens)))  # ordered set
            text += "\n" + result[RESULT_COL_CHUNK_TEXT]

            if index_def:
                if not text or (
                    text and len(text) < index_def.minimum_valid_text_length
                ):
                    continue

            # If it is an installation conditions and standards sub intelligence, use high-scoring self-resolution documents only
            if (
                sub_intelligence
                == sub_intelligences.INSTALLATION_CONDITIONS_AND_STANDARDS
                and (
                    "solution" in result.get("system_name")
                    and result.get("@search.score", 0) < 0.025
                )
            ):
                # In Installation Conditions and Standards, exclude solution index if reranker score is low
                continue

            if doc_count_dict.get(result.get("system_name"), 0) == 0:
                doc_count_dict[result.get("system_name")] = 1
            else:
                if (
                    "cpt" in result.get("system_name")
                    or "pvi" in result.get("system_name")
                    or "scrp" in result.get("system_name")
                ):
                    # use maximum for cpt, pvi, scrp indexes
                    doc_count_dict[result.get("system_name")] += 1
                elif doc_count_dict[result.get("system_name")] >= 2:
                    # use maximum of 2 for other indexes
                    continue
                doc_count_dict[result.get("system_name")] += 1

            o = {
                "question": top_query,
                "answer": text,  # result[RESULT_COL_CHUNK_TEXT],
                "caption": (
                    result[RESULT_COL_CAPTION][0].text
                    if result[RESULT_COL_CAPTION]
                    else []
                ),
                "score": (
                    result[RESULT_COL_RERANKER_SCORE]
                    if is_vector_search
                    else result[RESULT_COL_SCORE]
                ),
                "index": i,
                "id": result["id"],
                "source": source,
                "system_name": result.get("system_name"),
                "version": result.get("version"),
                # "image_urls": result.get(image_urls, None),
                "index_name": index_name,
                "param_dict": param_dict,
                "intelligence": intelligence,
                # "search_params": {
                #     str(k): [o.model_dump() for o in v]
                #     for k, v in search_params.items()
                # },
                "blob_path": blob_path,
                "display_seq": result.get("display_seq"),
                "model_code": result.get("model_code"),
                "goods_id": result.get("goods_id"),
                "reg_date": result.get("reg_date"),
                "reranker_score": result.get(RESULT_COL_RERANKER_SCORE),
                "goods_name_list": result.get("goods_nm", []),
                "model_code": result.get("model_code", []),
                "disp_strt_dtm": result.get("disp_strt_dtm"),
                "disp_end_dtm": result.get("disp_end_dtm"),
                "title": result.get("title"),
                "content": result.get("content", ""),
                "category1": result.get("category1"),
                "category2": result.get("category2"),
                "category3": result.get("category3"),
                "always_use_in_response": always_use_in_response,
            }
            if is_debug:
                debug_result = result.copy()
                if RESULT_COL_CAPTION in debug_result:
                    if debug_result[RESULT_COL_CAPTION]:
                        debug_result[RESULT_COL_CAPTION] = [
                            str(x) for x in debug_result[RESULT_COL_CAPTION]
                        ]
                del debug_result["embedding_chunk"]
                o["_debug_result"] = debug_result
                # o["_debug_result_pydantic"] = doc.model_dump()

            content[result["id"]] = o

    ordered_content = OrderedDict()
    topk = k
    count = 0

    for id in sorted(content, key=lambda x: content[x]["score"], reverse=True):
        ordered_content[id] = content[id]
        count += 1

        if count >= topk:
            break
    filtered_search_result = {key: 0 for key in result_lengths.keys()}

    for item in ordered_content.values():
        i = item.get("index_name")
        if i in filtered_search_result:
            filtered_search_result[i] += 1

    unstructured_search_meta = {
        "top_question": top_query,
        "intelligence": intelligence,
        "index_priorities": alias_list,
        "search_result": result_lengths,
        "filtered_search_result": filtered_search_result,
        "unstructured_code_mapping_list": unstructured_code_mapping_list,
        "all_alias_index_dict": all_alias_index_dict,
    }

    return ordered_content, unstructured_search_meta


def _check_always_use_in_response(
    is_integration_index, config_list_dict, system_name, index_name, product_option
):
    """Check if the index should always be used in the response based on the configuration.

    Args:
        is_integration_index (bool): Whether the index is an integration index.
        config_list_dict (dict): Dictionary of configuration lists.
        system_name (str): The system name to check.
        index_name (str): The index name to check.
        product_option (bool): Whether the product option is included.

    Returns:
        bool: True if the index should always be used in the response, False otherwise.
    """

    config_list: list[AiSearchConfig] | None = config_list_dict.get(
        is_integration_index, []
    )
    for config in config_list:
        always_use_in_response = getattr(config, "always_use_in_response", False)
        if (
            is_integration_index
            and config.integration_index_system_name[0] == system_name
        ) or (not is_integration_index and config.index_name == index_name):
            # Case when the condition to always be displayed is set in the search conditions
            filter_conds: list[AiSearchFilterCondition] | None = (
                config.filter_conditions.find(config.index_name)
            )

            # Case when the referenced index is set to always be displayed
            if config.index_def:

                if filter_conds:
                    for cond in filter_conds:
                        if (
                            # Case when the condition to always be displayed is set in the filter conditions,
                            # or the index is set to always be displayed
                            cond.always_use_in_response
                            or config.index_def.always_use_in_response
                        ) and (
                            # (
                            #     config.index_def.category1_type
                            #     == index_category_type.IndexCategoryType.PRODUCT_CATEGORY
                            #     and cond.category1_list
                            # )
                            # or
                            (  # When model codes are included in the filter conditions, and can also filter by model codes in the following index
                                config.index_def.has_model_code
                                and cond.product_model_codes
                            )
                        ):
                            dot_com_cpt_config = (
                                AiSearchIndexDefinitions.KR_DOT_COM_CPT()
                            )
                            dot_com_cpt_category_config = (
                                AiSearchIndexDefinitions.KR_DOT_COM_CPT_CATEGORY()
                            )
                            gb_dot_com_cpt_config = (
                                AiSearchIndexDefinitions.GB_DOT_COM_CPT()
                            )
                            # Exclude from always_use_in_response if product_option is present in ner and system_name is related to cpt
                            if (
                                system_name
                                in (
                                    [
                                        dot_com_cpt_config.integration_index_system_name[
                                            0
                                        ],
                                        dot_com_cpt_category_config.integration_index_system_name[
                                            0
                                        ],
                                        gb_dot_com_cpt_config.integration_index_system_name[
                                            0
                                        ],
                                    ]
                                )
                                and product_option
                            ):
                                always_use_in_response = False
                            else:
                                always_use_in_response = True
                                break
                if always_use_in_response:
                    break

        if always_use_in_response:
            break
    return always_use_in_response


def _is_duplicated_document(
    index_def: IndexInfo | None, duplicate_checker: DuplicateChecker, chunk, embedding
):
    # Remove duplicated documents based on chunk text or embedding vector
    dedup_with_text = False
    if not index_def or (index_def and not index_def.has_embedding_chunk):
        dedup_with_text = True

    if dedup_with_text:
        is_appended = duplicate_checker.append_with_key(chunk)
    else:
        # Not appending if embedding vector is None
        if not embedding:
            return True

        embedding = np.array(embedding, dtype=np.float32)
        is_appended = duplicate_checker.append_embedding(embedding)

    if not is_appended:
        # When a document is duplicated
        return True
    return False


def get_goods_nm(model_code, country_code):
    """function to get goods name from model code

    Args:
        model_code (list): List of model codes to search for.
        country_code (str): Country code for the search context.
    Returns:
        list: List of goods names corresponding to the model codes.
    """

    insert_model_code = "(" + ",".join(["'" + x + "'" for x in model_code]) + ")"
    if country_code == "KR":
        with connection.cursor() as cursor:
            sql = f"""
            SELECT DISTINCT ON (
                c.product_category_lv1,
                c.product_category_lv2,
                c.product_category_lv3
            )
                g.goods_nm
            FROM rubicon_data_pf_goods_list g
            INNER JOIN rubicon_data_product_category c
                ON g.mdl_code = c.mdl_code
                and g.dlgt_disp_yn = 'Y'
            where c.mdl_code in {insert_model_code}
            ORDER BY 
                c.product_category_lv3;"""
            cursor.execute(sql)
            goods_nm_result = cursor.fetchall()

    elif country_code == "GB":
        with connection.cursor() as cursor:
            sql = f"""
            select distinct on(
                sb.category_lv1, 
                sb.category_lv2, 
                sb.category_lv3
            )
                fm.display_name
            from rubicon_data_uk_product_family_list fm
            inner join rubicon_data_uk_product_spec_basics sb 
            on fm.model_code = sb.model_code
            and fm.site_cd = 'B2C'
            and sb.site_cd = 'B2C'
            and fm.key_model_yn = 'Y'
            where fm.model_code in {insert_model_code}
            ;"""
            cursor.execute(sql)
            goods_nm_result = cursor.fetchall()
    return [x[0] for x in goods_nm_result]


def select_ai_search_result(
    top_query,
    intelligence,
    sub_intelligence,
    channel_id,
    site_cd,
    alias_list,
    unstructured_code_mapping_list,
    model_code_dict: dict[tuple, set],
    all_alias_index_dict,
    filter_conditions: "AiSearchFilterConditions",
    country_code,
    topk=5,
    is_debug=False,
    vector_search=True,
    custom_filter=None,
    promo=False,
    date_filter=[],
):
    """Unstructured RAG execution function
    This function retrieves unstructured search results based on the provided query and configurations.

    Args:
        top_query (str),
        intelligence (str),
        sub_intelligence (str),
        channel_id (str),
        alias_list (list): List of index aliases to search.
        unstructured_code_mapping_list (list): List of code mappings for unstructured search.
        model_code_dict (dict[tuple, set]),
        all_alias_index_dict (dict): Dictionary mapping aliases to index names.
        filter_conditions (AiSearchFilterConditions): Filter conditions for the search.
        country_code (str),
        topk (int, optional): Number of results to return. Defaults to 5.
        is_debug (bool, optional): Whether to run in debug mode. Defaults to False.
        vector_search (bool, optional): Whether to use vector search. Defaults to True.
        custom_filter (str, optional): Custom filter string. Defaults to None.
        date_filter (list, optional): Date filter conditions. Defaults to []

    Returns:
        tuple[list, dict]: A tuple containing:
            - result_list (list): List of search results (limited to topk unless is_debug=True).
            - unstructured_search_meta (dict): Metadata about the search results.

    """
    # __log.debug(f"select_ai_search_result : {top_query} {unstructured_code_mapping}")
    unstructured_rag, unstructured_search_meta = get_ai_search_result(
        top_query,
        intelligence,
        sub_intelligence,
        alias_list,
        unstructured_code_mapping_list,
        model_code_dict,
        all_alias_index_dict,
        filter_conditions,
        country_code,
        k=topk,
        reranker_threshold=1.0,
        is_debug=is_debug,
        is_vector_search=vector_search,
        custom_filter=custom_filter,
        date_filter=date_filter,
        channel_id=channel_id,
        site_cd=site_cd,
    )
    # iter_unstructured_rag = iter(unstructured_rag.items())
    # unstructured_rag_len = len(unstructured_rag)
    # image_urls = []
    # icon_urls = {}
    result_list = []

    # Parse release date from RDBMS using model code
    model_code_list = [
        model_code
        for k, v in unstructured_rag.items()
        if v.get("model_code") is not None
        for model_code in v.get("model_code")
    ]
    model_code_to_release_date_dict = _get_model_code_to_release_date_dict(
        model_code_list, country_code
    )
    index_name_to_alias_dict = {v: k for k, v in all_alias_index_dict.items()}
    # for _ in range(min(topk * 2, unstructured_rag_len)):
    for k, v in unstructured_rag.items():
        # _, v = next(iter_unstructured_rag)
        model_codes = v.get("model_code")
        system_name = v.get("system_name")
        goods_nm_ls = []

        # Add to the main text if able to get model codes and if it is a promotion index
        if model_codes and "promotion" in system_name:
            goods_nm_ls = get_goods_nm(model_codes, country_code)

        answer = str(v.get("answer", ""))
        index_name = v.get("index_name")
        chunk_id = v.get("id")

        alias_name = index_name_to_alias_dict.get(index_name)
        version = v.get("version")
        matched_intelligence = v.get("intelligence")
        category1 = v.get("category1")
        category2 = v.get("category2")
        category3 = v.get("category3")
        display_seq = v.get("display_seq")
        reg_date = v.get("reg_date")
        goods_name_list = v.get("goods_name_list")
        score_similarity = v.get("score", 0)
        release_date_list = sorted(
            [
                model_code_to_release_date_dict[x]
                for x in v.get("model_code", [])
                if x in model_code_to_release_date_dict
            ]
        )
        latest_release_date = None
        if release_date_list:
            latest_release_date = release_date_list[-1]

        if reg_date:
            try:
                reg_date = datetime.datetime.fromisoformat(
                    reg_date.replace("Z", "+00:00")
                )
            except:
                pass

        # Conditions before using integration index
        # if alias_name == "INSTALLATION" or (
        #     alias_name
        #     == ai_search_index_definitions.AiSearchIndexDefinitions.ALIAS_INTEGRATION
        #     and system_name.startswith("installation")
        # ):
        # Allow images only for installation, else:
        if sub_intelligence in [
            "Installation Conditions And Standards",
            "Usage Explanation",
            "General Connection",
            "Samsung Care Plus Explanation",
            "Smartthings Explanation",
        ] and channel_id not in [
            "Sprinklr",
            "STAR",
            "STAR_VD",
            "STAR_DA",
            "SamsungPlus",
            "AITool",
        ]:
            cleaned_answer = answer
            pass
        else:
            PATTERN = re.compile(r"!\[([^\]]*)\]\(([^)]+)\)")

            cleaned_answer = PATTERN.sub(lambda m: f" ({m.group(1)}) ", answer)

        if country_code == "GB" and not promo and intelligence in ["Buy Information"]:
            PATTERN = re.compile(
                r"(?:"
                # Korean Won (KRW) patterns
                r"₩\s*[\d,]+(?:\.\d{1,2})?|"
                r"KRW\s*[\d,]+(?:\.\d{1,2})?|"
                r"원\s*[\d,]+(?:\.\d{1,2})?|"
                r"[\d,]+\s*원|"
                r"[\d,]+(?:\.\d{1,2})?\s*KRW|"
                # British Pound (GBP) patterns
                r"£\s*[\d,]+(?:\.\d{1,2})?|"
                r"GBP\s*[\d,]+(?:\.\d{1,2})?|"
                r"[\d,]+(?:\.\d{1,2})?\s*GBP|"
                r"[\d,]+(?:\.\d{1,2})?\s*pounds?|"
                # Euro (EUR) patterns
                r"€\s*[\d,]+(?:\.\d{1,2})?|"
                r"EUR\s*[\d,]+(?:\.\d{1,2})?|"
                r"[\d,]+(?:\.\d{1,2})?\s*EUR|"
                r"[\d,]+(?:\.\d{1,2})?\s*euros?"
                r")",
                re.IGNORECASE,
            )

            # Update the substitution to use [PRICE REDACTED] instead of the markdown image replacement
            cleaned_answer = PATTERN.sub("[PRICE REDACTED]", answer)

        # If good names exist, add them to the text
        cleaned_answer = (
            cleaned_answer
            if not goods_nm_ls
            else f"{cleaned_answer}, Applied models: {','.join(goods_nm_ls)} "
        )

        # image_urls = v.get("image_urls", [])
        # icon_url = []

        # if (
        #     image_urls is not None
        #     or alias_name == "MANUAL"
        #     or (alias_name == "INTEGRATION" and system_name == "scms")

        # ):
        #     # image_url.extend(re.findall(image_url_pattern, answer))
        #     found_urls = REGEX_IMAGE_URL_IN_MARKDOWN.findall(answer)
        #     for url in found_urls:
        #         # print(f"--{url}--")
        #         if "icon" in url.lower():
        #             icon_url.append(url)
        #         else:
        #             image_urls.append(url)
        # else:
        #     image_urls = None

        # if image_urls or icon_url:
        #     cleaned_answer = re.sub(
        #         r"!\[([^\]]*)\]\(([^)]+)\)",
        #         lambda m: (
        #             f"$$icon$$({m.group(2)})"
        #             if "icon" in m.group(2).lower()
        #             else f"({m.group(2)})"
        #         ),
        #         answer,
        #     )
        # else:
        #     cleaned_answer = answer.strip()
        #     image_urls = None

        # __log.debug(answer)
        now_dt = datetime.datetime.now()

        score_adjusment = 0
        if latest_release_date:
            rel_dt = datetime.datetime.combine(
                latest_release_date, datetime.datetime.min.time()
            )
            latest_release_date = latest_release_date.strftime("%Y-%m-%d %H:%M:%S")
            days = (now_dt - rel_dt).days

            if days > 365:
                score_adjusment = -1
            if days > 365 * 2:
                score_adjusment = -2
            if days > 365 * 4:
                score_adjusment = -20
            # else:
            #     score_recency = calculate_recency(days)

        relevance = score_similarity + score_adjusment

        o = {
            "top_query": top_query,
            "text_data": cleaned_answer,
            # "image_url": image_url,
            # "icon_url": icon_url,
            "intelligence": matched_intelligence,
            "index_name": index_name,
            "alias_name": alias_name,
            "system_name": system_name,
            "version": version,
            "id": chunk_id,
            "category1": category1,
            "category2": category2,
            "category3": category3,
            "display_seq": display_seq,
            "source": v.get("source"),
            "blob_path": v.get("blob_path"),
            "reg_date": reg_date,
            "latest_release_date": latest_release_date,
            "score_similarity": score_similarity,
            "score_adjusment": score_adjusment,
            "relevance": relevance,
            "model_code": model_codes,
            "disp_strt_dtm": v.get("disp_strt_dtm"),
            "disp_end_dtm": v.get("disp_end_dtm"),
            "title": v.get("title"),
            "content": v.get("content"),
            "category1": category1,
            "category2": category2,
            "category3": category3,
            "vector_search": vector_search,
            "always_use_in_response": v.get("always_use_in_response", False),
            # "goods_nm": value.get("goods_nm"),
            # "priority": "middle" if index_map == "DOT_COM:CPT" else "low",
        }
        if is_debug:
            o["_debug_result1"] = v

        result_list.append(o)

    result_list = sorted(result_list, key=lambda x: x["relevance"], reverse=True)

    for rank, o in enumerate(result_list, 1):
        o["rank"] = rank

    if is_debug:
        return result_list, unstructured_search_meta

    return result_list[:topk], unstructured_search_meta


def _is_promotion(intelligence, sub_intelligence):
    """Check if the intelligence and sub-intelligence indicate a promotion."""

    return (
        sub_intelligence != ""
        and sub_intelligence
        in [
            sub_intelligences.PRICE_EXPLANATION,
            sub_intelligences.PAYMENT_BENEFIT_EXPLANATION,
            sub_intelligences.EVENT_PROMOTION,
            sub_intelligences.BUNDLE_DISCOUNT,
        ]
    ) or (sub_intelligence == "" and intelligence == intelligences.BUY_INFORMATION)


def _add_alias(alias_list, index_info: IndexInfo):
    """Add index alias to the alias list if not already present."""
    if index_info.alias not in alias_list:
        alias_list.append(index_info.alias)


def execute_promo_rag(
    intelligence: str,
    sub_intelligence: str,
    site_cd: str,
    unstructured_code_mapping_list: list[dict],
    extended_info_result_list: list[dict],
    channel_id: str,
    country_code: str,
    topk=10,
    vector_search=False,
    is_debug=False,
):
    """Parse GB offers data from Vector DB if extended_info exists.

    Args:
        intelligence (str),
        sub_intelligence (str),
        unstructured_code_mapping_list (list[dict]),
        extended_info_result_list (list[dict]),
        channel_id (str),
        country_code (str),
        topk (int, optional),
        vector_search (bool, optional),
        is_debug (bool, optional),

    Returns:
        tuple[dict, dict]: A tuple containing:
            - response (dict): A dictionary containing the structured promotion data with keys:
                - "title": "PRODUCT OFFERS"
                - "system_name": The promotion system name
                - "text_data": JSON string of promotion information
                - "always_use_in_response": True
                - "alias_name": Index alias name
                - "blob_path": Concatenated URL paths
            - meta (dict): Metadata about the search results from select_ai_search_result.
    """

    all_alias_index_dict = AzureAiSearch._get_unstructured_index_name_dict(country_code)

    model_code_dict = {}

    alias_list = []

    config = AiSearchIndexDefinitions.GB_PROMOTION()

    # Search for promotion system_name only.
    # For model_code and disp_end_dtm filter conditions.
    _add_alias(alias_list, config)

    __log.debug(alias_list)

    if extended_info_result_list:
        for o in extended_info_result_list:
            key = (
                o.get("category_lv1"),
                o.get("category_lv2"),
                o.get("category_lv3"),
            )
            ex = o.get("extended_info", [])
            if ex:
                model_code_dict.setdefault(key, set()).update(ex)

    filter_conditions = _make_filter_conditions(
        intelligence,
        sub_intelligence,
        country_code,
        unstructured_code_mapping_list,
        model_code_dict,
        all_alias_index_dict,
    )

    response, meta = select_ai_search_result(
        top_query="*",
        intelligence=intelligence,
        sub_intelligence=sub_intelligence,
        channel_id=channel_id,
        site_cd=site_cd,
        alias_list=alias_list,
        unstructured_code_mapping_list=unstructured_code_mapping_list,
        model_code_dict=model_code_dict,
        all_alias_index_dict=all_alias_index_dict,
        filter_conditions=filter_conditions,
        country_code=country_code,
        topk=topk,
        is_debug=is_debug,
        vector_search=vector_search,
    )

    promotion_list = []

    url_list = []

    # Replace text_data with content if text_data is empty
    for item in response:
        promo_chunk_filter = item.get("text_data").replace("\n", " ").strip()
        content = item.get("content") or ""
        text_data = item.get("text_data") or ""
        title = item.get("title") or ""
        d = {
            "Promotion Title": title,
            "Promotion Information": (
                content + " " + text_data if promo_chunk_filter else content
            ),
            "Model Code": item.get("model_code"),
        }
        url = item.get("blob_path")
        if url:
            url_list.append(url)

        promotion_list.append(d)

    # Create text_data with list[dict] -> JSON string for better LLM understanding
    # Response creation quality was the best with JSON
    promo_string = json.dumps(promotion_list, indent=4, ensure_ascii=False)

    try:
        # bring promotion system_name
        promo_system_name = AiSearchIndexDefinitions.GB_PROMOTION()
        promo_system_name: str = promo_system_name.integration_index_system_name[0]
    except IndexError:
        # Set to rule_base just in case of error
        promo_system_name: str = f"{VITE_OP_TYPE.lower()}-promotion"

    response = {
        "title": "PRODUCT OFFERS",
        "system_name": promo_system_name,
        "text_data": promo_string,
        "always_use_in_response": True,
        "alias_name": AiSearchIndexDefinitions.ALIAS_INTEGRATION,
        "blob_path": "\n".join(list(set(url_list))),
    }

    return response, meta


# Return the existence of the document related to the model code in the extended_info_result_list
def execute_search_rag(
    intelligence: str,
    sub_intelligence: str,
    site_cd: str,
    alias_list: list,
    document_info: list,
    unstructured_code_mapping_list: list[dict],
    extended_info_result_list: list[dict],
    channel_id: str,
    country_code: str,
    topk=10,
    vector_search=False,
    is_debug=False,
):
    all_alias_index_dict = AzureAiSearch._get_unstructured_index_name_dict(country_code)
    model_code_dict = {}

    if extended_info_result_list:
        for o in extended_info_result_list:
            key = (
                o.get("category_lv1"),
                o.get("category_lv2"),
                o.get("category_lv3"),
            )
            ex = o.get("extended_info", [])
            if ex:
                model_code_dict.setdefault(key, set()).update(ex)

    filter_conditions = _make_filter_conditions(
        intelligence,
        sub_intelligence,
        country_code,
        [],
        model_code_dict,
        all_alias_index_dict,
    )

    response, meta = select_ai_search_result(
        top_query="*",
        intelligence=intelligence,
        sub_intelligence=sub_intelligence,
        channel_id=channel_id,
        site_cd=site_cd,
        alias_list=alias_list,
        unstructured_code_mapping_list=[],
        model_code_dict=model_code_dict,
        all_alias_index_dict=all_alias_index_dict,
        filter_conditions=filter_conditions,
        country_code=country_code,
        topk=topk,
        is_debug=is_debug,
        vector_search=vector_search,
    )

    model_ls = []
    for k, v in model_code_dict.items():
        model_ls.extend(list(v))

    if response:
        return_text = f"!!Important!!: {','.join(model_ls[:3])}: Smartthings 지원"
        fixed_response = {
            "title": "Smartthings Support Information",
            "system_name": document_info[0],
            "version": document_info[1],
            "text_data": return_text,
            "always_use_in_response": True,
            "alias_name": AiSearchIndexDefinitions.ALIAS_INTEGRATION,
            "blob_path": "-",
        }
    else:
        return_text = f"!!Important!!: {','.join(model_ls[:3])}: Smartthings 미지원"
        fixed_response = {
            "title": "Smartthings Support Information",
            "system_name": document_info[0],
            "version": document_info[1],
            "text_data": return_text,
            "always_use_in_response": True,
            "alias_name": AiSearchIndexDefinitions.ALIAS_INTEGRATION,
            "blob_path": "-",
        }

    return fixed_response, meta


def get_alias_list(
    sub_intelligence,
    intelligence,
    site_cd,
    country_code,
    alias_list,
    vector_search,
    extended_info_result_list,
    channel_id,
):
    """Get the list of aliases based on the sub-intelligence and country code."""

    if sub_intelligence == "Shallow":
        if country_code == "KR":
            news_config = AiSearchIndexDefinitions.KR_NEWS()
            sales_talk_config = AiSearchIndexDefinitions.KR_SALES_TALK()
            dot_com_cpt_config = AiSearchIndexDefinitions.KR_DOT_COM_CPT()
            _add_alias(alias_list, news_config)
            _add_alias(alias_list, sales_talk_config)
            _add_alias(alias_list, dot_com_cpt_config)
        if country_code == "GB":
            news_config = AiSearchIndexDefinitions.GB_NEWS()
            sales_talk_config = AiSearchIndexDefinitions.GB_SALES_TALK()
            dot_com_cpt_config = AiSearchIndexDefinitions.GB_DOT_COM_CPT()
            _add_alias(alias_list, news_config)
            _add_alias(alias_list, sales_talk_config)
            _add_alias(alias_list, dot_com_cpt_config)
    else:
        alias_list = _get_index_priority(intelligence, sub_intelligence)

    if hasattr(site_cds, "FN"):
        if site_cd == site_cds.FN and country_code == "KR":
            # Applied after creating mapping information between general index and FN index
            dot_com_scrap_config = AiSearchIndexDefinitions.KR_DOT_COM_SCRAP()
            fn_scrap_config = AiSearchIndexDefinitions.KR_FN_SCRAP()
            # kr_promo_config = AiSearchIndexDefinitions.KR_PROMOTION()
            kr_fn_promo_config = AiSearchIndexDefinitions.KR_FN_PROMOTION()
            # kr_promo_common_config = AiSearchIndexDefinitions.KR_PROMOTION_COMMON()
            kr_fn_promo_common_config = (
                AiSearchIndexDefinitions.KR_FN_PROMOTION_COMMON()
            )

            conversion_dict = {
                dot_com_scrap_config.alias: fn_scrap_config.alias,
            }
            _add_alias(alias_list, kr_fn_promo_config)
            _add_alias(alias_list, kr_fn_promo_common_config)

            alias_list = [conversion_dict.get(a, a) for a in alias_list]

            # Use notice index for the following sub intelligence
            if sub_intelligence in [
                sub_intelligences.EVENT_PROMOTION,
                sub_intelligences.PAYMENT_BENEFIT,
                sub_intelligences.PAYMENT_BENEFIT_EXPLANATION,
                sub_intelligences.PAYMENT_METHOD_INFORMATION,
                sub_intelligences.PRICE_EXPLANATION,
                sub_intelligences.INSTALLATION_CONDITIONS_AND_STANDARDS,
                sub_intelligences.DELIVERY_POLICY,
                sub_intelligences.ORDER_DELIVERY_TRACKING,
                sub_intelligences.BUYING_POLICY,
                sub_intelligences.EXCHANGE_RETURN_POLICY,
                sub_intelligences.SAMSUNG_CARE_PLUS_EXPLANATION,
            ]:
                kr_fn_notice_config = AiSearchIndexDefinitions.KR_FN_NOTICE()
                _add_alias(alias_list, kr_fn_notice_config)

    # For GB promotion information, use exact search in bm25 when extended_info_result_list exists
    # In this case, the Promotion index is not used in vector search
    if (
        country_code == "GB"
        and intelligence == intelligences.BUY_INFORMATION
        and vector_search
        and extended_info_result_list
    ):
        # In GB, Buy Information uses only the Promotion index.
        gb_promo_config = AiSearchIndexDefinitions.GB_PROMOTION()
        alias_list = [x for x in alias_list if x != gb_promo_config.alias]

    if country_code == "KR":
        kr_cpt_category_config = AiSearchIndexDefinitions.KR_DOT_COM_CPT_CATEGORY()
        if kr_cpt_category_config.alias in alias_list and extended_info_result_list:
            # CPT_CATEGORY index is not used when extended_info_result_list exists.
            alias_list.remove("DOT_COM:CPT_CATEGORY")

    # Use the third-party SmartThings index when the sub intelligence is 'SmartThings Explanation' and extended_info is not present
    if (
        channel_id == channels.SMARTTHINGS
        and sub_intelligence
        in [
            sub_intelligences.SMARTTHINGS_EXPLANATION,
        ]
        and not [
            item
            for sublist in extended_info_result_list
            for item in sublist.get("extended_info", "")
        ]
    ):
        if country_code == "KR":
            smt_info_ext_config = (
                AiSearchIndexDefinitions.KR_SMARTTHINGS_INFO_EXTENDED()
            )
            _add_alias(alias_list, smt_info_ext_config)
        if country_code == "GB":
            smt_info_ext_config = (
                AiSearchIndexDefinitions.GB_SMARTTHINGS_INFO_EXTENDED()
            )
            _add_alias(alias_list, smt_info_ext_config)

    if "MANUAL" in alias_list:
        if country_code == "KR":
            manual_n10_config = AiSearchIndexDefinitions.KR_MANUAL_N10()
            _add_alias(alias_list, manual_n10_config)
        if country_code == "GB":
            manual_n10_config = AiSearchIndexDefinitions.GB_MANUAL_N10()
            _add_alias(alias_list, manual_n10_config)

    if channel_id == channels.RETAIL_KX and (
        sub_intelligence in [sub_intelligences.SMARTTHINGS_EXPLANATION]
        or intelligence in [intelligences.FAQ]
    ):
        # When the channel is Retail KX and sub_ intelligence is Smartthings Explanation,
        # add the scrp index in the code and retrieve all documents by applying the filter.
        if country_code == "GB":
            scrp_config = AiSearchIndexDefinitions.GB_DOT_COM_SCRAP()
            _add_alias(alias_list, scrp_config)

    return list(set(alias_list))


# Final output function
def execute_unstructured_rag(
    top_query: str,
    keywords: list[str],
    intelligence: str,
    sub_intelligence: str,
    unstructured_code_mapping_list: list[dict],
    extended_info_result_list: list[dict],
    ner: list[dict],
    channel_id: str,
    country_code: str,
    site_cd: str,
    topk,
    exact_search=False,
    vector_search=False,
    is_debug=False,
):
    """Execute unstructured RAG based on the provided parameters.

    Returns:
        response (list): A list of search results

    """

    # __log.debug(f"ai top_query : {top_query} {code_mapping_list}")
    merged_response = {}
    merged_search_meta = {}
    # Search with rewrite query if no keywords
    if keywords:
        use_query = " ".join(keywords)
    else:
        use_query = top_query

    date_list = []
    try:
        date_list = get_date_range_bounds(date_list[0]["date_list"])
    except Exception as e:
        print(e)

    # __log.debug("use_query")
    # __log.debug(use_query)

    if intelligence == intelligences.ERROR_AND_FAILURE_RESPONSE:
        return []

    all_alias_index_dict = AzureAiSearch._get_unstructured_index_name_dict(country_code)

    model_code_dict = {}

    alias_list = []

    alias_list = get_alias_list(
        sub_intelligence,
        intelligence,
        site_cd,
        country_code,
        alias_list,
        vector_search,
        extended_info_result_list,
        channel_id,
    )

    __log.debug(alias_list)

    # Search model code
    NUM_MODEL_CODES_FOR_EACH_MODEL = 3
    if extended_info_result_list:
        for o in extended_info_result_list:
            key = (
                o.get("category_lv1"),
                o.get("category_lv2"),
                o.get("category_lv3"),
            )
            ex = o.get("extended_info", [])
            if ex:
                model_code_dict.setdefault(key, set()).update(
                    ex[:NUM_MODEL_CODES_FOR_EACH_MODEL]
                )

    filter_conditions = _make_filter_conditions(
        intelligence,
        sub_intelligence,
        country_code,
        unstructured_code_mapping_list,
        model_code_dict,
        all_alias_index_dict,
    )

    if (
        intelligence == intelligences.BUY_INFORMATION
        and country_code == "GB"
        and not vector_search
        and extended_info_result_list
    ):
        # In GB, when extended_info_result_list exists,
        # search the promotion data of the product and create it additionally.
        # This only works with bm25 search.

        response, unstructured_search_meta = execute_promo_rag(
            intelligence=intelligence,
            sub_intelligence=sub_intelligence,
            site_cd=site_cd,
            unstructured_code_mapping_list=unstructured_code_mapping_list,
            extended_info_result_list=extended_info_result_list,
            channel_id=channel_id,
            country_code=country_code,
            vector_search=vector_search,
            is_debug=is_debug,
        )

        response = [response]
    elif (
        sub_intelligence == sub_intelligences.INSTALLATION_CONDITIONS_AND_STANDARDS
        and country_code == "KR"
        and not vector_search
        and extended_info_result_list
    ):
        # In KR, search 'Installation Conditions and Standards' in the Installation index and create it additionally
        # when extended_info_result_list exists.
        # This only works with bm25 search.
        alias_list = []
        exre_config = AiSearchIndexDefinitions.KR_EX_RE()
        _add_alias(alias_list, exre_config)

        response, unstructured_search_meta = select_ai_search_result(
            top_query=use_query,
            intelligence=intelligence,
            sub_intelligence=sub_intelligence,
            channel_id=channel_id,
            site_cd=site_cd,
            alias_list=alias_list,
            unstructured_code_mapping_list=unstructured_code_mapping_list,
            model_code_dict=model_code_dict,
            all_alias_index_dict=all_alias_index_dict,
            filter_conditions=filter_conditions,
            country_code=country_code,
            topk=topk,
            is_debug=is_debug,
            vector_search=vector_search,
            custom_filter="title eq '배송정책 안내'",
            promo=True,
        )
    elif (
        sub_intelligence in [sub_intelligences.IN_STORE_GUIDE]
        and country_code == "GB"
        and channel_id == "Retail_KX"
        and not vector_search
    ):
        # In the case of Retail KX channel, country code is GB, and Store Information Intelligence,
        # the scrp index is added in the code and all documents are retrieved by applying the filter.
        # This only works with bm25 search.

        alias_list = []
        scrp_config = AiSearchIndexDefinitions.GB_DOT_COM_SCRAP()
        _add_alias(alias_list, scrp_config)
        topk = 15
        response, unstructured_search_meta = select_ai_search_result(
            top_query="*",
            intelligence=intelligence,
            sub_intelligence=sub_intelligence,
            channel_id=channel_id,
            site_cd=site_cd,
            alias_list=alias_list,
            unstructured_code_mapping_list=unstructured_code_mapping_list,
            model_code_dict=model_code_dict,
            all_alias_index_dict=all_alias_index_dict,
            filter_conditions=filter_conditions,
            country_code=country_code,
            topk=topk,
            is_debug=is_debug,
            vector_search=vector_search,
            custom_filter="category3 eq 'KX'",
        )
    elif exact_search:

        alias_list = []
        if country_code == "KR":
            smt_config = AiSearchIndexDefinitions.KR_SMARTTHINGS_INFO()
        elif country_code == "GB":
            smt_config = AiSearchIndexDefinitions.GB_SMARTTHINGS_INFO()
        _add_alias(alias_list, smt_config)
        # Exact search only works with bm25 search.
        response, unstructured_search_meta = execute_search_rag(
            intelligence=intelligence,
            sub_intelligence=sub_intelligence,
            site_cd=site_cd,
            alias_list=alias_list,
            document_info=smt_config.integration_index_system_name,
            unstructured_code_mapping_list=unstructured_code_mapping_list,
            extended_info_result_list=extended_info_result_list,
            channel_id=channel_id,
            country_code=country_code,
            vector_search=vector_search,
            is_debug=is_debug,
        )
    else:
        response, unstructured_search_meta = select_ai_search_result(
            top_query=use_query,
            intelligence=intelligence,
            sub_intelligence=sub_intelligence,
            channel_id=channel_id,
            site_cd=site_cd,
            alias_list=alias_list,
            unstructured_code_mapping_list=unstructured_code_mapping_list,
            model_code_dict=model_code_dict,
            all_alias_index_dict=all_alias_index_dict,
            filter_conditions=filter_conditions,
            country_code=country_code,
            topk=topk,
            is_debug=is_debug,
            vector_search=vector_search,
            date_filter=date_list,
        )

    del_key = "content"
    for d in response:
        if del_key in d:
            del d[del_key]

    merged_response[top_query] = response
    merged_search_meta[top_query] = unstructured_search_meta

    return response


def _make_filter_conditions(
    intelligence,
    sub_intelligence,
    country_code,
    unstructured_code_mapping_list,
    model_code_dict,
    all_alias_index_dict,
):
    """Create filter conditions based on the provided parameters."""

    code_mappings_with_category = []

    # category
    if (
        isinstance(unstructured_code_mapping_list, list)
        and unstructured_code_mapping_list
    ):
        code_mappings_with_category = [
            x
            for x in unstructured_code_mapping_list
            if x.get("category_lv1") and x.get("category_lv1") != "NA"
        ]

    # Using the first category mapping only
    data = code_mappings_with_category[0] if code_mappings_with_category else {}
    edge_value = data.get("edge", "")

    # model code
    model_code_list = list()
    for key, s in model_code_dict.items():
        model_code_list.extend(s)
    model_code_list = list(set(model_code_list))

    filter_conditions = AiSearchFilterConditions()

    if _is_promotion(intelligence, sub_intelligence):
        if country_code == "GB":
            alias_config = AiSearchIndexDefinitions.GB_DOT_COM_SCRAP()
            filter_conditions.add(
                AiSearchFilterCondition(
                    index_name=all_alias_index_dict[alias_config.alias],
                    category1_list=["Purchase Benefits Information"],
                    product_model_codes=list(model_code_list),
                    always_use_in_response=True,
                    country=country_code,
                )
            )
        if country_code == "KR":
            alias_config = AiSearchIndexDefinitions.KR_DOT_COM_SCRAP()
            filter_conditions.add(
                AiSearchFilterCondition(
                    index_name=all_alias_index_dict[alias_config.alias],
                    category1_list=["삼성닷컴 혜택"],
                    # category2_list=["카드 혜택", "나눠서 결제"],
                    always_use_in_response=True,
                    country=country_code,
                )
            )
            promo_config = AiSearchIndexDefinitions.KR_PROMOTION()
            filter_conditions.add(
                AiSearchFilterCondition(
                    category1_list=data.get("category_lv1"),
                    category2_list=data.get("category_lv2"),
                    category3_list=data.get("category_lv3"),
                    product_model_codes=list(model_code_list),
                    index_name=all_alias_index_dict[promo_config.alias],
                    display_date=True,
                    always_use_in_response=True,
                    country=country_code,
                )
            )
            promo_com_config = AiSearchIndexDefinitions.KR_PROMOTION_COMMON()
            filter_conditions.add(
                AiSearchFilterCondition(
                    index_name=all_alias_index_dict[promo_com_config.alias],
                    display_date=True,
                    always_use_in_response=True,
                    country=country_code,
                )
            )

    # Basic conditions without specifying index name: If there are no conditions for a specific index, it will search according to this condition
    filter_conditions.add(
        AiSearchFilterCondition(
            category1_list=data.get("category_lv1"),
            category2_list=data.get("category_lv2"),
            category3_list=data.get("category_lv3"),
            product_model_codes=list(model_code_list),
            country=country_code,
        )
    )
    return filter_conditions


# TODO: THIS IS ONLY FOR KR. NEED TO ADD for GB
def _get_model_code_to_release_date_dict(model_code_list, country_code):
    """
    Get a dictionary mapping model codes to their release dates.
    """

    if not model_code_list:
        return {}

    if country_code == "KR":
        result_iter = product_category.objects.filter(
            mdl_code__in=model_code_list
        ).values_list("mdl_code", "release_date")

    else:
        result_iter = uk_product_filter.objects.filter(
            model_code__in=model_code_list
        ).values_list("model_code", "launch_date")

    model_code_to_year = {
        model_code: release_date
        for model_code, release_date in result_iter
        if model_code and release_date and release_date.year >= 2000
    }

    return model_code_to_year


def main():
    django.setup()
    result = execute_unstructured_rag(
        "고객 서비스 전화번호를 알려주세요",
        [],
        "General Information",
        "General Information",
        [],
        [],
        "KR",
        8,
        vector_search=True,
    )

    print(result)


if __name__ == "__main__":
    model_code_list = ["SM-A366BZKBEEB"]
    country_code = "GB"

    # print(_get_model_code_to_release_date_dict(model_code_list, country_code))
    #
    result = execute_unstructured_rag(
        top_query="갤럭시 S25 시리즈를 구매하면 받을 수 있는 콘텐츠 구독 혜택에 대해 알려줘",
        keywords=[],
        intelligence="Buy Information",
        sub_intelligence="Payment Benefit Explanation",
        unstructured_code_mapping_list=[
            {
                "expression": "갤럭시 S25 시리즈",
                "field": "product_model",
                "mapping_code": [
                    "갤럭시 S25",
                    "갤럭시 S25 엣지",
                    "갤럭시 S25 울트라",
                    "갤럭시 S25+",
                ],
                "type": ["p2p"],
                "category_lv1": ["COOKING GOODS"],
                "category_lv2": ["HHP"],
                "category_lv3": [
                    "Galaxy S25",
                    "Galaxy S25 Ultra",
                    "Galaxy S25 Edge",
                    "Galaxy S25+",
                ],
                "original_expression": "갤럭시 S25 시리즈",
            }
        ],
        extended_info_result_list=[
            {
                "mapping_code": "갤럭시 S25+",
                "category_lv1": "HHP",
                "category_lv2": "NEW RADIO MOBILE (5G SMARTPHONE)",
                "category_lv3": "Galaxy S25+",
                "edge": "recommend",
                "meta": "",
                "extended_info": ["SM-S936NLGEKOO", "SM-S936NLBAKOO"],
                "id": 1,
            },
            {
                "mapping_code": "갤럭시 S25 울트라",
                "category_lv1": "HHP",
                "category_lv2": "NEW RADIO MOBILE (5G SMARTPHONE)",
                "category_lv3": "Galaxy S25 Ultra",
                "edge": "recommend",
                "meta": "",
                "extended_info": ["SM-S938NZBFKOO"],
                "id": 2,
            },
        ],  # 이게 있어야함
        channel_id="DEV debug",
        country_code="KR",
        topk=8,
        vector_search=True,
    )

    print([x["text_data"] for x in result])
