import pandas as pd
from icecream import ic
from alpha import __log
from alpha._db import chat_log_collection
from datetime import datetime
from apps.__common.utils import convert_unparsables_to_string
from dateutil import tz, parser
from pytz import timezone

seoul_tz = timezone("Asia/Seoul")


def read(request_dict):
    # __log.debug(request_dict)

    if "date" in request_dict["query"]:
        if len(request_dict["query"]["date"]) == 1:
            start_date = parser.parse(request_dict["query"]["date"][0]).astimezone(
                seoul_tz
            )
            end_date = parser.parse(request_dict["query"]["date"][0]).astimezone(
                seoul_tz
            ) + pd.DateOffset(days=1)
        if len(request_dict["query"]["date"]) == 2:
            start_date = parser.parse(request_dict["query"]["date"][0]).astimezone(
                seoul_tz
            )
            end_date = parser.parse(request_dict["query"]["date"][1]).astimezone(
                seoul_tz
            )
        start_date = start_date.strftime("%Y-%m-%d %H:%M:%S")
        end_date = end_date.strftime("%Y-%m-%d %H:%M:%S")
        start_date = datetime.strptime(start_date, "%Y-%m-%d %H:%M:%S")
        end_date = datetime.strptime(end_date, "%Y-%m-%d %H:%M:%S")

    pipeline = [
        {
            "$match": {
                "message_status.completed": True,
                "message_status.is_hidden": {"$ne": True},
                "message_status.multi_input": {"$ne": True},
            }
        },
        {
            "$project": {
                "_id": "$_id",
                "message_id": "$message_id",
                "channel": "$channel",
                "user_id": "$user_id",
                "department": "$department",
                "message": "$message",
                # "intelligence_triage": {
                #     "$filter": {
                #         "input": "$log",
                #         "as": "log",
                #         "cond": { "$eq": ["$$log.module", "intelligence_triage"] }
                #     }
                # },
                "re_write": {
                    "$filter": {
                        "input": "$log",
                        "as": "log",
                        "cond": {
                            "$ne": [
                                {
                                    "$ifNull": [
                                        "$$log.llm.output.re_write_query_list",
                                        None,
                                    ]
                                },
                                None,
                            ]
                        },
                    }
                },
                "final_module": {"$arrayElemAt": ["$log", -1]},
                "status": "$appraisal.status",
                "thumb_up": "$appraisal.thumb_up",
                "selection": "$appraisal.selection",
                "comment": "$appraisal.comment",
            }
        },
        # {'$match': {'final_module.module': 'open_ai_call_stream'}},
        {
            "$project": {
                "_id": 0,
                "message_id": "$message_id",
                "channel": "$channel",
                "user_id": "$user_id",
                "department": "$department",
                "message": "$message",
                # 'intelligence_triage': '$intelligence_triage.function.output',
                "re_write": "$re_write.llm.output.re_write_query_list",
                "final_module": "$final_module.module",
                "output": "$final_module.function.output",
                "created_on": "$final_module.created_on",
                "status": "$status",
                "thumb_up": "$thumb_up",
                "selection": "$selection",
                "comment": "$comment",
            }
        },
    ]
    if "channel" in request_dict["query"] and request_dict["query"]["channel"] != "ALL":
        pipeline = pipeline + [
            {"$match": {"channel": request_dict["query"]["channel"]}}
        ]
    if (
        "department" in request_dict["query"]
        and request_dict["query"]["department"] != "ALL"
    ):
        pipeline = pipeline + [
            {"$match": {"department": request_dict["query"]["department"]}}
        ]
    if (
        "thumb_up" in request_dict["query"]
        and request_dict["query"]["thumb_up"]["value"] != "ALL"
    ):
        pipeline = pipeline + [
            {"$match": {"thumb_up": request_dict["query"]["thumb_up"]["value"]}}
        ]

    if "date" in request_dict["query"]:
        pipeline = pipeline + [
            {"$match": {"created_on": {"$gte": start_date, "$lt": end_date}}}
        ]

    if "status" in request_dict["query"] and request_dict["query"]["status"] != "ALL":
        pipeline = pipeline + [{"$match": {"status": request_dict["query"]["status"]}}]

    pipeline = pipeline + [
        {"$sort": {"created_on": -1}},
        {
            "$facet": {
                "meta": [{"$group": {"_id": "null", "itemCount": {"$sum": 1}}}],
                "data": [
                    {"$skip": request_dict["paging"]["skip"]},
                    {"$limit": request_dict["paging"]["itemsPerPage"]},
                ],
            }
        },
    ]

    cursor = chat_log_collection.aggregate(pipeline)
    appraisal_list = list(cursor)
    # for appraisal in appraisal_list:
    #     ic(appraisal)
    # ic(appraisal_list[0]['data'])
    if appraisal_list[0]["data"] == []:
        return True, [], [{"itemCount": 0}], None

    response_data = []

    for appraisal in appraisal_list[0]["data"]:
        # ic(appraisal)
        data = {
            "id": appraisal["message_id"],
            "channel": appraisal["channel"],
            # 'user_id': appraisal['user_id'],
            "query": appraisal["message"],
        }

        if "re_write" in appraisal:
            data["re_write"] = appraisal["re_write"]

        if "output" in appraisal:
            # if appraisal['final_module'] == 'open_ai_call_stream':
            try:
                data["response"] = appraisal["output"][0]["value"]
            except:
                data["response"] = "Error, Haven't responsed properly"
            # else:
            #     data['response'] = 'Error, Haven\'t responsed properly'

        if "intelligence_triage" in appraisal:
            try:
                data["type"] = appraisal["intelligence_triage"][0][0]["value"][0]
                data["intelligence"] = appraisal["intelligence_triage"][0][0]["value"][
                    1
                ]
            except KeyError:
                __log.error(f"KeyError for appraisal {appraisal['message_id']}")
                pass
        if "user_id" in appraisal:
            data["user_id"] = appraisal["user_id"]
        if "department" in appraisal:
            data["department"] = appraisal["department"]
        if "status" in appraisal:
            data["status"] = appraisal["status"]
        if "thumb_up" in appraisal:
            data["thumb_up"] = appraisal["thumb_up"]
        if "comment" in appraisal:
            data["comment"] = appraisal["comment"]
        if "created_on" in appraisal:
            data["created_on"] = appraisal["created_on"]
        if "selection" in appraisal:
            for selected in appraisal["selection"]:
                if selected == 0:
                    data["item_0"] = True
                elif selected == 1:
                    data["item_1"] = True
                elif selected == 2:
                    data["item_2"] = True
                elif selected == 3:
                    data["item_3"] = True
                elif selected == 4:
                    data["item_4"] = True
                elif selected == 5:
                    data["item_5"] = True
        response_data.append(data)
        convert_unparsables_to_string(response_data)

    return (
        True,
        response_data,
        [{"itemCount": appraisal_list[0]["meta"][0]["itemCount"]}],
        None,
    )


def check_log(request_dict):
    # __log.debug(request_dict)
    document = chat_log_collection.find_one(
        {"message_id": request_dict["query"]["message_id"]}
    )
    # __log.debug(document)
    convert_unparsables_to_string(document)
    # __log.debug(document)
    document.pop("_id")
    # ic(document)
    return True, document, None, None


def resolve(request_dict):
    # __log.debug(request_dict)
    chat_log_collection.update_one(
        {"message_id": request_dict["query"]["id"]},
        {"$set": {"appraisal.status": "Resolved"}},
    )
    if "resolveComment" in request_dict["query"]:
        chat_log_collection.update_one(
            {"message_id": request_dict["query"]["id"]},
            {
                "$set": {
                    "appraisal.resolveComment": request_dict["query"]["resolveComment"]
                }
            },
        )
    return True, None, None, None
