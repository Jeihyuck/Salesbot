import sys

sys.path.append("/www/alpha/")
import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "alpha.settings")
django.setup()

import pandas as pd
import numpy as np
import asyncio
from decimal import Decimal
from datetime import datetime

from django.db import connection
from django.db.models import Q

from apps.rubicon_v3.__function import __embedding_rerank
from apps.rubicon_v3.__function._65_complement_price import (
    get_current_time_by_country_code,
)
from apps.rubicon_data.models import (
    product_category,
    uk_order_cards_info,
    card_istm_info,
    uk_product_trade_in,
    goods_base
)
from apps.rubicon_v3.__function.definitions import sub_intelligences
from apps.rubicon_v3.__external_api._03_price_check import PriceChecker
from apps.rubicon_v3.__external_api._08_kr_user_record import KR_UserRecord
from apps.rubicon_v3.__external_api._09_kr_goods_stock import KR_GoodsStock
from apps.rubicon_v3.__external_api._10_kr_membership_info import KR_MembershipInfo
from apps.rubicon_v3.__external_api._13_uk_membership_info import UK_MembershipInfo
import warnings

warnings.filterwarnings("ignore")

country_to_timezone = {"KR": "Asia/Seoul", "GB": "Europe/London"}

cardc_to_name = {
    "21": "해외 VISA",
    "22": "해외마스터",
    "24": "해외아멕스",
    "25": "해외다이너스",
    "41": "NH",
    "32": "광주",
    "33": "전북",
    "35": "산업카드",
    "48": "신협체크",
    "51": "수협",
    "52": "제주",
    "56": "KB증권",
    "71": "우체국체크",
    "34": "하나",
    "X029": "동남",
    "X82": "하나SK",
    "XC0": "올앳카드",
    "26": "중국은련",
    "54": "MG새마을금고체크",
    "95": "저축은행체크",
    "12": "삼성",
    "01": "하나(외환)",
    "1": "하나(외환)",
    "23": "해외 JCB",
    "17": "하나카드",
    "16": "NH",
    "55": "카카오뱅크",
    "11": "BC",
    "14": "신한",
    "44": "우리",
    "43": "씨티",
    "06": "국민",
    "6": "국민",
    "03": "롯데",
    "3": "롯데",
    "04": "현대",
    "4": "현대",
    "15": "KDP산업카드",
    "18": "조흥카드",
    "29": "삼성페이",
    "19": "애플페이",
    "20": "토스",
    "02": "케이뱅크",
    "13": "우리(비씨)",
    "08": "페이코",
    "09": "카카오페이",
    "28": "엘페이",
    "10": "SSG페이",
}

supported_payment_type = {
    "type": [
        "Normal",
        "Normal",
        "Normal",
        "Normal",
        "Normal",
        "Normal",
        "Installment",
        "Installment",
        "Installment",
    ],
    "payment_type": [
        "MasterCard",
        "Visa",
        "AmericanExpress",
        "SamsungPay",
        "PayPal",
        "Adyen",
        "Samsung Finance",
        "PaypalCredit",
        "Klarna",
    ],
}


def filter_model_to_dict(names, model_code, df_list):
    result_dict = {}
    for i, df in enumerate(df_list):
        df = df.drop_duplicates()
        if "Model Code" in df.columns:
            filtered_df = df[df["Model Code"] == model_code].drop(
                ["Model Code"], axis=1
            )
        else:
            filtered_df = df
        if not filtered_df.empty:
            result_dict[names[i]] = filtered_df.to_markdown(index=False)

    return result_dict


