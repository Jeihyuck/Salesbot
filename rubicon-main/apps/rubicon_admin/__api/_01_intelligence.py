import json
from alpha import __log
from django.db.models import F, Q
from django.core.paginator import Paginator
from django.contrib.postgres.search import SearchVector

from apps.rubicon_v3.models import Intelligence_V2

def create_intelligence(request_dict):
    __log.debug(request_dict)
    Intelligence_V2.objects.create(
        intelligence=request_dict['query']['intelligence'],
        site_cd='B2C',  # Default site_cd, can be changed later
        sub_intelligence=request_dict['query']['sub_intelligence'],
        intelligence_desc=request_dict['query']['intelligence_desc'],
        intelligence_meta=json.loads(request_dict['query']['intelligence_meta']),
        channel=json.loads(request_dict['query']['channel']),
        base=request_dict['query']['base'],
        product_card=request_dict['query']['product_card'],
        related_query=request_dict['query']['related_query'],
        hyperlink=request_dict['query']['hyperlink'],
        media=request_dict['query']['media'],
        map=request_dict['query']['map'],
    )
    return True, None, None, {'type': 'success', 'title': 'Success', 'text' : request_dict['query']['intelligence'] + ':' + request_dict['query']['sub_intelligence'] + ' has added.'}

def read_intelligence(request_dict):
    __log.debug(request_dict)

    query = Intelligence_V2.objects

    if 'intelligence' in request_dict['query']:
        query = query.filter(intelligence=request_dict['query']['intelligence'])
    if 'product_card' in request_dict['query']:
        query = query.filter(product_card=request_dict['query']['product_card'])
    if 'base' in request_dict['query']:
        query = query.filter(base=request_dict['query']['base'])
    if 'hyperlink' in request_dict['query']:
        query = query.filter(hyperlink=request_dict['query']['hyperlink'])
    if 'media' in request_dict['query']:
        query = query.filter(media=request_dict['query']['media'])
    if 'map' in request_dict['query']:
        query = query.filter(map=request_dict['query']['map'])

    item_count = query.count()
    items = list(query.order_by('intelligence', 'sub_intelligence').values('id', 'intelligence', 'sub_intelligence', 'intelligence_desc', 'intelligence_meta', 'channel', 'base', 'product_card', 'related_query', 'hyperlink', 'media', 'map'))
    paginator = Paginator(items, per_page=request_dict['paging']['itemsPerPage'], orphans=0)

    page_data = list(paginator.page(int(request_dict['paging']['page'])))

    return True, page_data, [{'itemCount': item_count}], None

def list_intelligence(request_dict):
    query = Intelligence_V2.objects
    items = list(query.order_by('intelligence').values('intelligence').distinct())

    return_list = []
    for item in items:
        return_list.append(item['intelligence'])

    return True, return_list, None, None

def update_intelligence(request_dict):
    # __log.debug(request_dict)
    Intelligence_V2.objects.filter(id=request_dict['query']['id']).update(
        site_cd='B2C',  # Default site_cd, can be changed later
        intelligence=request_dict['query']['intelligence'],
        sub_intelligence=request_dict['query']['sub_intelligence'],
        intelligence_desc=request_dict['query']['intelligence_desc'],
        intelligence_meta=json.loads(request_dict['query']['intelligence_meta']),
        channel=json.loads(request_dict['query']['channel']),
        base=request_dict['query']['base'],
        product_card=request_dict['query']['product_card'],
        related_query=request_dict['query']['related_query'],
        hyperlink=request_dict['query']['hyperlink'],
        media=request_dict['query']['media'],
        map=request_dict['query']['map'],
    )
    return True, None, None, {'type': 'success', 'title': 'Success', 'text' : request_dict['query']['intelligence'] + ':' + request_dict['query']['sub_intelligence'] + ' has updated.'}

def delete_intelligence(request_dict):
    # __log.debug(request_dict)
    Intelligence_V2.objects.filter(id=request_dict['query']['id']).delete()
    return True, None, None, {'type': 'success', 'title': 'Success', 'text' : request_dict['query']['intelligence'] + ':' + request_dict['query']['sub_intelligence'] + ' has deleted.'}
