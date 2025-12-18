# line 2 ~ 7 테스트 시 주석 해제
import sys
sys.path.append('/www/alpha/')
import os
import re
import itertools
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'alpha.settings')

import time
from copy import deepcopy
import pandas as pd
import ast
from word2number import w2n
from functools import reduce
from alpha import __log
from django.db import connection
from apps.rubicon_v3.__function import _62_complement_code_mapping_utils as cm_utils
from apps.rubicon_v3.__function import _65_complement_price as price_check
from apps.rubicon_v3.__function import _66_complement_promotion as promotion
from apps.rubicon_v3.__function.definitions import intelligences, sub_intelligences

# 20250502 color, high level key, release_date drop_na 주석부분 삭제

# HC1
# 일반적인 경우에 S.. 단품으로 질의를 하더라도, 시리즈로 답변해야 함(답변정책, 예. S25 -> S25 시리즈)
# 일부 질의의 경우 시리즈로 매핑되지 않고 단품으로 동작해야 함(S25와 S25+ 비교해줘: S25는 단품으로 동작해야 함)
# 해당 간극에 대응하기 위한 매핑 set의 list

# HC2
# 무빙스타일의 경우 복수의 기준정보 category_lv3이 존재하여 온전하게 추천순 정렬을 사용하기 어려우므로, 최신순 정렬을 사용함

# HC3
# 인증중고폰, 통신사폰, 전용컬러(B2C), 스페셜 컬러(FN)의 경우 동일 기준정보 내에서 별도로 우선순위에 따른 정렬이 필요

# HC4
# 갤럭시 워치 울트라는 2024제품과 2025제품을 구분할 수 있는 수단이 model_code 뿐 이므로, 우선순위 상 2025 제품을 먼저 표출하기 위해 별도 리스트 사용(답변정책)

# HC1
series_set_price = [
    set(['갤럭시 S25', '갤럭시 S25+', '갤럭시 S25 울트라', '갤럭시 S25 엣지']),
    set(['갤럭시 S24', '갤럭시 S24+', '갤럭시 S24 울트라']),
    set(['갤럭시 S23', '갤럭시 S23+', '갤럭시 S23 Ultra']),
    set(['갤럭시 S22', '갤럭시 S22+', '갤럭시 S22 울트라']),
    set(['갤럭시 S21', '갤럭시 S21+', '갤럭시 S21 울트라']),
    set(['Galaxy S25', 'Galaxy S25+', 'Galaxy S25 Ultra', 'Galaxy S25 Edge']),
    set(['Galaxy S24', 'Galaxy S24+', 'Galaxy S24 Ultra']),
    set(['Galaxy S23', 'Galaxy S23+', 'Galaxy S23 Ultra']),
    set(['Galaxy S22', 'Galaxy S22+', 'Galaxy S22 Ultra']),
    set(['Galaxy S21', 'Galaxy S21+', 'Galaxy S21 Ultra']),
]
series_base = set(['갤럭시 S25', '갤럭시 S24', '갤럭시 S23', '갤럭시 S22', '갤럭시 S21', 'Galaxy S25', 'Galaxy S24', 'Galaxy S23', 'Galaxy S22', 'Galaxy S21'])



def new_extended_info2(complement_code_mapping, intelligence, sub_intelligence, query_analyzer, ner, grouped_ner_list, mentioned_products, l4_filter_list, country_code, site_cd, guid, channel, message_id, k = 1, date_list = [], pflag = False):
    new_extended_info_start_time = time.time()  # Record start time
    # __log.debug(grouped_ner_list)
    # price_df = []
    # promotion_df = []
    full_extended_info = []
    not_full_extended_info = []
    # initial_full_extended_info = []
    c2c_key = []
    product_operator_key = False
    price_operator_dict = {}    
    mentioned_stop_key = False
    not_in_date_list = []
    not_in_l4_list = []
    qflag = False
    # pre_owned_product_key = False
    # __log.debug(date_list)

    # n_item = 3 if len(grouped_ner_list) == 1 else 1
    # price_key = any(['product_price' in n.values() for n in ner])

    # request_key = any(['extend_request' in n.values() for n in ner])
    request_key = 'Extended Request' in query_analyzer.get('query_type')
    recommend_order = 'Best Selling Products' in query_analyzer.get('query_type')

    pair_match_key = not any(set(['product_spec', 'product_color']) & set([d.get('field') for l in grouped_ner_list for d in l])) and len(grouped_ner_list) > 1
    # __log.debug(pair_match_key)

    seen = set()
    filtered_grouped_code_mapping = []

    for d in complement_code_mapping:
        items = _to_hashable(d)
        if items not in seen:
            seen.add(items)
            filtered_grouped_code_mapping.append(d)
    complement_code_mapping = filtered_grouped_code_mapping

    mentioned_codes = []
    if request_key:
        mentioned_codes = sum([[d.get('code') for d in l] for l in mentioned_products], [])
    # __log.debug(f"mentioned_codes: {mentioned_codes}")
    for n_list in grouped_ner_list:
        group_expression = [d.get('expression') for d in n_list] if country_code == 'KR' else [d.get('expression').upper() for d in n_list]
        group_code_mapping = [d for d in complement_code_mapping if d.get('expression') in group_expression] if country_code == 'KR' else [d for d in complement_code_mapping if d.get('expression').upper() in group_expression]
        # __log.debug(group_code_mapping)
        group_length_key = [d for d in group_code_mapping if d.get('field') in ['product_model', 'product_code']]
        c2c_key.append(any([d for d in group_length_key if 'c2c' in d.get('type') or 'e2e' in d.get('type')]) or intelligence != intelligences.PRODUCT_RECOMMENDATION or sub_intelligence in [sub_intelligences.SET_PRODUCT_RECOMMENDATION, sub_intelligences.SET_PRODUCT_DESCRIPTION, sub_intelligences.BUNDLE_DISCOUNT])
        if len(group_length_key) > 1:
            option_expression = [d.get('expression') for d in n_list if d.get('field') in ['product_spec', 'product_option']]
            # __log.debug(option_expression)
            if option_expression:
                group_code_mapping = [d for d in group_code_mapping if (d.get('field') in ['product_model', 'product_code'] and set(d.get('option', {}).get('expression')).issubset(set(option_expression))) or d.get('field') in ['product_option']]
        # __log.debug(f"group_code_mapping: {group_code_mapping}")
        if not group_code_mapping:
            continue
        if ('NEW RADIO MOBILE (5G SMARTPHONE)' in group_code_mapping[0].get('category_lv2') and
             'p2p' in group_code_mapping[0].get('type') and 
             len(group_code_mapping[0].get('mapping_code', [])) > 1 and 
             intelligence == intelligences.PRODUCT_COMPARISON):
            pair_match_key = True
        l4_expression = [d.get('expression') for d in group_code_mapping if d.get('field') in ['product_model']]
        # __log.debug(f"l4_expression: {l4_expression}")
        l4_product_filter = sum([d.get('product_filter', []) for d in l4_filter_list if d.get('expression', "") in l4_expression and d.get('product_filter', [])], [])
        is_date = [d.get('expression') for d in n_list if d.get('field') == 'product_release_date']
        # negative_l4_product_filter insert 0611
        negative_l4_product_filter = sum([d.get('negative_product_filter', []) for d in l4_filter_list if d.get('expression', "") in l4_expression and d.get('negative_product_filter', [])], [])
        # __log.debug(f"is_date: {is_date}")
        date_list_part = []
        if is_date:
            date_list_part = sum([d.get('date_list') for d in date_list if d.get('expression') in is_date], [])
            # __log.debug(f"date_list_part: {date_list_part}")
        # negative_l4_product_filter insert 0611
        try:
            expression_gcm = group_code_mapping[0].get('expression')
        except:
            expression_gcm = "not_gcm_expression_to_match@@"
        full_extended_info_temp, not_in_date_temp, qflag = extended_info(group_code_mapping, intelligence, sub_intelligence, country_code, site_cd, message_id, k = 1, date_list = date_list_part, l4_product_filter = l4_product_filter, l4_expression = l4_expression, negative_l4_product_filter = negative_l4_product_filter, pflag = pflag, recommend_order = recommend_order)
        if full_extended_info_temp:
            for i in range(len(full_extended_info_temp)):
                df_gcm_temp = full_extended_info_temp[i]
                if not df_gcm_temp.empty:
                    df_gcm_temp['expression'] = expression_gcm
                full_extended_info_temp[i] = df_gcm_temp

        if not_in_date_temp:
            not_in_date_list.append(
                {
                    'date_expression': [d.get('expression') for d in date_list if d.get('expression') in is_date],
                    'expression': list(set(not_in_date_temp))[0]
                }
            )
        if not full_extended_info_temp and not any(['misuse' in d.get('category_lv1') for d in group_code_mapping if d.get('field') == 'product_model']):
            if [d.get('expression') for d in n_list if d.get('field') in ['product_model', 'product_code']]:
                not_in_l4_list.append(
                    {
                        'expression': [d.get('expression') for d in n_list if d.get('field') in ['product_model', 'product_code']][0]
                    }
                )

        if l4_product_filter:
            l4_product_filter = [s for s in l4_product_filter if s.isdigit()]
        # __log.debug(f"l4_product_filter: {l4_product_filter}")
        # __log.debug(f"full_extended_info_temp: {full_extended_info_temp}")
        if l4_product_filter and l4_expression:
            for i in range(len(full_extended_info_temp)):
                for l4_single_pattern in l4_product_filter:
                    full_extended_info_temp[i] = full_extended_info_temp[i][
                        full_extended_info_temp[i]['mapping_code'].str.contains(re.escape(l4_single_pattern), case = False)
                    ]
            # __log.debug(f"{l4_expression[0]}: {full_extended_info_temp}")
        # __log.debug(f"full_extended_info_temp: {full_extended_info_temp}")

        # __log.debug(f"full_extended_info_temp: {full_extended_info_temp}")
        mentioned_stop_key_list = []
        if request_key:
            filtered_extended_info_temp = []
            for df_temp in full_extended_info_temp:
                df_filt_temp = df_temp[df_temp['extended_info'].apply(lambda x: len(set(x).intersection(set(mentioned_codes))) == 0)]
                if not df_temp.empty and df_filt_temp.empty:
                    mentioned_stop_key_list.append(True)
                    # mentioned_stop_key = True
                if not df_filt_temp.empty:
                    filtered_extended_info_temp.append(df_filt_temp)
                    mentioned_stop_key_list.append(False)
                else:
                    pass
            mentioned_stop_key = all(mentioned_stop_key_list)
            full_extended_info_temp = filtered_extended_info_temp
        
        full_extended_info.extend(full_extended_info_temp)

    if len(grouped_ner_list) > 1:
        for l, df in zip(grouped_ner_list, full_extended_info):
            new_price_operator = {}
            ner_price_opreator = [d for d in l if d.get('field') == 'product_price' and d.get('operator') in ['greater_than', 'less_than', 'about']]
            price_product = [d.get('expression') for d in l if d.get('field') in ['product_model', 'product_code']]
            # print(f"ner_price_opreator: {ner_price_opreator}")
            if price_product:
                price_product = price_product[0]
            else:
                continue
            if ner_price_opreator and not df.empty: 
                operator_list = [d.get('operator') for d in ner_price_opreator]
                new_price_operator = get_new_operator(ner_price_opreator, country_code)
                # __log.debug(f"operator_list: {operator_list}")
                # __log.debug(f"new_price_operator: {new_price_operator}")
                for s in operator_list:
                    if new_price_operator.get(s):
                        continue
                    else:
                        series_set = set(df['mapping_code'].tolist())
                        # __log.debug(f"series set: {series_set}")
                        # __log.debug(f"s: {s}")
                        if series_set in series_set_price and (s == 'greater_than' or s == 'about'):
                            new_price_operator.get(s).extend(sum(df[df['mapping_code'].isin(list(series_set & series_base))]['extended_info'], []))
                        else:
                            new_price_operator.get(s).extend(sum(df['extended_info'], []))
                        product_operator_key = True

            if product_operator_key:
                price_operator_dict[price_product] = new_price_operator
    
    if product_operator_key:
        price_op_filter_no = []
        for i, l in enumerate(grouped_ner_list):
            if any(set([d.get('expression') for d in l if d.get('field') in ['product_model', 'product_code']]) & set([d for d in price_operator_dict if price_operator_dict.get(d) == {}])):
                price_op_filter_no.append(i)
        full_extended_info = [full_extended_info[i] for i in price_op_filter_no]



    # __log.debug(f"product_operator_key: {product_operator_key}")    
    # __log.debug(f"price_operator_dict: {price_operator_dict}")

    if pair_match_key and not product_operator_key:
        try:
            matched_temp = cm_utils.matching_extended_spec_pairs(full_extended_info, country_code, site_cd)
        except:
            matched_temp = None
        if not matched_temp:
            pass
        else:
            full_extended_info = matched_temp
    
    filter_row_extended_info_temp = []
    # 후순위 랭킹 insert 0620
    is_product_key = [d.get('expression') for d in complement_code_mapping if 'NA' in d.get('category_lv1') and 'NA' in d.get('category_lv2') and 'NA' in d.get('category_lv3')]
    for df in full_extended_info:
        if is_product_key:
            df = cm_utils.extra_categories_rank_lower(df, country_code)
        df_filtered_row = df[df['id'] <= 30]
        filter_row_extended_info_temp.append(df_filtered_row)
    full_extended_info = filter_row_extended_info_temp
    # __log.debug(f"full_extended_info: {full_extended_info}")

    # __log.debug(f"c2c: {c2c_key}")
    # price_time = time.time()
    full_extended_info_purchasable = []
    purchasable_list = []
    for df, is_c2c, gn in zip(full_extended_info, c2c_key, grouped_ner_list):
        if is_c2c:
            full_extended_info_purchasable.append(df)
        else:
            # if product_operator_key:
            df2 = df.copy()
            df_purchasable = cm_utils.get_purchasable(df2, country_code, site_cd)
            if len(df2) > 0 and len(df_purchasable) == 0:
                gn = [d.get('expression') for d in gn if d.get('field') in ['product_model', 'product_code']]
                purchasable_list.extend(gn)
                
            full_extended_info_purchasable.append(df_purchasable)
    full_extended_info = full_extended_info_purchasable
    # __log.debug(full_extended_info)
    # __log.debug(purchasable_list)
    
    full_extended_info_temp2 = []
    for l, df in zip(grouped_ner_list, full_extended_info):
        if ('not_in' in [d.get('operator') for d in l if d.get('field') in ['product_model', 'product_code']]):
            not_full_extended_info.append(df)
        else:
            full_extended_info_temp2.append(df)
    
    full_extended_info_temp3 = []
    if not_full_extended_info:
        not_mdl_set = set(sum([sum(fd['extended_info'].tolist(), []) for fd in not_full_extended_info], []))
        for df in full_extended_info_temp2:
            df['extended_info'].apply(lambda x: [l for l in x if l not in not_mdl_set])
            df = df[df['extended_info'].apply(lambda x: len(x) > 0)]
            full_extended_info_temp3.append(df)
        full_extended_info = full_extended_info_temp3
    # __log.debug(full_extended_info)
    # __log.debug(not_full_extended_info)
    
    
    # S25 단일제품(시리즈)질의가 아닐 경우, S25 단품으로 축소
    # HC1
    if len([df for df in full_extended_info if not df.empty]) > 1:
        # if (all([isinstance(df, ) for df in full_extended_info]))
        prj_series = []
        for i in range(len(full_extended_info)):
            df_p = full_extended_info[i]
            if set(df_p['mapping_code'].tolist()) in series_set_price:
                prj_series.append(True)
            else:
                prj_series.append(False)
        if all(prj_series):
            # 비교 질의일 때 시리즈 간 비교면 어떻게 해야 할까
            # if intelligence in [intelligences.PRODUCT_COMPARISON]:
            #     if all([not('시리즈' in d.get('expression') or 'series' in d.get('expression').lower()) for d in complement_code_mapping if d.get('field') == 'product_model']):
            #         for i in range(len(full_extended_info)):
            #             df = full_extended_info[i]
            #             if set(df['mapping_code'].tolist()) in series_set_price:
            #                 df = df[df['mapping_code'].isin(series_base)].drop('id', axis = 1).reset_index(drop = True)
            #                 df['id'] = df.index
            #                 full_extended_info[i] = df
            #     else:
            #         pass
            pass
        else:
            for i in range(len(full_extended_info)):
                df = full_extended_info[i]
                if set(df['mapping_code'].tolist()) in series_set_price:
                    df = df[df['mapping_code'].isin(series_base)].drop('id', axis = 1).reset_index(drop = True)
                    df['id'] = df.index
                    full_extended_info[i] = df
    # __log.debug(full_extended_info)
    if sub_intelligence in [sub_intelligences.SET_PRODUCT_RECOMMENDATION, sub_intelligences.SET_PRODUCT_DESCRIPTION, sub_intelligences.BUNDLE_DISCOUNT] and country_code == 'KR':
        set_extended_info = extended_info_set(full_extended_info, site_cd)
        # full_extended_info.append(set_extended_info)
        if set_extended_info.empty and sub_intelligence == sub_intelligences.BUNDLE_DISCOUNT:
            pass
        else:
            full_extended_info = [set_extended_info]
    # __log.debug(full_extended_info)
    # __log.debug(set_extended_info)

    elapsed_time = time.time() - new_extended_info_start_time
    # __log.debug(f"new_extended_info: get extended info time: {elapsed_time}")
    return full_extended_info, mentioned_stop_key, product_operator_key, price_operator_dict, purchasable_list, not_in_date_list, not_in_l4_list, qflag

