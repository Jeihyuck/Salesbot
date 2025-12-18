import aiohttp
import pandas as pd
import asyncio
from sqlalchemy import create_engine, MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import sys
import os
sys.path.append("/www/alpha")
from apps.rubicon_v3.__external_api.__apiRequest import apiHandler
from apps.rubicon_v3.__external_api.__dkms_encode import DKMS_Encoder


## FROM KDP APIs
class KR_UserRecord:
    def __init__(self, country, guid, channel=None):
        self.country = country
        self.apiRequester = apiHandler(self.country, channel)
        self.opType = self.apiRequester.opType
        self.guid = guid
        self.dkmsClient = DKMS_Encoder(channel)
        try:
            self.encrypted_guid = self.dkmsClient.getEncryptedValue(self.guid)
        except:
            self.encrypted_guid = ""

    async def getRecentViewLists(self):
        try:
            token = await self.apiRequester.get_siis_token()
            param = {}
            if self.opType.upper() in ["DEV", "STG"]:
                base_url = "https://ipaas-scadev.sec.samsung.net/sec/kr/DigitalPlatform_KOREA_KDP_PROD_RCT_VIEW/1.0/719"
            elif self.opType.upper() in ["PROD", "PRD"]:
                base_url = "https://ipaas-sca.sec.samsung.net/sec/kr/DigitalPlatform_KOREA_KDP_PROD_RCT_VIEW/1.0/719"
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
                "kdp-api-clientId": os.environ.get("KDP_CLIENT_ID"),
                "kdp-api-ifId": "719",
            }
            data = {"guid": self.encrypted_guid}
            response = await self.apiRequester.call_api(
                "post", base_url, headers, param, data
            )
            payload = response.json().get("payload", {})
            recentGoodsList = payload.get("recentGoodsList", [])
            response_custom = [
                {
                    "goods_id": item.get("goodsId"),
                    "goods_nm": item.get("goodsNm"),
                    "mdl_code": item.get("mdlCode"),
                    "goods_path": item.get("goodsPath"),
                    "sysRegDtm": item.get("sysRegDtm")
                }
                for item in recentGoodsList
            ]
            return pd.DataFrame(response_custom)[["goods_id", "goods_nm", "mdl_code", "sysRegDtm"]]
        except Exception as e:
            return pd.DataFrame()

    async def getWishLists(self):
        try:
            token = await self.apiRequester.get_siis_token()
            param = {}
            if self.opType.upper() in ["DEV", "STG"]:
                base_url = "https://ipaas-scadev.sec.samsung.net/sec/kr/DigitalPlatform_KOREA_KDP_PROD_WISHLIST/1.0/720"
            elif self.opType.upper() in ["PROD", "PRD"]:
                base_url = "https://ipaas-sca.sec.samsung.net/sec/kr/DigitalPlatform_KOREA_KDP_PROD_WISHLIST/1.0/720"
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
                "kdp-api-clientId": os.environ.get("KDP_CLIENT_ID"),
                "kdp-api-ifId": "722",
            }
            data = {"guid": self.encrypted_guid}
            response = await self.apiRequester.call_api(
                "post", base_url, headers, param, data
            )
            result_df = pd.DataFrame(
                response.json().get("payload", {}).get("goods_list", [])
            )[
                [
                    "goodsId",
                    "goodsNm",
                    "mdlCode",
                    "goodsSalePrice",
                    "goodsPrice",
                    "salesYn",
                    "sysRegDtm"
                ]
            ]
            nameDict = {
                "goodsId": "goods_id",
                "goodsNm": "goods_nm",
                "mdlCode": "mdl_code",
                "goodsSalePrice": "inital_price",
                "goodsPrice": "final_price",
            }
            result_df.rename(columns=nameDict, inplace=True)
            return result_df
        except Exception as e:
            return pd.DataFrame()

    async def getDeliveryInfo(self):
        try:
            token = await self.apiRequester.get_siis_token()
            param = {}
            if self.opType.upper() in ["DEV", "STG"]:
                base_url = "https://ipaas-scadev.sec.samsung.net/sec/kr/DigitalPlatform_KOREA_KDP_USER_DLVRA/1.0/724"
            elif self.opType.upper() in ["PROD", "PRD"]:
                base_url = "https://ipaas-sca.sec.samsung.net/sec/kr/DigitalPlatform_KOREA_KDP_USER_DLVRA/1.0/724"
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
                "kdp-api-clientId": os.environ.get("KDP_CLIENT_ID"),
                "kdp-api-ifId": "724",
            }
            data = {"guid": self.encrypted_guid}
            response = await self.apiRequester.call_api(
                "post", base_url, headers, param, data
            )

            return pd.DataFrame(
                response.json().get("payload", {}).get("address_list", [])
            )[["dftYn", "postNoNew", "prclAddr", "roadAddr"]]
        except Exception as e:
            return pd.DataFrame()

    async def getOrderLists(self, api_type):
        try:
            """
            api type
            ORD: 주문/배송 내역
            CLM: 취소/반품 내역
            DIV: 나눠서 결제 내역
            REG: 정기 구매 내역
            """
            token = await self.apiRequester.get_siis_token()
            param = {}
            if self.opType.upper() in ["DEV", "STG"]:
                base_url = "https://ipaas-scadev.sec.samsung.net/sec/kr/DigitalPlatform_KOREA_KDP_USER_ORDER/1.0/711"
            elif self.opType.upper() in ["PROD", "PRD"]:
                base_url = "https://ipaas-sca.sec.samsung.net/sec/kr/DigitalPlatform_KOREA_KDP_USER_ORDER/1.0/711"
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
                "kdp-api-clientId": os.environ.get("KDP_CLIENT_ID"),
                "kdp-api-ifId": "710",
            }
            data = {
                "GUID": self.encrypted_guid,
                "api_type": api_type,
                # 'ord_no' : 'KR240423-00031743' [Optional]
            }
            response = await self.apiRequester.call_api(
                "post", base_url, headers, param, data
            )
            result = []
            for singleData in response.json().get("payload", {}).get("order_list", []):
                for orderData in singleData.get("order_detail_list", []):
                    simpleData = {}
                    simpleData["ord_no"] = singleData.get("ord_no", "")  ##주문번호
                    simpleData["ord_acpt_dtm"] = singleData.get(
                        "ord_acpt_dtm", ""
                    )  ##주문접수일시
                    simpleData["ord_cplt_dtm"] = singleData.get(
                        "ord_cplt_dtm", ""
                    )  ##주문완료일시
                    simpleData["ord_stat_cd_nm"] = singleData.get(
                        "ord_stat_cd_nm", ""
                    )  ##주문상태코드명 ex)주문완료
                    simpleData["pay_amt_total"] = singleData.get(
                        "pay_amt_total", ""
                    )  ##총결제금액
                    simpleData["ord_dlvr_mtd_cd_nm"] = singleData.get(
                        "ord_dlvr_mtd_cd_nm", ""
                    )  ##주문배송방법코드명 ex)일반배송
                    simpleData["ord_dtl_cnt"] = singleData.get(
                        "ord_dtl_cnt", ""
                    )  ##주문상세건수
                    simpleData["ord_mda_cd_nm"] = singleData.get(
                        "ord_mda_cd_nm", ""
                    )  ##주문매체코드명 ex)MOBILE
                    simpleData["ord_prcs_rst_cd_nm"] = singleData.get(
                        "ord_prcs_rst_cd_nm", ""
                    )  ##주문처리결과코드명 ex)정상처리
                    simpleData["pay_means_cd_nm"] = singleData.get(
                        "pay_means_cd_nm", ""
                    )  ##결제수단코드명 ex)네이버페이
                    simpleData["order_type"] = singleData.get(
                        "order_type", ""
                    )  ##주문유형 ex)ORD
                    simpleData["ord_dtl_stat_cd_nm"] = orderData.get(
                        "ord_dtl_stat_cd_nm", ""
                    )  ##주문상세상태코드명 ex)배송완료
                    simpleData["goods_id"] = orderData.get("goods_id", "")
                    simpleData["goods_nm"] = orderData.get("goods_nm", "")
                    simpleData["mdl_code"] = orderData.get("mdl_code", "")
                    simpleData["sale_amt"] = orderData.get("sale_amt", "")  ##판매금액
                    simpleData["prmt_dc_amt"] = orderData.get(
                        "prmt_dc_amt", ""
                    )  ##프로모션할인금액
                    simpleData["cp_dc_amt"] = orderData.get(
                        "cp_dc_amt", ""
                    )  ##쿠폰할인금액
                    simpleData["pay_amt"] = orderData.get("pay_amt", "")  ##결제금액
                    simpleData["dlvr_no"] = orderData.get("dlvr_no", "")  ##배송번호 1
                    simpleData["ord_qty"] = orderData.get("ord_qty", "")  ##주문수량
                    simpleData["dlvr_opt_cd_nm"] = orderData.get("dlvr_opt_cd_nm", "") ## 배송옵션코드명 ex)Parcel Service
                    simpleData["do_no"] = orderData.get("do_no", "") ##배송번호 2
                    simpleData["so_no"] = orderData.get("so_no", "") ##ERP주문번호
                    simpleData["inv_no"] = orderData.get("inv_no", "") ##송장번호
                    result.append(simpleData)
            result_df = pd.DataFrame(result)
            return result_df
        except Exception as e:
            return pd.DataFrame()

    ## if logged-in, use guid, else use 'null'
    async def getEstimatedPoints(self, goods_list):
        """
        SKU List, not GoodsList
        """
        try:
            token = await self.apiRequester.get_siis_token()
            if self.opType.upper() in ["DEV", "STG"]:
                base_url = "https://ipaas-scadev.sec.samsung.net/sec/kr/DigitalPlatform_KOREA_KDP_PROD_MEMBERSHIP_POINT/1.0/710"
            elif self.opType.upper() in ["PROD", "PRD"]:
                base_url = "https://ipaas-sca.sec.samsung.net/sec/kr/DigitalPlatform_KOREA_KDP_PROD_MEMBERSHIP_POINT/1.0/710"

            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
                "kdp-api-clientId": os.environ.get("KDP_CLIENT_ID"),
                "kdp-api-ifId": "710",
            }
            total_df = pd.DataFrame()
            guid = ""
            if self.guid is None or self.guid == "" or self.guid == 'default_gu_id':
                guid = "null"
            else:
                guid = self.encrypted_guid
            async with aiohttp.ClientSession() as session:
                tasks = [
                    self._getGoodsPointData(session, base_url, headers, goods_id, guid)
                    for goods_id in goods_list
                ]
                results = await asyncio.gather(*tasks)

            for result in results:
                total_df = pd.concat([total_df, result], ignore_index=True)

            nameDict = {"goodsId": "goods_id"}
            total_df.rename(columns=nameDict, inplace=True)
            return total_df
        except Exception as e:
            return pd.DataFrame()

    async def _getGoodsPointData(self, session, base_url, headers, goodsId, guid):
        try:
            data = {"goodsId": goodsId, "guid": guid}
            async with session.post(base_url, headers=headers, json=data) as response:
                if response.status == 200:
                    response_json = await response.json()
                    return await self._getFormattedPointData(goodsId, response_json)
                else:
                    print(
                        f"Error: {response.status}, Response: {await response.text()}"
                    )
                    return pd.DataFrame()
        except Exception as e:
            return pd.DataFrame()

    async def _getFormattedPointData(self, goodsId, response_json):
        try:
            payload = response_json.get("payload", {})
            response_custom = {
                "goodsId": goodsId,
                "webMembershipPoint": payload.get("webMembershipPoint", None),
                "appMembershipPoint": payload.get("appMembershipPoint", None),
            }
            if response_custom.get("webMembershipPoint") is None and response_custom.get("appMembershipPoint") is None:
                return pd.DataFrame()
            return pd.DataFrame([response_custom])
        except Exception as e:
            return pd.DataFrame()
        
    async def getCartList(self):
        try:
            token = await self.apiRequester.get_siis_token()
            param = {}
            if self.opType.upper() in ["DEV", "STG"]:
                base_url = "https://ipaas-scadev.sec.samsung.net/sec/kr/DigitalPlatform_KOREA_KDP_USER_CART/1.0/767"
            elif self.opType.upper() in ["PROD", "PRD"]:
                base_url = "https://ipaas-sca.sec.samsung.net/sec/kr/DigitalPlatform_KOREA_KDP_USER_CART/1.0/767"
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
                "kdp-api-clientId": os.environ.get("KDP_CLIENT_ID"),
                "kdp-api-ifId": "726",
            }
            data = {"guid": self.encrypted_guid}
            response = await self.apiRequester.call_api(
                "post", base_url, headers, param, data
            )
            return pd.DataFrame(response.json().get("payload", {}).get("cart_list", []))
        except Exception as e:
            return pd.DataFrame()


if __name__ == "__main__":
    infoObject = KR_UserRecord(
        "KR", "sjqheizzwm"
    )  # jcvsdcwkth - sh  ///// oaibtwbgeb - jh
    print(asyncio.run(infoObject.getRecentViewLists()))
    print(asyncio.run(infoObject.getDeliveryInfo()))
    print(asyncio.run(infoObject.getEstimatedPoints(['G000430001', 'G00043000'])))
    print(asyncio.run(infoObject.getWishLists()))
    print(asyncio.run(infoObject.getCartList()))
    print(asyncio.run(infoObject.getOrderLists("ORD")))
    #print(asyncio.run(infoObject.getOrderLists('CLM')))
    #print(asyncio.run(infoObject.getOrderLists('DIV')))
    #print(asyncio.run(infoObject.getOrderLists('REG')))
