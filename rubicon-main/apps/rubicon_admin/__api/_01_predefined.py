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

from apps.rubicon_v3.models import Predefined_Answer
from apps.rubicon_v3.__function.__embedding_rerank import baai_embedding


def create_predefined(request_dict):
    # __log.debug(request_dict)
    with connection.cursor() as cursor:
        embedding = baai_embedding(request_dict["query"]["query"], "test")
        query = f"""INSERT INTO rubicon_v3_predefined_answer (
                        {Predefined_Answer.embedding.field.name},
                        {Predefined_Answer.channel.field.name},
                        {Predefined_Answer.country_code.field.name},
                        {Predefined_Answer.category.field.name},
                        {Predefined_Answer.query.field.name},
                        {Predefined_Answer.predefined_answer.field.name},
                        {Predefined_Answer.created_on.field.name},
                        {Predefined_Answer.updated_on.field.name})
                    VALUES  (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"""
        params = (
            embedding[0],
            request_dict["query"]["channel"],
            request_dict["query"]["country_code"],
            request_dict["query"]["category"],
            request_dict["query"]["query"],
            request_dict["query"]["predefined_answer"],
            str(datetime.now()),
            str(datetime.now()),
        )
        cursor.execute(query, params)
        transaction.commit()
    return (
        True,
        None,
        None,
        {
            "type": "success",
            "title": "Success",
            "text": request_dict["query"]["query"] + " has created.",
        },
    )


def read_predefined(request_dict):
    # __log.debug(request_dict)
    if "embeddingSearch" in request_dict["query"]:
        with connection.cursor() as cursor:

            query_list = []

            if "country_code" in request_dict["query"]:
                query_list.append(
                    f"country_code = '{request_dict['query']['country_code']}'"
                )
            if "channel" in request_dict["query"]:
                query_list.append(f"channel = '{request_dict['query']['channel']}'")

            if "category" in request_dict["query"]:
                query_list.append(f"category = '{request_dict['query']['category']}'")
            if "predefined_type" in request_dict["query"]:
                query_list.append(
                    f"predefined_type = '{request_dict['query']['predefined_type']}'"
                )

            embedding = baai_embedding(request_dict["query"]["embeddingSearch"], "test")

            # ic(embedding)
            if len(query_list) > 0:
                # TODO: Change table name to grab from Predefined_Answer model
                query = f"""
                SELECT 
                    {Predefined_Answer.id.field.name},
                    {Predefined_Answer.country_code.field.name},
                    {Predefined_Answer.category.field.name},
                    {Predefined_Answer.query.field.name},
                    {Predefined_Answer.predefined_answer.field.name},
                    {Predefined_Answer.embedding.field.name} <=> '{str(embedding[0])}' AS distance,
                    {Predefined_Answer.channel.field.name}
                FROM rubicon_v3_predefined_answer
                WHERE {' AND '.join(query_list)}
                ORDER BY 6
                LIMIT 20;
                """
            else:
                # TODO: Change table name to grab from Predefined_Answer model
                query = f"""
                SELECT 
                    {Predefined_Answer.id.field.name},
                    {Predefined_Answer.country_code.field.name},
                    {Predefined_Answer.category.field.name},
                    {Predefined_Answer.query.field.name},
                    {Predefined_Answer.predefined_answer.field.name},
                    {Predefined_Answer.embedding.field.name} <=> '{str(embedding[0])}' AS distance,
                    {Predefined_Answer.channel.field.name}
                FROM rubicon_v3_predefined_answer
                ORDER BY 6
                LIMIT 20;
                """

            cursor.execute(query)
            result = cursor.fetchall()

            page_data = []
            key_list = [
                Predefined_Answer.id.field.name,
                Predefined_Answer.country_code.field.name,
                Predefined_Answer.category.field.name,
                Predefined_Answer.query.field.name,
                Predefined_Answer.predefined_answer.field.name,
                "distance",  # distance 값을 similarity로 변경
                Predefined_Answer.channel.field.name,
            ]
            for row in result:
                row_item = {}
                for index, key in enumerate(key_list):
                    if key == "distance":
                        row_item[key] = round(1 - row[index], 2)
                    else:
                        row_item[key] = row[index]
                page_data.append(row_item)
            page_data = rerank.calculate_rerank_score(
                request_dict["query"]["embeddingSearch"], page_data, "query"
            )
        item_count = request_dict["paging"]["itemsPerPage"]

    else:
        query = Predefined_Answer.objects
        if "country_code" in request_dict["query"]:
            query = query.filter(country_code=request_dict["query"]["country_code"])
        if "category" in request_dict["query"]:
            query = query.filter(category=request_dict["query"]["category"])
        if "predefined_type" in request_dict["query"]:
            query = query.filter(
                predefined_type=request_dict["query"]["predefined_type"]
            )
        if "channel" in request_dict["query"]:
            query = query.filter(channel=request_dict["query"]["channel"])

        item_count = query.count()
        items = list(
            query.order_by(f"-{Predefined_Answer.id.field.name}").values(
                Predefined_Answer.id.field.name,
                Predefined_Answer.country_code.field.name,
                Predefined_Answer.category.field.name,
                Predefined_Answer.query.field.name,
                Predefined_Answer.predefined_answer.field.name,
                Predefined_Answer.channel.field.name,
            )
        )
        paginator = Paginator(
            items, per_page=request_dict["paging"]["itemsPerPage"], orphans=0
        )

        page_data = list(paginator.page(int(request_dict["paging"]["page"])))

    return True, page_data, [{"itemCount": item_count}], None


def update_predefined(request_dict):
    # __log.debug(request_dict)
    with connection.cursor() as cursor:
        # Generate the embedding asynchronously
        embedding = baai_embedding(request_dict["query"]["query"], "test")
        update_tag = "update user : " + request_dict["user"]["username"]
        query = """
            UPDATE rubicon_v3_predefined_answer
            SET
                embedding = %s,
                country_code = %s,
                category = %s,        
                query = %s,
                predefined_answer = %s,
                updated_on = %s,
                channel = %s
            WHERE id = %s
        """
        # Parameters to prevent SQL injection
        params = (
            embedding[0],
            request_dict["query"]["country_code"],
            request_dict["query"]["category"],
            request_dict["query"]["query"],
            request_dict["query"]["predefined_answer"],
            datetime.now(),
            request_dict["query"]["channel"],
            request_dict["query"]["id"],
        )

        # Execute the query with parameters
        cursor.execute(query, params)
        transaction.commit()

    return (
        True,
        None,
        None,
        {
            "type": "success",
            "title": "Success",
            "text": f"{request_dict['query']['query']} has been updated.",
        },
    )


def delete_predefined(request_dict):
    Predefined_Answer.objects.filter(id=request_dict["query"]["id"]).delete()
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