def new_extended_info(complement_code_mapping, intelligence, sub_intelligence, query_analyzer, ner, grouped_ner_list, mentioned_products, l4_filter_list, country_code, site_cd, guid, channel, message_id, k = 1, date_list = []):
    qflag = False
    n_item = 3 if len(grouped_ner_list) == 1 else 1
    price_key = any(['product_price' in n.values() for n in ner])
    pre_owned_product_key = False
    initial_full_extended_info = []
    price_df = []
    promotion_df = []
    pflag = len([d for d in ner if d.get('field') == 'product_price' and d.get('operator') != 'in']) > 0 
    full_extended_info, mentioned_stop_key, product_operator_key, price_operator_dict, purchasable_list, not_in_date_list, not_in_l4_list, qflag = new_extended_info2(complement_code_mapping, intelligence, sub_intelligence, query_analyzer, ner, grouped_ner_list, mentioned_products, l4_filter_list, country_code, site_cd, guid, channel, message_id, k, date_list, False)
    
    
    # __log.debug(f"dadssdfassdfasF: {full_extended_info}")

    result_list = []
    if not full_extended_info:
        return full_extended_info, result_list, price_df, promotion_df, mentioned_stop_key, purchasable_list, not_in_date_list, not_in_l4_list
    
    # pre-owned product logic 0724
    if 'Pre-owned Products' in query_analyzer.get('query_type',[]):
        pre_owned_product_key = True

    full_extended_info_tmp = []
    if site_cd == 'B2C' and full_extended_info and not full_extended_info[0].empty:
        for df in full_extended_info:
            temp_df = deepcopy(df)
            temp_df = temp_df.to_dict('records')
            temp_df = pd.DataFrame(temp_df)
            
            if not temp_df.empty:
                if pre_owned_product_key:
                    temp_df['extended_info'] = temp_df['extended_info'].apply(
                    lambda lst: [x for x in lst if x.startswith('SM5')])
                else:
                    temp_df['extended_info'] = temp_df['extended_info'].apply(
                    lambda lst: [x for x in lst if not x.startswith('SM5')])
                temp_df = temp_df[temp_df['extended_info'].apply(lambda x: bool(x))] # extended_info list 가 비어있는 행 삭제
                full_extended_info_tmp.append(temp_df)
                
            else:
                full_extended_info_tmp.append(temp_df)
        
        full_extended_info = deepcopy(full_extended_info_tmp)
    
    if not full_extended_info:
        return full_extended_info, result_list, price_df, promotion_df, mentioned_stop_key, purchasable_list, not_in_date_list, not_in_l4_list
    
    if (not price_key and sub_intelligence not in [sub_intelligences.PRICE_EXPLANATION, sub_intelligences.PAYMENT_BENEFIT_EXPLANATION, sub_intelligences.EVENT_PROMOTION, sub_intelligences.BUNDLE_DISCOUNT, sub_intelligences.PAYMENT_METHOD_INFORMATION, sub_intelligences.PRODUCT_INVENTORY_AND_RESTOCKING]) or sub_intelligence in [sub_intelligences.PAYMENT_METHOD_INFORMATION]:
        # if sub_intelligence in ['Set Product Recommendation', 'Set Product Description', 'Bundle Discount']:
        #     full_extended_info = [df for df in full_extended_info if 'set' in df['meta'].tolist()]
        # __log.debug(full_extended_info)
        temp_list = []
        for df in full_extended_info:
            if df.empty:
                info_filtered = df
            else:
                df_filterd = df.copy()
                # __log.debug(df_filterd['mapping_code'].tolist())
                if set(df_filterd['mapping_code'].tolist()) in series_set_price:
                    info_filtered = df_filterd.to_dict('records')[:4]
                else:
                    info_filtered = df_filterd.to_dict('records')[:n_item]
            if not df.empty:
                temp_list.extend(info_filtered)
        temp_list_copied = deepcopy(temp_list)
        result_list.extend(temp_list_copied)
        
    else:
        dummy_key = []
        initial_full_extended_info = []
        
        for df in full_extended_info:
            initial_full_extended_info.extend(df.to_dict(orient='records'))
        # __log.debug(f"initial_full_extended_info: {initial_full_extended_info}")
        ### 06.05 inserted by hsm
        # if set(item['mapping_code']  for item in initial_full_extended_info) == set(['갤럭시 S25 울트라', '갤럭시 S25+', '갤럭시 S25']):
        #     initial_full_extended_info = list({item['mapping_code']: item for item in reversed(initial_full_extended_info)}.values())
        #     initial_full_extended_info = [{**item, 'id': idx} for idx, item in enumerate(initial_full_extended_info)]
            # __log.debug(f"initial_full_extended_info: {initial_full_extended_info}")
        ###
        # __log.debug(f"initial_full_extended_info2: {initial_full_extended_info}")
        initial_full_extended_info_copy = deepcopy(initial_full_extended_info)
        price_list_temp, price_df = price_check.price_check(ner, initial_full_extended_info_copy, country_code, grouped_ner_list, product_operator_key, price_operator_dict, pre_owned_product_key, site_cd)
        pflag = pflag and  price_df[0].get('price_status','') == 'no models in the price range' 
        if pflag and not qflag:
            full_extended_info, mentioned_stop_key, product_operator_key, price_operator_dict, purchasable_list, not_in_date_list, not_in_l4_list, qflag = new_extended_info2(complement_code_mapping, intelligence, sub_intelligence, query_analyzer, ner, grouped_ner_list, mentioned_products, l4_filter_list, country_code, site_cd, guid, message_id, k, date_list, pflag)
            initial_full_extended_info = []
            if 'Pre-owned Products' in query_analyzer.get('query_type',[]):
                pre_owned_product_key = True
            
            for df in full_extended_info:
                initial_full_extended_info.extend(df.to_dict(orient='records'))
            initial_full_extended_info_copy = deepcopy(initial_full_extended_info)
            price_list_temp, price_df = price_check.price_check(ner, initial_full_extended_info_copy, country_code, grouped_ner_list, product_operator_key, price_operator_dict, pre_owned_product_key, site_cd)


        price_df_temp = price_df[0].get('price',pd.DataFrame())
        # if not price_df_temp.empty:
        #     dummy_key = price_df_temp['Model Code'].iloc[:n_item].tolist()
        #     dummy_key = sum([[ss.strip() for ss in s.split(', ')] for s in dummy_key], [])
                
        # price_list = [d for d in price_list_temp if any(set(d.get('extended_info',[])) & set(dummy_key))]
        result_list.extend(price_list_temp)

        if result_list or price_df[0].get('telecom_price',{}):
            promotion_df = promotion.promotion_check(ner, result_list, deepcopy(price_df), sub_intelligence, country_code, guid, site_cd, channel)
            
        for item in price_df:
            if 'price' in item:
                final_df = item['price']
                grouped_final_df = (
                final_df.groupby(
                    ["Model Name", "standard_price", "benefit_price"], sort=False
                )
                .agg(
                    lambda x: (
                        ", ".join(map(str, set(x)))
                        if x.name != "standard_price"
                        and x.name != "benefit_price"
                        and x.name != "Model Name"
                        else x.iloc[0]
                    )
                )
                .reset_index()
            )

                original_columns = final_df.columns.tolist()
                final_df = grouped_final_df[original_columns]
            
                if country_code == 'KR':
                    final_df['standard_price'] = final_df['standard_price'].str.replace(' 원', '', regex=False)
                    final_df['standard_price'] = pd.to_numeric(final_df['standard_price'], errors='coerce')
                    final_df = final_df.sort_values(by='standard_price', ascending=True)
                    final_df['standard_price'] = final_df['standard_price'].astype(int).astype(str) + ' 원'
                else:
                    final_df['standard_price'] = final_df['standard_price'].str.replace(' GBP', '', regex=False)
                    final_df['standard_price'] = pd.to_numeric(final_df['standard_price'], errors='coerce')
                    final_df = final_df.sort_values(by='standard_price', ascending=True)
                    final_df['standard_price'] = final_df['standard_price'].astype(float).astype(str) + ' GBP'
                
                if site_cd == 'FN':
                    final_df = final_df.rename(columns={"standard_price":"출고가","benefit_price":"임직원가"})
                else:
                    final_df = final_df.rename(columns={"benefit_price":"discounted_price"})

                if final_df["Model Code"].str.startswith('SM-').any():
                    final_df = final_df.drop(["color"],axis=1, errors='ignore')
                                    
                final_df = final_df.rename(columns={"Model Code": "Key Model Code"}) 
                final_df = final_df[[col for col in final_df.columns if col != 'Key Model Code'] + ['Key Model Code']]

                item['price'] = final_df.to_markdown(index=False)

    return initial_full_extended_info, result_list, price_df, promotion_df, mentioned_stop_key, purchasable_list, not_in_date_list, not_in_l4_list

# negative l4 product filter insert yji
def extended_info(complement_code_mapping, intelligence, sub_intelligence, country_code, site_cd, message_id, k = 1, date_list = [], l4_product_filter = [], l4_expression = [], negative_l4_product_filter = [], pflag = False, recommend_order = False):
    qflag = False
    expressions = sum(
        [
            item["mapping_code"] if item["mapping_code"] is not None else [None]
            for item in complement_code_mapping
            if item["field"] in ["product_model", "product_code", "product_function", "product_option"]
        ],
        [],
    )
    # __log.debug(f"expression: {expressions}")
    # __log.debug(f"complement_code_mapping: {complement_code_mapping}")

    if not complement_code_mapping or not expressions:
        return [], []
    
    extended_result = []
    not_in_date = []

    # expression_embedding = embedding_rerank.baai_embedding(expression, message_id)
    if intelligence == intelligences.PRODUCT_RECOMMENDATION:
        k = 3
    field_list = list(set([ccm.get('field', "") for ccm in complement_code_mapping]))

    if any(f in field_list for f in ['product_model', 'product_code']):
        if sub_intelligence in [sub_intelligences.SET_PRODUCT_RECOMMENDATION, sub_intelligences.SET_PRODUCT_DESCRIPTION, sub_intelligences.BUNDLE_DISCOUNT] and site_cd == 'FN' and country_code == 'KR':
            extended_result_fn_set, not_in_date_fn_set = extended_info_fn_set(complement_code_mapping, intelligence, sub_intelligence, country_code, site_cd, message_id, k, date_list, l4_product_filter, l4_expression, negative_l4_product_filter, recommend_order)
            extended_result.extend(extended_result_fn_set)
            not_in_date.extend(not_in_date_fn_set)
        elif intelligence == intelligences.PRODUCT_RECOMMENDATION and not pflag:
            # __log.debug(f"l4_product_filterl4_product_filter: {l4_product_filter}")
            # negative_l4_product_filter insert 0611
            extended_result_recommend, not_in_date_recommend = extended_info_recommend(complement_code_mapping, intelligence, sub_intelligence, country_code, site_cd, message_id, k, date_list, l4_product_filter, l4_expression, negative_l4_product_filter, recommend_order)
            # __log.debug(f'extended_result_recommend: {extended_result_recommend}')
            len_info = 0
            if extended_result_recommend:
                len_info = sum([len(df) for df in extended_result_recommend])
            extended_result.extend(extended_result_recommend)
            not_in_date.extend(not_in_date_recommend)
            if not extended_result or len_info < 3:
                # negative_l4_product_filter insert 0611
                d_flag = False
                if not extended_result:
                    d_flag = True
                extended_result_product_code, not_in_date_code = extended_info_product_code(complement_code_mapping, intelligence, sub_intelligence, country_code, site_cd, message_id, k, date_list, l4_product_filter, l4_expression, negative_l4_product_filter)
                extended_result.extend(extended_result_product_code)
                if d_flag:
                    not_in_date = []
                else:
                    pass
                not_in_date.extend(not_in_date_code)
        else:
            # negative_l4_product_filter insert 0611
            extended_result_product_code, not_in_date_code = extended_info_product_code(complement_code_mapping, intelligence, sub_intelligence, country_code, site_cd, message_id, k, date_list, l4_product_filter, l4_expression, negative_l4_product_filter)
            extended_result.extend(extended_result_product_code)
            not_in_date.extend(not_in_date_code)
            qflag = True
    else:
        pass

    if extended_result:
        result_dataframe = pd.concat(extended_result, axis = 0).drop_duplicates(subset=['mapping_code'], keep='first').reset_index(drop=True)
        result_dataframe['id'] = result_dataframe.index
        extended_result= [result_dataframe]

    return extended_result, not_in_date, qflag

