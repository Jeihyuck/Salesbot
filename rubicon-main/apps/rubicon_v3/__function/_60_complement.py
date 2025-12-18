from email import message
import time
import traceback
from sympy import product
from copy import deepcopy
from alpha import __log

import pandas as pd
from apps.rubicon_v3.__function import __redis as redis
from apps.rubicon_v3.__function import __utils as utils
from apps.rubicon_v3.__function import (
    _61_complement_code_mapping as complementation_code_mapping,
)
from apps.rubicon_v3.__function import _62_complement_code_mapping_utils as cm_utils
from apps.rubicon_v3.__function import (
    _63_complement_managed_response as managed_response_check,
)
from apps.rubicon_v3.__function import (
    _67_complement_review_manager as complement_review_manager
)
from apps.rubicon_v3.__function import (
    _64_complement_extended_info as extended_info_check,
)
from apps.rubicon_v3.__function import (
    _64_complement_extended_info_2 as extended_info_check_2,
)
from apps.rubicon_v3.__function import _68_complement_add_on as add_on
from apps.rubicon_v3.__function.definitions import intelligences, sub_intelligences
from apps.rubicon_v3.__function import _69_complement_event_manager as event_manager

redis_client = redis.RedisClient()

from pydantic import BaseModel

# HC1
# 라인업 관련 질의에서, managed response를 각 제품이 아닌 라인업에 대한 managed resoponse로 응답하기 위해 set과 매핑되는 list의 dictionary를 구성
# 예: S25와 S24 비교해줘

MANAGED_SERIES_MAP = {
    frozenset(['갤럭시 S25', '갤럭시 S25+', '갤럭시 S25 울트라', '갤럭시 S25 엣지']): ['갤럭시 S25 시리즈'],
    frozenset(['갤럭시 S24', '갤럭시 S24+', '갤럭시 S24 울트라']): ['갤럭시 S24 시리즈'],
    frozenset(['갤럭시 S23', '갤럭시 S23+', '갤럭시 S23 Ultra']): ['갤럭시 S23 시리즈'],
    frozenset(['갤럭시 S22', '갤럭시 S22+', '갤럭시 S22 울트라']): ['갤럭시 S22 시리즈'],
    frozenset(['갤럭시 S21', '갤럭시 S21+', '갤럭시 S21 울트라']): ['갤럭시 S21 시리즈'],
    frozenset(['Galaxy S25', 'Galaxy S25+', 'Galaxy S25 Ultra', 'Galaxy S25 Edge']): ['Galaxy S25 Series'],
    frozenset(['Galaxy S24', 'Galaxy S24+', 'Galaxy S24 Ultra']): ['Galaxy S24 Series'],
    frozenset(['Galaxy S23', 'Galaxy S23+', 'Galaxy S23 Ultra']): ['Galaxy S23 Series'],
    frozenset(['Galaxy S22', 'Galaxy S22+', 'Galaxy S22 Ultra']): ['Galaxy S22 Series'],
    frozenset(['Galaxy S21', 'Galaxy S21+', 'Galaxy S21 Ultra']): ['Galaxy S21 Series'],
}

MANAGED_SERIES_PROJECTION_MAP = {
    frozenset(['갤럭시 S25', '갤럭시 S25+', '갤럭시 S25 울트라', '갤럭시 S25 엣지']): ['갤럭시 S25'],
    frozenset(['갤럭시 S24', '갤럭시 S24+', '갤럭시 S24 울트라']): ['갤럭시 S24'],
    frozenset(['갤럭시 S23', '갤럭시 S23+', '갤럭시 S23 울트라']): ['갤럭시 S23'],
    frozenset(['갤럭시 S22', '갤럭시 S22+', '갤럭시 S22 울트라']): ['갤럭시 S22'],
    frozenset(['갤럭시 S21', '갤럭시 S21+', '갤럭시 S21 울트라']): ['갤럭시 S21'],
    frozenset(['Galaxy S25', 'Galaxy S25+', 'Galaxy S25 Ultra', 'Galaxy S25 Edge']): ['Galaxy S25'],
    frozenset(['Galaxy S24', 'Galaxy S24+', 'Galaxy S24 Ultra']): ['Galaxy S24'],
    frozenset(['Galaxy S23', 'Galaxy S23+', 'Galaxy S23 Ultra']): ['Galaxy S23'],
    frozenset(['Galaxy S22', 'Galaxy S22+', 'Galaxy S22 Ultra']): ['Galaxy S22'],
    frozenset(['Galaxy S21', 'Galaxy S21+', 'Galaxy S21 Ultra']): ['Galaxy S21'],
}

# 20250502 assistant 관련 부분 제거

# def _prep_ner_result(unstructured_ner_result, error_logs):
#     """unstructured_ner_result 전처리
#     - 필드가 "N/A"인 경우 제거

#     Args:
#         unstructured_ner_result (_type_): _description_
#         error_logs (_type_): _description_

#     Returns:
#         _type_: _description_
#     """
#     unstructured_ner_result = [
#         item for item in unstructured_ner_result if item["field"] != "N/A"
#     ]

#     if (
#         unstructured_ner_result == "NO_VALID_VIEW_FIELDS"
#     ):  # TODO: 유효한 조건인지 확인 필요
#         __log.debug("Error : No Valid View Fields")
#         error_logs.append("No Valid View Fields")

