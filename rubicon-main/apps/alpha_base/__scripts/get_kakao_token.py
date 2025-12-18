import sys
sys.path.append("/www/alpha")
import json
import requests
from icecream import ic
# from rest_framework.decorators import api_view, permission_classes
# from django.shortcuts import render, redirect

# from rest_framework.views import APIView
# from rest_framework.response import Response
# from rest_framework.permissions import AllowAny

from alpha.settings import SOCIAL_OUTH_CONFIG

def kakaoLogin():
    client_id = SOCIAL_OUTH_CONFIG['KAKAO_REST_API_KEY']
    redirect_uri = SOCIAL_OUTH_CONFIG['KAKAO_REDIRECT_URI']
    url = "https://kauth.kakao.com/oauth/authorize?response_type=code&client_id={0}&redirect_uri={1}&response_type=code&scope=talk_message,friends".format(client_id, redirect_uri)
    response = requests.get(url)
    # ic(response.__dict__)
    tokenJson = response.json()

    ic(tokenJson['access_token'])
    ic(tokenJson['refresh_token'])

if __name__ == "__main__":
	kakaoLogin()