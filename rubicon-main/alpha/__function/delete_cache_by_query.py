import sys
sys.path.append("/www/alpha")

import redis
from alpha.settings import REDIS_ORCHESTRATOR_IP, REDIS_PORT, REDIS_PASSWORD

redis_client = redis.StrictRedis(
    host=REDIS_ORCHESTRATOR_IP,
    port=REDIS_PORT,
    db=0,
    password=REDIS_PASSWORD,
    ssl=True,
)

cursor = 0

query_input = (
    input(
        f"\n■■■ Redis Cache에서 삭제할 채널 또는 key 입력 : "
    )
)


if len(query_input) < 2 :
    print(f"\n재입력 부탁드립니다.")
    exit()

matching_query = '*' + query_input + '*'

matching_query_confirm = (
    input(
        f"\n■■■ Redis Cache에서 조회 및 삭제할 key가 {matching_query}가 맞습니까? (yes/no) : "
    ).strip().lower()
)

if matching_query_confirm != "yes":
    print("\n■■■ Cache delete canceled.")
else:
    print("\n■■■ processing")
    len_sum = 0

    while True:
        cursor, keys = redis_client.scan(cursor, match=matching_query, count=1000)
        
        for key in keys:
            print(key.decode('utf-8'))
        
        if cursor != 0:
            len_sum = len_sum + len(keys)
            continue

        if cursor == 0 and len(keys) > 0:
            len_sum = len_sum + len(keys)
        
        if len_sum == 0:
            print(f"\n■■■ {matching_query} 에 일치하는 key가 없습니다.")
            exit()
        if cursor == 0:
            break

    confirm = (
        input(
            f"\n■■■ Redis Cache에 저장된 위의 key, 그리고 key에 매핑된 cache를 지우시겠습니까? (yes/no) : "
        ).strip().lower()
    )

    if confirm != "yes":
        print("\n■■■ Cache delete canceled.")
    else:
        while True:
            cursor, keys = redis_client.scan(cursor, match=matching_query, count=1000)
            
            for key in keys:
                redis_client.delete(key)

            if cursor == 0:
                break
        print(f"\n■■■ Deleted cache : {matching_query}")

#######################################################
#### cache에 저장되어 있는 종류 예시
#### :1:질의__cache__{채널명}__{국가코드}   =>   :1:200만원 이하 TV 추천해주세요__cache__AIBot__KR
#### :1:response__질의__0__{언어코드}__{채널명}__{국가코드}   =>   :1:response__200만원 이하 TV 추천해주세요__0__Korean__AIBot__KR
#### :1:response__질의__1__{언어코드}__{채널명}__{국가코드}   =>   :1:response__200만원 이하 TV 추천해주세요__1__Korean__AIBot__KR
#### :1:welcome_message_{채널명}_{국가코드}_{언어}   =>   :1:welcome_message_AIBot_KR_Korean
#### :1:greeting_query_{채널명}_{국가코드}_{언어}   =>   :1:greeting_query_AIBot_KR_Korean
#######################################################
