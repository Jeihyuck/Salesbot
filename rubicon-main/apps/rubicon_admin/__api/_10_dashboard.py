from icecream import ic
from alpha import __log
import pandas as pd
# from django.db.models import F, Q
# from django.core.paginator import Paginator
# from django.contrib.postgres.search import SearchVector

# from apps.rubicon.models import Training_Intelligence_Triage, Prompt_Template
from alpha._db import chat_log_collection


def api_call_count(request_dict):
    # __log.debug(request_dict)

    pipeline = [
        {'$unwind': {'path': '$log', 'preserveNullAndEmptyArrays': True}},
        {'$match': {'log.module': 'intelligence_triage'}},
        {'$project': {
            '_id': '$_id',
            'channel': '$channel',
            'module': '$log.module',
            'function_output': '$log.function.output'
        }},
        {'$unwind': {'path': '$function_output', 'preserveNullAndEmptyArrays': True}},
        {'$project': {
            '_id': 0,
            'channel': '$channel',
            'intelligence': { '$arrayElemAt': ['$function_output.value', 1] }
        }},
        # {'$limit': 2}
    ]

    cursor = chat_log_collection.aggregate(pipeline)
    # dict_result = 

    # ic(dict_result)
    df = pd.DataFrame(list(cursor))
    # ic(df)

    api_call_count = len(df)
    # ic(api_call_count)

    channel_counts = df['channel'].value_counts().reset_index()
    channel_counts.columns = ['channel', 'count']
    channel_status = channel_counts.T.values.tolist()
    # ic(channel_status)

    intelligence_counts = df['intelligence'].value_counts().reset_index()
    intelligence_counts.columns = ['intelligence', 'count']
    # ic(intelligence_counts)
    intelligence_status = intelligence_counts.T.values.tolist()
    # ic(intelligence_status)
 
    count = {
        'channel': channel_status,
        'intelligence': intelligence_status,
    }

    return True, count, None, None
