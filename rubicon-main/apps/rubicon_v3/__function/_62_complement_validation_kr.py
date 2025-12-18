import numpy as np
import pandas as pd
import asyncio
import re
import time
from alpha import __log
from typing import Dict, List
from functools import reduce
from django.db import connection

from apps.rubicon_v3.models import Virtual_View_Field
from apps.rubicon_v3.__function import __embedding_rerank as embedding_rerank
from apps.rubicon_v3.__function import __utils as utils
import apps.rubicon_v3.__function._62_complement_code_mapping_utils as cm_utils
from apps.rubicon_v3.__function.definitions import intelligences

def product_validity_check(ner_value, code_mapping_results, intelligence, option_code_mapping_target_fields, country_code, site_cd, message_id):
    product_validity_check_start_time = time.time()  # Record start time
    exist_nonexist_flag = False
    err_spec = None
    about_operator_flag_list = []
    
    # 기능 매핑된 경우 미리 제거
    function_mapping_codes = [c for c in code_mapping_results if 'func' in c.get('type', []) or 'CPT' in c.get('type', []) or 'CPT_D' in c.get('type', [])]
    # __log.debug(f"function_mapping_codes: {function_mapping_codes}")
    ner_value = [d for d in ner_value if d.get('field') not in ['product_release_date', 'promotion_date', 'product_price', 'istm_prd', 'cardc_cd', 'extend_request', 'product_accessory', 'split_pay']]
    ner_value = [c for c in ner_value if c.get('expression') not in [c.get('expression') for c in code_mapping_results if 'func' in c.get('type') or 'CPT' in c.get('type', []) or 'CPT_D' in c.get('type', [])]]
    
    # 필터로 사용하지 않을 option 제거
    if country_code == 'KR':
        ner_value, removed_option = cm_utils.preprocess_ner_value(ner_value)
    else:
        ner_value, removed_option = cm_utils.preprocess_ner_value_front(ner_value)
        ner_value, removed_option = cm_utils.preprocess_ner_value(ner_value)

    elapsed_time = time.time() - product_validity_check_start_time
    # __log.debug(f'complement: _code_mapping: unstructured_code_mapping: product_validity_check: 필터로 사용하지 않을 option 제거: {round(elapsed_time, 4)}')
    # print("====================================")
    # __log.debug(ner_value) 
    # __log.debug(code_mapping_results) 
    # print("====================================")
    # elapsed_time = time.time() - product_validity_check_start_time
    # __log.debug(f'complement: _code_mapping: unstructured_code_mapping: product_validity_check: print: {round(elapsed_time, 4)}')

    code_mapping_results = [c for c in code_mapping_results if 'func' not in c.get('type', []) and 'CPT' not in c.get('type', []) and 'CPT_D' not in c.get('type', [])]
    # __log.debug(f"code_mapping_results: {code_mapping_results}")

    purchasable_key = (intelligence == intelligences.PRODUCT_RECOMMENDATION or intelligence == intelligences.BUY_INFORMATION) and not any(set(['c2c', 'e2e']) & set(sum([d.get('type') for d in code_mapping_results], [])))
    # Get category 123
    grouped_mapping_codes = group_mapping_codes(code_mapping_results)
    # __log.debug(f"grouped_mapping_codes: {grouped_mapping_codes}") 
    elapsed_time = time.time() - product_validity_check_start_time
    # __log.debug(f'complement: _code_mapping: unstructured_code_mapping: product_validity_check: group_mapping_codes: {round(elapsed_time, 4)}')
    product_category_lv1, product_category_lv2, product_category_lv3 = grouped_mapping_codes[0], grouped_mapping_codes[1], grouped_mapping_codes[2]
    
    # filtered_target = [{'field': result['field'], 'expression': result['expression'], 'operator': result.get('operator', '')} for result in ner_value if result['field'] in ['product_spec']]
    # __log.debug(f"filtered_target: {filtered_target}") # [{'field': 'product_spec', 'expression': '70인치', 'operator': 'less_than'}] 형태
    
    # Get Spec Names    
    spec_name = [
        {'field': result['field'], 'expression': result['expression'], 'operator': result.get('operator', '')} 
        for result in ner_value if result['field'] in ['product_option']]
    # __log.debug(f"spec_name: {spec_name}") 
    cm_mc = sum([d.get('mapping_code') for d in code_mapping_results], [])
    # exist_nonexist insert 0613, 0710
    option_unit_map, option_df_map, mapped_spec_list, exist_nonexist_flag = cm_utils.process_spec_options(spec_name, purchasable_key, product_category_lv1, product_category_lv2, product_category_lv3, country_code, site_cd, message_id, exist_nonexist_flag, cm_mc, code_mapping_results)
    
    # __log.debug(option_unit_map) 
    # __log.debug(option_df_map) 
    # elapsed_time = time.time() - product_validity_check_start_time
    # __log.debug(f'complement: _code_mapping: unstructured_code_mapping: process_spec_options: product_validity_check: {round(elapsed_time, 4)}')
    # __log.debug(mapped_spec_list) 
    for i, item in enumerate(ner_value):
        if item.get('field') in ['product_option', 'product_color']:
            expression = item.get('expression')
            if expression:
                # mapped_spec_list에서 일치하는 항목 찾기
                for mapped_spec in mapped_spec_list:
                    if mapped_spec.get('expression') == expression and mapped_spec.get('field') == item.get('field'):
                        # 일치하는 항목이 있으면 mapping_code로 변환 (첫 번째 요소 사용)
                        if mapped_spec.get('mapping_code') and len(mapped_spec.get('mapping_code')) > 0:
                            ner_value[i]['expression'] = mapped_spec.get('mapping_code')[0]
                        break 
    # __log.debug(f"dddddd: {ner_value}") 
    # elapsed_time = time.time() - product_validity_check_start_time
    # __log.debug(f'complement: _code_mapping: unstructured_code_mapping: process_spec_options: dddddd: {round(elapsed_time, 4)}')

    ner_split = cm_utils.split_ner_by_categories(ner_value)
    expressions = [d.get('expression') for d in ner_value if d.get('field') in ['product_color', 'product_spec']]
    if 's2s' in sum([d.get('type') for d in code_mapping_results if d.get('field') == 'product_model'], []):
        ner_color = []
        ner_minmax = []
        ner_llist = []
        ner_model = []
    else:
        ner_color, ner_model, ner_minmax, ner_llist = cm_utils.categorize_split_lists(ner_split)

    ner_llist = cm_utils.group_options_with_specs(ner_llist, option_unit_map)

    # print("-" * 210)
    # print("-" * 100 + "NER groups" + "-" * 100)
    # print("-" * 210)
    # __log.debug(ner_color)
    # __log.debug(ner_model)
    # __log.debug(ner_minmax)
    # __log.debug(ner_llist)
    # print("-" * 210)
    # elapsed_time = time.time() - product_validity_check_start_time
    # __log.debug(f'complement: _code_mapping: unstructured_code_mapping: process_spec_options: group_options_with_specs: {round(elapsed_time, 4)}')
    if not ner_color and not ner_minmax and not ner_llist:
        return code_mapping_results, err_spec, about_operator_flag_list

    high_level_key = 'h2h' in sum([d.get('type') for d in code_mapping_results if d.get('field') == 'product_model'], []) and 'p2p' not in sum([d.get('type') for d in code_mapping_results if d.get('field') == 'product_model'], [])
    high_level_mapping_code = [d.get('mapping_code')[0] for d in code_mapping_results if d.get('field') == 'product_model'][0] if high_level_key else None

    option_code_mapping_results, err_spec, about_operator_flag_list = process_ner_item_option(
        expressions,
        purchasable_key, 
        high_level_key, 
        high_level_mapping_code, 
        ner_color, 
        ner_model, 
        ner_minmax, 
        ner_llist, 
        option_df_map, 
        product_category_lv1, 
        product_category_lv2, 
        product_category_lv3, 
        country_code,
        site_cd, 
        message_id,
        exist_nonexist_flag,
        cm_mc,
        code_mapping_results)
    # __log.debug(f"option_code_mapping_results:{option_code_mapping_results}") # 볼거
    # elapsed_time = time.time() - product_validity_check_start_time
    # __log.debug(f'complement: _code_mapping: unstructured_code_mapping: process_spec_options: process_ner_item_option: {round(elapsed_time, 4)}')
    if option_code_mapping_results is None:
        return None, err_spec, about_operator_flag_list
    if option_code_mapping_results.get('mapping_code') is None:
        return None, err_spec, about_operator_flag_list

    if option_code_mapping_results.get('mapping_code'):
            for item in code_mapping_results:
                if item.get('field', "") == 'product_function':
                    pass
                else:
                    item['option'] = {
                        "expression": option_code_mapping_results['expression'],
                        "field": option_code_mapping_results['field'],
                        "mapping_code": option_code_mapping_results['values']
                    }
                    # item['original_expression'] = item['expression']
                    item['expression'] = item['expression']
                    item["mdl_code"] = option_code_mapping_results.get("mdl_code","")
                    item['mapping_code'] = option_code_mapping_results['mapping_code']
                    item['category_lv1'] = option_code_mapping_results.get('category_lv1')
                    item['category_lv2'] = option_code_mapping_results.get('category_lv2')
                    item['category_lv3'] = option_code_mapping_results.get('category_lv3')
    if function_mapping_codes:
        code_mapping_results.extend(function_mapping_codes) 
    return code_mapping_results, err_spec, about_operator_flag_list
    

