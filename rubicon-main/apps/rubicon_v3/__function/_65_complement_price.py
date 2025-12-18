import sys

sys.path.append("/www/alpha/")
import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "alpha.settings")
django.setup()

import re
import pandas as pd
import numpy as np
import pytz
from apps.rubicon_v3.__function import __django_cache as django_cache
from apps.rubicon_data.models import product_category, uk_product_spec_basics
from apps.rubicon_v3.models import Complement_Product_Spec
from django.db import connection
from datetime import datetime
from word2number import w2n
from copy import deepcopy
from decimal import Decimal
import warnings

warnings.filterwarnings("ignore")

country_to_timezone = {"KR": "Asia/Seoul", "GB": "Europe/London"}

telecom_dict = {"KTF": "KT", "LGT": "LG U+", "SKT": "SK telecom"}

telecom_dc_dict = {
    "10": "공시지원금 할인",
    "20": "12개월 선택약정 할인",
    "30": "24개월 선택약정 할인",
}
telecom_join_dict = {"10": "기기변경", "20": "번호이동", "30": "신규가입"}

django_cache_client = django_cache.DjangoCacheClient()


def get_current_time_by_country_code(country_code):
    if country_code in country_to_timezone:
        timezone = pytz.timezone(country_to_timezone[country_code])
        current_time = datetime.now(timezone)
        return current_time.strftime("%Y-%m-%d %H:%M:%S")
    else:
        return "Not supported country code"


"""
Function to convert Korean-style price expressions into numeric values
"""
def convert_price(price):
    amount_mapping = {
        "천만원": 10000000,
        "백만원": 1000000,
        "십만원": 100000,
        "만원": 10000,
        "만": 10000,
        "천원": 1000,
        "백원": 100,
        "원": 1,
        "억원": 100000000,
    }
    match = re.match(r"(\d+)\s*(억원|만원|천원|백원|원|만|십만원|백만원)?", price)
    if match:
        amount = int(match.group(1))
        unit = match.group(2)
        multiplier = amount_mapping.get(unit, 1)
        return amount * multiplier
    return 0


"""
Function 2 to convert Korean-style price expressions into numeric values
"""
def kr_to_number(text):
    text = text.replace("₩", "")
    num_dict = {
        "일": 1,
        "이": 2,
        "삼": 3,
        "사": 4,
        "오": 5,
        "육": 6,
        "칠": 7,
        "팔": 8,
        "구": 9,
        "영": 0,
    }
    unit_dict = {"십": 10, "백": 100, "천": 1000, "만": 10000, "억": 100000000}

    split_pattern = r"(억|만)"
    parts = re.split(f"({split_pattern})", text)
    result = 0
    temp = 0
    for part in parts:
        if not part:
            continue

        if part in unit_dict and unit_dict[part] >= 10000:
            result += temp * unit_dict[part]
            temp = 0
        else:
            num = 0
            unit = 1
            for char in part:
                if char in num_dict:
                    num = num_dict[char]
                elif char in unit_dict:
                    unit = unit_dict[char]
                    if num == 0:
                        num = 1
                    temp += num * unit
                    num = 0
            temp += num
    result += temp

    return result


"""
Function to convert UK price expressions into numeric values.
"""
def gb_to_number(text):
    try:
        text = text.replace("£", "")
        answer = w2n.word_to_num(text)
    except Exception as e:
        answer = 0
    return answer


"""
A function that, when a conditional price query targets a product, retrieves the product's actual price and substitutes it as the reference value for the condition. 
For example, in the query "Recommend phones more expensive than Galaxy S25 Ultra," the function fetches the Galaxy S25 Ultra's price and transforms the query into "Recommend phones more expensive than 1,000,000 won."
"""
def switch_price_standard(
    NER_output_operator_tmp, price_operator_dict_tmp, country_code, site_cd
):
    for product, details in price_operator_dict_tmp.items():
        for key in details.keys():
            if key in ["greater_than", "less_than", "about"]:
                prices = pd.DataFrame()
                codes = details[key]
                if country_code == "KR":
                    prices = kr_price_db(codes, site_cd)
                elif country_code == "GB":
                    prices = gb_price_db(codes, site_cd)
                else:
                    raise ValueError(f"Unsupported country code: {country_code}")

                if not prices.empty:
                    prices["tmp_price"] = prices[
                        ["standard_price", "benefit_price"]
                    ].min(axis=1)
                    for items in NER_output_operator_tmp:
                        if items["operator"] == key:
                            if key == "greater_than":
                                items["expression"] = str(prices["tmp_price"].max())
                            elif key == "less_than":
                                items["expression"] = str(prices["tmp_price"].min())
                            elif key == "about":
                                items["expression"] = str(prices["tmp_price"].mean())

    return NER_output_operator_tmp

