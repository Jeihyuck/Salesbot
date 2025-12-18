import aiohttp
import pandas as pd
import asyncio
from sqlalchemy import create_engine, MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import sys
sys.path.append("/www/alpha")
from apps.rubicon_v3.__external_api.__apiRequest import apiHandler

## FROM KDP APIs
class UK_UserRecord:
    def __init__(self, country, sa_id, channel=None):
        self.country = country
        self.apiRequester = apiHandler(self.country, channel)
        self.opType = self.apiRequester.opType
        self.sa_id = sa_id

    async def getOrderLists(self):
        try:
            token = await self.apiRequester.get_siis_token()
            param = {}
            if self.country in ['UK', 'GB']:
                if self.opType.upper() in ["DEV", "STG"]:
                    base_url = f"https://ipaas-scadev.sec.samsung.net/sec/kr/hybris_smn4_userorderhistory/1.0/uk/users/current/orders"
                elif self.opType.upper() in ["PROD", "PRD"]:
                    base_url = f"https://ipaas-sca.sec.samsung.net/sec/kr/hybris_smn4_userorderhistory/1.0/uk/users/current/orders"
            else:
                base_url = ''
            headers = {
                        'Authorization': f'Bearer {token}',
                        'Content-Type': 'application/json',
                        'cookie': f'sa_id={self.sa_id}'
                    }
            data = {}
            response = await self.apiRequester.call_api('get', base_url, headers, param, data)
            print(response.json())
            #return pd.DataFrame(response.json().get("payload",{}).get("order_list", []))
        except Exception as e:
            return pd.DataFrame()

    async def getCarts(self):
        try:
            token = await self.apiRequester.get_siis_token()
            param = {}
            if self.country in ['UK', 'GB']:
                if self.opType.upper() in ["DEV", "STG"]:
                    base_url = f"https://ipaas-scadev.sec.samsung.net/sec/kr/hybris_smn4_getcarts/1.0/uk/users/current/carts"
                elif self.opType.upper() in ["PROD", "PRD"]:
                    base_url = f"https://ipaas-sca.sec.samsung.net/sec/kr/hybris_smn4_getcarts/1.0/uk/users/current/carts"
            else:
                base_url = ''
            headers = {
                        'Authorization': f'Bearer {token}',
                        'Content-Type': 'application/json',
                        'cookie': f'sa_id={self.sa_id}'
                    }
            data = {}
            response = await self.apiRequester.call_api('get', base_url, headers, param, data)
            cart_list = response.json().get("carts", [])[0].get("entries", [])
            result = []
            for cart in cart_list:
                product_data = {}
                product_data['code'] = cart.get('product', {}).get('code', '')
                product_data['rrpPrice'] = cart.get('product', {}).get('rrpPrice', {}).get('value', 0)
                product_data['saveValue'] = cart.get('product', {}).get('saveValue', {}).get('value', 0)
                product_data['salesStatus'] = cart.get('product', {}).get('salesStatus', '')
                product_data['stock'] = cart.get('product', {}).get('stock', {}).get('stockLevel', 0)
                product_data['quantity'] = cart.get('quantity', '')
                result.append(product_data)
            return pd.DataFrame(result)
        except Exception as e:
            return pd.DataFrame()

    async def getWishLists(self):
        try:
            token = await self.apiRequester.get_siis_token()
            if self.country in ['UK', 'GB']:
                if self.opType.upper() in ["DEV", "STG"]:
                    base_url = f"https://ipaas-scadev.sec.samsung.net/sec/kr/hybris_smn4_wishlist/1.0/uk/users/current/wishlist"
                elif self.opType.upper() in ["PROD", "PRD"]:
                    base_url = f"https://ipaas-sca.sec.samsung.net/sec/kr/hybris_smn4_wishlist/1.0/uk/users/current/wishlist"
            else:
                base_url = ''
            param = {
                'fields': 'FULL'
            }
            headers = {
                        'Authorization': f'Bearer {token}',
                        'Content-Type': 'application/json',
                        'cookie': f'sa_id={self.sa_id}',
                    }
            data = {}
            response = await self.apiRequester.call_api('get', base_url, headers, param, data)
            wish_list = response.json().get('wishlists', [])[0].get('entries', [])
            result = []
            for wish in wish_list:
                product_data = {}
                product_data['code'] = wish.get('product', {}).get('code', '')
                product_data['rrpPrice'] = wish.get('product', {}).get('rrpPrice', {}).get('value', 0)
                product_data['saveValue'] = wish.get('product', {}).get('saveValue', {}).get('value', 0)
                product_data['salesStatus'] = wish.get('product', {}).get('salesStatus', '')
                product_data['stock'] = wish.get('product', {}).get('stock', {}).get('stockLevel', 0)
                result.append(product_data)
            return pd.DataFrame(result)
        except Exception as e:
            return pd.DataFrame()
    
if __name__ == "__main__":
    infoObject = UK_UserRecord('UK', '6e711a081c37c81e79fc27efd09fc5dc8e29d8d3c8fe393cda45aa001db661e4f152b02af8baf9fe979ce4d8182cb5b72509d15740765d0319eddc627c3a93871410c118932eeafc642d9337f1b9d61aaace7dd55f7972044691fcd9052d129337d83e0ef51791f299ab6590eb6b82f983225c73fd9f28fbacbe569a0f56c5831925f60d201fb8bef4d19e1df0e1b53daa6cb6fb07ac383c328a73c09e8ad00fab5a58dc670586280a5e557d016093787b77f1a51ad3834a474224fec212fc311d289cdfc19ce84deca5b3478f1683f63d8685a1079d7233ebb8d4cfcf971778b05908dcb87cb3ad1807ae396d161d196df58093abe0523767b72614a2b36daa')
    print(asyncio.run(infoObject.getCarts()))
    print(asyncio.run(infoObject.getWishLists()))
    print(asyncio.run(infoObject.getOrderLists()))