# line 2 ~ 7 테스트 시 주석 해제
import sys
sys.path.append('/www/alpha/')
import os
import re
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'alpha.settings')

import time
import datetime
from copy import deepcopy
import pandas as pd
import ast
from word2number import w2n
from alpha import __log
from django.db import connection
from apps.rubicon_v3.__function import __embedding_rerank as embedding_rerank
from apps.rubicon_v3.__function import _62_complement_validation_kr as cvk
from apps.rubicon_v3.__function import _62_complement_code_mapping_utils as cm_utils
from apps.rubicon_v3.__function import _64_complement_extended_info_2 as cme_2
from apps.rubicon_v3.__function import _84_product_extraction as product_extraction
from apps.rubicon_v3.__function.definitions import intelligences, sub_intelligences

def extend_request_info(extend_req, intelligence, country_code, site_cd, n_list, message_id):
    # start_time = time.time()
    extend_request_list = extend_req.get('product_extraction') # list
    # n_list = 3 if len(extend_request_list) == 1 else 1
    error_dict = {}
    extended_list = []

    for d in extend_request_list:
        extended_gpt_result = []
        model_expression = d.get('product_model')
        code_expression = d.get('product_code')
        spec_expression = d.get('product_spec')
        if spec_expression:
            acr_flag = bool(re.match(r'^\d+\.\d/\d+\.\d\s*(M²|㎡)$', spec_expression))
            # acr_match = re.match(r'^(\d+\.\d)/\d+\.\d\s*(M²|㎡)$', spec_expression)
            if acr_flag and model_expression:
                spec_expression = spec_expression.replace('M²', '㎡')
                model_expression = model_expression + ' ' + spec_expression
                spec_expression = None
                # acr_number = acr_match.group(1)
                # acr_unit = acr_match.group(2).replace('M²', '㎡')
                # spec_expression = f"{acr_number} {acr_unit}"
        # __log.debug(model_expression)
        if code_expression == 'None':
            code_expression = None
        if spec_expression == 'None':
            spec_expression = None
        if not code_expression:
            cm_dict, error_dict, l4_product_filter, negative_l4_product_filter = code_mapping_model(model_expression, country_code, site_cd, message_id)
        else:
            cm_dict, error_dict, l4_product_filter, negative_l4_product_filter = code_mapping_code(code_expression, country_code, site_cd, message_id)
        # elapsed_time = time.time() - start_time
        # __log.debug(f"model code mapping: {elapsed_time}s")
        if spec_expression and re.match(r'^(\d{1,2}\.\d\.\d) (채널|ch)$', spec_expression):
            spec_expression = re.match(r'^(\d{1,2}\.\d\.\d) (채널|ch)$', spec_expression).group(1)
        if spec_expression and cm_dict:

            cm_dict, err_spec = product_validity_check(cm_dict, spec_expression, intelligence, country_code, site_cd)
        # elapsed_time = time.time() - start_time
        # __log.debug(f"spec code mapping: {elapsed_time}s")

        if not cm_dict:
            continue

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
        # elapsed_time = time.time() - start_time
        # __log.debug(f"get extended: {elapsed_time}s")
        if l4_product_filter:
            l4_product_filter = [s for s in l4_product_filter if s.isdigit()]
        
        if l4_product_filter:
            for i in range(len(extended_gpt_result)):
                for l4_single_pattern in l4_product_filter:
                    extended_gpt_result[i] = extended_gpt_result[i][
                        extended_gpt_result[i]['mapping_code'].str.contains(re.escape(l4_single_pattern), case = False)
                    ]
        for df in extended_gpt_result:
            if df.empty:
                info_filtered = df
            else:
                df_filterd = df.copy()
                # __log.debug(df_filterd['mapping_code'].tolist())
                if set(df_filterd['mapping_code'].tolist()) == set(['갤럭시 S25 울트라', '갤럭시 S25+', '갤럭시 S25']):
                    info_filtered = df_filterd.to_dict('records')[:n_list]
                else:
                    info_filtered = df_filterd.to_dict('records')[:n_list]
            if not df.empty:
                extended_list.extend(info_filtered)
    # elapsed_time = time.time() - start_time
    # __log.debug(f"end: {elapsed_time}s")
    
    extended_list = get_rank(extended_list, intelligence, country_code, site_cd)

    return extended_list