"""
Process the conditional price function using the minimum value between the base price and the benefit price as the reference, 
applying the logic for greater than, less than, min, max, and about accordingly.
"""
def price_operator(NER_output_operator, group_final_df, country_code):
    final_df = deepcopy(group_final_df)
    new_operator_dict = {}
    no_model_range_flag = False
    final_df_operator = pd.DataFrame()
    final_df["tmp_price"] = final_df[["standard_price", "benefit_price"]].min(axis=1)
    final_df['tmp_price'] = pd.to_numeric(final_df['tmp_price'], errors='coerce')

    for items in NER_output_operator:
        actual_values = []
        price_standard = [
            word
            for word in items["expression"].replace(" ", "").split()
            if any(char.isdigit() for char in word)
        ]
        # Convert price-related expressions into actual numbers to construct new_operator_dict
        # for example: {'greater_than': [1000000], 'less_than': [2000000]}, where each condition is paired with its corresponding reference value.
        actual_values = sorted(
            [
                convert_price(price)
                for price in price_standard
                if convert_price(price) > 0
            ]
        )
        if not actual_values and country_code == "KR":
            actual_values = sorted(
                [
                    kr_to_number(word["expression"])
                    for word in [items]
                    if kr_to_number(word["expression"]) > 10
                ]
            )

        if not actual_values and country_code == "GB":
            actual_values = sorted(
                [
                    gb_to_number(word["expression"])
                    for word in [items]
                    if gb_to_number(word["expression"]) > 0
                ]
            )
        
        if actual_values or items.get('operator') in ['min','max']:
            if items["operator"] in new_operator_dict:
                new_operator_dict[items["operator"]].extend(actual_values)

            else:
                new_operator_dict[items["operator"]] = actual_values
    
    if new_operator_dict:
        # greater than, less than to between
        # ex) {'greater_than': [1000000], 'less_than': [2000000]} -> {'between': [1000000, 2000000]} 
        if (
            "greater_than" in new_operator_dict.keys()
            and "less_than" in new_operator_dict.keys()
        ):

            if (
                len(new_operator_dict["greater_than"]) > 0
                and all(
                    isinstance(value, (int, float))
                    for value in new_operator_dict["greater_than"]
                )
                and len(new_operator_dict["less_than"]) > 0
                and all(
                    isinstance(value, (int, float))
                    for value in new_operator_dict["less_than"]
                )
            ):
                if max(new_operator_dict["greater_than"]) < min(
                    new_operator_dict["less_than"]
                ):
                    new_operator_dict.update(
                        {
                            "between": [
                                max(new_operator_dict["greater_than"]),
                                min(new_operator_dict["less_than"]),
                            ]
                        }
                    )
                    del new_operator_dict["greater_than"]
                    del new_operator_dict["less_than"]

        # about to between
        # ex) {'about': [1000000]} -> {'between': [900000, 1100000]}
        if (
            "about" in new_operator_dict.keys()
            and len(new_operator_dict["about"]) > 0
            and all(isinstance(value, (int, float)) for value in new_operator_dict["about"])
        ):

            new_operator_dict.update(
                {
                    "between": [
                        min(new_operator_dict["about"]) * 0.9,
                        min(new_operator_dict["about"]) * 1.1,
                    ]
                }
            )
            del new_operator_dict["about"]
            
        # After processing the new operator dictionary, perform filtering. Convert expressions of 'greater than' and 'less than' into 'between' when possible, and also convert 'about' into 'between' for consistent filtering logic.
        
        # greater than
        if (
            "greater_than" in new_operator_dict.keys()
            and len(new_operator_dict["greater_than"]) > 0
            and all(
                isinstance(value, (int, float))
                for value in new_operator_dict["greater_than"]
            )
        ):
            final_df_tmp = final_df[
                final_df["tmp_price"] >= max(new_operator_dict["greater_than"])
            ]
            if final_df_tmp.empty: # if there are no prices that satisfy the condition, select the three most expensive model codes.
                final_df_tmp = final_df.nlargest(3, 'tmp_price')
                no_model_range_flag = True # no model range flag
            final_df_operator = pd.concat([final_df_operator, final_df_tmp], axis=0)

        # less than 
        if (
            "less_than" in new_operator_dict.keys()
            and len(new_operator_dict["less_than"]) > 0
            and all(
                isinstance(value, (int, float)) for value in new_operator_dict["less_than"]
            )
        ):
            final_df_tmp = final_df[
                final_df["tmp_price"] <= min(new_operator_dict["less_than"])
            ]

            if final_df_tmp.empty:
                final_df_tmp = final_df.nsmallest(3, 'tmp_price') # if there are no prices that satisfy the condition, select the three cheapest model codes.
                no_model_range_flag = True # no model range flag 
            final_df_operator = pd.concat([final_df_operator, final_df_tmp], axis=0)
        
        # between
        if "between" in new_operator_dict.keys() and all(
            isinstance(value, (int, float)) for value in new_operator_dict["between"]
        ):
            final_df_tmp = final_df[
                (final_df["tmp_price"] <= max(new_operator_dict["between"]))
                & (final_df["tmp_price"] >= min(new_operator_dict["between"]))
            ]

            if final_df_tmp.empty: # if there are no prices that satisfy the condition 
                max_value = final_df[
                    final_df["tmp_price"] > max(new_operator_dict["between"])
                ]["tmp_price"].min()
                final_df_tmp = final_df[final_df["tmp_price"] == max_value] # 

                min_value = final_df[
                    final_df["tmp_price"] < min(new_operator_dict["between"])
                ]["tmp_price"].max()
                final_df_tmp2 = final_df[final_df["tmp_price"] == min_value]
                final_df_tmp = pd.concat([final_df_tmp, final_df_tmp2], axis=0)
                no_model_range_flag = True
            final_df_operator = pd.concat([final_df_operator, final_df_tmp], axis=0)

        if "max" in new_operator_dict.keys():
            if not final_df_operator.empty:
                final_df_operator = final_df_operator.nlargest(3, 'tmp_price')
            else:
                if len(new_operator_dict["max"]) > 0 and all(
                    isinstance(value, (int, float)) for value in new_operator_dict["max"]
                ):
                    final_df_tmp = final_df[
                        final_df["tmp_price"] <= min(new_operator_dict["max"])
                    ]
                    if final_df_tmp.empty:
                        final_df_tmp = final_df.nsmallest(3, 'tmp_price')
                        no_model_range_flag = True

                else:
                    final_df_tmp = final_df.nlargest(3, 'tmp_price')

                final_df_operator = pd.concat([final_df_operator, final_df_tmp], axis=0)
            final_df_operator = final_df_operator.sort_values('tmp_price', ascending=False).reset_index(drop=True) # add: sort values

        if "min" in new_operator_dict.keys():
            if not final_df_operator.empty:
                final_df_operator = final_df_operator.nsmallest(3, 'tmp_price')
            else:
                if len(new_operator_dict["min"]) > 0 and all(
                    isinstance(value, (int, float)) for value in new_operator_dict["min"]
                ):
                    final_df_tmp = final_df[
                        final_df["tmp_price"] >= max(new_operator_dict["min"])
                    ]
                    if final_df_tmp.empty:
                        final_df_tmp = final_df.nlargest(3, 'tmp_price')
                        no_model_range_flag = True
                else:
                    final_df_tmp = final_df.nsmallest(3, 'tmp_price')

                final_df_operator = pd.concat([final_df_operator, final_df_tmp], axis=0)
            final_df_operator = final_df_operator.sort_values('tmp_price', ascending=True).reset_index(drop=True) # add: sort values

        if not final_df_operator.empty:
            final_filtered_df = final_df_operator.drop(["tmp_price"], axis=1)

        if final_df_operator.empty and not final_df.empty:
            final_filtered_df = final_df.drop(["tmp_price"], axis=1)
            no_model_range_flag = True
            
    else:
        final_filtered_df = final_df.drop(["tmp_price"], axis=1)

    return final_filtered_df, no_model_range_flag

