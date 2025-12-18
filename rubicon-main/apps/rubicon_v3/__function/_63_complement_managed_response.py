import sys
sys.path.append('/www/alpha/')
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'alpha.settings')

import pandas as pd
import asyncio
import re
from copy import deepcopy
from alpha import __log, settings
from typing import Dict, List
from django.db import connection

from apps.rubicon_v3.models import Virtual_View_Field
from apps.rubicon_v3.__function import __embedding_rerank as embedding_rerank
from apps.rubicon_v3.__function import _62_complement_validation_kr as product_function_validation
from apps.rubicon_v3.__function import __utils as utils

def managed_response_check(complement_code_mapping, date_llist, country_code):
    managed_response_result = []
    managed_only = []

    with connection.cursor() as cursor:
        for data, date_list in zip(complement_code_mapping, date_llist):
            date_list = list(set([s[:4] for s in date_list if date_list != 'NEWEST']))
            # __log.debug(f"data: {data}")
            try:
                product_category_lv1_placeholders = ", ".join('\'' + _ + '\'' for _ in data.get('category_lv1', ""))
                product_category_lv2_placeholders = ", ".join('\'' + _ + '\'' for _ in data.get('category_lv2', ""))
                product_category_lv3_placeholders = ", ".join('\'' + _ + '\'' for _ in data.get('category_lv3', ""))
                date_placeholders = ", ".join('\'' + _ + '\'' for _ in date_list)
                mapping_code_temp = data.get('mapping_code', [None])
                mapping_code = mapping_code_temp[0] if mapping_code_temp is not None else None
                field = data.get('field', "")
                if not mapping_code or not field:
                    continue
                else:
                    # TODO:필터 추가 필요 여부 확인
                    # managed_sql = f"""
                    #     SELECT * 
                    #     FROM rubicon_v3_managed_response_index
                    #     WHERE country_code = '{country_code}'
                    #     AND category_lv1 in ({product_category_lv1_placeholders})
                    #     AND category_lv2 in ({product_category_lv2_placeholders})
                    #     AND category_lv3 in ({product_category_lv3_placeholders})
                    # """

                    managed_sql = f"""
                        SELECT * 
                        FROM rubicon_v3_managed_response_index
                        WHERE country_code = '{country_code}'
                        AND {'function' if field == 'product_option' else 'product'} = '{mapping_code}'
                        AND active = True
                    """
                    if date_list:
                        managed_sql += f"AND date in ({date_placeholders})"
                    else:
                        managed_sql += f"AND date is null"
                    # __log.debug(f"managed_sql: {managed_sql}")
                    cursor.execute(managed_sql)
                    results = cursor.fetchall()
                    if not results:
                        pass
                    else:
                        df = pd.DataFrame(results, columns=[c.name for c in cursor.description])
                        if len(df): 
                            managed_response_value = df['managed_response'].tolist()
                            managed_response_json_value = df['managed_response_meta'].tolist()
                            managed_only.append(all(df['managed_only'].tolist()))
                            result_temp = {
                                'mapping_code': mapping_code,
                                'managed_response': managed_response_value,
                                'managed_response_json': managed_response_json_value,
                                'date': date_list
                            }
                            managed_response_result.append(deepcopy(result_temp))
            except:
                pass
        # __log.debug(f"mamam: {managed_only}")
        if managed_only:
            managed_only = all(managed_only)
        else:
            managed_only = False
    return managed_response_result, managed_only



if __name__ == "__main__":
    django.setup()
    test_code_mapping = [                                                                                                                                                                                
                   {
                       'expression': '갤럭시 S25',
                       'field': 'product_model',
                       'mapping_code': ['갤럭시 S25'],
                       'category_lv1': ['HHP'], 
                       'category_lv2': ['NEW RADIO MOBILE (5G SMARTPHONE)'],
                       'category_lv3': ['Galaxy S25'], 
                       'original_expression': 'Galaxy S25' 
                   },
                   {
                       'expression': 'Galaxy AI',
                       'field': 'product_function',
                       'mapping_code': ['Galaxy AI'],
                       'category_lv1': [''], 
                       'category_lv2': [''],
                       'category_lv3': [''], 
                       'original_expression': 'Galaxy AI' 
                   }
               ]
    
    managed_response_test_result = managed_response_check(test_code_mapping, "KR")
    __log.debug(f"managed_response_test_result: {managed_response_test_result}")
    # managed_response_data = managed_response_check.managed_response_check(complementation_code_mapping_result, country_code)