def extended_info_fn_set(complement_code_mapping, intelligence, sub_intelligence, country_code, site_cd, message_id, k, date_list = [], l4_product_filter = [], l4_expression = [], negative_l4_product_filter = [], recommend_order = False):
    if recommend_order:
        recommend_order_value = 'sales'
    else:
        recommend_order_value = 'ctg'
    SORTING_TYPE = {
        'KR': {
            'ctg': 'Recommend',
            'sales': 'Quantity'#'Quantity'
        },
    }
    sorting_type = SORTING_TYPE.get(country_code).get(recommend_order_value)
    recommend_table_nm = 'rubicon_data_product_recommend'
    filter_table_nm = 'rubicon_data_product_filter'

    code_mapping_fn = [cm for cm in complement_code_mapping if cm.get('field') == 'product_option' and ('func' in cm.get('type', "") or 'CPT' in cm.get('type', "") or 'CPT_D' in cm.get('type', ""))] 
    # __log.debug(f"code_mapping_fn: {code_mapping_fn}")
    code_mapping_prod = [cm for cm in complement_code_mapping if cm.get('field') in ['product_model', 'product_code']] 
    
    function_list = sum([
        value if isinstance(value, list) else [value]
        for f in code_mapping_fn
        for value in [f.get('mapping_code'),]
    ], [])
    result_list = []
    # __log.debug(f"function_list: {function_list}")
    function_operator_list = sum([
        value if isinstance(value, list) else [value]
        for f in code_mapping_fn
        for value in [f.get('operator'),]
    ], [])
    # __log.debug(f"function_operator_list: {function_operator_list}")

    recent_key=False
    date_len = None
    date_format = None
    not_in_date = []
    if date_list:
        if 'NEWEST' in date_list:
            recent_key = True
            date_list.remove('NEWEST')
        date_len = len(date_list[0])
        if date_len == 4:
            date_format = '%Y'
        elif date_len == 7:
            date_format = '%Y-%m'
        elif date_len == 10:
            date_list = [s[0:7] for s in date_list]
            date_format = '%Y-%m'
        

    with connection.cursor() as curs:

        for cmp in code_mapping_prod:

            category_lv1 = cmp.get('category_lv1', "")
            category_lv2 = cmp.get('category_lv2', "")
            category_lv3 = cmp.get('category_lv3', "")
            mapping_code = cmp.get('mapping_code', "")
            mdl_cd = cmp.get('mdl_code', "")

            field_value = cmp.get('field', "")
            spec_key = cmp.get('option', {}).get('field', "")
            set_key = "s2s" in cmp.get("type", "") or "fs2fs" in cmp.get("type", "")
                              

            category_lv1_placeholder = ", ".join(
                            "'" + _ + "'" for _ in cmp.get("category_lv1", "")
                        )
            category_lv2_placeholder = ", ".join(
                            "'" + _ + "'" for _ in cmp.get("category_lv2", "")
                        )
            category_lv3_placeholder = ", ".join(
                            "'" + _ + "'" for _ in cmp.get("category_lv3", "")
                        )
            mapping_code_palceholder = ", ".join(
                            "'" + _ + "'" for _ in list(set(cmp.get("mapping_code", "")))
                        )
            mdl_placeholder = ", ".join(
                            "'" + _ + "'" for _ in mdl_cd
                        )
            if country_code == "KR":
                if len(function_list) == 0:
                    query = f"""
                            SELECT 
                            product_category_lv1,
                            product_category_lv2,
                            product_category_lv3,
                            mdl_code,
                            goods_nm,
                            id as ids,
                            release_date
                            FROM
                            (SELECT
                            id,
                            product_category_lv1,
                            product_category_lv2,
                            product_category_lv3,
                            mdl_code,
                            goods_nm,
                            release_date, 
                            sorting_type, 
                            site_cd, 
                            disp_clsf_nm,
                            ctg_rank,
                            row_number () over (partition by disp_clsf_nm, goods_id, sorting_type order by ctg_rank) as rk from rubicon_data_product_recommend
                            UNION ALL
                            SELECT DISTINCT 
                                9999 AS id,    
                                main.cstrt_category_lv1 AS product_category_lv1,
                                main.cstrt_category_lv2 AS product_category_lv2,
                                main.cstrt_category_lv3 AS product_category_lv3,
                                main.cstrt_mdl_code AS mdl_code,
                                main.cstrt_goods_nm AS goods_nm,
                                cat.release_date,
                                sort_types.sorting_type,
                                'FN' AS site_cd,
                                disp_lv2 AS disp_clsf_nm,
                                9999 as ctg_rank,
                                1 AS rk
                            FROM rubicon_data_product_set_mst main
                            CROSS JOIN (
                                SELECT 'Recommend' AS sorting_type
                                UNION ALL
                                SELECT 'Quantity' AS sorting_type
                            ) sort_types
                            LEFT JOIN (
                                SELECT DISTINCT 
                                    mdl_code, 
                                    release_date 
                                FROM rubicon_data_product_category
                                WHERE mdl_code IN (
                                    SELECT DISTINCT cstrt_mdl_code 
                                    FROM rubicon_data_product_set_mst
                                    WHERE cstrt_mdl_code NOT IN (
                                        SELECT DISTINCT mdl_code 
                                        FROM rubicon_data_product_recommend 
                                        WHERE site_cd = 'FN'
                                    )
                                )
                            ) cat ON main.cstrt_mdl_code = cat.mdl_code
                            WHERE main.cstrt_mdl_code NOT IN (
                                SELECT DISTINCT mdl_code 
                                FROM rubicon_data_product_recommend 
                                WHERE site_cd = 'FN'
                            )
                            )
                            WHERE site_cd = '{site_cd}'
                            AND sorting_type = '{sorting_type}'
                            """
                    if category_lv1_placeholder and 'NA' not in category_lv1_placeholder:
                        query += f"and product_category_lv1 in ({category_lv1_placeholder})"
                    if category_lv2_placeholder and 'NA' not in category_lv2_placeholder:
                        query += f"and product_category_lv2 in ({category_lv2_placeholder})"
                    if category_lv3_placeholder and 'NA' not in category_lv3_placeholder:
                        query += f"and product_category_lv3 in ({category_lv3_placeholder})"
                    if mdl_placeholder:
                        query += f" and mdl_code in ({mdl_placeholder})"
                    query_2 = query
                    if not set_key:
                        query += f"and (goods_nm in ({mapping_code_palceholder}) or mdl_code in ({mapping_code_palceholder}))"
                    else:
                        set_pattern = f"%{mapping_code_palceholder.strip("'\"")}%"
                        query += f" and goods_nm like '{set_pattern}'"
                    query += """
                            and rk = 1
                            order by disp_clsf_nm, ctg_rank
                        """
                    query_2 += """
                            and rk = 1
                            order by disp_clsf_nm, ctg_rank
                        """
                else:
                    if len(function_list) > 0:
                        query = f"""
                            select product_category_lv1, product_category_lv2, product_category_lv3, mdl_code, goods_nm, ids, release_date from (
                            select pf.*, pr.ctg_rank, pr.id as ids, replace(pf.filter_item_nm,' ','') as stripped_filter_item_nm, row_number () over (partition by pf.disp_clsf_nm, pf.goods_id, pr.sorting_type order by pr.ctg_rank) as rk from {filter_table_nm} pf 
                                inner join {recommend_table_nm} pr on pr.goods_id = pf.goods_id and pr.site_cd = pf.site_cd
                                WHERE pf.mdl_code NOT IN (
                                    SELECT DISTINCT mdl_code 
                                    FROM {filter_table_nm}
                                    WHERE 
                        """
                        not_in_conditions = []
                        for f, fo in zip(function_list, function_operator_list):
                            if fo == "not_in":
                                not_in_conditions.append(f"replace(filter_item_nm,' ','') like '%{f.replace(' ','')}%'")
                        
                        if not_in_conditions:
                            query += " OR ".join(not_in_conditions)
                        else:
                            query += "1=2"
                        
                        query += ") "
                        if 'in' in function_operator_list:
                            query += "AND ("
                            for f, fo in zip(function_list, function_operator_list):
                                if fo == "in":
                                    query += f"""
                                        replace(pf.filter_item_nm,' ','') like '%{f.replace(' ','')}%' OR
                                    """
                            query += "1=2)"

                    else:
                        query = f"""
                            select product_category_lv1, product_category_lv2, product_category_lv3, mdl_code, goods_nm, ids, release_date from (
                            select pf.*, pr.ctg_rank, pr.id as ids, row_number () over (partition by pf.disp_clsf_nm, pf.goods_id, pr.sorting_type order by pr.ctg_rank) as rk from {filter_table_nm} pf 
                                inner join {recommend_table_nm} pr on pr.goods_id = pf.goods_id and pr.site_cd = pf.site_cd
                                WHERE 1=1
                        """
                    query += f" and pf.site_cd = '{site_cd}'"
                    query += f"and sorting_type = '{sorting_type}'"
                    if intelligence == intelligences.PRODUCT_RECOMMENDATION and country_code == 'KR' and sub_intelligence not in [sub_intelligences.SET_PRODUCT_RECOMMENDATION, sub_intelligences.SET_PRODUCT_DESCRIPTION, sub_intelligences.BUNDLE_DISCOUNT] and 's2s' not in cmp.get("type", ""):
                        query += f" and pf.set_tp_cd in ('00', '10')"
                    if category_lv1_placeholder and 'NA' not in category_lv1_placeholder:
                        query += f" and pf.product_category_lv1 in ({category_lv1_placeholder})"
                    if category_lv2_placeholder and 'NA' not in category_lv2_placeholder:
                        query += f" and pf.product_category_lv2 in ({category_lv2_placeholder})"
                    if category_lv3_placeholder and 'NA' not in category_lv3_placeholder:
                        query += f" and pf.product_category_lv3 in ({category_lv3_placeholder})"
                    if mdl_placeholder:
                        query += f" and pf.mdl_code in ({mdl_placeholder})"
                    query_2 = query
                    if not set_key:
                        query += f" and (pf.goods_nm in ({mapping_code_palceholder}) or pf.mdl_code in ({mapping_code_palceholder}))"
                    else:
                        set_pattern = f"%{mapping_code_palceholder.strip("'\"")}%"
                        query += f" and pf.goods_nm like '{set_pattern}'"
                    query += """)
                        where rk = 1
                        order by disp_clsf_nm, ctg_rank
                    """
                    query_2 += """)
                        where rk = 1
                        order by disp_clsf_nm, ctg_rank
                    """
                    # __log.debug(f'query_2: {query_2}')
            else:
                continue
            # __log.debug(query)
            curs.execute(query)
            result_nm = curs.fetchall()

            # print(result_nm)
            # print(f"****** {query}")
            if result_nm and '인덕션' not in mapping_code:
                # print(f"****** {query}")
                nm_list = []
                for row in result_nm:
                    category_lv1, category_lv2, category_lv3, model_code, goods_nm, id, release_date = row
                    product_filter_check = True
                    if l4_product_filter and l4_expression:
                        for l4_single_pattern in l4_product_filter:
                        ############## 0611 yji insert #################
                            if l4_single_pattern[0] =='[':
                                list_ = ast.literal_eval(l4_single_pattern)
                                if any(item in goods_nm.lower() for item in set(list_)):
                                    product_filter_check = product_filter_check and True
                                else:
                                    product_filter_check = product_filter_check and False
                            else:        
                                product_filter_check = product_filter_check and bool(re.search(re.escape(l4_single_pattern), goods_nm, re.IGNORECASE))
                        #################################################
                    # negative_l4_product_filter insert 0611
                    if negative_l4_product_filter and l4_expression:
                        for negative_l4_single_pattern in negative_l4_product_filter:
                            product_filter_check = product_filter_check and not bool(re.search(re.escape(negative_l4_single_pattern), goods_nm, re.IGNORECASE))

                    if product_filter_check:
                        nm_list.append({
                            "country_code": country_code,
                            "mapping_code": goods_nm if cmp.get("field") == 'product_model' else model_code,
                            "category_lv1": category_lv1,
                            "category_lv2": category_lv2,
                            "category_lv3": category_lv3,
                            "edge": "recommend",
                            "meta": "" if field_value == 'product_model' else goods_nm,
                            "model_code": model_code,
                            "id": id,
                            "release_date": release_date,
                        })
                df_nm = pd.DataFrame(nm_list)
                if df_nm.empty:
                    continue
                df_nm['id'] = df_nm['id'].fillna(99999)
                # HC2
                if cmp.get('category_lv3', "") == 'Moving Style':
                    df_nm = df_nm.sort_values('release_date', ascending=False)
                    df_nm['id'] = range(len(df_nm))
                if date_list and date_len and date_format:
                    date_len_flag = len(df_nm)
                    df_nm['release_date'] = df_nm['release_date'].apply(lambda x: x.strftime(date_format) if x is not None else x)
                    df_nm['release_date'] = df_nm['release_date'].fillna('1000-01-01')
                    if not recent_key:
                        df_nm = df_nm[df_nm['release_date'].isin(date_list)]
                    elif recent_key:
                        df_nm_fy = df_nm[df_nm['release_date'].isin(date_list)].copy()
                        if df_nm_fy.empty:
                            additional_date_list = cm_utils.create_date_sequence_excluding_base(date_list[0], '3Y')
                            date_list = additional_date_list + date_list
                            df_nm_fy = df_nm[df_nm['release_date'].isin(date_list)].copy()
                        df_nm = df_nm_fy
                        df_nm = df_nm.sort_values('release_date', ascending=False)
                        df_nm['id'] = range(len(df_nm))
                    if date_len_flag > 0 and len(df_nm) == 0 and not recent_key:
                        not_in_date.append(cmp.get('expression'))
                        continue
                nm_processed = (
                        df_nm
                        .drop_duplicates()
                        .assign(min_id = lambda x: x.groupby(["mapping_code", "category_lv1", "category_lv2", "category_lv3"])['id'].transform('min'))
                        .groupby(["mapping_code", "category_lv1", "category_lv2", "category_lv3", "edge", "meta", "min_id"])["model_code"]
                        .agg(list)
                        .reset_index()
                        .sort_values(['min_id'], ascending=True) 
                        .rename(columns = {'model_code': 'extended_info'})
                    )
                result_list.append(nm_processed)
            elif 'c2c' not in cmp.get("type", "") and 'e2e' not in cmp.get("type", "") and 's2s' not in cmp.get("type", "") and not mdl_placeholder:
                # print(f"--------{query_2}")
                if len(function_list) > 0:
                    curs.execute(query_2)
                else:
                    curs.execute(query_2)
                result_hnm = curs.fetchall()

                if not result_hnm:
                    pass 
                else:
                    hnm_list = []
                    for row in result_hnm:
                        # __log.debug(f"row: {row}")
                        category_lv1, category_lv2, category_lv3, model_code, goods_nm, id, release_date = row
                        product_filter_check = True
                        # __log.debug(f"l4_product_filter: {l4_product_filter}")
                        # __log.debug(f"negative_l4_product_filter: {negative_l4_product_filter}")
                        if country_code == 'KR':
                            is_merchandising = category_lv1 == "MERCHANDISING"
                            is_refrigrator = category_lv1 == "냉장고"
                            is_mobile = category_lv1 == "HHP"
                            is_printer = category_lv3 == "Printer"
                            is_external = (category_lv3 == "External HDD") or (category_lv3 == "External SSD")
                            is_airdresser = category_lv3 in ["Bespoke AirDresser", "AirDresser"]
                            is_serif = category_lv3 == "The Serif"
                            if l4_product_filter and l4_expression:
                                for l4_single_pattern in l4_product_filter:
                                ############## 0611 yji insert #################
                                    if l4_single_pattern[0] =='[':
                                        list_ = ast.literal_eval(l4_single_pattern)
                                        if any(item in goods_nm.lower() for item in set(list_)):
                                            product_filter_check = product_filter_check and True
                                        else:
                                            product_filter_check = product_filter_check and False
                                    else:        
                                        product_filter_check = product_filter_check and bool(re.search(re.escape(l4_single_pattern), goods_nm, re.IGNORECASE))
                                #################################################
                            # negative_l4_product_filter insert 0611
                            if negative_l4_product_filter and l4_expression:
                                for negative_l4_single_pattern in negative_l4_product_filter:
                                    product_filter_check = product_filter_check and not bool(re.search(re.escape(negative_l4_single_pattern), goods_nm, re.IGNORECASE))
                            expression = clean_expression_kr(goods_nm, is_merchandising, is_refrigrator, is_mobile, is_printer, is_external, is_airdresser, is_serif)
                            # __log.debug(f"{goods_nm}: {product_filter_check}")
                            # __log.debug(expression)
                        elif country_code == 'GB':
                            is_ha = category_lv1 == "Home Appliances"
                            is_mobile = category_lv1 == "Mobile"
                            is_printer = category_lv3 == "Printer"
                            is_external = (category_lv3 == "External HDD") or (category_lv3 == "External SSD")
                            is_computer = category_lv1 == 'Computers'
                            if l4_product_filter and l4_expression:
                                for l4_single_pattern in l4_product_filter:
                                ############## 0611 yji insert #################
                                    if l4_single_pattern[0] =='[':
                                        list_ = ast.literal_eval(l4_single_pattern)
                                        if any(item in goods_nm.lower() for item in set(list_)):
                                            product_filter_check = product_filter_check and True
                                        else:
                                            product_filter_check = product_filter_check and False
                                    else:        
                                        product_filter_check = product_filter_check and bool(re.search(re.escape(l4_single_pattern), goods_nm, re.IGNORECASE))
                                #################################################
                            # negative_l4_product_filter insert 0611
                            if negative_l4_product_filter and l4_expression:
                                for negative_l4_single_pattern in negative_l4_product_filter:
                                    product_filter_check = product_filter_check and not bool(re.search(re.escape(negative_l4_single_pattern), goods_nm, re.IGNORECASE))
                            expression = clean_expression_uk(goods_nm, model_code, is_ha, is_mobile, is_printer, is_external, is_computer)

                        if product_filter_check:
                            hnm_list.append({
                                "country_code": country_code,
                                "mapping_code": expression,
                                "goods_nm": goods_nm,
                                "category_lv1": category_lv1,
                                "category_lv2": category_lv2,
                                "category_lv3": category_lv3,
                                "edge": "recommend",
                                "meta": "",
                                "model_code": model_code,
                                "id": id,
                                "release_date": release_date,
                            })
                    df_hnm = pd.DataFrame(hnm_list)
                    if df_hnm.empty:
                        continue
                    if cmp.get('category_lv3', "") == 'Moving Style':
                        # print("aaaaaaaaaa")
                        df_hnm = df_hnm.sort_values('release_date', ascending=False)
                        df_hnm['id'] = range(len(df_hnm))
                    # HC3
                    spc_key = df_hnm['goods_nm'].str.contains('스페셜 컬러', na = False).any()
                    if spc_key:
                        df_hnm1 = df_hnm[~df_hnm['goods_nm'].str.contains('스페셜 컬러', na = False)]
                        df_hnm2 = df_hnm[df_hnm['goods_nm'].str.contains('스페셜 컬러', na = False)]
                        df_hnm = pd.concat([df_hnm1, df_hnm2], ignore_index=True)
                    if date_list and date_len and date_format:
                        date_len_flag = len(df_hnm)
                        df_hnm['release_date'] = df_hnm['release_date'].apply(lambda x: x.strftime(date_format) if x is not None else x)
                        df_hnm['release_date'] = df_hnm['release_date'].fillna('1000-01-01') 
                        if not recent_key:
                            df_hnm = df_hnm[df_hnm['release_date'].isin(date_list)]
                        elif recent_key:
                            df_hnm_fy = df_hnm[df_hnm['release_date'].isin(date_list)].copy()
                            if df_hnm_fy.empty:
                                additional_date_list = cm_utils.create_date_sequence_excluding_base(date_list[0], '3Y')
                                date_list = additional_date_list + date_list
                                df_hnm_fy = df_hnm[df_hnm['release_date'].isin(date_list)].copy()
                            df_hnm = df_hnm_fy
                            df_hnm = df_hnm.sort_values('release_date', ascending=False)
                            df_hnm['id'] = range(len(df_hnm))
                        df_hnm = df_hnm[df_hnm['release_date'].isin(date_list)]
                        if recent_key:
                            df_hnm = df_hnm.sort_values('release_date', ascending=False)
                            df_hnm['id'] = range(len(df_hnm))
                        if date_len_flag > 0 and len(df_hnm) == 0  and not recent_key:
                            not_in_date.append(cmp.get('expression'))
                    # __log.debug(df_hnm)
                    if df_hnm.empty:
                        continue
                    # 06.04 deleted by hsm
                    # if test_key:
                    #     df_hnm = df_hnm.loc[df_hnm['mapping_code'].str.lower().isin([s.lower() for s in mapping_code])]
                    hnm_processed = (
                        df_hnm
                        .drop_duplicates()
                        .assign(min_id = lambda x: x.groupby(["mapping_code", "category_lv1", "category_lv2", "category_lv3"])['id'].transform('min'))
                        .groupby(["mapping_code", "category_lv1", "category_lv2", "category_lv3", "edge", "meta", "min_id"])["model_code"]
                        .agg(list)
                        .reset_index()
                        .sort_values(['min_id'], ascending=True) 
                        .rename(columns = {'model_code': 'extended_info'})
                    )
                    # __log.debug(f'hnm_processed: {hnm_processed}')
                    if hnm_processed.empty:
                        pass
                    else:
                        result_list.append(hnm_processed)
    
    if result_list:
        result_dataframe = pd.concat(result_list, axis = 0).sort_values('min_id', ascending = True).reset_index(drop = True).drop('min_id', axis=1)
        result_list = [result_dataframe]

    return result_list, not_in_date