#     if len(unstructured_ner_result) == 0:
#         __log.debug("Error : No Valid NER Result")
#         error_logs.append("No Valid NER Result")

#     return unstructured_ner_result


def _code_mapping(
    top_query,
    intelligence,
    sub_intelligence,
    original_ner_result,
    unstructured_ner_result,
    assistant_result,
    date_list,
    country_code,
    site_cd,
    message_id,
    error_logs,
):
    complement_code_mapping_start_time = time.time()  # Record start time


    extended_temp = []
    code_mapping_temp = []
    managed_response_data = []
    compl_stop_key = False
    code_mapping_error_list = []
    l4_filter_list = []
    original_model_code_mapping = []
    err_spec = None
    about_operator_flag_list = []
    c2c_cm = []
    try:
        complement_code_mapping_result, top_query, original_ner_result, unstructured_ner_result, grouped_ner_result, code_mapping_error_list, l4_filter_list, original_model_code_mapping, err_spec, about_operator_flag_list, c2c_cm = (
            complementation_code_mapping.unstructured_code_mapping(
                top_query,
                original_ner_result,
                unstructured_ner_result,
                assistant_result, 
                date_list,
                intelligence,
                sub_intelligence,
                country_code,
                site_cd,
                message_id,
            )
        )
        if err_spec:
            error_logs.append(err_spec)
        elapsed_time = time.time() - complement_code_mapping_start_time
        __log.debug(f'complement: _code_mapping: unstructured_code_mapping: {round(elapsed_time, 4)}')
        complement_code_mapping_result = complement_code_mapping_result.get(
            "unstructured", []
        )
        # product_function
        for item in complement_code_mapping_result:
            if (
                item.get("field", "") == "product_model"
                and item.get("mapping_code", "") is None
            ):
                item["mapping_code"] = [item["original_expression"]]
                item["category_lv1"] = "NA"
                item["category_lv2"] = "NA"
                item["category_lv3"] = "NA"
                compl_stop_key = True

        # __log.debug(f"compl_stop_key: {compl_stop_key}")
        if compl_stop_key:
            detected_product = _detect_na_in_code_mapping(
                complement_code_mapping_result
            )

            question_complementation_results = {
                "completed": True,
                "top_query": top_query,
                "intelligence": intelligence,
                "ner": unstructured_ner_result,
                "code_mapping": complement_code_mapping_result,
                "extended_info_result": [],
                "assistant_result": assistant_result,
                "bing_inputs": [],
                "bing_image_inputs": [],
                "err_logs": ["Invalid product detected."],
                "unknown_product": detected_product,
                "should_correct": True,
                "managed_response": managed_response_data,
            }
            return question_complementation_results, None, None, None, None, None, None, None, None, None, None, [], []

        for item in complement_code_mapping_result:
            if (
                item.get("field", "") in ["product_option", "product_model"]
                and "misuse" in item.get("category_lv1", [])
                and "other company" in item.get("category_lv2", [])
            ):
                for a in item.keys():
                    item[a] = item[a] if isinstance(item[a], str) else item[a][0]
                item["mapping_code"] = (
                    [item["mapping_code"]]
                    if isinstance(item["mapping_code"], str)
                    else item["mapping_code"]
                )
                extended_temp.append(item)
            elif (
                item.get("field", "") == "product_option"
                and item.get("mapping_code", "") is None
            ):
                item["mapping_code"] = [item["original_expression"]]
                item["category_lv1"] = ""
                item["category_lv2"] = ""
                item["category_lv3"] = ""
                code_mapping_temp.append(item)
        ## Filter by "NA" in categories
        category_counts = [
            (
                idx,
                sum(
                    1
                    for cat in ["category_lv1", "category_lv2", "category_lv3"]
                    if item.get(cat)
                ),
            )
            for idx, item in enumerate(complement_code_mapping_result)
        ]
        # __log.debug(f"category_counts: {category_counts}")
        if len(category_counts) > 0:
            max_count = max(count for _, count in category_counts)
        else:
            max_count = 0

        removed_indices = [idx for idx, count in category_counts if count < max_count]

        complement_code_mapping_result = [
            item
            for idx, item in enumerate(complement_code_mapping_result)
            if idx not in removed_indices
        ]
    except Exception as e:
        complement_code_mapping_result = []
        grouped_ner_result = []
        max_count = 0
        error_logs.append(f"code mapping error: {traceback.format_exc()}")
        traceback.print_exc()
    return (
        None,
        complement_code_mapping_result,
        extended_temp,
        code_mapping_temp,
        top_query, 
        original_ner_result, 
        unstructured_ner_result,
        grouped_ner_result,
        code_mapping_error_list,
        l4_filter_list,
        original_model_code_mapping,
        about_operator_flag_list,
        c2c_cm
    )


