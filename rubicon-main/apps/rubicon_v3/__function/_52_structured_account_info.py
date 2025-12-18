import sys

sys.path.append("/www/alpha/")
import os
import django
import pandas as pd
import datetime
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "alpha.settings")
django.setup()

import asyncio

from apps.rubicon_v3.__external_api._08_kr_user_record import KR_UserRecord
from apps.rubicon_v3.__external_api._10_kr_membership_info import KR_MembershipInfo
from apps.rubicon_v3.__external_api._11_user_info import IndivInfo, getMyProducts
from apps.rubicon_v3.__external_api._12_uk_user_record import UK_UserRecord
from apps.rubicon_v3.__external_api._13_uk_membership_info import UK_MembershipInfo
from apps.rubicon_data.models import product_category, uk_product_spec_basics


def account_info_api(guid, country_code, channel):
    account_info_dict = {}
    if country_code == "KR":
        membershipInfo = KR_MembershipInfo("KR", guid, channel)
        mem_result = asyncio.run(membershipInfo.getMembershipIdTier())
        mem_info = mem_result.get("mem_rank", "") if mem_result is not None else ""
        mem_id = mem_result.get("mem_id", "") if mem_result is not None else ""
        mem_point = None
        if mem_id:
            mem_point_result = asyncio.run(membershipInfo.getOverallPoint(mem_id))
            mem_point = (
                mem_point_result.get("samsung_point", "")
                if mem_point_result is not None
                else ""
            )

        if mem_info:
            account_info_dict["rank"] = mem_info + " 등급"
        
        if mem_point:
            account_info_dict["point"] = mem_point + " P 보유"
        
            
    elif country_code == "GB":
        membershipInfo = UK_MembershipInfo("GB", guid, channel)
        mem_info = asyncio.run(membershipInfo.getMembershipTier())
        mem_point = asyncio.run(membershipInfo.getMembershipPoint())
        
        if mem_info:
            account_info_dict["rank"] = mem_info
            
        if mem_point is not None:
            account_info_dict["point"] = str(mem_point) + " p "
        
    return account_info_dict

def add_model_name(df, country_code, site_cd):
    model_name_result = []
    model_dict = {}
    product_codes = df["Model Code"].tolist()
    if country_code == "KR":
        model_name_result = list(product_category.objects.filter(
            mdl_code__in=product_codes, site_cd=site_cd
        ).values("goods_nm", "mdl_code"))

    elif country_code == "GB":
        model_name_result = list(uk_product_spec_basics.objects.filter(
            model_code__in=product_codes, site_cd=site_cd,
        ).values("display_name", "model_code"))
    
    if model_name_result:
        unique_results = {(item.get("mdl_code") or item.get("model_code")): (item.get("goods_nm") or item.get("display_name")) for item in model_name_result}
        model_dict = unique_results
        
    if model_dict:
        mask = df["Model Name"].isnull()
        model_codes_to_map = df.loc[mask, "Model Code"]
        df.loc[mask, "Model Name"] = model_codes_to_map.map(model_dict)

    return df