def extended_info_recommend(complement_code_mapping, intelligence, sub_intelligence, country_code, site_cd, message_id, k, date_list = [], l4_product_filter = [], l4_expression = [], negative_l4_product_filter = [], recommend_order = False):
    if recommend_order:
        recommend_order_value = 'sales'
    else:
        recommend_order_value = 'ctg'
    SORTING_TYPE = {
        'KR': {
            'ctg': 'Recommend',
            'sales': 'Quantity'#'Quantity'
        },
        'GB': {
            'ctg': 'recommended',
            'sales': 'recommended'#'없네?' # TODO: 값 들어오면 변경
        }
    }
    sorting_type = SORTING_TYPE.get(country_code).get(recommend_order_value)
    recommend_table_nm = 'rubicon_data_product_recommend' if country_code == 'KR' else 'rubicon_data_uk_product_order'
    filter_table_nm = 'rubicon_data_product_filter' if country_code == 'KR' else 'rubicon_data_uk_product_filter'

    code_mapping_fn = [cm for cm in complement_code_mapping if cm.get('field') == 'product_option' and ('func' in cm.get('type', "") or 'CPT' in cm.get('type', "") or 'CPT_D' in cm.get('type', ""))] 
    # __log.debug(f"code_mapping_fn: {code_mapping_fn}")
    code_mapping_prod = [cm for cm in complement_code_mapping if cm.get('field') in ['product_model', 'product_code']] 
    
    function_list = sum([
        value if isinstance(value, list) else [value]
        for f in code_mapping_fn
        for value in [f.get('mapping_code'),]
    ], [])
    result_list = []
    # __log.debug(f"function_list: {function_list}")
    function_operator_list = sum([
        value if isinstance(value, list) else [value]
        for f in code_mapping_fn
        for value in [f.get('operator'),]
    ], [])
    # __log.debug(f"function_operator_list: {function_operator_list}")

    recent_key=False
    date_len = None
    date_format = None
    not_in_date = []
    if date_list:
        if 'NEWEST' in date_list:
            recent_key = True
            date_list.remove('NEWEST')
        date_len = len(date_list[0])
        if date_len == 4:
            date_format = '%Y'
        elif date_len == 7:
            date_format = '%Y-%m'
        elif date_len == 10:
            date_list = [s[0:7] for s in date_list]
            date_format = '%Y-%m'
        

    with connection.cursor() as curs:

        for cmp in code_mapping_prod:

            category_lv1 = cmp.get('category_lv1', "")
            category_lv2 = cmp.get('category_lv2', "")
            category_lv3 = cmp.get('category_lv3', "")
            mapping_code = cmp.get('mapping_code', "")
            mdl_cd = cmp.get('mdl_code', "")

            field_value = cmp.get('field', "")
            spec_key = cmp.get('option', {}).get('field', "")
            test_key = ("h2h" in cmp.get("type", "") and 'p2p' not in cmp.get('type', ""))
            set_key = "s2s" in cmp.get("type", "")
                              

            category_lv1_placeholder = ", ".join(
                            "'" + _ + "'" for _ in cmp.get("category_lv1", "")
                        )
            category_lv2_placeholder = ", ".join(
                            "'" + _ + "'" for _ in cmp.get("category_lv2", "")
                        )
            category_lv3_placeholder = ", ".join(
                            "'" + _ + "'" for _ in cmp.get("category_lv3", "")
                        )
            mapping_code_palceholder = ", ".join(
                            "'" + _ + "'" for _ in list(set(cmp.get("mapping_code", "")))
                        )
            mdl_placeholder = ", ".join(
                            "'" + _ + "'" for _ in mdl_cd
                        )
            if country_code == "KR":
                if len(function_list) == 0:
                    query = f"""
                            SELECT 
                                product_category_lv1,
                                product_category_lv2,
                                product_category_lv3,
                                mdl_code,
                                goods_nm,
                                id as ids,
                                release_date
                            FROM
                            (SELECT * ,row_number () over (partition by disp_clsf_nm, goods_id, sorting_type order by ctg_rank) as rk from {recommend_table_nm})
                            WHERE site_cd = '{site_cd}'
                            AND sorting_type = '{sorting_type}'
                            """
                    if intelligence == intelligences.PRODUCT_RECOMMENDATION and country_code == 'KR' and sub_intelligence not in [sub_intelligences.SET_PRODUCT_RECOMMENDATION, sub_intelligences.SET_PRODUCT_DESCRIPTION, sub_intelligences.BUNDLE_DISCOUNT] and 's2s' not in cmp.get("type", ""):
                        query += f"and set_tp_cd in ('00', '10')"
                    if category_lv1_placeholder and 'NA' not in category_lv1_placeholder:
                        query += f"and product_category_lv1 in ({category_lv1_placeholder})"
                    if category_lv2_placeholder and 'NA' not in category_lv2_placeholder:
                        query += f"and product_category_lv2 in ({category_lv2_placeholder})"
                    if category_lv3_placeholder and 'NA' not in category_lv3_placeholder:
                        query += f"and product_category_lv3 in ({category_lv3_placeholder})"
                    if mdl_placeholder:
                        query += f" and mdl_code in ({mdl_placeholder})"
                    query_2 = query
                    if not set_key:
                        query += f"and (goods_nm in ({mapping_code_palceholder}) or mdl_code in ({mapping_code_palceholder}))"
                    else:
                        set_pattern = f"%{mapping_code_palceholder.strip("'\"")}%"
                        query += f" and goods_nm like '{set_pattern}'"
                    query += """
                            and rk = 1
                            order by disp_clsf_nm, ctg_rank
                        """
                    query_2 += """
                            and rk = 1
                            order by disp_clsf_nm, ctg_rank
                        """
                else:
                    if len(function_list) > 0:
                        query = f"""
                            select product_category_lv1, product_category_lv2, product_category_lv3, mdl_code, goods_nm, ids, release_date from (
                            select pf.*, pr.ctg_rank, pr.id as ids, replace(pf.filter_item_nm,' ','') as stripped_filter_item_nm, row_number () over (partition by pf.disp_clsf_nm, pf.goods_id, pr.sorting_type order by pr.ctg_rank) as rk from {filter_table_nm} pf 
                                inner join {recommend_table_nm} pr on pr.goods_id = pf.goods_id and pr.site_cd = pf.site_cd
                                WHERE pf.mdl_code NOT IN (
                                    SELECT DISTINCT mdl_code 
                                    FROM {filter_table_nm}
                                    WHERE 
                        """
                        not_in_conditions = []
                        for f, fo in zip(function_list, function_operator_list):
                            if fo == "not_in":
                                not_in_conditions.append(f"replace(filter_item_nm,' ','') like '%{f.replace(' ','')}%'")
                        
                        if not_in_conditions:
                            query += " OR ".join(not_in_conditions)
                        else:
                            query += "1=2"
                        
                        query += ") "
                        if 'in' in function_operator_list:
                            query += "AND ("
                            for f, fo in zip(function_list, function_operator_list):
                                if fo == "in":
                                    query += f"""
                                        replace(pf.filter_item_nm,' ','') like '%{f.replace(' ','')}%' OR
                                    """
                            query += "1=2)"

                    else:
                        query = f"""
                            select product_category_lv1, product_category_lv2, product_category_lv3, mdl_code, goods_nm, ids, release_date from (
                            select pf.*, pr.ctg_rank, pr.id as ids, row_number () over (partition by pf.disp_clsf_nm, pf.goods_id, pr.sorting_type order by pr.ctg_rank) as rk from {filter_table_nm} pf 
                                inner join {recommend_table_nm} pr on pr.goods_id = pf.goods_id and pr.site_cd = pf.site_cd
                                WHERE 1=1
                        """
                    query += f" and pf.site_cd = '{site_cd}'"
                    query += f"and sorting_type = '{sorting_type}'"
                    if intelligence == intelligences.PRODUCT_RECOMMENDATION and country_code == 'KR' and sub_intelligence not in [sub_intelligences.SET_PRODUCT_RECOMMENDATION, sub_intelligences.SET_PRODUCT_DESCRIPTION, sub_intelligences.BUNDLE_DISCOUNT] and 's2s' not in cmp.get("type", ""):
                        query += f" and pf.set_tp_cd in ('00', '10')"
                    if category_lv1_placeholder and 'NA' not in category_lv1_placeholder:
                        query += f" and pf.product_category_lv1 in ({category_lv1_placeholder})"
                    if category_lv2_placeholder and 'NA' not in category_lv2_placeholder:
                        query += f" and pf.product_category_lv2 in ({category_lv2_placeholder})"
                    if category_lv3_placeholder and 'NA' not in category_lv3_placeholder:
                        query += f" and pf.product_category_lv3 in ({category_lv3_placeholder})"
                    if mdl_placeholder:
                        query += f" and pf.mdl_code in ({mdl_placeholder})"
                    query_2 = query
                    if not set_key:
                        query += f" and (pf.goods_nm in ({mapping_code_palceholder}) or pf.mdl_code in ({mapping_code_palceholder}))"
                    else:
                        set_pattern = f"%{mapping_code_palceholder.strip("'\"")}%"
                        query += f" and pf.goods_nm like '{set_pattern}'"
                    query += """)
                        where rk = 1
                        order by disp_clsf_nm, ctg_rank
                    """
                    query_2 += """)
                        where rk = 1
                        order by disp_clsf_nm, ctg_rank
                    """
                    # __log.debug(f'query_2: {query_2}')
            else:
                if not spec_key and len(function_list) == 0:
                    query = f"""
                            SELECT DISTINCT
                                pf.category_lv1,
                                pf.category_lv2,
                                pf.category_lv3,
                                pr.representative_model,
                                pf.display_name,
                                -pr.sorting_no as id,
                                pf.launch_date
                            FROM
                            {recommend_table_nm} pr
                            inner join rubicon_data_uk_product_filter pf on pr.representative_model = pf.model_code and pr.site_cd = pf.site_cd
                            WHERE pf.site_cd = '{site_cd}'
                            AND pr.sort_type = '{sorting_type}'
                            """
                    if intelligence == intelligences.PRODUCT_RECOMMENDATION and country_code == 'KR' and sub_intelligence not in [sub_intelligences.SET_PRODUCT_RECOMMENDATION, sub_intelligences.SET_PRODUCT_DESCRIPTION, sub_intelligences.BUNDLE_DISCOUNT] and 's2s' not in cmp.get("type", ""):
                        query += f"and pf.set_tp_cd in ('00', '10')"
                    if category_lv1_placeholder and 'NA' not in category_lv1_placeholder:
                        query += f"and pf.category_lv1 in ({category_lv1_placeholder})"
                    if category_lv2_placeholder and 'NA' not in category_lv2_placeholder:
                        query += f"and pf.category_lv2 in ({category_lv2_placeholder})"
                    if category_lv3_placeholder and 'NA' not in category_lv3_placeholder:
                        query += f"and pf.category_lv3 in ({category_lv3_placeholder})"
                    if mdl_placeholder:
                        query += f"and pf.model_code in ({mdl_placeholder})"
                    query_2 = query
                    query += f"and (pf.display_name in ({mapping_code_palceholder}) or pr.representative_model in ({mapping_code_palceholder}))"
                    query += """
                            order by - sorting_no
                        """
                    query_2 += """
                            order by - sorting_no
                        """
                else:
                    if len(function_list) > 0:
                        query = f"""
                            select pf.category_lv1, pf.category_lv2, pf.category_lv3, pf.model_code, pf.display_name, -pr.sorting_no as id, pf.launch_date from rubicon_data_uk_product_filter pf
                            inner join rubicon_data_uk_product_order pr on pr.representative_model = pf.model_code and pr.site_cd = pf.site_cd
                            WHERE pf.model_code NOT IN (
                                SELECT DISTINCT model_code 
                                FROM rubicon_data_uk_product_filter
                                WHERE 
                        """
                        not_in_conditions = []
                        for f, fo in zip(function_list, function_operator_list):
                            if fo == "not_in":
                                not_in_conditions.append(f"replace(filter_item_nm,' ','') like '%{f.replace(' ','')}%'")
                        
                        if not_in_conditions:
                            query += " OR ".join(not_in_conditions)
                        else:
                            query += "1=2"
                        
                        query += ") "
                        if 'in' in function_operator_list:
                            query += "AND ("
                            for f, fo in zip(function_list, function_operator_list):
                                if fo == "in":
                                    query += f"""
                                        replace(pf.filter_item_nm,' ','') like '%{f.replace(' ','')}%' OR
                                    """
                            query += "1=2)"
                    else:
                        query = f"""
                            select pf.category_lv1, pf.category_lv2, pf.category_lv3, pf.model_code, pf.display_name, -pr.sorting_no as id, pf.launch_date from rubicon_data_uk_product_filter pf
                            inner join rubicon_data_uk_product_order pr on pr.representative_model = pf.model_code and pr.site_cd = pf.site_cd
                            WHERE 1=1
                        """
                    query += f" and pf.site_cd = '{site_cd}' and pr.sort_type = '{sorting_type}'"
                    if intelligence == intelligences.PRODUCT_RECOMMENDATION and country_code == 'KR' and sub_intelligence not in [sub_intelligences.SET_PRODUCT_RECOMMENDATION, sub_intelligences.SET_PRODUCT_DESCRIPTION, sub_intelligences.BUNDLE_DISCOUNT] and 's2s' not in cmp.get("type", ""):
                        query += f" and pf.set_tp_cd in ('00', '10')"
                    if category_lv1_placeholder and 'NA' not in category_lv1_placeholder:
                        query += f" and pf.category_lv1 in ({category_lv1_placeholder})"
                    if category_lv2_placeholder and 'NA' not in category_lv2_placeholder:
                        query += f" and pf.category_lv2 in ({category_lv2_placeholder})"
                    if category_lv3_placeholder and 'NA' not in category_lv3_placeholder:
                        query += f" and pf.category_lv3 in ({category_lv3_placeholder})"
                    if mdl_placeholder:
                        query += f" and pf.model_code in ({mdl_placeholder})"
                    query_2 = query
                    query += f" and (pf.display_name in ({mapping_code_palceholder}) or pf.model_code in ({mapping_code_palceholder}))"
                    query += """
                        order by sorting_no
                    """
                    query_2 += """
                        order by sorting_no
                    """

            if len(function_list) > 0:
                curs.execute(query)
            else:
                curs.execute(query)
            result_nm = curs.fetchall()

            # print(result_nm)
            # print(f"****** {query}")
            if result_nm and '인덕션' not in mapping_code:
                # print(f"****** {query}")
                nm_list = []
                for row in result_nm:
                    category_lv1, category_lv2, category_lv3, model_code, goods_nm, id, release_date = row
                    product_filter_check = True
                    if l4_product_filter and l4_expression:
                        for l4_single_pattern in l4_product_filter:
                        ############## 0611 yji insert #################
                            if l4_single_pattern[0] =='[':
                                list_ = ast.literal_eval(l4_single_pattern)
                                if any(item in goods_nm.lower() for item in set(list_)):
                                    product_filter_check = product_filter_check and True
                                else:
                                    product_filter_check = product_filter_check and False
                            else:        
                                product_filter_check = product_filter_check and bool(re.search(re.escape(l4_single_pattern), goods_nm, re.IGNORECASE))
                        #################################################
                    # negative_l4_product_filter insert 0611
                    if negative_l4_product_filter and l4_expression:
                        for negative_l4_single_pattern in negative_l4_product_filter:
                            product_filter_check = product_filter_check and not bool(re.search(re.escape(negative_l4_single_pattern), goods_nm, re.IGNORECASE))

                    if product_filter_check:
                        nm_list.append({
                            "country_code": country_code,
                            "mapping_code": goods_nm if cmp.get("field") == 'product_model' else model_code,
                            "category_lv1": category_lv1,
                            "category_lv2": category_lv2,
                            "category_lv3": category_lv3,
                            "edge": "recommend",
                            "meta": "" if field_value == 'product_model' else goods_nm,
                            "model_code": model_code,
                            "id": id,
                            "release_date": release_date,
                        })
                df_nm = pd.DataFrame(nm_list)
                if df_nm.empty:
                    continue
                df_nm['id'] = df_nm['id'].fillna(99999)
                if cmp.get('category_lv3', "") == 'Moving Style':
                    df_nm = df_nm.sort_values('release_date', ascending=False)
                    df_nm['id'] = range(len(df_nm))
                if date_list and date_len and date_format:
                    date_len_flag = len(df_nm)
                    df_nm['release_date'] = df_nm['release_date'].apply(lambda x: x.strftime(date_format) if x is not None else x)
                    df_nm['release_date'] = df_nm['release_date'].fillna('1000-01-01')
                    if not recent_key:
                        df_nm = df_nm[df_nm['release_date'].isin(date_list)]
                    elif recent_key:
                        df_nm_fy = df_nm[df_nm['release_date'].isin(date_list)].copy()
                        if df_nm_fy.empty:
                            additional_date_list = cm_utils.create_date_sequence_excluding_base(date_list[0], '3Y')
                            date_list = additional_date_list + date_list
                            df_nm_fy = df_nm[df_nm['release_date'].isin(date_list)].copy()
                        df_nm = df_nm_fy
                        df_nm = df_nm.sort_values('release_date', ascending=False)
                        df_nm['id'] = range(len(df_nm))
                    if date_len_flag > 0 and len(df_nm) == 0 and not recent_key:
                        not_in_date.append(cmp.get('expression'))
                        continue
                nm_processed = (
                        df_nm
                        .drop_duplicates()
                        .assign(min_id = lambda x: x.groupby(["mapping_code", "category_lv1", "category_lv2", "category_lv3"])['id'].transform('min'))
                        .groupby(["mapping_code", "category_lv1", "category_lv2", "category_lv3", "edge", "meta", "min_id"])["model_code"]
                        .agg(list)
                        .reset_index()
                        .sort_values(['min_id'], ascending=True) 
                        .rename(columns = {'model_code': 'extended_info'})
                    )
                result_list.append(nm_processed)
            elif 'c2c' not in cmp.get("type", "") and 'e2e' not in cmp.get("type", "") and 's2s' not in cmp.get("type", "") and not mdl_placeholder:
                # print(f"--------{query_2}")
                if len(function_list) > 0:
                    curs.execute(query_2)
                else:
                    curs.execute(query_2)
                result_hnm = curs.fetchall()

                if not result_hnm:
                    pass 
                else:
                    hnm_list = []
                    for row in result_hnm:
                        # __log.debug(f"row: {row}")
                        category_lv1, category_lv2, category_lv3, model_code, goods_nm, id, release_date = row
                        product_filter_check = True
                        # __log.debug(f"l4_product_filter: {l4_product_filter}")
                        # __log.debug(f"negative_l4_product_filter: {negative_l4_product_filter}")
                        if country_code == 'KR':
                            is_merchandising = category_lv1 == "MERCHANDISING"
                            is_refrigrator = category_lv1 == "냉장고"
                            is_mobile = category_lv1 == "HHP"
                            is_printer = category_lv3 == "Printer"
                            is_external = (category_lv3 == "External HDD") or (category_lv3 == "External SSD")
                            is_airdresser = category_lv3 in ["Bespoke AirDresser", "AirDresser"]
                            is_serif = category_lv3 == "The Serif"
                            if l4_product_filter and l4_expression:
                                for l4_single_pattern in l4_product_filter:
                                ############## 0611 yji insert #################
                                    if l4_single_pattern[0] =='[':
                                        list_ = ast.literal_eval(l4_single_pattern)
                                        if any(item in goods_nm.lower() for item in set(list_)):
                                            product_filter_check = product_filter_check and True
                                        else:
                                            product_filter_check = product_filter_check and False
                                    else:        
                                        product_filter_check = product_filter_check and bool(re.search(re.escape(l4_single_pattern), goods_nm, re.IGNORECASE))
                                #################################################
                            # negative_l4_product_filter insert 0611
                            if negative_l4_product_filter and l4_expression:
                                for negative_l4_single_pattern in negative_l4_product_filter:
                                    product_filter_check = product_filter_check and not bool(re.search(re.escape(negative_l4_single_pattern), goods_nm, re.IGNORECASE))
                            expression = clean_expression_kr(goods_nm, is_merchandising, is_refrigrator, is_mobile, is_printer, is_external, is_airdresser, is_serif)
                            # __log.debug(f"{goods_nm}: {product_filter_check}")
                            # __log.debug(expression)
                            # expression = expression if expression != '갤럭시 S25 울트라' else '갤럭시 S25 Ultra'
                        elif country_code == 'GB':
                            is_ha = category_lv1 == "Home Appliances"
                            is_mobile = category_lv1 == "Mobile"
                            is_printer = category_lv3 == "Printer"
                            is_external = (category_lv3 == "External HDD") or (category_lv3 == "External SSD")
                            is_computer = category_lv1 == 'Computers'
                            if l4_product_filter and l4_expression:
                                for l4_single_pattern in l4_product_filter:
                                ############## 0611 yji insert #################
                                    if l4_single_pattern[0] =='[':
                                        list_ = ast.literal_eval(l4_single_pattern)
                                        if any(item in goods_nm.lower() for item in set(list_)):
                                            product_filter_check = product_filter_check and True
                                        else:
                                            product_filter_check = product_filter_check and False
                                    else:        
                                        product_filter_check = product_filter_check and bool(re.search(re.escape(l4_single_pattern), goods_nm, re.IGNORECASE))
                                #################################################
                            # negative_l4_product_filter insert 0611
                            if negative_l4_product_filter and l4_expression:
                                for negative_l4_single_pattern in negative_l4_product_filter:
                                    product_filter_check = product_filter_check and not bool(re.search(re.escape(negative_l4_single_pattern), goods_nm, re.IGNORECASE))
                            expression = clean_expression_uk(goods_nm, model_code, is_ha, is_mobile, is_printer, is_external, is_computer)

                        if product_filter_check:
                            hnm_list.append({
                                "country_code": country_code,
                                "mapping_code": expression,
                                "goods_nm": goods_nm,
                                "category_lv1": category_lv1,
                                "category_lv2": category_lv2,
                                "category_lv3": category_lv3,
                                "edge": "recommend",
                                "meta": "",
                                "model_code": model_code,
                                "id": id,
                                "release_date": release_date,
                            })
                    df_hnm = pd.DataFrame(hnm_list)
                    if df_hnm.empty:
                        continue
                    # HC3
                    jyc_key = df_hnm['goods_nm'].str.contains('전용컬러', na = False).any()
                    spc_key = df_hnm['goods_nm'].str.contains('스페셜 컬러', na = False).any()
                    if jyc_key:
                        df_hnm1 = df_hnm[~df_hnm['goods_nm'].str.contains('전용컬러', na = False)]
                        df_hnm2 = df_hnm[df_hnm['goods_nm'].str.contains('전용컬러', na = False)]
                        df_hnm = pd.concat([df_hnm1, df_hnm2], ignore_index=True)
                    if spc_key:
                        df_hnm1 = df_hnm[~df_hnm['goods_nm'].str.contains('스페셜 컬러', na = False)]
                        df_hnm2 = df_hnm[df_hnm['goods_nm'].str.contains('스페셜 컬러', na = False)]
                        df_hnm = pd.concat([df_hnm1, df_hnm2], ignore_index=True)

                    # HC2
                    if cmp.get('category_lv3', "") == 'Moving Style':
                        # print("aaaaaaaaaa")
                        df_hnm = df_hnm.sort_values('release_date', ascending=False)
                        df_hnm['id'] = range(len(df_hnm))
                    if date_list and date_len and date_format:
                        date_len_flag = len(df_hnm)
                        df_hnm['release_date'] = df_hnm['release_date'].apply(lambda x: x.strftime(date_format) if x is not None else x)
                        df_hnm['release_date'] = df_hnm['release_date'].fillna('1000-01-01') 
                        if not recent_key:
                            df_hnm = df_hnm[df_hnm['release_date'].isin(date_list)]
                        elif recent_key:
                            df_hnm_fy = df_hnm[df_hnm['release_date'].isin(date_list)].copy()
                            if df_hnm_fy.empty:
                                additional_date_list = cm_utils.create_date_sequence_excluding_base(date_list[0], '3Y')
                                date_list = additional_date_list + date_list
                                df_hnm_fy = df_hnm[df_hnm['release_date'].isin(date_list)].copy()
                            df_hnm = df_hnm_fy
                            df_hnm = df_hnm.sort_values('release_date', ascending=False)
                            df_hnm['id'] = range(len(df_hnm))
                        df_hnm = df_hnm[df_hnm['release_date'].isin(date_list)]
                        if recent_key:
                            df_hnm = df_hnm.sort_values('release_date', ascending=False)
                            df_hnm['id'] = range(len(df_hnm))
                        if date_len_flag > 0 and len(df_hnm) == 0  and not recent_key:
                            not_in_date.append(cmp.get('expression'))
                    # __log.debug(df_hnm)
                    if df_hnm.empty:
                        continue
                    # 06.04 deleted by hsm
                    # if test_key:
                    #     df_hnm = df_hnm.loc[df_hnm['mapping_code'].str.lower().isin([s.lower() for s in mapping_code])]
                    hnm_processed = (
                        df_hnm
                        .drop_duplicates()
                        .assign(min_id = lambda x: x.groupby(["mapping_code", "category_lv1", "category_lv2", "category_lv3"])['id'].transform('min'))
                        .groupby(["mapping_code", "category_lv1", "category_lv2", "category_lv3", "edge", "meta", "min_id"])["model_code"]
                        .agg(list)
                        .reset_index()
                        .sort_values(['min_id'], ascending=True) 
                        .rename(columns = {'model_code': 'extended_info'})
                    )
                    # __log.debug(f'hnm_processed: {hnm_processed}')
                    if hnm_processed.empty:
                        pass
                    else:
                        result_list.append(hnm_processed)
    
    if result_list:
        result_dataframe = pd.concat(result_list, axis = 0).sort_values('min_id', ascending = True).reset_index(drop = True).drop('min_id', axis=1)
        result_list = [result_dataframe]

    return result_list, not_in_date

