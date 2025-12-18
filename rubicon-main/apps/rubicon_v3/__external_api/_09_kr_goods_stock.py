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

class KR_GoodsStock:
    def __init__(self, country, site_cd, channel=None):
        self.country = country
        self.apiRequester = apiHandler(self.country, channel)
        self.opType = self.apiRequester.opType
        self.site_cd = site_cd
    
    async def getGoodsStock(self, sku_list):
        '''
        SKU List, not GoodsList
        '''
        token = await self.apiRequester.get_siis_token()
        if self.opType.upper() in ["DEV", "STG"]:
            if self.site_cd == 'B2C':
                base_url = "https://ipaas-scadev.sec.samsung.net/sec/kr/DigitalPlatform_KOREA_KDP_PROD_STK/1.0/723"
            elif self.site_cd == 'FN':
                base_url = "https://ipaas-scadev.sec.samsung.net/sec/kr/DigitalPlatform_KOREA_KDP_FNET_PROD_STK/1.0/815"
        elif self.opType.upper() in ["PROD", "PRD"]:
            if self.site_cd == 'B2C':
                base_url = "https://ipaas-sca.sec.samsung.net/sec/kr/DigitalPlatform_KOREA_KDP_PROD_STK/1.0/723"
            elif self.site_cd == 'FN':
                base_url = "https://ipaas-sca.sec.samsung.net/sec/kr/DigitalPlatform_KOREA_KDP_FNET_PROD_STK/1.0/815"
        
        headers = {
                        'Authorization': f'Bearer {token}',
                        'Content-Type': 'application/json',
                        'kdp-api-clientId': os.getenv("KDP_CLIENT_ID"),
                        'kdp-api-ifId': '710'
                    }
        total_df = pd.DataFrame()
        
        async with aiohttp.ClientSession() as session:
            tasks = [self._getGoodsStockData(session, base_url, headers,  sku) for sku in sku_list]
            results = await asyncio.gather(*tasks)
        
        for result in results:
            total_df = pd.concat([total_df, result], ignore_index=True)
        
        return total_df
    
    async def _getGoodsStockData(self, session, base_url, headers, sku): 
        try:
            data = {
                'skuId': sku
            }
            # Use `json` instead of `data` for JSON payloads
            async with session.post(base_url, headers=headers, json=data) as response:
                if response.status == 200:
                    response_json = await response.json()
                    return await self._getFormattedStockData(sku, response_json)
                else:
                    return pd.DataFrame()
        except Exception as e:
            return pd.DataFrame()

        
    async def _getFormattedStockData(self, model, response_json):
        try:
            payload = response_json.get("payload",{})
            goodsstk = payload.get("goods", {})
            response_custom =     {
                "model_code": model,
                "stkQty" : goodsstk.get("stkQty", None),
                "goodsId" : goodsstk.get("goodsId", None),
                "saleStatCd" : goodsstk.get("saleStatCd", None)
            }
            if response_custom["stkQty"] is None and response_custom["goodsId"] is None and response_custom["saleStatCd"] is None:
                return pd.DataFrame()
            return pd.DataFrame([response_custom])
        except Exception as e:
            return pd.DataFrame()
    
if __name__ == "__main__":
    stockChecker = KR_GoodsStock('KR', 'FN')
    print(asyncio.run(stockChecker.getGoodsStock(['SM-S938NZKAKOO', 'SM-S938NZKAKzz'])))
    