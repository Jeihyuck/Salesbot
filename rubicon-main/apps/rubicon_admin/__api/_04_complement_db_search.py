# line 2 ~ 7 테스트 시 주석 해제
import sys
sys.path.append('/www/alpha/')
import os
import re
import itertools
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'alpha.settings')
django.setup()

import time
from copy import deepcopy
import pandas as pd
from functools import reduce
from alpha import __log
from django.db import connection
from django.db.models import F, Q

from apps.rubicon_v3.models import Complement_Code_Mapping
from apps.rubicon_v3.__function import _61_complement_code_mapping as ccm
from apps.rubicon_v3.__function import _64_complement_extended_info_2 as cei
from apps.rubicon_v3.__function import _65_complement_price as price_check
from apps.rubicon_v3.__function import _66_complement_promotion as promotion
from apps.rubicon_v3.__function.definitions import intelligences, sub_intelligences



pc_query = """
SELECT product_category_lv1, product_category_lv2, product_category_lv3, mdl_code, goods_nm, release_date, goods_stat_cd, show_yn, set_tp_cd, site_cd
FROM rubicon_data_product_category 
WHERE product_category_lv1 IN ('HHP')
AND product_category_lv2 IN ('NEW RADIO MOBILE (5G SMARTPHONE)')
AND product_category_lv3 IN ('Galaxy Z Fold7', 'Galaxy Z Flip7')
"""

pf_query = """
SELECT DISTINCT product_category_lv1, product_category_lv2, product_category_lv3, mdl_code, goods_nm, release_date, set_tp_cd, site_cd
FROM rubicon_data_product_filter 
WHERE product_category_lv1 IN ('HHP')
AND product_category_lv2 IN ('NEW RADIO MOBILE (5G SMARTPHONE)')
AND product_category_lv3 IN ('Galaxy Z Fold7', 'Galaxy Z Flip7')
"""

pr_query = """
SELECT DISTINCT product_category_lv1, product_category_lv2, product_category_lv3, mdl_code, goods_nm, sale_price, ctg_rank, release_date, set_tp_cd, site_cd, sorting_type
FROM rubicon_data_product_recommend
WHERE product_category_lv1 IN ('HHP')
AND product_category_lv2 IN ('NEW RADIO MOBILE (5G SMARTPHONE)')
AND product_category_lv3 IN ('Galaxy Z Fold7', 'Galaxy Z Flip7')
"""

