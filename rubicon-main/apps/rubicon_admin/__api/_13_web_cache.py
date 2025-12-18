import json
import asyncio
from alpha import __log
from icecream import ic
from datetime import datetime

from django.db.models import F, Q
from django.core.paginator import Paginator
from django.db import connection, transaction

from apps.rubicon_v3.models import web_clean_cache
from apps.rubicon_v3.__function.__embedding_rerank import baai_embedding

from apps.rubicon_admin.__function.perplexity import call_perplexity, post_process_content, insert_into_table

def create_reference_rag(request_dict):
    __log.debug(request_dict)

    # user_query = "인피니트와 일반 삼성제품 간에는 어떤 차이가 있어?"
    # country = "KR"
    country = request_dict['query']['country_code']
    url, content = call_perplexity(request_dict['query']['reference_query'])
    processed_content = post_process_content(content)
    content_embed = baai_embedding(processed_content, None)[0]

        # break
    insert_into_table('TRUE', url, processed_content, country, request_dict['query']['reference_query'], content_embed, request_dict['query']['update_tag'])

    return True, None, None, {'type': 'success', 'title': 'Success', 'text' : request_dict['query']['reference_query'] + ' has created.'}


def create_web_clean_cache(request_dict):
    __log.debug(request_dict)
    # try:
    with connection.cursor() as cursor:
        embedding = baai_embedding(request_dict['query']['summary'],'test')
        query = f"""INSERT INTO rubicon_v3_web_clean_cache (active, country_code, content_embed, title, summary, clean_content, source, update_tag, created_on)
                VALUES ('{request_dict['query']['active']}', '{request_dict['query']['country_code']}', '{embedding[0]}', '{request_dict['query']['title']}', '{request_dict['query']['summary']}', '{request_dict['query']['clean_content']}', '{request_dict['query']['source']}', '{request_dict['query']['update_tag']}', '{datetime.now()}')"""

        cursor.execute(query)
        transaction.commit()
    return True, None, None, {'type': 'success', 'title': 'Success', 'text' : request_dict['query']['title'] + ' has created.'}
    # except Exception as e:
    
    # update_tag = 'create user : ' + request_dict['user']['username']
    # web_clean_cache.objects.create(
    #     country_code=request_dict['query']['country_code'],
    #     query=request_dict['query']['query'],
    #     title=request_dict['query']['title'],
    #     summary=request_dict['query']['summary'],
    #     clean_content=request_dict['query']['clean_content'],
    #     source=request_dict['query']['source']
    # )

    # return True, None, None, {'type': 'success', 'title': 'Success', 'text' : request_dict['query']['word'] + ' has added.'}

def read_web_clean_cache(request_dict):
    __log.debug(request_dict)
    if 'embedding_query' in request_dict['query']:
        with connection.cursor() as cursor:
            embedding = baai_embedding(request_dict['query']['embedding_query'],'test')

            filter_string = ''
            filter_list = []
            if 'active' in request_dict['query']:
                if request_dict['query']['active'] == True:
                    filter_list.append(f' active = TRUE')
                else:
                    filter_list.append(f' active = FALSE')

            if 'country_code' in request_dict['query']:
                filter_list.append(f' country_code = \'{request_dict['query']['country_code']}\'')

            if 'source' in request_dict['query']:
                filter_list.append(f' source = \'{request_dict['query']['source']}\'')

            if 'update_tag' in request_dict['query']:
                filter_list.append(f' update_tag = \'{request_dict['query']['update_tag']}\'')

            if 'search_word_in_title' in request_dict['query']:
                filter_list.append(f' title LIKE \'{request_dict['query']['search_word_in_title']}\'')

            if 'search_word_in_content' in request_dict['query']:
                filter_list.append(f' clean_content LIKE \'{request_dict['query']['search_word_in_content']}\'')

            if filter_list != []:
                filter_string = 'WHERE ' + " AND ".join(filter_list)
            

            query = f"""
            SELECT 
                id, active, country_code, title, summary, clean_content, source, update_tag,
                content_embed <=> '{str(embedding[0])}' AS similarity
            FROM rubicon_v3_web_clean_cache {filter_string}
            ORDER BY content_embed <=> '{str(embedding[0])}'
            LIMIT 20;
            """

            cursor.execute(query)
            result = cursor.fetchall()

            page_data = []
            key_list = ['id', 'active', 'country_code', 'title', 'summary', 'clean_content', 'source', 'update_tag', 'similarity']
            for row in result:
                # ic(row)
                row_item = {}
                for index, key in enumerate(key_list):
                    # ic(index, key)
                    if key == 'similarity':
                        row_item[key] = round(1 - row[index], 2)
                    else:
                        row_item[key] = row[index]
                page_data.append(row_item)

        item_count = request_dict['paging']['itemsPerPage']
    else:
        query = web_clean_cache.objects
        if 'active' in request_dict['query']:
            query = query.filter(active=request_dict['query']['active'])
        if 'country_code' in request_dict['query']:
            query = query.filter(country_code=request_dict['query']['country_code'])
        if 'source' in request_dict['query']:
            query = query.filter(source=request_dict['query']['source'])
        if 'update_tag' in request_dict['query']:
            query = query.filter(update_tag=request_dict['query']['update_tag'])
        if 'search_word_in_title' in request_dict['query']:
            search_word = request_dict['query']['search_word_in_title']
            query = query.filter(title__contains=search_word)
        if 'search_word_in_content' in request_dict['query']:
            search_word = request_dict['query']['search_word_in_content']
            query = query.filter(clean_content__contains=search_word)
            # query = query.filter(
            #     Q(clean_content__contains=search_word) |
            #     Q(title__contains=search_word) |
            #     Q(summary__contains=search_word)
            # )

        item_count = query.count()
        __log.debug(item_count)
        if item_count == 0:
            return True, [], [{'itemCount': 0}], None
        else:
            items = list(query.order_by('-created_on').values('id', 'active', 'country_code', 'title', 'summary', 'clean_content', 'source', 'update_tag'))
            paginator = Paginator(items, per_page=request_dict['paging']['itemsPerPage'], orphans=0)

            page_data = list(paginator.page(int(request_dict['paging']['page'])))

    return True, page_data, [{'itemCount': item_count}], None