def group_mapping_codes(results):
        product_category_lv1 = []
        product_category_lv2 = []
        product_category_lv3 = []

        for result in results:
            if 'spec' in result.get('type'):
                pass
            else:
                product_category_lv1.extend(result.get("category_lv1", []))
                product_category_lv2.extend(result.get("category_lv2", []))
                product_category_lv3.extend(result.get("category_lv3", []))
        return [product_category_lv1, product_category_lv2, product_category_lv3]

# exist_nonexist insert 0613 (parameter 추가 - exist_nonexist_flag)
def process_ner_item_option(expressions, purchasable_key, high_level_key, high_level_mapping_code, ner_color, ner_model, ner_minmax, ner_llist, option_df_map, product_category_lv1, product_category_lv2, product_category_lv3, country_code, site_cd, message_id, exist_nonexist_flag, cm_mc, code_mapping_results) -> List[Dict[str, str]]:
    process_ner_item_option_start_time = time.time()

    err_spec = None
    about_operator_flag_list = []
    df_color = None
    df_mnmax = None
    df_llist = []
    df_llist_mnmax_mdlcd = []
    if ner_color:
        # exist_nonexist insert 0613 (parameter 추가 - exist_nonexist_flag)
        df_color, err_spec, about_operator_flag = code_retriever(ner_color, purchasable_key, None, 'color', None, None, product_category_lv1, product_category_lv2, product_category_lv3, country_code, site_cd, message_id, exist_nonexist_flag, None, cm_mc, code_mapping_results)
        if df_color.empty:
            return None, err_spec, about_operator_flag_list
    if ner_llist:
        for ner_list in ner_llist:
            # __log.debug(f"nerlist: {ner_list}")
            # exist_nonexist insert 0613 (parameter 추가 - exist_nonexist_flag)
            df_temp, err_spec, about_operator_flag = code_retriever(ner_list, purchasable_key, option_df_map, 'llist', high_level_key, high_level_mapping_code, product_category_lv1, product_category_lv2, product_category_lv3, country_code, site_cd, message_id, exist_nonexist_flag, None, cm_mc, code_mapping_results)
            if df_temp.empty:
                return None, err_spec, about_operator_flag_list
            if df_temp is not None:
                df_llist.append(df_temp)
                about_operator_flag_list.append(about_operator_flag)
                if not df_llist_mnmax_mdlcd:
                    df_llist_mnmax_mdlcd.extend(df_temp['mdl_code'].tolist())
                else:
                    df_llist_mnmax_mdlcd = list(set(df_llist_mnmax_mdlcd) & set(df_temp['mdl_code'].tolist()))
                    if not df_llist_mnmax_mdlcd:
                        return None, err_spec, about_operator_flag_list
    if ner_minmax:
        # exist_nonexist insert 0613 (parameter 추가 - exist_nonexist_flag)
        df_mnmax, err_spec, about_operator_flag = code_retriever(ner_minmax, purchasable_key, option_df_map, 'minmax', None, high_level_mapping_code, product_category_lv1, product_category_lv2, product_category_lv3, country_code, site_cd, message_id, exist_nonexist_flag, df_llist_mnmax_mdlcd, cm_mc, code_mapping_results)
        if df_mnmax.empty:
            return None, err_spec, about_operator_flag_list
    
    result_df = None
    key_cols = ['category_lv1', 'category_lv2', 'category_lv3', 'goods_nm', 'mdl_code']

    # elapsed_time = time.time() - process_ner_item_option_start_time
    # __log.debug(f'process_ner_item_option_start_time: code_retriever: {round(elapsed_time, 4)}')

    # __log.debug(f"df_color ------------------")
    # __log.debug(df_color)
    # __log.debug(f"df_mnmax ------------------")
    # __log.debug(df_mnmax)
    # __log.debug(f"df_llist ------------------")
    # __log.debug(df_llist)
    # __log.debug(f"------------------")
    # __log.debug(f"asdfasdfasdf {[df['category_lv3'].unique() for df in df_llist]}")
    # elapsed_time = time.time() - process_ner_item_option_start_time
    # __log.debug(f'process_ner_item_option_start_time: code_retriever result print : {round(elapsed_time, 4)}')

    all_dfs = []
    if df_color is not None:
        all_dfs.append(df_color)
    if df_mnmax is not None:
        all_dfs.append(df_mnmax)
    if df_llist:
        all_dfs.extend(df_llist)
    # __log.debug(f"------------------")
    # __log.debug(all_dfs)
    # __log.debug(f"------------------")
    if all_dfs:
        result_df = all_dfs[0].copy()

        value_cols = [col for col in result_df.columns if col.startswith('value')]

        if 'value' in value_cols:
            result_df = result_df.rename(columns={'value': 'value_0'})
        
        for i, df in enumerate(all_dfs[1:], 1):
            curr_value_cols = [col for col in df.columns if col.startswith('value')]
            
            rename_dict = {}
            
            existing_value_count = len([col for col in result_df.columns if col.startswith('value')])
            
            for j, col in enumerate(curr_value_cols):
                new_col_name = f'value_{existing_value_count + j}'
                rename_dict[col] = new_col_name
            
            df_renamed = df.rename(columns=rename_dict)
            
            result_df = pd.merge(result_df, df_renamed, on=key_cols, how='inner')
    

    ## 2025.07.18 주석처리 함 (외장 HDD)
    # if high_level_key and result_df is not None and not result_df.empty:
    #     high_level_mapping_code = re.escape(high_level_mapping_code)
    #     result_df = result_df[result_df['goods_nm'].str.contains(high_level_mapping_code, case = False)]

    # print("=" * 210)
    # __log.debug(high_level_key) 
    # __log.debug(high_level_mapping_code) 
    # __log.debug(f"{result_df}") 
    # print("=" * 210)
    # elapsed_time = time.time() - process_ner_item_option_start_time
    # __log.debug(f'process_ner_item_option_start_time: high_level_mapping_code : {round(elapsed_time, 4)}')

    field_value = []
    if ner_color:
        field_value.append('product_color')
    if ner_llist or ner_minmax:
        field_value.append('product_spec')

    # df = code_retriever_optional(expression, embedded_expression_value, mapped_spec, mapped_spec_operator, field, operator, product_category_lv1, product_category_lv2, product_category_lv3, country_code, message_id)
    # __log.debug(f"dfdf: {df}")
    # results = {}
    # Add the original field mapping
    results = {
        'expression': expressions,
        'field': field_value,  
        'mapping_code': result_df['goods_nm'].dropna().drop_duplicates().tolist() if (result_df is not None and not result_df.empty) else None,
        'mdl_code': result_df['mdl_code'].dropna().drop_duplicates().tolist() if (result_df is not None and not result_df.empty) else None,
        'values': (
            list(dict.fromkeys([v for col in [c for c in result_df.columns if c.startswith('value')] 
                            for v in result_df[col].dropna().drop_duplicates().tolist()]))
            if (result_df is not None and not result_df.empty and any(c.startswith('value') for c in result_df.columns))
            else None
        )
    }
    
    # Add product categories only if all three levels have values
    if result_df is not None and not result_df.empty:
        # Check if we have complete category information (all levels non-null)
        complete_categories = result_df[
            result_df['category_lv1'].notna() & 
            result_df['category_lv2'].notna() & 
            result_df['category_lv3'].notna()
        ]
        
        if not complete_categories.empty:
            # Take the first row with complete categories
            first_complete = complete_categories
            
            # Add each category level as a separate ner item
            results["category_lv1"] = list(set(complete_categories['category_lv1'].values.tolist()))
            results["category_lv2"] = list(set(complete_categories['category_lv2'].values.tolist()))
            results["category_lv3"] = list(set(complete_categories['category_lv3'].values.tolist()))
    
    return results, err_spec, about_operator_flag_list

