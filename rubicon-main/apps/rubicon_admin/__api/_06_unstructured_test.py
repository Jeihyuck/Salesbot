# import django_rq
import time
from alpha import __log
from azure.search.documents import SearchClient
from azure.core.credentials import AzureKeyCredential
from alpha.settings import AZURE_SEARCH_ENDPOINT, AZURE_SEARCH_API_KEY
from azure.search.documents.models import VectorizableTextQuery


def front_test_unstructured_rag(
    query, index, category1_value, category2_value, category3_value, k: int = 5
):
    search_client = SearchClient(
        endpoint=AZURE_SEARCH_ENDPOINT,
        index_name=index,
        credential=AzureKeyCredential(AZURE_SEARCH_API_KEY),
    )
    # api_version=AZURE_SEARCH_API_VERSION
    vector_query = VectorizableTextQuery(
        text=query, k_nearest_neighbors=k * 3, fields="embedding_semantic_chunk"
    )

    category1_value = (
        [category1_value]
        if isinstance(category1_value, str) and category1_value != ""
        else category1_value or []
    )

    category2_value = (
        [category2_value]
        if isinstance(category2_value, str) and category2_value != ""
        else category2_value or []
    )

    category3_value = (
        [category3_value]
        if isinstance(category3_value, str) and category3_value != ""
        else category3_value or []
    )

    filter_conditions = []
    if category1_value:
        filter_conditions.append(
            " or ".join([f"category1 eq '{cat}'" for cat in category1_value])
        )
    if category2_value:
        filter_conditions.append(
            " or ".join([f"category2 eq '{cat}'" for cat in category2_value])
        )
    if category3_value:
        filter_conditions.append(
            " or ".join([f"category3 eq '{cat}'" for cat in category3_value])
        )

    filter_condition = " and ".join(filter_conditions) if filter_conditions else None

    __log.debug(vector_query)
    __log.debug(filter_condition)
    search_results = search_client.search(
        search_text=query,
        vector_queries=[vector_query],
        filter=filter_condition,
        top=k * 6,
        query_type="semantic",
        semantic_configuration_name="my-semantic-config",
        query_caption="extractive",
    )

    all_results = []
    for result in search_results:
        # __log.debug(result['chunk'])
        # time.sleep(4)
        if "title" in result:
            all_results.append(
                {
                    "id": result["id"],
                    "goods_nm": result["goods_nm"],
                    "index": index,
                    "title": result["title"],
                    "chunk": f'<span style="color: #2089FF">### ID : {result["id"]}</span>'
                    + "\n"
                    + result["chunk"],
                    "score": round(result["@search.reranker_score"], 2),
                    "question": result.get("question", ""),
                    "answer": result.get("answer", ""),
                }
            )
        else:
            all_results.append(
                {
                    "id": result["id"],
                    "goods_nm": result["goods_nm"],
                    "index": index,
                    "chunk": result["chunk"],
                    "score": round(result["@search.reranker_score"], 2),
                    "question": result.get("question", ""),
                    "answer": result.get("answer", ""),
                }
            )

    return all_results


def unstructured_test(request_dict):
    # __log.debug(request_dict)
    try:
        if "query" not in request_dict["query"]:
            return False, None, None, None

        if "category_lv1" in request_dict["query"]:
            category_lv1 = request_dict["query"]["category_lv1"]
        else:
            category_lv1 = None
        if "category_lv2" in request_dict["query"]:
            category_lv2 = request_dict["query"]["category_lv2"]
        else:
            category_lv2 = None
        if "category_lv3" in request_dict["query"]:
            category_lv3 = request_dict["query"]["category_lv3"]
        else:
            category_lv3 = None

        search_restult = front_test_unstructured_rag(
            request_dict["query"]["query"],
            request_dict["query"]["ai_search_index"]["value"],
            category_lv1,
            category_lv2,
            category_lv3,
        )
        return True, search_restult, [{"itemCount": len(search_restult)}], None
    except Exception as e:
        __log.error(e)
        return (
            False,
            None,
            None,
            {
                "type": "warning",
                "title": "Warning",
                "text": "Something went wrong. Check your input",
            },
        )