"""
Function to attach model names to model codes (for both on sale and display products only)
"""
def simple_add_name(product_codes, country_code, site_cd):
    model_name_result = []
    final_df = pd.DataFrame()
    
    if country_code == "KR":
        model_name_result = list(product_category.objects.filter(
            mdl_code__in=product_codes, site_cd=site_cd, goods_stat_cd = '30', show_yn = 'Y'
        ).values("goods_nm", "mdl_code"))

    elif country_code == "GB":
        model_name_result = list(uk_product_spec_basics.objects.filter(
            model_code__in=product_codes, site_cd=site_cd,
        ).values("display_name", "model_code"))
    
    else:
        raise ValueError(f"Unsupported country code: {country_code}")

    if model_name_result:
        final_df = pd.DataFrame(model_name_result)
        final_df.columns = ["Model Name", "Model Code"]
        final_df = final_df.drop_duplicates()

    return final_df


"""
Function that appends model names to the price table and creates 'group' and 'id_2' columns.
"""
def add_name_ordering(extended_code_mapping, final_df, code_id, country_code, site_cd, min_max_operator):
    model_name = simple_add_name(final_df["Model Code"].tolist(), country_code, site_cd)
    if not model_name.empty:
        final_df = pd.merge(final_df, model_name, on="Model Code")
        last_col = final_df.iloc[:, -1]
        final_df = pd.concat([last_col, final_df.iloc[:, :-1]], axis=1)
        
        # ordering from code - id
        model_codes = final_df["Model Code"].tolist()
        tmp_order = pd.DataFrame(extended_code_mapping)
        tmp_order['group'] = (tmp_order['id']==0).cumsum()
        tmp_order = tmp_order.explode('extended_info')[['extended_info','group']]
        tmp_order.columns = ["Model Code", "group"]
        code_id = pd.merge(code_id, tmp_order, on="Model Code")
        #code_id["id_2"] = code_id.groupby("group").cumcount() + 1
        order_df = code_id[code_id["Model Code"].isin(model_codes)].reset_index(drop=True)
        
        final_df = final_df.drop(['id', 'group'], axis=1, errors='ignore') #merge 시 중복 칼럼 방지
        final_df = pd.merge(order_df, final_df, on="Model Code", how= "right")
        final_df = final_df.drop_duplicates(subset=["Model Code"], keep="first")
        final_df["id_2"] = final_df.groupby("group").cumcount() + 1 #add (min_max 순서 지켜서 id_2 부여하기 위해 뒤로 뺌)
        
    else:
        final_df = pd.DataFrame()

    return final_df

"""
Filters the final price table using the generated 'group' and 'id_2' values, and filters the input extended code mapping to include only those products present in the price table, providing the filtered extended code mapping.
"""
def filter_by_group_id(df, k):
    if len(set(df['group'])) == 1:
        if df['id'].nunique() == 1:
            return df.head(3).drop(["id", "group", "id_2"], axis=1)
        else:
            sort_df = df.sort_values(by='id_2')
            group_df = sort_df.groupby(['id']).head(1).reset_index().iloc[:k].drop(["id", "group", "id_2"], axis=1)
            return group_df
    elif len(set(df['group'])) > 1:
        sort_df = df.sort_values(by='id_2')
        group_df = sort_df.groupby(['group', 'id']).head(1)
        final_sort_df = group_df.sort_values(by=['id_2','group']).reset_index().iloc[:k].drop(["id", "group", "id_2"], axis=1)
        return final_sort_df
    else:
        return df.drop(["id", "group", "id_2"], axis=1, errors='ignore').reset_index().iloc[:k]