def _extended_info(
    top_query,
    intelligence,
    sub_intelligence,
    query_analyzer,
    unstructured_ner_result,
    grouped_ner_list,
    mentioned_products,
    l4_filter_list,
    error_logs,
    country_code,
    site_cd,
    guid,
    channel,
    message_id,
    complement_code_mapping_result,
    date_list,
    lineup_flag
):
    expressions = []
    extended_result = []
    initial_full_extended_info = []
    extended_info_df = []
    extended_promotion_df = []
    purchasable_list = []
    not_in_date_list = []
    not_in_l4_list = []
    mentioned_stop_key = False
    if len(complement_code_mapping_result) == 0 or lineup_flag == True:
        pass
    else:
        top_query = _adjust_top_query_expression(
            top_query, complement_code_mapping_result
        )
        try:
            initial_full_extended_info, extended_info_ner, extended_info_df, extended_promotion_df, mentioned_stop_key, purchasable_list, not_in_date_list, not_in_l4_list = (
                extended_info_check_2.new_extended_info(
                    complement_code_mapping_result,
                    intelligence,
                    sub_intelligence,
                    query_analyzer,
                    unstructured_ner_result,
                    grouped_ner_list,
                    mentioned_products,
                    l4_filter_list,
                    country_code,
                    site_cd,
                    guid,
                    channel,
                    message_id,
                    date_list=date_list
                )
            )
            extended_result.extend(extended_info_ner)
        except Exception as e:
            error_logs.append(f"extended info check error: {traceback.format_exc()}")

    extended_result = list(filter(None, extended_result))

    return initial_full_extended_info, extended_result, extended_info_df, extended_promotion_df, top_query, mentioned_stop_key, purchasable_list, not_in_date_list, not_in_l4_list


def _to_hashable(value):
    if isinstance(value, dict):
        return tuple((k, _to_hashable(v)) for k, v in sorted(value.items()))
    elif isinstance(value, list):
        return tuple(_to_hashable(v) for v in value)
    else:
        return value