# exist_nonexist insert 0613 (parameter 추가 - exist_nonexist_flag)
def code_retriever(ner_list, purchasable_key, option_df_map, type, high_level_key, high_level_mapping_code, product_category_lv1, product_category_lv2, product_category_lv3, country_code, site_cd, message_id, exist_nonexist_flag, mnmnax_llist, cm_mc, code_mapping_results):
    code_retriever_start_time = time.time()

    result_df = None
    err_spec_out = None
    about_operator_flag = None
    product_category_lv1_placeholders = ", ".join(
        "'" + _ + "'" for _ in product_category_lv1
    )
    product_category_lv2_placeholders = ", ".join(
        "'" + _ + "'" for _ in product_category_lv2
    )
    product_category_lv3_placeholders = ", ".join(
        "'" + _ + "'" for _ in product_category_lv3
    )
    with connection.cursor() as curs:
        if type == 'color':
            for d in ner_list:
                e = d.get('expression')
                # __log.debug(f"expression: {e}")
                color_embedding = embedding_rerank.baai_embedding(e, message_id)[0]

                color_base_sql = f"""SELECT DISTINCT
                                    rcm.mapping_code,
                                    rcm.expression,
                                    subq.distance
                                FROM (
                                    SELECT DISTINCT
                                        expression,
                                        field,
                                        country_code,
                                        embedding <=> '{str(color_embedding)}' AS distance
                                    FROM rubicon_v3_complement_code_mapping
                                    WHERE active = TRUE
                                    AND country_code = '{country_code}'
                                    AND site_cd = '{site_cd}'
                                    AND field = 'product_color'
                                    ORDER BY distance
                                    LIMIT 10
                                ) subq
                                JOIN rubicon_v3_complement_code_mapping rcm 
                                    ON rcm.expression = subq.expression
                                    AND rcm.active = TRUE
                                    AND rcm.country_code = subq.country_code
                                    AND rcm.field = subq.field
                                ORDER BY subq.distance
                                LIMIT 1"""                            
                
                curs.execute(color_base_sql)
                result_base = curs.fetchall()
                mapped_color = result_base[0][0]
                # __log.debug(mapped_color)
                mapped_color_list = sum([l for l in cm_utils.COLOR_MAP_KR if mapped_color in l], []) if country_code == 'KR' else sum([l for l in cm_utils.COLOR_MAP_UK if mapped_color in l], [])
                
                expression_placeholders = ", ".join(
                    "'" + _ + "'" for _ in mapped_color_list if 'NA' != _
                )
                color_sql = f"""
                        SELECT category_lv1, category_lv2, category_lv3, goods_nm, mdl_code, disp_nm1, disp_nm2, value
                        FROM rubicon_v3_complement_product_spec
                        WHERE value in ({expression_placeholders})
                        AND site_cd in ('{site_cd}')
                        AND on_sale not like 'X'
                        """
                if "NA" not in product_category_lv1:
                    color_sql += f"AND category_lv1 in ({product_category_lv1_placeholders})"
                if "NA" not in product_category_lv2:
                    color_sql += f"AND category_lv2 in ({product_category_lv2_placeholders})"
                if "NA" not in product_category_lv3:
                    color_sql += f"AND category_lv3 in ({product_category_lv3_placeholders})"
                if purchasable_key:
                    color_sql += "AND on_sale = 'Y'"
                curs.execute(color_sql)
                results = curs.fetchall()
                df = pd.DataFrame(results, columns=[c.name for c in curs.description])
                if df.empty:
                    return pd.DataFrame(), err_spec_out, about_operator_flag
                else:
                    df = df[['category_lv1', 'category_lv2', 'category_lv3', 'goods_nm', 'mdl_code', 'value']].drop_duplicates()
                
                if result_df is None:
                    result_df = df
                else:
                    result_df = pd.concat([result_df, df], axis = 0, ignore_index=True)
            # __log.debug(result_df)
            return result_df, err_spec_out, about_operator_flag

        elif type == 'minmax':
            # __log.debug(option_df_map) 
            i = 1
            for d in ner_list:
                e = d.get('expression')
                o = d.get('operator')
                df_option = option_df_map.get(e)
                # __log.debug(df_option) 
                if mnmnax_llist:
                    df_option = df_option[df_option['mdl_code'].isin(mnmnax_llist)]
                df, err_spec, about_operator_flag = extract_and_find_closest(df_option, None, o, product_category_lv1, product_category_lv2, product_category_lv3, country_code, False)
                if err_spec:
                    err_spec_out = err_spec
                # __log.debug(df) 
                if df.empty:
                    return pd.DataFrame(), err_spec_out, about_operator_flag
                else:
                    df = df[['category_lv1', 'category_lv2', 'category_lv3', 'goods_nm', 'mdl_code', 'value']].drop_duplicates()
                if result_df is None:
                    result_df = df
                else:
                    temp_df = df.copy()
                    temp_df = temp_df.rename(columns={'value': f'value_{i}'})
                    
                    if 'value' in result_df.columns:
                        result_df = result_df.rename(columns={'value': 'value_0'})
                    
                    result_df = pd.merge(result_df, temp_df, 
                                        on=['category_lv1', 'category_lv2', 'category_lv3', 'goods_nm', 'mdl_code'],
                                        how='inner', 
                                        suffixes=('', ''))
                    i += 1
            # __log.debug(f"minmax: {result_df}")
            return result_df, err_spec_out, about_operator_flag
        
        elif type == 'llist':
            option_list = [d for d in ner_list if d.get('field') == 'product_option']
            spec_list = [d for d in ner_list if d.get('field') == 'product_spec']
            

            elapsed_time = time.time() - code_retriever_start_time
            # __log.debug(f'code_retriever:llist: {round(elapsed_time, 4)}')
            # __log.debug(f"is there option?: {option_list}") 
            if option_list:
                option_name = option_list[0].get('expression')
                df_option = option_df_map.get(option_name)
                
                # exist_nonexist insert 0613
                if exist_nonexist_flag:
                    result_df = df_option[['category_lv1', 'category_lv2', 'category_lv3', 'goods_nm', 'mdl_code', 'value']].drop_duplicates()
                    
                else:
                    for d in spec_list:
                        e = d.get('expression')
                        o = d.get('operator')
                        # delete 0723
                        # if high_level_key:
                        #     df_option = df_option[df_option['goods_nm'].str.contains(high_level_mapping_code, case = False)]
                        if re.match(r'^(\d{1,2}\.\d\.\d) (채널)$', e):
                            e = re.match(r'^(\d{1,2}\.\d\.\d) (채널)$', e).group(1)
                        df, err_spec, about_operator_flag = extract_and_find_closest(df_option, e, o, product_category_lv1, product_category_lv2, product_category_lv3, country_code, False)
                        # __log.debug(f"{e} {o}: {df}") 
                        if err_spec:
                            err_spec_out, about_operator_flag = err_spec, about_operator_flag
                        if df.empty:
                            return pd.DataFrame(), err_spec_out, about_operator_flag
                        else:
                            df = df[['category_lv1', 'category_lv2', 'category_lv3', 'goods_nm', 'mdl_code', 'value']].drop_duplicates()
                        if result_df is None:
                            result_df = df
                        else:
                            result_df = pd.merge(result_df, df,
                                                on = ['category_lv1', 'category_lv2', 'category_lv3', 'goods_nm', 'mdl_code', 'value'],
                                                how = 'inner')
                elapsed_time = time.time() - code_retriever_start_time
                # __log.debug(f'code_retriever: option_list: {round(elapsed_time, 4)}')
            else:
                i = 1
                for d in spec_list:
                    e = d.get('expression')
                    o = d.get('operator')
                    # __log.debug(f'eo: {e}, {o}')
                    expression_placeholders = "'" + e + "'"

                    spec_sql = f"""
                        SELECT category_lv1, category_lv2, category_lv3, goods_nm, mdl_code, disp_nm1, disp_nm2, value
                        FROM rubicon_v3_complement_product_spec
                        WHERE site_cd = '{site_cd}'
                        AND on_sale not like 'X'
                        """
                    if "NA" not in product_category_lv1:
                        spec_sql += f"AND category_lv1 in ({product_category_lv1_placeholders})"
                    if "NA" not in product_category_lv2:
                        spec_sql += f"AND category_lv2 in ({product_category_lv2_placeholders})"
                    if "NA" not in product_category_lv3:
                        spec_sql += f"AND category_lv3 in ({product_category_lv3_placeholders})"
                    if purchasable_key:
                        spec_sql += "AND on_sale = 'Y'"
                    curs.execute(spec_sql)
                    results = curs.fetchall()
                    df = pd.DataFrame(results, columns=[c.name for c in curs.description])
                                        # GB Flip/Fold 처리
                    gb_flip_key = any(['Flip' in s for s in cm_mc])
                    gb_fold_key = any(['Fold' in s for s in cm_mc])
                    if 'Galaxy Z' in product_category_lv3 and not df.empty:
                        if gb_flip_key and gb_fold_key:
                            pass
                        elif gb_flip_key:
                            df = df[df['goods_nm'].str.contains('Flip')]
                        elif gb_fold_key:
                            df = df[df['goods_nm'].str.contains('Fold')]
                    if country_code == 'GB':
                        l4_input = code_mapping_results[0]
                        expression = code_mapping_results[0]["expression"]
                        l4_check, l4_filters = cm_utils.check_valid_product(expression, l4_input, country_code)
                        product_filter = l4_filters["product_filter"]
                        # __log.debug(f"product filter: {product_filter} ")
                        df = df[df['goods_nm'].astype(str).str.lower().apply(lambda x: all(keyword in x for keyword in product_filter))]
                    # elapsed_time = time.time() - code_retriever_start_time
                    # __log.debug(f'code_retriever: rubicon_v3_complement_product_spec query: {round(elapsed_time, 4)}')