def promotion_check(
    NER,
    extended_code_mapping,
    price_df,
    sub_intelligence,
    country_code,
    guid,
    site_cd,
    channel
):
    coupon_result = pd.DataFrame()
    card_promotion_result = pd.DataFrame()
    payment_method = pd.DataFrame()
    div_pay_result = pd.DataFrame()
    bundle_result = pd.DataFrame()
    card_istm_result = pd.DataFrame()
    trade_result = pd.DataFrame()
    outlet_result = pd.DataFrame()
    point_result = pd.DataFrame()
    stock_result = pd.DataFrame()
    promotion_result = {}

    model_price = price_df[0].get("price", pd.DataFrame())
    if not model_price.empty:
        model_price["standard_price"] = (
            model_price["standard_price"]
            .replace("[^0-9]", "", regex=True)
            .apply(lambda x: Decimal(x) if x else None)
        )
        model_price["benefit_price"] = (
            model_price["benefit_price"]
            .replace("[^0-9]", "", regex=True)
            .apply(lambda x: Decimal(x) if x else None)
        )

    code_id = pd.DataFrame()
    now = datetime.strptime(
        get_current_time_by_country_code(country_code), "%Y-%m-%d %H:%M:%S"
    )
    for data in extended_code_mapping:
        product_codes = data.get("extended_info", "")
        id_tmp = data.get("id", "")
        new_row = []
        for product_code in product_codes:
            new_row.append({"id": id_tmp, "Model Code": product_code})

        new_df = pd.DataFrame(new_row)
        code_id = pd.concat([code_id, new_df], ignore_index=False)

    card_output_operator = [item for item in NER if item["field"] == "istm_prd"]
    split_output_operator = [item for item in NER if item["field"] == "split_pay"]
    
    if  country_code =="KR" and not code_id.empty and site_cd == "FN":
        if card_output_operator:
            card_istm_result = card_istm_promotion(product_codes, NER, now, site_cd)
        
        if sub_intelligence == sub_intelligences.PRODUCT_INVENTORY_AND_RESTOCKING:
                    stock_result = stock_info(code_id, site_cd, country_code)
            
    else:
        if country_code == "KR":
            if not code_id.empty:
                if sub_intelligence == sub_intelligences.PRODUCT_INVENTORY_AND_RESTOCKING:
                    stock_result = stock_info(code_id, site_cd, country_code)
                
                else:
                    coupon_result = coupon_promotion(code_id, model_price, now, guid, site_cd, channel)
                    card_promotion_result = card_promotion(
                        code_id,
                        model_price,
                        coupon_result,
                        NER,
                        country_code,
                        now,
                        site_cd,
                    )
                    if not coupon_result.empty:
                        coupon_result["coupon_total_discount_amount"] = (
                            "총 "
                            + (coupon_result["coupon_total_discount_amount"]).astype(str)
                            + " 원 할인"
                        )
                        coupon_result["coupon_total_applied_price"] = (
                            coupon_result["coupon_total_applied_price"]
                        ).astype(str) + " 원"
                    bundle_result = bundle_promotion(code_id, now, site_cd)
                    outlet_result = outlet_promotion(code_id, site_cd)
                    point_result = point_promotion(
                        code_id, model_price, guid, site_cd, country_code, channel
                    )

            if card_output_operator:
                card_istm_result = card_istm_promotion(product_codes, NER, now, site_cd)

            if split_output_operator:
                div_pay_result = div_pay_promotion(code_id, site_cd)

        if country_code == "GB":
            if not code_id.empty:
                if sub_intelligence == sub_intelligences.PRODUCT_INVENTORY_AND_RESTOCKING:
                    stock_result = stock_info(code_id, site_cd, country_code)
                
                else:
                    card_promotion_result = card_promotion(
                        code_id,
                        model_price,
                        coupon_result,
                        NER,
                        country_code,
                        now,
                        site_cd,
                    )
                    trade_result = trade_promotion(code_id, site_cd)
                    point_result = point_promotion(
                        code_id, model_price, guid, site_cd, country_code, channel
                    )

                    payment_method = pd.DataFrame(supported_payment_type)

    total_df = [
        coupon_result,
        card_promotion_result,
        div_pay_result,
        bundle_result,
        card_istm_result,
        payment_method,
        trade_result,
        outlet_result,
        point_result,
        stock_result,
    ]

    names = [
        "coupon",
        "card_promotion",
        "split_payment_availability",
        "bundle_promotion",
        "card_istm",
        "payment_method",
        "trade_in/up",
        "outlet_product",
        "point",
        "stock_status",
    ]

    if not code_id.empty:
        for code in code_id["Model Code"].tolist():
            promotion_result[code] = filter_model_to_dict(names, code, total_df)

    return [promotion_result]


def stock_info(code_id, site_cd, country_code):
    product_codes = code_id["Model Code"].tolist()
    if country_code == "KR":
        stockChecker = KR_GoodsStock("KR",site_cd)
        result_df = asyncio.run(stockChecker.getGoodsStock(product_codes))
        if not result_df.empty:
            result_df = result_df[["model_code", "saleStatCd"]]
            result_df.columns = ["Model Code", "Stock Status"]
            stock_df = pd.merge(code_id, result_df, on="Model Code")
            stock_df = stock_df[["Model Code", "Stock Status"]]
            stock_df["Stock Status"] = stock_df.apply(
                lambda row: (
                    ("Out of Stock") if row["Stock Status"] == "13" else ("In Stock")
                ),
                axis=1,
            )
    elif country_code == "GB":
        with connection.cursor() as cursor:
            stock_query = """
                    SELECT model_code, stock_level_status
                    FROM rubicon_data_uk_model_price
                    WHERE model_code IN %s
                    AND site_cd = %s
                    """
            product_codes_input = (
                product_codes if len(product_codes) > 1 else product_codes + ["a"]
            )
            cursor.execute(stock_query, [tuple(product_codes_input), site_cd])
            stock_results = cursor.fetchall()
            if stock_results:
                stock_df = pd.DataFrame(
                    stock_results, columns=[c.name for c in cursor.description]
                )

                stock_df.columns = ["Model Code", "Stock Status"]
                stock_df["Stock Status"] = stock_df.apply(
                    lambda row: (
                        ("Out of Stock")
                        if row["Stock Status"] == "outOfStock"
                        else ("In Stock")
                    ),
                    axis=1,
                )
                stock_df = stock_df.fillna('-')

    return stock_df


def point_promotion(code_id, model_price, guid, site_cd, country_code, channel):
    product_codes = code_id["Model Code"].tolist()
    mem_info = ""
    goods_id_df = pd.DataFrame()
    point_df = pd.DataFrame()
    gb_dict = {"blue": 10, "gold": 30, "platinum": 50}
    if country_code == "KR":
        goods_id_df = pd.DataFrame()
        point_df = pd.DataFrame()
        goods_id_results = list(
            product_category.objects.filter(
                mdl_code__in=product_codes,
                site_cd=site_cd,
                goods_stat_cd="30",
                show_yn="Y",
            ).values("mdl_code", "goods_id")
        )
        if goods_id_results:
            goods_id_df = pd.DataFrame(goods_id_results)
            goods_id_df = goods_id_df.rename(columns={"mdl_code": "Model Code"})
            goods_id_list = goods_id_df["goods_id"].tolist()

        infoObject = KR_UserRecord("KR", guid, channel)
        membershipInfo = KR_MembershipInfo("KR", guid, channel)
        point_df = asyncio.run(infoObject.getEstimatedPoints(goods_id_list))
        
        if guid:
            mem_result = asyncio.run(membershipInfo.getMembershipIdTier())
            mem_info = mem_result.get("mem_rank", "") if mem_result is not None else ""

        if not point_df.empty:
            point_df = point_df.rename(columns={"goodsId": "goods_id"})
            point_df["Point"] = point_df.apply(
                lambda row: (f"{row['webMembershipPoint']} P 적립예정"),
                axis=1,
            )

            if mem_info:
                point_df["membership_rank"] = [mem_info + "회원"] * len(point_df)
            else:
                point_df["membership_rank"] = [
                    "멤버십 등급에 따라 추가 혜택이 있음"
                ] * len(point_df)
            point_df = goods_id_df.merge(point_df, on="goods_id")
            point_df = point_df[["Model Code", "membership_rank", "Point"]]

    elif country_code == "GB" and guid:
        membershipInfo = UK_MembershipInfo("GB", guid, channel)
        mem_info = asyncio.run(membershipInfo.getMembershipTier())
        if mem_info:
            point_df = model_price
            point_df["membership_rank"] = [mem_info] * len(point_df)
            point_df["multiply"] = (
                point_df["membership_rank"].str.lower().map(gb_dict).fillna(0)
            )
            point_df = point_df[point_df["multiply"] != 0]
            if not point_df.empty:
                point_df["tmp_price"] = point_df[
                    ["standard_price", "benefit_price"]
                ].min(axis=1)
                point_df["Point"] = point_df.apply(
                    lambda row: str(int(int(row["tmp_price"]) * row["multiply"]))
                    + " p ",
                    axis=1,
                )
                point_df = point_df[["Model Code", "membership_rank", "Point"]]

    return point_df


