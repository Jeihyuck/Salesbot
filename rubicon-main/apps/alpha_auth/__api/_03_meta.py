import json
import asyncio
from alpha import __log
from icecream import ic
from datetime import datetime

# from django.db.models import F, Q
from django.core.paginator import Paginator
from django.db import connection, transaction

from apps.alpha_auth.models import Alpha_Department
from alpha.settings import VITE_OP_TYPE


def list_department(request_dict):
    # __log.debug(request_dict)
    distinct_values = Alpha_Department.objects.order_by('order').values('department').distinct()
    distinct_values_list = [item['department'] for item in distinct_values]
    # distinct_values_list = sorted(distinct_values_list)
    # __log.debug(distinct_values_list)
    return True, distinct_values_list,  None, None