def final_filter(extended_code_mapping, final_df, set_code_id, k, min_max_operator, grouped_extended_code_mappings):
    filtered_extended_code_mapping = []
    filtered_df = pd.DataFrame()
    common_values = set()
    mapping_list = [item.get("mapping_code", "") for item in extended_code_mapping]
    mapping_set = {item for item in set(mapping_list) if '(' not in item and ')' not in item}
    mapping_set.discard('Galaxy S25 Ultra Enterprise Edition')

    if not set_code_id.empty:
        final_df = final_df[final_df['Model Code'].isin(set_code_id["Model Code"].tolist())]
        set_dict = dict(zip(set_code_id['Model Code'],set_code_id['id']))
        final_df['id_2'] = final_df['Model Code'].map(set_dict)
        final_df = final_df.sort_values(by='id_2').reset_index(drop=True)
    
    skip_common_values = False
    if min_max_operator is not None:
        skip_common_values = True
                            
    if "Storage" in final_df.columns and len(final_df)>3:
        tmp_df = final_df.groupby('group')['Storage'].agg(set).reset_index()
        if not tmp_df.empty:
            if set(['갤럭시 S25 울트라', '갤럭시 S25+', '갤럭시 S25', '갤럭시 S25 엣지']).issubset(set(mapping_list)):
                    k=4
            common_values = set(tmp_df['Storage'].iloc[0])
            for values in tmp_df['Storage'][1:]:
                common_values.intersection_update(values)
            if len(set(final_df['group'])) == 1:
                if final_df['id'].nunique() == 1:  
                    if final_df['Storage'].nunique() == 1:
                        filtered_df = filter_by_group_id(final_df, k)
                    else:
                        filtered_df = final_df.groupby(["Storage"]).head(1).reset_index().iloc[:k].drop(["id", "group", "id_2"], axis=1)
                else:
                    if (final_df['id'].nunique()) >1:
                        if common_values and skip_common_values==False: #min_max_operator 있을 때는 용량 맞추기 pass
                            final_common_values = max(common_values) #max로 변경
                            filtering = final_df['Model Name'].apply(lambda x: any(name in x for name in mapping_set) if isinstance(x, str) else False)
                            common_filtered_df = final_df[filtering &(final_df['Storage']==final_common_values)]
                            filtered_df = common_filtered_df.groupby(["id"]).head(1).reset_index().iloc[:k]
                            if filtered_df.empty:
                                filtered_df = final_df[final_df['Storage']==final_common_values].groupby(["id"]).head(1).reset_index().iloc[:k]
                        else:
                            filtered_df = filter_by_group_id(final_df, k)
            elif len(set(final_df['group'])) > 1:
                if common_values and skip_common_values==False: #min_max_operator 있을 때는 용량 맞추기 pass
                    final_common_values = max(common_values) #max로 변경
                    filtering = final_df['Model Name'].apply(lambda x: any(name in x for name in mapping_set))
                    common_filtered_df = final_df[filtering &(final_df['Storage']==final_common_values)]
                    filtered_df = filter_by_group_id(common_filtered_df, k)
                    if filtered_df.empty:
                        filtered_df = final_df[final_df['Storage']==final_common_values].groupby(["group"]).head(1).reset_index().iloc[:k]
                else:
                    filtered_df = filter_by_group_id(final_df, k)
        else:
            filtered_df = final_df.groupby(["id", "Storage"]).head(1).reset_index().iloc[:k]
            
        if not filtered_df.empty:
            filtered_df = filtered_df[
                [
                    "Model Name",
                    "Model Code",
                    "Storage",
                    "color",
                    "standard_price",
                    "benefit_price",
                ]
            ]
            
    elif len(final_df)>3:
        filtered_df = filter_by_group_id(final_df, k)
    
    else:
        filtered_df = final_df.drop(["id","group","id_2"], axis=1)

    # Filter the model codes in the extended code mapping to include only those present in the final filtered DataFrame.
    for item in extended_code_mapping:
        if not filtered_df.empty and filtered_df["Model Code"].tolist():
            filtered_item = item.copy()
            filtered_item["extended_info"] = [
                info
                for info in item["extended_info"]
                if info in filtered_df["Model Code"].tolist()
            ]
            if filtered_item["extended_info"]:
                filtered_extended_code_mapping.append(filtered_item)

    return filtered_extended_code_mapping, filtered_df
          
"""
Function to retrieve prices for KR
"""
def kr_price_db(product_codes, site_cd):
    combined = pd.DataFrame()
    with connection.cursor() as cursor:
        price_query = """
        SELECT price.sale_prc1, price.sale_prc2, price.sale_prc3, price.mdl_code, price.color
        FROM (
        SELECT a.sale_prc1
            ,a.sale_prc2
            ,a.sale_prc3
            ,c.mdl_code
            ,c.color
            ,a.sys_reg_dtm
            ,row_number() over(partition by c.mdl_code order by a.sys_reg_dtm desc) as rank 
        FROM rubicon_data_goods_price a, rubicon_data_product_category c
        WHERE c.mdl_code IN %s
        AND a.goods_id = c.goods_id
        AND c.goods_stat_cd = '30'
        AND c.show_yn = 'Y'
        AND a.sale_strt_dtm <= %s
        AND a.sale_end_dtm >= %s
        AND c.site_cd = %s) price
        where price.rank = 1
        """
        now = datetime.strptime(
            get_current_time_by_country_code("KR"), "%Y-%m-%d %H:%M:%S"
        )
        product_codes_input = (
            product_codes if len(product_codes) > 1 else product_codes + ["a"]
        )
        cursor.execute(price_query, [tuple(product_codes_input), now, now, site_cd])
        price_results = cursor.fetchall()
        if price_results:
            combined = pd.DataFrame(
                price_results, columns=[c.name for c in cursor.description]
            )
            combined = combined.rename(
                columns={
                    "sale_prc1": "standard_price",
                    "sale_prc2": "member_price",
                    "sale_prc3": "benefit_price",
                    "mdl_code": "Model Code"
                }
            )
            spec_results = list(Complement_Product_Spec.objects.filter(
                mdl_code__in=combined['Model Code'].tolist(), site_cd = site_cd
            ).values("mdl_code","disp_nm2", "value"))
            
            if spec_results:
                spec_combined = pd.DataFrame(spec_results)
                if any(spec in spec_combined["disp_nm2"].unique()for spec in ["스토리지(저장 용량) (TB)", "스토리지(저장 용량) (GB)"]):
                    spec_combined = spec_combined[
                        spec_combined["disp_nm2"].isin(
                            ["스토리지(저장 용량) (TB)", "스토리지(저장 용량) (GB)"]
                        )
                    ]
                    spec_combined = spec_combined.dropna()
                    spec_combined = spec_combined.rename(columns={"mdl_code":"Model Code"})
                    spec_combined['value'] = spec_combined['value'].replace('1024 GB', '1 TB')
                    combined = pd.merge(combined, spec_combined, on='Model Code', how='left')
                    combined['disp_nm2'] = combined['disp_nm2'].fillna('-')
                    combined['value'] = combined['value'].fillna('-')
                    
                    combined = combined.rename(columns = {"value": "Storage"})
                    combined = (
                        combined[
                            [
                                "Model Code",
                                "Storage",
                                "color",
                                "standard_price",
                                "benefit_price",
                            ]
                        ]
                        .sort_values(by=["Storage", "color"])
                        .reset_index(drop=True)
                    )
                else:
                    combined = (
                        combined
                        .drop_duplicates()
                        .reset_index(drop=True)
                    )
                    combined = (
                        combined[["Model Code", "color", "standard_price", "benefit_price"]]
                        .sort_values(by=["color"])
                        .reset_index(drop=True)
                    )
                    
            else:
                combined = (
                    combined
                    .drop_duplicates()
                    .reset_index(drop=True)
                )
                combined = (
                    combined[["Model Code", "color", "standard_price", "benefit_price"]]
                    .sort_values(by=["color"])
                    .reset_index(drop=True)
                )
        if not combined.empty:
            combined["Model Code"] = combined["Model Code"].astype(str)
            combined = combined.set_index("Model Code").loc[
                [code for code in product_codes if code in combined["Model Code"].values]
            ].reset_index() # db 검색 후 extended info에 잡힌 순서대로 정렬하기

    return combined