def trade_promotion(code_id, site_cd):
    product_codes = code_id["Model Code"].tolist()
    trade_df = pd.DataFrame()

    trade_results = list(
        uk_product_trade_in.objects.filter(
            buying_model_code__in=product_codes, site_cd=site_cd
        ).values("buying_model_code", "overall_total")
    )
    if trade_results:
        trade_df = pd.DataFrame(trade_results)
        if not trade_df.empty:
            trade_df = trade_df[trade_df["overall_total"] != 0]
            if not trade_df.empty:
                trade_df = (
                    trade_df.groupby("buying_model_code")["overall_total"]
                    .agg(discount_min="min", discount_max="max")
                    .reset_index()
                )
                trade_df = trade_df.rename(columns={"buying_model_code": "Model Code"})
                trade_df["discount_min"] = (trade_df["discount_min"]).astype(
                    str
                ) + " GBP"
                trade_df["discount_max"] = (trade_df["discount_max"]).astype(
                    str
                ) + " GBP"
                trade_df = trade_df[["Model Code", "discount_min", "discount_max"]]

    return trade_df


def div_pay_promotion(code_id, site_cd):
    product_codes = code_id["Model Code"].tolist()
    div_results = []
    div_df = pd.DataFrame()

    div_results = list(
        product_category.objects.filter(
            mdl_code__in=product_codes, site_cd=site_cd
        ).values("mdl_code", "div_pay_apl_yn")
    )

    if div_results:
        div_df = pd.DataFrame(div_results)
        div_df["split payment availability"] = div_df.apply(
            lambda row: (
                ("나눠서 결제 가능")
                if row["div_pay_apl_yn"] == "Y"
                else ("나눠서 결제 불가능")
            ),
            axis=1,
        )
        div_df = div_df.rename(columns={"mdl_code": "Model Code"}).drop(
            ["div_pay_apl_yn"], axis=1
        )

    return div_df


def outlet_promotion(code_id, site_cd):
    product_codes = code_id["Model Code"].tolist()
    outlet_df = pd.DataFrame(
        {
            "Model Code": product_codes,
            "outlet product": ["no"] * len(product_codes),
        }
    )
    with connection.cursor() as cursor:
        outlet_query = """
                SELECT mdl_code 
                FROM rubicon_data_product_category pc
                INNER JOIN rubicon_data_goods_add_column_info ci
                ON pc.goods_id = ci.goods_id
                AND ci.goods_col_gb_cd = '05'
                AND ci.col_val1='Y'
                AND mdl_code IN %s
                AND pc.site_cd = %s
                """
        product_codes_input = (
            product_codes if len(product_codes) > 1 else product_codes + ["a"]
        )
        cursor.execute(outlet_query, [tuple(product_codes_input), site_cd])
        outlet_results = cursor.fetchall()
        if outlet_results:
            outlet_model_code = pd.DataFrame(
                outlet_results, columns=[c.name for c in cursor.description]
            )["mdl_code"].tolist()
            outlet_df = code_id
            outlet_df["outlet product"] = outlet_df.apply(
                lambda row: "yes" if row["Model Code"] in outlet_model_code else "no",
                axis=1,
            )
            outlet_df = outlet_df[["Model Code", "outlet product"]]

    return outlet_df


