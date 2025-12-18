import asyncio
from alpha import __log
from datetime import datetime
from django.db.models import F, Q
from django.core.paginator import Paginator
from django.db import connection, transaction
from apps.rubicon_admin.__function import rerank
# from django.contrib.postgres.search import SearchVector

from apps.rubicon_v3.models import Assistant_Preferred_Recommendation
# from apps.rubicon_v3.__function.__embedding_rerank import baai_embedding
from apps.__common.alpha import value_extractor


# below code is for creating ner record for postgresql using pg_vector. convert below code for update.

def create_assistant_product(request_dict):
    # __log.debug(request_dict)
    Assistant_Preferred_Recommendation.objects.create(
        country_code = request_dict['query']['country_code'],
        category = request_dict['query']['category'],
        preferred_recommendation = request_dict['query']['preferred_recommendation'],
        product = request_dict['query']['product'],
        spec = request_dict['query']['spec'],
        key_features = request_dict['query']['key_features'],
        target_audience = request_dict['query']['target_audience']
    )
    return True, None, None, {'type': 'success', 'title': 'Success', 'text' : request_dict['query']['product'] + ' has created.'}


def read_assistant_product(request_dict):
    __log.debug(request_dict)
    qeury = Assistant_Preferred_Recommendation.objects

    if 'country_code' in request_dict['query']:
        qeury = qeury.filter(country_code=request_dict['query']['country_code'])
    if 'category' in request_dict['query']:
        __log.debug(request_dict['query']['category'])
        qeury = qeury.filter(category=request_dict['query']['category'])
       
    item_count = qeury.count()
    items = list(qeury.order_by('country_code', 'category', 'product').values('id', 'country_code', 'category', 'preferred_recommendation', 'product', 'spec', 'key_features', 'target_audience'))
    paginator = Paginator(items, per_page=request_dict['paging']['itemsPerPage'], orphans=0)

    page_data = list(paginator.page(int(request_dict['paging']['page'])))

    return True, page_data, [{'itemCount': item_count}], None


def update_assistant_product(request_dict):
    # __log.debug(request_dict)
    Assistant_Preferred_Recommendation.objects.filter(id=request_dict['query']['id']).update(
        country_code = request_dict['query']['country_code'],
        category = request_dict['query']['category'],
        preferred_recommendation = request_dict['query']['preferred_recommendation'],
        product = request_dict['query']['product'],
        spec = request_dict['query']['spec'],
        key_features = request_dict['query']['key_features'],
        target_audience = request_dict['query']['target_audience']
    )
    return True, None, None, {
        'type': 'success',
        'title': 'Success',
        'text': f"{request_dict['query']['product']} has been updated."
    }

    

def delete_assistant_product(request_dict):
    Assistant_Preferred_Recommendation.objects.filter(id=request_dict['query']['id']).delete()
    return True, None, None, None

def list_category(request_dict):
    # __log.debug(request_dict)
    distinct_values = Assistant_Preferred_Recommendation.objects.filter(country_code = request_dict['query']['country_code']).values('category').distinct()
    distinct_values_list = [item['category'] for item in distinct_values]
    distinct_values_list = sorted(distinct_values_list)
    return True, distinct_values_list,  None, None