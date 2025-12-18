import sys
sys.path.append("/www/alpha/")

import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "alpha.settings")
django.setup()

from typing import Literal
from pydantic import BaseModel

from alpha import __log
from apps.rubicon_v3.__function import __llm_call 
from apps.rubicon_v3.__function.definitions import intelligences
from apps.rubicon_v3.models import Prompt_Template, Front_Recommend


INTENT_GENERAL_CONVERSATION = "general_conversation"

class AssistantResult(BaseModel):
    re_asking_required: bool
    # product_group: Literal["모니터", "TV", "프로젝터", "사운드바", "냉장고", "세탁기", "청소기", "식기세척기", "에어컨", "큐커 멀티", "인덕션", "전자레인지", "스마트폰", "갤럭시 탭", "갤럭시 워치", "갤럭시 버즈", "갤럭시 링", "데스크탑", "갤럭시 북", "없음"]
    reasoning: str
import pandas as pd

def assistant(
    query: str,
    message_history: list,
    country_code: str,
    RAG_depth: str,
    query_type: str,
    init_ner_data,
    intelligence,
    model_name="gpt-4.1-mini",
    prompt="",
) -> bool:

    prompt = ""
    
    # target_product_conditions = list(Front_Recommend.objects.filter(active=True).values('front_disp_clsf_nm', 'front_filter_nm').distinct())
    # tp_df = pd.DataFrame(target_product_conditions).dropna().groupby('front_disp_clsf_nm', as_index=False)['front_filter_nm'].apply(lambda x: ','.join(x))
    # tp_df_string = tp_df.apply(lambda row: row['front_disp_clsf_nm']+': 가격', axis=1).to_string(header=False, index=False)
    # # tp_df_string = tp_df.apply(lambda row: row['front_disp_clsf_nm']+': '+"가격,"+row['front_filter_nm'], axis=1).to_string(header=False, index=False) # 나중에 살리기
    # # print(target_product_conditions)
    # prompt_values = {'target_product_placeholder': tp_df_string}
    
    try:
        prompt = list(Prompt_Template.objects.filter(country_code=country_code, response_type='assistant', active=True).values_list('prompt', flat=True))[0]
        # prompt = prompt % prompt_values
    except:
        pass

    # 시스템 프롬프트로 메시지 초기화
    messages = [{"role": "system", "content": [{"type": "text", "text": prompt}]}]
    
    # 완성된 사용자 메시지 추가
    messages.append(
        {"role": "user", "content": [{"type": "text", "text": f"User: {query}"}]}
    )

    response = __llm_call.open_ai_call_structured(
        model_name=model_name,
        messages=messages,
        temperature=0.01,
        top_p=1,
        response_format=AssistantResult,
        seed=42
    )


    if intelligence in [
        intelligences.ACCOUNT_MANAGEMENT,
        intelligences.FAQ,
        intelligences.ERROR_AND_FAILURE_RESPONSE,
        intelligences.ORDERS_AND_DELIVERY,
        intelligences.STORE_INFORMATION
    ]:
        response["re_asking_required"] = False


    return response


if __name__ == "__main__":

    # 삼성 냉장고 추천해줘
    # 신혼집에 사용할 냉장고 추천해줘
    # 아이가 곧 태어날 건데, 추천해줄 전자제품이 뭐가 있을까?
    # 아들이 초등학생인데, 어떤 핸드폰을 사주면 좋을까?

    # user_query = "내가 영화를 좋아하는데 어떤 삼성 제품이 좋을까?"
    # user_query = '20대 여동생에게 선물로 줄 거 추천해줄래?'
    # user_query = "부모님이 쓰실 TV 추천해줘"
    # user_query = "아이가 곧 태어날 건데, 추천해줄 전자제품이 뭐가 있을까?"
    # user_query = "신혼집에서 사용할 거 추천해줘"
    # user_query = "남편이 출장을 많이 다니는데 선물로 뭘 주면 좋을까?"
    # user_query = "갤럭시 S24 특징 알려줘"
    # user_query = "최근에 핸드폰은 사서 필요없는데"
    message_history = []
    
    qlist = """내 냉장고 매뉴얼좀 알려주라""".split('\n')
    
    for _q in qlist:
    
        response = assistant(
            query=_q,
            message_history=message_history,
            country_code='KR',
            RAG_depth='',
            query_type='',
            init_ner_data='',
            intelligence=intelligences.PRODUCT_DESCRIPTION,
            model_name="gpt-4.1-mini"
        )
        
        print('##########')
        print(_q)
        print(response)