"""
Function to retrieve prices for GB
"""
def gb_price_db(product_codes, site_cd):
    combined = pd.DataFrame()
    with connection.cursor() as cursor:
        price_query = """
        SELECT a.model_code, a.price, a.tiered_price, a.promotion_price, b.colors, c.disp_nm2, c.value
        FROM rubicon_data_uk_model_price a, rubicon_data_uk_product_spec_color b, rubicon_v3_complement_product_spec c
        WHERE a.model_code IN %s
        AND a.model_code = b.model_code
        AND b.model_code = c.mdl_code
        AND a.salesstatus = 'PURCHASABLE'
        AND a.site_cd = %s
        """
        product_codes_input = (
            product_codes if len(product_codes) > 1 else product_codes + ["a"]
        )
        cursor.execute(price_query, [tuple(product_codes_input), site_cd])
        price_results = cursor.fetchall()

        if price_results:
            combined = pd.DataFrame(
                price_results, columns=[c.name for c in cursor.description]
            )
            combined = combined.rename(
                columns={
                    "price": "standard_price",
                    "tiered_price": "member_price",
                    "promotion_price": "benefit_price",
                    "model_code": "Model Code",
                    "colors": "color",
                }
            )
            if any(
                spec in combined["disp_nm2"].unique()
                for spec in ["Storage (TB)", "Storage (GB)"]
            ):
                combined = combined[
                    combined["disp_nm2"].isin(["Storage (TB)", "Storage (GB)"])
                ]
                combined = combined[combined["value"].notna()].reset_index(drop=True)
                combined = combined.rename(columns={"value": "Storage"})
                combined["Storage"] = combined["Storage"].replace("1024 GB", "1 TB")
                combined = (
                    combined[
                        [
                            "Model Code",
                            "Storage",
                            "color",
                            "standard_price",
                            "benefit_price",
                        ]
                    ]
                    .sort_values(by=["Storage", "color"])
                    .reset_index(drop=True)
                )
            else:
                combined = combined.drop(
                    ["disp_nm2", "value"], axis=1
                ).drop_duplicates()
                combined = (
                    combined[["Model Code", "color", "standard_price", "benefit_price"]]
                    .sort_values(by=["color"])
                    .reset_index(drop=True)
                )
        if not combined.empty:
            combined["Model Code"] = combined["Model Code"].astype(str)
            combined = combined.set_index("Model Code").loc[
                [code for code in product_codes if code in combined["Model Code"].values]
            ].reset_index() # db 검색 후 extended info에 잡힌 순서대로 정렬하기
        
    return combined

"""
KR - Carrier price inquiry function
"""
def telecom_price(final_df, site_cd):
    product_codes = final_df["Model Code"].tolist()
    telecom_df = pd.DataFrame()
    result_dict = {}
    with connection.cursor() as cursor:
        tel_query = """     
        SELECT distinct amb.mdl_code, akmp.carrier_cd, pp.m_pt_nm, akmp.plan_join_tp_cd ,akmp.plan_dc_tp_cd , akmp.pay_amt, min(akmp.pay_amt) over (partition by amb.mdl_code) as min_pay_amt
        FROM (select * from rubicon_data_activate_model_base amb where amb.site_cd = %s) as amb
        INNER JOIN
        (select * from rubicon_data_activate_key_model_price akmp where akmp.site_cd = %s) as akmp
        ON amb.key_mdl_code = akmp.key_mdl_code
        INNER JOIN ( 
   		SELECT row_number() OVER(PARTITION BY actv_phone_plan_seq, actv_phone_plan_ver) AS row_num, * 
		    FROM (select * from rubicon_data_activate_phone_plan pp where pp.site_cd = %s)
		) AS pp  
		ON akmp.key_mdl_code = pp.key_mdl_code 
		AND akmp.m_pt_cd = pp.m_pt_cd
        AND amb.mdl_code in %s;
        """
        product_codes_input = (
            product_codes if len(product_codes) > 1 else product_codes + ["a"]
        )
        cursor.execute(tel_query, [site_cd, site_cd, site_cd, tuple(product_codes_input)])
        tel_results = cursor.fetchall()
        if tel_results:
            telecom_df = pd.DataFrame(
                tel_results, columns=[c.name for c in cursor.description]
            )
            telecom_df = telecom_df[telecom_df["pay_amt"] == telecom_df["min_pay_amt"]]
            telecom_df = telecom_df.drop(["min_pay_amt"], axis=1)
            telecom_df = telecom_df.drop_duplicates()
            telecom_df = (
                telecom_df.groupby("mdl_code", as_index=False)
                .first()
                .reset_index(drop=True)
            )
            telecom_df["pay_amt"] = telecom_df["pay_amt"].astype(str) + " 원"
            telecom_df["plan_join_tp_cd"] = (
                telecom_df["plan_join_tp_cd"].map(telecom_join_dict).fillna("기타")
            )
            telecom_df["plan_dc_tp_cd"] = (
                telecom_df["plan_dc_tp_cd"].map(telecom_dc_dict).fillna("기타")
            )
            telecom_df["carrier_cd"] = (
                telecom_df["carrier_cd"].map(telecom_dict).fillna("기타")
            )
            telecom_df["condition"] = (
                telecom_df["carrier_cd"]
                + "/"
                + telecom_df["plan_join_tp_cd"]
                + "/"
                + telecom_df["plan_dc_tp_cd"]
                + "/"
                + telecom_df["m_pt_nm"]
                + " 선택 시"
            )

            telecom_df = telecom_df[["mdl_code", "pay_amt", "condition"]]
            telecom_df.columns = ["Model Code", "월 납부 예상금액", "조건"]

            for code in product_codes:
                filtered_telecom_df = telecom_df[telecom_df["Model Code"] == code].drop(
                    ["Model Code"], axis=1
                )
                if not filtered_telecom_df.empty:
                    result_dict[code] = filtered_telecom_df.to_markdown(index=False)

    return result_dict

