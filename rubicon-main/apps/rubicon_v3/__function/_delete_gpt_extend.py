# line 2 ~ 7 테스트 시 주석 해제
import sys
sys.path.append('/www/alpha/')
import os
import re
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'alpha.settings')
django.setup()

import time
from copy import deepcopy
import pandas as pd
import ast
from word2number import w2n
from alpha import __log
from django.db import connection
from apps.rubicon_v3.__function import __embedding_rerank as embedding_rerank
from apps.rubicon_v3.__function import _62_complement_code_mapping_utils as cm_utils
from apps.rubicon_v3.__function import _64_complement_extended_info_2 as cme_2
from apps.rubicon_v3.__function.definitions import intelligences, sub_intelligences




def gpt_extended(expression, intelligence, country_code, site_cd, message_id):
    error_dict = {}
    extended_gpt_result = []

    df_cm = code_mapping_model(expression, country_code, message_id)

    if df_cm.empty:
        error_dict = [{
            'expression': expression,
            'error_type': 'invalid model name'
        }]
        return error_dict

    cm_mapping_code = (
        df_cm["mapping_code"].dropna().drop_duplicates().tolist()
        if not df_cm.empty
        else None
    )

    cm_dict = {
        "expression": expression,
        "field": 'product_model',
        "operator": 'in',
        "mapping_code": cm_mapping_code,
        "type": df_cm["type"]
    }

    complete_categories = df_cm[
        df_cm["category_lv1"].notna()
        & df_cm["category_lv2"].notna()
        & df_cm["category_lv3"].notna()
    ]

    if not complete_categories.empty:
        cm_dict["category_lv1"] = list(
            set(complete_categories["category_lv1"].values.tolist())
        )
        cm_dict["category_lv2"] = list(
            set(complete_categories["category_lv2"].values.tolist())
        )
        cm_dict["category_lv3"] = list(
            set(complete_categories["category_lv3"].values.tolist())
        )
        cm_dict["type"] = list(
            set(complete_categories["type"].values.tolist())
        )

    l4_check, l4_filters = cm_utils.check_valid_product(expression, cm_dict, country_code)
    if l4_check:
        error_dict = [{
            'expression': expression,
            'error_type': l4_check
        }]
        return error_dict
    
    l4_product_filter = l4_filters.get('product_filter')
    negative_l4_product_filter = l4_filters.get('negative_product_filter')
    if intelligence == 'Product Recommendation':
        recommend_lst = extended_recommend(cm_dict, intelligence, l4_product_filter, country_code, site_cd, negative_l4_product_filter)
        len_info = 0
        if recommend_lst:
            len_info = sum([len(df) for df in recommend_lst])
        extended_gpt_result.extend(recommend_lst)
        if not recommend_lst or len_info < 3:
            code_lst = extended_code(cm_dict, intelligence, l4_product_filter, country_code, site_cd, negative_l4_product_filter)
            extended_gpt_result.extend(code_lst)        
    else:
        code_lst = extended_code(cm_dict, intelligence, l4_product_filter, country_code, site_cd, negative_l4_product_filter)
        extended_gpt_result.extend(code_lst)
    if extended_gpt_result:
        result_dataframe = pd.concat(extended_gpt_result, axis = 0).drop_duplicates(subset=['mapping_code'], keep='first').reset_index(drop=True)
        result_dataframe['id'] = result_dataframe.index
        extended_gpt_result= [result_dataframe]
    
    if l4_product_filter:
        l4_product_filter = [s for s in l4_product_filter if s.isdigit()]
    
    if l4_product_filter:
        for i in range(len(extended_gpt_result)):
            for l4_single_pattern in l4_product_filter:
                extended_gpt_result[i] = extended_gpt_result[i][
                    extended_gpt_result[i]['mapping_code'].str.contains(re.escape(l4_single_pattern), case = False)
                ]
    
    extended_list = []
    for df in extended_gpt_result:
        if df.empty:
            info_filtered = df
        else:
            df_filterd = df.copy()
            # __log.debug(df_filterd['mapping_code'].tolist())
            if set(df_filterd['mapping_code'].tolist()) == set(['갤럭시 S25 울트라', '갤럭시 S25+', '갤럭시 S25']):
                info_filtered = df_filterd.to_dict('records')[:3]
            else:
                info_filtered = df_filterd.to_dict('records')[:3]
        if not df.empty:
            extended_list.extend(info_filtered)
    
    return extended_list

