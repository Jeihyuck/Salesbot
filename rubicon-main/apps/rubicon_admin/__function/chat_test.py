from concurrent.futures import ThreadPoolExecutor

from apps.rubicon_admin.models import Chat_Test
from apps.rubicon_v3.__function._00_rubicon import RubiconChatFlow, create_dataclass_from_dict
from apps.rubicon_v3.__function.__exceptions import HttpStatus

import re
import uuid
import redis
import asyncio
from icecream import ic
from django_rq import job
from datetime import datetime
from bson.objectid import ObjectId
from alpha.settings import REDIS_ORCHESTRATOR_IP, REDIS_PASSWORD, REDIS_PORT
from apps.rubicon_v3.__function.__redis import store_dict_with_expiry


@job('default', timeout=3600)
def chat_test_module(request_dict):
    def process_items_multithreading(items):
        with ThreadPoolExecutor(max_workers=3) as executor:
            results = list(executor.map(run_async_in_thread, [item for item in items]))
        return results

    async def consume_generator(item):
        session_expiry = 900
        data_expiry = 120
        input_arguments = create_dataclass_from_dict(
            {
                "channel": "CHAT_TEST",
                "country_code": item['country'],
                "model": "rubicon",
                "meta": {"country_code": item['country']},
                "user_id": "chat_test_user",
                "session_id": item['session_id'],
                "message_id": item['message_id'],
                "message_history": [],
                "message": [
                    {
                        "type": "text",
                        "content": item['query'],
                        "role": "user",
                        "message_id": item['message_id'],
                        "created_on": datetime.now().isoformat(),
                    }
                ],
                "lng": "ko" if item['country'] == 'KR' else "en",
                "gu_id": "default_gu_id",
                "sa_id": "default_sa_id",
                "jwt_token": "default_jwt_token",
                "estore_sitecode": "default_estore_sitecode",
                "department": "-",
            },
            RubiconChatFlow.InputArguments,
        )
        input_files = create_dataclass_from_dict(
            {"files": []}, RubiconChatFlow.InputFiles
        )

        chat_flow = RubiconChatFlow(
            input_arguments=input_arguments,
            input_files=input_files,
            object_id=ObjectId(),
            use_cache=False,
            stream=True,
            simple=False,
            status=HttpStatus(),
        )

        # Run the chat flow
        chat_flow.enqueue_chat_flow()

        response_generator = chat_flow.get_stream_response()

        response = ''
        async for token in response_generator:
            token = token.replace('data: ', '').rstrip('\n')
            ic(token)
            response = response + re.sub(r'<br\s*/?>', '\n', token, flags=re.IGNORECASE)
        Chat_Test.objects.filter(id=item['id']).update(response=response, tested=True)

    async def ruasync_wait(item):
        await asyncio.wait_for(consume_generator(item), timeout=60)
    
    def run_async_in_thread(item):
        return asyncio.run(ruasync_wait(item))

    if request_dict['query']['testMethod'] == 'items':
        items = list(Chat_Test.objects.filter(id__in = request_dict['query']['selected']).values('id', 'country', 'query'))

    elif request_dict['query']['testMethod'] == 'testId':
        items = list(Chat_Test.objects.filter(test_id = request_dict['query']['selectedTestId']).values('id', 'country', 'query'))


    redis_client = redis.StrictRedis(host=REDIS_ORCHESTRATOR_IP, port=REDIS_PORT, db=0, password=REDIS_PASSWORD, ssl=True, decode_responses=True)

    for item in items:
        # Chat_Test.objects.filter(id=item['id']).update(response='', tested=False)
        session_id = str(uuid.uuid4())
        message_id = str(uuid.uuid4())
        item['session_id'] = session_id
        item['message_id'] = message_id
        session_dict = {
            "exit_status": ["no", ""], 
            "unstructured_query_data": [], 
            "structured_query_data": [], 
            "image_url": [], 
            "message_history": [], 
            "lang_id": ""
        }
        store_dict_with_expiry(
            redis_client, 
            session_id, 
            session_dict, 
            300, 
            message_id
        )
    process_items_multithreading(items)