def complement(
    top_query,
    embedding,
    query_analyzer,
    intelligence,
    sub_intelligence,
    original_ner_result,
    unstructured_ner_result,
    assistant_result,
    date_list,
    country_code,
    guid,
    message_id,
    session_hash,
    data_expiry,
    channel="DEV Debug",
    mentioned_products=None,
    site_cd = 'B2C',
):
    if mentioned_products is None:
        mentioned_products = []
    error_logs = []
    about_operator_flag_list = []

    # ner 전처리
    # unstructured_ner_result = _prep_ner_result(unstructured_ner_result, error_logs)
    complement_start_time = time.time()  # Record start time
    
    if country_code == 'GB':
        original_ner_result, unstructured_ner_result = cm_utils.adjust_code_in_model(
            original_ner_result, unstructured_ner_result
        )

    original_ner_result, unstructured_ner_result = cm_utils.sort_ner_by_position(
        top_query, original_ner_result, unstructured_ner_result
    )
    elapsed_time = time.time() - complement_start_time
    # __log.debug(f'complement: cm_utils.sort_ner_by_position: {round(elapsed_time, 4)}')
    # __log.debug(f"assistant_result: {assistant_result}")
    # 61 unstructured code mapping
    # 62 unstructured product vailidity check
    (
        question_complementation_results,
        complement_code_mapping_result,
        extended_temp,
        code_mapping_temp,
        top_query,
        original_ner_result,
        unstructured_ner_result,
        grouped_ner_list,
        code_mapping_error_list,
        l4_filter_list,
        original_model_code_mapping,
        about_operator_flag_list,
        c2c_cm
    ) = _code_mapping(
        top_query,
        intelligence,
        sub_intelligence,
        original_ner_result,
        unstructured_ner_result,
        assistant_result,
        date_list,
        country_code,
        site_cd,
        message_id,
        error_logs,
    )
    if question_complementation_results:
        return question_complementation_results
    
    elapsed_time = time.time() - complement_start_time
    # __log.debug(f'complement: _code_mapping: {round(elapsed_time, 4)}')
    
    lineup_flag = False
    if sub_intelligence in [sub_intelligences.PRODUCT_LINEUP_COMPARISON, sub_intelligences.PRODUCT_LINEUP_DESCRIPTION, sub_intelligences.PRODUCT_LINEUP_RECOMMENDATION]:
        lineup_flag = True
    else:
        lineup_flag = False
    # if (intelligence in ['Product Comparison', 'Product Description'] and
    #     not any([any([d.get('field') in ['product_color', 'product_spec'] for d in l]) for l in grouped_ner_list]) and
    #     not any([d.get('field') == 'product_option' for d in complement_code_mapping_result]) and
    #     not any([d.get('option') is not None for d in complement_code_mapping_result]) and
    #     not (sub_intelligence in [sub_intelligences.SET_PRODUCT_RECOMMENDATION, sub_intelligences.SET_PRODUCT_DESCRIPTION, sub_intelligences.BUNDLE_DISCOUNT, sub_intelligences.PRODUCT_REVIEW] and country_code == 'KR')):
    #     if set(sum([d.get('mapping_code') for d in complement_code_mapping_result], [])).issubset(set(cm_utils.LINEUP_LIST)):
    #         if date_list:
    #             if all([all([len(s) == 4 for s in d.get('date_list')]) for d in date_list]):
    #                 lineup_flag = True
    #             else: lineup_flag = False
    #         else:
    #             lineup_flag = True
    #     # print("do not run extended")
    # else:
    #     pass
    #     # print("run extended")

    # __log.debug(lineup_flag)
    complement_code_mapping_result = complement_code_mapping_result + code_mapping_temp
    # __log.debug(f"complement_code_mapping_result: {complement_code_mapping_result}")
    initial_full_extended_info, extended_result, extended_price_df, extended_promotion_df, top_query, mentioned_stop_key, purchasable_list, not_in_date_list, not_in_l4_list = (
        _extended_info(
            top_query,
            intelligence,
            sub_intelligence,
            query_analyzer,
            unstructured_ner_result,
            grouped_ner_list,
            mentioned_products,
            l4_filter_list,
            error_logs,
            country_code,
            site_cd,
            guid,
            channel,
            message_id,
            complement_code_mapping_result,
            date_list,
            lineup_flag=False
        )
    )

    elapsed_time = time.time() - complement_start_time
    

    selected_code_mapping = (
        complement_code_mapping_result
    )

    extended_temp2 = []
    for d in extended_temp:
        de = deepcopy(d)
        if 'misuse' in d.get('category_lv1') and 'other company' in d.get('category_lv2') and isinstance(de.get('mapping_code'), list):
            if len(de.get('mapping_code')) > 0:
                de['mapping_code'] = de.get('mapping_code')[0]
        extended_temp2.append(de)
            


    selected_extended = (
        extended_result
        + extended_temp2
    )

    elapsed_time = time.time() - complement_start_time
    __log.debug(f'complement: selected_extended: {round(elapsed_time, 4)}')

    selected_price_df = (
        extended_price_df 
    )

    selected_promotion_df = (
        extended_promotion_df 
    )


    seen = set()
    filtered_selected_code_mapping = []

    for d in selected_code_mapping:
        items = _to_hashable(d)
        if items not in seen:
            seen.add(items)
            filtered_selected_code_mapping.append(d)

    extended_seen = set()
    filtered_selected_extended = []

    for d in selected_extended:
        items = _to_hashable(d)
        if items not in extended_seen:
            extended_seen.add(items)
            filtered_selected_extended.append(d)
    try:
        price_table = selected_price_df
    except Exception as e:
        price_table = ""

    ## 여기에 ordering 추가 
    
    try:
        promotion_table = selected_promotion_df
    except Exception as e:
        promotion_table = ""
    
    # managed_seen = set()
    managed_response_code_mapping = []
    if lineup_flag:
        managed_response_code_mapping = original_model_code_mapping
        # for d in original_model_code_mapping:
        #     items = _to_hashable(d)
        #     if items not in managed_seen:
        #         managed_seen.add(items)
        #         managed_response_code_mapping.append(d)
    else:
        for d in filtered_selected_extended:
            d2 = deepcopy(d)
            # __log.debug(d2)
            if country_code == 'KR':
                is_merchandising = d2.get('category_lv1') == "MERCHANDISING"
                is_refrigrator = d2.get('category_lv1') == "냉장고"
                is_mobile = d2.get('category_lv1') == "HHP"
                is_printer = d2.get('category_lv3') == "Printer"
                is_external = (d2.get('category_lv3') == "External HDD") or (d2.get('category_lv3') == "External SSD")
                is_airdresser = d2.get('category_lv3') in ["Bespoke AirDresser", "AirDresser"]
                is_serif = d2.get('category_lv3') == "The Serif"
                mc = d2.get('mapping_code') if isinstance(d2.get('mapping_code'), str) else d2.get('mapping_code')[0]
                d2['mapping_code'] = [extended_info_check_2.clean_expression_kr(mc, is_merchandising, is_refrigrator, is_mobile, is_printer, is_external, is_airdresser, is_serif)]
            else:
                is_ha = d2.get('category_lv1') == "Home Appliances"
                is_mobile = d2.get('category_lv1') == "Mobile"
                is_printer = d2.get('category_lv3') == "Printer"
                is_external = (d2.get('category_lv3') == "External HDD") or (d2.get('category_lv3') == "External SSD")
                is_computer = d2.get('category_lv1') == 'Computers'
                m_c = d2.get('extended_info')[0] if d2.get('extended_info') is not None else ''
                mc = d2.get('mapping_code') if isinstance(d2.get('mapping_code'), str) else d2.get('mapping_code')[0]
                d2['mapping_code'] = [extended_info_check_2.clean_expression_uk(mc, m_c, is_ha, is_mobile, is_printer, is_external, is_computer)]
            d2['field'] = 'product_model'
            managed_response_code_mapping.append(d2)
    # __log.debug(managed_response_code_mapping)
    if purchasable_list:
        for s in purchasable_list:
            purchasable_temp = [d for d in selected_code_mapping if d.get('expression') == s]
            if purchasable_temp:
                managed_response_code_mapping.extend(purchasable_temp)

    # __log.debug(f"code_mapping_error_list: {code_mapping_error_list}")
    # __log.debug(len(managed_response_code_mapping))
    # __log.debug(len(grouped_ner_list))
    
    managed_response_date_llist = []
    if len(grouped_ner_list) > 1 and len(managed_response_code_mapping) > 1:
        grouped_ner_list_temp = deepcopy(grouped_ner_list)
        for i in range(len(managed_response_code_mapping)):
            expression_mrcm = managed_response_code_mapping[i].get('expression')
            for j in range(len(grouped_ner_list_temp)):
                gnl_flag = expression_mrcm in [d.get('expression').title() for d in grouped_ner_list_temp[j]]
                if gnl_flag:
                    gnl_date_expression = [d.get('expression') for d in grouped_ner_list_temp[j] if d.get('field') == 'product_release_date']
                    if gnl_date_expression:
                        managed_response_date_llist.append(list(set(sum([d.get('date_list') for d in date_list if d.get('expression') in gnl_date_expression], []))))
                    else:
                        managed_response_date_llist.append([])
                    grouped_ner_list_temp.pop(j)
                    break
    elif len(grouped_ner_list) == 1 and len(managed_response_code_mapping) == 1:
        if date_list:
            managed_response_date_llist.append(sum([d.get('date_list') for d in date_list], []))
        else:
            managed_response_date_llist.append([])
    elif len(grouped_ner_list) == 1 and len(managed_response_code_mapping) > 1:
        if date_list:
            for _ in range(len(managed_response_code_mapping)):
                managed_response_date_llist.append(sum([d.get('date_list') for d in date_list], []))
        else:
            for _ in range(len(managed_response_code_mapping)):
                managed_response_date_llist.append([])
            
    # __log.debug(managed_response_code_mapping)
    # HC1
    managed_response_code_mapping_temp = []
    if intelligence in [intelligences.PRODUCT_COMPARISON] and len(managed_response_code_mapping) > 1 and filtered_selected_extended:
        if sub_intelligence in [sub_intelligences.PRODUCT_LINEUP_COMPARISON, sub_intelligences.PRODUCT_LINEUP_DESCRIPTION, sub_intelligences.PRODUCT_LINEUP_RECOMMENDATION]:
            for d in managed_response_code_mapping:
                d2 = deepcopy(d)
                e = d2.get('expression')
                mmc = d2.get('mapping_code')
                fe = [d.get('mapping_code') for d in filtered_selected_extended if d.get('expression') == e]
                if frozenset(fe) in MANAGED_SERIES_MAP.keys():
                    d2['mapping_code'] = MANAGED_SERIES_MAP[frozenset(fe)]
                if frozenset(mmc) in MANAGED_SERIES_PROJECTION_MAP.keys() and frozenset(fe) not in MANAGED_SERIES_MAP.keys():
                    d2['mapping_code'] = MANAGED_SERIES_PROJECTION_MAP[frozenset(mmc)]
                managed_response_code_mapping_temp.append(d2)
                managed_response_code_mapping = managed_response_code_mapping_temp
                # __log.debug(f"{e}: {fe}")
                # __log.debug(f"{e}: {d2}")
        else:
            pass
    # __log.debug(managed_response_date_llist)
    managed_response_data, managed_only = managed_response_check.managed_response_check(
        managed_response_code_mapping, managed_response_date_llist, country_code
    )
    
    
    managed_response_data = list(
        {create_managed_key(item): item for item in managed_response_data}.values()
    )
    managed_only = managed_only & (intelligence in ['Product Description', 'Product Comparison']) & (not any(set(['product_option', 'product_spec']) & set([d.get('field') for d in original_ner_result])))
    
    exception_response_data = []

    not_exist_format_kr_b2c = """!!Important!! 문의하신 {}(은/는) 삼성전자 홈페이지에서 판매하지 않는 모델입니다. 
Inform the customer that the {} they inquired about is not a model available for sale on the Samsung Electronics website."""

    not_exist_format_gb_b2c = """!!Important!! The {} you inquired about is not a model currently available for sale on the Samsung Electronics website. 
Inform the customer that the {} they inquired about is not a model available for sale on the Samsung Electronics website."""

    not_exist_format_kr_fn = """!!Important!! 문의하신 {}(은/는) 패밀리넷에서 판매하지 않는 모델입니다. 
Inform the customer that the {} they inquired about is not a model available for sale on FamilyNet website."""

    not_exist_format_gb_fn = """!!Important!! The {} you inquired about is not a model currently available for sale on FamilyNet website. 
Inform the customer that the {} they inquired about is not a model available for sale on FamilyNet website."""

    # managed response option/model insert 0619