def update_web_clean_cache(request_dict):

    # __log.debug(request_dict)
    with transaction.atomic():
        with connection.cursor() as cursor:
            # Generate the embedding asynchronously
            embedding = baai_embedding(request_dict['query']['summary'],'test')


            # Prepare the UPDATE SQL query with parameter placeholders
            query = """
                UPDATE rubicon_v3_web_clean_cache
                SET
                    active = %s,
                    country_code = %s,
                    content_embed = %s,
                    title = %s,
                    summary = %s,
                    clean_content = %s,
                    source = %s,
                    update_tag = %s
                WHERE id = %s
            """
 
            # Parameters to prevent SQL injection
            params = (
                request_dict['query']['active'],
                request_dict['query']['country_code'], 
                embedding[0],
                request_dict['query']['title'],
                request_dict['query']['summary'], 
                request_dict['query']['clean_content'],
                request_dict['query']['source'],
                request_dict['query']['update_tag'],
                request_dict['query']['id'] 
            )

            # Execute the query with parameters
            cursor.execute(query, params)

    return True, None, None, {
        'type': 'success',
        'title': 'Success',
        'text': f"{request_dict['query']['title']} has been updated."
    }


    # web_clean_cache.objects.filter(id=request_dict['query']['id']).update(
    #     country_code=request_dict['query']['country_code'],
    #     query=request_dict['query']['query'],
    #     title=request_dict['query']['title'],
    #     summary=request_dict['query']['summary'],
    #     clean_content=request_dict['query']['clean_content'],
    #     source=request_dict['query']['source']
    # )

    # return True, None, None, {'type': 'success', 'title': 'Success', 'text' : 'the row has updated.'}

def delete_web_clean_cache(request_dict):
    web_clean_cache.objects.filter(id=request_dict['query']['id']).delete()
    return True, None, None, {'type': 'success', 'title': 'Success', 'text' : 'the row has deleted.'}

def list_update_tag(request_dict):
    distinct_values = web_clean_cache.objects.filter(~Q(update_tag = None)).values('update_tag').distinct()
    distinct_values_list = [item['update_tag'] for item in distinct_values]
    distinct_values_list = sorted(distinct_values_list)
    return True, distinct_values_list,  None, None

# def list_type(request_dict):
#     distinct_values = web_clean_cache.objects.filter(~Q(type = None)).values('type').distinct()
#     distinct_values_list = [item['type'] for item in distinct_values]
#     distinct_values_list = sorted(distinct_values_list)
#     return True, distinct_values_list,  None, None

# def list_processing(request_dict):
#     distinct_values = web_clean_cache.objects.filter(~Q(processing = None)).values('processing').distinct()
#     distinct_values_list = [item['processing'] for item in distinct_values]
#     distinct_values_list = sorted(distinct_values_list)
#     return True, distinct_values_list,  None, None

# def list_update_tag(request_dict):
#     distinct_values = web_clean_cache.objects.filter(~Q(update_tag = None)).values('update_tag').distinct()
#     distinct_values_list = [item['update_tag'] for item in distinct_values]
#     distinct_values_list = sorted(distinct_values_list)
#     return True, distinct_values_list,  None, None