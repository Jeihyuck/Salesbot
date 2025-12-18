import json
import traceback
import django_rq

from uuid import UUID
from django.http import JsonResponse

from alpha.__log import debug, error, info
from alpha.settings import DEBUG, bcolors, BASE_URL, API_URL_PREFIX
# from apps.alpha_auth.__function import checkAPIPermission
from apps.alpha_log.__function import APILogging
from icecream import ic

def value_extractor(value_list):
    return_list = []
    for item in value_list:
        # print(item['value'])
        return_list.append(item['value'])
    return return_list

def sanitizeQuery(query):
    delete_key_list = []
    for key, value in query.items():
        if isinstance(value, list):
            while('' in value):
                value.remove('')
            if value == []:
                delete_key_list.append(key)
        else:
            if value == '' or None:
                delete_key_list.append(key)

    return_query = { key:query[key] for key in query if key not in delete_key_list }
    return return_query

class UUIDEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, UUID):
            return obj.hex
        return json.JSONEncoder.default(self, obj)

def stdResponse(request, api, show_request=False, show_response=False, cache=False, json=False, logging_level='none'):
    request_dict = standardPostRequestCheck(request, cache)
    # debug(request_dict)
    if DEBUG == True and show_request == True:
        print(bcolors.BLUE + str(api.__file__) + ' : ' + request_dict['action'] + bcolors.ENDC)
        debug(request_dict)
    try:
        # ic(request_dict['user'])
        # if checkAPIPermission(request_dict['user']['username'], request_dict['request']):
        permission_check = True
        if permission_check:
            func = getattr(api, request_dict['action'])
            # try:
            success, data, meta, msg = func(request_dict)
            # except:
            #     success = False
            #     data = None
            #     meta = None
            #     msg = str(traceback.format_exc()).splitlines()
            #     
            # Convert python objects to string
            # datetime : "YYYY-MM-DD HH:MM:SS"
            try:
                if data != None:
                    for item in data:
                        if item != None:
                            if 'created_on' in item:
                                if item['created_on'] != None:
                                    item['created_on'] = item['created_on'].strftime('%Y-%m-%d %H:%M:%S')
                            if 'updated_on' in item:
                                if item['updated_on'] != None:
                                    item['updated_on'] = item['updated_on'].strftime('%Y-%m-%d %H:%M:%S')
            except Exception as e:
                pass

            if DEBUG == True and show_response == True:
                debug('Return ---------------------')
                debug(data)
                debug(meta)

            if logging_level == 'full':
                django_rq.enqueue(APILogging,
                    request_dict['user']['username'],
                    request.build_absolute_uri().replace(BASE_URL, ''),
                    request_dict['action'], request_dict['query'], True, 
                    json.loads(json.dumps({'success': success, 'data': data, 'meta': meta, 'msg': msg}, cls=UUIDEncoder)))
            if logging_level == 'simple':
                django_rq.enqueue(APILogging,
                    request_dict['user']['username'],
                    request.build_absolute_uri().replace(BASE_URL, ''),
                    request_dict['action'], None, True, None
                )

            return JsonResponse({'success': success, 'data': data, 'meta': meta, 'msg': msg}, safe=False)

        else:
            if logging_level in ['full', 'simple']:
                django_rq.enqueue(APILogging,
                    request_dict['user']['username'],
                    request.build_absolute_uri().replace(BASE_URL, ''),
                    request_dict['action'], request_dict['query'], True,
                    json.loads(json.dumps({'success': False, 'msg': 'Service API Permission Denied'}, cls=UUIDEncoder))
                )
            error({'request': request_dict, 'success': False, 'msg': 'Service API Permission Denied'})
            return JsonResponse({'success': False, 'msg': 'Service API Permission Denied'}, safe=False)
    except Exception as e:
        print(bcolors.RED + '-------------------------- Check if return is composed of \"data\" & \"meta\" & \"msg\" -------------------------' + bcolors.ENDC)
        try:
            if logging_level in ['full', 'simple']:
                django_rq.enqueue(APILogging,
                    request_dict['user']['username'],
                    request.build_absolute_uri().replace(BASE_URL, ''),
                    request_dict['action'], request_dict['query'], False,
                    {'success': False, 'error': str(traceback.format_exc()).splitlines(), 'msg': str(e)}
                )
        except Exception as e:
            pass
        error(traceback.format_exc())
        return JsonResponse({'success': False, 'error': 'Internal Server Error', 'msg': str(e)}, safe=False)

def standardPostRequestCheck(request, cache=False, json_type=False):
    if cache: request_hash_string = request.data['action'] # request hash for cache
    request_dict = {}
    request_dict['request'] = { 'url' : request._request.path.replace(API_URL_PREFIX, ''), 'method' : request._request.method }
    # ic('request.data', str(request.data['user']))
    # try:
        # if 'user' not in request_dict:
        #     request_dict['user'] = { 'username' : request.user.username, 'email' : request.user.email }
    try:
        request_dict['user'] = { 'username' : request.user.username, 'email' : request.user.email }
    except Exception as e:
        request_dict['user'] = { 'username' : 'anonymous', 'email' : '-' }
    # except:
    #     pass

    request_dict['files'] = []
    # try:
    #     file_count = int(request.data['fileCount'])
    # except:
    #     file_count = 0

    for key in request.data:
        if key == 'query':
            if not isinstance(request.data['query'], dict):
                request_dict['query'] = json.loads(request.data['query'])
            else:
                request_dict['query'] = request.data['query']

            request_dict['query'] = sanitizeQuery(request_dict['query'])
            if cache: request_hash_string = request_hash_string + str(request_dict['query'])
        elif key == 'user':
            if not isinstance(request.data['user'], dict):
                request_dict['user'] = json.loads(request.data['user'])
        elif key  == 'paging':
            request_dict['paging'] = json.loads(request.data['paging'])
        elif key[:4] == 'file':
            pass
        else:
            request_dict[key] = request.data[key]

    files = request.FILES.getlist('files')
    # ic(files)
    # if file_count > 0:
    for index, file in enumerate(files):
        # ic(file.name)
        file_dict = {}
        file_dict['name'] = file.name
        file_dict['size'] = file.size
        file_dict['file'] = file.read()
        request_dict['files'].append(file_dict)
        if cache: request_hash_string = request_hash_string + str(file_dict['name'])

    if 'paging' in request_dict:
        if 'fullLoad' in request_dict['paging'] and request_dict['paging']['fullLoad'] == False:
        # if request_dict['paging']['fullLoad'] == False:
            # if 'page' in request_dict['paging']:
            request_dict['paging']['skip'] = (request_dict['paging']['page'] - 1) * request_dict['paging']['itemsPerPage']
            if cache: request_hash_string = request_hash_string + str(request_dict['paging']['page']) + str(request_dict['paging']['skip'])
            # else:
        else:
            request_dict['paging']['page'] = 1
            request_dict['paging']['itemsPerPage'] = 10000
            request_dict['paging']['skip'] = 0
            if cache: request_hash_string = request_hash_string + str(request_dict['paging']['page']) + str(request_dict['paging']['skip'])
        # else:
            
            
    if cache: request_dict['request']['requestHash'] = 'REQUEST_HASH:' + str(hash(request_hash_string))
    # ic(request_dict)
    return request_dict