#     not_exist_function_format_kr = """!!Important!! 해당 {}(을/를) 지원하는 {}(은/는) 없습니다. 
# Let the user know that model named {} with that {} specification does not exist."""

#     not_exist_function_format_gb = """!!Important!! {} with that {} specification does not exist. 
# Let the user know that model named {} with that {} specification does not exist."""

#     not_exist_spec_format_kr = """!!Important!! {}(은/는) 없습니다. 
# Let the user know that {} does not exist."""

#     not_exist_spec_format_gb = """!!Important!! {} does not exist. 
# Let the user know that {} does not exist."""
    ###

    not_in_sale_format_kr_b2c = """!!Important!! 문의하신 {}(은/는) 삼성전자 홈페이지에서 판매하지 않는 모델입니다. 
Inform the customer that the {} they inquired about is not a model available for sale on the Samsung Electronics website."""

    not_in_sale_format_gb_b2c = """!!Important!! The {} you inquired about is not a model currently available for sale on the Samsung Electronics website. 
Inform the customer that the {} they inquired about is not a model available for sale on the Samsung Electronics website."""

    not_in_sale_format_kr_fn = """!!Important!! 문의하신 {}(은/는) 패밀리넷에서 판매하지 않는 모델입니다. 
Inform the customer that the {} they inquired about is not a model available for sale on FamilyNet website."""

    not_in_sale_format_gb_fn = """!!Important!! The {} you inquired about is not a model currently available for sale on FamilyNet website. 
Inform the customer that the {} they inquired about is not a model available for sale on FamilyNet website."""

    not_in_date_format_kr = """!!Important!! {}에 출시한 {} 제품은 없습니다. 
Let the user know that model {} released on {} does not exist."""

    not_in_date_format_gb = """!!Important!! {} released on {} does not exist.
Let the user know that model {} released on {} does not exist."""

    if code_mapping_error_list:
        for d in code_mapping_error_list:
            if site_cd == 'B2C':
                managed_value = not_exist_format_kr_b2c.format(d.get('expression'), d.get('expression')) if country_code == 'KR' else not_exist_format_gb_b2c.format(d.get('expression'), d.get('expression'))
            else:
                managed_value = not_exist_format_kr_fn.format(d.get('expression'), d.get('expression')) if country_code == 'KR' else not_exist_format_gb_fn.format(d.get('expression'), d.get('expression'))
            
            exception_response_data.append(
                {
                    'mapping_code': d.get('expression'),
                    'managed_response': [managed_value],
                    'managed_response_json': [None]
                }
            )
    # __log.debug(f"not_in_l4_list: {not_in_l4_list}")
    # __log.debug(f"purchasable_list: {purchasable_list}")
    if not_in_l4_list and not not_in_date_list:
        for d in not_in_l4_list:
            # managed response option/model insert 0619
            group = [group for group in grouped_ner_list for i in range(len(group)) if group[i]['expression'] == d.get('expression')][0]
            option_value = [item['expression'] for item in group if item['field'] in ('product_option', 'product_spec')]

            if option_value:
                # managed_value = (not_exist_function_format_kr.format(', '.join(option_value),d.get('expression'), d.get('expression'), ', '.join(option_value)) if country_code == 'KR' else not_exist_function_format_gb.format(d.get('expression'), ', '.join(option_value), d.get('expression'), ', '.join(option_value)))
                # exception_response_data.append(
                #     {
                #         'mapping_code': d.get('expression'),
                #         'managed_response': [managed_value],
                #         'managed_response_json': [None]
                #     }
                # )
                continue
            ###
                
            else:
                if site_cd == 'B2C':
                    managed_value = not_exist_format_kr_b2c.format(d.get('expression'), d.get('expression')) if country_code == 'KR' else not_exist_format_gb_b2c.format(d.get('expression'), d.get('expression'))
                else:
                    managed_value = not_exist_format_kr_fn.format(d.get('expression'), d.get('expression')) if country_code == 'KR' else not_exist_format_gb_fn.format(d.get('expression'), d.get('expression'))
                
                exception_response_data.append(
                    {
                        'mapping_code': d.get('expression'),
                        'managed_response': [managed_value],
                        'managed_response_json': [None]
                    }
                )

    if purchasable_list: 
        for s in purchasable_list:
            if site_cd == 'B2C':
                managed_value = not_in_sale_format_kr_b2c.format(s, s) if country_code == 'KR' else not_in_sale_format_gb_b2c.format(s, s)
            else:
                managed_value = not_in_sale_format_kr_fn.format(s, s) if country_code == 'KR' else not_in_sale_format_gb_fn.format(s, s)
            exception_response_data.append(
                {
                    'mapping_code': s,
                    'managed_response': [managed_value],
                    'managed_response_json': [None]
                }
            )

    # __log.debug(f"not_in_date_list: {not_in_date_list}")
    if not_in_date_list:
        for d in not_in_date_list:
            managed_value = not_in_date_format_kr.format(', '.join(d.get('date_expression')), d.get('expression'), d.get('expression'), ', '.join(d.get('date_expression'))) if country_code == 'KR' else not_in_date_format_gb.format(d.get('expression'), ', '.join(d.get('date_expression')), d.get('expression'), ', '.join(d.get('date_expression')))
            exception_response_data.append(
                {
                    'mapping_code': d.get('expression'),
                    'managed_response': [managed_value],
                    'managed_response_json': [None]
                }
            )
    
    other_company_product_list = [d.get('expression') for d in filtered_selected_code_mapping if d.get('field') == 'product_model' and 'misuse' in d.get('category_lv1', []) and 'other company' in d.get('category_lv2', [])]
    other_company_product_format_kr = """!!Important!! 문의하신 {}(은/는) 삼성전자 홈페이지에서 판매하지 않는 모델입니다.
The customer mentioned the other company product. Inform the customer that as an AI from Samsung Electronics, you are unable to answer about {} they inquired."""
    other_company_product_format_gb = """!!Important!! The {} you inquired about is not a model currently available for sale on website. 
The customer mentioned the other company product. Inform the customer that as an AI from Samsung Electronics, you are unable to answer about {} they inquired."""
    if other_company_product_list:
        for s in other_company_product_list:
            managed_value = other_company_product_format_kr.format(s,s) if country_code == 'KR' else other_company_product_format_gb.format(s,s)
            exception_response_data.append(
                {
                    'mapping_code': d.get('expression'),
                    'managed_response': [managed_value],
                    'managed_response_json': [None]
                }
            )



    if mentioned_stop_key:
        exception_response_data = [{
                    'mapping_code': None,
                    'managed_response': ["!!Important!! 조건에 맞는 더 보여드릴 수 있는 제품이 삼성전자 홈페이지에서 판매되고 있지 않습니다. Inform the customer that there are no additional products that meet the given criteria available for sale on the Samsung Electronics website."],
                    'managed_response_json': [None]
                }]
    # bing inputs
    # bing_inputs, bing_image_inputs = _make_bing_inputs(
    #     top_query, intelligence, sub_intelligence, filtered_selected_extended
    # )

    # managed response option/model insert 0620
    # if not not_in_l4_list and not not_in_date_list and not purchasable_list and not filtered_selected_code_mapping:
    #     for i in range(len(grouped_ner_list)):
    #         if any(item['field'] == 'product_model' for item in grouped_ner_list[i]) and any(item['field'] == 'product_spec' for item in grouped_ner_list[i]):
    #             model_value = [item['expression'] for item in grouped_ner_list[i] if item['field'] in ('product_model', 'product_code')]
    #             option_value = [item['expression'] for item in grouped_ner_list[i] if item['field'] == 'product_spec']
    #             operators = [item['operator'] for item in grouped_ner_list[i] if item['field'] == 'product_spec']
                
    #             option_operator_str_ko = ""
    #             option_operator_str_eng = f"{model_value[0]}"
                
    #             for j in range(len(option_value)):
    #                 option_operator_str_ko += " " if option_operator_str_ko != "" else ""
    #                 option_operator_str_eng += " " if option_operator_str_eng != "" else ""
    #                 if operators[j] == 'greater_than':
    #                     option_operator_str_ko += f"{option_value[j]} 이상"
    #                     option_operator_str_eng += f"over {option_value[j]}"
    #                 if operators[j] == 'in':
    #                     option_operator_str_ko += f"{option_value[j]}"
    #                     option_operator_str_eng += f"that is {option_value[j]}"
    #                 if operators[j] == 'less_than':
    #                     option_operator_str_ko += f"{option_value[j]} 이하"
    #                     option_operator_str_eng += f"under {option_value[j]}"
    #             option_operator_str_ko += f" {model_value[0]}"

    #             managed_value = (not_exist_spec_format_kr.format(option_operator_str_ko, option_operator_str_eng) if country_code == 'KR' else (not_exist_spec_format_gb.format(option_operator_str_eng, option_operator_str_eng)))
    #             managed_response_data.append(
    #                 {
    #                     'mapping_code': model_value[0],
    #                     'managed_response': [managed_value],
    #                     'managed_response_json': [None]
    #                 }
    #             )
    ###

    detected_product = _detect_na_in_code_mapping(filtered_selected_code_mapping)
    
    # 
    try:
        sum_md = ''
        stat_md = ''
        category_md = ''
        sum_df = pd.DataFrame()
        stat_df = pd.DataFrame()
        category_df = pd.DataFrame()
        if intelligence == intelligences.PRODUCT_DESCRIPTION:
            if filtered_selected_extended:
                """extended_list = [
                    {"mapping_code": item["mapping_code"], "extended_info": item["extended_info"]}
                    for item in filtered_selected_extended
                ]"""
                reviewManager = complement_review_manager.ReviewManager(country_code, top_query, filtered_selected_extended, site_cd)
                sum_df, stat_df, category_df = reviewManager.get_review_sum_stat()
            if not sum_df.empty:
                sum_md = sum_df.to_markdown()
            if not stat_df.empty:
                stat_md = stat_df.to_markdown()
            if not category_df.empty:
                category_md = category_df.to_markdown()
    except Exception as e:
        sum_md = ''
        stat_md = ''
        category_md = ''
    
    # add_on
    
    add_on_table = []
    if 'Accessories/Consumables' in query_analyzer.get('query_type',[]):
        try:
            add_on_table = add_on.add_on_check(unstructured_ner_result, filtered_selected_extended, country_code, site_cd)
        
        except Exception as e:
            add_on_table = [f'error:{e}']
    
    # event manager table
    if sub_intelligence == sub_intelligences.EVENT_PROMOTION:
        try:
            promotion_extended, promotion_table = event_manager.event_manager(embedding, initial_full_extended_info, country_code, site_cd)
            filtered_selected_extended = promotion_extended
            price_table = []
            managed_response_data = []
            managed_only = False
            if promotion_table.empty:
                if country_code == 'KR':
                    promotion_table = ['현재 관련된 프로모션이 없습니다.']
                else:
                    promotion_table = []
            else:
                promotion_table = [promotion_table.to_markdown()]
        except Exception as e:
            promotion_table = [f'error:{e}']

    about_operator_flag_list = [x for x in about_operator_flag_list if x is not None]
    
    if exception_response_data and filtered_selected_code_mapping and managed_response_data:
        emce = [d.get('mapping_code') for d in exception_response_data]
        mcm = sum([d.get('mapping_code') for d in filtered_selected_code_mapping if d.get('expression') in emce], [])
        mcme = [d.get('expression') for d in filtered_selected_code_mapping if set(mcm) == set(d.get('mapping_code'))]
        if set(emce) < set(mcme):
            pass
        else:
            managed_response_data = [d for d in managed_response_data if d.get('mapping_code') not in mcm]


    if exception_response_data and filtered_selected_code_mapping and managed_response_data:
        emce = [d.get('mapping_code') for d in exception_response_data]
        mcm = sum([d.get('mapping_code') for d in filtered_selected_code_mapping if d.get('expression') in emce], [])
        mcme = [d.get('expression') for d in filtered_selected_code_mapping if set(mcm) == set(d.get('mapping_code'))]
        if set(emce) < set(mcme):
            pass
        else:
            managed_response_data = [d for d in managed_response_data if d.get('mapping_code') not in mcm]

    # c2c인 경우 exception과 extended_info를 동시에 반환
    if c2c_cm and intelligence == 'Product Description':
        if filtered_selected_extended:
            c2c_ei = sum([d.get('extended_info') for d in filtered_selected_extended], [])
            c2c_mc = sum([d.get('mapping_code') for d in c2c_cm if not any(set(d.get('mapping_code')) & set(c2c_ei))], [])
            if c2c_mc:
                for d in c2c_cm:
                    if any(set(d.get('mapping_code')) & set(c2c_mc)):
                        temp_ei = cm_utils.get_model_code_extended(d, country_code, site_cd)
                        filtered_selected_extended.extend(temp_ei)
            else:
                pass
        else:
            for d in c2c_cm:
                temp_ei = cm_utils.get_model_code_extended(d, country_code, site_cd)
                filtered_selected_extended.extend(temp_ei)
    

    question_complementation_results = {
        "completed": True,  # if len(error_logs) == 0 else 1,
        "site_cd": site_cd,
        "top_query": top_query,
        "query_analyzer": query_analyzer,
        "intelligence": intelligence,
        "sub_intelligence": sub_intelligence,
        "ner": unstructured_ner_result,
        "code_mapping": filtered_selected_code_mapping,
        "initial_extended_info_result": initial_full_extended_info,
        "extended_info_result": filtered_selected_extended,
        "not_purchasable_list": purchasable_list,
        # "assistant_result": processed_assistant_result,
        "err_logs": error_logs,
        "about_operator_flag_list": about_operator_flag_list,
        "unknown_product": detected_product,
        "should_correct": False,
        "managed_response": managed_response_data,
        "exception_response_data": exception_response_data,
        "price_table": price_table,
        "promotion_table": promotion_table,
        "add_on_table": add_on_table,
        "mentioned_stop_key": mentioned_stop_key,
        "review_summary": sum_md,
        "review_statistics": stat_md,
        "review_category": category_md,
        "code_mapping_error_list": code_mapping_error_list,
        "l4_filter_list": l4_filter_list,
        "date_list": date_list,
        "managed_only": managed_only,
    }

    return question_complementation_results


