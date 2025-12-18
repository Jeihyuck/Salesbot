import sys

sys.path.append("/www/alpha/")
import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "alpha.settings")
django.setup()

import json
import datetime
from apps.rubicon_v3.__function import _51_structured_data as structured_data
from apps.rubicon_v3.__function import _52_structured_account_info as account_info
from apps.rubicon_v3.__function.definitions import sub_intelligences
from decimal import Decimal


class DateTimeEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (datetime.date, datetime.datetime)):
            return obj.isoformat()
        elif isinstance(obj, Decimal):
            return str(obj)
        return super().default(obj)

# Use DateTimeEncoder to convert datetime dtypes
def refine_item(item):
    if isinstance(item, list):
        return [refine_item(sub_item) for sub_item in item]
    elif isinstance(item, dict):
        return json.loads(json.dumps(item, cls=DateTimeEncoder))
    elif isinstance(item, (datetime.date, datetime.datetime)):
        return item.isoformat()
    else:
        return item

"""
Provide personalized API and store-related information using the input provided by 40 rag distributer.
"""
def process_structured_rag(
    query,
    embedding,
    intelligence,
    sub_intelligence,
    distinct_views,
    NER_output,
    guid,
    said,
    country_code: str,
    channel: str,
    site_cd,
    message_id,
):
    required_guid_key = False
    # Membership tier, point balance 
    if sub_intelligence == sub_intelligences.ACCOUNT_MANAGEMENT_INFORMATION:
        if guid:
            account_info_dict = account_info.account_info_api(guid, country_code, channel)
            if account_info_dict:
                organized_structured_rag = {
                "completed": True,
                "structured_rag": [account_info_dict]
                }
                return organized_structured_rag
        else:
            required_guid_key = True
            
    # Provide owned devices, recently viewed products, wishlist, and shopping cart
    if sub_intelligence == sub_intelligences.ACCOUNT_ACTIVITY:
        if guid:
            account_activity_dict = account_info.account_activity_api(guid, said, country_code, site_cd, channel)
            if account_activity_dict:
                organized_structured_rag = {
                "completed": True,
                "structured_rag": [account_activity_dict]
                }
                return organized_structured_rag
        else:
            required_guid_key = True

    # Order devliery 
    if sub_intelligence == sub_intelligences.ORDER_DELIVERY_TRACKING:
        if guid:
            order_info_list = account_info.order_delivery_api(guid, country_code, channel)
            if order_info_list:
                organized_structured_rag = {
                "completed": True,
                "structured_rag": order_info_list
                }
                return organized_structured_rag
        else:
            required_guid_key = True
    
    # If the query is not related to personalization or store.
    view = distinct_views[0] if distinct_views else 'empty'
    if view != 'store':
        if required_guid_key:
            organized_structured_rag = {
                "completed": False,
                "debug_messages": "need guid"
                }
            
        else:
            organized_structured_rag = {
                "completed": False,
                "debug_messages": "OOS"
                }
        return organized_structured_rag
    
    # store 
    if view == 'store' and sub_intelligence not in [sub_intelligences.SAMSUNG_STORE_INFORMATION, sub_intelligences.SERVICE_CENTER_EXPLANATION]:
        organized_structured_rag ={
                    "completed": False,
                    "debug_messages": "Not related to store information"
                }
        return organized_structured_rag
    
    # Select target codes for store-related mappin
    target_fields = ['location','store_name','service_center_name']
    target_ner = [result
            for result in NER_output
            if result['field'] in target_fields and result['operator']=='in'
        ]

    # Execute store function
    structured_rag_result, debug_messages, code_mapping_result = structured_data.store(
        target_ner, country_code, message_id
    )

    if isinstance(structured_rag_result, list):
        structured_rag_result_refined = refine_item(structured_rag_result)

    elif isinstance(structured_rag_result, dict):
        structured_rag_result_refined = json.loads(
            json.dumps(structured_rag_result, cls=DateTimeEncoder)
        )

    if not structured_rag_result:
        invalid_store_key = False
        debug_messages =  [message for message in debug_messages if message.startswith("Store Invalid")] or debug_messages
        if any(message.startswith("Store") for message in debug_messages):
            #  When asking about Samsung Store in a country other than the specified one 
            invalid_store_key = True
        organized_structured_rag = {
            "completed": False,
            "debug_messages": debug_messages,
            "re_asking": True,
            "invalid_store": invalid_store_key,
            "code_mapping_result": code_mapping_result
        }
        return organized_structured_rag
    
    organized_structured_rag = {
            "completed": True,
            "structured_rag": structured_rag_result_refined,
            "code_mapping_result": code_mapping_result,
            "debug_messages": debug_messages
        }
    return organized_structured_rag