cps_query = """
SELECT DISTINCT category_lv1, category_lv2, category_lv3, goods_nm, mdl_code, country_code, site_cd, on_sale 
FROM rubicon_v3_complement_product_spec
WHERE category_lv1 IN ('HHP')
AND category_lv2 IN ('NEW RADIO MOBILE (5G SMARTPHONE)')
AND category_lv3 IN ('Galaxy Z Fold7', 'Galaxy Z Flip7')
"""
def complement_check_db(request_dict):
    # __log.debug(request_dict)
    no_model_flag = False
    if 'model_code' not in request_dict['query'] and 'embeddingSearch' not in request_dict['query']:
        no_model_flag = True
    if 'table' in request_dict['query'] and request_dict['query']['table']:
        search_table = request_dict['query']['table']
    else:
        search_table = 'rubicon_data_product_category'
    if 'country_code' in request_dict['query'] and request_dict['query']['country_code']:
        country_code = request_dict['query']['country_code']
    else:
        country_code = 'KR'
    if search_table in [
        "rubicon_data_product_category", 
        "rubicon_data_product_filter", 
        "rubicon_data_product_recommend",
        "rubicon_v3_complement_product_spec"]:
        total_count_query = f"SELECT count(*) FROM {search_table}"
    else:
        total_count_query = ""
    
    if country_code == 'KR':
        if search_table == 'rubicon_data_product_category':
            query = f"""
            SELECT 
                '{country_code}' as country_code,
                product_category_lv1 as category_lv1, 
                product_category_lv2 as category_lv2, 
                product_category_lv3 as category_lv3, 
                mdl_code, 
                goods_nm, 
                release_date, 
                goods_stat_cd, 
                show_yn, 
                set_tp_cd, 
                site_cd,
                '-' as sale_price,
                '-' as ctg_rank,
                '-' as sorting_type,
                '-' as on_sale
            FROM rubicon_data_product_category 
            WHERE 1=1
            """
            c1 = "product_category_lv1"
            c2 = "product_category_lv2"
            c3 = "product_category_lv3"
        elif search_table == "rubicon_data_product_filter":
            query = f"""
            SELECT DISTINCT 
                '{country_code}' as country_code,
                product_category_lv1 as category_lv1, 
                product_category_lv2 as category_lv2, 
                product_category_lv3 as category_lv3, 
                mdl_code, 
                goods_nm, 
                release_date, 
                set_tp_cd, 
                site_cd,
                '-' as sale_price,
                '-' as ctg_rank,
                '-' as sorting_type,
                '-' as on_sale
            FROM rubicon_data_product_filter 
            WHERE 1=1
            """
            c1 = "product_category_lv1"
            c2 = "product_category_lv2"
            c3 = "product_category_lv3"
        elif search_table == "rubicon_data_product_recommend":
            query = f"""
            SELECT DISTINCT 
                '{country_code}' as country_code,
                product_category_lv1 as category_lv1, 
                product_category_lv2 as category_lv2, 
                product_category_lv3 as category_lv3, 
                mdl_code, 
                goods_nm, 
                sale_price, 
                ctg_rank, 
                release_date, 
                set_tp_cd, 
                site_cd, 
                sorting_type,
                '-' as goods_stat_cd,
                '-' as show_yn,
                '-' as on_sale
            FROM rubicon_data_product_recommend
            WHERE 1=1
            """
            c1 = "product_category_lv1"
            c2 = "product_category_lv2"
            c3 = "product_category_lv3"
        elif search_table == "rubicon_v3_complement_product_spec":
            query = """
            SELECT DISTINCT 
            category_lv1, 
            category_lv2, 
            category_lv3, 
            goods_nm, 
            mdl_code, 
            country_code, 
            site_cd, 
            on_sale,
            '-' as release_date,
            '-' as goods_stat_cd,
            '-' as show_yn,
            '-' as set_tp_cd,
            '-' as sale_price,
            '-' as ctg_rank,
            '-' as sorting_type
            FROM rubicon_v3_complement_product_spec
            WHERE 1=1
            """
            c1 = "category_lv1"
            c2 = "category_lv2"
            c3 = "category_lv3"
        else:
            return True, [], [{'itemCount': 0}], None
    elif country_code == 'GB':
        if search_table == 'rubicon_data_uk_product_spec_basics':
            query = f"""
            SELECT DISTINCT 
                '{country_code}' as country_code,
                category_lv1, 
                category_lv2, 
                category_lv3, 
                model_code as mdl_code, 
                display_name as goods_nm, 
                creation_date as release_date, 
                site_cd,
                display as show_yn,
                '-'  as goods_stat_cd,
                '-' as set_tp_cd, 
                '-' as sale_price,
                '-' as ctg_rank,
                '-' as sorting_type,
                '-' as on_sale  
            FROM rubicon_data_uk_product_spec_basics 
            WHERE 1=1
            """
            c1 = "category_lv1"
            c2 = "category_lv2"
            c3 = "category_lv3"
        elif search_table == 'rubicon_data_uk_product_filter':
            query = f"""
            SELECT DISTINCT 
                '{country_code}' as country_code,
                category_lv1, 
                category_lv2, 
                category_lv3, 
                model_code as mdl_code, 
                display_name as goods_nm, 
                launch_date as release_date, 
                site_cd,
                '-' as set_tp_cd, 
                '-' as sale_price,
                '-' as ctg_rank,
                '-' as sorting_type,
                '-' as on_sale  
            FROM rubicon_data_uk_product_filter 
            WHERE 1=1
            """
            c1 = "category_lv1"
            c2 = "category_lv2"
            c3 = "category_lv3"
        elif search_table == 'rubicon_data_uk_product_order':
            query = f"""
            SELECT DISTINCT 
                '{country_code}' as country_code,
                category_lv1, 
                category_lv2, 
                category_lv3, 
                representative_model as mdl_code, 
                marketing_name as goods_nm, 
                '-' as sale_price, 
                sorting_no as ctg_rank, 
                launch_date as release_date, 
                '-' as set_tp_cd, 
                site_cd, 
                sort_type as sorting_type,
                '-' as goods_stat_cd,
                '-' as show_yn,
                '-' as on_sale
            FROM rubicon_data_uk_product_order
            WHERE 1=1
            """
            c1 = "category_lv1"
            c2 = "category_lv2"
            c3 = "category_lv3"
        elif search_table == "rubicon_v3_complement_product_spec":
            query = """
            SELECT DISTINCT 
            category_lv1, 
            category_lv2, 
            category_lv3, 
            goods_nm, 
            mdl_code, 
            country_code, 
            site_cd, 
            on_sale,
            '-' as release_date,
            '-' as goods_stat_cd,
            '-' as show_yn,
            '-' as set_tp_cd,
            '-' as sale_price,
            '-' as ctg_rank,
            '-' as sorting_type
            FROM rubicon_v3_complement_product_spec
            WHERE 1=1
            """
            c1 = "category_lv1"
            c2 = "category_lv2"
            c3 = "category_lv3"
        else:
            return True, [], [{'itemCount': 0}], None


    if not no_model_flag:
        model_codes = get_model_codes(request_dict)
    else:
        model_codes = []
    mdl_placeholder = ", ".join(
        "'" + _ + "'" for _ in model_codes
    )
    if not mdl_placeholder and not no_model_flag:
        return True, [], [{'itemCount':0}], None
    category_lv1 = []
    category_lv2 = []
    category_lv3 = []
    category_lv1_placeholder = ''
    category_lv2_placeholder = ''
    category_lv3_placeholder = ''

    if 'category_lv1' in request_dict['query'] and request_dict['query']['category_lv1']:
        category_lv1 = request_dict['query']['category_lv1']
    if 'category_lv2' in request_dict['query'] and request_dict['query']['category_lv2']:
        category_lv2 = request_dict['query']['category_lv2']
    if 'category_lv3' in request_dict['query'] and request_dict['query']['category_lv3']:
        category_lv3 = request_dict['query']['category_lv3']
    if category_lv1:
        category_lv1_placeholder = ", ".join(
                        "'" + _ + "'" for _ in [category_lv1]
                    )
    if category_lv2:
        category_lv2_placeholder = ", ".join(
                        "'" + _ + "'" for _ in [category_lv2]
                    )
    if category_lv3:
        category_lv3_placeholder = ", ".join(
                        "'" + _ + "'" for _ in [category_lv3]
                    )
    mdl_field = 'mdl_code' if (country_code == 'KR' or search_table == 'rubicon_v3_complement_product_spec') else ('model_code' if search_table != 'rubicon_data_uk_product_order' else 'representative_model')
    if not no_model_flag:
        query = query + f"AND {mdl_field} in ({mdl_placeholder})"
    if category_lv1_placeholder:
        query += f"""
            AND {c1} in ({category_lv1_placeholder})"""
    if category_lv2_placeholder:
        query += f"""
            AND {c2} in ({category_lv2_placeholder})"""
    if category_lv3_placeholder:
        query += f"""
            AND {c3} in ({category_lv3_placeholder})"""
        
    # __log.debug(query)
    with connection.cursor() as curs:
        if total_count_query:
            curs.execute(total_count_query)
            total_count = curs.fetchall()[0][0]
        else:
            total_count = None

        curs.execute(query)
        result = curs.fetchall()

        page_data = []
        key_list = [c.name for c in curs.description]
        for row in result:
            row_item = {}
            for index, key in enumerate(key_list):
                row_item[key] = row[index]
            page_data.append(row_item)

    if len(page_data) == 0:
        return True, [], [{'itemCount': 0}], None
    else:

        item_count = len(page_data)
        page = int(request_dict['paging']['page'])
        items_per_page = int(request_dict['paging']['itemsPerPage'])
        start_index = (page - 1) * items_per_page
        end_index = start_index + items_per_page
        page_data = page_data[start_index:end_index]

        return True, page_data, [{'itemCount': item_count}], None


