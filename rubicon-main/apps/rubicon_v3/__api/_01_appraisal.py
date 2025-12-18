import subprocess
import redis
from alpha import __log
from alpha._db import chat_log_collection
from alpha.settings import REDIS_ORCHESTRATOR_IP, REDIS_PASSWORD, REDIS_PORT
from apps.rubicon_v3.__function.__django_cache import DjangoCacheClient, CacheKey
from apps.__common.utils import convert_unparsables_to_string
import re


def convert_images_to_html(image_list):
    if image_list == None or image_list == "" or image_list == []:
        return ""
    else:
        pattern = r"!\[(.*?)\]\((.*?)\)"
        html_images = []

        for img in image_list:
            match = re.match(pattern, img)
            if match:
                caption, url = match.groups()
                html_img = f'<img class="result_image" src="{url}" title="{caption}">'
                html_images.append(html_img)
            else:
                print(f"Warning: Invalid markdown image format: {img}")

        return "<br>".join(html_images)


def ut_appraisal(request_dict):
    appraisal = {
        "thumb_up": request_dict["query"]["thumb_up"],
    }

    key = next(
        (k for k in ("selection", "selected_list") if k in request_dict["query"]), None
    )
    if key:
        appraisal["selection"] = request_dict["query"][key]
    if "comment" in request_dict["query"]:
        appraisal["comment"] = request_dict["query"]["comment"]
    if "type" in request_dict["query"]:
        appraisal["type"] = request_dict["query"]["type"]

    appraisal["raw"] = request_dict["query"]

    chat_log_collection.update_one(
        {"message_id": request_dict["query"]["message_id"]},
        {"$set": {"appraisal": appraisal}},
    )
    return True, None, None, None


def get_reference_document(request_dict):
    redis_key = request_dict["query"]["message_id"] + "unstructured_content"
    unstructured_content = DjangoCacheClient().get(redis_key)

    if "spcification_check_data" in unstructured_content:

        spec_table_dict = unstructured_content["spcification_check_data"]
        del unstructured_content["spcification_check_data"]
    else:
        spec_table_dict = {}

    spec_table_markdown = ""
    for query in spec_table_dict:
        for spec_table in spec_table_dict[query]:
            spec_table_markdown += f"{spec_table['table_name']} \n\n"

    return_object = {
        "unstructred_content": unstructured_content,
        "spec_table": spec_table_markdown,
    }
    return True, return_object, None, None

    # return True, result_list, [{'itemCount': len(result_list)}], None


def convert_to_markdown_table(timing_logs):
    table = "| Process | Elapsed Time |\n"
    table += "|:--------|-----:|\n"
    for item in timing_logs:
        table += f"| {item['process']} | {item['time']} |\n"
    return table


def get_last_commit_info():
    # Get the last commit hash
    commit_hash = (
        subprocess.check_output(["git", "rev-parse", "HEAD"]).strip().decode("utf-8")
    )

    # Get the last commit date
    commit_date = (
        subprocess.check_output(["git", "log", "-1", "--format=%cd"])
        .strip()
        .decode("utf-8")
    )

    # Get the last commit message
    commit_message = (
        subprocess.check_output(["git", "log", "-1", "--format=%B"])
        .strip()
        .decode("utf-8")
    )

    # Get the current branch name
    branch_name = (
        subprocess.check_output(["git", "rev-parse", "--abbrev-ref", "HEAD"])
        .strip()
        .decode("utf-8")
    )

    status = (
        subprocess.check_output(["git", "status"]).strip().decode("utf-8").split("\n")
    )

    return commit_hash, commit_date, commit_message, branch_name, status


import json


def get_debug(request_dict):
    redis_key = CacheKey.debug_content(request_dict["query"]["message_id"])
    debug_content = DjangoCacheClient().get(redis_key)

    redis_key = CacheKey.debug_timing_logs(request_dict["query"]["message_id"])
    timing_logs = DjangoCacheClient().get(redis_key)

    # __log.debug(timing_logs)

    rouned_time_logs = []
    for item in timing_logs:
        if isinstance(item, str):
            rouned_time_logs.append(
                {
                    "process": item[0],
                    "time": item[1],
                }
            )
        else:
            try:
                rouned_time_logs.append(
                    {
                        "process": item[0],
                        "time": (
                            str(round(item[1], 4)) + " Sec"
                            if item[1] != None
                            else "None"
                        ),
                    }
                )
            except Exception as e:
                rouned_time_logs.append(
                    {
                        "process": item[0],
                        "time": item[1],
                    }
                )

    markdown_table = convert_to_markdown_table(rouned_time_logs)

    commit_hash, commit_date, commit_message, branch_name, status = (
        get_last_commit_info()
    )
    if not debug_content:
        debug_content = []

    debug_content.insert(
        0,
        {
            "section_name": "Git",
            "commit_hash": commit_hash,
            "commit_date": commit_date,
            "commit_message": commit_message,
            "branch_name": branch_name,
            "status": status,
        },
    )

    return_object = {
        "debug_content": debug_content,
        "timing_logs": markdown_table,
        "timging_logs_json": timing_logs,
    }

    convert_unparsables_to_string(return_object)

    # for item in return_object['debug_content']:
    #     __log.debug(item)
    #     __log.debug(json.dumps(item))
    #     __log.debug('***********************************************************')
    return True, return_object, None, None