def _adjust_top_query_expression(top_query, complementation_code_mapping_result):
    for item in complementation_code_mapping_result:
        # if (
        #     item.get("field", "") == "product_model"
        #     and item.get("category_lv2", ["NA"])[0] != "NA"
        # ):
        #     top_query = top_query.replace(item["expression"], item["mapping_code"][0] if isinstance(item["mapping_code"], list) else item["mapping_code"])
        if "misuse" == item.get("category_lv1", "") and "product_option" == item.get(
            "field", ""
        ):
            top_query = top_query.replace(
                item["original_expression"],
                (
                    item["mapping_code"][0]
                    if isinstance(item["mapping_code"], list)
                    else item["mapping_code"]
                ),
            )
        elif "misuse" == item.get("category_lv1", "") and "product_model" == item.get(
            "field", ""
        ):
            top_query = top_query.replace(item["original_expression"], "타사 제품")
        if (
            "option" in item
            and item["option"]["mapping_code"] is not None
            and item["option"]["expression"]
            and len(item["option"]["mapping_code"]) == 1
        ):
            top_query = top_query.replace(
                item["option"]["expression"][0], item["option"]["mapping_code"][0]
            )

    return top_query


def _detect_na_in_code_mapping(code_mapping_result):
    detected_list = []
    for item in code_mapping_result:
        category_lv1_check = "NA" in item.get("category_lv1", "")
        category_lv2_check = "NA" in item.get("category_lv2", "")
        category_lv3_check = "NA" in item.get("category_lv3", "")
        if category_lv1_check or category_lv2_check or category_lv3_check:
            detected_list.append(item.get("original_expression", ""))
    return detected_list