def get_model_codes(request_dict):
    expression = None
    mdl_codes = []
    if 'country_code' in request_dict['query']:
        country_code = request_dict['query']['country_code']
    else:
        country_code = 'KR'
    
    if 'site_cd' in request_dict['query']:
        site_cd = request_dict['query']['site_cd']
    else:
        site_cd = 'B2C'

    if 'model_code' in request_dict['query'] and request_dict.get('query', {}).get('model_code'):
        expression = request_dict['query']['model_code']
        original_query = expression
        original_ner = [
            {
                'expression': expression, 
                'field': 'product_code',
                'operator': 'in'
            }
        ]
        new_ner = [
            {
                'expression': expression, 
                'field': 'product_code',
                'operator': 'in'
            }
        ]
    
    elif 'embeddingSearch' in request_dict['query']: 
        expression = request_dict['query']['embeddingSearch']
        original_query = expression
        original_ner = [
            {
                'expression': expression, 
                'field': 'product_model',
                'operator': 'in'
            }
        ]
        new_ner = [
            {
                'expression': expression, 
                'field': 'product_model',
                'operator': 'in'
            }
        ]
    if expression:
        if 'option' in request_dict['query'] and request_dict.get('query', {}).get('option'):
            option_base = request_dict['query']['option']
            original_query = original_query + option_base.upper()
            option_list = [
                s.strip().upper() for s in option_base.split(',')
                ]
            # 일단 spec은 다 in인걸로
            option_ner = [
                {
                    'expression': s,
                    'field': 'product_option',
                    'operator': 'in'
                } for s in option_list
            ]
            original_ner.extend(option_ner)
            new_ner.extend(option_ner)


        if 'spec' in request_dict['query'] and request_dict.get('query', {}).get('spec'):
            spec_base = request_dict['query']['spec']
            original_query = original_query + spec_base.upper()
            spec_list = [
                s.strip().upper() for s in spec_base.split(',')
                ]
            # 일단 spec은 다 in인걸로
            spec_ner = [
                {
                    'expression': s,
                    'field': 'product_spec',
                    'operator': 'in'
                } for s in spec_list
            ]
            original_ner.extend(spec_ner)
            new_ner.extend(spec_ner)



        cm, _, _, _, grouped_ner_result, code_mapping_error_list, l4_filter_list, original_model_code_mapping, err_spec = ccm.unstructured_code_mapping(
            original_query,
            original_ner,
            new_ner,
            {},
            [],
            'Product Description',
            'NANANA',
            country_code,
            site_cd,
            ""
        )
        cm = cm.get('unstructured')
        # __log.debug(cm)

        n_list = grouped_ner_result[0]
        c2c_key = []

        group_expression = [d.get('expression') for d in n_list] if country_code == 'KR' else [d.get('expression').upper() for d in n_list]
        group_code_mapping = [d for d in cm if d.get('expression') in group_expression] if country_code == 'KR' else [d for d in cm if d.get('expression').upper() in group_expression]
        # __log.debug(group_code_mapping)
        group_length_key = [d for d in group_code_mapping if d.get('field') in ['product_model', 'product_code']]
        c2c_key.append(any([d for d in group_length_key if 'c2c' in d.get('type') or 'e2e' in d.get('type')]))
        if len(group_length_key) > 1:
            option_expression = [d.get('expression') for d in n_list if d.get('field') in ['product_spec', 'product_option']]
            # __log.debug(option_expression)
            if option_expression:
                group_code_mapping = [d for d in group_code_mapping if (d.get('field') in ['product_model', 'product_code'] and set(d.get('option', {}).get('expression')).issubset(set(option_expression))) or d.get('field') in ['product_option']]

        l4_expression = [d.get('expression') for d in group_code_mapping if d.get('field') in ['product_model']]
        # __log.debug(f"l4_expression: {l4_expression}")
        l4_product_filter = sum([d.get('product_filter', []) for d in l4_filter_list if d.get('expression', "") in l4_expression and d.get('product_filter', [])], [])
        is_date = [d.get('expression') for d in n_list if d.get('field') == 'date']
        # negative_l4_product_filter insert 0611
        negative_l4_product_filter = sum([d.get('negative_product_filter', []) for d in l4_filter_list if d.get('expression', "") in l4_expression and d.get('negative_product_filter', [])], [])


        ext, _ = cei.extended_info_product_code(
            cm, 
            'Product Description',
            'NANANA',
            country_code,
            site_cd,
            "",
            3,
            [],
            l4_product_filter,
            l4_expression,
            negative_l4_product_filter
            )
        extended_result = pd.concat(ext, axis = 0)

        if not extended_result.empty:
            mdl_codes = sum(extended_result['extended_info'], [])

    return mdl_codes