def account_activity_api(guid, sa_id, country_code, site_cd, channel, n_item=10, n_item_recent_view=5):
    account_activity_dict = {}
    user_product_result = ["no registered devices"]
    wish_result = ["empty wish list"]
    cart_result = ["empty cart list"]
    recent_view_result = ["empty recent view list"] 
    
    if country_code == "KR":        
        infoObject_user = IndivInfo(country_code, sa_id, guid, channel)
        myproducts_input = asyncio.run(infoObject_user.getUserProducts())
        user_product_df = getMyProducts(myproducts_input) # 보유기기 
        
        infoObject = KR_UserRecord("KR", guid, channel)
        recent_view_df = asyncio.run(infoObject.getRecentViewLists()) # 최근 본 상품
        wish_df = asyncio.run(infoObject.getWishLists()) # 찜 목록
        cart_df = asyncio.run(infoObject.getCartList()) # 장바구니
        
        if not user_product_df.empty:
            user_product_result = user_product_df
            user_product_result['registrationTimestamp'] = user_product_result['registrationTimestamp'].apply(lambda x: datetime.datetime.fromtimestamp(x/1000).date().isoformat())
            user_product_result.columns = ["Model Code", "Model Name", "Registered Date"]
            user_product_result = user_product_result.sort_values(['Registered Date'], ascending=False).drop(["Registered Date"],axis=1)
            user_product_result = add_model_name(user_product_result, country_code, site_cd)
            user_product_result = user_product_result.to_dict("records")[:n_item]
  
        if not recent_view_df.empty:
            recent_view_result = recent_view_df[["mdl_code", "goods_nm", "sysRegDtm"]]
            recent_view_result['sysRegDtm'] = recent_view_result['sysRegDtm'].apply(lambda x: datetime.datetime.fromtimestamp(x/1000).date().isoformat())
            recent_view_result = recent_view_result.sort_values(['sysRegDtm'], ascending=False).drop(['sysRegDtm'],axis=1)
            recent_view_result.columns = ["Model Code", "Model Name"]
            recent_view_result = add_model_name(recent_view_result, country_code, site_cd)
            recent_view_result = recent_view_result.to_dict("records")[:n_item_recent_view]

        if not wish_df.empty:
            wish_result = wish_df[["mdl_code", "goods_nm", "sysRegDtm"]]
            wish_result['sysRegDtm'] = wish_result['sysRegDtm'].apply(lambda x: datetime.datetime.fromtimestamp(x/1000).date().isoformat())
            wish_result = wish_result.sort_values(['sysRegDtm'], ascending=False).drop(['sysRegDtm'],axis=1)
            wish_result.columns = ["Model Code", "Model Name"]
            wish_result = add_model_name(wish_result, country_code, site_cd)
            wish_result = wish_result.to_dict("records")[:n_item]

        if not cart_df.empty:
            goods_id_list = cart_df["goods_id"].tolist()
            goods_id_results = list(
                product_category.objects.filter(
                    goods_id__in=goods_id_list, site_cd=site_cd
                ).values("goods_id", "mdl_code", "goods_nm")
            )
            
            if goods_id_results:
                cart_result = pd.DataFrame(goods_id_results)
                cart_result = pd.merge(cart_df, cart_result, on='goods_id')
                if not cart_result.empty:
                    cart_result = cart_result[['mdl_code','goods_nm', 'buy_qty']]
                    cart_result.columns = ["Model Code", "Model Name", "Quantity"]
                    cart_result = cart_result.to_dict("records")
                else:
                    cart_result = ["empty cart list"]
        
        account_activity_dict["user_products"] = user_product_result
        account_activity_dict["recent_view_list"] = recent_view_result
        account_activity_dict["wish_list"] = wish_result
        account_activity_dict["cart_list"] = cart_result

    elif country_code == "GB":        
        infoObject_user = IndivInfo(country_code, sa_id, guid, channel)
        myproducts_input = asyncio.run(infoObject_user.getUserProducts())
        user_product_df = getMyProducts(myproducts_input) # 보유기기
        
        infoObject = UK_UserRecord("GB", sa_id, channel)
        wish_df = asyncio.run(infoObject.getWishLists()) # 찜 목록
        cart_df = asyncio.run(infoObject.getCarts()) # 장바구니 
        
        if not user_product_df.empty:
            user_product_result = user_product_df
            user_product_result['registrationTimestamp'] = user_product_result['registrationTimestamp'].apply(lambda x: datetime.datetime.fromtimestamp(x/1000).date().isoformat())
            user_product_result.columns = ["Model Code", "Model Name", "Registered Date"]
            user_product_result = user_product_result.sort_values(['Registered Date'], ascending=False).drop(["Registered Date"],axis=1)
            user_product_result = add_model_name(user_product_result, country_code, site_cd)
            user_product_result = user_product_result.to_dict("records")[:n_item]
        
        if not wish_df.empty:
            model_code_list = wish_df["code"].tolist()
            model_code_result = list(
                uk_product_spec_basics.objects.filter(
                    model_code__in=model_code_list, site_cd=site_cd
                ).values("model_code", "display_name")
            )
            
            if model_code_result:
                wish_result = pd.DataFrame(model_code_result)
                if not wish_result.empty:
                    wish_result.columns = ["Model Code", "Model Name"]
                    wish_result = wish_result.to_dict("records")[:n_item]

        if not cart_df.empty:
            model_code_list = cart_df["code"].tolist()
            model_code_result = list(
                uk_product_spec_basics.objects.filter(
                    model_code__in=model_code_list, site_cd=site_cd
                ).values("model_code", "display_name")
            )
            if model_code_result:
                cart_result = pd.DataFrame(model_code_result)
                cart_df = cart_df.rename(columns={'code':'model_code'})
                cart_result = pd.merge(cart_df, cart_result, on='model_code')
                if not cart_result.empty:
                    cart_result = cart_result[['model_code','display_name', 'quantity']]
                    cart_result.columns = ["Model Code", "Model Name", "Quantity"]
                    cart_result = cart_result.to_dict("records")
                    
        account_activity_dict["user_products"] = user_product_result
        account_activity_dict["wish_list"] = wish_result
        account_activity_dict["cart_list"] = cart_result

    return account_activity_dict


def order_delivery_api(guid, country_code, channel):
    order_info_list = ["empty order list"]
    order_df = pd.DataFrame()
    if country_code == "KR":
        infoObject = KR_UserRecord("KR", guid, channel)
        order_df = asyncio.run(infoObject.getOrderLists("ORD"))
        if not order_df.empty:
            order_df = order_df[
                [
                    "goods_nm",
                    "mdl_code",
                    "ord_qty",
                    "ord_stat_cd_nm",
                    "ord_dtl_stat_cd_nm",
                    "inv_no",
                ]
            ]
            order_df.columns = [
                "Model Name",
                "Model Code",
                "Order Quantity",
                "Order Status",
                "Order Detail Status",
                "Tracking Number",
            ]
            order_info_list = order_df.to_dict(orient="records")
    return order_info_list


if __name__ == "__main__":
    membershipInfo = account_info_api("3bpy5kn7yk", "GB", channel="DEV Debug")
    print(membershipInfo)
    order_info = order_delivery_api("sjqheizzwm", "KR", channel="DEV Debug")
    print(order_info)
