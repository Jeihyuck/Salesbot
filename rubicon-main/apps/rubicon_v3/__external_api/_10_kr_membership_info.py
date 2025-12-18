import aiohttp
import pandas as pd
import asyncio
from sqlalchemy import create_engine, MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import xmltodict
import sys
sys.path.append("/www/alpha")
from apps.rubicon_v3.__external_api.__apiRequest import apiHandler
from apps.rubicon_v3.__external_api.__aes_encode import AES_Encoder

## FROM GCRM APIs
class KR_MembershipInfo:
    def __init__(self, country, guid, channel=None):
        self.country = country
        self.apiRequester = apiHandler(self.country, channel)
        self.opType = self.apiRequester.opType
        self.guid = guid
        self.enccoder = AES_Encoder()

    async def getMembershipIdTier(self):
        try:
            token = await self.apiRequester.get_siis_token()
            param = {}
            random_id = ''
            if self.opType.upper() in ["DEV", "STG"]:
                base_url = "https://ipaas-scadev.sec.samsung.net/sec/kr/gcrm_kr_mem_search_api/1.0/MEM_SEARCH_API"
                random_id = 'YGW9OH8H'
            elif self.opType.upper() in ["PROD", "PRD"]:    
                base_url = "https://ipaas-sca.sec.samsung.net/sec/kr/gcrm_kr_mem_search_api/1.0/MEM_SEARCH_API"
                random_id = 'YGW9OH8H'
            authKey = self.enccoder.doEncoding(random_id)
            headers = {
                        'Authorization': f'Bearer {token}',
                        'AuthKey': f'{authKey}' 
                    }
            data = f"""<INFO><IV_RESTORE>N</IV_RESTORE><IV_RESTORE_RSN>RUBICON</IV_RESTORE_RSN><IV_AGENCY>SYS00042</IV_AGENCY><IV_ZZSAGUID>{self.guid}</IV_ZZSAGUID></INFO>"""
            response = await self.apiRequester.call_api('post', base_url, headers, param, data)
            response_text = response.text
            if len(response_text) > 0:
                result_dict = xmltodict.parse(response_text)
                result_json = {}
                result_json['mem_id'] = result_dict['RESULT']['EV_MEM_ID']
                result_json['mem_rank'] = result_dict['RESULT']['EV_MEM_TIER_NM']
                return result_json
            else:
                return None
        except Exception as e:
            return None
        
    async def getOverallPoint(self, mem_id):
        try:
            token = await self.apiRequester.get_siis_token()
            param = {}
            random_id = ''
            if self.opType.upper() in ["DEV", "STG"]:
                base_url = "https://ipaas-scadev.sec.samsung.net/sec/kr/gcrm_kr_zmem7107/1.0/ZMEM7107"
                random_id = 'A241025A'
            elif self.opType.upper() in ["PROD", "PRD"]:    
                base_url = "https://ipaas-sca.sec.samsung.net/sec/kr/gcrm_kr_zmem7107/1.0/ZMEM7107"
                random_id = 'YGW9OH8H'
            authKey = self.enccoder.doEncoding(random_id)
            headers = {
                        'Authorization': f'Bearer {token}',
                        'AuthKey': f'{authKey}' 
                    }
            data = f"""<INFO><IV_CERT_TP>10</IV_CERT_TP><IV_CERT_VAL>{mem_id}</IV_CERT_VAL><IV_COUNTRY>KR</IV_COUNTRY><IV_IF_ID>IFMEM0275S</IV_IF_ID><IV_PNT_TYPE_CD>SPNT</IV_PNT_TYPE_CD><IV_SYS_CD>COM_WEB</IV_SYS_CD></INFO>"""
            response = await self.apiRequester.call_api('post', base_url, headers, param, data)
            response_text = response.text
            if len(response_text) > 0:
                result_dict = xmltodict.parse(response_text)
                result_json = {}
                result_json['samsung_point'] = result_dict['RESULT']['EV_S_POINT']
                result_json['u_point'] = result_dict['RESULT']['EV_U_POINT']
                result_json['expire_point'] = result_dict['RESULT']['EV_E_POINT']
                result_json['ocb_point'] = result_dict['RESULT']['EV_OCB_POINT']
                return result_json
            else:
                return None
        except Exception as e:
            return None
        
    async def getMembershipValidity(self):
        try:
            token = await self.apiRequester.get_siis_token()
            param = {}
            random_id = ''
            if self.opType.upper() in ["DEV", "STG"]:
                base_url = "https://ipaas-scadev.sec.samsung.net/sec/kr/gcrm_kr_zmem7909_api/1.0/ZMEM7909_API"
                random_id = 'CO95G1DG'
            elif self.opType.upper() in ["PROD", "PRD"]:    
                base_url = "https://ipaas-sca.sec.samsung.net/sec/kr/gcrm_kr_zmem7909_api/1.0/ZMEM7909_API"
                random_id = 'YGW9OH8H'
            authKey = self.enccoder.doEncoding(random_id)
            headers = {
                        'Authorization': f'Bearer {token}',
                        'AuthKey': f'{authKey}' 
                    }
            data = f"""<INFO><IV_COUNTRY>KR</IV_COUNTRY><IV_SAGUID>{self.guid}</IV_SAGUID></INFO>"""
            response = await self.apiRequester.call_api('post', base_url, headers, param, data)
            response_text = response.text
            if len(response_text) > 0:
                result_dict = xmltodict.parse(response_text)
                result_json = {}
                result_json['mem_rank'] = result_dict['RESULT']['EV_TIER_LEVEL_TEXT']
                result_json['start_date'] = result_dict['RESULT']['EV_START_DATE']
                result_json['end_date'] = result_dict['RESULT']['EV_END_DATE']
                result_json['sales_from'] = result_dict['RESULT']['EV_SALES_FROM']
                result_json['sales_to'] = result_dict['RESULT']['EV_SALES_TO']
                result_json['next_rank'] = result_dict['RESULT']['EV_NEXT_TIER_TEXT']
                result_json['target_rank'] = result_dict['RESULT']['EV_NEXT_TGT_TEXT']
                result_json['required_amt'] = result_dict['RESULT']['EV_REQUIRED_AMT']
                result_json['target_limit'] = result_dict['RESULT']['EV_NEXT_TGT_LIMIT']
                return result_json
            else:
                return None
        except Exception as e:
            return None
    
if __name__ == "__main__":
    membershipInfo = KR_MembershipInfo('KR', '9n0umijbja')
    mem_result = asyncio.run(membershipInfo.getMembershipIdTier())
    print(mem_result)
    mem_point = asyncio.run(membershipInfo.getOverallPoint(mem_result['mem_id']))
    print(mem_point)
    validity = asyncio.run(membershipInfo.getMembershipValidity())
    print(validity)
    #asyncio.run(membershipInfo.getCashbackPoint(mem_result['mem_id']))

    