def list_category_lv1(request_dict):
    # __log.debug(request_dict)
    if 'country_code' in request_dict['query']:
        distinct_values = Complement_Code_Mapping.objects.filter(country_code = request_dict['query']['country_code']).filter(~Q(category_lv1 = None)).values('category_lv1').distinct()
        distinct_values_list = [item['category_lv1'] for item in distinct_values]
        distinct_values_list = sorted(distinct_values_list)
        return True, distinct_values_list,  None, None
    else:
        return True, None,  None, None

def list_category_lv2(request_dict):
    # __log.debug(request_dict)
    distinct_values = Complement_Code_Mapping.objects.filter(category_lv1 = request_dict['query']['category_lv1']).filter(~Q(category_lv2 = None)).values('category_lv2').distinct()
    distinct_values_list = [item['category_lv2'] for item in distinct_values]
    distinct_values_list = sorted(distinct_values_list)
    return True, distinct_values_list,  None, None

def list_category_lv3(request_dict):
    # __log.debug(request_dict)
    distinct_values = Complement_Code_Mapping.objects.filter(category_lv2 = request_dict['query']['category_lv2']).filter(~Q(category_lv3 = None)).values('category_lv3').distinct()
    distinct_values_list = [item['category_lv3'] for item in distinct_values]
    distinct_values_list = sorted(distinct_values_list)
    return True, distinct_values_list,  None, None



