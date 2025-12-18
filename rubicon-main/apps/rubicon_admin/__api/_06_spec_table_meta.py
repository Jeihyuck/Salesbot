import json
import asyncio
from icecream import ic
from alpha import __log
from datetime import datetime
# from django.db.models import F, Q
from django.core.paginator import Paginator
from django.db import connection, transaction

from apps.rubicon_v3.models import Spec_Table_Meta

def create_spec_table_meta(request_dict):
    with connection.cursor() as cursor:
        query = f"""INSERT INTO rubicon_v3_spec_table_meta (country_code, category_lv1, category_lv2, category_lv3, model_code, spec_lv1, spec_lv2, spec_value, created_on, updated_on)
                VALUES ('{request_dict['query']['country_code']}', '{request_dict['query']['category_lv1']}', '{request_dict['query']['category_lv2']}', '{request_dict['query']['category_lv3']}', '{request_dict['query']['model_code']}', '{request_dict['query']['spec_lv1']}', '{request_dict['query']['spec_lv2']}', '{request_dict['query']['spec_value']}', '{datetime.now()}', '{datetime.now()}')"""
        cursor.execute(query)
        transaction.commit()
    return True, None, None, {'type': 'success', 'title': 'Success', 'text' : request_dict['query']['spec_value'] + ' has created.'}

def read_spec_table_meta(request_dict):
    query = Spec_Table_Meta.objects
    if 'country_code' in request_dict['query']:
        query = query.filter(country_code=request_dict['query']['country_code'])
    if 'category_lv1' in request_dict['query']:
        query = query.filter(category_lv1=request_dict['query']['category_lv1'])
    if 'category_lv2' in request_dict['query']:
        query = query.filter(category_lv2=request_dict['query']['category_lv2'])
    if 'category_lv3' in request_dict['query']:
        query = query.filter(category_lv3=request_dict['query']['category_lv3'])
    if 'model_code' in request_dict['query']:
        query = query.filter(model_code=request_dict['query']['model_code'])
    if 'spec_lv1' in request_dict['query']:
        query = query.filter(spec_lv1=request_dict['query']['spec_lv1'])
    if 'spec_lv2' in request_dict['query']:
        query = query.filter(spec_lv2=request_dict['query']['spec_lv2'])
    if 'spec_value' in request_dict['query']:
        query = query.filter(spec_value=request_dict['query']['spec_value'])
                   
    item_count = query.count()
    items = list(query.order_by('id').values('id','country_code', 'category_lv1', 'category_lv2', 'category_lv3', 'model_code', 'spec_lv1', 'spec_lv2', 'spec_value'))
    paginator = Paginator(items, per_page=request_dict['paging']['itemsPerPage'], orphans=0)

    page_data = list(paginator.page(int(request_dict['paging']['page'])))

    return True, page_data, [{'itemCount': item_count}], None

def update_spec_table_meta(request_dict):
    __log.debug(request_dict)
    with transaction.atomic():
        with connection.cursor() as cursor:
            # Generate the embedding asynchronously
            query = """
                UPDATE rubicon_v3_spec_table_meta
                SET
                    country_code = %s,
                    category_lv1 = %s,
                    category_lv2 = %s,
                    category_lv3 = %s,
                    model_code = %s,
                    spec_lv1 = %s,
                    spec_lv2 = %s,
                    spec_value = %s,
                    updated_on = %s
                WHERE id = %s
            """
            params = (
                request_dict['query']['country_code'],
                request_dict['query']['category_lv1'],
                request_dict['query']['category_lv2'],
                request_dict['query']['category_lv3'],
                request_dict['query']['model_code'],
                request_dict['query']['spec_lv1'],
                request_dict['query']['spec_lv2'],
                request_dict['query']['spec_value'],
                datetime.now(),
                request_dict['query']['id']  # This is used in the WHERE clause
            )

            # Execute the query with parameters
            cursor.execute(query, params)

    return True, None, None, {
        'type': 'success',
        'title': 'Success',
        'text': f"{request_dict['query']['spec_value']} has been updated."
    }

def delete_spec_table_meta(request_dict):
    Spec_Table_Meta.objects.filter(id=request_dict['query']['id']).delete()
    return True, None, None, {'type': 'success', 'title': 'Success', 'text' : str(request_dict['query']['id']) + ' has deleted.'}