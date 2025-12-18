import sys
sys.path.append("/home/rubicon/")

import os
# import re
import django
import enum
import json
import numpy as np

from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from sklearn.metrics.pairwise import cosine_similarity


os.environ.setdefault("DJANGO_SETTINGS_MODULE", "alpha.settings")
django.setup()
from alpha import settings

from datetime import datetime, timedelta
from alpha import __log
from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from azure.search.documents.models import VectorizedQuery
# from django.db import connection

# from apps.rubicon_admin.__function import rerank
from apps.rubicon_v3.__function import __utils
# from apps.rubicon_v3.__function.__embedding_rerank import baai_embedding
from apps.rubicon_v3.__function._71_product_rag_web_search_filter import text_cleaner
from apps.__common import multi_threading

from apps.rubicon_v3.models import (
    Unstructured_Index,
)

from alpha.settings import (
    VITE_OP_TYPE,
)

# Default integration index name for development environment
INDEX_NAME = "dev-integration-v5"


class IndexName(str, enum.Enum):
    """Enumeration of available search index names."""
    NEWSROOM = "NEWS"
    SALES_TALK = "SALES_TALK"
    DOT_COM_CPT = "DOT_COM:CPT"
    INTEGRATION = "INTEGRATION"


def benefits_chunk_list():
    """Retrieve UK benefits information chunks from Azure AI Search.
    
    Searches specific UK Samsung website URLs to extract benefits information
    and returns consolidated content chunks.
    
    Returns:
        list: List of content chunks from UK benefits pages
    """
    country_code = "GB"
    k = 5
    query = ""
    
    index_name = Unstructured_Index.objects.filter(
        country_code=country_code, op_type=VITE_OP_TYPE, name=IndexName.INTEGRATION.value
    ).values_list("ai_search_index", flat=True)

    settings.override_azure_search_env(country_code)

    client = SearchClient(
        endpoint=settings.AZURE_SEARCH_ENDPOINT,
        index_name=index_name[0],
        credential=AzureKeyCredential(settings.AZURE_SEARCH_API_KEY),
    )

    # UK Samsung website URLs for benefits information
    url_list = [
        "https://www.samsung.com/uk/why-buy-from-samsung/",
        "https://www.samsung.com/uk/price-promise/",
        "https://www.samsung.com/uk/trade-in/",
        "https://www.samsung.com/uk/samsung-finance/",
        "https://www.samsung.com/uk/klarna/",
        "https://www.samsung.com/uk/paypal-credit/"
    ]

    chunk_list = []

    # Extract content from each URL
    for url in url_list:

        results = client.search(
            search_text=query,
            filter=f"blob_path eq '{url}'"
        )

        content = ""

        # Consolidate chunks from search results
        for result in results:
            chunk = result.get("chunk")
            
            if chunk:
                content += " ".join(chunk.split())

        chunk_list.append(content)

    return chunk_list