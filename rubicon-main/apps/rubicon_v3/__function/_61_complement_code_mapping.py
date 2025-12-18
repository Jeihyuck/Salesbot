import sys

sys.path.append("/www/alpha/")
import os
import django
import time

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "alpha.settings")

import pandas as pd
import re
from copy import deepcopy
from alpha import __log
from django.db import connection

from apps.rubicon_v3.models import Virtual_View_Field
from apps.rubicon_v3.__function import __embedding_rerank as embedding_rerank
from apps.rubicon_v3.__function import (
    _62_complement_code_mapping_utils as cm_utils
)
from apps.rubicon_v3.__function import (
    _62_complement_validation_kr as product_function_validation_kr,
)
from apps.rubicon_v3.__function import __utils as utils
from apps.rubicon_v3.__function.definitions import ner_fields, intelligences
from apps.rubicon_v3.__function.definitions.sub_intelligences import SET_PRODUCT_DESCRIPTION, SET_PRODUCT_RECOMMENDATION, BUNDLE_DISCOUNT



def find_index_with_model(grouped_ner_list, o_value):
    for i, inner_list in enumerate(grouped_ner_list):
        if isinstance(inner_list, list):
            for item in inner_list:
                if isinstance(item, dict) and 'expression' in item and item['expression'] == o_value:
                    return i
    return 0

def merge_lists(list1, list2):
    merged = []
    for item1 in list1:
        field1 = item1.get("field")
        mapping1 = item1.get("mapping_code") or []

        match = next((item2 for item2 in list2 if item2.get("field") == field1), None)
        if match:
            mapping2 = match.get("mapping_code") or []
            merged.append({"field": field1, "mapping_code": mapping1 + mapping2})
        else:
            merged.append(item1)

    fields_in_list1 = {item["field"] for item in list1}
    for item2 in list2:
        if item2["field"] not in fields_in_list1:
            mapping2 = item2.get("mapping_code") or []
            merged.append({"field": item2.get("field"), "mapping_code": mapping2})

    return merged

def extract_categories(code_mapping_list):
    """
    code_mapping_list에서 category_lv1, category_lv2, category_lv3 값을 추출하여 반환
    
    Args:
        code_mapping_list: 카테고리 정보가 포함된 딕셔너리 리스트
        
    Returns:
        tuple: (model_category_lv1, model_category_lv2, model_category_lv3) 형태의 튜플
    """
    model_category_lv1 = []
    model_category_lv2 = []
    model_category_lv3 = []
    
    for item in code_mapping_list:
        if 'category_lv1' in item:
            model_category_lv1.extend(item['category_lv1'])
        
        if 'category_lv2' in item:
            model_category_lv2.extend(item['category_lv2'])
        
        if 'category_lv3' in item:
            model_category_lv3.extend(item['category_lv3'])

    model_category_lv1 = list(set(model_category_lv1))
    model_category_lv2 = list(set(model_category_lv2))
    model_category_lv3 = list(set(model_category_lv3))
    
    return model_category_lv1, model_category_lv2, model_category_lv3
    

