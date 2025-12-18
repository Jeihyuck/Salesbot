import asyncio
import json
from alpha import __log
from django.db import connection, transaction

from django.db.models import F, Q
from django.core.paginator import Paginator
# from django.contrib.postgres.search import SearchVector
from apps.rubicon_admin.__function import rerank
from apps.rubicon_v3.models import Assistant_Ref_Info
from apps.rubicon_v3.__function.__embedding_rerank import baai_embedding
from datetime import datetime
from icecream import ic
# from pgvector.django import CosineDistance

# structured, unstructured,

def create_assistant_ref_info(request_dict):
    # __log.debug(request_dict)
    if 'related_question' not in request_dict['query']:
        return True, None, None, {'type': 'fail', 'title': 'Success', 'text' :'Related Question should be entered.'}
    if request_dict['query']['related_question'] == '':
        return True, None, None, {'type': 'fail', 'title': 'Success', 'text' :'Related Question should be entered.'}


    with connection.cursor() as cursor:
        embedding = baai_embedding(request_dict['query']['related_question'], '-')
        request_dict['query']['title'] = request_dict['query']['title'].replace("'", "''")
        request_dict['query']['text'] = request_dict['query']['text'].replace("'", "''")
        request_dict['query']['related_question'] = request_dict['query']['related_question'].replace("'", "''")

        query = f"""INSERT INTO rubicon_v3_assistant_ref_info 
                    (active,
                     country_code,
                     embedding,
                     title,
                     related_question,
                     text, 
                     created_on, updated_on)
                VALUES (TRUE,
                        '{request_dict['query']['country_code']}',
                        '{embedding[0]}',
                        '{request_dict['query']['title']}',
                        '{request_dict['query']['related_question']}',
                        '{request_dict['query']['text']}',
                        '{datetime.now()}', '{datetime.now()}')"""

        cursor.execute(query)
        transaction.commit()
    return True, None, None, {'type': 'success', 'title': 'Success', 'text' : request_dict['query']['title'] + ' has created.'}


def read_assistant_ref_info(request_dict):
    # __log.debug(request_dict)
    if 'embeddingSearch' in request_dict['query']:
        with connection.cursor() as cursor:
            embedding = baai_embedding(request_dict['query']['embeddingSearch'],'-')

            filter_string = ''
            filter_list = []
            if 'active' in request_dict['query']:
                if request_dict['query']['active'] == True:
                    filter_list.append(f' active = TRUE')
                else:
                    filter_list.append(f' active = FALSE')

            if 'country_code' in request_dict['query']:
                filter_list.append(f' country_code = \'{request_dict['query']['country_code']}\'')


            if filter_list != []:
                filter_string = 'WHERE ' + " AND ".join(filter_list)

            query = f"""
            SELECT 
                id,
                active,
                update_tag,
                country_code::text,
                title::text,
                related_question::text,
                text::text,
                embedding <=> '{str(embedding[0])}' AS distance
            FROM rubicon_v3_assistant_ref_info {filter_string}
            ORDER BY embedding <=> '{str(embedding[0])}'
            LIMIT 10;
            """

            cursor.execute(query)
            result = cursor.fetchall()

            page_data = []
            key_list = ['id', 'active', 'update_tag', 'country_code', 'title', 'related_question', 'text', 'distance']
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
            page_data = rerank.calculate_rerank_score(request_dict['query']['embeddingSearch'], page_data, 'related_question')
            page_data = sorted(page_data, key=lambda x: x["rerank_score"], reverse=True)

            # __log.debug(page_data)
            # filtered_page_data = []
            # for item in page_data:
            #     if item['rerank_score'] > 2:
            #         filtered_page_data.append(item['title'] + ':' + item['text'])
            # __log.debug(filtered_page_data)

        item_count = request_dict['paging']['itemsPerPage']
    
    else:
        qeury = Assistant_Ref_Info.objects
        if 'active' in request_dict['query']:
            qeury = qeury.filter(active=request_dict['query']['active'])
        if 'update_tag' in request_dict['query']:
            qeury = qeury.filter(update_tag=request_dict['query']['update_tag'])
        if 'country_code' in request_dict['query']:
            qeury = qeury.filter(country_code=request_dict['query']['country_code'])

        item_count = qeury.count()
        items = list(qeury.order_by('-id').values('id', 'active', 'country_code', 'update_tag', 'title', 'related_question', 'text', 'created_on', 'updated_on'))
        paginator = Paginator(items, per_page=request_dict['paging']['itemsPerPage'], orphans=0)

        page_data = list(paginator.page(int(request_dict['paging']['page'])))

    return True, page_data, [{'itemCount': item_count}], None


def list_update_tag(request_dict):
    distinct_values = Assistant_Ref_Info.objects.filter(~Q(update_tag = None)).values('update_tag').distinct()
    distinct_values_list = [item['update_tag'] for item in distinct_values]
    distinct_values_list = sorted(distinct_values_list)
    return True, distinct_values_list,  None, None


def update_assistant_ref_info(request_dict):
    # __log.debug(request_dict)
    with transaction.atomic():
        with connection.cursor() as cursor:
            # Generate the embedding asynchronously
            embedding = baai_embedding(request_dict['query']['title'] + ':' + request_dict['query']['text'],'-')

            # Prepare the UPDATE SQL query with parameter placeholders
            query = """
                UPDATE rubicon_v3_assistant_ref_info
                SET
                    active = TRUE,
                    country_code = %s,
                    embedding = %s,
                    title = %s,
                    related_question = %s,
                    text = %s,
                    update_tag = %s,
                    updated_on = %s
                WHERE id = %s
            """
 
            # Parameters to prevent SQL injection
            params = (
                request_dict['query']['country_code'],
                embedding[0],
                request_dict['query']['title'],
                request_dict['query']['related_question'],
                request_dict['query']['text'],
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

def delete_assistant_ref_info(request_dict):
    Assistant_Ref_Info.objects.filter(id=request_dict['query']['id']).delete()
    return True, None, None, {'type': 'success', 'title': 'Success', 'text' : str(request_dict['query']['id']) + ' has deleted.'}