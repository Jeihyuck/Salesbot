import sys

sys.path.append("/www/alpha/")
import os
import django
import json

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "alpha.settings")
django.setup()

import pandas as pd
import pprint as p
from itertools import chain
from django.db import connection
from copy import deepcopy

from apps.rubicon_data.models import product_category, uk_product_spec_basics


def set_to_model(extended_code_mapping, site_cd, k=3):
    mapping_set = pd.DataFrame()
    filtered_mapping_set = pd.DataFrame()
    extended_code_mapping_tmp = []
    extended_code_mapping_final = []
    for data in extended_code_mapping:
        model_code = data.get("extended_info", [])

        with connection.cursor() as cursor:
            set_query = """
            select cs.model_code, sb.category_lv1 as cstrt_category_lv1, sb.category_lv2 as cstrt_category_lv2, sb.category_lv3 as cstrt_category_lv3, cs.cstrt_model_code, sb.display_name as cstrt_display_name from rubicon_data_uk_product_cstrt_info cs
            inner join rubicon_data_uk_product_spec_basics sb
            on sb.model_code = cs.cstrt_model_code 
            and sb.display = 'yes'
            and cs.model_code in %s
            and sb.site_cd = %s
            """
            product_codes_input = (
                model_code if len(model_code) > 1 else model_code + ["a"]
            )
            cursor.execute(set_query, [tuple(product_codes_input), site_cd])
            set_result = cursor.fetchall()

        if set_result:
            mapping_set_tmp = pd.DataFrame(
                set_result, columns=[c.name for c in cursor.description]
            )
            mapping_set = pd.concat([mapping_set, mapping_set_tmp], axis=0)
            mapping_list = mapping_set.to_dict("records")
            for d in mapping_list:
                tmp_dict = {}
                tmp_dict["mapping_code"] = d.get("cstrt_display_name", "")
                tmp_dict["extended_info"] = [d.get("cstrt_model_code", "")]

                tmp_dict["category_lv1"] = d.get("cstrt_category_lv1", "")
                tmp_dict["category_lv2"] = d.get("cstrt_category_lv2", "")
                tmp_dict["category_lv3"] = d.get("cstrt_category_lv3", "")
                tmp_dict["meta"] = "set_comp"

                extended_code_mapping_tmp.append(tmp_dict)

        extended_code_mapping_tmp = list(
            {
                json.dumps(d, sort_keys=True): d
                for d in extended_code_mapping_tmp.copy()
            }.values()
        )

    filtered_mapping_set = mapping_set

    if not filtered_mapping_set.empty:
        extended_code_mapping_tmp = [
            d
            for d in extended_code_mapping_tmp
            if d.get("extended_info")[0]
            in filtered_mapping_set["cstrt_model_code"].tolist()
        ]
        extended_code_mapping_final = extended_code_mapping + extended_code_mapping_tmp
    return filtered_mapping_set, extended_code_mapping_final