# negative_l4_product_filter insert 0611
def extended_info_product_code(complement_code_mapping, intelligence, sub_intelligence, country_code, site_cd, message_id, k, date_list, l4_product_filter = [], l4_expression = [], negative_l4_product_filter = []):
    filter_table_nm = 'rubicon_data_product_filter' if country_code == 'KR' else 'rubicon_data_uk_product_filter'
    full_table_nm = 'rubicon_data_product_category' if country_code == 'KR' else 'rubicon_data_uk_product_spec_basics'

    code_mapping_fn = [cm for cm in complement_code_mapping if cm.get('field') == 'product_option' and ('func' in cm.get('type', "") or 'CPT' in cm.get('type', "") or 'CPT_D' in cm.get('type', ""))] 
    code_mapping_prod = [cm for cm in complement_code_mapping if cm.get('field') in ['product_model', 'product_code']] 
    
    function_list = sum([
        value if isinstance(value, list) else [value]
        for f in code_mapping_fn
        for value in [f.get('mapping_code'),]
    ], [])
    function_operator_list = sum([
        value if isinstance(value, list) else [value]
        for f in code_mapping_fn
        for value in [f.get('operator'),]
    ], [])

    recent_key=False
    date_len = None
    date_format = None
    not_in_date = []
    if date_list:
        if 'NEWEST' in date_list:
            recent_key = True
            date_list.remove('NEWEST')
        date_len = len(date_list[0])
        if date_len == 4:
            date_format = '%Y'
        elif date_len == 7:
            date_format = '%Y-%m'
        elif date_len == 10:
            date_list = [s[0:7] for s in date_list]
            date_format = '%Y-%m'

    if country_code == 'KR':
        n10_table = """select 
                        product_category_lv1, 
                        product_category_lv2, 
                        product_category_lv3, 
                        mdl_code, 
                        goods_nm, 
                        release_date, 
                        site_cd, 
                        set_tp_cd 
                    from rubicon_data_product_category
                    union all
                    select 
                        product_category_lv1, 
                        product_category_lv2, 
                        product_category_lv3, 
                        mdl_code, 
                        goods_nm, 
                        release_date, 
                        site_cd, 
                        set_tp_cd
                    from rubicon_data_prd_mst_hist"""
    else:
        n10_table = """select 
	category_lv1, 
	category_lv2,
	category_lv3,
	model_code,
	display_name,
	launch_date,
	site_cd
from rubicon_data_uk_product_spec_basics 
union all
select 
	category_lv1, 
	category_lv2,
	category_lv3,
	model_code,
	display_name,
	launch_date,
	site_cd
from rubicon_data_uk_product_spec_basics_hist"""

    if country_code == 'KR':
        n10_filter_table = """
select product_category_lv1, product_category_lv2, product_category_lv3, mdl_code, goods_nm, release_date, goods_id, site_cd, set_tp_cd, filter_item_nm
from rubicon_data_product_filter_hst
union all
select product_category_lv1, product_category_lv2, product_category_lv3, mdl_code, goods_nm, release_date, goods_id, site_cd, set_tp_cd, filter_item_nm
from rubicon_data_product_filter
"""
    else:
        n10_filter_table = "select * from rubicon_data_uk_product_filter"

    # print("**************************************")
    # print(f"code_mapping_prod: {code_mapping_prod}")
    # print(function_list)
    # print("**************************************")
    result_list = []

    with connection.cursor() as curs:

        for cmp in code_mapping_prod:

            category_lv1 = cmp.get('category_lv1', "")
            category_lv2 = cmp.get('category_lv2', "")
            category_lv3 = cmp.get('category_lv3', "")
            mapping_code = cmp.get('mapping_code', "")
            mdl_cd = cmp.get('mdl_code', "")
            
            field_value = cmp.get('field', "")
            spec_key = cmp.get('option', {}).get('field', "")
            test_key = ("h2h" in cmp.get("type", "") and 'p2p' not in cmp.get('type', ""))
            set_key = "s2s" in cmp.get("type", "")

            category_lv1_placeholder = ", ".join(
                            "'" + _ + "'" for _ in cmp.get("category_lv1", "")
                        )
            category_lv2_placeholder = ", ".join(
                            "'" + _ + "'" for _ in cmp.get("category_lv2", "")
                        )
            category_lv3_placeholder = ", ".join(
                            "'" + _ + "'" for _ in cmp.get("category_lv3", "")
                        )
            mapping_code_palceholder = ", ".join(
                            "'" + _ + "'" for _ in list(set(cmp.get("mapping_code", "")))
                        )

            mdl_placeholder = ", ".join(
                            "'" + _ + "'" for _ in mdl_cd
                        )
            
            if len(function_list) == 0:
                query = f"""
                        SELECT
                            {'product_category_lv1' if country_code == 'KR' else 'category_lv1'}, 
                            {'product_category_lv2' if country_code == 'KR' else 'category_lv2'}, 
                            {'product_category_lv3' if country_code == 'KR' else 'category_lv3'}, 
                            {'mdl_code' if country_code == 'KR' else 'model_code'}, 
                            {'goods_nm' if country_code == 'KR' else 'display_name'}, 
                            {'release_date' if country_code == 'KR' else 'launch_date'} as release_date
                        FROM ({n10_table})
                        WHERE site_cd = '{site_cd}'
                        """

                if intelligence == intelligences.PRODUCT_RECOMMENDATION and country_code == 'KR' and sub_intelligence not in [sub_intelligences.SET_PRODUCT_RECOMMENDATION, sub_intelligences.SET_PRODUCT_DESCRIPTION, sub_intelligences.BUNDLE_DISCOUNT] and 's2s' not in cmp.get("type", ""):
                        query += f"and set_tp_cd in ('00', '10')"
                if intelligence == intelligences.PRODUCT_COMPARISON and country_code == 'KR' and 'c2c' not in cmp.get("type", "") and 'e2e' not in cmp.get("type", "") and 's2s' not in cmp.get("type", ""):
                        query += f"and set_tp_cd in ('00', '10')"
                if category_lv1_placeholder and 'NA' not in category_lv1_placeholder:
                    query += f"AND {'product_category_lv1' if country_code == 'KR' else 'category_lv1'} in ({category_lv1_placeholder}) "
                if category_lv2_placeholder and 'NA' not in category_lv2_placeholder:
                    query += f"AND {'product_category_lv2' if country_code == 'KR' else 'category_lv2'}  in ({category_lv2_placeholder}) "
                if category_lv3_placeholder and 'NA' not in category_lv3_placeholder:
                    query += f"AND {'product_category_lv3' if country_code == 'KR' else 'category_lv3'}  in ({category_lv3_placeholder}) "
                if mdl_placeholder:
                    query += f"AND {'mdl_code' if country_code == 'KR' else 'model_code'} in ({mdl_placeholder})"
                query_2 = query

                if not (set_key and country_code == 'KR'):
                    query += f"""AND ({'goods_nm' if country_code == 'KR' else 'display_name'} in ({mapping_code_palceholder}) 
                                OR {'mdl_code' if country_code == 'KR' else 'model_code'} in ({mapping_code_palceholder}))"""
                else:
                    set_pattern = f"%{mapping_code_palceholder.strip("'\"")}%"
                    query += f" and goods_nm like '{set_pattern}'"
            else:
                if len(function_list) > 0:
                    mdl_code_col = 'mdl_code' if country_code == 'KR' else 'model_code'
                    
                    query = f"""
                        SELECT
                            a.{'product_category_lv1' if country_code == 'KR' else 'category_lv1'}, 
                            a.{'product_category_lv2' if country_code == 'KR' else 'category_lv2'}, 
                            a.{'product_category_lv3' if country_code == 'KR' else 'category_lv3'}, 
                            a.{'mdl_code' if country_code == 'KR' else 'model_code'}, 
                            a.{'goods_nm' if country_code == 'KR' else 'display_name'}, 
                            b.{'release_date' if country_code == 'KR' else 'launch_date'} as release_date
                        FROM ({n10_filter_table}) a, {full_table_nm} b
                    """
                    
                    if country_code == 'KR':
                        query += f"""
                            WHERE a.goods_id = b.goods_id and a.mdl_code = b.mdl_code and a.site_cd = b.site_cd
                        """
                        if intelligence == intelligences.PRODUCT_COMPARISON and 'c2c' not in cmp.get("type", "") and 'e2e' not in cmp.get("type", "") and 's2s' not in cmp.get("type", ""):
                            query += f"and b.set_tp_cd in ('00', '10')"
                            
                    else:
                        query += f"""
                            WHERE a.model_code = b.model_code and a.site_cd = b.site_cd
                        """
                    query += f"""
                        AND a.{mdl_code_col} NOT IN (
                            SELECT DISTINCT {mdl_code_col}
                            FROM {filter_table_nm}
                            WHERE 
                    """
                    
                    not_in_conditions = []
                    for f, fo in zip(function_list, function_operator_list):
                        if fo == "not_in":
                            not_in_conditions.append(f"replace(filter_item_nm,' ','') like '%{f.replace(' ','')}%'")
                    
                    if not_in_conditions:
                        query += " OR ".join(not_in_conditions)
                    else:
                        query += "1=2"
                    
                    query += ") "
                    if 'in' in function_operator_list:
                        query += "AND ("
                        for f, fo in zip(function_list, function_operator_list):
                            if fo == "in":
                                query += f"""
                                    replace(a.filter_item_nm,' ','') like '%{f.replace(' ','')}%' OR
                                """
                        query += "1=2)"
                else:
                    query = f"""
                            SELECT 
                                a.{'product_category_lv1' if country_code == 'KR' else 'category_lv1'}, 
                                a.{'product_category_lv2' if country_code == 'KR' else 'category_lv2'}, 
                                a.{'product_category_lv3' if country_code == 'KR' else 'category_lv3'}, 
                                a.{'mdl_code' if country_code == 'KR' else 'model_code'}, 
                                a.{'goods_nm' if country_code == 'KR' else 'display_name'}, 
                                b.{'release_date' if country_code == 'KR' else 'launch_date'} as release_date
                            FROM {filter_table_nm} a, {full_table_nm} b
                        """
                    if country_code == 'KR':
                        query += f"""
                                WHERE a.goods_id = b.goods_id and a.mdl_code = b.mdl_code and a.site_cd = b.site_cd
                            """
                    else:
                        query += f"""
                                WHERE a.model_code = b.model_code and a.site_cd = b.site_cd
                            """
                query += f"and a.site_cd = '{site_cd}'"
                if intelligence == intelligences.PRODUCT_RECOMMENDATION and country_code == 'KR' and sub_intelligence not in [sub_intelligences.SET_PRODUCT_RECOMMENDATION, sub_intelligences.SET_PRODUCT_DESCRIPTION, sub_intelligences.BUNDLE_DISCOUNT] and 's2s' not in cmp.get("type", ""):
                    query += f"and a.set_tp_cd in ('00', '10')"
                if category_lv1_placeholder and 'NA' not in category_lv1_placeholder:
                    query += f"AND a.{'product_category_lv1' if country_code == 'KR' else 'category_lv1'} in ({category_lv1_placeholder})"
                if category_lv2_placeholder and 'NA' not in category_lv2_placeholder:
                    query += f"AND a.{'product_category_lv2' if country_code == 'KR' else 'category_lv2'} in ({category_lv2_placeholder})"
                if category_lv3_placeholder and 'NA' not in category_lv3_placeholder:
                    query += f"AND a.{'product_category_lv3' if country_code == 'KR' else 'category_lv3'} in ({category_lv3_placeholder})"
                if mdl_placeholder:
                    query += f"AND a.{'mdl_code' if country_code == 'KR' else 'model_code'} in ({mdl_placeholder})"

                query_2 = query
                if not (country_code == 'KR' and set_key):
                    query += f"""AND (a.{'goods_nm' if country_code == 'KR' else 'display_name'} in ({mapping_code_palceholder}) 
                                OR a.{'mdl_code' if country_code == 'KR' else 'model_code'} in ({mapping_code_palceholder}))"""
                else:
                    set_pattern = f"%{mapping_code_palceholder.strip("'\"")}%"
                    query += f" and a.goods_nm like '{set_pattern}'"
            # print(query)
            if len(function_list) > 0:
                curs.execute(query)
            else:
                curs.execute(query)
            result_nm = curs.fetchall()

            if result_nm and '인덕션' not in mapping_code:
                # print("----------------*")
                # print(query)
                nm_list = []
                for row in result_nm:
                    category_lv1, category_lv2, category_lv3, model_code, goods_nm, release_date = row
                    product_filter_check = True
                    if l4_product_filter and l4_expression:
                        for l4_single_pattern in l4_product_filter:
                        ############## 0611 yji insert #################
                            if l4_single_pattern[0] =='[':
                                list_ = ast.literal_eval(l4_single_pattern)
                                if any(item in goods_nm.lower() for item in set(list_)):
                                    product_filter_check = product_filter_check and True
                                else:
                                    product_filter_check = product_filter_check and False
                            else:        
                                product_filter_check = product_filter_check and bool(re.search(re.escape(l4_single_pattern), goods_nm, re.IGNORECASE))
                        #################################################
                    # negative_l4_product_filter insert 0611
                    if negative_l4_product_filter and l4_expression:
                        for negative_l4_single_pattern in negative_l4_product_filter:
                            product_filter_check = product_filter_check and not bool(re.search(re.escape(negative_l4_single_pattern), goods_nm, re.IGNORECASE))
                    if product_filter_check:
                        nm_list.append({
                            "country_code": country_code,
                            "mapping_code": goods_nm if cmp.get("field") == 'product_model' else model_code,
                            "category_lv1": category_lv1,
                            "category_lv2": category_lv2,
                            "category_lv3": category_lv3,
                            "edge": "recommend",
                            "meta": "" if field_value == 'product_model' else goods_nm,
                            "model_code": model_code,
                            "release_date": release_date
                        })
                df_nm = pd.DataFrame(nm_list)
                if df_nm.empty:
                    continue
                # __log.debug(df_nm)
                if date_list and date_len and date_format:
                    date_len_flag = len(df_nm)
                    df_nm['release_date'] = df_nm['release_date'].apply(lambda x: x.strftime(date_format) if x is not None else x)
                    df_nm['release_date'] = df_nm['release_date'].fillna('1000-01-01')
                    if not recent_key:
                        df_nm = df_nm[df_nm['release_date'].isin(date_list)]
                    elif recent_key:
                        df_nm_fy = df_nm[df_nm['release_date'].isin(date_list)].copy()
                        if df_nm_fy.empty:
                            additional_date_list = cm_utils.create_date_sequence_excluding_base(date_list[0], '3Y')
                            date_list = additional_date_list + date_list
                            df_nm_fy = df_nm[df_nm['release_date'].isin(date_list)].copy()
                        df_nm = df_nm_fy
                    if date_len_flag > 0 and len(df_nm) == 0  and not recent_key:
                        not_in_date.append(cmp.get('expression'))
                df_nm = attach_ctg(df_nm, country_code, site_cd)
                nm_processed = (
                        df_nm
                        .drop_duplicates()
                        .assign(min_id = lambda x: x.groupby(["mapping_code", "category_lv1", "category_lv2", "category_lv3"])['id'].transform('min'))
                        .groupby(["mapping_code", "category_lv1", "category_lv2", "category_lv3", "edge", "meta", "min_id"])["model_code"]
                        .agg(list)
                        .reset_index()
                        .sort_values(['min_id'], ascending=True) 
                        .rename(columns = {'model_code': 'extended_info'})
                    )
                # nm_processed = (
                #         df_nm
                #         .drop_duplicates()
                #         .pipe(lambda x: x.assign(release_date = x['release_date'].fillna('1000-01-01').astype(str)))
                #         .assign(latest_release_date = lambda x: x.groupby(["mapping_code", "category_lv1", "category_lv2", "category_lv3"])['release_date'].transform('max'))
                #         .groupby(["mapping_code", "category_lv1", "category_lv2", "category_lv3", "edge", "meta", "latest_release_date"])["model_code"]
                #         .agg(list)
                #         .reset_index()
                #         .sort_values(by = ['latest_release_date', 'mapping_code'], ascending=[False, False])
                #         .rename(columns = {'model_code': 'extended_info'})
                #     )
                
                # HC4
                # 갤럭시 워치 울트라는 2024제품과 2025제품을 구분할 수 있는 수단이 model_code 뿐 이므로, 우선순위 상 2025 제품을 먼저 표출하기 위해 별도 리스트 사용(답변정책)
                if not nm_processed.empty and '갤럭시 워치 울트라' in nm_processed['mapping_code'].tolist():
                            watch_order = ['SM-L705NZB1KOO', 'SM-L705NZA1KOO', 'SM-L705NAW1KOO', 'SM-L705NZS1KOO', 'SM-L705NDAAKOO', 'SM-L705NZWAKOO', 'SM-L705NZTAKOO']
                            target_mask = nm_processed['mapping_code'] == '갤럭시 워치 울트라'
                            target_indices = nm_processed[target_mask].index.tolist()
                            for idx in target_indices:
                                current_list = nm_processed.loc[idx, 'extended_info']
                                reordered_list = []
                                for item in watch_order:
                                    if item in current_list:
                                        reordered_list.append(item)
                                for item in current_list:
                                    if item not in watch_order:
                                        reordered_list.append(item)
                                nm_processed.loc[idx, 'extended_info'] = reordered_list
                result_list.append(nm_processed)
            elif 'c2c' not in cmp.get("type", "") and 'e2e' not in cmp.get("type", "") and 's2s' not in cmp.get("type", ""):
                # print("************")
                # print(query_2)
                if len(function_list) > 0:
                    curs.execute(query_2)
                else:
                    curs.execute(query_2)
                result_hnm = curs.fetchall()
                if not result_hnm:
                    pass 
                else:
                    hnm_list = []
                    for row in result_hnm:
                        category_lv1, category_lv2, category_lv3, model_code, goods_nm, release_date = row
                        product_filter_check = True
                        # __log.debug(f"l4_product_filter: {l4_product_filter}")
                        if country_code == 'KR':
                            is_merchandising = category_lv1 == "MERCHANDISING"
                            is_refrigrator = category_lv1 == "냉장고"
                            is_mobile = category_lv1 == "HHP"
                            is_printer = category_lv3 == "Printer"
                            is_external = (category_lv3 == "External HDD") or (category_lv3 == "External SSD")
                            is_airdresser = category_lv3 in ["Bespoke AirDresser", "AirDresser"]
                            is_serif = category_lv3 == "The Serif"
                            if l4_product_filter and l4_expression:
                                for l4_single_pattern in l4_product_filter:
                                ############## 0611 yji insert #################
                                    if l4_single_pattern[0] =='[':
                                        list_ = ast.literal_eval(l4_single_pattern)
                                        if any(item in goods_nm.lower() for item in set(list_)):
                                            product_filter_check = product_filter_check and True
                                        else:
                                            product_filter_check = product_filter_check and False
                                    else:        
                                        product_filter_check = product_filter_check and bool(re.search(re.escape(l4_single_pattern), goods_nm, re.IGNORECASE))
                                #################################################
                            # negative_l4_product_filter insert 0611
                            if negative_l4_product_filter and l4_expression:
                                for negative_l4_single_pattern in negative_l4_product_filter:
                                    product_filter_check = product_filter_check and not bool(re.search(re.escape(negative_l4_single_pattern), goods_nm, re.IGNORECASE))
      
                            expression = clean_expression_kr(goods_nm, is_merchandising, is_refrigrator, is_mobile, is_printer, is_external, is_airdresser, is_serif)
                            # __log.debug(expression)
                            # expression = expression if expression != '갤럭시 S25 울트라' else '갤럭시 S25 Ultra'
                        elif country_code == 'GB':
                            is_ha = category_lv1 == "Home Appliances"
                            is_mobile = category_lv1 == "Mobile"
                            is_printer = category_lv3 == "Printer"
                            is_external = (category_lv3 == "External HDD") or (category_lv3 == "External SSD")
                            is_computer = category_lv1 == 'Computers'
                            if l4_product_filter and l4_expression:
                                for l4_single_pattern in l4_product_filter:
                                ############## 0611 yji insert #################
                                    if l4_single_pattern[0] =='[':
                                        list_ = ast.literal_eval(l4_single_pattern)
                                        if any(item in goods_nm.lower() for item in set(list_)):
                                            product_filter_check = product_filter_check and True
                                        else:
                                            product_filter_check = product_filter_check and False
                                    else:        
                                        product_filter_check = product_filter_check and bool(re.search(re.escape(l4_single_pattern), goods_nm, re.IGNORECASE))
                                #################################################
                            # negative_l4_product_filter insert 0611
                            if negative_l4_product_filter and l4_expression:
                                for negative_l4_single_pattern in negative_l4_product_filter:
                                    product_filter_check = product_filter_check and not bool(re.search(re.escape(negative_l4_single_pattern), goods_nm, re.IGNORECASE))
                            
                            expression = clean_expression_uk(goods_nm, model_code, is_ha, is_mobile, is_printer, is_external, is_computer)
                            # __log.debug(f"{goods_nm}: {product_filter_check}")
                            # __log.debug(expression)

                        if product_filter_check:
                            hnm_list.append({
                                "country_code": country_code,
                                "mapping_code": expression,
                                "goods_nm": goods_nm,
                                "category_lv1": category_lv1,
                                "category_lv2": category_lv2,
                                "category_lv3": category_lv3,
                                "edge": "recommend",
                                "meta": "",
                                "model_code": model_code,
                                "release_date": release_date
                            })
                    df_hnm = pd.DataFrame(hnm_list)
                    if df_hnm.empty:
                        continue

                    # HC3
                    tss_key = df_hnm['goods_nm'].str.contains('통신사폰', na = False).any()
                    jyc_key = df_hnm['goods_nm'].str.contains('전용컬러', na = False).any()
                    spc_key = df_hnm['goods_nm'].str.contains('스페셜 컬러', na = False).any()
                    jgp_key = df_hnm['goods_nm'].str.contains('인증중고폰', na = False).any()
                    # __log.debug(f"jgp_key: {jgp_key}")
                    if tss_key:
                        df_hnm1 = df_hnm[~df_hnm['goods_nm'].str.contains('통신사폰', na = False)]
                        df_hnm2 = df_hnm[df_hnm['goods_nm'].str.contains('통신사폰', na = False)]
                        df_hnm = pd.concat([df_hnm1, df_hnm2], ignore_index=True)
                    if jyc_key:
                        df_hnm1 = df_hnm[~df_hnm['goods_nm'].str.contains('전용컬러', na = False)]
                        df_hnm2 = df_hnm[df_hnm['goods_nm'].str.contains('전용컬러', na = False)]
                        df_hnm = pd.concat([df_hnm1, df_hnm2], ignore_index=True)
                    if spc_key:
                        df_hnm1 = df_hnm[~df_hnm['goods_nm'].str.contains('스페셜 컬러', na = False)]
                        df_hnm2 = df_hnm[df_hnm['goods_nm'].str.contains('스페셜 컬러', na = False)]
                        df_hnm = pd.concat([df_hnm1, df_hnm2], ignore_index=True)
                    if jgp_key:
                        df_hnm1 = df_hnm[~df_hnm['goods_nm'].str.contains('인증중고폰', na = False)]
                        df_hnm2 = df_hnm[df_hnm['goods_nm'].str.contains('인증중고폰', na = False)]
                        df_hnm = pd.concat([df_hnm1, df_hnm2], ignore_index=True)
                    df_hnm = df_hnm.drop('goods_nm', axis = 1)
                    # 06.04 deleted by hsm
                    # if test_key:
                    #     df_hnm = df_hnm.loc[df_hnm['mapping_code'].str.lower().isin([s.lower() for s in mapping_code])]
                    if date_list and date_len and date_format:
                        date_len_flag = len(df_hnm)
                        df_hnm['release_date'] = df_hnm['release_date'].apply(lambda x: x.strftime(date_format) if x is not None else x)
                        df_hnm['release_date'] = df_hnm['release_date'].fillna('1000-01-01')
                        if not recent_key:
                            df_hnm = df_hnm[df_hnm['release_date'].isin(date_list)]
                        elif recent_key:
                            df_hnm_fy = df_hnm[df_hnm['release_date'].isin(date_list)].copy()
                            if df_hnm_fy.empty:
                                additional_date_list = cm_utils.create_date_sequence_excluding_base(date_list[0], '3Y')
                                date_list = additional_date_list + date_list
                                df_hnm_fy = df_hnm[df_hnm['release_date'].isin(date_list)].copy()
                            df_hnm = df_hnm_fy
                        if date_len_flag > 0 and len(df_hnm) == 0 and not recent_key:
                            not_in_date.append(cmp.get('expression'))
                    # __log.debug(df_hnm)
                    if df_hnm.empty:
                        continue
                    df_hnm = attach_ctg(df_hnm, country_code, site_cd)
                    hnm_processed = (
                        df_hnm
                        .drop_duplicates()
                        .assign(min_id = lambda x: x.groupby(["mapping_code", "category_lv1", "category_lv2", "category_lv3"])['id'].transform('min'))
                        .groupby(["mapping_code", "category_lv1", "category_lv2", "category_lv3", "edge", "meta", "min_id"])["model_code"]
                        .agg(list)
                        .reset_index()
                        .sort_values(['min_id'], ascending=True) 
                        .rename(columns = {'model_code': 'extended_info'})
                    )
                    # hnm_processed = (
                    #     df_hnm
                    #     .drop_duplicates()
                    #     .pipe(lambda x: x.assign(release_date = x['release_date'].fillna('1000-01-01').astype(str)))
                    #     .assign(latest_release_date = lambda x: x.groupby(["mapping_code", "category_lv1", "category_lv2", "category_lv3"])['release_date'].transform('max'))
                    #     .groupby(["mapping_code", "category_lv1", "category_lv2", "category_lv3", "edge", "meta", "latest_release_date"])["model_code"]
                    #     .agg(list)
                    #     .reset_index()
                    #     .sort_values(by = ['latest_release_date', 'mapping_code'], ascending=[False, False])
                    #     .rename(columns = {'model_code': 'extended_info'})
                    # )
                    # __log.debug(hnm_processed)
                    if hnm_processed.empty:
                        pass
                    else:
                        # HC4 
                        if '갤럭시 워치 울트라' in hnm_processed['mapping_code'].tolist():
                            watch_order = ['SM-L705NZB1KOO', 'SM-L705NZA1KOO', 'SM-L705NAW1KOO', 'SM-L705NZS1KOO', 'SM-L705NDAAKOO', 'SM-L705NZWAKOO', 'SM-L705NZTAKOO']
                            target_mask = hnm_processed['mapping_code'] == '갤럭시 워치 울트라'
                            target_indices = hnm_processed[target_mask].index.tolist()
                            for idx in target_indices:
                                current_list = hnm_processed.loc[idx, 'extended_info']
                                reordered_list = []
                                for item in watch_order:
                                    if item in current_list:
                                        reordered_list.append(item)
                                for item in current_list:
                                    if item not in watch_order:
                                        reordered_list.append(item)
                                hnm_processed.at[idx, 'extended_info'] = reordered_list
                        result_list.append(hnm_processed)
    
    if result_list:
        result_dataframe = pd.concat(result_list, axis = 0).sort_values('min_id', ascending = True).reset_index(drop = True).drop('min_id', axis=1)
        # result_dataframe = pd.concat(result_list, axis = 0).sort_values('latest_release_date', ascending = False).reset_index(drop = True).drop('latest_release_date', axis=1)
        result_list = [result_dataframe]

    return result_list, not_in_date

