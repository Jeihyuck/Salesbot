import json
import asyncio
from alpha import __log
from icecream import ic
from datetime import datetime

# from django.db.models import F, Q
from django.core.paginator import Paginator
from django.db import connection, transaction

from apps.rubicon_v3.models import Unstructured_Index
from alpha.settings import VITE_OP_TYPE

def create_unstructured_index(request_dict):
    __log.debug(request_dict)

    Unstructured_Index.objects.create(
        country_code=request_dict['query']['country_code'],
        op_type=request_dict['query']['op_type'],
        name=request_dict['query']['name'],
        ai_search_index=request_dict['query']['ai_search_index']
    )
    return True, None, None, {'type': 'success', 'title': 'Success', 'text' : request_dict['query']['name'] + ' has added.'}

def read_unstructured_index(request_dict):
    # __log.debug(request_dict)

    qeury = Unstructured_Index.objects
    if 'country_code' in request_dict['query']:
        qeury = qeury.filter(country_code=request_dict['query']['country_code'])
    if 'op_type' in request_dict['query']:
        qeury = qeury.filter(op_type=request_dict['query']['op_type'])

    item_count = qeury.count()
    items = list(qeury.order_by('country_code', '-op_type', 'name').values('id', 'country_code', 'op_type', 'name', 'ai_search_index'))
    paginator = Paginator(items, per_page=request_dict['paging']['itemsPerPage'], orphans=0)

    page_data = list(paginator.page(int(request_dict['paging']['page'])))

    return True, page_data, [{'itemCount': item_count}], None

def update_unstructured_index(request_dict):
    # __log.debug(request_dict)

    Unstructured_Index.objects.filter(id=request_dict['query']['id']).update(
        country_code=request_dict['query']['country_code'],
        name=request_dict['query']['name'],
        ai_search_index=request_dict['query']['ai_search_index']
    )

    return True, None, None, {'type': 'success', 'title': 'Success', 'text' : request_dict['query']['name'] + ' has updated.'}

def delete_unstructured_index(request_dict):
    # __log.debug(request_dict)
    Unstructured_Index.objects.filter(id=request_dict['query']['id']).delete()
    return True, None, None, {'type': 'success', 'title': 'Success', 'text' : 'a config has deleted.'}


def list_op_type(request_dict):
    # __log.debug(request_dict)
    distinct_values = Unstructured_Index.objects.filter(country_code=request_dict['query']['country_code']).values('op_type').distinct()
    distinct_values_list = [item['op_type'] for item in distinct_values]
    distinct_values_list = sorted(distinct_values_list)
    __log.debug(distinct_values_list)
    return True, distinct_values_list,  None, None

def list_index(request_dict):
    # distinct_values = Unstructured_Index.objects.filter(country_code=request_dict['query']['country_code']).filter(op_type=request_dict['query']['op_type']).order_by('ai_search_index').values('country_code', 'op_type', 'name', 'ai_search_index').distinct()
    # distinct_values_list = [{'title' : item['country_code'] + ':' + item['op_type'] + ':' + item['name'], 'value': item['ai_search_index']} for item in distinct_values]
    # distinct_values_list = sorted(distinct_values_list)
    distinct_values = Unstructured_Index.objects.filter(country_code=request_dict['query']['country_code'], op_type='TEST').order_by('op_type').values('op_type', 'name', 'ai_search_index').distinct()
    distinct_values_list = [{'title' : item['op_type'] + ' : ' + item['name'] + ' : ' + item['ai_search_index'], 'value': item['ai_search_index']} for item in distinct_values]
    # distinct_values_list = sorted(distinct_values_list)
    return True, distinct_values_list,  None, None