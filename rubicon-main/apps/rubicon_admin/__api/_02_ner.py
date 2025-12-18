import json
from alpha import __log
from django.db import connection, transaction
from django.db.models import Q
from django.core.paginator import Paginator

from apps.rubicon_v3.models import NER_Ref
from apps.rubicon_v3.__function.__embedding_rerank import baai_embedding
from datetime import datetime

def create_ner(request_dict):
    __log.debug(request_dict)
    with connection.cursor() as cursor:
        update_tag = 'create user : ' + request_dict['user']['username']
        embedding = baai_embedding(request_dict['query']['query'],'test')
        measure_dimension = json.dumps(json.loads(request_dict['query']['measure_dimension']))
        query = f"""INSERT INTO rubicon_v3_ner_ref (active, update_tag, country_code, site_cd, embedding, query, measure_dimension, created_on, updated_on, confirmed)
                VALUES (TRUE, '{update_tag}', '{request_dict['query']['country_code']}', '{request_dict['query']['site_cd']}', '{embedding[0]}', '{request_dict['query']['query']}', '{measure_dimension}', '{datetime.now()}', '{datetime.now()}', {False})"""

        cursor.execute(query)
        transaction.commit()
    return True, None, None, {'type': 'success', 'title': 'Success', 'text' : request_dict['query']['query'] + ' has created.'}

def read_ner(request_dict):
    __log.debug(request_dict)
    if 'embeddingSearch' in request_dict['query']:
        filter_string = ''
        filter_list = []
        if 'active' in request_dict['query']:
            if request_dict['query']['active'] == True:
                filter_list.append(f' active = TRUE')
            else:
                filter_list.append(f' active = FALSE')
        if 'update_tag' in request_dict['query']:
            filter_list.append(f' update_tag = \'{request_dict['query']['update_tag']}\'')
        if 'site_cd' in request_dict['query']:
            filter_list.append(f' site_cd = \'{request_dict['query']['site_cd']}\'')
        if 'country_code' in request_dict['query']:
            filter_list.append(f' country_code = \'{request_dict['query']['country_code']}\'')

        if filter_list != []:
            filter_string = 'WHERE ' + " AND ".join(filter_list)

        with connection.cursor() as cursor:
            embedding = baai_embedding(request_dict['query']['embeddingSearch'],'test')

            query = f"""
            SELECT 
                id,
                query,
                active,
                update_tag,
                country_code::text,
                site_cd::text,
                measure_dimension::text,
                embedding <=> '{str(embedding[0])}' AS distance
            FROM rubicon_v3_ner_ref {filter_string}
            ORDER BY embedding <=> '{str(embedding[0])}'
            LIMIT {request_dict['paging']['itemsPerPage']};
            """

            cursor.execute(query)
            result = cursor.fetchall()

            page_data = []
            key_list = ['id', 'query', 'active', 'update_tag', 'country_code', 'site_cd', 'measure_dimension', 'distance']
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

        item_count = request_dict['paging']['itemsPerPage']
    
    else:
        qeury = NER_Ref.objects
        if 'active' in request_dict['query']:
            qeury = qeury.filter(active=request_dict['query']['active'])
        if 'update_tag' in request_dict['query']:
            qeury = qeury.filter(update_tag=request_dict['query']['update_tag'])
        if 'country_code' in request_dict['query']:
            qeury = qeury.filter(country_code=request_dict['query']['country_code'])
        if 'site_cd' in request_dict['query']:
            qeury = qeury.filter(site_cd=request_dict['query']['site_cd'])

        item_count = qeury.count()

        items = list(qeury.order_by('-id').values('id', 'active', 'update_tag', 'query', 'country_code', 'site_cd', 'measure_dimension'))
        paginator = Paginator(items, per_page=request_dict['paging']['itemsPerPage'], orphans=0)

        page_data = list(paginator.page(int(request_dict['paging']['page'])))

    return True, page_data, [{'itemCount': item_count}], None


def update_ner(request_dict):
    __log.debug(request_dict)
    with connection.cursor() as cursor:
        # Generate the embedding asynchronously
        embedding = baai_embedding(request_dict['query']['query'],'test')

        # Parse the measure_dimension from the request
        measure_dimension = json.dumps(json.loads(request_dict['query']['measure_dimension']))
        update_tag = 'update user : ' + request_dict['user']['username']
        # Prepare the UPDATE SQL query with parameter placeholders
        query = """
            UPDATE rubicon_v3_ner_ref
            SET
                embedding = %s,
                active = %s,
                country_code = %s,
                site_cd = %s,
                query = %s,                
                measure_dimension = %s,
                updated_on = %s,
                update_tag = %s
            WHERE id = %s
        """

        # Parameters to prevent SQL injection
        params = (
            embedding[0],
            request_dict['query']['active'],
            request_dict['query']['country_code'],
            request_dict['query']['site_cd'],
            request_dict['query']['query'],
            measure_dimension,
            datetime.now(),
            update_tag,
            request_dict['query']['id']
        )

        # Execute the query with parameters
        cursor.execute(query, params)
        transaction.commit()

    return True, None, None, {
        'type': 'success',
        'title': 'Success',
        'text': f"{request_dict['query']['query']} has been updated."
    }

def delete_ner(request_dict):
    NER_Ref.objects.filter(id=request_dict['query']['id']).delete()
    return True, None, None, {'type': 'success', 'title': 'Success', 'text' : request_dict['query']['query'] + ' has deleted.'}

def list_update_tag(request_dict):
    distinct_values = NER_Ref.objects.filter(~Q(update_tag = None)).values('update_tag').distinct()
    distinct_values_list = [item['update_tag'] for item in distinct_values]
    distinct_values_list = sorted(distinct_values_list)
    return True, distinct_values_list,  None, None

def list_site_cd(request_dict):
    distinct_values = NER_Ref.objects.filter(~Q(site_cd = None)).values('site_cd').distinct()
    distinct_values_list = [item['site_cd'] for item in distinct_values]
    distinct_values_list = sorted(distinct_values_list)
    return True, distinct_values_list,  None, None