def extended_info_set(full_extended_info, site_cd):
    set_df_list = []

    mdl_code_llist = [list(itertools.chain.from_iterable(df['extended_info'])) for df in full_extended_info]
    for mdl_code_list in mdl_code_llist:
        mdl_code_placeholders = ", ".join(
            "'" + _ + "'" for _ in mdl_code_list if 'NA' != _
        )
        query = f"""
    SELECT psm.id, psm.mdl_code, psm.goods_id, psm.goods_nm , psm.product_category_lv1, psm.product_category_lv2, psm.product_category_lv3
    FROM rubicon_data_product_set_mst psm
    where cstrt_mdl_code in ({mdl_code_placeholders})
    and site_cd = '{site_cd}'
    """
        

        with connection.cursor() as curs:
            curs.execute(query)
            results =curs.fetchall()
            if results:
                set_df = pd.DataFrame(results, columns=[c.name for c in curs.description])
                set_df_list.append(set_df)
    # __log.debug(set_df_list)
    if not set_df_list:
        return pd.DataFrame()
    full_set_df = pd.concat(set_df_list, ignore_index=True).groupby(['mdl_code', 'goods_id', 'goods_nm', 'product_category_lv1', 'product_category_lv2', 'product_category_lv3'])['id'].min().reset_index()
    common_set = reduce(
        lambda l, r: pd.merge(l, r, on = ['mdl_code', 'goods_id', 'goods_nm', 'product_category_lv1', 'product_category_lv2', 'product_category_lv3'], how = 'inner'),
        set_df_list
    )

    common_set_df = pd.merge(common_set[['mdl_code', 'goods_id', 'goods_nm', 'product_category_lv1', 'product_category_lv2', 'product_category_lv3']].drop_duplicates(),
                             full_set_df,
                             on = ['mdl_code', 'goods_id', 'goods_nm', 'product_category_lv1', 'product_category_lv2', 'product_category_lv3'],
                             how = 'inner').rename(columns = {
                                'product_category_lv1': 'category_lv1',
                                'product_category_lv2': 'category_lv2',
                                'product_category_lv3': 'category_lv3',
                                'goods_nm': 'mapping_code',
                             })
    
    common_set_df['meta'] = 'set'
    common_set_df['edge'] = 'set'

    common_set_df_processed = (
                        common_set_df
                        .drop_duplicates()
                        .assign(min_id = lambda x: x.groupby(["mapping_code", "category_lv1", "category_lv2", "category_lv3"])['id'].transform('min'))
                        .groupby(["mapping_code", "category_lv1", "category_lv2", "category_lv3", "edge", "meta", "min_id"])["mdl_code"]
                        .agg(list)
                        .reset_index()
                        .sort_values(['min_id'], ascending=True)
                        .drop('min_id', axis=1) 
                        .rename(columns = {'mdl_code': 'extended_info'})
                    )
    common_set_df_processed['id'] = common_set_df_processed.index
    
    return common_set_df_processed

