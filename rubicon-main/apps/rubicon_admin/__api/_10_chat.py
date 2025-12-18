import pandas as pd
from icecream import ic
from alpha import __log
from alpha._db import chat_log_collection


def get_chat_history(request_dict):
    # __log.debug(request_dict)
    pipeline = [
        {
            "$match": {
                "user_id": request_dict["query"]["userId"],
                "message_status.completed": True,
                "message_status.is_hidden": {"$ne": True},
            }
        },
        {
            "$project": {
                "_id": "$_id",
                "message_id": "$message_id",
                "message": "$message",
                "final_module": {"$arrayElemAt": ["$log", -1]},
                "created_on": "$created_on",
            }
        },
        {
            "$project": {
                "_id": 0,
                "message_id": "$message_id",
                "message": "$message",
                "output": "$final_module.function.output",
                "created_on": "$created_on",
            }
        },
        {"$sort": {"created_on": -1}},
        {"$limit": 20},
    ]
    cursor = chat_log_collection.aggregate(pipeline)
    msg_history = list(cursor)

    response_data = []
    for msg in msg_history:
        try:
            output = msg["output"][0]["value"]
        except KeyError:
            __log.error(f"KeyError for message_id {msg}")
            output = "Response had an error"

        response_data.append(
            {"id": msg["message_id"], "message": msg["message"], "output": output}
        )

    return True, response_data, None, None