def code_mapping_code(expression, country_code, site_cd, message_id):
    field = 'product_model' # TODO: product_code가 나올 경우는 있나?
    embedding = list(embedding_rerank.baai_embedding(expression, message_id)[0])
    expression.replace('\\u0027', '\\u0022')
    res_df = pd.DataFrame(columns=['mapping_code', 'field', 'expression', 'category_lv1', 'category_lv2', 'category_lv3', 'type'])
    error_dict = []

    exact_match_sql = f"""
        SELECT distinct rcm.mapping_code, rcm.field, rcm.expression, rcm.category_lv1, rcm.category_lv2, rcm.category_lv3, rcm.type
        FROM rubicon_v3_complement_code_mapping rcm
        WHERE rcm.active = TRUE
        AND rcm.country_code = '{country_code}'
        AND rcm.field = '{field}'
        AND rcm.site_cd = '{site_cd}'
        AND rcm.expression = '{expression}'
    """
    with connection.cursor() as curs:
        curs.execute(exact_match_sql)
        results = curs.fetchall()
        if results:
            res_df = pd.DataFrame(results, columns=[c.name for c in curs.description])
        else:
            error_dict = [{
            'expression': expression,
            'error_type': 'invalid model code'
        }]
            return {}, error_dict, [], []

    cm_mapping_code = (
        res_df["mapping_code"].dropna().drop_duplicates().tolist()
        if not res_df.empty
        else None
    )

    cm_dict = {
        "expression": expression,
        "field": 'product_model',
        "operator": 'in',
        "mapping_code": cm_mapping_code,
        "type": res_df["type"]
    }

    complete_categories = res_df[
        res_df["category_lv1"].notna()
        & res_df["category_lv2"].notna()
        & res_df["category_lv3"].notna()
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

    return cm_dict, error_dict, [], []




def code_mapping_model(expression, country_code, site_cd, message_id):
    field = 'product_model' # TODO: product_code가 나올 경우는 있나?
    embedding = list(embedding_rerank.baai_embedding(expression, message_id)[0])
    expression.replace('\\u0027', '\\u0022')
    res_df = pd.DataFrame(columns=['mapping_code', 'field', 'expression', 'category_lv1', 'category_lv2', 'category_lv3', 'type'])
    error_dict = []

    # Initialize empty DataFrame for reranked results
    df_reranked = pd.DataFrame()

    exact_match_sql = f"""
        SELECT distinct rcm.mapping_code, rcm.field, rcm.expression, rcm.category_lv1, rcm.category_lv2, rcm.category_lv3, rcm.type, rcm.site_cd
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
    ORDER BY subq.distance
    """

    with connection.cursor() as curs:
        curs.execute(exact_match_sql)
        results = curs.fetchall()
        if results:
            result_df = pd.DataFrame(results, columns=[c.name for c in curs.description])
            df_reranked = result_df[result_df['site_cd'] == site_cd].drop('site_cd', axis = 1)
        else:
            curs.execute(similarity_sql)
            results = curs.fetchall()

            df = pd.DataFrame(results, columns=[c.name for c in curs.description])
            if not df.empty:
                df = df[df['site_cd'] == site_cd]
                if df.empty:
                    df_reranked = pd.DataFrame(columns=['mapping_code', 'field', 'expression', 'category_lv1', 'category_lv2', 'category_lv3', 'type'])
                
                else:
                    df_reranked = embedding_rerank.rerank_db_results(
                        expression, df, text_column="expression", top_k=18, score_threshold=1 
                    )
                    if df_reranked.empty:
                        df_reranked = pd.DataFrame(columns=['mapping_code', 'field', 'expression', 'category_lv1', 'category_lv2', 'category_lv3', 'type'])
                    else:
                        df_reranked = df_reranked.sort_values('reranker_score', ascending=False)
                        df_reranked = df_reranked.loc[df_reranked['reranker_score'] == df_reranked['reranker_score'].max()]
                # res_df = df_reranked
            else:
                df_reranked = pd.DataFrame(columns=['mapping_code', 'field', 'expression', 'category_lv1', 'category_lv2', 'category_lv3', 'type'])

            
    if df_reranked.empty:
        error_dict = [{
            'expression': expression,
            'error_type': 'invalid model name'
        }]
        return {}, error_dict, [], []

    cm_mapping_code = (
        df_reranked["mapping_code"].dropna().drop_duplicates().tolist()
        if not df_reranked.empty
        else None
    )

    cm_dict = {
        "expression": expression,
        "field": 'product_model',
        "operator": 'in',
        "mapping_code": cm_mapping_code,
        "type": df_reranked["type"]
    }

    complete_categories = df_reranked[
        df_reranked["category_lv1"].notna()
        & df_reranked["category_lv2"].notna()
        & df_reranked["category_lv3"].notna()
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
        return {}, error_dict, [], []
    
    l4_product_filter = l4_filters.get('product_filter')
    negative_l4_product_filter = l4_filters.get('negative_product_filter')

    return cm_dict, error_dict, l4_product_filter, negative_l4_product_filter
    
def product_validity_check(cm_dict, spec_expression, intelligence, country_code, site_cd):
    purchasable_key = True
    product_category_lv1 = cm_dict.get('category_lv1')
    product_category_lv2 = cm_dict.get('category_lv2')
    product_category_lv3 = cm_dict.get('category_lv3')
    result_df = pd.DataFrame()
    err_spec_out = None
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
        spec_sql = f"""
            SELECT category_lv1, category_lv2, category_lv3, goods_nm, mdl_code, disp_nm1, disp_nm2, value
            FROM rubicon_v3_complement_product_spec
            WHERE site_cd = '{site_cd}'
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
        if df.empty:
            result_df = pd.DataFrame()
        # __log.debug(spec_sql)
        if 'COOKING GOODS' in product_category_lv1:
            df['value'] = df['value'].astype(str).str.replace(r'\s*\([^)]*\)', '', regex=True)
        df, err_spec, _ = cvk.extract_and_find_closest(df, spec_expression, 'in', product_category_lv1, product_category_lv2, product_category_lv3, country_code, True)
        if err_spec:
            err_spec_out = err_spec
        # __log.debug(f'code_retriever: extract_and_find_closest: {round(elapsed_time, 4)}')

        if df.empty:
            result_df = pd.DataFrame()
        else:
            df = df[['category_lv1', 'category_lv2', 'category_lv3', 'goods_nm', 'mdl_code', 'value']].drop_duplicates()
            result_df = df

    
    if not result_df.empty:
        option_code_mapping_results = {
            'expression': cm_dict.get('expression'),
            'field': 'product_model',  
            'mapping_code': result_df['goods_nm'].dropna().drop_duplicates().tolist() if (result_df is not None and not result_df.empty) else None,
            'mdl_code': result_df['mdl_code'].dropna().drop_duplicates().tolist() if (result_df is not None and not result_df.empty) else None,
            'values': (
                list(dict.fromkeys([v for col in [c for c in result_df.columns if c.startswith('value')] 
                                for v in result_df[col].dropna().drop_duplicates().tolist()]))
                if (result_df is not None and not result_df.empty)
                else None
            )
        }
    else:
        option_code_mapping_results = None

    if result_df is not None and not result_df.empty:
        # Check if we have complete category information (all levels non-null)
        complete_categories = result_df[
            result_df['category_lv1'].notna() & 
            result_df['category_lv2'].notna() & 
            result_df['category_lv3'].notna()
        ]
        
        if not complete_categories.empty:            
            # Add each category level as a separate ner item
            option_code_mapping_results["category_lv1"] = list(set(complete_categories['category_lv1'].values.tolist()))
            option_code_mapping_results["category_lv2"] = list(set(complete_categories['category_lv2'].values.tolist()))
            option_code_mapping_results["category_lv3"] = list(set(complete_categories['category_lv3'].values.tolist()))

    if option_code_mapping_results is None:
        return None, err_spec_out

    if option_code_mapping_results.get('mapping_code'):
        cm_dict['option'] = {
            "expression": option_code_mapping_results['expression'],
            "field": option_code_mapping_results['field'],
            "mapping_code": option_code_mapping_results['values']
        }
        # item['original_expression'] = item['expression']
        cm_dict["mdl_code"] = option_code_mapping_results.get("mdl_code","")
        cm_dict['mapping_code'] = option_code_mapping_results['mapping_code']
        cm_dict['category_lv1'] = option_code_mapping_results.get('category_lv1')
        cm_dict['category_lv2'] = option_code_mapping_results.get('category_lv2')
        cm_dict['category_lv3'] = option_code_mapping_results.get('category_lv3')
    return cm_dict, err_spec_out

def extended_recommend(cm_dict, intelligence, l4_product_filter, country_code, site_cd, negative_l4_product_filter):
    result_list = []

    category_lv1 = cm_dict.get('category_lv1', "")
    category_lv2 = cm_dict.get('category_lv2', "")
    category_lv3 = cm_dict.get('category_lv3', "")
    mdl_cd = cm_dict.get('mdl_code', "")

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
    mdl_placeholder = ", ".join(
                            "'" + _ + "'" for _ in mdl_cd
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
            if mdl_placeholder:
                query += f" and mdl_code in ({mdl_placeholder})"
            query_2 = query
            # query += f"and goods_nm in ({mapping_code_palceholder})"
            query += f"and (goods_nm in ({mapping_code_palceholder}) or mdl_code in ({mapping_code_palceholder}))"
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
            # query += f"and pf.display_name in ({mapping_code_palceholder})"
            query += f"and (pf.display_name in ({mapping_code_palceholder}) or pr.representative_model in ({mapping_code_palceholder}))"
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
            if df_nm.empty:
                return []
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
                if df_hnm.empty:
                    return []
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
    mdl_cd = cm_dict.get('mdl_code', "")

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
    mdl_placeholder = ", ".join(
                            "'" + _ + "'" for _ in mdl_cd
                        )

    full_table_nm = 'rubicon_data_product_category' if country_code == 'KR' else 'rubicon_data_uk_product_spec_basics'

    with connection.cursor() as curs:
        if country_code == 'KR':
            query = f"""
                        SELECT
                            product_category_lv1, 
                            product_category_lv2, 
                            product_category_lv3, 
                            mdl_code, 
                            goods_nm, 
                            release_date,
                            CASE
                                WHEN goods_stat_cd = '30' THEN 'PURCHASABLE'
                                WHEN goods_stat_cd = '20' THEN NULL
                                else NULL
                            END AS purchasable
                        FROM {full_table_nm}
                        WHERE site_cd = '{site_cd}'
                        AND show_yn = 'Y' 
                        AND goods_stat_cd in ('20', '30')
                        """
        else:  # GB
            query = f"""
                        SELECT
                            t.category_lv1, 
                            t.category_lv2, 
                            t.category_lv3, 
                            t.model_code, 
                            t.display_name, 
                            t.creation_date as release_date,
                            mp.salesstatus as purchasable
                        FROM {full_table_nm} t
                        INNER JOIN rubicon_data_uk_model_price mp ON t.model_code = mp.model_code
                        WHERE t.site_cd = '{site_cd}'
                        AND t.display = 'yes'
                        """

        if intelligence == 'Product Recommendation' and country_code == 'KR':
            query += f"and set_tp_cd in ('00', '10')"

        if category_lv1_placeholder and 'NA' not in category_lv1_placeholder:
            query += f"AND {'product_category_lv1' if country_code == 'KR' else 't.category_lv1'} in ({category_lv1_placeholder}) "

        if category_lv2_placeholder and 'NA' not in category_lv2_placeholder:
            query += f"AND {'product_category_lv2' if country_code == 'KR' else 't.category_lv2'}  in ({category_lv2_placeholder}) "

        if category_lv3_placeholder and 'NA' not in category_lv3_placeholder:
            query += f"AND {'product_category_lv3' if country_code == 'KR' else 't.category_lv3'}  in ({category_lv3_placeholder}) "

        if mdl_placeholder:
            query += f"AND {'mdl_code' if country_code == 'KR' else 't.model_code'} in ({mdl_placeholder})"

        query_2 = query

        query += f"""AND ({'goods_nm' if country_code == 'KR' else 't.display_name'} in ({mapping_code_palceholder}) 
                                OR {'mdl_code' if country_code == 'KR' else 't.model_code'} in ({mapping_code_palceholder}))"""
        # __log.debug(query)
        curs.execute(query)
        result_nm = curs.fetchall()
        if result_nm:
            nm_list = []
            for row in result_nm:
                category_lv1, category_lv2, category_lv3, model_code, goods_nm, release_date, purchasable = row
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
                        "release_date": release_date,
                        "purchasable": purchasable
                    })
            df_nm = pd.DataFrame(nm_list)
            if df_nm.empty:
                return []
            if 'PURCHASABLE' in df_nm['purchasable'].unique():
                df_nm = df_nm[df_nm['purchasable'] == 'PURCHASABLE']
            df_nm = df_nm.drop('purchasable', axis = 1)
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
                    category_lv1, category_lv2, category_lv3, model_code, goods_nm, release_date, purchasable = row
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
                            "release_date": release_date,
                            "purchasable": purchasable
                        })
                df_hnm = pd.DataFrame(hnm_list)
                if df_hnm.empty:
                    return []
                if 'PURCHASABLE' in df_hnm['purchasable'].unique():
                    df_hnm = df_hnm[df_hnm['purchasable'] == 'PURCHASABLE']
                df_hnm = df_hnm.drop('purchasable', axis = 1)
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

def get_rank(extended_list, intelligence, country_code, site_cd):
    recommend_table_nm = 'rubicon_data_product_recommend' if country_code == 'KR' else 'rubicon_data_uk_product_order'
    full_table_nm = 'rubicon_data_product_category' if country_code == 'KR' else 'rubicon_data_uk_product_spec_basics'
    rank_l = []
    release_l = []
    not_l = []
    df_l = []
    df_ord = pd.DataFrame()
    with connection.cursor() as curs:
        for d in extended_list:
            mdl_placeholder = ", ".join(
                        "'" + _ + "'" for _ in d.get('extended_info')
                    )
            if country_code == 'KR':
                query = f"""
                        SELECT 
                            a.product_category_lv1,
                            a.product_category_lv2,
                            a.product_category_lv3,
                            a.mdl_code,
                            a.goods_nm,
                            a.id as ids,
                            a.release_date
                        FROM
                        (SELECT * ,row_number () over (partition by disp_clsf_nm, goods_id order by ctg_rank) as rk from {recommend_table_nm}) a
                        INNER JOIN rubicon_data_product_category b ON a.mdl_code = b.mdl_code
                        WHERE a.site_cd = '{site_cd}' and a.mdl_code in ({mdl_placeholder})
                        """
                query += "and a.set_tp_cd in ('00', '10')"
                query += """
                            and a.rk = 1
                            order by a.disp_clsf_nm, a.ctg_rank
                            """
                # print(query)
            elif country_code == 'GB':
                query = f"""
                       SELECT DISTINCT
                           pf.category_lv1,
                           pf.category_lv2,
                           pf.category_lv3,
                           pr.representative_model,
                           pf.display_name,
                           -pr.sorting_no as ids,
                           pf.launch_date
                       FROM
                       {recommend_table_nm} pr
                       inner join rubicon_data_uk_product_filter pf on pr.representative_model = pf.model_code and pr.site_cd = pf.site_cd
                       inner join rubicon_data_uk_model_price mp on pf.model_code = mp.model_code
                       WHERE pf.site_cd = '{site_cd}'
                       AND pr.sort_type = 'recommended' 
                       AND pf.model_code in ({mdl_placeholder})
                       AND mp.salesstatus = 'PURCHASABLE'
                       ORDER BY - sorting_no
                       """
            curs.execute(query)
            result = curs.fetchall()
            if result:
                res_df = pd.DataFrame(result, columns=[c.name for c in curs.description])
                min_id = min(res_df['ids'])
                rank_l.append({
                    'mapping_code': d.get('mapping_code'),
                    'ord': min_id
                })
            else:
                if country_code == 'KR':
                    query = f"""
                                        SELECT
                                            product_category_lv1, 
                                            product_category_lv2, 
                                            product_category_lv3, 
                                            mdl_code, 
                                            goods_nm, 
                                            release_date
                                        FROM {full_table_nm}
                                        WHERE site_cd = '{site_cd}'
                                        """
                    query += f"and set_tp_cd in ('00', '10')"
                    query += f"AND mdl_code in ({mdl_placeholder})"
                    # __log.debug(query)
                    
                else:  # country_code == 'GB'
                    query = f"""
                                        SELECT
                                            t.category_lv1, 
                                            t.category_lv2, 
                                            t.category_lv3, 
                                            t.model_code, 
                                            t.display_name, 
                                            t.creation_date as release_date
                                        FROM {full_table_nm} t
                                        INNER JOIN rubicon_data_uk_model_price mp ON t.model_code = mp.model_code
                                        WHERE t.site_cd = '{site_cd}'
                                        AND mp.salesstatus = 'PURCHASABLE'
                                        AND t.model_code in ({mdl_placeholder})
                                        """

                    query += "ORDER BY release_date DESC"
                curs.execute(query)
                result = curs.fetchall()
                if result:
                    res_df = pd.DataFrame(result, columns=[c.name for c in curs.description])
                    if not res_df.empty and res_df['release_date'].isnull().any():
                        res_df['release_date'] = res_df['release_date'].fillna(datetime.date(1000,1,1))

                    recent_date = max(res_df['release_date'])
                    release_l.append({
                        'mapping_code': d.get('mapping_code'),
                        'ord': recent_date
                    })
                else:
                    not_l.append({
                        'mapping_code': d.get('mapping_code'),
                        'ord': 0
                    })
        
        max_ctg = None
        if rank_l:
            rank_df = pd.DataFrame(rank_l).sort_values(by = ['ord'], ascending = [False]).reset_index(drop = True)
            rank_df['order'] = rank_df.index
            max_ctg = max(rank_df['order']) + 1
            df_l.append(rank_df)
        
        if release_l:
            release_df = pd.DataFrame(release_l).sort_values(by = ['ord'], ascending = [False]).reset_index(drop = True)
            release_df['order'] = release_df.index
            if max_ctg:
                release_df['order'] = release_df['order'] + max_ctg
            max_ctg = max(release_df['order']) + 1
            df_l.append(release_df)
        
        if not_l:
            not_df = pd.DataFrame(not_l)
            not_df['order'] = not_df.index
            if max_ctg:
                not_df['order'] = not_df['order'] + max_ctg
            df_l.append(not_df)
        
        if df_l:
            df_ord = pd.concat(df_l)

        if not df_ord.empty:
            for i in range(len(extended_list)):
                new_d = extended_list[i]
                new_d['id'] = min(df_ord[df_ord['mapping_code'] == new_d.get('mapping_code')]['order'])
                new_d.pop('min_id', 'None')
                extended_list[i] = new_d
        
        return extended_list

        

        

    









if __name__=='__main__':
    django.setup()
    res = {'product_extraction': [{'product_model': 'AI 무풍 갤러리', 'product_code': None, 'product_spec': None}, {'product_model': 'AI 무풍 클래식', 'product_code': None, 'product_spec': None}, {'product_model': 'Q9000', 'product_code': None, 'product_spec': None}]}
    res = {"product_extraction": [{'product_model': 'Series 9 Washing Machine', 'product_code': None, 'product_spec': None}, {'product_model': 'Series 6 Washing Machine', 'product_code': None, 'product_spec': None}]}
    start_time = time.time()
    res2 = extend_request_info(res, intelligence=None, country_code='KR', site_cd='B2C', n_list=1, message_id='test')
    elapsed_time = time.time() - start_time
    __log.debug(f"extend request info elapsed time: {elapsed_time} s")
    __log.debug(res2)