def code_mapping_model(expression, country_code, message_id):
    field = 'product_model' # TODO: product_code가 나올 경우는 있나?
    embedding = list(embedding_rerank.baai_embedding(expression, message_id)[0])
    expression.replace('\\u0027', '\\u0022')
    exact_match_sql = f"""
        SELECT distinct rcm.mapping_code, rcm.field, rcm.expression, rcm.category_lv1, rcm.category_lv2, rcm.category_lv3, rcm.type
        FROM rubicon_v3_complement_code_mapping rcm
        WHERE rcm.active = TRUE
        AND rcm.country_code = '{country_code}'
        AND rcm.field = '{field}'
        AND rcm.expression = '{expression}'
    """
    similarity_sql = f"""SELECT DISTINCT
        rcm.mapping_code,
        rcm.field,
        rcm.expression,
        rcm.category_lv1,
        rcm.category_lv2,
        rcm.category_lv3,
        rcm.type,
        subq.distance
    FROM (
        SELECT DISTINCT
            expression,
            field,
            country_code,
            embedding <=> '{str(embedding)}' AS distance
        FROM rubicon_v3_complement_code_mapping
        WHERE active = TRUE
        AND country_code = '{country_code}'
        AND field = '{field}'
        ORDER BY distance
        LIMIT 10
    ) subq
    JOIN rubicon_v3_complement_code_mapping rcm 
        ON rcm.expression = subq.expression
        AND rcm.active = TRUE
        AND rcm.country_code = subq.country_code
        AND rcm.field = subq.field
    ORDER BY subq.distance
    """

    with connection.cursor() as curs:
        curs.execute(exact_match_sql)
        results = curs.fetchall()
        if results:
            return pd.DataFrame(results, columns=[c.name for c in curs.description])
        # else:
        #     if field == 'product_code':
        #         return pd.DataFrame(columns=['mapping_code', 'field', 'expression', 'category_lv1', 'category_lv2', 'category_lv3', 'type'])
        curs.execute(similarity_sql)
        results = curs.fetchall()

        df = pd.DataFrame(results, columns=[c.name for c in curs.description])

        if not df.empty:
            df_reranked = embedding_rerank.rerank_db_results(
                expression, df, text_column="expression", top_k=12, score_threshold=1 
            )
            if df_reranked.empty:
                return pd.DataFrame(columns=['mapping_code', 'field', 'expression', 'category_lv1', 'category_lv2', 'category_lv3', 'type'])
            else:
                df_reranked = df_reranked.sort_values('reranker_score', ascending=False)
                df_reranked = df_reranked.loc[df_reranked['reranker_score'] == df_reranked['reranker_score'].max()]
                return df_reranked
            
        return pd.DataFrame(columns=['mapping_code', 'field', 'expression', 'category_lv1', 'category_lv2', 'category_lv3', 'type'])

