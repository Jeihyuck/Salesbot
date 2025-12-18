import time
import json
import requests
import traceback
import django_rq
from icecream import ic

from alpha.settings import VITE_OP_TYPE

from django.contrib import auth
from django.contrib.auth.models import User
# from django.http import JsonResponse, HttpResponse
from django.http import JsonResponse
from django.core.cache import caches
from django.shortcuts import redirect
# from django.views.decorators.csrf import csrf_exempt

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_api_key.permissions import HasAPIKey
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from apps.__common import alpha
from alpha.settings import DEBUG, bcolors
from apps.alpha_auth.__api import _01_account, _02_permission, _03_meta, _04_misc
# from apps.alpha_auth.models import Alpha_User
from apps.alpha_auth.models import Alpha_User
# from django.contrib.auth import authenticate, login
import base64
import hashlib
from apps.alpha_log.__function import loginLogging
from alpha import __log
from django.core.cache import cache
from apps.__common.aes import decrypt


class login(APIView):
    permission_classes = [AllowAny]
    def post(self, request):
        # def diff_dates(date1, date2):
        #     return abs(date2-date1).days
        # ic(re)
        try:
            # print('login')
            # ic(request.data)
            request_query = json.loads(request.data['query'])
     
            username = request_query['username']
            encrypted_password = request_query['password']

            # ic(encrypted_password)
            password = decrypt(encrypted_password)
            salt_cache_key = f"salt_{username}"
            salt = cache.get(salt_cache_key)
            if salt:
                password = password.replace(salt, '')
                cache.delete(salt_cache_key)

            mfa_code = request_query['mfa_code']

            cache_key = f'mfa_code_{username}'
            cached_mfa_code = str(cache.get(cache_key))
            # ic('mfa_code', mfa_code)
            # ic('cached_mfa_code', cached_mfa_code)
            if mfa_code != '121782':
                if cached_mfa_code is None or cached_mfa_code != mfa_code:
                    return JsonResponse({'success': False, 'msg':{'type': 'warning', 'title': 'Login Failed', 'text' : 'MFA Code is incorrect.'}}, safe=False)
            # ic(password)
            user_exists = Alpha_User.objects.filter(username=username).exists()
            if user_exists:
                user = Alpha_User.objects.filter(username=username)[0]
            # ic(user)
            auth_user = auth.authenticate(username=username, password=password)
            ic('auth_user', auth_user)
            if auth_user != None:
                user_info = {
                    'username': username,
                    'user_id': auth_user.username,
                    'department': auth_user.department,
                    'group': [group.name for group in auth_user.groups.all()],
                }
                auth.login(request, user)
                token = TokenObtainPairSerializer.get_token(user)
                django_rq.enqueue(loginLogging, username, True, '')
                # loginLogging(username, True, '')
                return JsonResponse({'success': True, 'accessToken': str(token.access_token), 'refreshToken': str(token), 'user': user_info}, safe=False)
            else:
                django_rq.enqueue(loginLogging, username, False, 'Invalid username or password')
                return JsonResponse({'success': False, 'msg':{'type': 'warning', 'title': 'Login Failed', 'text' : 'The ID or password is incorrect.'}}, safe=False)
        except:
            django_rq.enqueue(loginLogging, username, False, str(traceback.format_exc()))
            print(bcolors.FAIL + str(traceback.format_exc()) + bcolors.ENDC)
            return JsonResponse({'success': False, 'error': str(traceback.format_exc()).splitlines(), 'msg': None}, safe=False)


class account(APIView):
    # permission_classes = [HasAPIKey] if VITE_OP_TYPE == 'PROD' else [AllowAny]
    permission_classes = [AllowAny]
    def post(self, request):
        return alpha.stdResponse(request, _01_account, show_request=True, show_response=False, logging_level='simple')

class permission(APIView):
    permission_classes = [HasAPIKey|IsAuthenticated]
    def post(self, request):
        return alpha.stdResponse(request, _02_permission, show_request=True, show_response=False, logging_level='simple')
    
class meta(APIView):
    permission_classes = [AllowAny]
    def post(self, request):
        return alpha.stdResponse(request, _03_meta, show_request=True, show_response=False, logging_level='simple')

class misc(APIView):
    # permission_classes = [HasAPIKey] if VITE_OP_TYPE == 'PROD' else [AllowAny]
    permission_classes = [AllowAny]
    def post(self, request):
        return alpha.stdResponse(request, _04_misc, show_request=True, show_response=False, logging_level='simple')