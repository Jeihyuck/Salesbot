import aiohttp
import pandas as pd
import asyncio
from sqlalchemy import create_engine, MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import sys
sys.path.append("/www/alpha")
from apps.rubicon_v3.__external_api.__apiRequest import apiHandler
from datetime import datetime
import os

## FROM GCRM APIs
class UK_MembershipInfo:
    def __init__(self, country, guid, channel=None):
        self.country = country
        self.apiRequester = apiHandler(self.country, channel)
        self.opType = self.apiRequester.opType
        self.guid = guid
        #self.enccoder = AES_Encoder()

    async def getToken(self):
        try:
            headers = {}
            if self.opType.upper() in ["DEV", "STG"]:
                base_url = "https://api-qas-rewards.gcdmloyalty.com/crm/eims/sap/opu/odata/sap/ZTIER_INFO_SRV"
                headers['Authorization'] = f'Bearer {os.environ.get("GLOBAL_GCRM_AUTH_STG")}'
            elif self.opType.upper() in ["PROD", "PRD"]:    
                base_url = "https://api-rewards.gcdmloyalty.com/crm/eims/sap/opu/odata/sap/ZTIER_INFO_SRV"
                headers['Authorization'] = f'Bearer {os.environ.get("GLOBAL_GCRM_AUTH_PRD")}'
            headers['X-CSRF-Token'] = 'fetch'
            param = {}
            data = {}
            response = await self.apiRequester.call_api('get', base_url, headers, param, data)
            if self.opType.upper() in ["DEV", "STG"]:
                return response.headers.get('x-csrf-token', None), response.cookies.get('SAP_SESSIONID_CLQ_200')
            elif self.opType.upper() in ["PROD", "PRD"]:
                return response.headers.get('x-csrf-token', None), response.cookies.get('sap-XSRF_CLP_100')
        except Exception as e:
            return None
    
    async def getMembershipPoint(self):
        try:
            headers = {}
            if self.opType.upper() in ["DEV", "STG"]:
                base_url = "https://api-qas-rewards.gcdmloyalty.com/crm/eims/sap/bc/ZRWD1103"
                headers['Authorization'] = f'Bearer {os.environ.get("GLOBAL_GCRM_AUTH_STG")}'
            elif self.opType.upper() in ["PROD", "PRD"]:    
                base_url = "https://api-rewards.gcdmloyalty.com/crm/eims/sap/bc/ZRWD1103"
                headers['Authorization'] = f'Bearer {os.environ.get("GLOBAL_GCRM_AUTH_PRD")}'
            headers['x-smrs-cc2'] = 'GB'
            headers['x-smrs-pid'] = 'AI_CHAT_GB'
            headers['user-id'] = f'{self.guid}'
            param = {}
            data = {}
            response = await self.apiRequester.call_api('get', base_url, headers, param, data)
            return response.json().get('pointBalance', None)
        except Exception as e:
            return None
        
    async def getMembershipTier(self):
        try:
            csrf_token, cookie_value = await self.getToken()
            if csrf_token == None:
                return None
            else:
                headers = {}
                if self.opType.upper() in ["DEV", "STG"]:
                    base_url = "https://api-qas-rewards.gcdmloyalty.com/crm/eims/sap/opu/odata/sap/ZTIER_INFO_SRV/TierInfoSet"
                    headers['Authorization'] = f'Bearer {os.environ.get("GLOBAL_GCRM_AUTH_STG")}'
                    headers['Cookie'] = f'SAP_SESSIONID_CLQ_200={cookie_value}'
                elif self.opType.upper() in ["PROD", "PRD"]:    
                    base_url = "https://api-rewards.gcdmloyalty.com/crm/eims/sap/opu/odata/sap/ZTIER_INFO_SRV/TierInfoSet"
                    headers['Authorization'] = f'Bearer {os.environ.get("GLOBAL_GCRM_AUTH_PRD")}'
                    headers['Cookie'] = f'sap-XSRF_CLP_100={cookie_value}'
                headers['Accept'] = 'application/json'
                headers['X-CSRF-Token'] = f'{csrf_token}'
                
                param = {}
                if self.country in ['UK', 'GB']:
                    country = "GB"
                else:
                    country = ''
                now = datetime.now()
                formatted = now.strftime("%Y-%m-%dT%H:%M:%S")
                data = {
                    "Id" : "12345678910",
                    "Timestamp" : f"{formatted}",
                    "SAGuid" : f"{self.guid}",
                    "CountryDescription" : f"{country}"
                }
                response = await self.apiRequester.call_api('post', base_url, headers, param, data)
                return response.json().get('d', {}).get('TierName', None)
        except Exception as e:
            return None
        
    async def getExpirePoint(self):
        try:
            headers = {}
            if self.opType.upper() in ["DEV", "STG"]:
                base_url = "https://api-qas-rewards.gcdmloyalty.com/crm/eims/sap/bc/ZRWD1108"
                headers['Authorization'] = f'Bearer {os.environ.get("GLOBAL_GCRM_AUTH_STG")}'
            elif self.opType.upper() in ["PROD", "PRD"]:    
                base_url = "https://api-rewards.gcdmloyalty.com/crm/eims/sap/bc/ZRWD1108"
                headers['Authorization'] = f'Bearer {os.environ.get("GLOBAL_GCRM_AUTH_PRD")}'
            headers['x-smrs-cc2'] = 'GB'
            headers['x-smrs-pid'] = 'AI_CHAT_GB'
            headers['user-id'] = f'{self.guid}'
            param = {}
            data = {}
            response = await self.apiRequester.call_api('get', base_url, headers, param, data)
            return pd.DataFrame(response.json().get('expirations', None))
        except Exception as e:
            return pd.DataFrame()
    
if __name__ == "__main__":
    membershipInfo = UK_MembershipInfo('GB', 'lbflzfgtbc')
    result = asyncio.run(membershipInfo.getMembershipTier())
    print(result)
    result2 = asyncio.run(membershipInfo.getMembershipPoint())
    print(result2)
    result3 = asyncio.run(membershipInfo.getExpirePoint())
    print(result3)