def code_retriever(
    expression,
    field,
    original_field,
    p_type,
    embedding,
    country_code,
    site_cd,
    message_id,
    model_category_lv1=None,
    model_category_lv2=None,
    model_category_lv3=None
):
    # AS/AVAS
    similarity_sql_misuse = ""
    # AS/AVAS
    model_category_lv1_placeholders = None
    model_category_lv2_placeholders = None
    model_category_lv3_placeholders = None
    if model_category_lv1:
        model_category_lv1_placeholders = ", ".join(
            "'" + _ + "'" for _ in model_category_lv1 if 'NA' != _
        )
    if model_category_lv2:
        model_category_lv2_placeholders = ", ".join(
            "'" + _ + "'" for _ in model_category_lv2 if 'NA' != _
        )
    if model_category_lv3:
        model_category_lv3_placeholders = ", ".join(
            "'" + _ + "'" for _ in model_category_lv3 if 'NA' != _
        )

    embedding = list(embedding)

    exact_not_sim = False

    # 20250605 inserted by YJI
    expression.replace('\\u0027', '\\u0022')
    exact_match_sql = f"""
        SELECT distinct rcm.mapping_code, rcm.field, rcm.expression, rcm.category_lv1, rcm.category_lv2, rcm.category_lv3, rcm.type, rcm.site_cd
        FROM rubicon_v3_complement_code_mapping rcm
        WHERE rcm.active = TRUE
        AND rcm.country_code = '{country_code}'
        AND rcm.field = '{field}'
        AND rcm.expression = '{expression}'
    """
    if p_type == 'function':
        exact_match_sql += "AND rcm.type in ('func', 'CPT')"
        exact_match_sql_misuse = exact_match_sql
    if model_category_lv1_placeholders and p_type == 'function':
        exact_match_sql += f"AND rcm.category_lv1 in ({model_category_lv1_placeholders})"
    if model_category_lv2_placeholders and p_type == 'function':
        exact_match_sql += f"AND rcm.category_lv2 in ({model_category_lv2_placeholders})"
    if model_category_lv3_placeholders and p_type == 'function':
        exact_match_sql += f"AND rcm.category_lv3 in ({model_category_lv3_placeholders})"

    # like_match_sql = f"""
    #     SELECT distinct rcm.mapping_code, rcm.field, rcm.expression, rcm.category_lv1, rcm.category_lv2, rcm.category_lv3, rcm.type, length(rcm.expression) as lex
    #     FROM rubicon_v3_complement_code_mapping rcm
    #     WHERE replace(rcm.expression, ' ', '') like '%{expression.replace(' ','')}%'
    #     AND rcm.country_code = '{country_code}'
    #     AND rcm.field = '{field}'
    #     AND rcm.type in ('p2p', 'h2h')
    #     AND rcm.active = TRUE
    #     ORDER BY length(rcm.expression) ASC
    #     LIMIT 1
    # """
    like_match_sql = f"""
        SELECT DISTINCT filtered_rcm.mapping_code, filtered_rcm.field, filtered_rcm.expression, filtered_rcm.category_lv1, filtered_rcm.category_lv2, filtered_rcm.category_lv3, filtered_rcm.type, LENGTH(filtered_rcm.expression) AS lex
        FROM (
            SELECT *
            FROM rubicon_v3_complement_code_mapping
            WHERE active = TRUE
            AND country_code = '{country_code}'
            AND field = '{field}'
            AND type IN ('p2p', 'h2h', 's2s', 'fs2fs')   
        ) filtered_rcm
        WHERE REPLACE(filtered_rcm.expression, ' ', '') LIKE '%{expression.replace(' ', '')}%'
        ORDER BY LENGTH(filtered_rcm.expression) ASC
        LIMIT 3
    """


    if p_type == 'product':
        similarity_sql = f"""SELECT DISTINCT
                                    rcm.mapping_code,
                                    rcm.field,
                                    rcm.expression,
                                    rcm.category_lv1,
                                    rcm.category_lv2,
                                    rcm.category_lv3,
                                    rcm.type,
                                    rcm.site_cd,
                                    subq.distance
                                FROM (
                                    SELECT DISTINCT
                                        expression,
                                        field,
                                        country_code,
                                        site_cd,
                                        embedding <=> '{str(embedding)}' AS distance
                                    FROM rubicon_v3_complement_code_mapping
                                    WHERE active = TRUE
                                    AND country_code = '{country_code}'
                                    AND field = '{field}'
                                    AND type != 'c2c'
                                    ORDER BY distance
                                    LIMIT 10
                                ) subq
                                JOIN rubicon_v3_complement_code_mapping rcm 
                                    ON rcm.expression = subq.expression
                                    AND rcm.active = TRUE
                                    AND rcm.site_cd = subq.site_cd
                                    AND rcm.country_code = subq.country_code
                                    AND rcm.field = subq.field
                                ORDER BY subq.distance"""
    elif p_type == "function":
        similarity_sql_misuse = f"""SELECT DISTINCT
                                rcm.mapping_code,
                                rcm.field,
                                rcm.expression,
                                rcm.category_lv1,
                                rcm.category_lv2,
                                rcm.category_lv3,
                                rcm.type,
                                rcm.site_cd,
                                subq.distance
                            FROM (
                                SELECT DISTINCT
                                    expression,
                                    field,
                                    country_code,
                                    site_cd,
                                    embedding <=> '{str(embedding)}' AS distance
                                FROM rubicon_v3_complement_code_mapping
                                WHERE active = TRUE
                                AND country_code = '{country_code}'
                                AND field = '{field}'
                                AND site_cd = '{site_cd}'
                                AND type = 'func'
                                ORDER BY distance
                                LIMIT 20
                            ) subq
                            JOIN rubicon_v3_complement_code_mapping rcm 
                                ON rcm.expression = subq.expression
                                AND rcm.active = TRUE
                                AND rcm.site_cd = subq.site_cd
                                AND rcm.field = subq.field
                                AND rcm.type = 'func'
                                AND rcm.country_code = subq.country_code
                            ORDER BY subq.distance
                            LIMIT 1
                                """

        similarity_sql = f"""SELECT DISTINCT
                                rcm.mapping_code,
                                rcm.field,
                                rcm.expression,
                                rcm.category_lv1,
                                rcm.category_lv2,
                                rcm.category_lv3,
                                rcm.type,
                                rcm.site_cd,
                                subq.distance
                            FROM (
                                SELECT DISTINCT
                                    expression,
                                    field,
                                    country_code,
                                    site_cd,
                                    embedding <=> '{str(embedding)}' AS distance
                                FROM rubicon_v3_complement_code_mapping
                                WHERE active = TRUE
                                AND country_code = '{country_code}'
                                AND field = '{field}'
                                AND site_cd = '{site_cd}'
                                AND type in ('func', 'CPT')
                                ORDER BY distance
                                LIMIT 20
                            ) subq
                            JOIN rubicon_v3_complement_code_mapping rcm 
                                ON rcm.expression = subq.expression
                                AND rcm.active = TRUE
                                AND rcm.site_cd = subq.site_cd
                                AND rcm.field = subq.field
                                AND rcm.type in ('func', 'CPT')
                                AND rcm.country_code = subq.country_code
                                """
        if model_category_lv1_placeholders:
            similarity_sql += f"AND rcm.category_lv1 in ({model_category_lv1_placeholders})"
        if model_category_lv2_placeholders:
            similarity_sql += f"AND rcm.category_lv2 in ({model_category_lv2_placeholders})"
        if model_category_lv3_placeholders:
            similarity_sql += f"AND rcm.category_lv3 in ({model_category_lv3_placeholders})"

        similarity_sql += f"""
                            ORDER BY subq.distance
                            LIMIT 20"""

    with connection.cursor() as curs:
        # Try exact match first
        if p_type == 'function':
            curs.execute(exact_match_sql_misuse)
            results = curs.fetchall()
            if results:
                misuse_df = pd.DataFrame(results, columns=[c.name for c in curs.description])
                if 'misuse' in misuse_df['category_lv1'].tolist():
                    return misuse_df, exact_not_sim

        curs.execute(exact_match_sql)
        results = curs.fetchall()

        # __log.debug(f"exact_match_sql result: {results}")

        # If exact match found, return it
        if results:
            result_df = pd.DataFrame(results, columns=[c.name for c in curs.description])
            result_df = result_df[result_df['site_cd'] == site_cd].drop('site_cd', axis = 1)
            exact_not_sim = True
            return result_df, exact_not_sim
        else:
            if original_field == 'product_code':
                return pd.DataFrame(columns=['mapping_code', 'field', 'expression', 'category_lv1', 'category_lv2', 'category_lv3', 'type']), exact_not_sim
        
        # Comment out like_match_sql for now
        # if p_type == 'product':
        #     curs.execute(like_match_sql)
        #     # __log.debug(like_match_sql)
        #     results = curs.fetchall()

        #     if results:
        #         like_df = pd.DataFrame(results, columns=[c.name for c in curs.description]).drop('lex', axis = 1)
        #         if 'p2p' in like_df['type'].tolist():
        #             like_df = like_df[like_df['type'] == 'p2p']
        #         return like_df
            # __log.debug(f"like_match_sql result: {results}")

        # If no exact match, try similarity search with reranking
        # curs.execute(similarity_sql, [embedding, country_code])
        if p_type == 'function':
            curs.execute(similarity_sql_misuse)
            results = curs.fetchall()
            if results:
                misuse_df = pd.DataFrame(results, columns=[c.name for c in curs.description])
                if 'misuse' == misuse_df['category_lv1'].iloc[0] and misuse_df['distance'].iloc[0] < 0.2:
                    # __log.debug(f"misuse_df: {misuse_df}")
                    misuse_df = misuse_df.drop('site_cd', axis = 1)
                    return misuse_df, exact_not_sim

        curs.execute(similarity_sql)
        results = curs.fetchall()
        

        df = pd.DataFrame(results, columns=[c.name for c in curs.description])
        # __log.debug(f"!! {expression}: {df}") 

        if not df.empty:
            df = df[df['site_cd'] == site_cd]
            if df.empty:
                return pd.DataFrame(columns=['mapping_code', 'field', 'expression', 'category_lv1', 'category_lv2', 'category_lv3', 'type']), exact_not_sim

            # Rerank based on expressions
            # TODO: p2p에서 가장 많은 항목을 가진 케이스로 업데이트 필요. (현: 갤럭시 S 시리즈, 18)
            df_reranked = embedding_rerank.rerank_db_results(
                expression, df, text_column="expression", top_k=18, score_threshold=1 # 재논UVC살균 지원하는 슈드레서 추천해줘. 질의 테스트 하려면 1.5로
            )
            # df_reranked = df_reranked_full[df_reranked_full['mapping_code'] == df_reranked_full.iloc[0]['mapping_code']]

            # Log or print the filtered DataFrame
            # __log.debug(f"Filtered DataFrame: {df_reranked}")

            # __log.debug(df_reranked.columns.tolist())
            # Return empty DataFrame if reranked results are empty
            if df_reranked.empty:
                return pd.DataFrame(columns=['mapping_code', 'field', 'expression', 'category_lv1', 'category_lv2', 'category_lv3', 'type']), exact_not_sim
            else:
                df_reranked = df_reranked.sort_values('reranker_score', ascending=False)
                # __log.debug(f"df_reranked: {df_reranked}") 
                if p_type == 'function':
                    if df_reranked['type'].iloc[0] == 'func':
                        df_reranked = df_reranked.loc[df_reranked['reranker_score'] == df_reranked['reranker_score'].max()]
                    else:
                        df_reranked = df_reranked
                else:
                    df_reranked = df_reranked.loc[df_reranked['reranker_score'] == df_reranked['reranker_score'].max()]
                # __log.debug(df_reranked)
                if expression.replace(' ', '') == '전체용량' and '대용량' in df_reranked['mapping_code'].tolist():
                    df_reranked = df_reranked[df_reranked['mapping_code'] != '대용량']
                df_reranked.loc[df_reranked['type'].isin(['s2s', 'fs2fs']), 'mapping_code'] = df_reranked.loc[df_reranked['type'].isin(['s2s', 'fs2fs']), 'mapping_code'].str.strip()
                # df_reranked['mapping_code'] = df_reranked['mapping_code'].str.strip()
                return df_reranked, exact_not_sim
            
        return pd.DataFrame(columns=['mapping_code', 'field', 'expression', 'category_lv1', 'category_lv2', 'category_lv3', 'type']), exact_not_sim
          # Return empty DataFrame if no results found from similarity search


