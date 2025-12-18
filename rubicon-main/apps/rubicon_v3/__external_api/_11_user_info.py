import hmac
import hashlib
import base64
import requests
import certifi
from datetime import datetime, timezone
from urllib.parse import urlparse
import asyncio
import sys
sys.path.append("/www/alpha")
from apps.rubicon_v3.__external_api.__apiRequest import apiHandler
import time
import pandas as pd
import os

class IndivInfo():

    def __init__(self, country, sa_id, guid, channel=None):
        self.country = country
        self.apiRequester = apiHandler(self.country, channel)
        self.opType = self.apiRequester.opType
        self.sa_id = sa_id
        self.guid = guid
        #self.jwt_token = jwt_token
        if self.opType.upper() in ["DEV", "STG"]:
            self.client_id = os.environ.get("SA_CLIENT_ID_STG")
            self.client_secret = os.environ.get("SA_CLIENT_SECRET_STG")
        elif self.opType.upper() in ["PRD", "PROD"]:
            self.client_id = os.environ.get("SA_CLIENT_ID_PRD")
            self.client_secret = os.environ.get("SA_CLIENT_SECRET_PRD")
        else:
            self.client_id = ""
            self.client_secret = ""

    async def get_rfc1123_date(self):
        return datetime.now(timezone.utc).strftime('%a, %d %b %Y %H:%M:%S UTC')
    
    async def generate_hmac_signature(self, secret: str, data: str) -> str:
        digest = hmac.new(secret.encode('utf-8'), data.encode('utf-8'), hashlib.sha256).digest()
        return base64.b64encode(digest).decode('utf-8')
    
    async def build_user_signature(self, date_header) -> str:
        lines = [f"(request-target): get /v1/users"]
        headers = {
            "date": date_header,
            "x-app-id": self.client_id
        }
        for k, v in headers.items():
            lines.append(f"{k}: {v}")
        return "\n".join(lines)
    
    async def getUserInfo(self):
        try:
            if self.sa_id == 'default_sa_id' or self.sa_id is None:
                return None
            if self.opType.upper() in ["DEV", "STG"]:
                url = "https://ipaas-scadev.sec.samsung.net/sec/kr/samsungaccount_gs_getuser/1.0/v1/users"
            elif self.opType.upper() in ["PRD", "PROD"]:
                url = "https://ipaas-sca.sec.samsung.net/sec/kr/samsungaccount_gs_getuser/1.0/v1/users"
            parsed_proxy = urlparse(url)
            query = f"{parsed_proxy.query}&cookie={self.sa_id}" if parsed_proxy.query else f"cookie={self.sa_id}"
            full_proxy_url = f"{parsed_proxy.scheme}://{parsed_proxy.netloc}{parsed_proxy.path}?{query}"

            date_header = await self.get_rfc1123_date()
            signature_string = await self.build_user_signature(date_header)
            signature = await self.generate_hmac_signature(self.client_secret, signature_string)
            token = await self.apiRequester.get_siis_token()

            # 요청 헤더 세팅
            request_headers = {
                "Authorization": f"Bearer {token}",
                "iPaaS-Backend-Authorization": (
                    f'Signature keyId="{self.client_id}",algorithm="hmac-sha256",headers="(request-target) date x-app-id",signature="{signature}"'
                ),
                "x-app-id": self.client_id,
                #"Content-Type": "application/json",
                "Accept": "application/json",
                "Accept-Charset": "UTF-8",
                #"User-Agent": "Mozilla/5.0",
                "date": date_header
            }

            response = await self.apiRequester.call_api(
                method="get",
                url=full_proxy_url,
                headers=request_headers,
                param=None,
                data=None
            )
            if response.status_code == 200:
                self.guid = getGuid(response.json())
                return response.json()
            else:
                return None
        except Exception as e:
            return None
        
    async def build_product_signature(self, date_header) -> str:
        lines = [f"(request-target): get /v2/product"]
        headers = {
            "date": date_header,
            "x-osp-appid": self.client_id
        }
        for k, v in headers.items():
            lines.append(f"{k}: {v}")
        return "\n".join(lines)
        
    async def getUserProducts(self):
        try:
            url = ""
            if self.opType.upper() in ["DEV", "STG"]:
                if self.country == "KR":
                    url = "https://ipaas-scadev.sec.samsung.net/sec/kr/samsungaccount_ap_product/1.0/product" 
                elif self.country in ["UK", "GB"]:
                    url = "https://ipaas-scadev.sec.samsung.net/sec/kr/samsungaccount_eu_product/1.0/product"
            elif self.opType.upper() in ["PRD", "PROD"]:
                if self.country == "KR":
                    url = "https://ipaas-sca.sec.samsung.net/sec/kr/samsungaccount_ap_product/1.0/product" 
                elif self.country in ["UK", "GB"]:
                    url = "https://ipaas-sca.sec.samsung.net/sec/kr/samsungaccount_eu_product/1.0/product"

            date_header = await self.get_rfc1123_date()
            signature_string = await self.build_product_signature(date_header)
            signature = await self.generate_hmac_signature(self.client_secret, signature_string)
            token = await self.apiRequester.get_siis_token()

            # 요청 헤더 세팅
            request_headers = {
                "date": date_header,
                "x-osp-appid": self.client_id,
                "iPaaS-Backend-Authorization": (
                    f'Signature keyId="{self.client_id}",algorithm="hmac-sha256",headers="(request-target) date x-osp-appid",signature="{signature}"'
                ),
                "Accept": "application/json",
                "Accept-Charset": "utf-8",
                "Authorization": f"Bearer {token}",
                'Content-Type': 'application/json'
            }
            param = {}
            param["userId"] = self.guid
            response = await self.apiRequester.call_api(
                method="get",
                url=url,
                headers=request_headers,
                param=param,
                data=None
            )
            if response.status_code == 200:
                return response.json()
            else:
                return None
        except Exception as e:
            return None

