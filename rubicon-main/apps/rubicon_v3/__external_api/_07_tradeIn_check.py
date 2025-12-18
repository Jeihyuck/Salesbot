import aiohttp
import pandas as pd
import asyncio
from sqlalchemy import create_engine, MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import sys
sys.path.append("/www/alpha")
from apps.rubicon_v3.__external_api.__apiRequest import apiHandler

class MSARequest:

    def __init__(self, country, channel=None):
        self.country = country
        self.apiRequester = apiHandler(self.country, channel)
        self.opType = self.apiRequester.opType

    async def callTradeIn(self, model_list):
        token = await self.apiRequester.get_siis_token()
        if self.country in ['UK', 'GB']:
            if self.opType.upper() in ["DEV", "STG"]:
                base_url = f"https://ipaas-scadev.sec.samsung.net/sec/kr/d2c_msa_eu_exchange/1.0/gbr/trade-in/sku-devices/uk/"
            elif self.opType.upper() in ["PROD", "PRD"]:
                base_url = f"https://ipaas-sca.sec.samsung.net/sec/kr/d2c_msa_eu_exchange/1.0/gbr/trade-in/sku-devices/uk/"
        else:
            base_url = ''
        
        headers = {'Authorization': f'Bearer {token}'}
        total_df = pd.DataFrame()

        async with aiohttp.ClientSession() as session:
            tasks = [self.get_model_data(session, base_url, headers, model) for model in model_list]
            results = await asyncio.gather(*tasks)
        
        for result in results:
            total_df = pd.concat([total_df, result], ignore_index=True)
        
        return total_df

    async def get_model_data(self, session, base_url, headers, model):
        param = {}
        data = {}
        try:
            async with session.get(base_url + model, headers=headers, params=param, data=data) as response:
                if response.status == 200:
                    response_json = await response.json()
                    return await self.getFormattedData(model, response_json)
                else:
                    return pd.DataFrame()
        except Exception as e:
            return pd.DataFrame()

    async def getFormattedData(self, model, response_json):
        result_df = pd.DataFrame()
        try:
            for item in response_json:
                estimated_discount = item.get("estimated_discount", {})
                total_amount = estimated_discount.get("total", {}).get("amount", 0)
                result_df = pd.concat([result_df, pd.DataFrame([{"overall_total": total_amount, "buying_model_code": model}])], axis=0)
            return result_df
        except Exception as e:
            return pd.DataFrame()
        
    async def doSum(self, trade_df):
        if not trade_df.empty:
            trade_df = trade_df[trade_df["overall_total"] != 0]
            if not trade_df.empty:
                grouped_df = trade_df.groupby("buying_model_code").agg(
                    discount_min=pd.NamedAgg(column="overall_total", aggfunc="min"),
                    discount_max=pd.NamedAgg(column="overall_total", aggfunc="max")
                ).reset_index()
                
                grouped_df = grouped_df.rename(columns={"buying_model_code": "Model Code"})
                grouped_df["discount_min"] = grouped_df["discount_min"].astype(str) + " GBP"
                grouped_df["discount_max"] = grouped_df["discount_max"].astype(str) + " GBP"
        
                return grouped_df

        return pd.DataFrame()

if __name__ == "__main__":
    msaRequest = MSARequest('uk')
    model_list = ['SM-A266BZKCEUB', 'SM-A356BLVGEUB', 'SM-A356BZKBEUB']
    import time
    start = time.time()
    result = asyncio.run(msaRequest.callTradeIn(model_list))
    result2 = asyncio.run(msaRequest.doSum(result))
    print(result2)
    print(time.time() - start)