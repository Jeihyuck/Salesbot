import sys
sys.path.append("/www/alpha/")
import os
import django
import pandas as pd
import numpy as np
import re
from datetime import datetime
from decimal import Decimal
import ast

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "alpha.settings")
django.setup()

from django.db import connection, transaction
from apps.rubicon_v3.__function._65_complement_price import get_current_time_by_country_code
from apps.rubicon_v3.__function import _62_complement_code_mapping_utils as cm_utils
from apps.rubicon_v3.__function.__llm_call import open_ai_call
from apps.rubicon_v3.__function._64_complement_extended_info_2 import clean_expression_kr, clean_expression_uk

from apps.rubicon_v3.__function import (
    __django_cache
)

from alpha import __log

CATEGORY3_KR_TARGETS = {'Accessory Kit', 'Adapter', 'Band', 'Battery', 'Cable', 'Camera', 'Cartridges', 'Case', 'Charger', 'Cover', 'Film', 'Installation Kit', 'Keyboard', 'Kimchi Container', 'Mouse', 'Panel', 'Remote Controller', 'Shelf', 'Stand', 'Tray','Box','Brush','Connector','Container','Dispenser','Dust Bag','Filter','Foucet','Hanger','Kettle','Memory','Mircrophone','Mop','Paper','Station','Storage','Weight', 'DEFAULT'}
CATEGORY2_KR_TARGETS = {'HHP OPTION', 'MOBILE-VPS PRODUCT', 'HHP ACC', 'HOME APPLIANCE', 'SMART HOME DEVICES', 'VD-VPS PRODUCT'}

