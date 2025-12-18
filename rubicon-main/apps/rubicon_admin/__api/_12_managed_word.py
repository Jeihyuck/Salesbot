import json
import asyncio
from alpha import __log
from icecream import ic
from datetime import datetime

from django.db.models import F, Q
from django.core.paginator import Paginator
from django.db import connection, transaction

from apps.rubicon_v3.models import Managed_Word

def create_managed_word(request_dict):
    update_tag = 'create user : ' + request_dict['user']['username']
    Managed_Word.objects.create(
        active=True,
        update_tag=update_tag,
        module=request_dict['query']['module'],
        type=request_dict['query']['type'],
        word=request_dict['query']['word'],
        replace_word=request_dict['query']['replace_word'],
        processing=request_dict['query']['processing']
    )
    return True, None, None, {'type': 'success', 'title': 'Success', 'text' : request_dict['query']['word'] + ' has added.'}

def read_managed_word(request_dict):
    __log.debug(request_dict)

    qeury = Managed_Word.objects

    if 'module' in request_dict['query']:
        qeury = qeury.filter(module=request_dict['query']['module'])
    if 'type' in request_dict['query']:
        qeury = qeury.filter(type=request_dict['query']['type'])
    if 'processing' in request_dict['query']:
        qeury = qeury.filter(processing=request_dict['query']['processing'])
    if 'word' in request_dict['query']:
        qeury = qeury.filter(word__contains=request_dict['query']['word'])

    item_count = qeury.count()
    __log.debug(item_count)
    if item_count == 0:
        return True, [], [{'itemCount': 0}], None
    else:
        items = list(qeury.order_by('-update_tag').values('id', 'active', 'update_tag', 'module', 'type', 'word', 'replace_word', 'processing'))
        paginator = Paginator(items, per_page=request_dict['paging']['itemsPerPage'], orphans=0)

        page_data = list(paginator.page(int(request_dict['paging']['page'])))

        return True, page_data, [{'itemCount': item_count}], None

def update_managed_word(request_dict):
    update_tag = 'update user : ' + request_dict['user']['username']


    Managed_Word.objects.filter(id=request_dict['query']['id']).update(
        active=True,
        update_tag=update_tag,
        module=request_dict['query']['module'],
        type=request_dict['query']['type'],
        word=request_dict['query']['word'],
        replace_word=request_dict['query']['replace_word'],
        processing=request_dict['query']['processing']
    )

    return True, None, None, {'type': 'success', 'title': 'Success', 'text' : request_dict['query']['word'] + ' has updated.'}

def delete_managed_word(request_dict):
    Managed_Word.objects.filter(id=request_dict['query']['id']).delete()
    return True, None, None, {'type': 'success', 'title': 'Success', 'text' : request_dict['query']['word'] + ' has deleted.'}

def list_module(request_dict):
    distinct_values = Managed_Word.objects.filter(~Q(module = None)).values('module').distinct()
    distinct_values_list = [item['module'] for item in distinct_values]
    distinct_values_list = sorted(distinct_values_list)
    return True, distinct_values_list,  None, None

def list_type(request_dict):
    distinct_values = Managed_Word.objects.filter(~Q(type = None)).values('type').distinct()
    distinct_values_list = [item['type'] for item in distinct_values]
    distinct_values_list = sorted(distinct_values_list)
    return True, distinct_values_list,  None, None

def list_processing(request_dict):
    distinct_values = Managed_Word.objects.filter(~Q(processing = None)).values('processing').distinct()
    distinct_values_list = [item['processing'] for item in distinct_values]
    distinct_values_list = sorted(distinct_values_list)
    return True, distinct_values_list,  None, None

def list_update_tag(request_dict):
    distinct_values = Managed_Word.objects.filter(~Q(update_tag = None)).values('update_tag').distinct()
    distinct_values_list = [item['update_tag'] for item in distinct_values]
    distinct_values_list = sorted(distinct_values_list)
    return True, distinct_values_list,  None, None