def process_ner_item(
    item: dict,
    p_type: str,
    country_code,
    site_cd,
    message_id,
    model_category_lv1 = None,
    model_category_lv2 = None,
    model_category_lv3 = None
) -> list[dict[str, str]]:
    expression = item.get("expression")
    field = item.get("field")
    operator = item.get("operator")
    error_dict = {}
    error_key = field
    l4_filters = {
        'expression': expression,  
        'code_filter_str': None,
        'code_filter_int': None,
        'product_filter': []
    }



    if field == 'product_model' and country_code == 'GB':
        expression = expression.title()
    # __log.debug(f'expression: {expression}') 
    original_field = field
    field = 'product_model' if field == 'product_code' else field

    embedded_expression_value = embedding_rerank.baai_embedding(expression, message_id)
    embedded_expression_value = embedded_expression_value[0]
    
    df, exact_not_sim = code_retriever(
        expression=expression,
        model_category_lv1=model_category_lv1,
        model_category_lv2=model_category_lv2,
        model_category_lv3=model_category_lv3,
        field=field,
        original_field=original_field,
        p_type = p_type,
        embedding=embedded_expression_value,
        country_code=country_code,
        site_cd=site_cd,
        message_id=message_id,
    )
    
    # results = {}
    # print(df) 
    # Add the original field mapping
    if df.empty:
        if error_key == 'product_code':
            error_dict = {
                'expression': expression,
                'error_type': 'invalid model code'
            }
        elif error_key == 'product_model':
            error_dict = {
                'expression': expression,
                'error_type': 'invalid model name'
            }
        return None, error_dict, l4_filters
    else:
        mapping_code = (
                df["mapping_code"].dropna().drop_duplicates().tolist()
                if not df.empty
                else None
            )
        if mapping_code and p_type == 'function':
            operator = [operator] * len(mapping_code)
        results = {
            "expression": expression,
            "field": field,
            "operator": operator,
            "mapping_code": mapping_code,
            "type": df["type"]
        }

        # Add product categories only if all three levels have values
        if not df.empty:
            # Check if we have complete category information (all levels non-null)
            complete_categories = df[
                df["category_lv1"].notna()
                & df["category_lv2"].notna()
                & df["category_lv3"].notna()
            ]

            if not complete_categories.empty:
                # Take the first row with complete categories
                first_complete = complete_categories
                results["category_lv1"] = list(
                    set(complete_categories["category_lv1"].values.tolist())
                )
                results["category_lv2"] = list(
                    set(complete_categories["category_lv2"].values.tolist())
                )
                results["category_lv3"] = list(
                    set(complete_categories["category_lv3"].values.tolist())
                )
                results["type"] = list(
                    set(complete_categories["type"].values.tolist())
                )
        
        if error_key == 'product_model':
            l4_check, l4_filters = cm_utils.check_valid_product(expression, results, country_code)
            if exact_not_sim and l4_check == 'code filter failed':
                l4_check = None
                l4_filters['code_filter_str'] = []
                l4_filters['code_filter_int'] = []          
            if l4_check:
                results = None
                error_dict = {
                    'expression': expression,
                    'error_type': l4_check
                }

        return results, error_dict, l4_filters