CATEGORY3_GB_TARGETS = {'BESPOKE panels', 'Accessories'}
CATEGORY2_GB_TARGETS = {'Computer Accessories', 'Display Accessories', 'Home Appliance Accessories', 'Mobile Accessories', 'Projector Accessories', 'SmartThings', 'TV Accessories', 'TV Audio Accessories'}


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
            WHERE model_code IN %s
            AND salesstatus = 'PURCHASABLE'
            AND site_cd = %s
            """
            cursor.execute(price_query, [tuple(product_codes_input), site_cd])
            
        price_results = cursor.fetchall()
        if price_results:
            price_df = pd.DataFrame(price_results, columns=[c.name for c in cursor.description])
            price_df.columns = ["model_code", "standard_price", "benefit_price"]
            combined_df = pd.merge(price_df, df, on="model_code")
            combined_df = combined_df[["model_name","product","model_code","standard_price","benefit_price"]]
            if site_cd == "FN":
                discount = combined_df["benefit_price"].apply(lambda x: Decimal(x) * Decimal('0.25'))
                discount = discount.apply(lambda x: int(np.round(int(x+1) / 100.0) * 100))
                combined_df["benefit_price"] = combined_df["benefit_price"].apply(Decimal) - discount
                combined_df["benefit_price"] = combined_df["benefit_price"].astype(int)
            combined_df = combined_df.fillna('-')
        
    return combined_df

def extra_clean_expression(goods_nm, country_code, category_lv1, category_lv2, category_lv3):
    if country_code == 'KR':
        if category_lv1 == 'AIR CONDITIONER':
            goods_nm = goods_nm.replace("청정", "")
            goods_nm = goods_nm.replace("냉난방", "")
            goods_nm = goods_nm.replace("냉방전용", "")
            goods_nm = goods_nm.replace("1등급", "")
            goods_nm = goods_nm.replace("냉방", "")
            goods_nm = goods_nm.replace("시스템 에어컨", "시스템에어컨")
            goods_nm = goods_nm.replace("중대형 에어컨", "중대형에어컨")
            goods_nm = goods_nm.replace("사각패널", "")

        elif "TV" in category_lv2 or 'OLED SCREEN' in category_lv2:  # Fixed: use 'in' instead of .contains()
            goods_nm = goods_nm.replace("풀 모션 슬림핏 벽걸이형", "")
            goods_nm = goods_nm.replace("벽걸이형", "")
            # goods_nm = goods_nm.replace("OLED", "")
            goods_nm = goods_nm.replace("  ", " ")
            # goods_nm = goods_nm.replace("라이트", "")
            # goods_nm = goods_nm.replace("스탠다드", "")
            
            # Clean The Frame products - remove everything after "The Frame" that ends with "베젤"
            if "The Frame" in goods_nm:
                # First handle "The Frame Pro" case - preserve it completely
                if "The Frame Pro" in goods_nm:
                    # Remove bezel descriptions after "The Frame Pro"
                    goods_nm = re.sub(r'(The Frame Pro)\s+.*?(베젤|베즐|bezel).*?$', r'\1', goods_nm, flags=re.IGNORECASE)
                    goods_nm = re.sub(r'(The Frame Pro)\s+.*?베젤', r'\1', goods_nm)
                else:
                    # For regular "The Frame" (not Pro), remove bezel descriptions
                    goods_nm = re.sub(r'(The Frame)(?!\s+Pro)\s+.*?베젤', r'\1', goods_nm)
                    goods_nm = re.sub(r'(The Frame)(?!\s+Pro)\s+.*?(베젤|베즐|bezel).*?$', r'\1', goods_nm, flags=re.IGNORECASE)

        elif category_lv1 == "냉장고" or category_lv1 == '김치냉장고':
            # Remove X도어 pattern (1도어, 4도어, etc.)
            goods_nm = re.sub(r'\s*\d+도어\s*', ' ', goods_nm)
            goods_nm = re.sub(r'\s+', ' ', goods_nm)  # Clean up multiple spaces
        
        elif category_lv1 == '진공청소기':
            goods_nm = goods_nm.replace("그리너리", "") 
            if "제트" in goods_nm:
                goods_nm = re.sub(r'\s*\d+W\s*', ' ', goods_nm)
                goods_nm = re.sub(r'\s+', ' ', goods_nm)  # Clean up multiple spaces
                # First handle "제트 Lite" case - preserve it completely
                if "제트 Lite" in goods_nm:
                    # Remove package descriptions after "제트 Lite"
                    goods_nm = re.sub(r'(제트 Lite)\s+.*?패키지.*?$', r'\1', goods_nm, flags=re.IGNORECASE)
                    goods_nm = re.sub(r'(제트 Lite)\s+.*?패키지', r'\1', goods_nm)
                else:
                    # For regular "제트" (not Lite), remove package descriptions
                    goods_nm = re.sub(r'(제트)(?!\s+Lite)\s+.*?패키지', r'\1', goods_nm)
                    goods_nm = re.sub(r'(제트)(?!\s+Lite)\s+.*?패키지.*?$', r'\1', goods_nm, flags=re.IGNORECASE)
        
        elif category_lv3 == 'Dryer':
            colors_in_goods_nm = ['화이트', '블랙케비어']
            # Remove all colors in one go using regex
            pattern = '|'.join(colors_in_goods_nm)
            goods_nm = re.sub(pattern, '', goods_nm)
        
        elif category_lv3 == 'Bespoke Dishwasher' or category_lv3 == 'Dishwasher':
            goods_nm = re.sub(r'\s*\d+\s*인용\s*', ' ', goods_nm)
            goods_nm = re.sub(r'\s+', ' ', goods_nm)  # Clean up multiple spaces

    
    elif country_code == 'GB':
        if category_lv2 == 'Display Monitors':
            goods_nm = re.sub(r'\s*\d+\s*Hz\s*', ' ', goods_nm)
            goods_nm = re.sub(r'\s+', ' ', goods_nm)  # Clean up multiple spaces
        
        if 'Galaxy Flip7' in goods_nm:
            goods_nm = goods_nm.replace('Galaxy Flip7', 'Galaxy Z Flip7')
        if 'Galaxy Fold7' in goods_nm:
            goods_nm = goods_nm.replace('Galaxy Fold7', 'Galaxy Z Fold7')

    return goods_nm.strip()


def process_mapping_codes(mapping_codes, extended_empty, country_code, site_cd):
    # Assuming the original processing function returns a DataFrame
    # We will use pd.concat to combine the DataFrames
    dfs = [get_price_list(code, extended_empty, country_code, site_cd) for code in mapping_codes]  # Create DataFrames for each mapping code
    combined_df = pd.concat(dfs, ignore_index=True)  # Combine all DataFrames into one
    return combined_df

def get_price_list(mapping_code, extended_empty, country_code, site_cd):
    df_all = pd.DataFrame()
    query_country_code = f"""
    select distinct type, category_lv1, category_lv2, category_lv3 from rubicon_v3_complement_code_mapping
    where type in ('p2p', 'h2h')
    and mapping_code = '{mapping_code}'
    and site_cd = '{site_cd}'
    and active = True
    """
    with connection.cursor() as cursor:
        cursor.execute(query_country_code)
        columns = [col[0] for col in cursor.description]
        rows = cursor.fetchall()

    df1 = pd.DataFrame(rows, columns=columns)
    final_df = pd.DataFrame()
    combined_df = pd.DataFrame()
    if not df1.empty:
        typee = df1['type'].tolist()
        type_p2p = 'p2p' in typee
        type_h2h = 'h2h' in typee
        c1 = df1['category_lv1'].tolist()
        c2 = df1['category_lv2'].tolist()
        c3 = df1['category_lv3'].tolist()

        if country_code == "KR":

            if type_p2p:

                query_p2p_kr = f"""
                select distinct rvccm.category_lv1, rvccm.category_lv2, rvccm.category_lv3, rdpc.goods_nm, rdpc.mdl_code
                from 
                rubicon_v3_complement_code_mapping rvccm 
                right join rubicon_data_product_category rdpc
                """
                if 'NA' in c3 and 'NA' not in c2:
                    query_p2p_kr += f"""on rvccm.category_lv2 = rdpc.product_category_lv2
                    and rvccm.category_lv1 = rdpc.product_category_lv1"""
                elif 'NA' in c3 and 'NA' in c2 and 'NA' not in c1:
                    query_p2p_kr += f"""on rvccm.category_lv1 = rdpc.product_category_lv1"""
                else:
                    query_p2p_kr += f"""on rvccm.category_lv3 = rdpc.product_category_lv3
                    and rvccm.category_lv2 = rdpc.product_category_lv2
                    and rvccm.category_lv1 = rdpc.product_category_lv1"""
                
                query_p2p_kr += f"""
                where rvccm.type like 'p2p'
                and rvccm.mapping_code like '{mapping_code}'
                and rdpc.site_cd = '{site_cd}'
                and rvccm.active = True
                and rdpc.set_tp_cd != '20';
                """

                with connection.cursor() as cursor:
                    cursor.execute(query_p2p_kr)
                    columns = [col[0] for col in cursor.description]
                    rows = cursor.fetchall()
                    df = pd.DataFrame(rows, columns=columns)

                if not df.empty:
                    if extended_empty: 
                        df = df[~df['category_lv3'].isin(CATEGORY3_KR_TARGETS)]
                        df = df[~df['category_lv2'].isin(CATEGORY2_KR_TARGETS)]
                    if not df.empty:
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

                        l4_check, l4_filters = cm_utils.check_valid_product(
                            mapping_code, results, country_code
                        )
                        product_filter = l4_filters["product_filter"]
                        negative_product_filter = l4_filters["negative_product_filter"]
                        final_df = df[
                            df["goods_nm"]
                            .astype(str)
                            .str.lower()
                            .apply(lambda x: all((keyword in x) if not keyword.startswith('[') else any(item in x for item in set(ast.literal_eval(keyword))) for keyword in product_filter))
                        ]
                        final_df = final_df[~final_df['goods_nm'].astype(str).str.lower().apply(lambda x: any(keyword in x for keyword in negative_product_filter))]
                        if not final_df.empty:
                            final_df["product"] = final_df.apply(
                                            lambda row: clean_expression_kr(
                                                row["goods_nm"],
                                                row["category_lv1"] == "MERCHANDISING",
                                                row["category_lv1"] == "냉장고",
                                                row["category_lv1"] == "HHP",
                                                row["category_lv3"] == "Printer",
                                                (row["category_lv3"] == "External HDD") or (row["category_lv3"] == "External SSD"),
                                                row["category_lv3"] in [
                                                    "Bespoke AirDresser",
                                                    "AirDresser",
                                                ],
                                                row["category_lv3"] == "The Serif"
                                            ),
                                            axis=1,
                                        )
                            final_df["product"] = final_df.apply(
                                            lambda row: extra_clean_expression(
                                                row["product"],
                                                country_code,
                                                row["category_lv1"],
                                                row["category_lv2"],
                                                row["category_lv3"]
                                            ),
                                            axis=1,
                                        )
                                    
                df_all= pd.concat([df_all, final_df], ignore_index=True)

            if type_h2h:
                query_h2h_kr = f"""
                select distinct p.goods_nm, p.mdl_code, m.category_lv1, m.category_lv2, m.category_lv3
                FROM rubicon_data_product_category p
                RIGHT JOIN rubicon_v3_complement_code_mapping m 
                ON p.goods_nm LIKE CONCAT('%', m.mapping_code, '%')
                where m.type = 'h2h'
                and m.country_code like 'KR'
                and p.product_category_lv3 = m.category_lv3
                and p.product_category_lv2 = m.category_lv2
                and p.product_category_lv1 = m.category_lv1
                and m.mapping_code = '{mapping_code}'
                and p.site_cd = '{site_cd}'
                and m.active = True
                and p.set_tp_cd != '20';
                """

                with connection.cursor() as cursor:
                    cursor.execute(query_h2h_kr)
                    columns = [col[0] for col in cursor.description]
                    rows = cursor.fetchall()

                final_df = pd.DataFrame(rows, columns=columns)
                if not final_df.empty:
                    if extended_empty:
                        final_df = final_df[~final_df['category_lv3'].isin(CATEGORY3_KR_TARGETS)]
                        final_df = final_df[~final_df['category_lv2'].isin(CATEGORY2_KR_TARGETS)]
                    
                    if not final_df.empty:
                        final_df["product"] = final_df.apply(
                                        lambda row: clean_expression_kr(
                                            row["goods_nm"],
                                            row["category_lv1"] == "MERCHANDISING",
                                            row["category_lv1"] == "냉장고",
                                            row["category_lv1"] == "HHP",
                                            row["category_lv3"] == "Printer",
                                            (row["category_lv3"] == "External HDD") or (row["category_lv3"] == "External SSD"),
                                            row["category_lv3"] in [
                                                "Bespoke AirDresser",
                                                "AirDresser",
                                            ],
                                            row["category_lv3"] == "The Serif"
                                        ),
                                        axis=1,
                                    )
                        final_df["product"] = final_df.apply(
                                        lambda row: extra_clean_expression(
                                            row["product"],
                                            country_code,
                                            row["category_lv1"],
                                            row["category_lv2"],
                                            row["category_lv3"]
                                        ),
                                        axis=1,
                                    )  

                df_all= pd.concat([df_all, final_df], ignore_index=True)

        elif country_code == "GB":
            # p2p
            if type_p2p:                          
                query_p2p_uk = f"""
                select distinct price.dn as display_name, price.c1 as category_lv1, price.c2 as category_lv2, price.c3 as category_lv3, price.model_code_ as model_code from 
                rubicon_v3_complement_code_mapping rvccm 
                right join (
                    select distinct rdupsb.site_cd, rdupsb.model_code, rdupsb.category_lv1 as c1, rdupsb.category_lv2 as c2, rdupsb.category_lv3 as c3, rdupsb.display_name as dn, rdupsb.model_code as model_code_,
                    rdump.salesstatus as ss, rdump.price as price, rdump.currency as cc, rdump.promotion_price as promotion_price from 
                    rubicon_data_uk_product_spec_basics rdupsb
                    left join
                    rubicon_data_uk_model_price rdump 
                    on rdupsb.model_code = rdump.model_code
                    and rdupsb.site_cd = rdump.site_cd
                ) as price
                """
                if 'NA' in c3 and 'NA' not in c2:
                    query_p2p_uk += f"""on rvccm.category_lv2 = price.c2
                    and rvccm.category_lv1 = price.c1"""
                elif 'NA' in c3 and 'NA' in c2 and 'NA' not in c1:
                    query_p2p_uk += f"""on rvccm.category_lv1 = price.c1"""
                else:
                    query_p2p_uk += f"""on rvccm.category_lv3 = price.c3
                    and rvccm.category_lv2 = price.c2
                    and rvccm.category_lv1 = price.c1"""

                query_p2p_uk += f"""
                where rvccm.type like 'p2p'
                and rvccm.country_code like 'GB'
                and mapping_code like '{mapping_code}'
                and price.site_cd = '{site_cd}'
                and rvccm.active = True
                and price.model_code not ilike 'F-%'
                """
                with connection.cursor() as cursor:
                    cursor.execute(query_p2p_uk)
                    columns = [col[0] for col in cursor.description]
                    rows = cursor.fetchall()
                

                df = pd.DataFrame(rows, columns=columns)
                if not df.empty:
                    if extended_empty:
                        df = df[~df['category_lv3'].isin(CATEGORY3_GB_TARGETS)]
                        df = df[~df['category_lv2'].isin(CATEGORY2_GB_TARGETS)]
                    if not df.empty:
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
                    

                        l4_check, l4_filters = cm_utils.check_valid_product(
                            mapping_code, results, country_code
                        )
                        product_filter = l4_filters["product_filter"]
                        negative_product_filter = l4_filters["negative_product_filter"]
                        final_df = df[
                            df["display_name"]
                            .astype(str)
                            .str.lower()
                            .apply(lambda x: all((keyword in x) if not keyword.startswith('[') else any(item in x for item in set(ast.literal_eval(keyword))) for keyword in product_filter))
                        ]
                        __log.debug(f"product_filter: {product_filter}, negative_product_filter: {negative_product_filter}")
                        final_df = final_df[~final_df['display_name'].astype(str).str.lower().apply(lambda x: any(keyword in x for keyword in negative_product_filter))]
                        if not final_df.empty:
                            final_df["product"] = final_df.apply(
                                            lambda row: clean_expression_uk(
                                                row["display_name"],
                                                row["model_code"],
                                                row["category_lv1"] == "Home Appliances",
                                                row["category_lv1"] == "Mobile",
                                                row["category_lv3"] == "Printer",
                                                (row["category_lv3"] == "External HDD") or (
                                                    row["category_lv3"] == "External SSD"
                                                ),
                                                row["category_lv1"] == "Computers",
                                            ),
                                            axis=1,
                                        )
                            final_df["product"] = final_df.apply(
                                            lambda row: extra_clean_expression(
                                                row["product"],
                                                country_code,
                                                row["category_lv1"],
                                                row["category_lv2"],
                                                row["category_lv3"]
                                            ),
                                            axis=1,
                                        )

                df_all= pd.concat([df_all, final_df], ignore_index=True)

            if type_h2h:
                query_h2h_uk = f"""
                select distinct b.display_name , b.model_code, m.category_lv1, m.category_lv2, m.category_lv3
                FROM rubicon_data_uk_product_spec_basics b
                RIGHT JOIN rubicon_v3_complement_code_mapping m
                ON b.display_name LIKE CONCAT('%', m.mapping_code, '%')
                join rubicon_data_uk_model_price price 
                on price.model_code = b.model_code
                where m.type = 'h2h'
                and m.country_code = 'GB'
                and b.category_lv3 = m.category_lv3
                and b.category_lv2 = m.category_lv2
                and b.category_lv1 = m.category_lv1
                and m.mapping_code = '{mapping_code}'
                and b.site_cd = '{site_cd}'
                and m.active = True
                and b.model_code not ilike 'F-%';
                """
                with connection.cursor() as cursor:
                    cursor.execute(query_h2h_uk)
                    columns = [col[0] for col in cursor.description]
                    rows = cursor.fetchall()

                final_df = pd.DataFrame(rows, columns=columns)
                if not final_df.empty:
                    if extended_empty:
                        final_df = final_df[~final_df['category_lv3'].isin(CATEGORY3_GB_TARGETS)]
                        final_df = final_df[~final_df['category_lv2'].isin(CATEGORY2_GB_TARGETS)]

                    if not final_df.empty:
                        final_df["product"] = final_df.apply(
                                        lambda row: clean_expression_uk(
                                            row["display_name"],
                                            row["model_code"],
                                            row["category_lv1"] == "Home Appliances",
                                            row["category_lv1"] == "Mobile",
                                            row["category_lv3"] == "Printer",
                                            (row["category_lv3"] == "External HDD") or (
                                                row["category_lv3"] == "External SSD"
                                            ),
                                            row["category_lv1"] == "Computers",
                                        ),
                                        axis=1,
                                    )
                        final_df["product"] = final_df.apply(
                                        lambda row: extra_clean_expression(
                                            row["product"],
                                            country_code,
                                            row["category_lv1"],
                                            row["category_lv2"],
                                            row["category_lv3"]
                                        ),
                                        axis=1,
                                    )

                df_all= pd.concat([df_all, final_df], ignore_index=True)

        if not df_all.empty:
            df_all = df_all.drop(columns=['category_lv1', 'category_lv2', 'category_lv3'])
            df_all = df_all.reset_index(drop=True)
            df_all.columns = ["model_name", "model_code", "product"]
            combined_df = get_price(df_all, country_code, site_cd)
    return combined_df

def high_level_price_check(mapping_codes, extended_info_initial, extended_info, country_code, site_cd):
    if country_code == "KR":
        currency = 'KRW'
    elif country_code == "GB":
        currency = 'GBP'

    # Prepare initial extended info
    if len(extended_info_initial) > 0:
        df = pd.DataFrame(extended_info_initial)
        extended_info_initial = df[['mapping_code', 'category_lv1', 'category_lv2', 'category_lv3']].copy()
        # Apply cleaning to transform the mapping_code column
        extended_info_initial['mapping_code'] = extended_info_initial.apply(
            lambda row: extra_clean_expression(
                row["mapping_code"], 
                country_code, 
                row['category_lv1'],
                row['category_lv2'], 
                row['category_lv3']
            ), axis=1
        )
        extended_init_mapping_codes = extended_info_initial['mapping_code'].tolist()
    else:
        extended_init_mapping_codes = []

    # Prepare extended info
    if len(extended_info) > 0:
        extended_empty = False
        df = pd.DataFrame(extended_info)
        extended_info = df[['mapping_code', 'category_lv1', 'category_lv2', 'category_lv3']].copy()
        # Apply cleaning to transform the mapping_code column
        extended_info['mapping_code'] = extended_info.apply(
            lambda row: extra_clean_expression(
                row["mapping_code"], 
                country_code, 
                row['category_lv1'],
                row['category_lv2'], 
                row['category_lv3']
            ), axis=1
        )
        extended_info_mc = extended_info['mapping_code'].tolist()
    else:
        extended_empty = True
        extended_info_mc = []

    if len(mapping_codes) > 0:
        price_df = process_mapping_codes(mapping_codes, extended_empty, country_code, site_cd)
        if not price_df.empty:
            if site_cd == 'FN':
                price_df = price_df.drop(columns=['model_code','standard_price'])
                price_df = price_df.drop_duplicates(subset=['model_name', 'benefit_price'])
                price_df = price_df.sort_values(by='benefit_price').reset_index(drop=True)

                # Handle extended_info_mc - check if it's empty first
                if extended_info_mc:
                    # Find which extended_info_mc products actually exist in price_df, and including them all
                    extended_info_mc_series = pd.Series(list(set(extended_info_mc)))
                    existing_mc_products = extended_info_mc_series[extended_info_mc_series.isin(price_df['product'])].tolist()
                    final_products = existing_mc_products.copy()
                else:
                    # If extended_info_mc is empty, start with empty final_products
                    final_products = []
                
                # Calculate how many more products we need to reach 5 total & Fill up remaining slots if needed
                products_needed = 5 - len(final_products)
                if products_needed > 0:
                    # Fill up to 5 products using set operations for better performance
                    extended_info_mc_set = set(extended_info_mc)
                    extended_init_set = set(extended_init_mapping_codes)
                    remaining_candidates = list(extended_init_set - extended_info_mc_set)
                    if remaining_candidates:
                        remaining_price_stats = price_df[price_df['product'].isin(remaining_candidates)].groupby('product')['benefit_price'].agg(['min', 'max']).reset_index()
                        if not remaining_price_stats.empty:
                            remaining_price_stats['max'] = pd.to_numeric(remaining_price_stats['max'], errors='coerce')
                            top_expensive = remaining_price_stats.nlargest(products_needed, 'max')['product'].tolist()
                            final_products.extend(top_expensive)
                        else:
                            # Fallback if no price data available
                            final_products.extend(remaining_candidates[:products_needed])
                    else:
                        # Fallback when no initial extended info, extended info available - use top products from price_df
                        if not price_df.empty:
                            price_df = price_df.sort_values('benefit_price', ascending=False)
                            available_products = price_df['product'].unique()[:products_needed]
                            final_products.extend(available_products.tolist())
                
                # Filter price_df to only include final products if we have any
                if final_products:
                    price_df = price_df[price_df['product'].isin(final_products)]
                
                price_grouped = price_df.groupby('product')['benefit_price'].agg(min_price='min', max_price='max').reset_index()
                price_grouped['benefit_price'] = price_grouped.apply(lambda x: f" {x['min_price']} {currency}  ~  {x['max_price']} {currency} ", axis=1)
                # Sort to show extended_info_mc products first, then the rest
                # if len(extended_info_mc) > 0:
                #     mc_products = price_grouped[price_grouped['product'].isin(extended_info_mc)]
                #     other_products = price_grouped[~price_grouped['product'].isin(extended_info_mc)]
                #     # Sort extended info products by descending max price
                #     mc_products = mc_products.sort_values('max_price', ascending=True)
                #     # Sort other products by descending max price too
                #     other_products = other_products.sort_values('max_price', ascending=True)
                #     price_df = pd.concat([mc_products, other_products], ignore_index=True)
                # else:
                    # If no extended info, just sort by descending max price
                price_df = price_grouped.sort_values('max_price', ascending=True)
                
                price_df = price_df[['product', 'benefit_price']]
                price_df = price_df.rename(columns={'product': 'Product Line', 'benefit_price': '임직원가'})
            
            else:
                price_df = price_df.drop(columns=['model_code','benefit_price'])
                price_df = price_df.drop_duplicates(subset=['model_name', 'standard_price'])
                price_df = price_df.sort_values(by='standard_price').reset_index(drop=True)
                # Handle extended_info_mc - check if it's empty first
                if extended_info_mc:
                    # Find which extended_info_mc products actually exist in price_df, and including them all
                    extended_info_mc_series = pd.Series(list(set(extended_info_mc)))
                    existing_mc_products = extended_info_mc_series[extended_info_mc_series.isin(price_df['product'])].tolist()
                    final_products = existing_mc_products.copy()
                else:
                    # If extended_info_mc is empty, start with empty final_products
                    final_products = []
                
                # Calculate how many more products we need to reach 5 total & Fill up remaining slots if needed
                products_needed = 5 - len(final_products)
                if products_needed > 0:
                    # Fill up to 5 products using set operations for better performance
                    extended_info_mc_set = set(extended_info_mc)
                    extended_init_set = set(extended_init_mapping_codes)
                    remaining_candidates = list(extended_init_set - extended_info_mc_set)
                    if remaining_candidates:
                        remaining_price_stats = price_df[price_df['product'].isin(remaining_candidates)].groupby('product')['standard_price'].agg(['min', 'max']).reset_index()
                        if not remaining_price_stats.empty:
                            remaining_price_stats['max'] = pd.to_numeric(remaining_price_stats['max'], errors='coerce')
                            top_expensive = remaining_price_stats.nlargest(products_needed, 'max')['product'].tolist()
                            final_products.extend(top_expensive)
                        else:
                            # Fallback if no price data available
                            final_products.extend(remaining_candidates[:products_needed])
                    else:
                        # Fallback when no initial extended info, extended info available - use top products from price_df
                        if not price_df.empty:
                            price_df = price_df.sort_values('standard_price', ascending=False)
                            available_products = price_df['product'].unique()[:products_needed]
                            final_products.extend(available_products.tolist())
                
                # Filter price_df to only include final products if we have any
                if final_products:
                    price_df = price_df[price_df['product'].isin(final_products)]
                
                price_grouped = price_df.groupby('product')['standard_price'].agg(min_price='min', max_price='max').reset_index()
                price_grouped['standard_price'] = price_grouped.apply(lambda x: f" {x['min_price']} {currency}  ~  {x['max_price']} {currency} ", axis=1)
                
                # Sort to show extended_info_mc products first, then the rest
                # if len(extended_info_mc) > 0:
                #     mc_products = price_grouped[price_grouped['product'].isin(extended_info_mc)]
                #     other_products = price_grouped[~price_grouped['product'].isin(extended_info_mc)]
                #     # Sort extended info products by descending max price
                #     mc_products = mc_products.sort_values('max_price', ascending=True)
                #     # Sort other products by descending max price too
                #     other_products = other_products.sort_values('max_price', ascending=True)
                #     price_df = pd.concat([mc_products, other_products], ignore_index=True)
                # else:
                    # If no extended info, just sort by descending max price
                price_df = price_grouped.sort_values('max_price', ascending=True)
                
                price_df = price_df[['product', 'standard_price']]
                price_df = price_df.rename(columns={'product': 'Product Line', 'standard_price': 'Standard Price'})

        price_table = price_df.to_markdown(index=False)

        return price_table

# if __name__ == "__main__":
#     # FOR TESTING
#     from apps.rubicon_v3.__test.complement_test import get_complement_result
#     # Example usage
#     ####################################################
#     site_cd = 'B2C'
#     country_code = 'GB'
#     query = 'Price range of galaxy phones'   
#     #####################################################

#     qc_result = get_complement_result(query, country_code, [], site_cd)
#     mapping_codes = [code for code_mapping in qc_result['code_mapping']
#                     for code in code_mapping.get("mapping_code", [])
#                     if code and code_mapping.get("field") == 'product_model']
#     extended_info_initial = qc_result['initial_extended_info_result']
#     extended_info = qc_result['extended_info_result']

#     # extended_info_initial = extended_info = []

#     print(f"HERE!: {extended_info}")
 
    
#     price_table = high_level_price_check(mapping_codes, extended_info_initial, extended_info, country_code, site_cd)
#     print(price_table)