def getGuid(dictionary):
    if dictionary is None:
        return None
    if "id" in dictionary:
        return dictionary["id"]
    else:
        return None
    
def getCountryCode(dictionary):
    if dictionary is None:
        return None
    if "countryCode" in dictionary:
        return dictionary["countryCode"]
    else:
        return None
    
def getFirstName(dictionary):
    if dictionary is None:
        return None
    if "firstName" in dictionary:
        return dictionary["firstName"]
    else:
        return None
    
def getLastName(dictionary):
    if dictionary is None:
        return None
    if "lastName" in dictionary:
        return dictionary["lastName"]
    else:
        return None
    
def getBirthDay(dictionary):
    if dictionary is None:
        return None
    if "birthday" in dictionary:
        return dictionary["birthday"]
    else:
        return None
    
def getGender(dictionary):
    if dictionary is None:
        return None
    if "gender" in dictionary:
        return dictionary["gender"]
    else:
        return None
    
def getMyProducts(dictionary):
    if dictionary is None:
        return pd.DataFrame()
    if "products" in dictionary:
        try:
            result_df = pd.DataFrame(dictionary["products"])[['modelCode', 'modelName', 'registrationTimestamp']]
            return result_df
        except Exception as e:
            return pd.DataFrame()
    else:
        return pd.DataFrame()

if __name__ == "__main__":
    start = time.time()
    country = "GB"
    sa_id = "dd4d51bd5fc67f72eda6c56a6602a036984e25ce1042d2a3b9b5622ab3ff59d11e7f529dff4f1077273f07f870f883832892dfc114265dc2dc5d9f18f3f5563ec76b7591c6c8eabe6333f0f5f6b7df7c8692a3c4e1678b7eca46848627525e86d8729fba86500c79b66f9ae5a95216076e984d76a49ded2c137854dd2f222fcc158bdb1da11818ca63ea5ac5f08a9077ffbb809441ab2651db9d35037dbe0dc5d7dd42b6abfd8e6251d1442cfb002917b44506640b8d1b179bf38c39e73cbd32884c4035f2c033f4d6ca6c1cac496ac19a52da998b2110fff365c353f2657856b37abce61153fe0e6d6d94a010a43261e332b3e1ff35925dc3a5ccf2768522328bf2266dab1938c4cf5de803f4be857d3f0510181f7d2d16e54e25a626dd843bf3c0"
    #guid = "jcvsdcwkth"
    ddd = IndivInfo(country, sa_id, "3423423423")
    result_dict = asyncio.run(ddd.getUserInfo())
    print(result_dict)  
    print(getGuid(result_dict))
    #print(getCountryCode(None))
    #print(getFirstName(result_dict))
    #print(getLastName(result_dict))
    #print(getBirthDay(result_dict))
    #print(getGender(result_dict))
    #result_dict2 = asyncio.run(ddd.getUserProducts())
    #print(f'input:{result_dict2}')
    #print(getMyProducts(result_dict2))