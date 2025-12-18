# line 2 ~ 7 테스트 시 주석 해제
import sys
sys.path.append('/www/alpha/')
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'alpha.settings')
django.setup()

import json
import pandas as pd
from alpha import __log
from django.db import connection
from datetime import datetime, date

from apps.rubicon_v3.__function import __utils as utils
from apps.rubicon_v3.__function import __embedding_rerank as embedding_rerank
from apps.rubicon_v3.__function.definitions import intelligences

def extended_info(expression, intelligence, country_code, guid, message_id, k = 1):
    __log.debug(f"expression: {expression}")
    if not expression:
        return {}
    # expression_embedding = embedding_rerank.baai_embedding(expression, message_id)
    if intelligence == intelligences.PRODUCT_RECOMMENDATION:
        k = 3

    exact_match_sql = f"""
                SELECT country_code, mapping_code, category_lv1, category_lv2, category_lv3, edge, extended_info
                FROM rubicon_v3_complement_code_mapping_extended
                WHERE mapping_code = %s
                AND country_code = '{str(country_code)}'
            """


    with connection.cursor() as curs:
        curs.execute(exact_match_sql, (expression,))
        result = curs.fetchall()

        column_names = [c.name for c in curs.description]
        result_dict = {}
        meta_temp = ""
        overwrite_key = 0

        if result:
            for row in result:
                edge_value = row[column_names.index('edge')]  
                row_dict = {col_name: row[i] for i, col_name in enumerate(column_names)}
                extended_info = row_dict['extended_info']
                if extended_info:
                    extended_info = extended_info.strip('"').replace("'", '"')
                    row_dict['extended_info'] = json.loads(extended_info)
                # if edge_value in ["product_code", "recommend"]:
                if edge_value == 'product_meta':
                    meta_temp = row_dict.get('extended_info', [""])[0]
                if edge_value != 'function':
                    product_codes_placeholder = ", ".join('\'' + _ + '\'' for _ in row_dict.get('extended_info', ""))
                    if country_code == "KR":
                        release_date_sql = f"""
                                        SELECT mdl_code, release_date FROM rubicon_data_product_category 
                                        WHERE mdl_code IN ({product_codes_placeholder})
                                    """
                    elif country_code == "GB":
                        release_date_sql = f"""
                                        SELECT model_code, launch_date FROM rubicon_data_uk_product_spec_basics 
                                        WHERE model_code IN ({product_codes_placeholder})
                                    """
    
                    curs.execute(release_date_sql)
                    product_code_release_date = curs.fetchall()
                    row_df = pd.DataFrame(product_code_release_date, columns=[c.name for c in curs.description])
                    row_df.columns = ['model_code', 'release_date']
                    row_df = row_df.sort_values('release_date', ascending=False)
                    len_key = len(row_df)
                    sorted_products_df = row_df[:k]
                    sorted_products = sorted_products_df['model_code']
                    if all(x is None for x in sorted_products_df['release_date']):
                        sorted_products = product_code_release_date[:k]
                    row_dict['extended_info'] = list(set([product for product in sorted_products]))
                if not result_dict.get(edge_value, ""):
                    result_dict[edge_value] = row_dict
                else:
                    if overwrite_key >= len_key:
                        pass
                    else:
                        overwrite_key = len_key
                        result_dict[edge_value] = row_dict                
            # __log.debug(f"result_dict: {result_dict}")
            selected_value = (result_dict['recommend'] if 'recommend' in result_dict and (result_dict['recommend']['extended_info'] != [''] and result_dict['recommend']['extended_info'] != []) else 
                              (result_dict['product_code'] if 'product_code' in result_dict else result_dict['function']))
            selected_value['meta'] = meta_temp


            # return selected_value # pd.DataFrame(result, columns = [c.name for c in curs.description])
        else:
            selected_value = {
                'country_code': country_code,
                'mapping_code': expression,
                'category_lv1': 'not_found',
                'category_lv2': 'not_found',
                'category_lv3': 'not_found',
                'edge': 'not_found',
                'extended_info': [expression],
                'name': meta_temp
            }
            # return selected_value

        # curs.execute(similarity_sql)
        # result = curs.fetchall()
        # df = pd.DataFrame(result, columns = [c.name for c in curs.description])

        return selected_value
    

if __name__=="__main__":
    # expr = "블루스카이 3100"
    # expr = "갤럭시 S23"
    expr = "AI 업스케일링"
    res = extended_info(expr, 'product_recommendation',"KR","test")
    __log.debug(res)