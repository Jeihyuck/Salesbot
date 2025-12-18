import sys
sys.path.append("/www/alpha")
from apps.rubicon_v3.__external_api.__apiRequest import apiHandler
import pandas as pd
import asyncio
import aiohttp
import os

class PriceChecker():

    def __init__(self, country, channel=None):
        self.country = country
        self.apiRequester = apiHandler(self.country, channel)
        self.opType = self.apiRequester.opType

    async def _getGoodsPriceData(self, session, base_url, headers, model, guid): 
        try:
            data = {
                'goodsId': model,
                'guid': guid #'nwrijtt80g'
                #'guid': encrypted_guid
            }
            async with session.post(base_url, headers=headers, json=data) as response:
                if response.status == 200:
                    response_json = await response.json()
                    return await self._getFormattedPriceData(response_json)
                else:
                    # Log the error if the status is not 200
                    #print(f"Error: {response.status}, Response: {await response.text()}")
                    return pd.DataFrame()
        except Exception as e:
            return pd.DataFrame()
        
    async def _getFormattedPriceData(self, response_json):
        try:
            response_data = response_json['payload']['goods']
            keys_to_extract = ['goodsId', 'mdlCode', 'salePrc1', 'salePrc2', 'salePrc3', 'totalPrice', 'appTotalPrice']
            final_response = {key: response_data[key] for key in keys_to_extract if key in response_data}
            return pd.DataFrame([final_response])
        except Exception as e:
            return pd.DataFrame()
        
    async def callPriceApi(self, guid, model_list):
        param = {}
        #try:
        if (self.country == 'KR'):
            if self.opType.upper() in ["DEV", "STG"]:
                base_url = 'https://ipaas-scadev.sec.samsung.net/sec/kr/DigitalPlatform_KOREA_KDP_PROD_PRC/1.0/722'
            elif self.opType.upper() in ["PROD", "PRD"]:
                base_url = 'https://ipaas-sca.sec.samsung.net/sec/kr/DigitalPlatform_KOREA_KDP_PROD_PRC/1.0/722'
            if guid == '' or guid == None:
                #guid = 'nwrijtt80g'
                return pd.DataFrame()
            token = await self.apiRequester.get_siis_token()
            headers = {
                    'Authorization': f'Bearer {token}',
                    'Content-Type': 'application/json',
                    'kdp-api-clientId': os.environ.get("KDP_CLIENT_ID"),
                    'kdp-api-ifId': '710'
                }
            total_df = pd.DataFrame()

            async with aiohttp.ClientSession() as session:
                tasks = [self._getGoodsPriceData(session, base_url, headers, goods_id, guid) for goods_id in model_list]
                results = await asyncio.gather(*tasks)
            
            for result in results:
                total_df = pd.concat([total_df, result], ignore_index=True)
            
            return total_df
        elif (self.country in ['UK', 'GB']):
            if self.opType.upper() in ["DEV", "STG"]:
                url = f'https://ipaas-scadev.sec.samsung.net/sec/kr/hybris_smn4_getproduct/1.0/uk/products'
            elif self.opType.upper() in ["PROD", "PRD"]:
                url = f'https://ipaas-sca.sec.samsung.net/sec/kr/hybris_smn4_getproduct/1.0/uk/products'
            else:
                url = ''              
            data = {
            }
            batch_size = 100
            result_df = pd.DataFrame()
            for i in range(0, len(model_list), batch_size):
                token = await self.apiRequester.get_siis_token()
                headers = {
                'Authorization': f'Bearer {token}',
                }
                batch = model_list[i:i+batch_size]
                product_codes_str = ",".join(batch)
                param['productCodes'] = product_codes_str
                response = await self.apiRequester.call_api('get', url, headers, param, data)
                response_data = response.json()
                for i in range(len(response_data)):
                    try:
                        single_data = response_data[i]
                        keys_to_extract = ['code', 'price', 'promotionPrice', 'salesStatus']
                        final_response = {key: single_data[key] for key in keys_to_extract if key in single_data}
                        flattened_data = {
                        'model_code': batch[i],
                        'price': final_response.get('price', {}).get('value') if type(final_response.get('price', {}).get('value')) is not type(None) else None,
                        'promotion_price': float((final_response.get('promotionPrice', {}).get('formattedValue')[1:]).replace(",", "")) if type(final_response.get('promotionPrice', {}).get('formattedValue')) is not type(None) else None,
                        'salesstatus': final_response.get('salesStatus', None)
                        }
                        single_df = pd.DataFrame([flattened_data])
                        result_df = pd.concat([result_df, single_df], axis=0)
                    except Exception as e:
                        pass
            result_df = result_df[result_df['salesstatus']=='PURCHASABLE'].reset_index(drop=True)       
            return result_df
        else:
            return pd.DataFrame()
        #except Exception as e:
            #return pd.DataFrame()
    
if __name__ == '__main__':
    priceChecker = PriceChecker('KR')
    result = asyncio.run(priceChecker.callPriceApi('9n0umijbja', ['G000386018', 'G0003dddd8601']))
    print(result)
    #priceChecker = PriceChecker('uk')
    #result = asyncio.run(priceChecker.callPriceApi('', ['SM-R630NZWAEUA'])) #, 'MUF-64BE3/EU', 'QE85QN93DATXXU', 'MS32DG4504ATE3', 'EF-BX110TBEGWW', 'EP-OL300BBEGWW', 'SM-S928BZTGEUB', 'SM-S931BLBGEUB', 'SM-A155FZYDEUB', 'SM-X110NZAEEUB']))
    #print(result)
