import sys
sys.path.append("/www/alpha/")

import os
import django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "alpha.settings")
django.setup()
from django.db import connection

import pandas as pd
from apps.rubicon_v3.__function._65_complement_price import get_current_time_by_country_code

def get_price(df, country_code, site_cd):
    now = get_current_time_by_country_code(country_code)
    price_df = pd.DataFrame()
    combined_df = pd.DataFrame()
    product_codes = df['model_code'].tolist()
    product_codes_input = (
                product_codes if len(product_codes) > 1 else product_codes + ["a"]
            )
    with connection.cursor() as cursor:
        if country_code == "KR":
            price_query  = """
            SELECT price.mdl_code, price.sale_prc1, price.sale_prc3
            FROM (
            SELECT gp.sale_prc1
                ,gp.sale_prc3
                ,pc.mdl_code
                ,gp.sys_reg_dtm
                ,row_number() over(partition by pc.mdl_code order by gp.sys_reg_dtm desc) as rank 
            FROM rubicon_data_goods_price gp, rubicon_data_product_category pc
            WHERE pc.mdl_code IN %s
            AND gp.goods_id = pc.goods_id
            AND pc.goods_stat_cd = '30'
            AND pc.show_yn = 'Y'
            AND %s between gp.sale_strt_dtm and gp.sale_end_dtm
            AND pc.site_cd = %s) price
            where price.rank = 1
            """
            cursor.execute(price_query, [tuple(product_codes_input), now, site_cd])
            
        elif country_code == "GB":
            price_query = """
            SELECT model_code, price, promotion_price
            FROM rubicon_data_uk_model_price 
            AND model_code IN %s
            AND salesstatus = 'PURCHASABLE'
            AND site_cd = %s
            """
            cursor.execute(price_query, [tuple(product_codes_input), site_cd])
            
        price_results = cursor.fetchall()
        if price_results:
            price_df = pd.DataFrame(price_results, columns=[c.name for c in cursor.description])
            price_df.columns = ["model_code", "standard_price", "benefit_price"]
            combined_df = pd.merge(price_df, df, on="model_code")
        
    return combined_df
            
            
            