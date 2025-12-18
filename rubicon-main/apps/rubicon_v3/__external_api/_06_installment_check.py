import sys
sys.path.append("/www/alpha")
from apps.rubicon_v3.__external_api.__apiRequest import apiHandler
import pandas as pd
import aiohttp

import asyncio

class InstallmentChecker():

    def __init__(self, country, channel=None):
        self.country = country
        self.apiRequester = apiHandler(self.country, channel)
        self.opType = self.apiRequester.opType

    async def callInstallmentApi(self, model_list):
        token = await self.apiRequester.get_siis_token()
        if self.country in ['UK', 'GB']:
            if self.opType.upper() in ["DEV", "STG"]:
                base_url = f"https://ipaas-scadev.sec.samsung.net/sec/kr/hybris_smn4_getinstallmentresponse/1.0/uk/products/"
            elif self.opType.upper() in ["PROD", "PRD"]:
                base_url = f"https://ipaas-sca.sec.samsung.net/sec/kr/hybris_smn4_getinstallmentresponse/1.0/uk/products/"
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
            async with session.get(base_url + model + '/calculateInstallment', headers=headers, params=param, data=data) as response:
                if response.status == 200:
                    response_json = await response.json()
                    return await self.getFormattedData(model, response_json)
                else:
                    return pd.DataFrame()
        except Exception as e:
            return pd.DataFrame()
        
        
    async def getFormattedData(self, model, response_json):
        result_list = []
        try:
            for payment_mode in response_json["values"]:
                code1 = payment_mode["code"]
                code_name = payment_mode["name"]
                for value in payment_mode["values"]:
                    record = {
                        "model_code": model,
                        "code1": code1,
                        "code_name": code_name,
                        "code2": int(value["code"]),
                        "commision": float(value.get("commission", 0.0)),
                        "currency": "GBR",  # 값에 따라 조정 가능
                        "downpayment": float(value.get("downPayment", 0.0)),
                        "interestrate": float(str(value.get("interestRate", "0")).replace("£", "")),
                        "originalprice": float(str(value["originalPrice"]).replace("£", "")),
                        "period": value["period"],
                        "periodvalue": float(str(value["periodicValue"]).replace("£", "")),
                        "purchasecost": float(str(value["purchaseCost"]).replace("£", "")),
                        "totalcost": float(str(value["totalCost"]).replace("£", "")),
                        "totalinterest": float(str(value["totalInterest"]).replace("£", "")),
                        "min_amount": float(str(value.get("minAmount", "0")).replace("£", ""))
                    }
                    result_list.append(record)
            df = pd.DataFrame(result_list)
            return df
        except Exception as e:
            return pd.DataFrame()   
    
if __name__ == '__main__':
    installmentChecker = InstallmentChecker('uk')
    result = asyncio.run(installmentChecker.callInstallmentApi(['SM-R630NZWAEUA','VG-SESB11K/XC','SM-R860NZKAEUA']))
    print(result)