import redis
import dill
import pickle
from alpha.settings import LOCATION, VITE_OP_TYPE, REDIS_TIMEOUT
from clickhouse_driver import connect
# from django.core.cache import cache
from datetime import datetime
from django_redis import get_redis_connection

REDIS_MAIN_IP = "127.0.0.1"

""" REDIS DB Numbers
        REDIS_CACHE, DJANGO_REDIS_QUEUE             : 0
        SCHEDULER_REDIS_QUEUE                       : 1
        MONITOR_REDIS_QUEUE                         : 2
        FILE_STORAGE                                : 3
        DATA_OBJECT                                 : 4
        JOB_STATUS_BOARD                            : 5
        PYTHON_FUNCTION                             : 6
        RUBICON_ORCHESTRATOR                        : 7
"""


def flushRedisCache(cache_name):
    get_redis_connection(cache_name).flushall()

def connectRQRedis():
    r = redis.StrictRedis(host=REDIS_MAIN_IP, port=6379, db=1)
    return r

def connectRedisFileStore():
    r = redis.StrictRedis(host=REDIS_MAIN_IP, port=6379, db=3)
    return r

def putRequestFileToRedis(file_id, n, file_data, file_extension):
    r = connectRedisFileStore()  
    redis_key = file_id + ':RequestFile:' + str(n) + ':' + file_extension
    r.setex(redis_key, REDIS_TIMEOUT, file_data)

def saveResultFileToRedis(file_path):
    r = connectRedisFileStore()
    redis_key = file_path
    
    with open(file_path, "rb") as fr:
	    file_data = fr.read()

    r.setex(redis_key, REDIS_TIMEOUT, file_data)
    return redis_key




########################################################################################################
r_data_object_board = redis.StrictRedis(host=REDIS_MAIN_IP, port=6379, db=4)
def setDataObjectToRedis(data_uuid, data):
    r_data_object_board.setex(data_uuid, REDIS_TIMEOUT, pickle.dumps(data))

def getDataObjectFromRedis(data_uuid):
    # r = redis.StrictRedis(host=REDIS_MAIN_IP, port=6379, db=4)
    pickle_data = r_data_object_board.get(data_uuid)
    data = pickle.loads(pickle_data)
    return data


########################################################################################################
r_function_object_board = redis.StrictRedis(host=REDIS_MAIN_IP, port=6379, db=6)
def setFunctionToRedis(redis_key, function_object):
    # r = redis.StrictRedis(host=REDIS_MAIN_IP, port=6379, db=6)
    r_function_object_board.set(redis_key, dill.dumps(function_object))

def getFunctionFromRedis(redis_key):
    # r = redis.StrictRedis(host=REDIS_MAIN_IP, port=6379, db=6)
    dill_data = r_function_object_board.get(redis_key)
    function_object = dill.loads(dill_data)
    return function_object