def unstructured_code_mapping(
    rewrite_query, 
    original_ner_list, 
    ner_list: list, 
    assistant_result, 
    date_list, 
    intelligence, 
    sub_intelligence, 
    country_code, 
    site_cd, 
    message_id
) -> dict[str, list[dict[str, str]]]:
    code_mapping_target_fields = [
        ner_fields.PRODUCT_MODEL,
        ner_fields.PRODUCT_CODE,
        ner_fields.PRODUCT_OPTION,
        ner_fields.PRODUCT_SPEC,
        ner_fields.PRODUCT_COLOR,
        'product_release_date',
        'promotion_date',
        'product_price',
        'istm_prd',
        'cardc_cd',
        'extend_request',
        'product_accessory',
        'split_pay'
    ]

    model_code_mapping_target_fields = [
        ner_fields.PRODUCT_MODEL,
        ner_fields.PRODUCT_CODE,
    ]

    function_code_mapping_target_fields = [
        ner_fields.PRODUCT_OPTION,
    ]
    
    option_code_mapping_target_fields = [
        ner_fields.PRODUCT_SPEC,
        ner_fields.PRODUCT_COLOR,
        ner_fields.PRODUCT_OPTION,
    ]
    unstructured_code_mapping_start_time = time.time()  # Record start time

    code_mapping_results = []
    code_mapping_results_model = []
    code_mapping_results_function = []
    code_mapping_error_list = []
    l4_filter_list = []
    invalid_items = []
    invalid_groups = []
    ignore_list = []
    default_fn = []
    c2c_cm = []
    ignore_expression_set = None
    assistant_key = False
    err_spec_out = None
    about_operator_flag_list = []
    # __log.debug(f"original_ner_list: {original_ner_list}")
    # __log.debug(f"ner_list: {ner_list}")
    original_ner_list = [d for d in original_ner_list if d.get('field') in code_mapping_target_fields]
    ner_list = [d for d in ner_list if d.get('field') in code_mapping_target_fields]

    # 25/18 KG 증강 (S/G mixed)
    sgm_spec = [d.get('expression') for d in ner_list if d.get('field') == 'product_spec' and (bool(re.match(r'^\d{2}/\d{2} KG$', d.get('expression'))) or bool(re.match(r'^\d{2} KG/\d{2} KG$', d.get('expression'))))]
    sgm_target_index = []
    # __log.debug(sgm_spec)
    try:
        if sgm_spec:
            sgm_original_ner_list = []
            sgm_new_ner_list = []
            sgm_rewrite_flag = False
            for i in range(len(ner_list)):
                if ner_list[i].get('expression') in sgm_spec:
                    sgm_target_index.append(i)
            sgm_target_index.sort(reverse=True)
            for j in sgm_target_index:
                sgm_value = ner_list[j].get('expression')
                # __log.debug(sgm_value)
                sgm_match = re.match(r'^(\d{2})/(\d{2}) KG$', sgm_value)
                if not sgm_match:
                    sgm_match = re.match(r'^(\d{2}) KG/(\d{2}) KG$', sgm_value)
                if sgm_match:
                    sgm_temp1 = sgm_match.group(1) + ' KG'
                    sgm_temp2 = sgm_match.group(2) + ' KG'
                    sgm_ner_aug = [
                        {'expression': '세탁 용량', 'field': 'product_option', 'operator': 'in'},
                        {'expression': sgm_temp1, 'field': 'product_spec', 'operator': 'in'},
                        {'expression': '건조 용량', 'field': 'product_option', 'operator': 'in'},
                        {'expression': sgm_temp2, 'field': 'product_spec', 'operator': 'in'}
                    ]
                    sgm_query_aug = f"세탁 용량 {sgm_temp1} 건조 용량 {sgm_temp2}"
                    sgm_query_orig = original_ner_list[j].get('expression')

                    if sgm_original_ner_list:
                        sgm_original_ner_list = sgm_original_ner_list[:j] + sgm_ner_aug + sgm_original_ner_list[j+1:]
                    else:
                        sgm_original_ner_list = original_ner_list[:j] + sgm_ner_aug + original_ner_list[j+1:]
                    if sgm_new_ner_list:
                        sgm_new_ner_list = sgm_new_ner_list[:j] + sgm_ner_aug + sgm_new_ner_list[j+1:]
                    else:
                        sgm_new_ner_list = ner_list[:j] + sgm_ner_aug + ner_list[j+1:]
                    if not sgm_rewrite_flag:
                        sgm_rewrite_query = rewrite_query.replace(sgm_query_orig, sgm_query_aug)
                        sgm_rewrite_flag = True
                    else:
                        sgm_rewrite_query = sgm_rewrite_query.replace(sgm_query_orig, sgm_query_aug)
                    # __log.debug(sgm_original_ner_list)
                    # __log.debug(sgm_new_ner_list)
                    # __log.debug(sgm_rewrite_query)
            original_ner_list = sgm_original_ner_list
            ner_list = sgm_new_ner_list
            rewrite_query = sgm_rewrite_query
    except:
        pass
             
    
    assistant_product = assistant_result.get('product')
    # assistant_extracted = assistant_result.get('extracted')
    # assistant_extracted_index = []
    if assistant_product:
        assistant_key = all([len(d.get("assistant")) > 0 for d in assistant_product])
    # __log.debug(f"***************** {assistant_key}")
    # if assistant_key and assistant_extracted:
    #     extracted_expression = [d.get('expression') for d in assistant_extracted]
    #     for i in range(len(original_ner_list)):
    #         if original_ner_list[i].get('expression') in extracted_expression:
    #             assistant_extracted_index.append(i)
    
    #     original_ner_list = [original_ner_list[i] for i in assistant_extracted_index]
    #     ner_list = [ner_list[i] for i in assistant_extracted_index]
        
    if not original_ner_list:
        grouped_ner_list = [ner_list]
    else:
        if country_code == 'KR':
            grouped_ner_list = cm_utils.split_ner_by_conjunction(rewrite_query, original_ner_list, ner_list)
        else:
            grouped_ner_list = cm_utils.split_ner_by_conjunction(rewrite_query, original_ner_list, ner_list, conjunction_list=['와', '과', '랑', '의', 'and', 'or', ','])
    # __log.debug(f"grouped_ner_list: {grouped_ner_list}") 
    # elapsed_time = time.time() - unstructured_code_mapping_start_time
    # __log.debug(f'complement: _code_mapping: unstructured_code_mapping: grouped_ner_list: {round(elapsed_time, 4)}')

    if assistant_key:
        rewrite_query, original_ner_list, ner_list, grouped_ner_list = cm_utils.augment_query_and_ner(rewrite_query, original_ner_list, ner_list, grouped_ner_list, assistant_product)
        # print("augmented_query:", rewrite_query)
        # print("augmented_original_ner:", original_ner_list)
        # print("augmented_unstruct_ner:", ner_list)
        # print("증augmented_grouped:", grouped_ner_list)

    
    for item in ner_list:
        # __log.debug(f"item: {item}")
        if item["field"] in model_code_mapping_target_fields and item['expression']:
            result, error_dict, l4_filters = process_ner_item(item=item, 
                                      p_type='product',
                                      country_code=country_code,
                                      site_cd=site_cd, 
                                      message_id=message_id)
            # __log.debug(f"**** {result}")
            if result and 'IGNORE' in result.get('mapping_code'):
                ignore_list.append(result)
                continue
            if result is not None and 'spec' not in result.get("type", ""):
                code_mapping_results_model.append(result)
            if error_dict:
                code_mapping_error_list.append(error_dict)
                invalid_items.append(item['expression'])
            if l4_filters:
                l4_filter_list.append(l4_filters)
    # __log.debug(f"code_mapping_results: {code_mapping_results_model}") # 볼거
    if code_mapping_results_model:
        c2c_cm = [d for d in code_mapping_results_model if 'c2c' in d.get('type')]
    # __log.debug(ignore_list)
    if ignore_list:
        ignore_expression_set = set([d.get('expression') for d in ignore_list])
    if ignore_expression_set:
        for i in range(len(grouped_ner_list) -1, -1, -1):
            grouped_ignore_check = grouped_ner_list[i]
            if any(set([d.get('expression') for d in grouped_ignore_check]) & ignore_expression_set):
                grouped_ner_list.pop(i)
            # __log.debug(grouped_ignore_check)
    if ignore_expression_set:
        original_ner_list = [d for d in original_ner_list if d.get('expression') not in ignore_expression_set]
        ner_list = [d for d in ner_list if d.get('expression') not in ignore_expression_set]

    if sub_intelligence in [SET_PRODUCT_RECOMMENDATION, SET_PRODUCT_DESCRIPTION, BUNDLE_DISCOUNT]:
        original_ner_list, ner_list, grouped_ner_list, code_mapping_results_model = cm_utils.adjust_arguments_set_product(original_ner_list, ner_list, grouped_ner_list, code_mapping_results_model)

    # __log.debug(f"code_mapping_results: {code_mapping_results_model}") # 볼거
    # elapsed_time = time.time() - unstructured_code_mapping_start_time
    # __log.debug(f'complement: _code_mapping: unstructured_code_mapping: process_ner_item 1st: {round(elapsed_time, 4)}')

    is_product_key = [d.get('expression') for d in code_mapping_results_model if 'NA' in d.get('category_lv1') and 'NA' in d.get('category_lv2') and 'NA' in d.get('category_lv3')]
    # __log.debug(f"is_product_key: {is_product_key}")
    if is_product_key and len([d.get('expression') for d in ner_list if d.get('field') in ['product_model', 'product_code']]) > 1:
        for i in range(len(grouped_ner_list)-1, -1, -1):
            product_group_list = grouped_ner_list[i]
            product_group_check = any([d for d in product_group_list if d.get('expression') in is_product_key])
            # __log.debug(f"product_group_check: {product_group_check}")
            if product_group_check and len(product_group_list) == 1:
                grouped_ner_list.pop(i)
                original_ner_list = [d for d in original_ner_list if d.get('expression') not in is_product_key]
                ner_list = [d for d in ner_list if d.get('expression') not in is_product_key]
                code_mapping_results_model = [d for d in code_mapping_results_model if d.get('expression') not in is_product_key]

    is_nanana_key = [d.get('expression') for d in code_mapping_results_model if 'NA' in d.get('category_lv1') and 'NA' in d.get('category_lv2') and 'NA' in d.get('category_lv3')]
    if is_nanana_key and len([d.get('expression') for d in ner_list if d.get('field') in ['product_model', 'product_code']]) > 1:
        for i in range(len(original_ner_list)-1, -1, -1):
            o_ner = original_ner_list[i]
            if o_ner.get('field') in 'product_model' and o_ner.get('expression') in is_nanana_key:
                original_ner_list.pop(i)
                ner_list.pop(i)

        if country_code == 'KR':
            grouped_ner_list = cm_utils.split_ner_by_conjunction(rewrite_query, original_ner_list, ner_list)
        else:
            grouped_ner_list = cm_utils.split_ner_by_conjunction(rewrite_query, original_ner_list, ner_list, conjunction_list=['와', '과', '랑', '의', 'and', 'or', ','])

    # __log.debug(grouped_ner_list)

    for group_ner in grouped_ner_list:
        removed_option = []
        remove_ner_tg = [d for d in group_ner if d.get('field') not in ['product_release_date', 'product_price', 'istm_prd', 'cardc_cd', 'extend_request', 'product_accessory', 'split_pay']]
        if country_code == 'KR':
            _, removed_option = cm_utils.preprocess_ner_value(remove_ner_tg)
            if removed_option:
                removed_option = [d.get('expression') for d in removed_option]
        else:
            _, removed_option_front = cm_utils.preprocess_ner_value_front(remove_ner_tg)
            _, removed_option_end = cm_utils.preprocess_ner_value(remove_ner_tg)
            removed_option = removed_option_front + removed_option_end
            if removed_option:
                removed_option = list(set([d.get('expression') for d in removed_option]))
        for item in group_ner:
        # for item in group_ner:
            if item["field"] in function_code_mapping_target_fields and item["expression"]:
                if item['operator'] in ['min', 'max']:
                    continue
                target_ner_list = [d for d in group_ner if d.get("field") in ['product_model', 'product_code']]
                ### 06.05 modified by hsm (lower 추가)
                target_code_mapping = [d for d in code_mapping_results_model if d.get('expression') in [d.get('expression') for d in target_ner_list]] if country_code == 'KR' else [d for d in code_mapping_results_model if d.get('expression').lower() in [d.get('expression').lower() for d in target_ner_list]]
                # target_code_mapping = [d for d in code_mapping_results_model if d.get('expression') in [d.get('expression') for d in target_ner_list]] if country_code == 'KR' else [d for d in code_mapping_results_model if d.get('expression').lower() in [d.get('expression') for d in target_ner_list]]
                ###
                if any(set([d.get('expression') for d in target_code_mapping]) & set(invalid_items)):
                    continue
                model_category_lv1, model_category_lv2, model_category_lv3 = extract_categories(target_code_mapping)
                result, _, _ = process_ner_item(item=item, 
                                        p_type='function', 
                                        model_category_lv1=model_category_lv1, 
                                        model_category_lv2=model_category_lv2, 
                                        model_category_lv3=model_category_lv3, 
                                        country_code=country_code,
                                        site_cd=site_cd, 
                                        message_id=message_id)
                if result is not None and 'spec' not in result.get("type", ""):
                    code_mapping_results_function.append(result)
                else:
                    # __log.debug(f"removed_option: {removed_option}")
                    # __log.debug(item.get('expression'))
                    if removed_option and item.get('expression') in removed_option:
                        continue
                    else:
                        # ct = time.time()
                        result, cpt_flag = cm_utils.match_rewrite_cpt_option(rewrite_query, item, model_category_lv1, model_category_lv2, model_category_lv3, country_code, site_cd, message_id)
                        # __log.debug(f"test time: {time.time() - ct} s")
                        # __log.debug(f"res: {result} : {cpt_flag}")
                        if cpt_flag:
                            code_mapping_results_function.append(result)
                    # continue
        # __log.debug(f"code_mapping_results2: {code_mapping_results_function}")
    # elapsed_time = time.time() - unstructured_code_mapping_start_time
    # __log.debug(f'complement: _code_mapping: unstructured_code_mapping: process_ner_item 2nd: {round(elapsed_time, 4)}')

    if code_mapping_results_function:
        default_fn = [d.get('expression') for d in code_mapping_results_function if 'DEFAULT' in d.get('mapping_code')]
        if default_fn:
            original_ner_list = [d for d in original_ner_list if not (d.get('expression') in default_fn and d.get('field') == 'product_option')]
            ner_list = [d for d in ner_list if not (d.get('expression') in default_fn and d.get('field') == 'product_option')]
            code_mapping_results_function = [d for d in code_mapping_results_function if 'DEFAULT' not in d.get('mapping_code')]


    for i in range(len(grouped_ner_list) -1, -1, -1):
        is_invalid_expr = [d.get('expression') for d in grouped_ner_list[i] if d.get('field') in ['product_code', 'product_model']]
        # __log.debug(f"check_invalid_expr: {is_invalid_expr}")
        if any(set(is_invalid_expr) & set(invalid_items)):
            invalid_groups.extend([d.get('expression') for d in grouped_ner_list[i]])
            grouped_ner_list.pop(i)
    if invalid_groups:
        ner_list = [d for d in ner_list if d.get('expression') not in invalid_groups]
    elapsed_time = time.time() - unstructured_code_mapping_start_time

    code_mapping_results = code_mapping_results_model + code_mapping_results_function
    code_mapping_results_function_deepcopy = deepcopy(code_mapping_results_function)
    # __log.debug(f"code_mapping_results_check: {code_mapping_results}")
    for item in code_mapping_results:
        item["original_expression"] = item["expression"]
    if any(result["field"] in option_code_mapping_target_fields for result in ner_list):
        filtered_target = [
            {"field": result["field"], "expression": result["expression"], "operator": result["operator"]}
            for result in ner_list
            if result["field"] in option_code_mapping_target_fields
        ]

        # __log.debug(f"filtered_target: {filtered_target}")
        expression = [result["expression"] for result in filtered_target][0]
        match = re.match(r"([\d.]+)\s*(.*)", str(expression))
        if match:
            match_soundbar = re.match(r'^(\d{1,2}\.\d\.\d) (채널)$', expression)
            if match_soundbar:
                number = match.group(1)
            else:
                number = float(match.group(1))
                unit = match.group(2).strip()
        else:
            number = None
            unit = None
        
        # 'func' in type일 경우 처리 방안 
        # 예: 
        # type_key = any(["func" in c["type"] for c in filtered_target])
        # validity_key = any(set(option_code_mapping_target_fields) & set(list(filtered_target.keys())))
        validity_key = any(set(sum([c.get('type', []) for c in code_mapping_results], [])) & set(['func', 'CPT']))
        minmax_key = any([bool(set(['min', 'max']) & set(n.values())) for n in filtered_target])
        color_key = any(['product_color' in f.get('field', "") for f in filtered_target])
        spec_key = any(['product_spec' in f.get('field', "") for f in filtered_target])

        # __log.debug(f"""
        # validity_key: {validity_key}
        # minmax_key: {minmax_key}
        # color_key: {color_key}
        # spec_key: {spec_key}
        # number: {number}
        # """)
        if not number is None or minmax_key or color_key or not validity_key or spec_key:
            # if country_code == 'KR':
            code_mapping_results_temp = []
            # __log.debug(f"==-=-=-=-=-=-=-=-=-=-: {code_mapping_results}") # 볼거

            for n in grouped_ner_list:
                # print("*"*210)
                # __log.debug(f"n: {n}")
                expression_n = [d.get('expression') for d in n] if country_code == 'KR' else [d.get('expression').upper() for d in n]
                # __log.debug(f"expression_n:{expression_n}")
                cm_filtered = [deepcopy(d) for d in code_mapping_results if d.get('expression') in expression_n] if country_code == 'KR' else [d for d in code_mapping_results if d.get('expression').upper() in expression_n]
                # __log.debug(f"cm_filtered: {cm_filtered}")
                function_expression = [d.get('expression') for d in cm_filtered if 'func' in d.get('type', []) or 'CPT' in d.get('type', [])]
                cm_filtered = [d for d in cm_filtered if d.get('expression').upper() not in function_expression]
                # __log.debug(f"function_expression: {function_expression}")
                n = [d for d in n if d.get('expression') not in function_expression]
                # print("*"*210)
                code_mapping_results_n, err_spec, about_operator_flag_list_temp = product_function_validation_kr.product_validity_check(
                    n,
                    cm_filtered,
                    intelligence,
                    option_code_mapping_target_fields,
                    country_code,
                    site_cd,
                    message_id,
                )
                # __log.debug(f"code_mapping_results_n: {code_mapping_results_n}")
                if err_spec:
                    err_spec_out = err_spec
                if about_operator_flag_list_temp:
                    about_operator_flag_list.extend(about_operator_flag_list_temp)
                if code_mapping_results_n is None:
                    continue
                    # return {"unstructured": []}, rewrite_query, original_ner_list, ner_list, grouped_ner_list, code_mapping_error_list, l4_filter_list, code_mapping_results_model, err_spec_out
                # elapsed_time = time.time() - unstructured_code_mapping_start_time
                # __log.debug(f'complement: _code_mapping: unstructured_code_mapping: product_validity_check: {round(elapsed_time, 4)}')

                code_mapping_results_n_copy = deepcopy(code_mapping_results_n)
                code_mapping_results_temp.extend(code_mapping_results_n_copy)
            code_mapping_results = code_mapping_results_temp + code_mapping_results_function_deepcopy
            # __log.debug(f"code_mapping_results_check: {code_mapping_results}")

            for data in code_mapping_results:
                expression_placeholders = data.get("expression", "")
                mapping_codes = data.get('mapping_code')
                option_fields = data.get('option',{}).get('field')
                for ner in ner_list:
                    # __log.debug(ner)

                    if "product_model" == ner["field"]:
                        pass
                    if "product_spec" == ner["field"]:
                        # __log.debug(ner['expression'])
                        if ner["expression"].lower().replace(
                            " ", ""
                        ) in expression_placeholders.lower().replace(
                            " ", ""
                        ):
                            pass
                        else:
                            expression_placeholders = (
                                expression_placeholders
                                + " "
                                + str(ner["expression"])
                            )

                # __log.debug(f'expression_placeholders: {expression_placeholders}')

                if intelligence == intelligences.PRODUCT_RECOMMENDATION or mapping_codes is None or option_fields or len(mapping_codes) > 1:
                    data["mapping_code"] = mapping_codes
                else:
                    if len(mapping_codes) == 1:
                        reranked_data = mapping_codes
                    else:
                        # rerank_start_time = time.time()

                        reranked_data, _ = embedding_rerank.rerank_list(
                            expression_placeholders, mapping_codes
                        )
                        # elapsed_time = time.time() - rerank_start_time
                        # __log.debug(f'complement: _code_mapping: unstructured_code_mapping: rerank_duration: {round(elapsed_time, 4)}')

                    mapping_codes = reranked_data[0]

                    data["mapping_code"] = [mapping_codes]

                # elapsed_time = time.time() - unstructured_code_mapping_start_time
                # __log.debug(f'complement: _code_mapping: unstructured_code_mapping: rerank_list: {round(elapsed_time, 4)}')

    # elapsed_time = time.time() - unstructured_code_mapping_start_time
    # __log.debug(f'complement: _code_mapping: unstructured_code_mapping: final: {round(elapsed_time, 4)}')
    return {"unstructured": code_mapping_results}, rewrite_query, original_ner_list, ner_list, grouped_ner_list, code_mapping_error_list, l4_filter_list, code_mapping_results_model, err_spec_out, about_operator_flag_list, c2c_cm


