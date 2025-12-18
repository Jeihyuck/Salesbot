# line 2 ~ 7 테스트 시 주석 해제
import sys

sys.path.append("/www/alpha/")
import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "alpha.settings")
django.setup()
import time

import pandas as pd
import json
import ast
from alpha import __log
from django.db import connection, transaction
from apps.rubicon_v3.__function._64_complement_extended_info_2 import (
    clean_expression_kr,
    clean_expression_uk,
)

from apps.rubicon_v3.__function.__embedding_rerank import rerank_db_results


def make_data(x: pd.DataFrame):
    rst_dict = {}
    for _, row in x.iterrows():
        rst_dict[row["spec_lv1"]] = row["value_in_rows"]
    return rst_dict


def drop_dup_dict(
    extended_code_mapping: list,
    crit_keys=["category_lv1", "category_lv2", "category_lv3"],
):

    seen = list()
    unique_code_mapping = []

    for data in extended_code_mapping:
        
        
        if data.get('field', '') == "product_option":
            pass
        else:
            key = tuple(data[k] for k in crit_keys)
            # if _filter:
            #     if (key not in seen) & (_filter[0] in data.get('mapping_code')):
            #         seen.append(key)
            #         unique_code_mapping.append(data)
            if key not in seen:
                seen.append(key)
                unique_code_mapping.append(data)

    return unique_code_mapping

def remove_except_case(country_code, extended_code_mapping):
    
    result = []
    
    for x in extended_code_mapping:
        if country_code == 'GB':
            if x.get('category_lv2', '') != 'Smartphones':
                result.append(x)
                
        else: # kr
            result.append(x)
                
    return result


