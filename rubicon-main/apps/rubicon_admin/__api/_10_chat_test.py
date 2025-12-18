import django_rq
from alpha import __log
from icecream import ic
from django.db.models import F, Q
from django.core.paginator import Paginator
from django.contrib.postgres.search import SearchVector

from apps.rubicon_admin.models import Chat_Test
# from apps.rubicon.views import rubicon_debug

import re
import uuid
import redis
import asyncio
from alpha.settings import REDIS_ORCHESTRATOR_IP, REDIS_PASSWORD, REDIS_PORT
from django.http import StreamingHttpResponse
# from apps.rubicon.__function.__redis import store_dict_with_expiry
from apps.__common import multi_threading
from apps.rubicon_admin.__function.chat_test import chat_test_module

def read_chat_test(request_dict):
    __log.debug(request_dict)
    qeury = Chat_Test.objects
    if 'case' in request_dict['query']:
        qeury = qeury.filter(case=request_dict['query']['case'])
    if 'test_id' in request_dict['query']:
        qeury = qeury.filter(test_id=request_dict['query']['test_id'])
    if 'language' in request_dict['query']:
        qeury = qeury.filter(language=request_dict['query']['language'])
    if 'channel' in request_dict['query']:
        qeury = qeury.filter(channel=request_dict['query']['channel'])
    if 'country' in request_dict['query']:
        qeury = qeury.filter(country=request_dict['query']['country'])
    if 'intelligence' in request_dict['query']:
        qeury = qeury.filter(intelligence=request_dict['query']['intelligence'])

                 
    item_count = qeury.count()
    items = list(qeury.order_by('-updated_on').values('id', 'test_query_id', 'test_id', 'case', 'language', 'channel', 'country', 'intelligence', 'query', 'response', 'tested'))
    paginator = Paginator(items, per_page=request_dict['paging']['itemsPerPage'], orphans=0)

    page_data = list(paginator.page(int(request_dict['paging']['page'])))
    # __log.debug(page_data)

    return True, page_data, [{'itemCount': item_count}], None



def list_test_id(request_dict):
    qeury = Chat_Test.objects
    items = list(qeury.order_by('test_id').values('test_id').distinct())

    return_list = []
    for item in items:
        return_list.append(item['test_id'])
    return True, return_list, None, None



def delete_chat_test(request_dict):
    ic(request_dict)
    if request_dict['query']['testMethod'] == 'items':
        items = list(Chat_Test.objects.filter(id__in = request_dict['query']['selected']).values('id', 'country', 'query'))

    elif request_dict['query']['testMethod'] == 'testId':
        items = list(Chat_Test.objects.filter(test_id = request_dict['query']['selectedTestId']).values('id', 'country', 'query'))

    for item in items:
        Chat_Test.objects.filter(id=item['id']).delete()

    return True, None, None, {'type': 'success', 'title': 'Test Job has deleted', 'text' : 'Test job has deleted.'}



def chat_test(request_dict):
    # ic(request_dict)
    if request_dict['query']['testMethod'] == 'items':
        items = list(Chat_Test.objects.filter(id__in = request_dict['query']['selected']).values('id', 'country', 'query'))

    elif request_dict['query']['testMethod'] == 'testId':
        items = list(Chat_Test.objects.filter(test_id = request_dict['query']['selectedTestId']).values('id', 'country', 'query'))

    for item in items:
        # ic(item)
        Chat_Test.objects.filter(id=item['id']).update(response='', tested=False)


    django_rq.enqueue(chat_test_module, request_dict)

    return True, None, None, {'type': 'success', 'title': 'Test Job has created', 'text' : 'Test job has submitted for testing. will completed in a few miniutes depends on the size of test items.'}