def specification_check(
    extended_code_mapping, country_code, is_pd_intelligence, site_cd="B2C"
):
    extended_code_mapping_new = []
    other_company_expression_list = []
    set_identified_model_markdown_tables = []
    identified_model_markdown_tables = []
    common_spec_tables = []
    spec_markdown_tables = []
    set_info_list = []
    total_spec_table = pd.DataFrame()
    df_identified_model = pd.DataFrame()
    bundle_component_dict = {}
    bundle_component_spec_tables = []
    grouped_bundle_spec_table = pd.DataFrame()
    name_code_dict = {}
    unique_model_code = set()

    sorted_diff_spec_table_cols = []

    debug_list = []

    if country_code == "GB":
        mapping_set, extended_code_mapping_new = set_to_model(
            extended_code_mapping, site_cd
        )
        if not mapping_set.empty:
            set_mdl_code = mapping_set["model_code"].unique().tolist()
            set_info_list = list(
                uk_product_spec_basics.objects.filter(
                    model_code__in=set_mdl_code,
                    site_cd=site_cd,
                ).values(
                    "category_lv1",
                    "category_lv2",
                    "category_lv3",
                    "display_name",
                    "model_code",
                    "launch_date",
                )
            )

            if set_info_list:
                set_identified_model = pd.DataFrame(set_info_list)
                set_identified_model.columns = [
                    "Category Lv1",
                    "Category Lv2",
                    "Category Lv3",
                    "Model Name",
                    "Model Code",
                    "Release Date",
                ]
                set_identified_model["Release Date"] = set_identified_model[
                    "Release Date"
                ].apply(lambda x: x.strftime("%Y-%m") if x is not None else x)
                component_codes = (
                    mapping_set.groupby("model_code")["cstrt_model_code"]
                    .apply(lambda x: ", ".join(x))
                    .reset_index()
                )
                component_codes.columns = ["Model Code", "Component Model Codes"]
                set_identified_model = pd.merge(
                    set_identified_model, component_codes, on="Model Code", how="left"
                )
                set_identified_model_markdown_tables.append(
                    set_identified_model.to_markdown(index=False)
                )

    if not extended_code_mapping_new:
        extended_code_mapping_new = deepcopy(extended_code_mapping)

    for item in extended_code_mapping_new:
        model_codes = item.get("extended_info", [])
        unique_model_code.update(model_codes)

    n_item = (
        3 if len(extended_code_mapping_new) == 1 or len(unique_model_code) <= 3 else 1
    )

    with connection.cursor() as cursor:
        for data in extended_code_mapping_new:
            bundle_dict = {}
            bundle_model_codes = []
            bundle_df = pd.DataFrame()

            o = {
                "data": data,
            }
            debug_list.append(o)

            product_category_lv1_placeholders = data.get("category_lv1", "")
            product_category_lv2_placeholders = data.get("category_lv2", "")
            product_category_lv3_placeholders = data.get("category_lv3", "")
            product_code_placeholders = data.get("extended_info", "")
            mapping_code_placeholders = data.get("mapping_code", "")

            other_company_expression = {
                "is_other_company": "other company" in data.get("category_lv2", ""),
                "other_company_expression": data.get("original_expression", ""),
                "samsung_expression": data.get("mapping_code", [""]),
            }

            if other_company_expression["is_other_company"]:
                other_company_expression_list.append(other_company_expression)

            if (
                not product_category_lv1_placeholders
                or not product_category_lv2_placeholders
                or not product_category_lv3_placeholders
                or not product_code_placeholders
                or not mapping_code_placeholders
            ):
                continue

            else:
                model_code_placeholders = data.get("extended_info", "")[:n_item]
                sorted_diff_spec_table_cols.extend(model_code_placeholders)
                if country_code == "KR":
                    # check bundle model code
                    bundle_sql = """
                    SELECT mdl_code
                    FROM rubicon_data_product_category
                    WHERE goods_tp_cd = '20'
                    AND mdl_code in %s
                    AND site_cd = %s
                    """

                    cursor.execute(
                        bundle_sql, [tuple(model_code_placeholders), site_cd]
                    )
                    bundle_results = cursor.fetchall()

                    # Return empty DataFrame if no results meet similarity threshold
                    if bundle_results:
                        # Create DataFrame with all results
                        bundle_model_codes = pd.DataFrame(
                            bundle_results,
                            columns=[c.name for c in cursor.description],
                        )["mdl_code"].tolist()

                        bundle_sql2 = """
                        SELECT distinct rdpc.goods_id, rdpc.mdl_code, rdpc.goods_nm, rdgci.cstrt_goods_id, rdgbo.mdl_code as cstrt_mdl_code, rdgbo.goods_nm as cstrt_nm, rdgci.conts_show_yn from rubicon_data_goods_cstrt_info rdgci
                            INNER JOIN rubicon_data_product_category rdpc ON rdgci.goods_id = rdpc.goods_id
                                AND rdpc.goods_tp_cd = '20'
                                AND rdgci.goods_cstrt_gb_cd = '10'		
                            INNER JOIN rubicon_data_goods_base rdgbo ON rdgci.cstrt_goods_id = rdgbo.goods_id
                            INNER JOIN rubicon_data_product_detail_spec_info rdpdc ON rdpdc.mdl_code = rdgbo.mdl_code 	
                        WHERE rdpc.mdl_code in %s 
                        AND rdpc.site_cd = %s
                        ORDER BY rdpc.mdl_code, rdgci.conts_show_yn DESC
                        LIMIT 5
                        """

                        cursor.execute(
                            bundle_sql2, [tuple(bundle_model_codes), site_cd]
                        )
                        bundle_products = cursor.fetchall()

                        if bundle_products:
                            # Create DataFrame with all results
                            bundle_df = pd.DataFrame(
                                bundle_products,
                                columns=[c.name for c in cursor.description],
                            )[["mdl_code", "cstrt_mdl_code"]].rename(
                                columns={
                                    "mdl_code": "Model Code",
                                    "cstrt_mdl_code": "Component Model Code",
                                }
                            )
                            bundle_dict = (
                                bundle_df.groupby("Model Code")["Component Model Code"]
                                .apply(list)
                                .to_dict()
                            )
                            bundle_code_placeholders = [
                                bundle_dict.get(item, item)
                                for item in model_code_placeholders
                            ]
                            bundle_code_placeholders = list(
                                chain.from_iterable(bundle_code_placeholders)
                            )

                            bundle_spec_sql = """
                            SELECT mdl_code, coalesce(disp_nm1, '-') as disp_nm1, coalesce(disp_nm2, '-') as disp_nm2, spec_value
                            FROM rubicon_data_product_detail_spec_info
                            WHERE mdl_code in %s
                            and disp_nm1 not in ('네트워크 (S/W 사용)', '안전인증정보', '인증정보', '법적필수고지정보','EMC', '안전 인증 정보', 'EMC')
                            and spec_value not in ('-', 'N/A') 
                            """

                            cursor.execute(
                                bundle_spec_sql,
                                [tuple(bundle_code_placeholders)],
                            )
                            bundle_spec_results = cursor.fetchall()

                            # Return empty DataFrame if no results meet similarity threshold
                            if bundle_spec_results:
                                # Create DataFrame with all results
                                bundle_spec = pd.DataFrame(
                                    bundle_spec_results,
                                    columns=[c.name for c in cursor.description],
                                )
                                bundle_spec.columns = [
                                    "Model Code",
                                    "Spec Lv1",
                                    "Spec Lv2",
                                    "Spec Value",
                                ]
                                bundle_spec["Spec Name"] = (
                                    bundle_spec["Spec Lv1"]
                                    + " : "
                                    + bundle_spec["Spec Lv2"]
                                )
                                bundle_spec = bundle_spec.drop(
                                    ["Spec Lv1", "Spec Lv2"], axis=1
                                )
                                bundle_spec = bundle_spec[
                                    ["Model Code", "Spec Name", "Spec Value"]
                                ].drop_duplicates()

                                grouped_bundle_spec_table = bundle_spec[
                                    bundle_spec["Spec Value"] != ""
                                ]

                model_code_placeholders = (
                    tuple(model_code_placeholders)
                    if len(model_code_placeholders) > 1
                    else ("('" + model_code_placeholders[0] + "')")
                )

                if country_code == "KR":
                    sql = f"""
                    select 
                        coalesce(b.product_category_lv1, c.product_category_lv1) as product_category_lv1, 
                        coalesce(b.product_category_lv2, c.product_category_lv2) as product_category_lv2, 
                        coalesce(b.product_category_lv3, c.product_category_lv3) as product_category_lv3, 
                        b.color as color, 
                        coalesce(b.goods_nm, c.goods_nm) as goods_nm, 
                        a.mdl_code, 
                        coalesce(a.disp_nm1, '-') as disp_nm1, 
                        coalesce(a.disp_nm2, '-') as disp_nm2, 
                        a.value,
                        coalesce(b.release_date, c.release_date) as release_date 
                    from
                        rubicon_v3_complement_product_spec a
                        left join rubicon_data_product_category b on a.mdl_code = b.mdl_code 
                            and b.product_category_lv1 = '{product_category_lv1_placeholders}'
                            and b.product_category_lv2 = '{product_category_lv2_placeholders}'
                            and b.product_category_lv3 = '{product_category_lv3_placeholders}'
                            and b.site_cd = '{site_cd}'
                            and a.on_sale != 'X'
                        left join rubicon_data_prd_mst_hist c on a.mdl_code = c.mdl_code
                            and c.product_category_lv1 = '{product_category_lv1_placeholders}'
                            and c.product_category_lv2 = '{product_category_lv2_placeholders}'
                            and c.product_category_lv3 = '{product_category_lv3_placeholders}'
                            and c.site_cd = '{site_cd}'
                            and a.on_sale = 'X'
                    where 
                        a.disp_nm1 not in ('네트워크 (S/W 사용)', '안전인증정보', '인증정보', '법적필수고지정보','EMC')
                        and a.value not in ('-', 'N/A') 
                        and a.mdl_code in {model_code_placeholders}
                        and (b.mdl_code is not null or c.mdl_code is not null)
                    order by 
                        a.disp_nm1, 
                        a.disp_nm2
                    """
                else:  # (2/5 UK대응) GB spec table 중 spec_name값이 안 들어가 있는 경우 데이터를 불러올 수 없어, spec_name is not null 조건 삭제
                    sql = f"""
                    select 
                        a.category_lv1, 
                        a.category_lv2, 
                        a.category_lv3, 
                        b.colors, 
                        a.goods_nm, 
                        a.mdl_code, 
                        coalesce(a.disp_nm1, '-') as disp_nm1, 
                        coalesce(a.disp_nm2, '-') as disp_nm2, 
                        a.value, 
                        coalesce(c.launch_date, d.launch_date) as launch_date 
                    from 
                        rubicon_v3_complement_product_spec a
                        left join rubicon_data_uk_product_spec_color b on a.mdl_code = b.model_code
                            and a.on_sale != 'X'
                        left join rubicon_data_uk_product_spec_basics c on a.mdl_code = c.model_code
                            and c.category_lv1 = '{product_category_lv1_placeholders}'
                            and c.category_lv2 = '{product_category_lv2_placeholders}'
                            and c.category_lv3 = '{product_category_lv3_placeholders}'
                            and c.site_cd = '{site_cd}'
                            and a.on_sale != 'X'
                        left join rubicon_data_uk_product_spec_basics_hist d on a.mdl_code = d.model_code
                            and d.category_lv1 = '{product_category_lv1_placeholders}'
                            and d.category_lv2 = '{product_category_lv2_placeholders}'
                            and d.category_lv3 = '{product_category_lv3_placeholders}'
                            and d.site_cd = '{site_cd}'
                            and a.on_sale = 'X'
                    where 
                        a.site_cd = '{site_cd}'
                        and (value is not NULL or value = '-')
                        and a.category_lv1 = '{product_category_lv1_placeholders}'
                        and a.category_lv2 = '{product_category_lv2_placeholders}'
                        and a.category_lv3 = '{product_category_lv3_placeholders}'
                        and a.mdl_code in {model_code_placeholders}
                        and (c.model_code is not null or d.model_code is not null)
                    order by 
                        a.disp_nm1, 
                        a.disp_nm2
                    """
                o["sql"] = sql

                cursor.execute(sql)
                results = cursor.fetchall()

                o["sql_result"] = p.pformat(
                    pd.DataFrame(
                        results,
                        columns=[c.name for c in cursor.description],
                    ).to_dict(orient="records")
                )

                # Return empty DataFrame if no results meet similarity threshold
                if not results:
                    df = pd.DataFrame()

                # Create DataFrame with all results
                df = pd.DataFrame(results, columns=[c.name for c in cursor.description])
                df.columns = [
                    "Category Lv1",
                    "Category Lv2",
                    "Category Lv3",
                    "Color",
                    "Model Name",
                    "Model Code",
                    "Spec Lv1",
                    "Spec Lv2",
                    "Spec Value",
                    "Release Date",
                ]

                df_spec_table = df[
                    ["Model Code", "Spec Lv1", "Spec Lv2", "Spec Value"]
                ].drop_duplicates()

                grouped_df_spec_table = df_spec_table[df_spec_table["Spec Value"] != ""]
                grouped_df_spec_table = grouped_df_spec_table[
                    ~grouped_df_spec_table["Model Code"].isin(bundle_model_codes)
                ]

                replace_sql = f"""
                    select 
                        model_code , coalesce(spec_lv1, '-') as spec_lv1, coalesce(spec_lv2, '-') as spec_lv2, spec_value
                    from 
                        rubicon_v3_spec_table_meta
                    where 
                        model_code in {model_code_placeholders}
                    order by spec_lv1, spec_lv2
                    """

                cursor.execute(replace_sql)
                replace_result = cursor.fetchall()

                replace_df = pd.DataFrame(
                    replace_result, columns=[c.name for c in cursor.description]
                )

                if replace_result:
                    replace_df.columns = [
                        "Model Code",
                        "Spec Lv1",
                        "Spec Lv2",
                        "Spec Value",
                    ]
                    merged = grouped_df_spec_table.merge(
                        replace_df,
                        on=["Model Code", "Spec Lv1", "Spec Lv2"],
                        how="outer",
                        suffixes=("", "_b"),
                    )
                    merged["Spec Value"] = merged["Spec Value_b"].combine_first(
                        merged["Spec Value"]
                    )

                    grouped_df_spec_table = merged[
                        ["Model Code", "Spec Lv1", "Spec Lv2", "Spec Value"]
                    ]

                total_spec_table = pd.concat(
                    [total_spec_table, grouped_df_spec_table], ignore_index=True
                )

                df = df.sort_values(by="Release Date", ascending=True)
                df["Release Date"] = df["Release Date"].apply(
                    lambda x: x.strftime("%Y-%m") if x is not None else x
                )
                df_identified_model = pd.concat(
                    [
                        df_identified_model,
                        df[
                            [
                                "Category Lv1",
                                "Category Lv2",
                                "Category Lv3",
                                "Model Name",
                                "Model Code",
                                "Release Date",
                            ]
                        ].drop_duplicates(),
                    ],
                    ignore_index=True,
                )

                name_code_dict = dict(
                    zip(
                        df_identified_model["Model Code"],
                        df_identified_model["Model Name"],
                    )
                )

                if not bundle_df.empty and country_code == "KR":
                    df_identified_model_tmp = df_identified_model[
                        df_identified_model["Model Code"].isin(
                            bundle_df["Model Code"].tolist()
                        )
                    ]
                    if "Component Model Code" in df_identified_model_tmp.columns:
                        df_identified_model_tmp = df_identified_model_tmp.drop(
                            ["Component Model Code"], axis=1
                        )
                    df_identified_model_tmp = pd.merge(
                        df_identified_model_tmp, bundle_df, on="Model Code"
                    )
                    if df_identified_model_tmp.empty and country_code == "KR":
                        bundle_target_model = bundle_df["Model Code"].tolist()
                        tmp_result = list(
                            product_category.objects.filter(
                                mdl_code__in=bundle_target_model,
                                site_cd=site_cd,
                            ).values(
                                "product_category_lv1",
                                "product_category_lv2",
                                "product_category_lv3",
                                "goods_nm",
                                "mdl_code",
                                "release_date",
                            )
                        )
                        if tmp_result:
                            df_identified_model_tmp = pd.DataFrame(tmp_result)
                            df_identified_model_tmp.columns = [
                                "Category Lv1",
                                "Category Lv2",
                                "Category Lv3",
                                "Model Name",
                                "Model Code",
                                "Release Date",
                            ]
                            df_identified_model_tmp = pd.merge(
                                df_identified_model_tmp, bundle_df, on="Model Code"
                            )
                    df_identified_model = pd.concat(
                        [df_identified_model, df_identified_model_tmp], axis=0
                    )
                    grouped_bundle_spec_table = grouped_bundle_spec_table.fillna(
                        "-"
                    ).reset_index()
                    if not grouped_bundle_spec_table.empty:
                        for comp in bundle_df["Component Model Code"]:
                            bundle_component_dict[comp] = grouped_bundle_spec_table[
                                grouped_bundle_spec_table["Model Code"] == comp
                            ].to_markdown(index=False)
                        bundle_component_spec_tables.append(bundle_component_dict)

        identified_model_markdown_tables.append(
            df_identified_model.to_markdown(index=False)
        )

        if not total_spec_table.empty:
            total_spec_table["Spec Name"] = (
                total_spec_table["Spec Lv1"] + " : " + total_spec_table["Spec Lv2"]
            )
            total_spec_table = total_spec_table.drop(["Spec Lv1", "Spec Lv2"], axis=1)
            total_spec_table = total_spec_table[
                ["Model Code", "Spec Name", "Spec Value"]
            ].drop_duplicates()

            model_code_count = total_spec_table["Model Code"].nunique()
            common_specs_tmp = (
                total_spec_table.groupby(["Spec Name", "Spec Value"])["Model Code"]
                .apply(set)
                .reset_index()
            )

            if not common_specs_tmp.empty:
                common_specs = (
                    common_specs_tmp[
                        common_specs_tmp["Model Code"].apply(
                            lambda x: len(x) == model_code_count
                        )
                    ]
                    .drop(["Model Code"], axis=1)
                    .reset_index(drop=True)
                )
                common_specs = common_specs.rename(
                    columns={"Spec Value": "Common Spec Value"}
                )
                common_spec_tables.append(common_specs.to_markdown(index=False))

                diff_spec_table = common_specs_tmp[
                    common_specs_tmp["Model Code"].apply(
                        lambda x: len(x) != model_code_count
                    )
                ]
                diff_spec_table["Model Code"] = (
                    diff_spec_table["Model Code"]
                    .astype(str)
                    .str.strip("{}")
                    .str.split(", ")
                )
                diff_spec_table = diff_spec_table.explode("Model Code")

                diff_spec_table = diff_spec_table.groupby(
                    ["Spec Name", "Model Code"], as_index=False
                ).first()
                diff_spec_table = diff_spec_table.pivot(
                    index=["Spec Name"], columns="Model Code", values="Spec Value"
                )

                sorted_diff_spec_table_cols = [
                    "'" + x + "'" for x in sorted_diff_spec_table_cols
                ]
                sorted_diff_spec_table_cols = [
                    x
                    for x in sorted_diff_spec_table_cols
                    if x in list(diff_spec_table.columns)
                ]

                # diff_spec_table.columns = [
                #     f"Spec Value ({col})" for col in diff_spec_table.columns
                # ]
                diff_spec_table = diff_spec_table[sorted_diff_spec_table_cols]
                diff_spec_table.columns = [
                    f"Spec Value ({name_code_dict.get(col.replace("'",''), 'None')}, '{col}')"
                    for col in sorted_diff_spec_table_cols
                ]

                diff_spec_table.columns.name = None
                diff_spec_table = diff_spec_table.fillna("-").reset_index()
                # diff_spec_table = diff_spec_table.dropna().reset_index()
                spec_markdown_tables.append(diff_spec_table.to_markdown(index=False))

        return (
            other_company_expression_list,
            set_identified_model_markdown_tables,
            identified_model_markdown_tables,
            common_spec_tables,
            spec_markdown_tables,
            bundle_component_spec_tables,
        ), debug_list
