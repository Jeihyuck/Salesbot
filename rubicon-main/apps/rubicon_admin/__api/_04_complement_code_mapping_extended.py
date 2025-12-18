import asyncio
import json
from alpha import __log
from django.db import connection, transaction

from django.db.models import F, Q
from django.core.paginator import Paginator
# from django.contrib.postgres.search import SearchVector
from apps.rubicon_admin.__function import rerank
from apps.rubicon_v3.models import Complement_Code_Mapping_Extended
from apps.rubicon_v3.__function.__embedding_rerank import baai_embedding
from datetime import datetime
from icecream import ic
# from pgvector.django import CosineDistance

# structured, unstructured,

def create_code_mapping_extended(request_dict):
    __log.debug(request_dict)

    return True, None, None, {'type': 'success', 'title': 'Success', 'text' : request_dict['query']['mapping_code'] + ' has created.'}

def read_code_mapping_extended(request_dict):
    __log.debug(request_dict)

    qeury = Complement_Code_Mapping_Extended.objects
    if 'active' in request_dict['query']:
        qeury = qeury.filter(active=request_dict['query']['active'])
    if 'country_code' in request_dict['query']:
        qeury = qeury.filter(country_code=request_dict['query']['country_code'])
    if 'update_tag' in request_dict['query']:
        qeury = qeury.filter(update_tag=request_dict['query']['update_tag'])
    if 'edge' in request_dict['query']:
        qeury = qeury.filter(edge=request_dict['query']['edge'])
    if 'category_lv1' in request_dict['query']:
        qeury = qeury.filter(category_lv1=request_dict['query']['category_lv1'])
    if 'category_lv2' in request_dict['query']:
        qeury = qeury.filter(category_lv2=request_dict['query']['category_lv2'])
    if 'category_lv3' in request_dict['query']:
        qeury = qeury.filter(category_lv3=request_dict['query']['category_lv3'])
    if 'mapping_code' in request_dict['query']:
        qeury = qeury.filter(mapping_code=request_dict['query']['mapping_code'])


    item_count = qeury.count()
    __log.debug(item_count)
    items = list(qeury.order_by('-id').values('id', 'active', 'update_tag', 'country_code', 'category_lv1', 'category_lv2', 'category_lv3', 'mapping_code', 'edge', 'extended_info', 'created_on', 'updated_on'))
    paginator = Paginator(items, per_page=request_dict['paging']['itemsPerPage'], orphans=0)

    page_data = list(paginator.page(int(request_dict['paging']['page'])))

    return True, page_data, [{'itemCount': item_count}], None

def list_distinct_edge_list(request_dict):
    distinct_values = Complement_Code_Mapping_Extended.objects.values('edge').distinct()
    distinct_values_list = [item['edge'] for item in distinct_values]
    distinct_values_list = sorted(distinct_values_list)
    return True, distinct_values_list,  None, None

def list_update_tag(request_dict):
    distinct_values = Complement_Code_Mapping_Extended.objects.filter(~Q(update_tag = None)).values('update_tag').distinct()
    distinct_values_list = [item['update_tag'] for item in distinct_values]
    distinct_values_list = sorted(distinct_values_list)
    return True, distinct_values_list,  None, None

def list_category_lv1(request_dict):
    # __log.debug(request_dict)
    if 'country_code' in request_dict['query']:
        distinct_values = Complement_Code_Mapping_Extended.objects.filter(country_code = request_dict['query']['country_code']).filter(~Q(category_lv1 = None)).values('category_lv1').distinct()
        distinct_values_list = [item['category_lv1'] for item in distinct_values]
        distinct_values_list = sorted(distinct_values_list)
        return True, distinct_values_list,  None, None
    else:
        return True, None,  None, None

def list_category_lv2(request_dict):
    # __log.debug(request_dict)
    distinct_values = Complement_Code_Mapping_Extended.objects.filter(country_code = request_dict['query']['country_code']).filter(category_lv1 = request_dict['query']['category_lv1']).filter(~Q(category_lv2 = None)).values('category_lv2').distinct()
    distinct_values_list = [item['category_lv2'] for item in distinct_values]
    distinct_values_list = sorted(distinct_values_list)
    return True, distinct_values_list,  None, None

def list_category_lv3(request_dict):
    # __log.debug(request_dict)
    distinct_values = Complement_Code_Mapping_Extended.objects.filter(country_code = request_dict['query']['country_code']).filter(category_lv2 = request_dict['query']['category_lv2']).filter(~Q(category_lv3 = None)).values('category_lv3').distinct()
    distinct_values_list = [item['category_lv3'] for item in distinct_values]
    distinct_values_list = sorted(distinct_values_list)
    return True, distinct_values_list,  None, None

def update_code_mapping_extended(request_dict):
    __log.debug(request_dict)
    with transaction.atomic():
        with connection.cursor() as cursor:
            # Generate the embedding asynchronously
            embedding = baai_embedding(request_dict['query']['expression'],'test')

            if 'category_lv1' in request_dict['query']:
                category_lv1 = request_dict['query']['category_lv1']
            else:
                category_lv1 = ''

            if 'category_lv2' in request_dict['query']:
                category_lv2 = request_dict['query']['category_lv2']
            else:
                category_lv2 = ''

            if 'category_lv3' in request_dict['query']:
                if request_dict['query']['category_lv3'] != None:
                    category_lv3 = request_dict['query']['category_lv3']
                else:
                    category_lv3 = ''
            else:
                category_lv3 = ''
            # Prepare the UPDATE SQL query with parameter placeholders
            query = """
                UPDATE rubicon_v3_Complement_Code_Mapping_Extended
                SET
                    active = TRUE,
                    expression_embedding = %s,
                    expression = %s,
                    country_code = %s,
                    field = %s,
                    mapping_code = %s,
                    category_lv1 = %s,
                    category_lv2 = %s,
                    category_lv3 = %s,
                    update_tag = %s,
                    structured = %s,
                    unstructured = %s,
                    updated_on = %s
                WHERE id = %s
            """
 
            # Parameters to prevent SQL injection
            params = (
                embedding[0],
                request_dict['query']['expression'],
                request_dict['query']['country_code'],
                request_dict['query']['field'],
                request_dict['query']['mapping_code'],
                category_lv1,
                category_lv2,
                category_lv3,
                'update user : ' + request_dict['user']['username'],
                request_dict['query']['structured'],
                request_dict['query']['unstructured'],
                datetime.now(),
                request_dict['query']['id']  # This is used in the WHERE clause
            )

            # Execute the query with parameters
            cursor.execute(query, params)

    return True, None, None, {
        'type': 'success',
        'title': 'Success',
        'text': f"{request_dict['query']['expression']} has been updated."
    }

def delete_code_mapping_extended(request_dict):
    Complement_Code_Mapping_Extended.objects.filter(id=request_dict['query']['id']).delete()
    return True, None, None, {'type': 'success', 'title': 'Success', 'text' : str(request_dict['query']['id']) + ' has deleted.'}