def bundle_promotion(code_id, now, site_cd):
    product_codes = code_id["Model Code"].tolist()
    bundle_df = pd.DataFrame(
        {
            "Model Code": product_codes,
            "apply_check": ["번들 프로모션 없음"] * len(product_codes),
        }
    )

    with connection.cursor() as cursor:
        bundle_query = """
        select a.prmt_no, a.main_mdl_code, a.apl_goods_id, a.apl_mdl_code, a.apl_goods_nm, a.prmt_apl_cd, a.apl_sale_prc1, a.apl_sale_prc3, a.apl_val
        from rubicon_data_promotion_bundle_map a
        inner join rubicon_data_product_category b
        on a.apl_mdl_code = b.mdl_code
        and a.site_cd = %s
        and main_mdl_code in %s
        and cstrt_yn = 'Y'
        and prmt_apl_cd = '20'
        """
        product_codes_input = (
            product_codes if len(product_codes) > 1 else product_codes + ["a"]
        )
        cursor.execute(bundle_query, [site_cd, tuple(product_codes_input)])
        bundle_results = cursor.fetchall()

        if bundle_results:
            bundle_df = pd.DataFrame(
                bundle_results, columns=[c.name for c in cursor.description]
            )
            stockChecker = KR_GoodsStock("KR",site_cd)
            result_df = asyncio.run(stockChecker.getGoodsStock(bundle_df['apl_mdl_code'].tolist()))
            if not result_df.empty:
                valid_mdl_codes = result_df[result_df['saleStatCd']=='12']['model_code'].tolist()
                bundle_df = bundle_df[bundle_df['apl_mdl_code'].isin(valid_mdl_codes)].reset_index(drop=True)
            
            if not bundle_df.empty:
                bundle_df["tmp_price"] = bundle_df[["apl_sale_prc1", "apl_sale_prc3"]].min(
                    axis=1
                )

                bundle_df["promotion_price"] = bundle_df.apply(
                    lambda row: (
                        row["tmp_price"] * (1 - Decimal(row["apl_val"]) / 100)
                        if row["prmt_apl_cd"] == 10
                        else row["tmp_price"] - Decimal(row["apl_val"])
                    ),
                    axis=1,
                )
                bundle_df["promotion_price"] = bundle_df["promotion_price"].apply(
                    lambda x: str(int(x)) + " 원"
                )

                bundle_df = bundle_df.rename(
                    columns={
                        "main_mdl_code": "Model Code",
                        "apl_goods_id": "goods_id",
                        "apl_mdl_code": "Bundle Model Code",
                        "apl_goods_nm": "Bundle Model Name",
                    }
                )
                bundle_df = bundle_df[
                    [
                        "Model Code",
                        "Bundle Model Code",
                        "Bundle Model Name",
                        "promotion_price",
                        "goods_id",
                    ]
                ]
                bundle_df = (
                    bundle_df.sort_values("goods_id", ascending=False)
                    .groupby("Model Code")
                    .head(3)
                    .drop(["goods_id"], axis=1)
                )

                grouped_merged_df = (
                    bundle_df.groupby(
                        ["Model Code", "Bundle Model Name", "promotion_price"],
                        sort=False,
                    )
                    .agg(
                        lambda x: (
                            ", ".join(map(str, set(x)))
                            if x.name != "Model Code"
                            and x.name != "Bundle Model Name"
                            and x.name != "promotion_price"
                            else x.iloc[0]
                        )
                    )
                    .reset_index()
                )

                original_columns = bundle_df.columns.tolist()
                bundle_df = grouped_merged_df[original_columns]

                absent_models = set(product_codes) - set(bundle_df["Model Code"])
                new_rows = []
                for model in absent_models:
                    new_rows.append(
                        {"Model Code": model, "apply_check": "번들 프로모션 없음"}
                    )
                new_df = pd.DataFrame(new_rows)
                bundle_df = pd.concat([bundle_df, new_df], ignore_index=True)
                bundle_df = bundle_df.fillna("-")
                
            else:
                bundle_df = pd.DataFrame(
                    {
                        "Model Code": product_codes,
                        "apply_check": ["번들 프로모션 없음"] * len(product_codes),
                    }
                )

    return bundle_df