def _to_hashable(value):
    if isinstance(value, dict):
        return tuple((k, _to_hashable(v)) for k, v in sorted(value.items()))
    elif isinstance(value, list):
        return tuple(_to_hashable(v) for v in value)
    else:
        return value

def clean_expression_kr(goods_nm, is_merchandising=False, is_refrigrator=False, is_mobile=False, is_printer=False, is_external=False, is_airdresser=False, is_serif=False):
    """
    정규표현식을 이용해 goods_nm을 정제하여 expression을 생성
    """
    # 연도 정보 제거 ('21년), ("21년"), ['21년'] 등의 괄호 포함 여부 상관없이 삭제
    goods_nm = re.sub(r"[\(\[\{\'\"\`\‘]*\d{2,4}년형[\)\]\}\'\"\`]*", "", goods_nm)
    goods_nm = re.sub(r"[\(\[\{\'\"\`\‘]*\d{2,4}년[\)\]\}\'\"\`]*", "", goods_nm)
    goods_nm = re.sub(r"^(202[0-9]|203[0-9])\s+", "", goods_nm.lstrip()) # 250829 yji : 앞에 오는 2020, 2021, 2022, 2023, 2024, 2025 제거
    # 괄호 내용 제거 (예: "(35.6 cm)", "[선매립]" 등)
    goods_nm = re.sub(r"\((?!Wi-Fi\)).*?\)", "", goods_nm)  # 소괄호 제거 but keep (Wi-Fi)
    goods_nm = re.sub(r"\[.*?\]", "", goods_nm)  # 대괄호 제거
    goods_nm = re.sub(r"\{.*?\}", "", goods_nm)  # 중괄호 제거


    # 프린터인 경우 숫자 ppm 이후 내용 모두 제거
    if is_printer:
        goods_nm = re.sub(r"\s*\d+(?:\s*/\s*\d+)?\s*ppm.*$", "", goods_nm, flags=re.IGNORECASE)

    if is_external:
        goods_nm = re.sub(r"\s*\d+(?:\s*/\s*\d+)?\s*TB.*$", "", goods_nm, flags=re.IGNORECASE)

    # 숫자와 특정 단위(㎡, ppm, 매 등) 제거 (예: 3.5L → 삭제)
    if 'Snapdragon' in goods_nm or 'Core' in goods_nm or is_mobile:
        goods_nm = re.sub(r"\b(?!5G)\d+(?:,\d{3})*(?:\.\d+)?(?:/\d+)?\s*(L|ml|g|kg|개|EA|매|ppm|㎡|실|W)\b", "", goods_nm, flags=re.IGNORECASE)
    else:
        goods_nm = re.sub(r"\b\d+(?:,\d{3})*(?:\.\d+)?(?:/\d+)?\s*(L|ml|g|kg|개|EA|매|ppm|㎡|실|W)\b", "", goods_nm, flags=re.IGNORECASE)

    # `cm`, `mm`, `"`, `″` 제거 
    # yji edit to address decimals
    goods_nm = re.sub(r"\b\d+(?:\.\d+)?\s*(cm|mm|″|\"|‟)\b", "", goods_nm)

    # `㎡`와 붙어 있는 숫자 제거
    goods_nm = re.sub(r"\d+(\.\d+)?\s*\/\s*\d+(\.\d+)?\s*㎡", "", goods_nm)  # 예: 10.0/10.0㎡, 16.9/13.2㎡
    goods_nm = re.sub(r"\d+(\.\d+)?\s*㎡", "", goods_nm)  # 예: 10.0㎡, 16.9㎡

    # `W`가 붙은 숫자 제거 (예: 301W → 삭제)
    goods_nm = re.sub(r"\b\d+W\b", "", goods_nm)
    # yji kW 가 붙은 숫자도 제거
    goods_nm = re.sub(r"\b\d+kW\b", "", goods_nm)


    #  HTML 태그 제거 (<br> 등)
    goods_nm = re.sub(r"<br\s*/?>", " ", goods_nm, flags=re.IGNORECASE)

    # "/"와 "," 이후 내용 제거 (MERCHANDISING, 냉장고면 유지)
    if not is_merchandising and not is_refrigrator:
        goods_nm = re.split(r"[,/]", goods_nm)[0]
    # "통신사폰", "자급제" 제거 (HHP인 경우에만)
    if is_mobile:
        goods_nm = re.sub(r"\s*(통신사폰|자급제|사업자향|톰브라운 에디션|레트로|메종 마르지엘라 에디션|인증중고폰).*$", "", goods_nm)
    # 에어드레서에서 일반용량, 대용량 뒤 내용 삭제
    if is_airdresser:
        match = re.match(r".*?(대용량|일반용량)", goods_nm)
        # 250829 yji
        if match:
            goods_nm = match.group()
    # 더 세리프 2024 뗌
    if is_serif:
        goods_nm = re.sub('2024', '', goods_nm)
    # yji
    if 'Snapdragon' in goods_nm or 'Core' in goods_nm or 'Pentium' in goods_nm:
        goods_nm = re.split("Snapdragon", goods_nm)[0]
        goods_nm = re.split("Core", goods_nm)[0]
        goods_nm = re.split("Pentium", goods_nm)[0]

    goods_nm = re.sub(r"\?", "", goods_nm)
    goods_nm = re.sub(r"\('", "", goods_nm)
    # 숫자만 남아 있으면 삭제
    goods_nm = re.sub(r"^\d+$", "", goods_nm)

    # 1공백 여러 개를 하나로 변경
    goods_nm = re.sub(r"\s+", " ", goods_nm)

    # 마지막에 남은 <를 제거
    goods_nm = re.sub(r"\<","", goods_nm)

    # yji + 기준 split 삭제
    # if not is_mobile:
    #     goods_nm = goods_nm.split('+')[0].strip()

    # 예외 케이스 처리(복합기18/4, 큐브 94)
    goods_nm = re.sub("복합기18","복합기", goods_nm)
    goods_nm = re.sub("프린터18","프린터", goods_nm)
    goods_nm = re.sub("큐브 94","큐브", goods_nm)
    goods_nm = re.sub("핏홈 62.6","핏홈", goods_nm)

    # yji 마지막에 남아있는 comma나 period 삭제
    goods_nm = goods_nm.rstrip(".,").strip()
    return goods_nm
            
