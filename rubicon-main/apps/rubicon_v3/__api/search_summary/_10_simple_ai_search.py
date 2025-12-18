import sys

sys.path.append("/www/alpha/")

import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "alpha.settings")
django.setup()

from apps.__common import multi_threading
from azure.search.documents import SearchClient
from azure.core.credentials import AzureKeyCredential

from apps.rubicon_v3.__function.ai_search.ai_search_index_definitions import (
    AiSearchIndexDefinitions,
)
from apps.rubicon_v3.models import Unstructured_Index

from apps.rubicon_v3.__function._72_product_rag_ai_search import _add_alias

from alpha.settings import AZURE_SEARCH_ENDPOINT, AZURE_SEARCH_API_KEY, VITE_OP_TYPE


def execute_cpt_rag(
    query: str,
    model_list: list,
    country_code: str,
    n=10,
    endpoint=AZURE_SEARCH_ENDPOINT,
    api_key=AZURE_SEARCH_API_KEY,
):
    """Parse GB offers data from Vector DB if extended_info exists."""
    alias_list = []

    # index_config = AiSearchIndexDefinitions.KR_INTEGRATION()
    get_index_name = Unstructured_Index.objects.filter(
        country_code=country_code,
        op_type=os.getenv("VITE_OP_TYPE"),
        name="INTEGRATION",
    ).values("ai_search_index")

    if country_code == "KR":
        system_config = AiSearchIndexDefinitions.KR_DOT_COM_CPT()
    else:
        system_config = AiSearchIndexDefinitions.GB_DOT_COM_CPT()

    # system_name promotion만 탐색함.
    # model_code 및 disp_end_dtm 필터 조건을 위함.
    _add_alias(alias_list, system_config)

    final_filter = f"""(system_name eq '{system_config.integration_index_system_name[0]}' and version eq '{system_config.integration_index_system_name[1]}')"""

    if model_list:
        final_filter += (
            " and ("
            + " or ".join([f"model_code/any(x: x eq '{v}')" for v in model_list])
            + ")"
        )

    select_field_list = [
        "id",
        "system_name",
        "version",
        "model_code",
        "chunk",
        "goods_id",
        "disp_strt_dtm",
        "disp_end_dtm",
        "title",
        "category1",
        "category2",
        "category3",
    ]

    param_dict = {
        "search_text": query,
        "filter": final_filter,
        "select": select_field_list,
        "top": n,
        "query_type": "simple",
    }

    if VITE_OP_TYPE == "DEV" and country_code == "KR":
        endpoint = "https://dev-search-rb-krc.search.windows.net"
        api_key = os.getenv("AZURE_SEARCH_API_KEY")
    elif VITE_OP_TYPE == "DEV" and country_code == "GB":
        endpoint = "https://dev-search-rb-krc-uks.search.windows.net"
        api_key = os.getenv("AZURE_DEV_GB_SEARCH_API_KEY")

    def _create_search_client(index_name):
        return SearchClient(
            endpoint=endpoint,
            index_name=index_name,
            credential=AzureKeyCredential(api_key),
        )

    search_client = _create_search_client(get_index_name[0]["ai_search_index"])

    thread_params = []
    thread_params.append(
        [
            search_client.search,
            (),
            param_dict,
        ]
    )

    thread_result = multi_threading.run_in_threads_multi_function(thread_params)
    result_list = [[y for y in x] for x in thread_result][0]
    no_dup_list = []
    filtered_result = []
    for item in result_list:
        sample_dict = {}
        if item["chunk"] not in no_dup_list:
            no_dup_list.append(item["chunk"])
            sample_dict["id"] = item["id"]
            sample_dict["system_name"] = item["system_name"]
            sample_dict["version"] = item["version"]
            sample_dict["category1"] = item["category1"]
            sample_dict["category2"] = item["category2"]
            sample_dict["category3"] = item["category3"]
            sample_dict["model_code"] = item["model_code"]
            sample_dict["title"] = item["title"]
            sample_dict["chunk"] = item["chunk"]
            sample_dict["disp_strt_dtm"] = item["disp_strt_dtm"]
            sample_dict["disp_end_dtm"] = item["disp_end_dtm"]
            filtered_result.append(sample_dict)

    return filtered_result
