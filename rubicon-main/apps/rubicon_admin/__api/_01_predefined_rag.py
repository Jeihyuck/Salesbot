import json
import asyncio
from icecream import ic
from alpha import __log

from datetime import datetime

# from django.db.models import F, Q
from django.core.paginator import Paginator
from django.db import connection, transaction

import django

django.setup()

from apps.rubicon_admin.__function import rerank

from apps.rubicon_v3.models import Predefined_RAG
from apps.rubicon_v3.__function.__embedding_rerank import baai_embedding


def create_predefined_rag(request_dict):
    Predefined_RAG.objects.create(
        active=request_dict['query']['active'],
        country_code=request_dict['query']['country_code'],
        site_cd=request_dict['query']['site_cd'],
        channel_filter=json.loads(request_dict['query']['channel_filter']),
        matching_rule=json.loads(request_dict['query']['matching_rule']),
        description=request_dict['query']['description'],
        contents=request_dict['query']['contents']
    )
    return (
        True,
        None,
        None,
        {
            "type": "success",
            "title": "Success",
            "text": request_dict["query"]["description"] + " has created.",
        },
    )


def read_predefined_rag(request_dict):
    query = Predefined_RAG.objects
    if "country_code" in request_dict["query"]:
        query = query.filter(country_code=request_dict["query"]["country_code"])
    # if "channel" in request_dict["query"]:
    #     query = query.filter(channel=request_dict["query"]["channel"])

    item_count = query.count()
    items = list(query.values('id', 'active', 'country_code', 'site_cd', 'channel_filter', 'matching_rule', 'contents', 'description'))
    paginator = Paginator(items, per_page=request_dict['paging']['itemsPerPage'], orphans=0)

    page_data = list(paginator.page(int(request_dict['paging']['page'])))

    return True, page_data, [{'itemCount': item_count}], None

def update_predefined_rag(request_dict):
    # __log.debug(request_dict)
    Predefined_RAG.objects.filter(id=request_dict['query']['id']).update(
        active=request_dict['query']['active'],
        country_code=request_dict['query']['country_code'],
        site_cd=request_dict['query']['site_cd'],
        channel_filter=json.loads(request_dict['query']['channel_filter']),
        matching_rule=json.loads(request_dict['query']['matching_rule']),
        description=request_dict['query']['description'],
        contents=request_dict['query']['contents']
    )
    return (
        True,
        None,
        None,
        {
            "type": "success",
            "title": "Success",
            "text": f"{request_dict['query']['description']} has been updated.",
        },
    )


def delete_predefined(request_dict):
    Predefined_RAG.objects.filter(id=request_dict["query"]["id"]).delete()
    return (
        True,
        None,
        None,
        {
            "type": "success",
            "title": "Success",
            "text": str(request_dict["query"]["id"]) + " has deleted.",
        },
    )
