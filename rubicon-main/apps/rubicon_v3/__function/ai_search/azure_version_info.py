from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass, field
from azure.search.documents import SearchClient
from azure.core.credentials import AzureKeyCredential
from azure.search.documents.models import VectorizedQuery
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

import os
import sys
import django

sys.path.append("/www/alpha/")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "alpha.settings")
django.setup()

from alpha.settings import (
    VITE_OP_TYPE,
    AZURE_SEARCH_ENDPOINT,
    AZURE_SEARCH_API_KEY,
    override_azure_search_env
)
from apps.rubicon_v3.models import (
    Unstructured_Index,
    Pipeline_Version_KR,
    Pipeline_Version_UK
)


def main() -> None:
    country_code = "KR"
    index_name = list(Unstructured_Index.objects.filter(
            country_code=country_code,
            op_type=VITE_OP_TYPE,
            name="INTEGRATION"
        ).values_list("ai_search_index", flat=True)
    )[0]

    # TODO: op_type 별 분기
    if country_code == "KR":
        system_name_list = list(
            Pipeline_Version_KR.objects.values_list("system_name", flat=True).distinct() 
        )
    else:
        system_name_list = list(
            Pipeline_Version_UK.objects.values_list("system_name", flat=True).distinct() 
        )

    # DEV GB는 다른 endpoint 사용함
    override_azure_search_env(country_code)
    search_client = SearchClient(
        endpoint=AZURE_SEARCH_ENDPOINT,
        index_name=index_name,
        credential=AzureKeyCredential(AZURE_SEARCH_API_KEY)
    )

    system_name_version = {}

    for system_name in system_name_list:

        results = search_client.search(
            search_text="*",
            query_type="simple",
            include_total_count=True,
            select="system_name",
            facets=["version"],
            filter=f"system_name eq '{system_name}'"
        )

        version_dict = results.get_facets() # facet 결과를 따로 추출함
        version_list = version_dict.get("version") # dict 안에 list of dict로 들어가있음 [{"value": "dev-promotion", "count": 1234}, ...] 식임

        # facet은 count가 1 이상인 경우만 가져오므로 if x["count"] > 0 없어도 됨
        version = max([x["value"] for x in version_list]) 

        # key-value pair로 쉽게 찾을수 있도록 함
        system_name_version[system_name] = version


    print(system_name_version)


if __name__ == "__main__":
    main()