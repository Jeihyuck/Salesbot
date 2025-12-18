import sys
sys.path.append("/www/alpha")
from apps.rubicon_v3.__external_api.__apiRequest import apiHandler
import pandas as pd
from enum import Enum
import asyncio
import json
class ProductRecommend():

    def __init__(self, country, channel=None):
        self.apiRequester = apiHandler(country, channel)
        self.VITE_OP_TYPE = self.apiRequester.opType
        self.country = country

    async def getRecommendedProduct(self, modelCode):
        token = await self.apiRequester.get_siis_token()
        param = {}	
        try:
            if (self.country == 'KR'):
                country_code = 'sec'
                if self.VITE_OP_TYPE.upper() in ['DEV', 'STG']:
                    url = 'https://ipaas-scadev.sec.samsung.net/sec/kr/ap_brs_recommendation/1.0/recommendation'
                elif self.VITE_OP_TYPE.upper() in ['PRD', 'PROD']:
                    url = 'https://ipaas-sca.sec.samsung.net/sec/kr/ap_brs_recommendation/1.0/recommendation'
                else:
                    url = ''
            elif (self.country in ['UK', 'GB']):
                country_code = 'uk'
                if self.VITE_OP_TYPE.upper() in ['DEV', 'STG']:
                    url = f'https://ipaas-scadev.sec.samsung.net/sec/kr/eu_brs_recommendation/1.0/recommendation'
                elif self.VITE_OP_TYPE.upper() in ['PRD', 'PROD']:
                    url = f'https://ipaas-sca.sec.samsung.net/sec/kr/eu_brs_recommendation/1.0/recommendation'
                else:
                    url = ''
            else:
                return []
                
            headers = {
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json',
                'requestId': 'rubicon_test',
                'country': country_code,
                'product-info': 'false',
                'num': '10',
            }
            modelCodeToList = modelCode if isinstance(modelCode, list) else [modelCode]
            data = {
                'pageType': 'chatbot',
                'logicType': 'frequently_replaced_product',
                'modelList': modelCodeToList
            }
            
            response = await self.apiRequester.call_api('post', url, headers, param, data)
            response_text = response.text
            if len(response_text) > 0:
                result_json = json.loads(response_text).get('recommendations', [])
                return result_json
            else:
                return []
        except Exception as e:
            return []
    
if __name__ == '__main__':
    recommender = ProductRecommend('KR')
    result = asyncio.run(recommender.getRecommendedProduct('SM-S928NLBEKOO'))
    print(result)


    # top_selling sample
    #result = recommender.getRecommendedProduct('kr', 'top_selling', None, None, None, None, None) 

    # bought_together_product; SM-S928NLBEKOO, SM-F956NAKAPMS
    #result = recommender.getRecommendedProduct('kr', 'bought_together_product', ['SM-F956NAKAPMS'], None, None, None, None) 

    # bought_together_accessory; SM-S928NLBEKOO, SM-F956NAKAPMS
    #result = recommender.getRecommendedProduct('kr', 'bought_together_accessory', ['SM-F956NAKAPMS'], None, None, None, None) 

    ## demo_popular; every combinations
    #result = asyncio.run(recommender.getRecommendedProduct('demo_popular_in_category', None, ['Dryers'], '40s', 'M', None, None, None))
    #print(result)
    # similar_product; SM-S928NLBEKOO
    #result = recommender.getRecommendedProduct('kr', 'similar_product', ['SM-S928NLBEKOO'], None, None, None, None)

    # product_with_price_in_category;
    #result = recommender.getRecommendedProduct('kr', 'product_with_price_in_category', None, [recommender.Category.REFRIGERATORS.value], None, None, 3000000)

    #result  = asyncio.run(recommender.getRecommendedProduct('guid_based_recommendation', None, None, None, None, None, None, 'lrlvshvf7h'))
    #print(result)