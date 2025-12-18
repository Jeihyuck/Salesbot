import asyncio
import json
from alpha import __log
from django.db import connection, transaction

from django.db.models import F, Q
from django.core.paginator import Paginator
# from django.contrib.postgres.search import SearchVector
from apps.rubicon_admin.__function import rerank
from apps.rubicon_v3.models import Complement_Code_Mapping
from apps.rubicon_v3.__function.__embedding_rerank import baai_embedding
from datetime import datetime
from icecream import ic
# from pgvector.django import CosineDistance

# structured, unstructured,

def create_code_mapping(request_dict):
    # __log.debug(request_dict)

    with connection.cursor() as cursor:
        embedding = baai_embedding(request_dict['query']['expression'],'test')
        if 'category_lv1'in request_dict['query']:
            category_lv1 = request_dict['query']['category_lv1']
        else:
            category_lv1 = 'NA'

        if 'category_lv2' in request_dict['query']:
            category_lv2 = request_dict['query']['category_lv2']
        else:
            category_lv2 = 'NA'

        if 'category_lv3' in request_dict['query']:
            if request_dict['query']['category_lv3'] != None:
                category_lv3 = request_dict['query']['category_lv3']
            else:
                category_lv3 = 'NA'
        else:
            category_lv3 = 'NA'
        update_tag = 'create user : ' + request_dict['user']['username'],
        # ic(update_tag)
        query = f"""INSERT INTO rubicon_v3_complement_code_mapping 
                    (type,
                     embedding,
                     active, 
                     update_tag, 
                     expression, 
                     country_code,
                     field,
                     mapping_code,
                     site_cd,
                     category_lv1, category_lv2, category_lv3, created_on, updated_on)
                VALUES ('{request_dict['query']['type']}',
                        '{embedding[0]}',
                        TRUE,
                        '{update_tag[0]}',
                        '{request_dict['query']['expression']}',
                        '{request_dict['query']['country_code']}',
                        '{request_dict['query']['field']}',
                        '{request_dict['query']['mapping_code']}',
                        'B2C',
                        '{category_lv1}', '{category_lv2}', '{category_lv3}', '{datetime.now()}', '{datetime.now()}')"""

        cursor.execute(query)
        transaction.commit()
    return True, None, None, {'type': 'success', 'title': 'Success', 'text' : request_dict['query']['expression'] + ' has created.'}
    # except Exception as e:
    #     return False, None, None, {'type': 'error', 'title': 'Error', 'text' : str(e)}

def read_code_mapping(request_dict):
    __log.debug(request_dict)
    if 'embeddingSearch' in request_dict['query']:
        with connection.cursor() as cursor:
            embedding = baai_embedding(request_dict['query']['embeddingSearch'],'test')
            # __log.debug(embedding[0][:10])

            filter_string = ''
            filter_list = []
            if 'active' in request_dict['query']:
                if request_dict['query']['active'] == True:
                    filter_list.append(f' active = TRUE')
                else:
                    filter_list.append(f' active = FALSE')

            if 'country_code' in request_dict['query']:
                filter_list.append(f' country_code = \'{request_dict['query']['country_code']}\'')
            if 'category_lv1' in request_dict['query']:
                filter_list.append(f' category_lv1 = \'{request_dict['query']['category_lv1']}\'')
            if 'category_lv2' in request_dict['query']:
                filter_list.append(f' category_lv2 = \'{request_dict['query']['category_lv2']}\'')
            if 'category_lv3' in request_dict['query']:
                filter_list.append(f' category_lv3 = \'{request_dict['query']['category_lv3']}\'')
            if 'field' in request_dict['query']:
                filter_list.append(f' field = \'{request_dict['query']['field']}\'')
            if 'type' in request_dict['query']:
                filter_list.append(f' type = \'{request_dict['query']['type']}\'')

            if filter_list != []:
                filter_string = 'WHERE ' + " AND ".join(filter_list)

            query = f"""
            SELECT 
                id,
                active,
                update_tag,
                expression,
                country_code::text,
                field::text,
                type::text,
                mapping_code::text,
                category_lv1::text,
                category_lv2::text,
                category_lv3::text,
                embedding <=> '{str(embedding[0])}' AS distance
            FROM rubicon_v3_complement_code_mapping {filter_string}
            ORDER BY embedding <=> '{str(embedding[0])}'
            LIMIT 20;
            """

            # __log.debug(query)

            cursor.execute(query)
            result = cursor.fetchall()

            page_data = []
            key_list = ['id', 'active', 'update_tag', 'expression', 'country_code', 'field', 'type', 'mapping_code', 'category_lv1', 'category_lv2', 'category_lv3', 'distance']
            for row in result:
                # ic(row)
                row_item = {}
                for index, key in enumerate(key_list):
                    # ic(index, key)
                    if key == 'distance':
                        row_item[key] = round(1 - row[index], 2)
                    else:
                        row_item[key] = row[index]
                page_data.append(row_item)

            # __log.debug(page_data)
            if len(page_data) == 0:
                return True, [], [{'itemCount': 0}], None
            else:

                page_data = rerank.calculate_rerank_score(request_dict['query']['embeddingSearch'], page_data, 'expression')
                # page_data = sorted(page_data, key=lambda x: page_data[x]["rerank_score"], reverse=True)
                page_data = sorted(page_data, key=lambda x: x["rerank_score"], reverse=True)
                item_count = request_dict['paging']['itemsPerPage']
                return True, page_data, [{'itemCount': item_count}], None

    else: ## Exact Search
        qeury = Complement_Code_Mapping.objects
        if 'active' in request_dict['query']:
            qeury = qeury.filter(active=request_dict['query']['active'])
        if 'update_tag' in request_dict['query']:
            qeury = qeury.filter(update_tag=request_dict['query']['update_tag'])
        if 'category_lv1' in request_dict['query']:
            qeury = qeury.filter(category_lv1=request_dict['query']['category_lv1'])
        if 'category_lv2' in request_dict['query']:
            qeury = qeury.filter(category_lv2=request_dict['query']['category_lv2'])
        if 'category_lv3' in request_dict['query']:
            qeury = qeury.filter(category_lv3=request_dict['query']['category_lv3'])
        if 'field' in request_dict['query']:
            qeury = qeury.filter(field=request_dict['query']['field'])
        if 'type' in request_dict['query']:
            qeury = qeury.filter(type=request_dict['query']['type'])
        if 'expression' in request_dict['query']:
            qeury = qeury.filter(expression__contains=request_dict['query']['expression'])
        if 'country_code' in request_dict['query']:
            qeury = qeury.filter(country_code=request_dict['query']['country_code'])

        item_count = qeury.count()

        if item_count == 0:
            return True, [], [{'itemCount': 0}], None
        else:
            items = list(qeury.order_by('-id').values('id', 'active', 'update_tag', 'expression', 'country_code', 'field', 'mapping_code', 'category_lv1', 'category_lv2', 'category_lv3', 'type', 'created_on', 'updated_on'))
            paginator = Paginator(items, per_page=request_dict['paging']['itemsPerPage'], orphans=0)

            page_data = list(paginator.page(int(request_dict['paging']['page'])))

            return True, page_data, [{'itemCount': item_count}], None
   