def high_level_specification_check(query, extended_code_mapping, l4_filter_list, country_code, site_cd="B2C"):

    # "l4_filter_list": [
    #       {
    #         "expression": "그랑데 건조기",
    #         "code_filter_str": [],
    #         "code_filter_int": [],
    #         "product_filter": [
    #           "그랑데"
    #         ]
    #       }
    #     ],

    result_dict = {}
    debug_list = []

    try:
        if extended_code_mapping:
            # __log.debug("#########################################")
            code_mapping = drop_dup_dict(extended_code_mapping=extended_code_mapping)
            # __log.debug(f"code_mapping: {code_mapping}")
            # __log.debug(l4_filter_list)
            code_mapping = remove_except_case(country_code=country_code, extended_code_mapping=code_mapping)
            
            if not code_mapping: 
                return result_dict, debug_list
            else:
            
                final_result = pd.DataFrame()

                with connection.cursor() as cursor:
                    for data in code_mapping:

                        _filter = [x.get('product_filter', '') for x in l4_filter_list if x.get('expression', '') == data.get('mapping_code', '')]
                        # o = {
                        #     "data": data,
                        # }
                        # debug_list.append(o)

                        product_category_lv1 = data.get("category_lv1", "")
                        product_category_lv2 = data.get("category_lv2", "")
                        product_category_lv3 = data.get("category_lv3", "")

                        if country_code == "KR":

                            cond1 = (
                                ""
                                if product_category_lv1 in ["NA"]
                                else f"and a.product_category_lv1='{product_category_lv1}'"
                            )
                            cond2 = (
                                ""
                                if product_category_lv2 in ["NA"]
                                else f"and a.product_category_lv2='{product_category_lv2}'"
                            )
                            cond3 = (
                                ""
                                if product_category_lv3 in ["NA"]
                                else f"and a.product_category_lv3='{product_category_lv3}'"
                            )
                            
                            cond1_hist = (
                                ""
                                if product_category_lv1 in ["NA"]
                                else f"and c.product_category_lv1='{product_category_lv1}'"
                            )
                            cond2_hist = (
                                ""
                                if product_category_lv2 in ["NA"]
                                else f"and c.product_category_lv2='{product_category_lv2}'"
                            )
                            cond3_hist = (
                                ""
                                if product_category_lv3 in ["NA"]
                                else f"and c.product_category_lv3='{product_category_lv3}'"
                            )

                            sql = f"""SELECT coalesce(a.goods_nm, c.goods_nm) as goods_nm, 
                                coalesce(a.mdl_code, c.mdl_code) as mdl_code, 
                                '색상' as disp_nm1, 
                                '' as disp_nm2, 
                                coalesce(a.color, c.color) as spec_value
            FROM rubicon_v3_complement_product_spec b
            LEFT JOIN rubicon_data_product_category a ON b.mdl_code = a.mdl_code {cond1}{cond2}{cond3}
                AND a.show_yn = 'Y'
                AND a.site_cd = '{site_cd}'
                AND b.on_sale != 'X'
            LEFT JOIN rubicon_data_prd_mst_hist c ON b.mdl_code = c.mdl_code {cond1_hist}{cond2_hist}{cond3_hist}
                AND c.site_cd = '{site_cd}'
                AND b.on_sale = 'X'
            WHERE b.disp_nm1 not in ('EMC', '안전인증정보', '기본정보', '상품기본정보')
            AND b.value not in ('-', 'N/A')
            AND b.value is not NULL 
            AND (a.mdl_code is not null or c.mdl_code is not null)
            UNION
            SELECT coalesce(a.goods_nm, c.goods_nm) as goods_nm, 
                   coalesce(a.mdl_code, c.mdl_code) as mdl_code, 
                   b.disp_nm1, 
                   coalesce(b.disp_nm2, ''), 
                   b.value as spec_value
            FROM rubicon_v3_complement_product_spec b 
            LEFT JOIN rubicon_data_product_category a ON b.mdl_code = a.mdl_code {cond1}{cond2}{cond3}
                AND a.show_yn = 'Y'
                AND a.site_cd = '{site_cd}'
                AND b.on_sale != 'X'
            LEFT JOIN rubicon_data_prd_mst_hist c ON b.mdl_code = c.mdl_code {cond1_hist}{cond2_hist}{cond3_hist}
                AND c.site_cd = '{site_cd}'
                AND b.on_sale = 'X'
            WHERE b.disp_nm1 is not NULL
            AND b.disp_nm1 not in ('EMC', '안전인증정보', '기본정보', '상품기본정보')
            AND b.value not in ('-', 'N/A') 
            AND b.value is not NULL
            AND (a.mdl_code is not null or c.mdl_code is not null)
            ORDER BY goods_nm, mdl_code;
            """

                        else:

                            cond1 = (
                                ""
                                if product_category_lv1 in ["NA"]
                                else f"and c.category_lv1='{product_category_lv1}'"
                            )
                            cond2 = (
                                ""
                                if product_category_lv2 in ["NA"]
                                else f"and c.category_lv2='{product_category_lv2}'"
                            )
                            cond3 = (
                                ""
                                if product_category_lv3 in ["NA"]
                                else f"and c.category_lv3='{product_category_lv3}'"
                            )
                            
                            cond1_hist = (
                                ""
                                if product_category_lv1 in ["NA"]
                                else f"and d.category_lv1='{product_category_lv1}'"
                            )
                            cond2_hist = (
                                ""
                                if product_category_lv2 in ["NA"]
                                else f"and d.category_lv2='{product_category_lv2}'"
                            )
                            cond3_hist = (
                                ""
                                if product_category_lv3 in ["NA"]
                                else f"and d.category_lv3='{product_category_lv3}'"
                            )

                            sql = f"""SELECT coalesce(c.display_name, d.display_name) as display_name, 
                                coalesce(c.model_code, d.model_code) as model_code, 
                                'Color' as spec_type, 
                                '' as spec_name, 
                                b.colors as spec_value
            FROM rubicon_v3_complement_product_spec a
            LEFT JOIN rubicon_data_uk_product_spec_color b ON a.mdl_code = b.model_code
                AND a.on_sale != 'X'
            LEFT JOIN rubicon_data_uk_product_spec_basics c ON a.mdl_code = c.model_code {cond1}{cond2}{cond3}
                AND c.site_cd = '{site_cd}'
                AND a.on_sale != 'X'
            LEFT JOIN rubicon_data_uk_product_spec_basics_hist d ON a.mdl_code = d.model_code {cond1_hist}{cond2_hist}{cond3_hist}
                AND d.site_cd = '{site_cd}'
                AND a.on_sale = 'X'
            WHERE (c.model_code is not null or d.model_code is not null)
            UNION 
            SELECT coalesce(c.display_name, d.display_name) as display_name, 
                   coalesce(c.model_code, d.model_code) as model_code, 
                   a.disp_nm1 as spec_type, 
                   coalesce(a.disp_nm2,'') as spec_name, 
                   a.value as spec_value
            FROM rubicon_v3_complement_product_spec a
            LEFT JOIN rubicon_data_uk_product_spec_basics c ON a.mdl_code = c.model_code {cond1}{cond2}{cond3}
                AND c.site_cd = '{site_cd}'
                AND a.on_sale != 'X'
            LEFT JOIN rubicon_data_uk_product_spec_basics_hist d ON a.mdl_code = d.model_code {cond1_hist}{cond2_hist}{cond3_hist}
                AND d.site_cd = '{site_cd}'
                AND a.on_sale = 'X'
            WHERE a.disp_nm1 not in ('specHighlights', 'Network/Bearer')
            AND (a.value is not NULL or a.value = '-')
            AND a.site_cd = '{site_cd}'
            AND (c.model_code is not null or d.model_code is not null)
            ORDER BY display_name, model_code
            """
            
            # as all_spec
            # left join (select representative_model, 'Y' as recomm, sorting_no from rubicon_data_uk_product_recommend) as recomm
            # on all_spec.model_code = recomm.representative_model

                        cursor.execute(sql)
                        # cursor.execute(sql)
                        # o["sql_product"] = sql_product
                        sql_result = cursor.fetchall()
                        df = pd.DataFrame(
                            sql_result,
                            columns=[
                                "model_nm",
                                "model_cd",
                                "spec_lv1",
                                "spec_lv2",
                                "spec_value",
                            ],
                        )
                        
                        ### 기존 complement 로직 활용
                        if country_code == "KR":
                            is_merchandising = product_category_lv1 == "MERCHANDISING"
                            is_refrigrator = product_category_lv1 == "냉장고"
                            is_mobile = product_category_lv1 == "HHP"
                            is_printer = product_category_lv3 == "Printer"
                            is_external = (product_category_lv3 == "External HDD") or (
                                product_category_lv3 == "External SSD"
                            )
                            is_airdresser = product_category_lv3 in [
                                "Bespoke AirDresser",
                                "AirDresser",
                            ]
                            is_serif = product_category_lv3 == "The Serif"
                            
                            if len(df) > 0:
                            # print(df.apply(lambda row: clean_expression_kr(row['model_nm'], is_merchandising, is_refrigrator, is_mobile, is_printer, is_external, is_airdresser, is_serif), axis=1))
                                df["high_level"] = df.apply(
                                    lambda row: clean_expression_kr(
                                        row["model_nm"],
                                        is_merchandising,
                                        is_refrigrator,
                                        is_mobile,
                                        is_printer,
                                        is_external,
                                        is_airdresser,
                                        is_serif,
                                    ),
                                    axis=1,
                                )
                            else:
                                return result_dict, debug_list
                            # expression = clean_expression_kr(goods_nm, is_merchandising, is_refrigrator, is_mobile, is_printer, is_external, is_airdresser, is_serif)
                        elif country_code == "GB":
                            is_ha = product_category_lv1 == "Home Appliances"
                            is_mobile = product_category_lv1 == "Mobile"
                            is_printer = product_category_lv3 == "Printer"
                            is_external = (product_category_lv3 == "External HDD") or (
                                product_category_lv3 == "External SSD"
                            )
                            is_computer = product_category_lv1 == "Computers"
                            # expression = clean_expression_uk(goods_nm, model_code, is_ha, is_mobile, is_printer, is_external, is_computer)
                            if len(df) > 0:
                                df["high_level"] = df.apply(
                                    lambda row: clean_expression_uk(
                                        row["model_nm"],
                                        row["model_cd"],
                                        is_ha,
                                        is_mobile,
                                        is_printer,
                                        is_external,
                                        is_computer,
                                    ),
                                    axis=1,
                                )
                            else:
                                return result_dict, debug_list
                        
                        if len(df) > 0:
                            high_level_df = (
                                df[
                                    [
                                        "high_level",
                                        "spec_lv1",
                                        "spec_lv2",
                                        "spec_value",
                                        # "recomm_yn",
                                        # "sorting_no", 
                                    ]
                                ]
                                .drop_duplicates()
                                .dropna()
                            )

                            if _filter:
                                try:
                                    high_level_df = high_level_df[
                                        high_level_df["high_level"].str.contains(_filter[0][0])
                                    ]
                                except:
                                    pass

                            if len(high_level_df["high_level"].unique()) <= 10:
                                high_level_df_summ = (
                                    high_level_df.groupby(["high_level", "spec_lv1", "spec_lv2"])[
                                        "spec_value"
                                    ]
                                    .apply(lambda x: ",".join(x))
                                    .reset_index()
                                )
                            else:
                                top_high_level_lst = []
                                
                                rerank_df = rerank_db_results(
                                    query, high_level_df[['high_level']].drop_duplicates(), "high_level", 10, -1, skip_threshold=True, skip_cleaning=True
                                )

                                top_high_level_lst = rerank_df['high_level'].tolist()

                                # top_high_level_lst = (
                                #     (
                                #         high_level_df[high_level_df["recomm_yn"] == "Y"][
                                #             ["high_level", "sorting_no"]
                                #         ].drop_duplicates()
                                #     )
                                #     .sort_values(
                                #         by=["high_level", "sorting_no"], ascending=[False, True]
                                #     )["high_level"]
                                #     .unique()[0:10]
                                # )
                                high_level_df_summ = high_level_df[high_level_df["high_level"].isin(top_high_level_lst)][["high_level", "spec_lv1", "spec_lv2", "spec_value"]].drop_duplicates()
                                high_level_df_summ = high_level_df_summ.groupby(["high_level", "spec_lv1", "spec_lv2"])["spec_value"].apply(lambda x: ",".join(x)).reset_index()

                            # df["model"] = df.apply(
                            #     lambda row: row["model_nm"] + " (" + row["model_cd"] + ")", axis=1
                            # )
                            
                            high_level_df_summ["spec"] = high_level_df_summ.apply(
                                lambda row: row["spec_lv2"] + ": " + row["spec_value"], axis=1
                            )

                            # __log.debug(high_level_df_summ)
                            result = (
                                high_level_df_summ.groupby(["high_level", "spec_lv1"])
                                .apply(lambda x: "\n".join(x["spec"]))
                                .reset_index()
                            )
                            result.columns = ["high_level", "spec_lv1", "value_in_rows"]
                            final_result = pd.concat([final_result, result]).drop_duplicates()

                result_dict = {}
                idx = 0
                for _model in final_result["high_level"].unique():
                    # print(_model)
                    if idx < 10:
                        result_dict[_model] = make_data(
                            final_result[final_result["high_level"] == _model].copy()
                        )
                        idx += 1
                    else:
                        pass
    
    except:
        pass
        # return True
    return result_dict, debug_list