# if __name__=='__main__':
#     request_dict = {
#                'request': {
#                    'url': '/api/rubicon_admin/complementation_code_mapping/',
#                    'method': 'POST'
#                },
#                'user': {'username': 'jeongin.yang@pwc.com', 'email': ''},
#                'files': [],
#                'action': 'read_code_mapping',
#                'query': {
#                    'country_code': 'KR',
#                    'category_lv1': 'HHP',
#                    'category_lv2': 'NEW RADIO MOBILE (5G SMARTPHONE)',
#                    'category_lv3': 'Galaxy Z Flip6',
#                    'model_code': '',
#                    'embeddingSearch': '플립6',
#                    'spec': '4400 mAh, 512 GB',
#                    'color': '화이트',
#                    'option': '무선충전, 나이토그래피',
#                    'table': 'rubicon_data_product_category'
#                },
#                'paging': {
#                    'page': 1,
#                    'itemsPerPage': 10,
#                    'fullLoad': False,
#                    'skip': 0
#                }
#            }
    
    # request_dict = {
    #            'request': {
    #                'url': '/api/rubicon_admin/complementation_code_mapping/',
    #                'method': 'POST'
    #            },
    #            'user': {'username': 'jeongin.yang@pwc.com', 'email': ''},
    #            'files': [],
    #            'action': 'read_code_mapping',
    #            'query': {
    #                'country_code': 'KR',
    #                'model_code': 'SM-F741NZYEKOD',
    #                'table': 'rubicon_data_product_category'
    #            },
    #            'paging': {
    #                'page': 1,
    #                'itemsPerPage': 10,
    #                'fullLoad': False,
    #                'skip': 0
    #            }
    #        }
    
    # start_time = time.time()
    # res = complement_check_db(request_dict)
    # __log.debug(f"check db time: {time.time() - start_time}s")
    # __log.debug(res)