"""
KR Family Net price inquiry function
"""
def kr_price_db_FNET(product_codes, site_cd):
    combined = pd.DataFrame()
    with connection.cursor() as cursor:
        price_query = """
        SELECT price.sale_prc1, price.sale_prc2, price.sale_prc3, price.mdl_code, price.color
        FROM (
        SELECT a.sale_prc1
            ,a.sale_prc2
            ,a.sale_prc3
            ,c.mdl_code
            ,c.color
            ,a.sys_reg_dtm
            ,row_number() over(partition by c.mdl_code order by a.sys_reg_dtm desc) as rank 
        FROM rubicon_data_goods_price a, rubicon_data_product_category c
        WHERE c.mdl_code IN %s
        AND a.goods_id = c.goods_id
        AND c.goods_stat_cd = '30'
        AND c.show_yn = 'Y'
        AND a.sale_strt_dtm <= %s
        AND a.sale_end_dtm >= %s
        AND c.site_cd = %s) price
        where price.rank = 1
        """
        now = datetime.strptime(
            get_current_time_by_country_code("KR"), "%Y-%m-%d %H:%M:%S"
        )
        product_codes_input = (
            product_codes if len(product_codes) > 1 else product_codes + ["a"]
        )
        cursor.execute(price_query, [tuple(product_codes_input), now, now, site_cd])
        price_results = cursor.fetchall()

        if price_results:
            combined = pd.DataFrame(
                price_results, columns=[c.name for c in cursor.description]
            )
            combined = combined.rename(
                columns={
                    "sale_prc1": "standard_price",
                    "sale_prc2": "member_price",
                    "sale_prc3": "benefit_price",
                    "mdl_code": "Model Code"
                }
            )
            
            discount = combined["benefit_price"].apply(lambda x: Decimal(x) * Decimal('0.25'))
            discount = discount.apply(lambda x: int(np.round(int(x+1) / 100.0) * 100))
            combined["benefit_price"] = combined["benefit_price"].apply(Decimal) - discount
            combined["benefit_price"] = combined["benefit_price"].astype(int)
            
            spec_results = list(Complement_Product_Spec.objects.filter(
                mdl_code__in=combined['Model Code'].tolist(), site_cd = site_cd
            ).values("mdl_code","disp_nm2", "value"))
            
            if spec_results:
                spec_combined = pd.DataFrame(spec_results)
                if any(spec in spec_combined["disp_nm2"].unique()for spec in ["스토리지(저장 용량) (TB)", "스토리지(저장 용량) (GB)"]):
                    spec_combined = spec_combined[
                        spec_combined["disp_nm2"].isin(
                            ["스토리지(저장 용량) (TB)", "스토리지(저장 용량) (GB)"]
                        )
                    ]
                    spec_combined = spec_combined.dropna()
                    spec_combined = spec_combined.rename(columns={"mdl_code":"Model Code"})
                    spec_combined['value'] = spec_combined['value'].replace('1024 GB', '1 TB')
                    combined = pd.merge(combined, spec_combined, on='Model Code', how='left')
                    combined['disp_nm2'] = combined['disp_nm2'].fillna('-')
                    combined['value'] = combined['value'].fillna('-')
                    
                    combined = combined.rename(columns = {"value": "Storage"})
                    combined = (
                        combined[
                            [
                                "Model Code",
                                "Storage",
                                "color",
                                "standard_price",
                                "benefit_price",
                            ]
                        ]
                        .sort_values(by=["Storage", "color"])
                        .reset_index(drop=True)
                    )
                else:
                    combined = (
                        combined
                        .drop_duplicates()
                        .reset_index(drop=True)
                    )
                    combined = (
                        combined[["Model Code", "color", "standard_price", "benefit_price"]]
                        .sort_values(by=["color"])
                        .reset_index(drop=True)
                    )
            else:
                combined = (
                    combined
                    .drop_duplicates()
                    .reset_index(drop=True)
                )
                combined = (
                    combined[["Model Code", "color", "standard_price", "benefit_price"]]
                    .sort_values(by=["color"])
                    .reset_index(drop=True)
                )
        
        if not combined.empty:
            combined["Model Code"] = combined["Model Code"].astype(str)
            combined = combined.set_index("Model Code").loc[
                [code for code in product_codes if code in combined["Model Code"].values]
            ].reset_index() # db 검색 후 extended info에 잡힌 순서대로 정렬하기
                
    return combined

"""
Function to format price columns based on country code (added function)
"""
def format_price_columns(df, country_code) -> pd.DataFrame:
    if not df.empty:
        df[["standard_price", "benefit_price"]] = df[["standard_price", "benefit_price"]].apply(
            lambda x: (
                x.astype(str) + " 원"
                if country_code == "KR"
                else x.astype(str) + " GBP"
            )
        )
        # Replace invalid or missing price values with "-"
        df = df.replace(
            {
                "None GBP": "-",
                "None 원": "-",
                "nan GBP": "-",
                "nan 원": "-",
            }
        )
    return df