#                     __log.debug(f"""
# c1: {product_category_lv1}
# c2: {product_category_lv2}
# c3: {product_category_lv3}""")

                    # __log.debug(f'no spec name df: {df}')

                    if df.empty:
                        return pd.DataFrame(), err_spec_out, about_operator_flag

                    if 'COOKING GOODS' in product_category_lv1:
                        df['value'] = df['value'].astype(str).str.replace(r'\s*\([^)]*\)', '', regex=True)
                    if re.match(r'^(\d{1,2}\.\d\.\d) (채널)$', e):
                        e = re.match(r'^(\d{1,2}\.\d\.\d) (채널)$', e).group(1)
                    # delete 0723
                    # if high_level_key:
                    #     df = df[df['goods_nm'].str.contains(high_level_mapping_code, case = False)]
                    df, err_spec, about_operator_flag = extract_and_find_closest(df, e, o, product_category_lv1, product_category_lv2, product_category_lv3, country_code, True)
                    if err_spec:
                        err_spec_out = err_spec, about_operator_flag
                    elapsed_time = time.time() - code_retriever_start_time
                    # __log.debug(f'code_retriever: extract_and_find_closest: {round(elapsed_time, 4)}')

                    if df.empty:
                        return pd.DataFrame(), err_spec_out, about_operator_flag
                    df = df[['category_lv1', 'category_lv2', 'category_lv3', 'goods_nm', 'mdl_code', 'value']].drop_duplicates()
                    if result_df is None:
                        result_df = df
                    else:
                        temp_df = df.copy()
                        temp_df = temp_df.rename(columns={'value': f'value_{i}'})
                        
                        if 'value' in result_df.columns:
                            result_df = result_df.rename(columns={'value': 'value_0'})
                        
                        result_df = pd.merge(result_df, temp_df, 
                                            on=['category_lv1', 'category_lv2', 'category_lv3', 'goods_nm', 'mdl_code'],
                                            how='inner', 
                                            suffixes=('', ''))
                        i += 1
            elapsed_time = time.time() - code_retriever_start_time
            # __log.debug(f'code_retriever:final: {round(elapsed_time, 4)}')
            # __log.debug(f"result:{ner_list} \n {result_df}")
            return result_df, err_spec_out, about_operator_flag

        