def adjust_ner_expression(top_query, unstructured_ner_result, code_mapping_list):
    new_unstructured_ner_result = []
    for item in code_mapping_list:
        if (
            item["field"] == "product" or item["field"] == "product_option"
        ) and item.get("product_category_lv1", ""):
            for ner_item in unstructured_ner_result:
                if item["original_expression"] == ner_item["expression"]:
                    ner_item["expression"] = item["expression"]
                    if "option" in item:
                        top_query = top_query.replace(
                            item["option"]["expression"],
                            item["option"]["mapping_code"][0],
                        )
                    # top_query.replace(ner_item['expression'], item['expression'])
                    new_unstructured_ner_result.append(ner_item)
                if item["product_category_lv1"][0] == "other company":
                    ner_item["expression"] = item["mapping_code"][0]
                    top_query = top_query.replace(
                        item["expression"], item["mapping_code"][0]
                    )
        elif item["field"] in ["product_option1", "product_option2", "product_color"]:
            pass
        else:
            for ner_item in unstructured_ner_result:
                new_unstructured_ner_result.append(ner_item)
    return top_query, new_unstructured_ner_result

def create_managed_key(item):
        mapping_code = item['mapping_code']
        date_list = item['date']
        
        if len(date_list) == 0 or date_list == ['']:
            date_part = ''
        elif len(date_list) == 1:
            date_part = date_list[0]
        else:
            date_part = f"{date_list[0]}to{date_list[-1]}"
        # __log.debug(f"{mapping_code}_{date_part}")
        return f"{mapping_code}_{date_part}"


if __name__ == "__main__":
    ...
