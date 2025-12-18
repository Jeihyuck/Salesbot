import sys
sys.path.append("/www/alpha/")
import os
import django
import pandas as pd
from datetime import datetime

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "alpha.settings")
django.setup()

from django.db import connection, transaction
from apps.rubicon_v3.__function import _62_complement_code_mapping_utils as cm_utils


def fetch_p2p_h2h(mapping_code, country_code, site_cd):
    query_country_code = f"""
    select distinct type from rubicon_v3_complement_code_mapping
    where type in ('p2p', 'h2h')
    and mapping_code = '{mapping_code}'
    and site_cd = '{site_cd}'
    """
    with connection.cursor() as cursor:
        cursor.execute(query_country_code)
        columns = [col[0] for col in cursor.description]
        rows = cursor.fetchall()

    df1 = pd.DataFrame(rows, columns=columns)
    if not df1.empty:
        type_ = df1.iloc[0,0]
        print(country_code, type_)

        if country_code == 'KR':
            if type_ == 'p2p':
                query_p2p_kr = f"""
                select distinct rvccm.category_lv1, rvccm.category_lv2, rvccm.category_lv3, rdpc.goods_nm, rdpc.mdl_code
                from 
                rubicon_v3_complement_code_mapping rvccm 
                right join rubicon_data_product_category rdpc
                on rvccm.category_lv3 = rdpc.product_category_lv3 
                join rubicon_data_goods_price price 
                on price.goods_id = rdpc.goods_id
                where rvccm.type like 'p2p'
                and rdpc.goods_stat_cd like '30'
                and rdpc.show_yn = 'Y'
                and rvccm.mapping_code like '{mapping_code}'
                and rvccm.site_cd = '{site_cd}';
                """
                with connection.cursor() as cursor:
                    cursor.execute(query_p2p_kr)
                    columns = [col[0] for col in cursor.description]
                    rows = cursor.fetchall()
                
                df = pd.DataFrame(rows, columns=columns)
                results = {
                    'expression': f'{mapping_code}', 
                    'field': 'product_model', 
                    'operator': 'in', 
                    'mapping_code': [str(mapping_code)], 
                    'type': ['p2p'],
                    'category_lv1': list(set(df['category_lv1'].tolist())), 
                    'category_lv2': list(set(df['category_lv2'].tolist())), 
                    'category_lv3': list(set(df['category_lv3'].tolist()))
                    }
                    
                l4_check, l4_filters = cm_utils.check_valid_product(mapping_code, results, country_code)
                product_filter = l4_filters["product_filter"]
                df = df[df['goods_nm'].astype(str).str.lower().apply(lambda x: all(keyword in x for keyword in product_filter))]
                final_df = df.drop(['category_lv1', 'category_lv2', 'category_lv3'], axis=1)
            
            elif type_ == 'h2h':
                query_h2h_kr = f'''
                select distinct p.goods_nm, p.mdl_code
                FROM rubicon_data_product_category p
                RIGHT JOIN rubicon_v3_complement_code_mapping m 
                ON p.goods_nm LIKE CONCAT('%', m.mapping_code, '%')
                join rubicon_data_goods_price price
                on price.goods_id = p.goods_id
                where m.type = 'h2h'
                and m.country_code like 'KR'
                and p.product_category_lv3 = m.category_lv3
                and m.mapping_code = '{mapping_code}'
                and m.site_cd = '{site_cd}';
                '''

                with connection.cursor() as cursor:
                    cursor.execute(query_h2h_kr)
                    columns = [col[0] for col in cursor.description]
                    rows = cursor.fetchall()
                
                final_df = pd.DataFrame(rows, columns=columns)

        
        
        elif country_code == 'GB':
            # p2p
            if type_ == 'p2p':
                query_p2p_uk = f"""
                select distinct price.dn as display_name , price.model_code_ as model_code from 
                rubicon_v3_complement_code_mapping rvccm 
                right join (
                    select distinct rdupsb.model_code, rdupsb.category_lv1, rdupsb.category_lv2, rdupsb.category_lv3 as c3, rdupsb.display_name as dn, rdupsb.model_code as model_code_,
                    rdump.salesstatus as ss, rdump.price as price, rdump.currency as cc, rdump.promotion_price as promotion_price from 
                    rubicon_data_uk_product_spec_basics rdupsb
                    left join
                    rubicon_data_uk_model_price rdump 
                    on rdupsb.model_code = rdump.model_code
                ) as price
                on rvccm.category_lv3 = price.c3
                where rvccm.type like 'p2p'
                and price.ss = 'PURCHASABLE'
                and rvccm.country_code like 'GB'
                and mapping_code like '{mapping_code}'
                and rvccm.site_cd = '{site_cd}'
                """
                with connection.cursor() as cursor:
                    cursor.execute(query_p2p_uk)
                    columns = [col[0] for col in cursor.description]
                    rows = cursor.fetchall()
                
                df = pd.DataFrame(rows, columns=columns)


                results = {
                    'expression': f'{mapping_code}', 
                    'field': 'product_model', 
                    'operator': 'in', 
                    'mapping_code': [str(mapping_code)], 
                    'type': ['p2p'],
                    'category_lv1': list(set(df['category_lv1'].tolist())), 
                    'category_lv2': list(set(df['category_lv2'].tolist())), 
                    'category_lv3': list(set(df['category_lv3'].tolist()))
                    }
                    
                l4_check, l4_filters = cm_utils.check_valid_product(mapping_code, results, country_code)
                product_filter = l4_filters["product_filter"]
                df = df[df['goods_nm'].astype(str).str.lower().apply(lambda x: all(keyword in x for keyword in product_filter))]
                final_df = df.drop(['category_lv1', 'category_lv2', 'category_lv3'], axis=1)


            
            elif type_ == 'h2h':
                query_h2h_uk = f"""
                select distinctb.display_name , b.model_code
                FROM rubicon_data_uk_product_spec_basics b
                RIGHT JOIN rubicon_v3_complement_code_mapping m
                ON b.display_name LIKE CONCAT('%', m.mapping_code, '%')
                join rubicon_data_uk_model_price price 
                on price.model_code = b.model_code
                where m.type = 'h2h'
                and m.country_code like 'GB'
                and b.category_lv3 = m.category_lv3
                and price.salesstatus = 'PURCHASABLE'
                and m.mapping_code = '{mapping_code}'
                and m.site_cd = '{site_cd}';
                """
                with connection.cursor() as cursor:
                    cursor.execute(query_h2h_uk)
                    columns = [col[0] for col in cursor.description]
                    rows = cursor.fetchall()
                
                final_df = pd.DataFrame(rows, columns=columns)
        
        final_df = final_df.reset_index(drop=True)
        return final_df, country_code, site_cd
            
    else:
        print('Such mapping code does not exist')


       
## return df, country_code, site_cd

if __name__ == "__main__":
    mapping_code = 'S39CD'
    country_code = 'KR'
    site_cd = 'B2C'
    df, country_code, site_cd = fetch_p2p_h2h('S39GD', country_code, site_cd)
    print(df)
    df.to_excel('/www/alpha/___dev/YJI/AA/test.xlsx')