"""
The overall price check function retrieves and processes prices per model code, and ultimately provides the filtered extended code mapping along with the price table.
"""
def price_check(
    NER,
    extended_code_mapping,
    country_code,
    grouped_ner_list,
    product_operator_key, # Returns true if the target of the conditional price is a product, as in queries like 'phones more expensive than Galaxy S25'
    price_operator_dict, # A dictionary used to identify whether the target of a conditional price query is a product or model. 
    pre_owned_product_key, # Returns true if the query pertains to certified used phones (KR only).
    site_cd, 
    k=3, # By default, keep price results only up to 3
):  
    filtered_extended_code_mapping = []
    final_df = pd.DataFrame()
    no_model_flag = False
    no_model_range_flag = False
    code_id = pd.DataFrame()
    set_code_id = pd.DataFrame()
    telecom_dict = {}
    telecom_dict_tmp = {}
    final_price_dict = {}
    min_max_operator = [] # add
    grouped_extended_code_mappings = [] #add
    NER_output_operator = [] #add

    # Handle set products
    for data in extended_code_mapping:
        product_codes = data.get("extended_info", "")
        id_tmp = data.get("id", "")
        set_key = data.get("edge","")
        new_row = []
        set_new_row = []
        for product_code in product_codes:
            new_row.append({"id": id_tmp, "Model Code": product_code})
            if set_key == 'set':
                set_new_row.append({"id": id_tmp, "Model Code": product_code})

        new_df = pd.DataFrame(new_row)
        code_id = pd.concat([code_id, new_df], ignore_index=False)
        
        # Create separate set df as set products are excluded during final filtering
        set_new_df = pd.DataFrame(set_new_row)
        set_code_id = pd.concat([set_code_id, set_new_df], ignore_index=False) 

    if not code_id.empty:
        code_id_tmp = code_id.copy()
        # Handle certified used phones
        # If the query is for certified used phones, keep only the model codes starting with SM5 (certified used phones)
        if pre_owned_product_key:
            code_id = code_id[code_id["Model Code"].str.startswith('SM5')]
        # Exclude the target models if the query is not for certified used phones
        else:
            code_id = code_id[~code_id["Model Code"].str.startswith('SM5')]
            if code_id.empty:
                final_price_dict["price_status"] = "no pre-owned-models on sale"
                code_id = code_id_tmp
        
        # Handle the conditional price question which targets models
        # Remove model codes that are used as price comparison targets from the list of codes to be searched
        if product_operator_key:
            except_model_codes = []
            for key, value in price_operator_dict.items():
                if isinstance(value, dict):
                    for sub_key, sub_value in value.items():
                        if isinstance(sub_value, list):
                            except_model_codes.extend(sub_value)

            code_id = code_id[~code_id["Model Code"].isin(except_model_codes)]
        product_codes = code_id["Model Code"].tolist()

        # Search the price DB per country and site
        if country_code == "KR":
            # Family Net price inquiry - separate calculation required for employee prices
            if site_cd == "FN":
                final_df = kr_price_db_FNET(product_codes, site_cd)  
            # Default price inquiry - Samsung.com prices
            else:
                final_df = kr_price_db(product_codes, site_cd)
                # Handle carrier phone prices
                if not final_df.empty:
                    telecom_dict_tmp = telecom_price(final_df, site_cd)
                if telecom_dict_tmp:
                    telecom_dict = dict(list(telecom_dict_tmp.items())[:3]) # Keep only up to 3 carrier phone prices
                    final_df = final_df[
                    ~final_df["Model Code"].isin(list(telecom_dict_tmp.keys())) # Exclude model codes corresponding to carrier phones from the entire price table
                ]

        elif country_code == "GB":
            final_df = gb_price_db(product_codes, site_cd)

        else:
            raise ValueError(f"Unsupported country code: {country_code}")
 
    # If no products are found in the price DB, set no_model_flag to True
    if extended_code_mapping and final_df.empty:
        no_model_flag = True
    
    # add: product operator 독립 처리
    # If the conditional price question targets models, replace the values in NER_output_operator with the actual prices of the target models.
    if product_operator_key:
        NER_output_operator = [
            item
            for item in NER
            if item["field"] == "product_price" and item["operator"] != "in"
        ]
        if NER_output_operator and not final_df.empty:
            NER_output_operator = switch_price_standard(
                deepcopy(NER_output_operator),
                deepcopy(price_operator_dict),
                country_code,
                site_cd
            )

            final_df, no_model_range_flag = price_operator(
                NER_output_operator, final_df, country_code
            )
            
        if not final_df.empty:
            final_df = format_price_columns(final_df, country_code)
            final_df = final_df.drop_duplicates().reset_index(drop=True)
            
            # Attach model names to model codes and generate 'group' and 'id_2' columns to facilitate the final filtering process. 
            final_df = add_name_ordering(extended_code_mapping, final_df, code_id, country_code, site_cd, min_max_operator)
            
            if not final_df.empty:
                
                # Select the final price table to be provided, retain only the model codes corresponding to that price table, and filter and provide the extended code mapping accordingly 
                filtered_extended_code_mapping, final_df = final_filter(
                    extended_code_mapping, final_df, set_code_id, k, min_max_operator if min_max_operator else None, grouped_extended_code_mappings
                )

                if not final_df.empty:
                    final_price_dict["price"] = final_df

                if no_model_range_flag:
                    final_price_dict["price_status"] = "no models in the price range"
    
    else:
        # Group extended_code_mapping by id
        grouped_extended_code_mappings = []
        current_group = []
        
        for item in extended_code_mapping:
            if item.get('id') == 0:
                if current_group:
                    grouped_extended_code_mappings.append(current_group)
                current_group = [item]
            else:
                current_group.append(item)
        if current_group:
            grouped_extended_code_mappings.append(current_group)
            
        all_df = pd.DataFrame()
        all_df_list = []
        
        if grouped_ner_list and not final_df.empty:
            for ner_group in grouped_ner_list:
                # Extract all product_model expressions from the current ner_group
                ner_expressions = set(
                    ner_item["expression"].lower()
                    for ner_item in ner_group
                    if ner_item.get("field") == "product_model" and "expression" in ner_item
                )
                
                # Extract all product_model expressions from grouped_extended_code_mappings
                matched_group = None
                for group in grouped_extended_code_mappings: 
                    group_expressions = set(
                        group_item.get("expression", "").lower() for group_item in group if group_item.get("expression", "")
                    )

                    # Find the matching group in grouped_extended_code_mappings for a ner_group
                    if ner_expressions & group_expressions:
                        matched_group = group
                        break
                
                # If a matching group is found, use only that group's NER expressions
                if matched_group:
                    # Extract NER_output_operator from the current ner_group
                    # NER_output_operator is for conditional price queries where the operator is not 'in' but one of greater_than, less_than, min, max, or about
                    NER_output_operator = [
                        operator_item
                        for operator_item in ner_group
                        if operator_item.get("field") == "product_price" and operator_item.get("operator") != "in"
                    ]
                    min_max_operator.extend(
                        [op for op in NER_output_operator if op.get("operator") in ["max", "min"]]
                    )

                    # Filter final_df to include only the model codes in the matched group
                    group_model_codes = []
                    for item in matched_group:
                        group_model_codes.extend(item.get("extended_info", []))
                    group_final_df = final_df[final_df["Model Code"].isin(group_model_codes)]
                    
                    if NER_output_operator and not group_final_df.empty:
                        # Run price_operator for the matched group
                        group_df, no_model_range_flag = price_operator(
                            NER_output_operator, group_final_df, country_code
                        )
                        
                        # ADD model name and ordering
                        group_df = format_price_columns(group_df, country_code)
                        group_df = group_df.drop_duplicates().reset_index(drop=True)
                        
                        # Attach model names to model codes and generate 'group' and 'id_2' columns to facilitate the final filtering process. 
                        group_df = add_name_ordering(extended_code_mapping, group_df, code_id, country_code, site_cd, min_max_operator)
                        all_df_list.append(group_df)
                    else:
                        group_final_df = format_price_columns(group_final_df, country_code)
                        group_final_df = group_final_df.drop_duplicates().reset_index(drop=True)
                        
                        group_final_df = add_name_ordering(extended_code_mapping, group_final_df, code_id, country_code, site_cd, min_max_operator) 
                        all_df_list.append(group_final_df)
                else:
                    final_df = format_price_columns(final_df, country_code)
                    final_df = final_df.drop_duplicates().reset_index(drop=True)
                    
                    final_df = add_name_ordering(extended_code_mapping, final_df, code_id, country_code, site_cd, min_max_operator) 
                    all_df_list.append(final_df)
            
            if all_df_list and any(not df.empty for df in all_df_list):
                all_df = pd.concat([df for df in all_df_list if not df.empty], ignore_index=True)
            else:
                all_df = pd.DataFrame()
        
            final_df = all_df.copy(deep=True)
        
        if not final_df.empty:
            # Select the final price table to be provided, retain only the model codes corresponding to that price table, and filter and provide the extended code mapping accordingly 
            filtered_extended_code_mapping, final_df = final_filter(
                extended_code_mapping, final_df, set_code_id, k, min_max_operator if min_max_operator else None, grouped_extended_code_mappings
            )

            if not final_df.empty:
                final_price_dict["price"] = final_df

            if no_model_range_flag:
                final_price_dict["price_status"] = "no models in the price range"
                
    if final_df.empty and no_model_flag:
        final_price_dict["price_status"] = "no models on sale"

    if telecom_dict:
        final_price_dict["telecom_price"] = telecom_dict

    if product_operator_key and NER_output_operator is not None:
        final_price_dict["debug_price_standard"] = NER_output_operator

    return filtered_extended_code_mapping, [final_price_dict]


