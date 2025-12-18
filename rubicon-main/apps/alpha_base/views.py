import traceback
from django.shortcuts import render

from alpha.settings import API_URL_PREFIX, FRONTEND_DEV_URL

from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_api_key.permissions import HasAPIKey

from icecream import ic
from django.http import JsonResponse, HttpResponse

from alpha.settings import DEBUG, bcolors, VITE_OP_TYPE

from apps.__common import alpha

from apps.__protobuf.alpha_grpc_stub import grpc_stub_function
from apps.alpha_base.__api import  _01_menu,  _02_table, _03_api, _04_code, _11_channels, _31_util

import alpha._db as DB
from alpha.__log import info, debug
import alpha._redis as REDIS


# from apps.alpha_service.scheduler import *

class channel(APIView):
    permission_classes = [HasAPIKey|IsAuthenticated]
    def post(self, request):
        return alpha.stdResponse(request, _11_channels, logging_level='none')





# def kakaoMessageView(request):
#     return render(request, 'base/kakao_message_view.html', {
#         'api_url_prefix': API_URL_PREFIX,
#         'frontend_dev_url': FRONTEND_DEV_URL
#     })


class util(APIView):
    permission_classes = [AllowAny]
    def post(self, request):
        return alpha.stdResponse(request, _31_util, show_request=False, logging_level='none')

class menu(APIView):
    permission_classes = [IsAuthenticated] if VITE_OP_TYPE == 'PROD' else [AllowAny]
    def post(self, request):
        return alpha.stdResponse(request, _01_menu, show_request=False, logging_level='none')

class table(APIView):
    permission_classes = [IsAuthenticated] if VITE_OP_TYPE == 'PROD' else [AllowAny]
    def post(self, request):
        return alpha.stdResponse(request, _02_table, show_request=False, logging_level='none')

class api(APIView):
    permission_classes = [IsAuthenticated] if VITE_OP_TYPE == 'PROD' else [AllowAny]
    def post(self, request):
        return alpha.stdResponse(request, _03_api, show_request=False, logging_level='none')

class code(APIView):
    permission_classes = [IsAuthenticated] if VITE_OP_TYPE == 'PROD' else [AllowAny]
    def post(self, request):
        return alpha.stdResponse(request, _04_code, show_request=False, logging_level='none')

class grpc(APIView):
    permission_classes = [AllowAny]
    def post(self, request, gpu_server, function):
        print(bcolors.BLUE + 'GPRC_SERVER: ' + gpu_server + ', FUNCTION: ' + function + bcolors.ENDC)
        try:
            query_dict = alpha.standardPostRequestCheck(request)
            if DEBUG == True:
                info(query_dict)
            grpc_response = grpc_stub_function(gpu_server, function, query_dict['action'], query_dict['query'])
            return JsonResponse(grpc_response, safe=False)
        except Exception as e:
            if DEBUG == True: print(bcolors.FAIL + str(traceback.format_exc()) + bcolors.ENDC)
            return JsonResponse({'success': False, 'error': str(traceback.format_exc()).splitlines(), 'msg': str(e)}, safe=False)

class getFile(APIView):
    permission_classes = [AllowAny]
    def get(self, request, filename):

        r = REDIS.connectRedisFileStore()
        redis_key = '/tmp/'+ filename
        if r.exists(redis_key):
            file_data = r.get(redis_key)
        else:
            file_path = '/www/alpha/apps/alpha_base/__excel_download_template/' + filename
            with open(file_path, 'rb') as f:
                file_data = f.read()

        return HttpResponse(file_data, content_type='application/octet-stream')