if __name__ == "__main__":
    django.setup()

    ner_value = [
          {
            "field": "product_model",
            "expression": "TV",
            "operator": "in"
          },
          {
            "field": "product_option",
            "expression": "AI upscaling",
            "operator": "in"
          },
          {
            "field": "product_spec",
            "expression": "60 INCH",
            "operator": "greater_than"
          },
          {
            "field": "product_spec",
            "expression": "80 INCH",
            "operator": "less_than"
          }
        ]
    
    # new_ner_value = unstructured_code_mapping('What are the options for a TV with AI upscaling over 60 inches and up to 80 inches?', original_ner, ner_value, 'Product Recommendation', "GB", "test")

    # 50 인치 이하 TV 추천해줘
    # new_ner_value = unstructured_code_mapping('Please recommend me the biggest TV model.', original_ner, ner_value, 'Product Recommendation', "GB", "test")

    # original_ner = [                                                                                                                                                                                                                                                                                                                 
    #                {'expression': 'smallest', 'field': 'product_option', 'operator': 'min'},
    #                {'expression': 'QLED TV', 'field': 'product_model', 'operator': 'in'}                                                                                                                       
    #            ]
    # ner_value = [                                                                                                                                                                                                                                                                                                                 
    #                {'expression': 'smallest', 'field': 'product_option', 'operator': 'min'},
    #                {'expression': 'QLED TV', 'field': 'product_model', 'operator': 'in'}      
    # ]
    # new_ner_value = unstructured_code_mapping('Please recommend me the smallest QLED TV model.', original_ner, ner_value, 'Product Recommendation', "GB", "test")
    
    # print("*"* 200)
    # __log.debug(new_ner_value)
