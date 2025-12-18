import os
import json
import math
import uuid
import redis
import smtplib
import psycopg2
import requests
import codecs
import pickle
import hashlib
import traceback
from django.http import JsonResponse
# import sys
# sys.path.append('/www/alpha/')

from datetime import datetime
from icecream import ic

from rich.console import Console
console = Console()

# import alpha.__log as Log
# import alpha._db as AICC_DB
# from apps.__common.redis_setting import setDataObjectToRedis

from alpha.settings import VITE_API_SERVER_URL, API_URL_PREFIX, ALPHA_API_KEY, POSTGRESQL_ID, POSTGRESQL_PWD, POSTGRESQL_IP, POSTGRESQL_PORT




def getTodayString():
    today = datetime.today()
    today_string = today.strftime('%Y-%m-%d')
    return today_string

def datetimeToString(datetime):
    return datetime.strftime('%Y-%m-%d %H:%M:%S')

def convertDatetimeToStringOfResponse(data, key_list):
    for item in data:
        for key in key_list:
            item[key] = datetimeToString(item[key])
    return data

def stringToDatetime(string):
    return datetime.strptime(string, "%Y-%m-%d %H:%M:%S")

def stringToDate(string):
    return datetime.strptime(string, "%Y-%m-%d")

def getStandardedTimestamp(reference_date_string, date_string, time_type):
    if time_type == 'seconds':
        standarded_timestamp = int(datetime.datetime.strptime(date_string[:12], "%Y%m%d%H%M").timestamp()) - int(datetime.datetime.strptime(reference_date_string, "%Y%m%d%H%M").timestamp())
        return standarded_timestamp
    elif time_type == 'minutes':
        standarded_timestamp = int((datetime.datetime.strptime(date_string[:12], "%Y%m%d%H%M").timestamp() - datetime.datetime.strptime(reference_date_string, "%Y%m%d%H%M").timestamp()) / 60)
        return standarded_timestamp
    else:
        return 'not_supported'

def getTimestampFromStandardedTimestamp(reference_date_string, standarded_timestamp, time_type):
    if time_type == 'seconds':
        epoch_timestamp = standarded_timestamp + datetime.datetime.strptime(reference_date_string, "%Y%m%d%H%M").timestamp()
        date_time = datetime.datetime.fromtimestamp(epoch_timestamp)
        return date_time
    elif time_type == 'minutes':
        epoch_timestamp = (standarded_timestamp * 60) + datetime.datetime.strptime(reference_date_string, "%Y%m%d%H%M").timestamp()
        date_time = datetime.datetime.fromtimestamp(epoch_timestamp)
        return date_time
    else:
        return 'not_supported'