def extended_recommend(cm_dict, intelligence, l4_product_filter, country_code, site_cd, negative_l4_product_filter):
    result_list = []

    category_lv1 = cm_dict.get('category_lv1', "")
    category_lv2 = cm_dict.get('category_lv2', "")
    category_lv3 = cm_dict.get('category_lv3', "")

    category_lv1_placeholder = ", ".join(
                            "'" + _ + "'" for _ in cm_dict.get("category_lv1", "")
                        )
    category_lv2_placeholder = ", ".join(
                    "'" + _ + "'" for _ in cm_dict.get("category_lv2", "")
                )
    category_lv3_placeholder = ", ".join(
                    "'" + _ + "'" for _ in cm_dict.get("category_lv3", "")
                )
    mapping_code_palceholder = ", ".join(
                    "'" + _ + "'" for _ in cm_dict.get("mapping_code", "")
                )

    recommend_table_nm = 'rubicon_data_product_recommend' if country_code == 'KR' else 'rubicon_data_uk_product_order'

    with connection.cursor() as curs:
        if country_code == "KR":
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
                    (SELECT * ,row_number () over (partition by disp_clsf_nm, goods_id order by ctg_rank) as rk from {recommend_table_nm})
                    WHERE site_cd = '{site_cd}'
                    """
            if intelligence == 'Product Recommendation' and country_code == 'KR':
                query += f"and set_tp_cd in ('00', '10')"
            if category_lv1_placeholder and 'NA' not in category_lv1_placeholder:
                query += f"and product_category_lv1 in ({category_lv1_placeholder})"
            if category_lv2_placeholder and 'NA' not in category_lv2_placeholder:
                query += f"and product_category_lv2 in ({category_lv2_placeholder})"
            if category_lv3_placeholder and 'NA' not in category_lv3_placeholder:
                query += f"and product_category_lv3 in ({category_lv3_placeholder})"
            query_2 = query
            query += f"and goods_nm in ({mapping_code_palceholder})"
            query += """
                    and rk = 1
                    order by disp_clsf_nm, ctg_rank
                """
            query_2 += """
                    and rk = 1
                    order by disp_clsf_nm, ctg_rank
                """
        else:
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
                    AND pr.sort_type = 'recommended'
                    """
            if intelligence == 'Product Recommendation' and country_code == 'KR':
                query += f"and pf.set_tp_cd in ('00', '10')"
            if category_lv1_placeholder and 'NA' not in category_lv1_placeholder:
                query += f"and pf.category_lv1 in ({category_lv1_placeholder})"
            if category_lv2_placeholder and 'NA' not in category_lv2_placeholder:
                query += f"and pf.category_lv2 in ({category_lv2_placeholder})"
            if category_lv3_placeholder and 'NA' not in category_lv3_placeholder:
                query += f"and pf.category_lv3 in ({category_lv3_placeholder})"
            query_2 = query
            query += f"and pf.display_name in ({mapping_code_palceholder})"
            query += """
                    order by - sorting_no
                """
            query_2 += """
                    order by - sorting_no
                """
        curs.execute(query)
        result_nm = curs.fetchall()
        if result_nm:
            nm_list = []
            for row in result_nm:
                category_lv1, category_lv2, category_lv3, model_code, goods_nm, id, release_date = row
                product_filter_check = True
                if l4_product_filter:
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
                if negative_l4_product_filter:
                    for negative_l4_single_pattern in negative_l4_product_filter:
                        product_filter_check = product_filter_check and not bool(re.search(re.escape(negative_l4_single_pattern), goods_nm, re.IGNORECASE))
                if product_filter_check:
                    nm_list.append({
                        "country_code": country_code,
                        "mapping_code": goods_nm,
                        "category_lv1": category_lv1,
                        "category_lv2": category_lv2,
                        "category_lv3": category_lv3,
                        "edge": "recommend",
                        "meta": "",
                        "model_code": model_code,
                        "id": id,
                        "release_date": release_date,
                    })
            df_nm = pd.DataFrame(nm_list)
            df_nm['id'] = df_nm['id'].fillna(99999)
            if category_lv3 == 'Moving Style':
                df_nm = df_nm.sort_values('release_date', ascending=False)
                df_nm['id'] = range(len(df_nm))
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
        elif 'e2e' not in cm_dict.get("type", ""):
            curs.execute(query_2)
            result_hnm = curs.fetchall()

            if not result_hnm:
                return []
            else:
                hnm_list = []
                for row in result_hnm:
                    category_lv1, category_lv2, category_lv3, model_code, goods_nm, id, release_date = row
                    product_filter_check = True
                    if country_code == 'KR':
                        is_merchandising = category_lv1 == "MERCHANDISING"
                        is_refrigrator = category_lv1 == "냉장고"
                        is_mobile = category_lv1 == "HHP"
                        is_printer = category_lv3 == "Printer"
                        is_external = (category_lv3 == "External HDD") or (category_lv3 == "External SSD")
                        is_airdresser = category_lv3 in ["Bespoke AirDresser", "AirDresser"]
                        is_serif = category_lv3 == "The Serif"
                        if l4_product_filter:
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
                        if negative_l4_product_filter:
                                for negative_l4_single_pattern in negative_l4_product_filter:
                                    product_filter_check = product_filter_check and not bool(re.search(re.escape(negative_l4_single_pattern), goods_nm, re.IGNORECASE))
                        expression = cme_2.clean_expression_kr(goods_nm, is_merchandising, is_refrigrator, is_mobile, is_printer, is_external, is_airdresser, is_serif)
                        # __log.debug(f"{goods_nm}: {product_filter_check}")
                        # __log.debug(expression)
                        # expression = expression if expression != '갤럭시 S25 울트라' else '갤럭시 S25 Ultra'
                    elif country_code == 'GB':
                        is_ha = category_lv1 == "Home Appliances"
                        is_mobile = category_lv1 == "Mobile"
                        is_printer = category_lv3 == "Printer"
                        is_external = (category_lv3 == "External HDD") or (category_lv3 == "External SSD")
                        is_computer = category_lv1 == 'Computers'
                        if l4_product_filter:
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
                        if negative_l4_product_filter:
                                for negative_l4_single_pattern in negative_l4_product_filter:
                                    product_filter_check = product_filter_check and not bool(re.search(re.escape(negative_l4_single_pattern), goods_nm, re.IGNORECASE))
                        expression = cme_2.clean_expression_uk(goods_nm, model_code, is_ha, is_mobile, is_printer, is_external, is_computer)

                    if product_filter_check:
                        hnm_list.append({
                            "country_code": country_code,
                            "mapping_code": expression,
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
                if category_lv3 == 'Moving Style':
                    df_hnm = df_hnm.sort_values('release_date', ascending=False)
                    df_hnm['id'] = range(len(df_hnm))
                if df_hnm.empty:
                    return []
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
                if hnm_processed.empty:
                    pass
                else:
                    result_list.append(hnm_processed)
    
    return result_list

            

def extended_code(cm_dict, intelligence, l4_product_filter, country_code, site_cd, negative_l4_product_filter):
    result_list = []

    category_lv1 = cm_dict.get('category_lv1', "")
    category_lv2 = cm_dict.get('category_lv2', "")
    category_lv3 = cm_dict.get('category_lv3', "")
    mapping_code = cm_dict.get('mapping_code', "")

    category_lv1_placeholder = ", ".join(
                            "'" + _ + "'" for _ in cm_dict.get("category_lv1", "")
                        )
    category_lv2_placeholder = ", ".join(
                    "'" + _ + "'" for _ in cm_dict.get("category_lv2", "")
                )
    category_lv3_placeholder = ", ".join(
                    "'" + _ + "'" for _ in cm_dict.get("category_lv3", "")
                )
    mapping_code_palceholder = ", ".join(
                    "'" + _ + "'" for _ in cm_dict.get("mapping_code", "")
                )

    full_table_nm = 'rubicon_data_product_category' if country_code == 'KR' else 'rubicon_data_uk_product_spec_basics'

    with connection.cursor() as curs:
        query = f"""
                SELECT
                    {'product_category_lv1' if country_code == 'KR' else 'category_lv1'}, 
                    {'product_category_lv2' if country_code == 'KR' else 'category_lv2'}, 
                    {'product_category_lv3' if country_code == 'KR' else 'category_lv3'}, 
                    {'mdl_code' if country_code == 'KR' else 'model_code'}, 
                    {'goods_nm' if country_code == 'KR' else 'display_name'}, 
                    {'release_date' if country_code == 'KR' else 'creation_date'} as release_date
                FROM {full_table_nm}
                WHERE site_cd = '{site_cd}'
                """
        if intelligence == 'Product Recommendation' and country_code == 'KR':
                query += f"and set_tp_cd in ('00', '10')"
        if category_lv1_placeholder and 'NA' not in category_lv1_placeholder:
            query += f"AND {'product_category_lv1' if country_code == 'KR' else 'category_lv1'} in ({category_lv1_placeholder}) "
        if category_lv2_placeholder and 'NA' not in category_lv2_placeholder:
            query += f"AND {'product_category_lv2' if country_code == 'KR' else 'category_lv2'}  in ({category_lv2_placeholder}) "
        if category_lv3_placeholder and 'NA' not in category_lv3_placeholder:
            query += f"AND {'product_category_lv3' if country_code == 'KR' else 'category_lv3'}  in ({category_lv3_placeholder}) "
        query_2 = query

        query += f"""AND {'goods_nm' if country_code == 'KR' else 'display_name'} in ({mapping_code_palceholder})"""
        
        curs.execute(query)
        result_nm = curs.fetchall()
        if result_nm:
            nm_list = []
            for row in result_nm:
                category_lv1, category_lv2, category_lv3, model_code, goods_nm, release_date = row
                product_filter_check = True
                if l4_product_filter:
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
                if negative_l4_product_filter:
                    for negative_l4_single_pattern in negative_l4_product_filter:
                        product_filter_check = product_filter_check and not bool(re.search(re.escape(negative_l4_single_pattern), goods_nm, re.IGNORECASE))
                if product_filter_check:
                    nm_list.append({
                        "country_code": country_code,
                        "mapping_code": goods_nm,
                        "category_lv1": category_lv1,
                        "category_lv2": category_lv2,
                        "category_lv3": category_lv3,
                        "edge": "recommend",
                        "meta": "",
                        "model_code": model_code,
                        "release_date": release_date
                    })
            df_nm = pd.DataFrame(nm_list)
            nm_processed = (
                    df_nm
                    .drop_duplicates()
                    .pipe(lambda x: x.assign(release_date = x['release_date'].fillna('1000-01-01').astype(str)))
                    .assign(latest_release_date = lambda x: x.groupby(["mapping_code", "category_lv1", "category_lv2", "category_lv3"])['release_date'].transform('max'))
                    .groupby(["mapping_code", "category_lv1", "category_lv2", "category_lv3", "edge", "meta", "latest_release_date"])["model_code"]
                    .agg(list)
                    .reset_index()
                    .sort_values(by = ['latest_release_date', 'mapping_code'], ascending=[False, False])
                    .rename(columns = {'model_code': 'extended_info'})
                )
            result_list.append(nm_processed)
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
                    if country_code == 'KR':
                        is_merchandising = category_lv1 == "MERCHANDISING"
                        is_refrigrator = category_lv1 == "냉장고"
                        is_mobile = category_lv1 == "HHP"
                        is_printer = category_lv3 == "Printer"
                        is_external = (category_lv3 == "External HDD") or (category_lv3 == "External SSD")
                        is_airdresser = category_lv3 in ["Bespoke AirDresser", "AirDresser"]
                        is_serif = category_lv3 == "The Serif"
                        if l4_product_filter:
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
                        expression = cme_2.clean_expression_kr(goods_nm, is_merchandising, is_refrigrator, is_mobile, is_printer, is_external, is_airdresser, is_serif)
                        # negative_l4_product_filter insert 0611
                        if negative_l4_product_filter:
                            for negative_l4_single_pattern in negative_l4_product_filter:
                                product_filter_check = product_filter_check and not bool(re.search(re.escape(negative_l4_single_pattern), goods_nm, re.IGNORECASE))
                        # __log.debug(expression)
                        # expression = expression if expression != '갤럭시 S25 울트라' else '갤럭시 S25 Ultra'
                    elif country_code == 'GB':
                        is_ha = category_lv1 == "Home Appliances"
                        is_mobile = category_lv1 == "Mobile"
                        is_printer = category_lv3 == "Printer"
                        is_external = (category_lv3 == "External HDD") or (category_lv3 == "External SSD")
                        is_computer = category_lv1 == 'Computers'
                        if l4_product_filter:
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
                        if negative_l4_product_filter:
                            for negative_l4_single_pattern in negative_l4_product_filter:
                                product_filter_check = product_filter_check and not bool(re.search(re.escape(negative_l4_single_pattern), goods_nm, re.IGNORECASE))
                        expression = cme_2.clean_expression_uk(goods_nm, model_code, is_ha, is_mobile, is_printer, is_external, is_computer)

                    if product_filter_check:
                        hnm_list.append({
                            "country_code": country_code,
                            "mapping_code": expression,
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
                    return []
                hnm_processed = (
                    df_hnm
                    .drop_duplicates()
                    .pipe(lambda x: x.assign(release_date = x['release_date'].fillna('1000-01-01').astype(str)))
                    .assign(latest_release_date = lambda x: x.groupby(["mapping_code", "category_lv1", "category_lv2", "category_lv3"])['release_date'].transform('max'))
                    .groupby(["mapping_code", "category_lv1", "category_lv2", "category_lv3", "edge", "meta", "latest_release_date"])["model_code"]
                    .agg(list)
                    .reset_index()
                    .sort_values(by = ['latest_release_date', 'mapping_code'], ascending=[False, False])
                    .rename(columns = {'model_code': 'extended_info'})
                )
                if hnm_processed.empty:
                    pass
                else:
                    result_list.append(hnm_processed)
    
    if result_list:
        result_dataframe = pd.concat(result_list, axis = 0).sort_values('latest_release_date', ascending = False).reset_index(drop = True).drop('latest_release_date', axis=1)
        result_list = [result_dataframe]

    return result_list    

if __name__=='__main__':
    start_time = time.time()
    res = gpt_extended('갤럭시 S25', 'Product Description', 'KR', 'B2C', "")
    elapsed_time = time.time() - start_time
    __log.debug(f"gpt extend: {elapsed_time}s")
    __log.debug(res)
    

    
            

        

        
    