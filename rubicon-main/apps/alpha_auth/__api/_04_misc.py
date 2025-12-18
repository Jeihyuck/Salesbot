# import json
# import asyncio

from alpha import __log
from django.contrib import auth
# from icecream import ic

from django.core.cache import cache
# # from django.db.models import F, Q
# from django.core.paginator import Paginator
# from django.db import connection, transaction

# from apps.alpha_auth.models import Alpha_Department
# from alpha.settings import VITE_OP_TYPE
from apps.alpha_auth.models import Alpha_User
from apps.alpha_auth.__function._01_azure_email_mfa import make_mfa_code
from apps.__common.aes import decrypt, salt_generator




def get_one_time_salt(request_dict):
    """
    One Time Salt generator.
    """
    __log.debug(request_dict)
    try:
        username = request_dict['query']['username']
        salt = salt_generator()
        print(salt)

        cache_key = f"salt_{username}"
        cache.set(cache_key, salt, timeout=2)  # Store for 2 seconds
        return_date = {'one_time_salt': salt}
        return False, return_date, None, None
    except Exception as e:
        return False, None, None, {'type': 'error', 'title': 'Error', 'text' : 'System has an error. Check to your admin.'}

def mfa(request_dict):
    """
    MFA (Multi-Factor Authentication) handler.
    """
    # __log.debug(request_dict)
    try:
        username = request_dict['query']['username']
        encrypted_password = request_dict['query']['password']
        password = str(decrypt(encrypted_password))
        # __log.debug(f"Username: {username}, Salted_Password: {password}")
        salt_cache_key = f"salt_{username}"
        salt = cache.get(salt_cache_key)
        if salt:
            password = password.replace(salt, '')
            cache.delete(salt_cache_key)
        __log.debug(f"Username: {username}, Password: {password}")
        auth_user = None
        user_exists = Alpha_User.objects.filter(username=username).exists()
        if user_exists:
            user = Alpha_User.objects.filter(username=username)[0]
            # __log.debug(user)
            str_password = str(password)
            auth_user = auth.authenticate(username=username, password=str_password)
            # __log.debug('-------------------')
            # __log.debug(auth_user)

            if auth_user != None:
                __log.debug('Make MFA Code')
                make_mfa_code(username)
                return True, None, None, {'type': 'success', 'title': 'Success', 'text' : 'MFA has sent to your E-Mail Address. Valid during 5 minutees. Please check your inbox.'}
            else:
                return False, None, None, {'type': 'error', 'title': 'Error', 'text' : 'User not found or password is incorrect.'}
        else:
            return False, None, None, {'type': 'error', 'title': 'Error', 'text' : 'User not found or password is incorrect.'}
    except Exception as e:
        return False, None, None, {'type': 'error', 'title': 'Error', 'text' : 'System has an error. Check to your admin.'}
    
