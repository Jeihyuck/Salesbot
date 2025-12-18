import json
import asyncio
from icecream import ic
from alpha import __log

from datetime import datetime
# from django.db.models import F, Q
from django.core.paginator import Paginator
from django.db import connection, transaction
from apps.rubicon_admin.__function import rerank

from apps.rubicon_v3.models import Managed_Response_Index

def create_managed_response(request_dict):
    __log.debug(request_dict)

    if 'product' not in request_dict['query']:
        request_dict['query']['product'] = None

    Managed_Response_Index.objects.create(
        active=request_dict['query']['active'],
        country_code=request_dict['query']['country_code'],
        site_cd=request_dict['query']['site_cd'],
        category_lv1=request_dict['query']['category_lv1'],
        category_lv2=request_dict['query']['category_lv2'],
        category_lv3=request_dict['query']['category_lv3'],
        product=request_dict['query']['product'],
        function=request_dict['query']['function'],
        date=request_dict['query']['date'],
        managed_response=request_dict['query']['managed_response'],
        managed_only=request_dict['query']['managed_only'],
        reference=request_dict['query']['reference'],
    )

    return True, None, None, {'type': 'success', 'title': 'Success', 'text' : request_dict['query']['product'] + ' has created.'}

def read_managed_response(request_dict):
    __log.debug(request_dict)
    qeury = Managed_Response_Index.objects
    if 'active' in request_dict['query']:
        qeury = qeury.filter(active=request_dict['query']['active'])
    if 'managed_only' in request_dict['query']:
        qeury = qeury.filter(managed_only=request_dict['query']['managed_only'])
    if 'reference' in request_dict['query']:
        qeury = qeury.filter(reference=request_dict['query']['reference'])

    if 'country_code' in request_dict['query']:
        qeury = qeury.filter(country_code=request_dict['query']['country_code' ])
    if 'site_cd' in request_dict['query']:
        qeury = qeury.filter(site_cd=request_dict['query']['site_cd'])
    if 'product_search' in request_dict['query']:
        qeury = qeury.filter(product__contains=request_dict['query']['product_search'])
    if 'function_search' in request_dict['query']:
        qeury = qeury.filter(function__contains=request_dict['query']['function_search'])
    if 'date_search' in request_dict['query']:
        qeury = qeury.filter(date__contains=request_dict['query']['date_search'])


    item_count = qeury.count()
    items = list(qeury.order_by('product', 'function', 'date').values(
        'id',
        'active',
        'update_tag',
        'country_code',
        'site_cd',
        'product',
        'function',
        'date',
        'managed_response',
        'managed_only',
        'reference',
        'created_on',
        'updated_on'
    ))
    paginator = Paginator(items, per_page=request_dict['paging']['itemsPerPage'], orphans=0)

    page_data = list(paginator.page(int(request_dict['paging']['page'])))

    return True, page_data, [{'itemCount': item_count}], None

def update_managed_response(request_dict):
    __log.debug(request_dict)
    if 'product' not in request_dict['query']:
        request_dict['query']['product'] = None
    if 'function' not in request_dict['query']:
        request_dict['query']['function'] = None
    if 'date' not in request_dict['query']:
        request_dict['query']['date'] = None
    if 'managed_only' not in request_dict['query']:
        request_dict['query']['managed_only'] = False
    if 'reference' not in request_dict['query']:
        request_dict['query']['reference'] = False

    Managed_Response_Index.objects.filter(id=request_dict['query']['id']).update(
        active=request_dict['query']['active'],
        managed_only=request_dict['query']['managed_only'],
        reference=request_dict['query']['reference'],
        country_code=request_dict['query']['country_code'],
        site_cd=request_dict['query']['site_cd'],
        product=request_dict['query']['product'],
        function=request_dict['query']['function'],
        date=request_dict['query']['date'],
        managed_response=request_dict['query']['managed_response'],
    )
    return True, None, None, {
        'type': 'success',
        'title': 'Success',
        'text': f"{request_dict['query']['product']} has been updated."
    }

def delete_managed_response(request_dict):
    # Managed_Response_Index.objects.filter(id=request_dict['query']['id']).delete()
    Managed_Response_Index.objects.filter(id=request_dict['query']['id']).update(
        active=False
    )
    return True, None, None, {'type': 'success', 'title': 'Success', 'text' : str(request_dict['query']['id']) + ' has deleted.'}
