import asyncio
import json
from alpha import __log
from django.db import connection, transaction

from django.db.models import F, Q
from django.core.paginator import Paginator
# from django.contrib.postgres.search import SearchVector
from apps.rubicon_admin.__function import rerank
from apps.rubicon_v3.models import Complement_Code_Mapping_l4
from apps.rubicon_v3.__function.__embedding_rerank import baai_embedding
from datetime import datetime
from icecream import ic
# from pgvector.django import CosineDistance

# structured, unstructured,

def create_code_mapping_l4(request_dict):
    __log.debug(request_dict)
    update_tag = 'create user : ' + request_dict['user']['username'],
    Complement_Code_Mapping_l4.objects.create(
        update_tag=update_tag,
        active=request_dict['query']['active'],
        country_code=request_dict['query']['country_code'],
        category_lv1=request_dict['query']['category_lv1'],
        category_lv2=request_dict['query']['category_lv2'],
        category_lv3=request_dict['query']['category_lv3'],
        type=request_dict['query']['type'],
        condition=request_dict['query']['condition'],
        l4_identifier=request_dict['query']['l4_identifier'],
        l4_product_expression=request_dict['query']['l4_product_expression'],
        code_filter=request_dict['query']['code_filter'],
        product_filter=request_dict['query']['product_filter'],
        site_code='B2C'
    )
    return True, None, None, {'type': 'success', 'title': 'Success', 'text' : request_dict['query']['l4_identifier'] + ' has created.'}

def read_code_mapping_l4(request_dict):
    __log.debug(request_dict)

    qeury = Complement_Code_Mapping_l4.objects
    if 'active' in request_dict['query']:
        qeury = qeury.filter(active=request_dict['query']['active'])
    if 'country_code' in request_dict['query']:
        qeury = qeury.filter(country_code=request_dict['query']['country_code'])
    if 'update_tag' in request_dict['query']:
        qeury = qeury.filter(update_tag=request_dict['query']['update_tag'])
    if 'category_lv1' in request_dict['query']:
        qeury = qeury.filter(category_lv1=request_dict['query']['category_lv1'])
    if 'category_lv2' in request_dict['query']:
        qeury = qeury.filter(category_lv2=request_dict['query']['category_lv2'])
    if 'category_lv3' in request_dict['query']:
        qeury = qeury.filter(category_lv3=request_dict['query']['category_lv3'])
    if 'type' in request_dict['query']:
        qeury = qeury.filter(type=request_dict['query']['type'])
    if 'condition' in request_dict['query']:
        qeury = qeury.filter(condition=request_dict['query']['condition'])
    if 'l4_identifier' in request_dict['query']:
        qeury = qeury.filter(l4_identifier__contains=request_dict['query']['l4_identifier'])
    if 'l4_product_expression' in request_dict['query']:
        qeury = qeury.filter(l4_product_expression__contains=request_dict['query']['l4_product_expression'])
    if 'code_filter' in request_dict['query']:
        qeury = qeury.filter(code_filter=request_dict['query']['code_filter'])
    if 'product_filter' in request_dict['query']:
        qeury = qeury.filter(product_filter=request_dict['query']['product_filter'])

    item_count = qeury.count()
    items = list(qeury.order_by('category_lv1', 'category_lv2', 'category_lv3', 'type', 'condition', 'l4_identifier', 'l4_product_expression').values('id', 'active', 'update_tag', 'country_code', 'category_lv1', 'category_lv2', 'category_lv3', 'type', 'condition', 'l4_identifier', 'l4_product_expression', 'code_filter', 'product_filter'))
    paginator = Paginator(items, per_page=request_dict['paging']['itemsPerPage'], orphans=0)

    page_data = list(paginator.page(int(request_dict['paging']['page'])))

    return True, page_data, [{'itemCount': item_count}], None


def list_update_tag(request_dict):
    distinct_values = Complement_Code_Mapping_l4.objects.filter(~Q(update_tag = None)).values('update_tag').distinct()
    distinct_values_list = [item['update_tag'] for item in distinct_values]
    distinct_values_list = sorted(distinct_values_list)
    return True, distinct_values_list,  None, None

def list_category_lv1(request_dict):
    # __log.debug(request_dict)
    if 'country_code' in request_dict['query']:
        distinct_values = Complement_Code_Mapping_l4.objects.filter(country_code = request_dict['query']['country_code']).filter(~Q(category_lv1 = None)).values('category_lv1').distinct()
        distinct_values_list = [item['category_lv1'] for item in distinct_values]
        distinct_values_list = sorted(distinct_values_list)
        return True, distinct_values_list,  None, None
    else:
        return True, None,  None, None

def list_category_lv2(request_dict):
    # __log.debug(request_dict)
    distinct_values = Complement_Code_Mapping_l4.objects.filter(country_code = request_dict['query']['country_code']).filter(category_lv1 = request_dict['query']['category_lv1']).filter(~Q(category_lv2 = None)).values('category_lv2').distinct()
    distinct_values_list = [item['category_lv2'] for item in distinct_values]
    distinct_values_list = sorted(distinct_values_list)
    return True, distinct_values_list,  None, None

def list_category_lv3(request_dict):
    # __log.debug(request_dict)
    distinct_values = Complement_Code_Mapping_l4.objects.filter(country_code = request_dict['query']['country_code']).filter(category_lv2 = request_dict['query']['category_lv2']).filter(~Q(category_lv3 = None)).values('category_lv3').distinct()
    distinct_values_list = [item['category_lv3'] for item in distinct_values]
    distinct_values_list = sorted(distinct_values_list)
    return True, distinct_values_list,  None, None

def update_code_mapping_l4(request_dict):
    # __log.debug(request_dict)
    update_tag = 'update user : ' + request_dict['user']['username'],
    Complement_Code_Mapping_l4.objects.filter(id=request_dict['query']['id']).update(
        active=request_dict['query']['active'],
        update_tag=update_tag,
        country_code=request_dict['query']['country_code'],
        category_lv1=request_dict['query']['category_lv1'],
        category_lv2=request_dict['query']['category_lv2'],
        category_lv3=request_dict['query']['category_lv3'],
        type=request_dict['query']['type'],
        condition=request_dict['query']['condition'],
        l4_identifier=request_dict['query']['l4_identifier'],
        l4_product_expression=request_dict['query']['l4_product_expression'],
        code_filter=request_dict['query']['code_filter'],
        product_filter=request_dict['query']['product_filter'],
        site_code='B2C'
    )

    return True, None, None, {
        'type': 'success',
        'title': 'Success',
        'text': f"{request_dict['query']['l4_identifier']} has been updated."
    }

def delete_code_mapping_l4(request_dict):
    Complement_Code_Mapping_l4.objects.filter(id=request_dict['query']['id']).delete()
    return True, None, None, {'type': 'success', 'title': 'Success', 'text' : str(request_dict['query']['id']) + ' has deleted.'}