def list_distinct_field_list(request_dict):
    distinct_values = Complement_Code_Mapping.objects.values('field').distinct()
    distinct_values_list = [item['field'] for item in distinct_values]
    distinct_values_list = sorted(distinct_values_list)
    return True, distinct_values_list,  None, None

def list_type(request_dict):
    distinct_values = Complement_Code_Mapping.objects.filter(~Q(type = None)).values('type').distinct()
    distinct_values_list = [item['type'] for item in distinct_values]
    distinct_values_list = sorted(distinct_values_list)
    return True, distinct_values_list,  None, None

def list_update_tag(request_dict):
    distinct_values = Complement_Code_Mapping.objects.filter(~Q(update_tag = None)).values('update_tag').distinct()
    distinct_values_list = [item['update_tag'] for item in distinct_values]
    distinct_values_list = sorted(distinct_values_list)
    return True, distinct_values_list,  None, None

def list_category_lv1(request_dict):
    # __log.debug(request_dict)
    if 'country_code' in request_dict['query']:
        distinct_values = Complement_Code_Mapping.objects.filter(country_code = request_dict['query']['country_code']).filter(~Q(category_lv1 = None)).values('category_lv1').distinct()
        distinct_values_list = [item['category_lv1'] for item in distinct_values]
        distinct_values_list = sorted(distinct_values_list)
        return True, distinct_values_list,  None, None
    else:
        return True, None,  None, None

def list_category_lv2(request_dict):
    # __log.debug(request_dict)
    distinct_values = Complement_Code_Mapping.objects.filter(category_lv1 = request_dict['query']['category_lv1']).filter(~Q(category_lv2 = None)).values('category_lv2').distinct()
    distinct_values_list = [item['category_lv2'] for item in distinct_values]
    distinct_values_list = sorted(distinct_values_list)
    return True, distinct_values_list,  None, None

def list_category_lv3(request_dict):
    # __log.debug(request_dict)
    distinct_values = Complement_Code_Mapping.objects.filter(category_lv2 = request_dict['query']['category_lv2']).filter(~Q(category_lv3 = None)).values('category_lv3').distinct()
    distinct_values_list = [item['category_lv3'] for item in distinct_values]
    distinct_values_list = sorted(distinct_values_list)
    return True, distinct_values_list,  None, None

def update_code_mapping(request_dict):
    __log.debug(request_dict)
    with transaction.atomic():
        with connection.cursor() as cursor:
            # Generate the embedding asynchronously
            embedding = baai_embedding(request_dict['query']['expression'],'test')

            if 'active' in request_dict['query']:
                if request_dict['query']['active'] == True:
                    active = 'TRUE'
                else:
                    active = 'FALSE'
            else:
                active = 'TRUE'


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
                UPDATE rubicon_v3_complement_code_mapping
                SET
                    active = %s,
                    embedding = %s,
                    expression = %s,
                    country_code = %s,
                    field = %s,
                    type= %s,
                    mapping_code = %s,
                    category_lv1 = %s,
                    category_lv2 = %s,
                    category_lv3 = %s,
                    update_tag = %s,
                    updated_on = %s
                WHERE id = %s
            """
 
            # Parameters to prevent SQL injection
            params = (
                active,
                embedding[0],
                request_dict['query']['expression'],
                request_dict['query']['country_code'],
                request_dict['query']['field'],
                request_dict['query']['type'],
                request_dict['query']['mapping_code'],
                category_lv1,
                category_lv2,
                category_lv3,
                'update user : ' + request_dict['user']['username'],
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

def delete_code_mapping(request_dict):
    Complement_Code_Mapping.objects.filter(id=request_dict['query']['id']).delete()
    return True, None, None, {'type': 'success', 'title': 'Success', 'text' : str(request_dict['query']['id']) + ' has deleted.'}