def extract_and_find_closest(df, expression, operator, product_category_lv1, product_category_lv2, product_category_lv3, country_code, fixed_spec_name_key = False):
    extract_and_find_closest_start_time = time.time()  # Record start time
    # __log.debug(f'extract_and_find_closest: start')
    # __log.debug(f'extract_and_find_closest df: {df}')
    def get_sig(number):
        round_to_int = round(number)

        if round_to_int % 10 != 0:
            round_to_ten = round(round_to_int, -1)
        else:
            round_to_ten = round_to_int
        
        str_number = str(int(round_to_ten))
        last_nz = 0

        for i in range(len(str_number) -1, -1, -1):
            if str_number[i] != '0':
                last_nz = i
                break
        position = len(str_number) - 1 - last_nz
        return 10 ** position
    
    error_spec = None
    about_operator_flag = None
    converter = cm_utils.NetworkUnitConverter()

    if expression is not None:
    # expression에서도 숫자-단위 쌍 추출
        expression_pairs = cm_utils.extract_number_and_unit(expression)
        expression_number, expression_unit = expression_pairs[0]
        if not expression_pairs:
            return pd.DataFrame(), error_spec, about_operator_flag
        related_expression_units = converter.get_related_units(expression_unit)
        if len(related_expression_units) == 0:
            related_expression_units = [expression_unit]
        # __log.debug(f"expression_pairs: {expression_number} / {expression_unit} / {related_expression_units}") 
    else:
        expression_unit = None
        expression_number = None
        related_expression_units = []
    
    if fixed_spec_name_key:
        spec_name, spec_unit = cm_utils.specify_unknown_spec(expression_unit, related_expression_units, product_category_lv1, product_category_lv2, product_category_lv3, country_code)
        if any(set(['HOME AUDIO', 'COMSUMER AUDIO', 'PRO-AUDIO']) & set(product_category_lv1)) and isinstance(spec_name, list):
            if any(set(['본체 무게', '전체 무게', 'Weight (kg)', '중량', '무게정보', '무게', 'Weight']) & set(spec_name)):
                df = df[df['disp_nm2'].isin(['본체 무게', '전체 무게', 'Weight (kg)', '중량', '무게정보', '무게', 'Weight'])]
        if spec_name is not None and 'WEARABLE DEVICE VOICE' in product_category_lv2 and any(set(['크기(Main)', '크기 (Main Display)']) & set(spec_name)):
            df = df[df['disp_nm2'].isin(['크기(Main)', '크기 (Main Display)'])]
            for c3, r in cm_utils.WATCH_SIZE_REPLACE.items():
                mask = df['category_lv3'] == c3
                for ov, nv in r:
                    df.loc[mask, 'value'] = df.loc[mask, 'value'].str.replace(ov, nv)
        if spec_name and not ('WEARABLE DEVICE VOICE' in product_category_lv2 and any(set(['크기(Main)', '크기 (Main Display)']) & set(spec_name))):
            df = df[(df['disp_nm2'].isin(spec_name)) | (df['disp_nm1'].isin(spec_name))]
        if spec_name is not None and 'Size (Main Display)' in spec_name and 'Galaxy Watch' in product_category_lv3:
            df = df[df['disp_nm2'] == 'Size (Main Display)']
            df['cat'] = df['goods_nm'].apply(cm_utils.extract_watch_category)
            df['value'] = df['value'].apply(cm_utils.extract_mm_value)
            for c, r in cm_utils.WATCH_GB_REPLACE.items():
                mask = df['cat'] == c
                for ov, nv in r:
                    df.loc[mask, 'value'] = df.loc[mask, 'value'].str.replace(ov, nv)
            df = df.drop('cat', axis = 1)
        # 20250704 insert yji
        if 'MODULE' in product_category_lv2 and isinstance(spec_name, list) and any(set(['이어버드 배터리 용량 (Typical, mAh)', '배터리 용량 (이어버드, Typical)']) & set(spec_name)):
            df = df[df['disp_nm2'].isin(['이어버드 배터리 용량 (Typical, mAh)', '배터리 용량 (이어버드, Typical)'])]
            df['value'] = df['value'].apply(lambda x: x if 'mAh' in x else x + ' mAh')
        if spec_unit:
            # df['value'] = df['value'].astype(str) + ' ' + spec_unit
            df['value'] = np.where(
                df['value'].str.lower().str.endswith(spec_unit.lower()),
                df['value'],
                df['value'].astype(str) + ' ' + spec_unit
            )
    # __log.debug(df)
    # elapsed_time = time.time() - extract_and_find_closest_start_time
    # __log.debug(f'extract_and_find_closest: load converter: {round(elapsed_time, 4)}')
    # Extract number and unit pairs from each value in the DataFrame
    df_to_explode = df.copy().dropna(subset = 'value')
    if ('Internal SSD' in product_category_lv3 or 'Micro SD' in product_category_lv3 or 'SD Memory' in product_category_lv3 or 'BRAND CARD' in product_category_lv2) and 'TB' in related_expression_units:
        df_to_explode = df_to_explode[df_to_explode['disp_nm2'].isin(['용량', 'Capacity'])]
        df_to_explode['value'] = df_to_explode['value'].str.replace(r'\s*\([^)]*\)', '', regex = True)
        df_to_explode['value'] = df_to_explode['value'].str.extract(r'([\d,]+\s*GB)', flags = re.IGNORECASE)[0]
        df_to_explode['value'] = df_to_explode['value'].str.replace(',', '', regex=False).replace(r'(\d+)\s*(GB)', r'\1 \2', regex=True)
    
    elif ('Internal SSD' in product_category_lv3 or 'Micro SD' in product_category_lv3  or 'SD Memory' in product_category_lv3 or 'BRAND CARD' in product_category_lv2) and not related_expression_units and operator in ['min', 'max']:
        # df_to_explode = df_to_explode[df_to_explode['disp_nm2'].isin(['용량', 'Capacity'])]
        df_to_explode['value'] = df_to_explode['value'].str.replace(r'\s*\([^)]*\)', '', regex = True)
        df_to_explode['value'] = df_to_explode['value'].str.replace('1TB|1 TB', '1024GB', regex = True)
        df_to_explode['value'] = df_to_explode['value'].str.extract(r'([\d,]+\s*GB)', flags = re.IGNORECASE)[0]
        df_to_explode['value'] = df_to_explode['value'].str.replace(',', '', regex=False).replace(r'(\d+)\s*(GB)', r'\1 \2', regex=True)

    try:
        if '화면크기' in df_to_explode['disp_nm2'].tolist():
            if set(['KU60UD7050FXKR','KU65UD7050FXKR','KU65UD7030FXKR']) & set(df_to_explode[df_to_explode['disp_nm2'] == '화면크기']['mdl_code'].tolist()):
                df_to_explode.loc[df_to_explode['mdl_code'].isin(['KU60UD7050FXKR','KU65UD7050FXKR','KU65UD7030FXKR']), 'value'] = df_to_explode.loc[df_to_explode['mdl_code'].isin(['KU60UD7050FXKR','KU65UD7050FXKR','KU65UD7030FXKR']), 'value'].str.replace('60', '152')
                df_to_explode.loc[df_to_explode['mdl_code'].isin(['KU60UD7050FXKR','KU65UD7050FXKR','KU65UD7030FXKR']), 'value'] = df_to_explode.loc[df_to_explode['mdl_code'].isin(['KU60UD7050FXKR','KU65UD7050FXKR','KU65UD7030FXKR']), 'value'].str.replace('65', '163')
    except:
        pass

    df_to_explode['number_unit_pairs'] = df_to_explode['value'].apply(cm_utils.extract_number_and_unit)

    # __log.debug(f'df_to_explode: {df_to_explode}')

    # elapsed_time = time.time() - extract_and_find_closest_start_time
    # __log.debug(f'extract_and_find_closest: apply: {round(elapsed_time, 4)}')
    # Explode the DataFrame to create a row for each number-unit pair
    df_exploded = df_to_explode.explode('number_unit_pairs')

    # elapsed_time = time.time() - extract_and_find_closest_start_time
    # __log.debug(f'extract_and_find_closest: exploded: {round(elapsed_time, 4)}')

    # 안전하게 split tuples into separate columns
    df_exploded['extracted_number'] = df_exploded['number_unit_pairs'].apply(lambda x: x[0] if x else None)
    df_exploded['extracted_unit'] = df_exploded['number_unit_pairs'].apply(lambda x: x[1] if x else None)
    df_exploded = df_exploded.dropna(subset = ['extracted_number', 'extracted_unit'], how = 'any')
    # __log.debug(f'df_exploded:{df_exploded}')
    
    elapsed_time = time.time() - extract_and_find_closest_start_time
    # __log.debug(f'extract_and_find_closest: df_exploded: {round(elapsed_time, 4)}')

    if expression_unit and expression_number and related_expression_units:
        df_exploded = df_exploded.loc[df_exploded['extracted_unit'].str.upper().isin(related_expression_units)]
        # df = df.loc[df['value'].astype(str).str.contains(expression_unit, case = False, regex = True)]
        # Convert units if needed.
        # __log.debug(f"df_exploded2: {df_exploded}")    
        df_exploded = converter.expand_dataframe(df_exploded)
        # __log.debug(f"0000 {df_exploded.sort_values('extracted_number')}")
        # Drop rows where no pairs were found
        # __log.debug(f'df_exploded: {df_exploded.shape}')
        # __log.debug(df_exploded)
        if df_exploded.empty or not set(['extracted_number', 'extracted_unit']).issubset(set(df_exploded.columns)):
            error_spec = 'spec issue'
            return pd.DataFrame(), error_spec, about_operator_flag
        df_filtered = df_exploded.dropna(subset=['extracted_number', 'extracted_unit'])

        unique_units = df_filtered['extracted_unit'].nunique()
        consider_units = unique_units > 1


        df_unit_filtered = df_filtered.copy()
        if expression_unit not in df_unit_filtered['extracted_unit'].unique():
            # Assume all rows in the DataFrame use the same unit for simplicity
            target_unit = df_unit_filtered['extracted_unit'].iloc[0]
            expression_unit = target_unit
        if consider_units:
            df_unit_filtered = df_unit_filtered.loc[df_unit_filtered['extracted_unit'] == expression_unit]
    else:
        df_filtered = df_exploded.dropna(subset=['extracted_number', 'extracted_unit'])

        unique_units = df_filtered['extracted_unit'].nunique()
        consider_units = unique_units > 1


        df_unit_filtered = df_filtered.copy()
    # __log.debug(f"df_unit_filtered: {df_unit_filtered.sort_values('extracted_number', ascending=False)}")
    if not df_unit_filtered.empty:
        if operator == 'less_than':
            df_unit_filtered['difference_key'] = df_unit_filtered['extracted_number'] - expression_number
            df_unit_filtered = df_unit_filtered.loc[df_unit_filtered['difference_key'] <= 0]
            result = df_unit_filtered
        elif operator == 'greater_than':
            df_unit_filtered['difference_key'] = df_unit_filtered['extracted_number'] - expression_number
            df_unit_filtered = df_unit_filtered.loc[df_unit_filtered['difference_key'] >= 0]
            result = df_unit_filtered
        elif operator == 'about':
            range_key = get_sig(expression_number) + expression_number
            # df_unit_filtered['difference_key'] = abs(df_unit_filtered['extracted_number'] - expression_number * 1.1)
            df_unit_filtered_temp = df_unit_filtered.loc[(df_unit_filtered['extracted_number'] >= expression_number) & (df_unit_filtered['extracted_number'] < range_key)]
            result = df_unit_filtered_temp.sort_values('extracted_number', ascending = True) #.nsmallest(1, 'difference_key') # TODO how?
            if result.empty and expression_unit not in ['GB', 'TB']:
                # __log.debug(expression_unit)
                df_unit_filtered['difference_key'] = abs(df_unit_filtered['extracted_number'] - expression_number)
                df_unit_filtered = df_unit_filtered[df_unit_filtered['difference_key'] <= 0.2 * expression_number]
                # __log.debug(df_unit_filtered)
                result = df_unit_filtered.nsmallest(2, 'difference_key')
                about_operator_flag = {expression: 'retry'}
                # __log.debug(about_operator_flag)
        elif operator == 'max':
            k_near = df_unit_filtered.sort_values('extracted_number', ascending = False)['extracted_number'].unique()[:1]
            result = df_unit_filtered.loc[df_unit_filtered['extracted_number'].isin(k_near)]                    
        elif operator == 'min':
            k_near = df_unit_filtered.sort_values('extracted_number', ascending = True)['extracted_number'].unique()[:1]
            result = df_unit_filtered.loc[df_unit_filtered['extracted_number'].isin(k_near)]
        elif operator == 'not_in'                    :
            df_unit_filtered['difference_key'] = df_unit_filtered['extracted_number'] - expression_number
            df_unit_filtered = df_unit_filtered.loc[df_unit_filtered['difference_key'] != 0]
            result = df_unit_filtered
        else:
            df_unit_filtered['difference_key'] = abs(df_unit_filtered['extracted_number'] - expression_number)
            min_value = df_unit_filtered['difference_key'].min()
            result = df_unit_filtered.loc[df_unit_filtered['difference_key'] == min_value]
    if not result.empty:
        result = result.drop(['disp_nm1', 'disp_nm2', 'number_unit_pairs', 'extracted_number', 'extracted_unit'], axis = 1)
    # __log.debug(result)
    return result, error_spec, about_operator_flag