import sys, requests, time, httpx, os
import django

sys.path.append("/www/alpha/")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "alpha.settings")

from alpha.settings import VITE_OP_TYPE
from apps.rubicon_v3.__function import __django_cache as django_cache
from apps.rubicon_v3.__function.definitions import channels

class apiHandler:

    def __init__(self, country, channel=None):
        self.opType = VITE_OP_TYPE
        if channel in [channels.SMARTTHINGS]:
            self.opType = "PRD"
        (
            self.TOKEN_URL,
            self.CLIENT_ID,
            self.CLIENT_SECRET,
            self.USERNAME,
            self.PASSWORD,
        ) = ("", "", "", "", "")
        self.country = country
        self.django_cache_client = django_cache.DjangoCacheClient()
        self.api_key_code = django_cache.CacheKey.siis_api_key(self.country, self.opType)
        # self.django_cache_client.delete(self.api_key_code)
        self.cache_expiry = 60 * 60 * 24 * 1  # 1 day
        self.SIIS_TOKEN = None
        if self.country == "KR":
            #self.USERNAME = "sst5692def"
            self.USERNAME = os.environ.get("SIIS_USERNAME_KR")
            if self.opType.upper() in ["DEV", "STG"]:
                self.TOKEN_URL = (
                    "https://ipaas-scadev.sec.samsung.net/sec/kr/long/oauth2/token"
                )
                self.CLIENT_ID = os.environ.get("SIIS_CLIENT_ID_KR_STG")
                self.CLIENT_SECRET = os.environ.get("SIIS_CLIENT_SECRET_KR_STG")
                self.PASSWORD = os.environ.get("SIIS_PASSWORD_KR_STG")
            elif self.opType.upper() in ["PROD", "PRD"]:
                self.TOKEN_URL = (
                    "https://ipaas-sca.sec.samsung.net/sec/kr/long/oauth2/token"
                )
                self.CLIENT_ID = os.environ.get("SIIS_CLIENT_ID_KR_PRD")
                self.CLIENT_SECRET = os.environ.get("SIIS_CLIENT_SECRET_KR_PRD")
                self.PASSWORD = os.environ.get("SIIS_PASSWORD_KR_PRD")
        elif self.country in ["UK", "GB"]:
            self.USERNAME = os.environ.get("SIIS_USERNAME_GB")
            if self.opType.upper() in ["DEV", "STG"]:
                self.TOKEN_URL = (
                    "https://ipaas-scadev.sec.samsung.net/sec/kr/long/oauth2/token"
                )
                self.CLIENT_ID = os.environ.get("SIIS_CLIENT_ID_GB_STG")
                self.CLIENT_SECRET = os.environ.get("SIIS_CLIENT_SECRET_GB_STG")
                self.PASSWORD = os.environ.get("SIIS_PASSWORD_GB_STG")
            elif self.opType.upper() in ["PROD", "PRD"]:
                self.TOKEN_URL = (
                    "https://ipaas-sca.sec.samsung.net/sec/kr/long/oauth2/token"
                )
                self.CLIENT_ID = os.environ.get("SIIS_CLIENT_ID_GB_PRD")
                self.CLIENT_SECRET = os.environ.get("SIIS_CLIENT_SECRET_GB_PRD")
                self.PASSWORD = os.environ.get("SIIS_PASSWORD_GB_PRD")
        else:
            raise ValueError(f"Unsupported country: {self.country}")

    ##################################################################################################
    async def get_siis_token(self):
        try:
            full_token = self.django_cache_client.get(self.api_key_code)
            if full_token:
                if await self.is_access_token_expired(full_token):
                    self.SIIS_TOKEN = await self.refresh_siis_token(full_token)
                else:
                    self.SIIS_TOKEN = full_token["access_token"]
            else:
                self.SIIS_TOKEN = await self.get_siis_access_token()

            return self.SIIS_TOKEN
        except Exception as e:
            raise e

    async def get_siis_access_token(self):
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.TOKEN_URL,
                    auth=(self.CLIENT_ID, self.CLIENT_SECRET),
                    data={
                        "username": self.USERNAME,
                        "password": self.PASSWORD,
                        "grant_type": "password",
                    },
                )

                if response.status_code == 200:
                    self.django_cache_client.store(
                        self.api_key_code, response.json(), self.cache_expiry
                    )
                    self.SIIS_TOKEN = response.json()["access_token"]
                    return self.SIIS_TOKEN
                else:
                    return None
        except Exception as e:
            raise e

    async def refresh_siis_token(self, token_info: dict):
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.TOKEN_URL,
                    auth=(self.CLIENT_ID, self.CLIENT_SECRET),
                    data={
                        "username": self.USERNAME,
                        "password": self.PASSWORD,
                        "grant_type": "refresh_token",
                        "refresh_token": token_info["refresh_token"],
                    },
                )

                if response.status_code == 200:
                    self.django_cache_client.update(
                        self.api_key_code, response.json(), self.cache_expiry
                    )
                    self.SIIS_TOKEN = response.json()["access_token"]
                    return self.SIIS_TOKEN
                else:
                    return None
        except Exception as e:
            raise e

    async def is_access_token_expired(self, token_info: dict):
        try:
            consented_on = token_info["consented_on"]
            expires_in = token_info["expires_in"]
            expiration_time = consented_on + expires_in
            current_time = int(time.time())
            return current_time >= expiration_time
        except Exception as e:
            raise e

    async def call_api(self, method, url, headers, param, data):
        if "get" in method:
            return requests.get(url=url, params=param, headers=headers, timeout=30)
        elif "post" in method:
            return requests.post(url=url, json=data, headers=headers, timeout=30)

    ##################################################################################################
    def get_siis_token_sync(self):
        try:
            full_token = self.django_cache_client.get(self.api_key_code)
            if full_token:
                if self.is_access_token_expired_sync(full_token):
                    self.SIIS_TOKEN = self.refresh_siis_token_sync(full_token)
                else:
                    self.SIIS_TOKEN = full_token["access_token"]
            else:
                self.SIIS_TOKEN = self.get_siis_access_token_sync()

            return self.SIIS_TOKEN
        except Exception as e:
            raise e

    def get_siis_access_token_sync(self):
        try:
            with httpx.Client() as client:
                response = client.post(
                    self.TOKEN_URL,
                    auth=(self.CLIENT_ID, self.CLIENT_SECRET),
                    data={
                        "username": self.USERNAME,
                        "password": self.PASSWORD,
                        "grant_type": "password",
                    },
                )

                if response.status_code == 200:
                    self.django_cache_client.store(
                        self.api_key_code, response.json(), self.cache_expiry
                    )
                    self.SIIS_TOKEN = response.json()["access_token"]
                    return self.SIIS_TOKEN
                else:
                    return None
        except Exception as e:
            raise e

    def refresh_siis_token_sync(self, token_info: dict):
        try:
            with httpx.Client() as client:
                response = client.post(
                    self.TOKEN_URL,
                    auth=(self.CLIENT_ID, self.CLIENT_SECRET),
                    data={
                        "username": self.USERNAME,
                        "password": self.PASSWORD,
                        "grant_type": "refresh_token",
                        "refresh_token": token_info["refresh_token"],
                    },
                )

                if response.status_code == 200:
                    self.django_cache_client.update(
                        self.api_key_code, response.json(), self.cache_expiry
                    )
                    self.SIIS_TOKEN = response.json()["access_token"]
                    return self.SIIS_TOKEN
                else:
                    return None
        except Exception as e:
            raise e

    def is_access_token_expired_sync(self, token_info: dict):
        try:
            consented_on = token_info["consented_on"]
            expires_in = token_info["expires_in"]
            expiration_time = consented_on + expires_in
            current_time = int(time.time())
            return current_time >= expiration_time
        except Exception as e:
            raise e

if __name__ == '__main__':
    django.setup()
    api_handler = apiHandler("KR")
    token = api_handler.get_siis_token_sync()
    print(token)