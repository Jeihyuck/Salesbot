from ast import Param
import sys
from matplotlib.axis import Tick

sys.path.append("/www/alpha/")

import os
import glob
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "alpha.settings")
django.setup()

from alpha import __log

from apps.rubicon_admin.__function._gatekeeper import (
    get_service_ticket,
    process_tickets,
    get_specific_ticket,
    get_log_by_ids,
    hide_messages,
    unhide_messages,
    delete_messages,
    export_messages
)


def get_specific_ticket_gatekeeper(request_dict):
    __log.debug(request_dict)

    _, tickets, _, _ = get_ticket_gatekeeper(request_dict)

    specific_ticket = get_specific_ticket(tickets, request_dict.get("guId"))
    __log.debug(f"Specific ticket: {specific_ticket}")
    return (
        True,
        specific_ticket,
        None,
        {"type": "success", "title": "Success", "text": "Specific Ticket Retrieved."},
    )


def get_logs_by_ids_gatekeeper(request_dict):
    __log.debug(request_dict)
    request_dict = request_dict["query"]
    guId = request_dict.get("guid", "")
    userId = request_dict.get("userid", "")
    saId = request_dict.get("said", "")

    logs = get_log_by_ids(guId, saId, userId)
    # __log.debug(f"Retrieved logs: {logs}")
    return (
        True,
        logs,
        None,
        {"type": "success", "title": "Success", "text": "Logs Retrieved."},
    )
    # return logs


def hide_messages_gatekeeper(request_dict):
    query_params = request_dict.get("query", {})
    message_ids = query_params.get("message_ids", [])
    
    result = hide_messages(message_ids)
    return (
        True,
        result,
        None,
        {"type": "success", "title": "Success", "text": "Messages Hidden."},
    )


def unhide_messages_gatekeeper(request_dict):
    query_params = request_dict.get("query", {})
    message_ids = query_params.get("message_ids", [])

    result = unhide_messages(message_ids)
    return (
        True,
        result,
        None,
        {"type": "success", "title": "Success", "text": "Messages Unhidden."},
    )
    
def delete_messages_gatekeeper(request_dict):
    query_params = request_dict.get("query", {})
    message_ids = query_params.get("message_ids", [])
    
    result = delete_messages(message_ids)
    return (
        True,
        result,
        None,
        {"type": "success", "title": "Success", "text": "Messages Deleted."},
    )

def export_messages_gatekeeper(request_dict):
    query_params = request_dict.get("query", {})
    
    result = export_messages(query_params)
    return (
        True,
        result,
        None,
        {"type": "success", "title": "Success", "text": "Messages Exported."},
    )


def create_params_gatekeeper():

    params = {
        "base_url": os.getenv("GK_URL"),
        "service_code": "GKSCD51035",
        "username": "GKSCD51035",
        "password": os.getenv("GK_PW"),
    }

    return params


def get_ticket_gatekeeper(request_dict):
    __log.debug(request_dict)

    params = create_params_gatekeeper()

    tickets = get_service_ticket(**params)

    return (
        True,
        tickets,
        None,
        {"type": "success", "title": "Success", "text": "Privacy Queue Checked."},
    )


def process_ticket_gatekeeper(tickets):
    __log.debug(tickets)

    zip_dir = "/www/alpha/apps/rubicon_admin/__function/fileUpload"
    if os.path.isdir(zip_dir):
        for err_file in glob.glob(os.path.join(zip_dir, "RubiconChatbot_*.zip")):
            os.remove(err_file)
            __log.debug(f"Removed zip file: {err_file}")

    params = create_params_gatekeeper()

    results = process_tickets(tickets, **params)

    return (
        True,
        results,
        None,
        {"type": "success", "title": "Success", "text": "Privacy Queue Processed."},
    )


def check_privacy(request_dict):
    __log.debug(request_dict)

    """
    Endpoint to check privacy-related queries.
    """
    return_data = {"privacy_check_result": "Privacy has been checked successfully."}
    return (
        True,
        return_data,
        None,
        {"type": "success", "title": "Success", "text": "Privacy has checked."},
    )


# 성공/실패, 데이터, 데이터 메타, 메시지
