import json
from alpha import __log
from django.db.models import F, Q
from django.core.paginator import Paginator
from django.contrib.postgres.search import SearchVector

from apps.rubicon_v3.models import Prompt_Template


def create_prompt_template(request_dict):

    Prompt_Template.objects.create(
        active=request_dict['query']['active'],
        country_code=request_dict['query']['country_code'],
        site_cd=request_dict['query'].get('site_cd', 'B2C'),
        channel=request_dict['query'].get('channel', ''),
        channel_filter=json.loads(request_dict['query'].get('channel_filter', '')),
        response_type=request_dict['query']['response_type'],
        category_lv1=request_dict['query']['category_lv1'],
        category_lv2=request_dict['query']['category_lv2'],
        tag=request_dict['query'].get('tag', ''),
        description=request_dict['query'].get('description', ''),
        prompt=request_dict['query']['prompt']
    )
    return True, None, None, {'type': 'success', 'title': 'Successfully Created', 'text' : 'Successfully added up prompt'}

def read_prompt_template(request_dict):
    __log.debug(request_dict)
    qeury = Prompt_Template.objects

    if 'active' in request_dict['query']:
        qeury = qeury.filter(active=request_dict['query']['active'])
    if 'country_code' in request_dict['query']:
        qeury = qeury.filter(country_code=request_dict['query']['country_code'])
    if 'response_type' in request_dict['query']:
        qeury = qeury.filter(response_type=request_dict['query']['response_type'])
    if 'category_lv1' in request_dict['query']:
        qeury = qeury.filter(category_lv1=request_dict['query']['category_lv1'])
    if 'category_lv2' in request_dict['query']:
        qeury = qeury.filter(category_lv2=request_dict['query']['category_lv2'])
                 
    item_count = qeury.count()
    items = list(qeury.order_by('active', 'country_code', 'site_cd', 'channel', 'response_type', 'category_lv1', 'category_lv2').values('id', 'active', 'country_code', 'site_cd', 'channel', 'response_type', 'category_lv1', 'category_lv2', 'prompt', 'tag', 'description', 'channel_filter', 'created_on', 'updated_on'))
    paginator = Paginator(items, per_page=request_dict['paging']['itemsPerPage'], orphans=0)

    page_data = list(paginator.page(int(request_dict['paging']['page'])))
    # __log.debug(page_data)

    return True, page_data, [{'itemCount': item_count}], None


def update_prompt_template_only(request_dict):
    # __log.debug(request_dict)?
    Prompt_Template.objects.filter(id=request_dict['query']['id']).update(
        prompt=request_dict['query']['prompt']
    )
    return True, None, None, None

def update_prompt_template(request_dict):
    # __log.debug(request_dict)
    # __log.debug(json.loads(request_dict['query'].get('channel_filter', '')))
    Prompt_Template.objects.filter(id=request_dict['query']['id']).update(
        active=request_dict['query']['active'],
        country_code=request_dict['query']['country_code'],
        site_cd=request_dict['query'].get('site_cd', 'B2C'),
        channel=request_dict['query']['channel'],
        response_type=request_dict['query']['response_type'],
        category_lv1=request_dict['query']['category_lv1'],
        category_lv2=request_dict['query']['category_lv2'],
        channel_filter=json.loads(request_dict['query'].get('channel_filter', '')),
        prompt=request_dict['query']['prompt'],
        tag=request_dict['query'].get('tag', ''),
        description=request_dict['query'].get('description', '')
    )
    return True, None, None, None

def delete_prompt_template(request_dict):
    # __log.debug(request_dict)
    Prompt_Template.objects.filter(id=request_dict['query']['id']).delete()
    return True, None, None, None


def list_response_type(request_dict):
    distinct_values = Prompt_Template.objects.filter(~Q(response_type = None))\
        .filter(active=request_dict['query']['active'])\
        .filter(country_code=request_dict['query']['country_code'])\
        .values('response_type').distinct()
    distinct_values_list = [item['response_type'] for item in distinct_values]
    distinct_values_list = sorted(distinct_values_list)
    return True, distinct_values_list,  None, None

def list_category_lv1(request_dict):
    distinct_values = Prompt_Template.objects.filter(~Q(category_lv1 = None))\
        .filter(active=request_dict['query']['active'])\
        .filter(country_code=request_dict['query']['country_code'])\
        .filter(response_type=request_dict['query']['response_type']).values('category_lv1').distinct()
    distinct_values_list = [item['category_lv1'] for item in distinct_values]
    distinct_values_list = sorted(distinct_values_list)
    return True, distinct_values_list,  None, None

def list_category_lv2(request_dict):
    distinct_values = Prompt_Template.objects.filter(~Q(category_lv2 = None))\
        .filter(active=request_dict['query']['active'])\
        .filter(country_code=request_dict['query']['country_code'])\
        .filter(response_type=request_dict['query']['response_type'])\
        .filter(category_lv1=request_dict['query']['category_lv1']).values('category_lv2').distinct()
    distinct_values_list = [item['category_lv2'] for item in distinct_values]
    distinct_values_list = sorted(distinct_values_list)
    return True, distinct_values_list,  None, None