if __name__ == "__main__":
    grouped_ner_list = [                                                                                                                                      
                   [{'expression': '갤럭시 Z 플립6', 'field': 'product_model', 'operator': 'in'},                                                             
                   {'expression': '1 TB', 'field': 'product_spec', 'operator': 'in'}]                                                                                                                                            
               ]
    ner = [                                                                                                                                      
                   {'expression': '갤럭시 Z 플립6', 'field': 'product_model', 'operator': 'in'},                                                             
                   {'expression': '1 TB', 'field': 'product_spec', 'operator': 'in'}                                                                                                                                             
               ]
    extended_info_result = [                                                                                                             
                   {                                                                                                                                         
                       'mapping_code': '갤럭시 Z 플립6 통신사폰 (SKT/KT/LG U+)',                                                                             
                       'category_lv1': 'HHP',                                                                                                                
                       'category_lv2': 'NEW RADIO MOBILE (5G SMARTPHONE)',                                                                                   
                       'category_lv3': 'Galaxy Z Flip6',                                                                                                     
                       'edge': 'recommend',                                                                                                                  
                       'meta': '',                                                                                                                           
                       'extended_info': ['SM-F741NLBEKOD', 'SM-F741NLGEKOD', 'SM-F741NZSEKOD', 'SM-F741NZYEKOD'],                                            
                       'id': 0,                                                                                                                              
                       'expression': '갤럭시 Z 플립6'                                                                                                        
                   },                                                                                                                                        
                   {                                                                                                                                         
                       'mapping_code': '갤럭시 Z 플립6 자급제 (삼성닷컴/삼성 강남 전용컬러)',                                                                
                       'category_lv1': 'HHP',                                                                                                                
                       'category_lv2': 'NEW RADIO MOBILE (5G SMARTPHONE)',                                                                                   
                       'category_lv3': 'Galaxy Z Flip6',                                                                                                     
                       'edge': 'recommend',                                                                                                                  
                       'meta': '',                                                                                                                           
                       'extended_info': ['SM-F741NAKEKOO', 'SM-F741NZOEKOO', 'SM-F741NZWEKOO'],                                                              
                       'id': 1,                                                                                                                              
                       'expression': '갤럭시 Z 플립6'                                                                                                        
                   },                                                                                                                                        
                   {                                                                                                                                         
                       'mapping_code': '갤럭시 Z 플립6 자급제',                                                                                              
                       'category_lv1': 'HHP',                                                                                                                
                       'category_lv2': 'NEW RADIO MOBILE (5G SMARTPHONE)',                                                                                   
                       'category_lv3': 'Galaxy Z Flip6',                                                                                                     
                       'edge': 'recommend',                                                                                                                  
                       'meta': '',                                                                                                                           
                       'extended_info': ['SM-F741NLBEKOO', 'SM-F741NLGEKOO', 'SM-F741NZSEKOO', 'SM-F741NZYEKOO'],                                            
                       'id': 2,                                                                                                                              
                       'expression': '갤럭시 Z 플립6'                                                                                                        
                   }                                                                                                                                                                                                                                                                            
               ]
    import time
    start = time.time()
    result = price_check(
        ner,
        extended_info_result,
        "KR",
        grouped_ner_list,
        False,
        {},
        False,
        "B2C"  
    )
    print(time.time()-start)
    print(result)