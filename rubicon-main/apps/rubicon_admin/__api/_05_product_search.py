import asyncio
import json
from alpha import __log
from django.db import connection, transaction

from django.db.models import F, Q
from django.core.paginator import Paginator
# from django.contrib.postgres.search import SearchVector
from apps.rubicon_admin.__function import rerank
from apps.rubicon_data.models import product_card, uk_product_card
from apps.rubicon_v3.__function.__embedding_rerank import baai_embedding
from datetime import datetime
from icecream import ic
# from pgvector.django import CosineDistance


def read_product_search(request_dict):
    __log.debug(request_dict)

    if request_dict['query']['country_code'] == 'KR':
        query = product_card.objects
        if 'search_words' in request_dict['query']:
            search_words = request_dict['query']['search_words']
            search_words_list = search_words.split(' ')
            if search_words_list:
                for word in search_words_list:
                    query = query.filter(
                        Q(goods_nm__icontains=word) |
                        Q(mdl_code__icontains=word)
                    )
        if 'excluding_search_words' in request_dict['query']:
            excluding_search_words = request_dict['query']['excluding_search_words']
            excluding_search_words_list = excluding_search_words.split(' ')
            if excluding_search_words_list:
                for word in excluding_search_words_list:
                    query = query.exclude(
                        Q(goods_nm__icontains=word) |
                        Q(mdl_code__icontains=word)
                    )
        query = query.values('id', 'goods_nm', 'mdl_code').order_by('mdl_code', '-id').distinct("mdl_code")
        item_count = query.count()
        # __log.debug(item_count)
        items = list(query)

    elif request_dict['query']['country_code'] == 'GB':
        query = uk_product_card.objects
        if 'search_words' in request_dict['query']:
            search_words = request_dict['query']['search_words']
            search_words_list = search_words.split(' ')
            if search_words_list:
                for word in search_words_list:
                    query = query.filter(
                        Q(display_name__icontains=word) |
                        Q(model_code__icontains=word)
                    )
        if 'excluding_search_words' in request_dict['query']:
            excluding_search_words = request_dict['query']['excluding_search_words']
            excluding_search_words_list = excluding_search_words.split(' ')
            if excluding_search_words_list:
                for word in excluding_search_words_list:
                    query = query.exclude(
                        Q(display_name__icontains=word) |
                        Q(model_code__icontains=word)
                    )

        query = query.values('id', 'display_name', 'model_code').order_by('model_code', '-id').distinct('model_code')
        item_count = query.count()
        # __log.debug(item_count)
        items = list(query)


    paginator = Paginator(items, per_page=request_dict['paging']['itemsPerPage'], orphans=0)

    page_data = list(paginator.page(int(request_dict['paging']['page'])))

    for item in page_data:
        if request_dict['query']['country_code'] == 'KR':
            item['product_name'] = item.pop('goods_nm')
            item['product_code'] = item.pop('mdl_code')
        elif request_dict['query']['country_code'] == 'GB':
            item['product_name'] = item.pop('display_name')
            item['product_code'] = item.pop('model_code')

    return True, page_data, [{'itemCount': item_count}], None