def card_istm_promotion(product_codes, NER, now, site_cd):
    istm_results = []
    istm_df = pd.DataFrame()
    with connection.cursor() as cursor:
        card_istm_query = """
            SELECT bb.mdl_code,
            ci.cardc_cd,
            ci.no_itrst_std_amt,
            ci.no_itrst_prd,
            ci.long_no_itrst_std_amt,
            ci.long_no_itrst_prd
            FROM (
                SELECT gb.* ,case when (dgb.comp_no = '313' or dgb.comp_no = '354' or dgb.comp_no = '415' or dgb.comp_no = '422' or dgb.comp_no = '427') then replace(mid_new, '1_','_')
                            else mid_new end as mid_new_1
                FROM (
                        SELECT mdl_code ,goods_nm,goods_id,
                            CASE when %s between mid1_strt_dtm and mid1_end_dtm then mid1
                                    when %s between mid2_strt_dtm and mid2_end_dtm then mid2
                            ELSE 'samsung0'   END AS mid_new
                        FROM public.rubicon_data_product_category
                        WHERE goods_stat_cd = '30'
                            AND site_cd = %s) gb
                INNER JOIN public.rubicon_data_goods_base dgb
                    ON gb.goods_id = dgb.goods_id
                AND dgb.site_cd = %s ) bb
            INNER JOIN  public.rubicon_data_card_istm_info ci
                ON  bb.mid_new_1= ci.sid
                AND ci.no_itrst_strt_dt::timestamp <= %s
                AND ci.no_itrst_end_dt::timestamp >= %s
                AND ci.site_cd = %s
                WHERE bb.mdl_code IN %s;
        """
                        
        product_codes_input = (
                product_codes if len(product_codes) > 1 else product_codes + ["a"]
            )
        cursor.execute(card_istm_query, [now, now, site_cd, site_cd, now, now, site_cd, tuple(product_codes_input)])
        istm_results = cursor.fetchall()
        
        if istm_results:
            istm_df = pd.DataFrame(
                istm_results, columns=[c.name for c in cursor.description]
            )
            istm_df =  istm_df[
                [
                    "cardc_cd",
                    "no_itrst_std_amt",
                    "no_itrst_prd",
                    "long_no_itrst_std_amt",
                    "long_no_itrst_prd",
                ]
            ]
            
            istm_df = istm_df.dropna(subset=["no_itrst_prd"])

            card_results = card_code_mapping(NER)
            if card_results:
                if not any(istm_df["cardc_cd"].isin(list(card_results.values())[0])):
                    istm_df = pd.DataFrame(
                        {
                            "card_name": [list(card_results.keys())[0]],
                            "apply_check": ["적용 안됨"],
                        }
                    )
                    return istm_df
                istm_df = istm_df[istm_df["cardc_cd"].isin(list(card_results.values())[0])]

            istm_df["cardc_cd"] = istm_df["cardc_cd"].apply(
                lambda card: (
                    cardc_to_name.get(card, "기타") + " 카드"
                    if len(cardc_to_name.get(card, "기타")) <= 2
                    else cardc_to_name.get(card, "기타")
                )
            )
            istm_df["first"] = istm_df["no_itrst_prd"].str.split("^").str[0].str.strip()
            istm_df["last"] = istm_df["no_itrst_prd"].str.split("^").str[-1].str.strip()
            istm_df["no_itrst_prd"] = istm_df["first"] + "~" + istm_df["last"]

            istm_df = istm_df.drop(["first", "last"], axis=1)

            istm_df["no_itrst_std_amt"] = np.where(
                istm_df["no_itrst_std_amt"] + 1 < 100000000,
                "최소 "
                + ((istm_df["no_itrst_std_amt"] + 1) // 10000).astype(str)
                + "만원 대상",
                "최소 "
                + ((istm_df["no_itrst_std_amt"] + 1) // 100000000).astype(str)
                + "억 대상",
            )
            istm_df["long_no_itrst_std_amt"] = np.where(
                istm_df["long_no_itrst_std_amt"] + 1 < 100000000,
                "최소 "
                + ((istm_df["long_no_itrst_std_amt"] + 1) // 10000).astype(str)
                + "만원 대상",
                "최소 "
                + ((istm_df["long_no_itrst_std_amt"] + 1) // 100000000).astype(str)
                + "억 대상",
            )
            istm_df["no_itrst_prd"] = (istm_df["no_itrst_prd"]).astype(
                str
            ) + " 개월 무이자 할부"
            istm_df["long_no_itrst_prd"] = (istm_df["long_no_itrst_prd"]).astype(
                str
            ) + " 개월 무이자 할부"
            istm_df = istm_df.rename(
                columns={
                    "cardc_cd": "card_name",
                    "no_itrst_std_amt": "min_short_term_interest_free_amount",
                    "no_itrst_prd": "short_term_interest_free",
                    "long_no_itrst_std_amt": "min_long_term_interest_free_amount",
                    "long_no_itrst_prd": "long_term_interest_free",
                }
            )

            istm_df = istm_df.dropna(subset=["short_term_interest_free"])
            istm_df = istm_df.replace(
                {
                    "None 개월 무이자 할부": "-",
                    "None 원": "-",
                    "최소 nan억 대상": "-",
                }
            )

    return istm_df


def coupon_promotion(code_id, model_price, now, guid, site_cd, channel):
    product_codes = code_id["Model Code"].tolist()
    merged_df = pd.DataFrame()
    if guid:
        goods_id_df = pd.DataFrame()
        coupon_df = pd.DataFrame()
        goods_id_results = list(
            product_category.objects.filter(
                mdl_code__in=product_codes, site_cd=site_cd
            ).values("mdl_code", "goods_id")
        )
        if goods_id_results:
            goods_id_df = pd.DataFrame(goods_id_results)
            goods_id_df = goods_id_df.rename(columns={"mdl_code": "Model Code"})
            goods_id_list = goods_id_df["goods_id"].tolist()

        priceChecker = PriceChecker("KR", channel)
        coupon_df = asyncio.run(priceChecker.callPriceApi(guid, goods_id_list))
        if not coupon_df.empty:
            coupon_df = coupon_df.rename(
                columns={
                    "mdlCode": "Model Code",
                    "totalPrice": "coupon_total_applied_price",
                }
            )
            coupon_df = coupon_df[["Model Code", "coupon_total_applied_price"]]
            merged_df = pd.merge(coupon_df, model_price, on="Model Code")
            merged_df["tmp_price"] = merged_df[["standard_price", "benefit_price"]].min(
                axis=1
            )
            merged_df["coupon_discount_amount"] = merged_df.apply(
                lambda row: (int(row["tmp_price"] - row["coupon_total_applied_price"])),
                axis=1,
            )
            merged_df["coupon_total_discount_amount"] = merged_df.groupby("Model Code")[
                "coupon_discount_amount"
            ].transform("sum")

            merged_df["coupon_total_discount_amount"] = merged_df.apply(
                lambda row: (round(row["coupon_total_discount_amount"] / 100) * 100),
                axis=1,
            )

            merged_df = (
                merged_df.groupby(
                    ["Model Code", "tmp_price", "coupon_total_discount_amount"],
                    sort=False,
                )
                .agg(
                    lambda x: (
                        ", ".join(map(str, set(x)))
                        if x.name != "Model Code"
                        and x.name != "coupon_total_discount_amount"
                        and x.name != "tmp_price"
                        else x.iloc[0]
                    )
                )
                .reset_index()
            )

            merged_df["coupon_discount_amount"] = merged_df.apply(
                lambda row: (str(row["coupon_discount_amount"]) + " 원 할인"), axis=1
            )

            merged_df["coupon_name"] = ["-"] * len(merged_df)
            merged_df = merged_df[
                [
                    "Model Code",
                    "coupon_name",
                    "coupon_discount_amount",
                    "coupon_total_discount_amount",
                    "coupon_total_applied_price",
                ]
            ]
            last_columns = merged_df.columns[-2:]
            valid_rows = []
            for column in last_columns:
                for index, value in merged_df[column].items():
                    try:
                        merged_df.at[index, column] = Decimal(value)
                        valid_rows.append(index)
                    except Exception as e:
                        continue
            merged_df = merged_df[merged_df.index.isin(valid_rows)]

    else:
        with connection.cursor() as cursor:
            coupon_query = """
            SELECT pc.mdl_code, aa.cp_nm, aa.cp_apl_cd, aa.apl_val, aa.duple_use_yn, aa.multi_apl_yn from (
                SELECT cb.cp_no, cb.cp_nm, cb.cp_apl_cd, cb.vld_prd_end_dtm, cb.vld_prd_day, cb.cp_pvd_mth_cd, cb.apl_end_dtm, cb.isu_host_cd, cb.duple_use_yn, cb.multi_apl_yn,
                    CASE WHEN ct.disp_clsf_no is null THEN ct.goods_id
                        ELSE dg.goods_id end AS apl_goods_id, cb.apl_val FROM rubicon_data_coupon_base cb
                    JOIN rubicon_data_coupon_target ct ON cb.cp_no = ct.cp_no	
                        AND %s BETWEEN cb.apl_strt_dtm AND cb.apl_end_dtm
                        AND %s BETWEEN cb.vld_prd_strt_dtm and cb.vld_prd_end_dtm
                        AND cb.site_cd = %s
                        AND cb.cp_stat_cd = '20'
                        AND cb.cp_pvd_mth_cd = '10'
                        and cb.cp_show_yn = 'Y'
                        and cb.max_dc_amt = 0
                    LEFT JOIN (select * from rubicon_data_display_goods where site_cd = %s) dg on ct.disp_clsf_no = dg.disp_clsf_no) aa
                    JOIN rubicon_data_product_category pc on aa.apl_goods_id = pc.goods_id
                        AND pc.goods_stat_cd = '30' 
                        AND pc.mdl_code IN %s
                        AND pc.site_cd = %s; 
            """
            product_codes_input = (
                product_codes if len(product_codes) > 1 else product_codes + ["a"]
            )
            cursor.execute(
                coupon_query,
                [now, now, site_cd, site_cd, tuple(product_codes_input), site_cd],
            )
            coupon_result = cursor.fetchall()

            if coupon_result:
                coupon_df = pd.DataFrame(
                    coupon_result, columns=[c.name for c in cursor.description]
                )
                coupon_df = coupon_df.rename(
                    columns={"mdl_code": "Model Code", "cp_nm": "coupon_name"}
                )
                merged_df = pd.merge(coupon_df, model_price, on="Model Code")
                merged_df["tmp_price"] = merged_df[
                    ["standard_price", "benefit_price"]
                ].min(axis=1)
                merged_df["coupon_discount_amount"] = merged_df.apply(
                    lambda row: (
                        (str(row["apl_val"]) + " 원 할인")
                        if row["cp_apl_cd"] == "20"
                        else (str(row["apl_val"]) + " % 할인")
                    ),
                    axis=1,
                )

                merged_df["coupon_discount_price"] = merged_df.apply(
                    lambda row: (
                        int(row["tmp_price"] * Decimal(row["apl_val"] / 100))
                        if row["cp_apl_cd"] == "10"
                        else int(Decimal(row["apl_val"]))
                    ),
                    axis=1,
                )

                merged_df = merged_df[
                    [
                        "Model Code",
                        "tmp_price",
                        "coupon_name",
                        "coupon_discount_amount",
                        "coupon_discount_price",
                    ]
                ]

                merged_df = merged_df.drop_duplicates()
                merged_df["coupon_total_discount_amount"] = merged_df.groupby(
                    "Model Code"
                )["coupon_discount_price"].transform("sum")
                merged_df["coupon_total_discount_amount"] = merged_df.apply(
                    lambda row: (
                        round(row["coupon_total_discount_amount"] / 100) * 100
                    ),
                    axis=1,
                )
                merged_df = (
                    merged_df.groupby(
                        ["Model Code", "tmp_price", "coupon_total_discount_amount"],
                        sort=False,
                    )
                    .agg(
                        lambda x: (
                            ", ".join(map(str, set(x)))
                            if x.name != "Model Code"
                            and x.name != "coupon_total_discount_amount"
                            and x.name != "tmp_price"
                            else x.iloc[0]
                        )
                    )
                    .reset_index()
                )

                merged_df["coupon_total_applied_price"] = merged_df.apply(
                    lambda row: (
                        int(row["tmp_price"] - row["coupon_total_discount_amount"])
                    ),
                    axis=1,
                )

                merged_df = merged_df[
                    [
                        "Model Code",
                        "coupon_name",
                        "coupon_discount_amount",
                        "coupon_total_discount_amount",
                        "coupon_total_applied_price",
                    ]
                ]

    return merged_df


def card_code_mapping(NER):
    results = {}
    filtered_NER = [
        {"field": result["field"], "expression": result["expression"]}
        for result in NER
        if result["field"] == "cardc_cd"
    ]

    for component in filtered_NER:
        expression = component.get("expression")
        embedded_expression_value = __embedding_rerank.baai_embedding(
            expression, "tmp"
        )[0]

        df = card_retriever(expression, embedded_expression_value)
        results = {}

        if not df.empty:
            results[expression] = df["mapping_code"].dropna().drop_duplicates().tolist()

    return results


def card_retriever(expression, embedding):
    df_reranked = pd.DataFrame()
    final_df = pd.DataFrame()
    with connection.cursor() as cursor:
        exact_sql = """
        SELECT mapping_code, expression 
        FROM rubicon_v3_structured_code_mapping
        WHERE field = 'cardc_cd'
        AND expression = %s
        AND country_code = 'KR'
        AND active = TRUE
        AND structured = TRUE;
        """

        similarity_sql = """
        SELECT mapping_code, expression, 1-(expression_embedding <=> %s::vector) AS similarity_score
        FROM rubicon_v3_structured_code_mapping
        WHERE field = 'cardc_cd'
        AND country_code = 'KR'
        AND active = TRUE
        AND structured = TRUE
        AND 1-(expression_embedding <=> %s::vector) >= 0.7
        ORDER BY similarity_score DESC
        LIMIT 10;
        """
        cursor.execute(exact_sql, [expression])
        results = cursor.fetchall()
        if results:
            final_df = pd.DataFrame(
                results, columns=[c.name for c in cursor.description]
            )

        else:
            cursor.execute(similarity_sql, [embedding, embedding])
            results = cursor.fetchall()
            final_df = pd.DataFrame(
                results, columns=[c.name for c in cursor.description]
            )

        if not final_df.empty:
            df_reranked = __embedding_rerank.rerank_db_results(
                expression, final_df, text_column="expression", top_k=1
            )

            if not df_reranked.empty:
                top_expression = df_reranked["expression"].iloc[0]
                final_df = final_df[final_df["expression"] == top_expression]

    return final_df


def card_promotion_KR(product_codes, model_price, coupon_result, NER, now, site_cd):
    merged_df = pd.DataFrame()
    goods_mid = pd.DataFrame()
    with connection.cursor() as cursor:
        goods_mid_query = """
        SELECT * FROM (
            SELECT gb.mdl_code, gb.mid_new, bb.mid, bb.pg_bnft_no, bb.pg_bnft_nm, bb.cardc_cd, bb.disp_strt_dtm, bb.disp_end_dtm,
            case when gb.mid_new = 'default' and %s between bb.disp_strt_dtm and bb.disp_end_dtm then 'active'
            else gb.mid_new end as mid_new_1
            FROM (
                    SELECT mdl_code ,goods_nm,
                    CASE when %s between mid1_strt_dtm and mid1_end_dtm then mid1
                        when %s between mid2_strt_dtm and mid2_end_dtm then mid2
                    ELSE 'default'
                    END AS mid_new
                    FROM public.rubicon_data_product_category
                    WHERE goods_stat_cd = '30'
                    AND site_cd = %s) gb
                    INNER JOIN (
                    SELECT pg_bnft_no, COALESCE(mid,'default') as mid, pg_bnft_nm, cardc_cd, disp_strt_dtm, disp_end_dtm
                    FROM public.rubicon_data_pg_benefit_base
                    where bnft_stat_cd = '20'
                    ) bb
                    ON gb.mid_new = bb.mid) cc
            INNER JOIN public.rubicon_data_pg_benefit_detail pm
            ON cc.pg_bnft_no = pm.pg_bnft_no
            where cc.mid_new_1 != 'default'
            and cc.mdl_code IN %s;
        """
        product_codes_input = (
            product_codes if len(product_codes) > 1 else product_codes + ["a"]
        )
        cursor.execute(goods_mid_query, [now, now, now, site_cd, tuple(product_codes_input)])
        goods_mid_results = cursor.fetchall()

        if goods_mid_results:
            goods_mid = pd.DataFrame(
                goods_mid_results, columns=[c.name for c in cursor.description]
            )
            goods_mid = goods_mid[
                [
                    "mdl_code",
                    "pg_bnft_nm",
                    "cardc_cd",
                    "min_bnft_amt",
                    "max_bnft_amt",
                    "dc_amt",
                    "max_dc_amt",
                ]
            ]

        if not goods_mid.empty:
            card_results = card_code_mapping(NER)

            if card_results:
                if not any(goods_mid["cardc_cd"].isin(list(card_results.values())[0])):
                    merged_df = pd.DataFrame(
                        {
                            "Model Code": product_codes,
                            "card_name": [list(card_results.keys())[0]]
                            * len(product_codes),
                            "apply_check": ["적용 안됨"] * len(product_codes),
                        }
                    )
                    return merged_df

                if any(
                    items["operator"] == "not_in"
                    for items in NER
                    if items["field"] == "cardc_cd"
                ):
                    goods_mid = goods_mid[
                        ~goods_mid["cardc_cd"].isin(list(card_results.values())[0])
                    ]

                else:
                    goods_mid = goods_mid[
                        goods_mid["cardc_cd"].isin(list(card_results.values())[0])
                    ]

            cards = goods_mid["cardc_cd"].unique().tolist()
            card_df = pd.DataFrame()
            for card in cards:
                tmp = goods_mid[goods_mid["cardc_cd"] == card]
                tmp["tmp_min"] = np.where(
                    tmp["min_bnft_amt"] < 100000000,
                    (tmp["min_bnft_amt"] // 10000).astype(str) + "만원",
                    (tmp["min_bnft_amt"] // 100000000).astype(str) + "억",
                )

                tmp["tmp_max"] = np.where(
                    tmp["max_bnft_amt"] + 1 < 100000000,
                    ((tmp["max_bnft_amt"] + 1) // 10000).astype(str) + "만원 대상",
                    ((tmp["max_bnft_amt"] + 1) // 100000000).astype(str) + "억 대상",
                )

                tmp["price_range"] = tmp["tmp_min"].astype(str) + " ~ " + tmp["tmp_max"]

                tmp["discount_info"] = np.where(
                    tmp["dc_amt"] <= 100,
                    tmp["dc_amt"].astype(str) + "% 할인",
                    (tmp["dc_amt"] // 10000).astype(str) + "만원 할인",
                )
                tmp["max_discount"] = np.where(
                    tmp["max_dc_amt"] == 0,
                    "",
                    "최대 " + (tmp["max_dc_amt"] // 10000).astype(str) + "만원 할인",
                )
                tmp["card_name"] = (
                    cardc_to_name.get(card, "기타") + "카드"
                    if len(cardc_to_name.get(card, "기타")) <= 2
                    else cardc_to_name.get(card, "기타")
                )
                card_df = pd.concat([card_df, tmp], axis=0)

            card_df = card_df.replace({"0 ~ 0만원 대상": "제한 없음"})
            card_df = card_df.rename(
                columns={
                    "mdl_code": "Model Code",
                    "pg_bnft_nm": "payment benefit category",
                }
            )
            card_df = card_df.drop_duplicates().reset_index(drop=True)

            if not card_df.empty and not model_price.empty:
                merged_df = pd.merge(card_df, model_price, on="Model Code")
                merged_df["tmp_price"] = merged_df[
                    ["standard_price", "benefit_price"]
                ].min(axis=1)
                if not coupon_result.empty:
                    merged_df_2 = pd.merge(merged_df, coupon_result, on="Model Code")
                    if not merged_df_2.empty:
                        merged_df = merged_df_2
                        merged_df["tmp_price"] = merged_df[
                            [
                                "standard_price",
                                "benefit_price",
                                "coupon_total_applied_price",
                            ]
                        ].min(axis=1)

                merged_df["card_discount_price"] = merged_df.apply(
                    lambda row: (
                        round(row["tmp_price"] * Decimal(row["dc_amt"]) / 100)
                        if Decimal(row["dc_amt"]) < 100
                        else row["dc_amt"]
                    ),
                    axis=1,
                )
                merged_df["card_discount_applied_price"] = merged_df.apply(
                    lambda row: (
                        row["tmp_price"] - row["card_discount_price"]
                        if row["tmp_price"] >= row["min_bnft_amt"]
                        and row["card_discount_price"] <= row["max_dc_amt"]
                        else row["tmp_price"]
                    ),
                    axis=1,
                )

                merged_df = merged_df[
                    merged_df["tmp_price"] != merged_df["card_discount_applied_price"]
                ]

                if not merged_df.empty:
                    merged_df = merged_df[
                        [
                            "Model Code",
                            "payment benefit category",
                            "card_name",
                            "discount_info",
                            "card_discount_price",
                            "card_discount_applied_price",
                        ]
                    ]
                    merged_df["card_discount_price"] = merged_df[
                        ["card_discount_price"]
                    ].apply(lambda x: x.astype(str) + " 원 할인")
                    merged_df["card_discount_applied_price"] = merged_df[
                        ["card_discount_applied_price"]
                    ].apply(lambda x: x.astype(str) + " 원")

                    grouped_merged_df = (
                        merged_df.groupby(
                            [
                                "Model Code",
                                "payment benefit category",
                                "discount_info",
                                "card_discount_price",
                                "card_discount_applied_price",
                            ],
                            sort=False,
                        )
                        .agg(
                            lambda x: (
                                ", ".join(map(str, set(x)))
                                if x.name != "Model Code"
                                and x.name != "discount_info"
                                and x.name != "card_discount_price"
                                and x.name != "card_discount_applied_price"
                                else x.iloc[0]
                            )
                        )
                        .reset_index()
                    )

                    original_columns = merged_df.columns.tolist()
                    merged_df = grouped_merged_df[original_columns]

    return merged_df


def card_promotion_GB(product_codes, site_cd):
    goods_mid_results = []
    card_df = pd.DataFrame()

    goods_mid_results = list(
        uk_order_cards_info.objects.filter(
            model_code__in=product_codes, site_cd=site_cd
        ).values(
            "model_code",
            "code_name",
            "code2",
            "downpayment",
            "interestrate",
            "periodvalue",
        )
    )

    if goods_mid_results:
        card_df = pd.DataFrame(goods_mid_results)
        card_df["code2"] = (card_df["code2"]).astype(str) + " Months"
        card_df["downpayment"] = (card_df["downpayment"]).astype(str) + " GBP"
        card_df["interestrate"] = (card_df["interestrate"]).astype(str) + " %"
        card_df["periodvalue"] = (card_df["periodvalue"]).astype(str) + " GBP/Month"
        card_df = card_df.replace({"nan GBP": "-"})
        card_df = card_df.rename(
            columns={
                "model_code": "Model Code",
                "code_name": "payment options",
                "code2": "loan duration",
                "downpayment": "minimum deposit",
                "interestrate": "interest rate",
                "periodvalue": "monthly payment amount",
            }
        )

    return card_df


def card_promotion(
    code_id, model_price, coupon_result, NER, country_code, now, site_cd
):
    final_df = pd.DataFrame()
    product_codes = code_id["Model Code"].tolist()

    if product_codes:
        if country_code == "KR":
            final_df = card_promotion_KR(
                product_codes,
                model_price,
                coupon_result,
                NER,
                now,
                site_cd,
            )

        if country_code == "GB":
            final_df = card_promotion_GB(product_codes, site_cd)

    return final_df


if __name__ == "__main__":
    from apps.rubicon_v3.__function._65_complement_price import price_check
    import time

    start = time.time()
    country_code = "KR"
    NER = [
        {"expression": "갤럭시 Z플립7", "field": "product_model", "operator": "in"}
    ]
    extended_info_result = [
        {
            "mapping_code": "갤럭시 Z 플립7",
            "category_lv1": "HHP",
            "category_lv2": "NEW RADIO MOBILE (5G SMARTPHONE)",
            "category_lv3": "Galaxy Z Flip7",
            "edge": "recommend",
            "meta": "",
            "extended_info": ["SM-F766NZRAKOO", "SM-F766NZKEKOO"],
            "id": 0,
        }
    ]
    _, price_df = price_check(NER, extended_info_result, country_code, [],True, {}, False, 'FN')
    promotion = promotion_check(
        NER, extended_info_result, price_df, "",country_code, "9n0umijbja","FN",""
    )
    print(time.time() - start)
    print(promotion)