def clean_expression_uk(goods_nm, mdl_code, is_ha=False, is_mobile=False, is_printer=False, is_external=False, is_computer=False):
    """
    정규표현식을 이용해 goods_nm을 정제하여 expression을 생성
    """
    if goods_nm == 'Built-In Grill Microwave with Smart Humidity Sensor':
        return 'Built-In Grill Microwave with Smart Humidity Sensor'
    # 연도 정보 제거 ('21년), ("21년"), ['21년'] 등의 괄호 포함 여부 상관없이 삭제
    goods_nm = re.sub(r"[\(\[\{\'\"\`\‘]*\d{2,4}년[\)\]\}\'\"\`]*", "", goods_nm)

    # 괄호 내용 제거 (예: "(35.6 cm)", "[선매립]" 등)
    goods_nm = re.sub(r"\(.*?\)", "", goods_nm)  # 소괄호 제거
    goods_nm = re.sub(r"\[.*?\]", "", goods_nm)  # 대괄호 제거
    goods_nm = re.sub(r"\{.*?\}", "", goods_nm)  # 중괄호 제거

    # 프린터인 경우 숫자 ppm 이후 내용 모두 제거
    if is_printer:
        goods_nm = re.sub(r"\s*\d+(?:\s*/\s*\d+)?\s*ppm.*$", "", goods_nm, flags=re.IGNORECASE)

    if is_external:
        goods_nm = re.sub(r"\s*\d+(?:\s*/\s*\d+)?\s*TB.*$", "", goods_nm, flags=re.IGNORECASE)

    # 숫자와 특정 단위(㎡, ppm, 매 등) 제거 (예: 3.5L → 삭제)
    # goods_nm = re.sub(r"\b\d+(?:,\d{3})*(?:\.\d+)?(?:/\d+)?\s*(L|ml|g|kg|개|EA|매|ppm|㎡|실|W|inch|\”|\"|\u0022|\u201D|\u2033|\u201F)\b", "", goods_nm, flags=re.IGNORECASE)
    goods_nm = re.sub(r"\b\d+(?:\.\d+)?(\u0022|\u201D|\u2033|\u201F|L+)|\b\d+(?:,\d{3})*(?:\.\d+)?(?:/\d+)?\s*(L|L|ml|g|kg|개|EA|매|ppm|㎡|실|W|inch|GB|TB)\b", "", goods_nm, flags=re.IGNORECASE)
    # `cm`, `mm`, `"`, `″` 제거
    goods_nm = re.sub(r"\b\d+\s*(cm|mm|″|\"|‟)\b", "", goods_nm)

    # `㎡`와 붙어 있는 숫자 제거
    goods_nm = re.sub(r"\d+(\.\d+)?\s*\/\s*\d+(\.\d+)?\s*㎡", "", goods_nm)  # 예: 10.0/10.0㎡, 16.9/13.2㎡
    goods_nm = re.sub(r"\d+(\.\d+)?\s*㎡", "", goods_nm)  # 예: 10.0㎡, 16.9㎡

    # `W`가 붙은 숫자 제거 (예: 301W → 삭제)
    goods_nm = re.sub(r"\b\d+W\b", "", goods_nm)

    #  HTML 태그 제거 (<br> 등)
    goods_nm = re.sub(r"<br\s*/?>", " ", goods_nm, flags=re.IGNORECASE)

    # TM 태그 제거
    goods_nm = goods_nm.replace('™', '')

    # "-"로 분리 후 가장 마지막 부분만 제거
    # model code가 이름에 있는경우 제거
    # model code가 .../EU인데 /EU 없이 있는 경우 제거
    if is_ha:
        goods_nm = goods_nm.rsplit(' - ', 1)[0]
        goods_nm = re.sub(mdl_code, "", goods_nm)
        goods_nm = re.sub(re.sub("/EU|/U4|/U1|/S1", "", mdl_code), "", goods_nm)
        if mdl_code.endswith(("S1", "EU", "U4", "U1", "S1")):
            goods_nm = re.sub(mdl_code[:-2], "", goods_nm)
        goods_nm = re.sub('RS68CG883EB1|DV90BB9445GB', '', goods_nm)
    # 기타 수식어 제거 (Mobile인 경우에만)
    if is_mobile:
        goods_nm = re.sub(r"\s*(Bluetooth|BT Golf Edition|LTE|Enterprise Edition|Certified Re-Newed|Bora Purple|Graphite|White|2024).*$", "", goods_nm)
    # 기타 수식어 제거 (Computer인 경우에만)
    if is_computer:
        goods_nm = re.sub(r"\s*(LTE|Chrome OS|15.3|15.5|a Copilot\+ PC|2024).*$", "", goods_nm)
    
    if 'Hz' in goods_nm or 'hz' in goods_nm:
        goods_nm = re.sub(r'\s*\d+\s*(Hz|hz)\s*', ' ', goods_nm)
        goods_nm = re.sub(r'\s+', ' ', goods_nm)  # Clean up multiple spaces

    goods_nm = re.sub(r"\?", "", goods_nm)
    goods_nm = re.sub(r"\('", "", goods_nm)
    # 숫자만 남아 있으면 삭제
    goods_nm = re.sub(r"^\d+$", "", goods_nm)

    # 1공백 여러 개를 하나로 변경
    goods_nm = re.sub(r"\s+", " ", goods_nm)

    # 마지막에 남은 <를 제거
    goods_nm = re.sub(r"\<","", goods_nm)

    # 예외 케이스 처리(복합기18/4, 큐브 94)
    goods_nm = re.sub("복합기18","복합기", goods_nm)
    goods_nm = re.sub("프린터18","프린터", goods_nm)
    goods_nm = re.sub("큐브 94","큐브", goods_nm)
    goods_nm = re.sub("핏홈 62.6","핏홈", goods_nm)

    # with ... 기능 제거
    goods_nm = goods_nm.rsplit('with ', 1)[0].strip()
    goods_nm = goods_nm.rsplit('With', 1)[0]

    # 제일 마지막에 붙은 ",", "." 제거
    goods_nm = goods_nm.strip()
    goods_nm = goods_nm.rstrip(',')
    
    if goods_nm.strip() == 'Galaxy Chromebook 2 360':
        goods_nm = 'Galaxy Chromebook 2'

    return goods_nm.strip()    

def convert_price(price):
    amount_mapping = {
        "천만원": 10000000,
        "백만원": 1000000,
        "십만원": 100000,
        "만원": 10000,
        "만": 10000,
        "천원": 1000,
        "백원": 100,
        "원": 1,
    }
    match = re.match(r"(\d+)\s*(만원|천원|백원|원|만|십만원|백만원)?", price)
    if match:
        amount = int(match.group(1))
        unit = match.group(2)
        multiplier = amount_mapping.get(unit, 1)
        return amount * multiplier
    return 0

def kr_to_number(text):
    text = text.replace("₩","")
    num_dict = {
        "일": 1,
        "이": 2,
        "삼": 3,
        "사": 4,
        "오": 5,
        "육": 6,
        "칠": 7,
        "팔": 8,
        "구": 9,
        "영": 0,
    }
    unit_dict = {"십": 10, "백": 100, "천": 1000, "만": 10000, "억": 100000000}

    split_pattern = r"(억|만)"
    parts = re.split(f"({split_pattern})", text)
    result = 0
    temp = 0
    for part in parts:
        if not part:
            continue

        if part in unit_dict and unit_dict[part] >= 10000:
            result += temp * unit_dict[part]
            temp = 0
        else:
            num = 0
            unit = 1
            for char in part:
                if char in num_dict:
                    num = num_dict[char]
                elif char in unit_dict:
                    unit = unit_dict[char]
                    if num == 0:
                        num = 1
                    temp += num * unit
                    num = 0
            temp += num
    result += temp

    return result


def uk_to_number(text):
    try:
        text = text.replace("£","")
        answer = w2n.word_to_num(text)
    except Exception as e:
        answer = 0
    return answer

def get_new_operator(ner_price_opreator, country_code):
    new_operator_dict = {}

    for items in ner_price_opreator:
        actual_values = []
        price_standard = [
            word
            for word in items["expression"].replace(" ", "").split()
            if any(char.isdigit() for char in word)
        ]
        actual_values = sorted(
            [
                convert_price(price)
                for price in price_standard
                if convert_price(price) > 0
            ]
        )
        if not actual_values and country_code == "KR":
            actual_values = sorted(
                [
                    kr_to_number(word["expression"])
                    for word in [items]
                    if kr_to_number(word["expression"]) > 0
                ]
            )

        if not actual_values and country_code == "GB":
            actual_values = sorted(
                [
                    uk_to_number(word["expression"])
                    for word in [items]
                    if uk_to_number(word["expression"]) > 0
                ]
            )

        if items["operator"] in new_operator_dict:
            new_operator_dict[items["operator"]].extend(actual_values)

        else:
            new_operator_dict[items["operator"]] = actual_values


    return new_operator_dict

if __name__=="__main__":
    django.setup()
    # expr = "블루스카이 3100"
    # expr = "갤럭시 S23"
    # expr = "AI 업스케일링"
    
    ner = [{'expression': '갤럭시 워치 클래식', 'field': 'product_model', 'operator': 'in'}, {'expression': '추천', 'field': 'product_recommend', 'operator': 'in'}]
    cm = [                                                                                                                                                                       
                   {                                                                                                                                                                                   
                       'expression': '갤럭시 워치 클래식',                                                                                                                                             
                       'field': 'product_model',                                                                                                                                                       
                       'mapping_code': ['갤럭시 워치'],                                                                                                                                                
                       'type': ['p2p'],                                                                                                                                                                
                       'category_lv1': ['HHP'],                                                                                                                                                        
                       'category_lv2': ['WEARABLE DEVICE VOICE'],                                                                                                                                      
                       'category_lv3': ['NA'],                                                                                                                                                         
                       'original_expression': '갤럭시 워치 클래식'                                                                                                                                     
                   }                                                                                                                                                                                   
               ]                                                                                                                                                                                    
    res = new_extended_info(cm, 'Product Recommendation', ner, "KR","test")
    __log.debug(res)

def attach_ctg(df, country_code, site_cd):
    recommend_table_nm = 'rubicon_data_product_recommend' if country_code == 'KR' else 'rubicon_data_uk_product_order'

    mdl_cd = df['model_code'].tolist()
    mdl_placeholder = ", ".join(
                            "'" + _ + "'" for _ in mdl_cd
                        )
    if country_code == 'KR':
        query = f"""
                SELECT 
                    product_category_lv1 as category_lv1,
                    product_category_lv2 as category_lv2,
                    product_category_lv3 as category_lv3,
                    mdl_code,
                    goods_nm,
                    id as ids,
                    release_date
                FROM
                (SELECT * ,row_number () over (partition by disp_clsf_nm, goods_id, sorting_type order by ctg_rank) as rk from {recommend_table_nm})
                WHERE site_cd = '{site_cd}'
                AND sorting_type = 'Recommend'
                AND mdl_code in ({mdl_placeholder})
                AND rk = 1
                order by disp_clsf_nm, ctg_rank
                """
    else:
        query = f"""
                SELECT DISTINCT
                    pf.category_lv1,
                    pf.category_lv2,
                    pf.category_lv3,
                    pr.representative_model as mdl_code,
                    pf.display_name as goods_nm,
                    -pr.sorting_no as ids,
                    pf.launch_date as release_date
                FROM
                {recommend_table_nm} pr
                inner join rubicon_data_uk_product_filter pf on pr.representative_model = pf.model_code and pr.site_cd = pf.site_cd
                WHERE pf.site_cd = '{site_cd}'
                AND pr.sort_type = 'recommended'
                AND pf.model_code in ({mdl_placeholder})
                order by -sorting_no
                """
        
    if not mdl_cd:
        df = df.sort_values(['release_date', 'mapping_code'], ascending=[False,False]).reset_index(drop=True)
        df['id'] = df.index + 1
        return df
    with connection.cursor() as curs:
        curs.execute(query)
        result = curs.fetchall()
        res_df = pd.DataFrame(result, columns=[c.name for c in curs.description])
        if res_df.empty:
            df = df.sort_values(['release_date', 'mapping_code'], ascending=[False,False]).reset_index(drop=True)
            df['id'] = df.index + 1
            return df
        else:
            if country_code == 'KR':
                res_df['mapping_code'] = res_df.apply(
                    lambda row: clean_expression_kr(
                        row['goods_nm'],
                        row['category_lv1'] == "MERCHANDISING",
                        row['category_lv1'] == "냉장고", 
                        row['category_lv1'] == "HHP",
                        row['category_lv3'] == "Printer",
                        (row['category_lv3'] == "External HDD") or (row['category_lv3'] == "External SSD"),
                        row['category_lv3'] in ["Bespoke AirDresser", "AirDresser"],
                        row['category_lv3'] == "The Serif"
                    ),
                    axis=1
                )
            else:
                res_df['mapping_code'] = res_df.apply(
                    lambda row: clean_expression_uk(
                        row['goods_nm'],
                        row['mdl_code'],
                        row['category_lv1'] == "Home Appliances",
                        row['category_lv1'] == "Mobile", 
                        row['category_lv3'] == "Printer",
                        (row['category_lv3'] == "External HDD") or (row['category_lv3'] == "External SSD"),
                        row['category_lv3'] == "Computers"
                    ),
                    axis=1
                )
            res_df = res_df[['mapping_code', 'ids']]
            res_df.columns = ['mapping_code', 'id']
            res_df = res_df.loc[res_df.groupby('mapping_code')['id'].idxmin()]
            
            ctg_df = pd.merge(df, res_df, on = 'mapping_code', how = 'left')
            ctg_df['id'] = ctg_df['id'].fillna(9999)

            if ctg_df.empty:
                df = df.sort_values(['release_date', 'mapping_code'], ascending=[False,False]).reset_index(drop=True)
                df['id'] = df.index + 1
                return df
            else:
                return ctg_df
    df = df.sort_values(['release_date', 'mapping_code'], ascending=[False,False]).reset_index(drop=True)
    df['id'] = df.index + 1
    return df