if __name__ == "__main__":

    code_mapping = [
          {
            "mapping_code": "갤럭시 Z 플립7 FE",
            "category_lv1": "HHP",
            "category_lv2": "NEW RADIO MOBILE (5G SMARTPHONE)",
            "category_lv3": "Galaxy Z Flip7 FE",
            "edge": "recommend",
            "meta": "",
            "extended_info": [
              "SM-F761NZKEKOO",
              "SM-F761NZWEKOO",
              "SM-F761NZWVKOO",
              "SM-F761NZKVKOO",
              "SM-F761NZKEKOD",
              "SM-F761NZWEKOD",
              "SM-F761NZKVKOD",
              "SM-F761NZWVKOD"
            ],
            "id": 0
          }
        ]
    country_code = "KR"

    # code_mapping = [
    #       {
    #         "mapping_code": "Bespoke AI Series 9 Laundry Front",
    #         "category_lv1": "Home Appliances",
    #         "category_lv2": "Washers and Dryers",
    #         "category_lv3": "Washing Machines",
    #         "edge": "recommend",
    #         "meta": "",
    #         "extended_info": [
    #           "WF90F09C4SU1"
    #         ],
    #         "id": 0
    #       },
    #       {
    #         "mapping_code": "Samsung Series 5 AI Energy WiFi-enabled, Washing Machine,",
    #         "category_lv1": "Home Appliances",
    #         "category_lv2": "Washers and Dryers",
    #         "category_lv3": "Washing Machines",
    #         "edge": "recommend",
    #         "meta": "",
    #         "extended_info": [
    #           "WW11DG5B25ABEU",
    #           "WW11DG5B25AEEU",
    #           "WW11DG5B25AHEU"
    #         ],
    #         "id": 1
    #       },
    #       {
    #         "mapping_code": "Samsung Series 6 AI Energy U U WiFi-enabled, Washing Machine,",
    #         "category_lv1": "Home Appliances",
    #         "category_lv2": "Washers and Dryers",
    #         "category_lv3": "Washing Machines",
    #         "edge": "recommend",
    #         "meta": "",
    #         "extended_info": [
    #           "WW90DG6U25LBU1",
    #           "WW90DG6U25LEU1"
    #         ],
    #         "id": 2
    #       }
    #     ]
    # country_code = "GB"
    ## 코드매핑의 type: p2p or h2h이고 intelligence가 product description인 경우
    query = "플립7 FE 는 컬러 뭐뭐 나와"
    __log.debug(high_level_specification_check(query, code_mapping, [], country_code))

