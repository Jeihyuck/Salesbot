import asyncio
import json
from alpha import __log
from django.db import connection, transaction

from django.db.models import F, Q
from django.core.paginator import Paginator
# from django.contrib.postgres.search import SearchVector
from apps.rubicon_admin.__function import rerank
from apps.rubicon_v3.models import Structured_Code_Mapping
from apps.rubicon_v3.__function.__embedding_rerank import baai_embedding
from datetime import datetime
from icecream import ic
# from pgvector.django import CosineDistance

# structured, unstructured,

def create_code_mapping(request_dict):
    __log.debug(request_dict)
    # try:
    with connection.cursor() as cursor:
        embedding = baai_embedding(request_dict['query']['expression'],'test')
        query = f"""INSERT INTO rubicon_v3_structured_code_mapping (expression_embedding, active,  expression, country_code, field, mapping_code, created_on, updated_on, site_cd, expression_to_code, structured)
                VALUES ('{embedding[0]}', TRUE, '{request_dict['query']['expression']}', '{request_dict['query']['country_code']}', '{request_dict['query']['field']}', '{request_dict['query']['mapping_code']}', '{datetime.now()}', '{datetime.now()}', 'B2C', '{request_dict['query']['expression_to_code']}', TRUE)"""

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

            filter_string = ''
            filter_list = []
            if 'active' in request_dict['query']:
                if request_dict['query']['active'] == True:
                    filter_list.append(f' active = TRUE')
                else:
                    filter_list.append(f' active = FALSE')

            if 'structured' in request_dict['query']:
                if request_dict['query']['structured'] == True:
                    filter_list.append(f' structured = TRUE')
                else:
                    filter_list.append(f' structured = FALSE')

            if 'expression_to_code' in request_dict['query']:
                if request_dict['query']['expression_to_code'] == True:
                    filter_list.append(f' expression_to_code = TRUE')
                else:
                    filter_list.append(f' expression_to_code = FALSE')

            if 'country_code' in request_dict['query']:
                filter_list.append(f' country_code = \'{request_dict['query']['country_code']}\'')

            if 'field' in request_dict['query']:
                filter_list.append(f' field = \'{request_dict['query']['field']}\'')

            if filter_list != []:
                filter_string = 'WHERE ' + " AND ".join(filter_list)

            query = f"""
            SELECT 
                id,
                active,
                expression,
                country_code::text,
                field::text,
                mapping_code::text,
                structured,
                expression_to_code,
                expression_embedding <=> '{str(embedding[0])}' AS distance
            FROM rubicon_v3_structured_code_mapping {filter_string}
            ORDER BY expression_embedding <=> '{str(embedding[0])}'
            LIMIT 20;
            """

            cursor.execute(query)
            result = cursor.fetchall()

            page_data = []
            key_list = ['id', 'active', 'expression', 'country_code', 'field', 'mapping_code', 'structured', 'expression_to_code', 'distance']
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

            page_data = rerank.calculate_rerank_score(request_dict['query']['embeddingSearch'], page_data, 'expression')

        item_count = request_dict['paging']['itemsPerPage']
    
    else:
        qeury = Structured_Code_Mapping.objects
        if 'active' in request_dict['query']:
            qeury = qeury.filter(active=request_dict['query']['active'])
        if 'structured' in request_dict['query']:
            qeury = qeury.filter(structured=request_dict['query']['structured'])
        if 'expression_to_code' in request_dict['query']:
            qeury = qeury.filter(expression_to_code=request_dict['query']['expression_to_code'])
        if 'field' in request_dict['query']:
            qeury = qeury.filter(field=request_dict['query']['field'])
        if 'expression' in request_dict['query']:
            qeury = qeury.filter(expression=request_dict['query']['expression'])
        if 'country_code' in request_dict['query']:
            qeury = qeury.filter(country_code=request_dict['query']['country_code'])

        item_count = qeury.count()
        items = list(qeury.order_by('-id').values('id', 'active', 'expression', 'country_code', 'field', 'mapping_code', 'structured', 'expression_to_code', 'created_on', 'updated_on'))
        paginator = Paginator(items, per_page=request_dict['paging']['itemsPerPage'], orphans=0)

        page_data = list(paginator.page(int(request_dict['paging']['page'])))

    return True, page_data, [{'itemCount': item_count}], None

def list_distint_field_list(request_dict):
    distinct_values = Structured_Code_Mapping.objects.values('field').distinct()
    distinct_values_list = [item['field'] for item in distinct_values]
    distinct_values_list = sorted(distinct_values_list)
    return True, distinct_values_list,  None, None


def update_code_mapping(request_dict):
    __log.debug(request_dict)
    with transaction.atomic():
        with connection.cursor() as cursor:
            # Generate the embedding asynchronously
            embedding = baai_embedding(request_dict['query']['expression'],'test')
            
            # Prepare the UPDATE SQL query with parameter placeholders
            query = """
                UPDATE rubicon_v3_structured_code_mapping
                SET
                    active = TRUE,
                    expression_embedding = %s,
                    expression = %s,
                    country_code = %s,
                    field = %s,
                    mapping_code = %s,
                    structured = %s,
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
                request_dict['query']['structured'],
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
    Structured_Code_Mapping.objects.filter(id=request_dict['query']['id']).delete()
    return True, None, None, {'type': 'success', 'title': 'Success', 'text' : str(request_dict['query']['id']) + ' has deleted.'}