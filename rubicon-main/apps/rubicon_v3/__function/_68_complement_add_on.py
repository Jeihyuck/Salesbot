import sys

sys.path.append("/www/alpha/")
import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "alpha.settings")
django.setup()

import pandas as pd
import numpy as np

from django.db import connection

from apps.rubicon_v3.__function._66_complement_promotion import filter_model_to_dict

import warnings

warnings.filterwarnings("ignore")


def add_on_check(NER, extended_code_mapping, country_code, site_cd):
    add_on_result = {}
    code_id = pd.DataFrame()
    acc_df = pd.DataFrame()
    final = []
    n_item = 3 if len(extended_code_mapping) == 1 else 1
    for data in extended_code_mapping:
        product_codes = data.get("extended_info", "")[:n_item]
        id_tmp = data.get("id", "")
        new_row = []
        for product_code in product_codes:
            new_row.append({"id": id_tmp, "Model Code": product_code})

        new_df = pd.DataFrame(new_row)
        code_id = pd.concat([code_id, new_df], ignore_index=False)

    if country_code == "KR" and not code_id.empty:
        acc_df = acc_kr(code_id, site_cd)
        
    elif country_code == "GB" and not code_id.empty:
        acc_df = acc_gb(code_id, site_cd)

    else:
        raise ValueError(f"Unsupported country code: {country_code}")

    total_df = [
        acc_df
    ]
    
    names = ["accessory"]
    
    if not code_id.empty:
        for code in code_id["Model Code"].tolist():
            dict_tmp = {}
            dict_tmp = filter_model_to_dict(names, code, total_df)
            if dict_tmp:
                add_on_result[code] = dict_tmp
    
    if add_on_result:
        final = [add_on_result]
    return final


def acc_kr(code_id, site_cd):
    product_codes = code_id["Model Code"].tolist()
    acc_df = pd.DataFrame()
    with connection.cursor() as cursor:
        acc_query = """
        SELECT a.mdl_code, a.rltn_goods_tp_cd, a.rltn_mdl_code, b.goods_nm, b.release_date, c.usp_desc
        FROM rubicon_data_rltn_goods_manage a , rubicon_data_product_category b, rubicon_data_goods_add_info c
        WHERE b.mdl_code = a.rltn_mdl_code
        AND b.goods_id = c.goods_id
        AND a.mdl_code IN %s
        AND b.goods_stat_cd = '30'
        AND b.show_yn = 'Y'
        AND b.site_cd = %s
        ORDER BY b.release_date desc
        """
        product_codes_input = (
            product_codes if len(product_codes) > 1 else product_codes + ["a"]
        )
        cursor.execute(acc_query, [tuple(product_codes_input), site_cd])
        acc_results = cursor.fetchall()
        if acc_results:
            acc_df = pd.DataFrame(acc_results, columns = [c.name for c in cursor.description])
            acc_df = (
                    acc_df
                    .groupby("mdl_code")
                    .head(3)
                    .drop(["release_date"], axis=1)
                )
            acc_df.columns = ["Model Code", "Type","Relation Model Code","Relation Model Name", "Relation Model Description"]
            acc_df['Type'] = np.where(
                acc_df['Type'] == '10',
                "액세서리",
                "소모품"
            )
            acc_df['Relation Model Description'] = acc_df['Relation Model Description'].apply(lambda x: x.replace('\n', ',') if x is not None else x)
            acc_df = acc_df.dropna(axis=1, how='all')
            
    return acc_df

def acc_gb(code_id, site_cd):
    product_codes = code_id["Model Code"].tolist()
    acc_df = pd.DataFrame()
    with connection.cursor() as cursor:
        acc_query = """
        SELECT a.model_code, a.rltn_model_code, b.display_name, b.usp_text, b.launch_date
        FROM rubicon_data_uk_product_rltn a, rubicon_data_uk_product_spec_basics b, rubicon_data_uk_model_price c
        WHERE b.model_code = a.rltn_model_code 
        AND b.model_code = c.model_code
        AND c.salesstatus = 'PURCHASABLE'
        AND a.model_code IN %s
        AND c.site_cd = %s
        ORDER BY b.launch_date DESC
        """
        product_codes_input = (
            product_codes if len(product_codes) > 1 else product_codes + ["a"]
        )
        cursor.execute(acc_query, [tuple(product_codes_input), site_cd])
        acc_results = cursor.fetchall()
        if acc_results:
            acc_df = pd.DataFrame(acc_results, columns = [c.name for c in cursor.description])
            acc_df = (
                    acc_df.dropna().reset_index(drop=True)
                    .groupby("model_code")
                    .head(3)
                    .drop(["launch_date"], axis=1)
                )
            acc_df.columns = ["Model Code","Relation Model Code","Relation Model Name", "Relation Model Description"]
    return acc_df
