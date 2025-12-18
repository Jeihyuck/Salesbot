import sys

sys.path.append("/www/alpha/")

import requests
import os
from datetime import datetime, timezone
from django.db.utils import DatabaseError
from pymongo import DESCENDING
import pandas as pd
import base64
import json
import pyminizip
import hashlib
from bson import ObjectId
from collections import Counter
import re
import csv
import io

from alpha._db import chat_log_collection

from alpha import __log
from apps.rubicon_v3.__external_api.__dkms_encode import DKMS_Encoder

GDPRS_PATH = "/www/alpha/apps/rubicon_admin/__function/fileUpload"
BASE_PATH = "/www/alpha/apps/rubicon_admin/__function/"

CERT_PATH = (
    os.path.join(os.path.dirname(__file__), "cert", "pwc.crt"),
    os.path.join(os.path.dirname(__file__), "cert", "pwc.key"),
)

dkms_encoder = DKMS_Encoder()


def get_service_ticket(base_url, service_code, username, password):
    """
    게이트키퍼 서비스 티켓을 얻어오는 함수

    Args:
        base_url (str): API 기본 URL
        service_code (str): 서비스 코드
        username (str): 인증 username
        password (str): 인증 password

    Returns:
        dict: API 응답 결과 (성공 시)
        None: 실패 시
    """
    country_code = os.getenv("VITE_COUNTRY")
    try:
        response = requests.get(
            f"{base_url}/v2.0/gatekeeper/service/ticket",
            params={"service_code": service_code},
            auth=(username, password),
        )

        if response.status_code == 200:
            original_tickets = response.json()
            if country_code == "KR":
                # 한국의 경우 country_code가 'KR'인 티켓만 필터링
                filtered_tickets = [
                    x for x in original_tickets if x.get("country_code", "") == "KR"
                ]
            else:
                # 다른 국가의 경우 country_code가 빈 문자열인 티켓만 필터링
                filtered_tickets = [
                    x for x in original_tickets if x.get("country_code", "") != "KR"
                ]
            return filtered_tickets
        else:
            __log.debug(f"Error: {response.status_code}")
            __log.debug(f"Response: {response.text}")
            return None

    except requests.exceptions.RequestException as e:
        __log.debug(f"Request failed: {e}")
        return None


def save_chatlog(filter_criteria, file_name: str, save_data: bool = True):
    total_log_pd = pd.DataFrame(
        columns=["created_on", "session_title", "message", "output"]
    )
    try:
        cursor = chat_log_collection.find(filter_criteria).sort(
            "created_on", DESCENDING
        )
        total_row_ls = []
        for doc in cursor:
            # if doc['log'] != []:
            try:
                user_query = dkms_encoder.getDecryptedValue(
                    doc["input_log"]["message"]
                )  # 복호화 하여 가져옴
                query_response = dkms_encoder.getDecryptedValue(
                    doc["log"]["full_response"]
                )  # 복호화 하여 가져옴

                row_ls = [
                    json.loads(user_query)[0]["content"],
                    doc["session_title"],
                    query_response,
                    doc["created_on"],
                ]
                total_row_ls.append(row_ls)
            except Exception as e:
                __log.debug(f"KeyError: {e} in document")
                continue
        __log.debug(f"Total rows: {len(total_row_ls)}")
        total_log_pd = pd.DataFrame(
            total_row_ls, columns=["message", "session_title", "log", "created_on"]
        )
        if save_data:
            total_log_pd.to_excel(GDPRS_PATH + "/" + file_name, index=False)
        return True

    except DatabaseError as e:
        # 데이터베이스 오류 처리 (적재 시점 차이로 인해 스키마다 다르면 발생할 수 있음)
        __log.debug(f"DatabaseError: {e}")
        return False


def delete_chatlog(filter_criteria):
    batch_size = 1000
    total_deleted = 0
    try:
        while True:
            # fetch a batch of document _ids
            cursor = chat_log_collection.find(filter_criteria, {"_id": 1}).limit(
                batch_size
            )
            ids = [doc["_id"] for doc in cursor]
            if not ids:
                break
            # delete this batch
            result = chat_log_collection.delete_many({"_id": {"$in": ids}})
            total_deleted += result.deleted_count
            __log.debug(
                f"Batch deleted {result.deleted_count} documents; total so far {total_deleted}."
            )
        __log.debug(f"Finished deleting documents; total deleted: {total_deleted}.")
        return True
    except DatabaseError as e:
        __log.debug(f"DatabaseError: {e}")
        __log.debug("Failed to delete documents.")
        return False


def modify_chatlog(filter_criteria, new_value: bool):
    batch_size = 1000
    total_modified = 0
    # combine base filter with mismatch on current hidden status
    mismatch_filter = {
        "$and": [filter_criteria, {"messgae_status.is_hidden": {"$ne": new_value}}]
    }
    try:
        while True:
            # fetch a batch of document _id's where is_hidden != new_value
            cursor = chat_log_collection.find(mismatch_filter, {"_id": 1}).limit(
                batch_size
            )
            ids = [doc["_id"] for doc in cursor]
            if not ids:
                break

            # update this batch
            result = chat_log_collection.update_many(
                {"_id": {"$in": ids}},
                {
                    "$set": {
                        "messgae_status.is_hidden": new_value,
                        "message_status.hidden_on": datetime.now(timezone.utc),
                    }
                },
            )
            total_modified += result.modified_count
            __log.debug(
                f"Batch modified {result.modified_count} docs; total so far {total_modified}."
            )

        __log.debug(f"Finished modifying documents; total modified: {total_modified}.")
        return True
    except DatabaseError as e:
        __log.debug(f"DatabaseError: {e}")
        __log.debug("Failed to modify documents.")
        return False


def prosess_one_ticket(search_id, event_type, event_sub_type):

    # 전달 받은 search_id를 암호화
    encoded_id = search_id

    filter_criteria = {
        "input_log.guId": encoded_id,
    }

    count = chat_log_collection.count_documents(filter_criteria)
    __log.debug(f"Count of documents for gu_id {search_id}: {count}")
    task_log = False
    try:
        if count > 0:
            # 이동권, 열람권
            if event_type in ["A", "P"]:
                task_log = save_chatlog(filter_criteria, "Raw data.xlsx")
            # 삭제권
            elif event_type in ["E"]:
                task_log = delete_chatlog(filter_criteria)
            # 처리제한권, 반대권
            elif event_type in ["R", "O"]:
                # 처리 제한 해제
                if event_type == "R" and event_sub_type == "C":
                    task_log = modify_chatlog(filter_criteria, False)
                # 처리 제한
                elif event_type == "R" and event_sub_type == "R":
                    task_log = modify_chatlog(filter_criteria, True)
                # 반대권
                else:
                    task_log = modify_chatlog(filter_criteria, True)
            # 구독취소 (200 처리)
            elif event_type in ["U"]:
                task_log = True
        else:
            task_log = True
            __log.debug(f"No documents found for user_id: {search_id}")
    except Exception as e:
        __log.debug(f"Error processing ticket {search_id}: {e}")

    return task_log, count


def create_encrypted_zip(
    file_list, gdprs_folder, service_name, gk_id, password, event_type
):
    """
    파일들을 암호화된 zip으로 압축하는 함수

    Args:
        file_list (list): 압축할 파일들의 이름 리스트
        gdprs_folder (str): GDPRS 폴더 경로
        service_name (str): 서비스 이름
        gk_id (str): 게이트키퍼 티켓 ID
        password (str): 압축 파일 비밀번호
        event_type (str): 이벤트 타입 ("A" 또는 "P")

    Returns:
        str: 생성된 압축 파일의 전체 경로
        None: 실패 시
    """
    try:
        # 현재 날짜로 creation_date 생성 (YYYYMMDD)
        creation_date = datetime.now().strftime("%Y%m%d")

        # ticket_type 결정
        ticket_type = "access" if event_type == "A" else "portability"

        # 압축 파일 이름 생성
        compressed_file = f"{service_name}_{gk_id}_{creation_date}_{ticket_type}.zip"
        zip_path = os.path.join(gdprs_folder, compressed_file)

        pyminizip.compress_multiple(
            [
                os.path.join(gdprs_folder, file_name)
                for file_name in file_list
                if os.path.exists(os.path.join(gdprs_folder, file_name))
            ],  # 압축할 파일 리스트
            [],  # 빈 리스트로 대체 (압축 경로 없음)
            zip_path,  # 생성할 zip 파일 경로
            password,  # 압축 비밀번호
            5,  # 압축 레벨 (1-9, 9가 가장 높은 압축률)
        )

        raw_data_path = os.path.join(gdprs_folder, "Raw data.xlsx")
        if os.path.exists(raw_data_path):
            os.remove(
                raw_data_path
            )  # Raw data.xlsx 파일은 압축 후 삭제 (타 유저 전달 방지용)

        return zip_path

    except Exception as e:
        __log.debug(f"Error creating zip file: {e}")
        return None


def create_upload_url(
    link, cid, content_type, content_length, partner_id, unit_id, cert_path
):
    """
    업로드 URL을 생성하는 API를 호출하는 함수

    Args:
        link (str): API 기본 URL
        cid (str): Content ID
        content_type (str): 컨텐츠 타입 (예: 'application/zip')
        content_length (int): 파일 크기
        partner_id (str): 파트너 ID
        unit_id (str): 유닛 ID
        cert_path (tuple): 인증서 경로 튜플 (cert_file, key_file)

    Returns:
        dict: API 응답 결과 (성공 시)
        None: 실패 시
    """
    endpoint = f"{link}/objects"

    headers = {
        "x-sc-content-type": content_type,
        "x-sc-content-length": str(content_length),
        "x-sc-partner-id": partner_id,
        "x-sc-unit-id": unit_id,
    }

    params = {"cid": cid}

    try:
        response = requests.post(
            endpoint, headers=headers, params=params, cert=cert_path
        )
        # __log.debug(f"cert_path: {cert_path}")
        # __log.debug(f"create upload url: {response.json()}")
        if response.status_code == 200:

            return response.json()
        else:
            __log.debug(f"Error: {response.status_code}")
            __log.debug(f"Response: {response.text}")
            return None

    except requests.exceptions.RequestException as e:
        __log.debug(f"Request failed: {e}")
        return None


# S3 data upload
def upload_to_s3(upload_info, file_path, content_type):
    """
    S3에 파일을 업로드하는 함수
    Args:
        upload_info (dict): create_upload_url()의 응답 결과
        file_path (str): 업로드할 파일의 경로
        content_type (str): 컨텐츠 타입
    Returns:
        requests.Response: 업로드 요청의 응답 객체
        None: 실패 시
    """
    try:
        with open(file_path, "rb") as f:
            headers = {"Content-Type": content_type}
            response = requests.put(
                upload_info["upload_info"]["url"], data=f, headers=headers
            )
        if response.status_code == 200:
            return response
        else:
            __log.debug(f"Error: {response.status_code}")
            __log.debug(f"Response: {response.text}")
            return None
    except Exception as e:
        __log.debug(f"Upload failed: {e}")
        return None


# Get Download URL API
def get_signed_url(
    link, object_id, cid, partner_id, unit_id, filename, content_type, cert_path
):
    """
    signed URL을 받아오는 함수

    Args:
        link (str): API 기본 URL
        object_id (str): 업로드된 객체 ID
        cid (str): Content ID
        partner_id (str): 파트너 ID
        unit_id (str): 유닛 ID
        filename (str): 응답에 포함될 파일명
        content_type (str): 컨텐츠 타입
        cert_path (tuple): 인증서 경로 튜플 (cert_file, key_file)

    Returns:
        dict: API 응답 결과 (성공 시)
        None: 실패 시
    """
    endpoint = f"{link}/objects/{object_id}/signed"

    headers = {
        "x-sc-partner-id": partner_id,
        "x-sc-unit-id": unit_id,
        "x-sc-response-filename": filename,
        "x-sc-response-content-type": content_type,
    }

    params = {"cid": cid}

    try:
        response = requests.get(
            endpoint, headers=headers, params=params, cert=cert_path
        )

        if response.status_code == 200:
            return response.json()
        else:
            __log.debug(f"Error: {response.status_code}")
            __log.debug(f"Response: {response.text}")
            return None

    except requests.exceptions.RequestException as e:
        __log.debug(f"Request failed: {e}")
        return None


# S3에 파일 업로드 후 signed URL 획득
def process_file_upload(
    link,
    cid,
    content_type,
    file_path,
    partner_id,
    unit_id,
    cert_path,
    content_length=None,
):
    # 파일 크기 자동 계산 (지정되지 않은 경우)
    if content_length is None:
        content_length = os.path.getsize(file_path)

    # 1. Upload URL 생성
    upload_info = create_upload_url(
        link=link,
        cid=cid,
        content_type=content_type,
        content_length=content_length,
        partner_id=partner_id,
        unit_id=unit_id,
        cert_path=cert_path,
    )

    if not upload_info:
        __log.debug("Failed to get upload URL")
        return None

    __log.debug("Upload URL created successfully")

    # 2. S3에 파일 업로드
    upload_response = upload_to_s3(
        upload_info=upload_info, file_path=file_path, content_type=content_type
    )

    if not upload_response:
        __log.debug("Failed to upload file to S3")
        return None
    if upload_response:
        __log.debug("File uploaded to S3 successfully")

    # 3. Signed URL 획득
    filename = os.path.basename(file_path)
    signed_url = get_signed_url(
        link=link,
        object_id=upload_info["object_id"],
        cid=cid,
        partner_id=partner_id,
        unit_id=unit_id,
        filename=filename,
        content_type=content_type,
        cert_path=cert_path,
    )

    if not signed_url:
        __log.debug("Failed to get signed URL")
        return None

    __log.debug("Signed URL obtained successfully")
    return signed_url


def process_tickets(tickets, base_url, username, password, service_code):

    # Normalize input to always be a list
    if isinstance(tickets, dict):
        # Single ticket case
        tickets_list = [tickets]
        __log.debug("Processing single ticket")
    elif isinstance(tickets, list):
        # Multiple tickets case
        tickets_list = tickets
        __log.debug(f"Processing {len(tickets_list)} tickets")
    else:
        __log.error(f"Invalid tickets type: {type(tickets)}. Expected dict or list.")
        return []

    # --- verify private key file format before proceeding, auto-fix missing markers ---
    cert_file = os.path.join(os.path.dirname(__file__), "cert", "pwc.key")
    try:
        # read raw lines
        with open(cert_file, "r", encoding="utf-8") as cf:
            content = cf.read()
            lines = content.splitlines()
            original_content = content

        begin_marker = "-----BEGIN PRIVATE KEY-----"
        end_marker = "-----END PRIVATE KEY-----"
        modified = False

        # ensure BEGIN marker
        if not lines or lines[0].strip() != begin_marker:
            lines.insert(0, begin_marker)
            modified = True
        # ensure END marker
        if not lines or lines[-1].strip() != end_marker:
            lines.append(end_marker)
            modified = True

        # save back if we inserted markers
        if modified:
            with open(cert_file, "w", encoding="utf-8") as cf:
                cf.write("\n".join(lines) + "\n")
            __log.info(f"Inserted missing private key markers into {cert_file}")
    except Exception as e:
        __log.debug(f"Error verifying private key file format: {e}")
        return []

    FILES_TO_COMPRESS = [
        "Category.pdf",
        "Raw data.xlsx",
        "Rubicon Chatbot_File Description_en_v1.0.pdf",
        "Rubicon Chatbot_File Description_fr_v1.0.pdf",
    ]

    # Basic 인증 헤더 생성
    auth_str = f"{username}:{password}"
    auth_bytes = auth_str.encode("ascii")
    base64_auth = base64.b64encode(auth_bytes).decode("ascii")
    zip_path = GDPRS_PATH + "/sample.zip"
    results = []

    for ticket in tickets_list:
        ticket_dict = {}
        __log.debug(ticket)
        count = 0
        try:
            if "target_service_cd" in ticket:
                raise ValueError("Invalid ticket format: 'target_service_cd' found")
            event_type = ticket.get("event_type", "")
            event_sub_type = ticket.get("event_sub_type", "")
            search_id = ticket.get("id_type_guid", "")

            task_result, count = prosess_one_ticket(
                search_id, event_type, event_sub_type
            )
            __log.debug(task_result)

            # 이동권, 열람권인 경우 대화 내역 포함 전달
            if event_type in "A":
                FILES_TO_COMPRESS_EXEC = FILES_TO_COMPRESS.copy()

            # 이동권의 경우 Category.pdf 제외
            if event_type in "P":
                FILES_TO_COMPRESS_EXEC = [
                    x for x in FILES_TO_COMPRESS if "Category" not in x
                ]

            # 이동권, 열람권이 아닌 경우 대화 내역 제외 전달
            if event_type not in ["A", "P"]:
                FILES_TO_COMPRESS_EXEC = [
                    x for x in FILES_TO_COMPRESS if "RAW data" not in x
                ]

            # 1. 압축 파일 생성
            zip_params = {
                "file_list": FILES_TO_COMPRESS_EXEC,
                "gdprs_folder": GDPRS_PATH,
                "service_name": "RubiconChatbot",
                "gk_id": ticket.get("gk_id", ""),
                "password": ticket.get("password", ""),
                "event_type": event_type,
            }

            zip_path = create_encrypted_zip(**zip_params)
            if not zip_path:
                raise Exception("Failed to create zip file")

            # 압축 파일 크기 확인
            file_size = str(os.path.getsize(zip_path))
            file_name = os.path.basename(zip_path)

            # 2. S3 업로드 처리
            upload_params = {
                "link": os.getenv("S3_LINK"),
                "cid": os.getenv("S3_CID"),
                "content_type": "application/zip",
                "file_path": zip_path,
                "partner_id": os.getenv("S3_PARTNER_ID"),
                "unit_id": ticket.get("id_type_guid", ""),
                "cert_path": CERT_PATH,
            }

            upload_result = process_file_upload(**upload_params)
            if not upload_result:
                raise Exception("Failed to upload file")

            # 3. API 호출
            if task_result:
                # 로그가 존재하며 정상 처리일 경우 200
                if count > 0:
                    result_code = 200
                # 로그가 미존재하며 정상 처리일 경우 201
                if count == 0:
                    result_code = 201
            # 오류 케이스
            else:
                result_code = 500
            result_payload = {
                "service_code": service_code,
                "gk_id": ticket.get("gk_id", ""),
                "result_code": result_code,
                "event_type": event_type,
                "event_sub_type": ticket.get("event_sub_type", ""),
                "password": ticket.get("password", ""),
                "provided_link": [
                    {
                        "link": upload_result["download_info"]["url"],
                        "file_name": file_name,
                        "file_size": file_size,
                        "exp_date": str(upload_result["download_info"]["expires"]),
                    }
                ],
            }
            # __log.debug(result_payload)

            result_headers = {
                "Authorization": f"Basic {base64_auth}",
                "Content-Type": (
                    "application/zip" if event_type == "A" else "application/json"
                ),
            }

            response = requests.post(
                f"{base_url}/v2.0/gatekeeper/service/result",
                headers=result_headers,
                data=json.dumps(result_payload),
            )

            # if not task_result:
            #     raise Exception(
            #         f"Task processing failed for ticket {ticket.get('gk_id', '')}"
            #     )

            ticket_dict = {
                "gk_id": ticket.get("gk_id", ""),
                "status_code": response.status_code,
                "event_type": event_type,
                "response": response.text,
                "log_count": str(count),
            }

            # A/P 타입인 경우 추가 정보 저장
            if event_type in ["A", "P"]:
                ticket_dict["upload_result"] = upload_result
                ticket_dict["upload_url"] = upload_result["download_info"]["url"]

        except Exception as e:
            error_ticket = (
                ticket["gk_id"] if "gk_id" in ticket else ticket["target_service_cd"]
            )
            if not error_ticket:
                error_ticket = "Unknown Ticket"
            __log.debug(f"Error processing ticket {error_ticket}: {e}")
            ticket_dict = {
                "gk_id": error_ticket,
                "status_code": None,
                "event_type": ticket.get("event_type", ""),
                "response": str(e),
                "log_count": str(count),
            }

        finally:
            if os.path.exists(zip_path):
                os.remove(zip_path)  # 업로드 후 압축 파일 삭제
            # 결과 저장
            results.append(ticket_dict)

    # __log.debug(results)
    # --- revert pwc.key file to original state if it was modified ---
    try:
        if original_content is not None:
            with open(cert_file, "w", encoding="utf-8") as cf:
                cf.write(original_content)
            __log.info(f"Reverted {cert_file} to original state")
    except Exception as e:
        __log.error(f"Failed to revert {cert_file}: {e}")
    return results


def get_specific_ticket(tickets, gu_id):
    for ticket in tickets:
        if ticket.get("id_type_guid", "") == gu_id:
            return ticket
    return None


def get_log_by_ids(guId=None, saId=None, userId=None):
    filter_criteria = {}
    if guId:
        filter_criteria["input_log.guId"] = guId
    if saId:
        filter_criteria["input_log.saId"] = saId
    if userId:
        user_hash = hashlib.sha256(str(userId).encode("utf-8")).hexdigest()
        filter_criteria["user_hash"] = user_hash

    __log.debug(f"Filter criteria : {filter_criteria}")

    if not filter_criteria:
        __log.debug("No valid identifiers provided for log retrieval.")
        return []

    cursor = chat_log_collection.find(filter_criteria).sort("created_on", DESCENDING)
    logs = list(cursor)
    __log.debug(f"Retrieved {len(logs)} logs matching criteria: {filter_criteria}")

    results = []
    for doc in logs:
        try:
            # Extract and decrypt relevant fields
            message_id = doc.get("message_id", "")
            guid = doc.get("input_log", {}).get("guId", "")
            said = doc.get("input_log", {}).get("saId", "")
            userid = dkms_encoder.getDecryptedValue(
                doc.get("input_log", {}).get("userId", "")
            )
            created = doc.get("created_on", "")
            updated = doc.get("hidden_on", "")
            status = doc.get("messgae_status", {}).get("is_hidden", False)

            # Convert status to readable format
            status_text = "hidden" if status else "active"

            results.append(
                {
                    "messageid": message_id,
                    "guid": guid,
                    "said": said,
                    "userid": userid,
                    "created": created,
                    "updated": updated,
                    "status": status_text,
                }
            )

        except Exception as e:
            # print(f"Error processing document {doc.get('_id')}: {e}")
            continue

    return results


# In your Django backend privacy functions
def hide_messages(message_ids):
    """
    Hide selected chat messages by setting messgae_status.is_hidden to True

    Args:
        request_data: Dictionary containing 'message_ids' list

    Returns:
        dict: Results of the hide operation
    """
    try:
        if not message_ids:
            return {"error": "No message IDs provided", "success": False}

        # Build filter criteria
        filter_criteria = {"message_id": {"$in": message_ids}}

        # Update documents to hide them
        from datetime import datetime, timezone

        update_data = {
            "$set": {
                "messgae_status.is_hidden": True,
                "messgae_status.hidden_on": datetime.now(timezone.utc),
            }
        }

        # Perform the update
        result = chat_log_collection.update_many(filter_criteria, update_data)

        # Get the updated documents to verify
        updated_docs = list(
            chat_log_collection.find(
                filter_criteria,
                {
                    "_id": 1,
                    "messgae_status.is_hidden": 1,
                    "messgae_status.hidden_on": 1,
                },
            )
        )

        response_data = {
            "success": True,
            "matched_count": result.matched_count,
            "modified_count": result.modified_count,
            "requested_ids": len(message_ids),
            "updated_documents": [
                {
                    "id": str(doc["_id"]),
                    "is_hidden": doc.get("messgae_status", {}).get("is_hidden", False),
                    "hidden_on": (
                        doc.get("messgae_status", {}).get("hidden_on", "").isoformat()
                        if doc.get("messgae_status", {}).get("hidden_on")
                        else None
                    ),
                }
                for doc in updated_docs
            ],
        }

        print(
            f"Hide messages result: {result.matched_count} matched, {result.modified_count} modified"
        )
        return response_data

    except Exception as e:
        print(f"Error in hide_messages: {e}")
        return {
            "error": str(e),
            "success": False,
            "matched_count": 0,
            "modified_count": 0,
        }


# In your Django backend privacy functions
def unhide_messages(message_ids):
    """
    Hide selected chat messages by setting messgae_status.is_hidden to True

    Args:
        request_data: Dictionary containing 'message_ids' list

    Returns:
        dict: Results of the hide operation
    """
    try:
        if not message_ids:
            return {"error": "No message IDs provided", "success": False}

        # Build filter criteria
        filter_criteria = {"message_id": {"$in": message_ids}}

        # Update documents to hide them
        from datetime import datetime, timezone

        update_data = {
            "$set": {
                "messgae_status.is_hidden": False,
                "messgae_status.hidden_on": datetime.now(timezone.utc),
            }
        }

        # Perform the update
        result = chat_log_collection.update_many(filter_criteria, update_data)

        # Get the updated documents to verify
        updated_docs = list(
            chat_log_collection.find(
                filter_criteria,
                {
                    "_id": 1,
                    "messgae_status.is_hidden": 1,
                    "messgae_status.hidden_on": 1,
                },
            )
        )

        response_data = {
            "success": True,
            "matched_count": result.matched_count,
            "modified_count": result.modified_count,
            "requested_ids": len(message_ids),
            "updated_documents": [
                {
                    "id": str(doc["_id"]),
                    "is_hidden": doc.get("messgae_status", {}).get("is_hidden", False),
                    "hidden_on": (
                        doc.get("messgae_status", {}).get("hidden_on", "").isoformat()
                        if doc.get("messgae_status", {}).get("hidden_on")
                        else None
                    ),
                }
                for doc in updated_docs
            ],
        }

        print(
            f"Hide messages result: {result.matched_count} matched, {result.modified_count} modified"
        )
        return response_data

    except Exception as e:
        print(f"Error in hide_messages: {e}")
        return {
            "error": str(e),
            "success": False,
            "matched_count": 0,
            "modified_count": 0,
        }


# Similar implementation for other functions
def delete_messages(message_ids):
    """
    Permanently delete selected chat messages
    """
    try:
        if not message_ids:
            return {"error": "No message IDs provided", "success": False}

        # Build filter criteria
        filter_criteria = {"message_id": {"$in": message_ids}}

        # Get documents before deletion for logging
        docs_to_delete = list(
            chat_log_collection.find(filter_criteria, {"_id": 1, "input_log.guId": 1})
        )

        # Perform the deletion
        result = chat_log_collection.delete_many(filter_criteria)

        response_data = {
            "success": True,
            "deleted_count": result.deleted_count,
            "requested_ids": len(message_ids),
            "deleted_documents": [
                {
                    "id": str(doc["_id"]),
                    "guid": doc.get("input_log", {}).get("guId", ""),
                }
                for doc in docs_to_delete
            ],
        }

        print(f"Delete messages result: {result.deleted_count} deleted")
        return response_data

    except Exception as e:
        print(f"Error in delete_messages: {e}")
        return {"error": str(e), "success": False, "deleted_count": 0}


def export_messages(query_params):
    """
    Export selected chat messages to specified format
    """
    try:
        message_ids = query_params.get("message_ids", [])
        export_format = query_params.get("format", "json")

        if not message_ids:
            return {"error": "No message IDs provided", "success": False}

        # Get documents
        filter_criteria = {"message_id": {"$in": message_ids}}
        documents = list(chat_log_collection.find(filter_criteria))

        # Process documents for export
        export_data = []
        for doc in documents:
            try:
                user_query = dkms_encoder.getDecryptedValue(
                    doc["input_log"]["message"]
                )  # 복호화 하여 가져옴
                query_response = dkms_encoder.getDecryptedValue(
                    doc["log"]["full_response"]
                )  # 복호화 하여 가져옴

                row_ls = {
                    "message": json.loads(user_query)[0]["content"],
                    "session_title": doc["session_title"],
                    "log": query_response,
                    "created_on": doc["created_on"],
                }
                export_data.append(row_ls)
            except Exception as e:
                print(f"KeyError: {e} in document")
                continue

        if export_format.lower() == "csv":
            # Create CSV
            output = io.StringIO()
            if export_data:
                writer = csv.DictWriter(output, fieldnames=export_data[0].keys())
                writer.writeheader()
                writer.writerows(export_data)
            csv_content = output.getvalue()
            output.close()

            return {
                "success": True,
                "format": "csv",
                "count": len(export_data),
                "data": csv_content,
                "filename": f"chat_logs_export_{len(export_data)}_messages.csv",
            }
        else:
            # Return JSON
            return {
                "success": True,
                "format": "json",
                "count": len(export_data),
                "data": export_data,
                "filename": f"chat_logs_export_{len(export_data)}_messages.json",
            }

    except Exception as e:
        print(f"Error in export_messages: {e}")
        return {"error": str(e), "success": False, "count": 0}


# TODO : 체크 기반 수정, 삭제 처리 (팝업 기반)


# 사용 예시
if __name__ == "__main__":
    params = {
        "base_url": os.getenv("GK_URL"),
        "service_code": "GKSCD51035",
        "username": "GKSCD51035",
        "password": os.getenv("GK_PW"),
    }

    user_id = "jungsoo.park@pwc.com"
    import hashlib

    user_hash = hashlib.sha256(str(user_id).encode("utf-8")).hexdigest()

    filter_criteria = {
        # "input_log.guId": "g4ttiheybj",
        "user_hash": user_hash,
    }
    count = chat_log_collection.count_documents(filter_criteria)
    # cursor = chat_log_collection.find(filter_criteria).sort("created_on", DESCENDING)
    cursor = chat_log_collection.find().sort("created_on", DESCENDING).limit(100)
    # print([x['input_log']['guId'] for x in cursor][:10])
    # tickets = get_service_ticket(**params)
    # tickets = [x for x in tickets if x.get('event_type','') == 'E']
    # __log.debug(tickets)

    # save_chatlog(
    #     chat_log_collection,
    #     filter_criteria,
    #     file_name = '',
    #     save_data = False)

    # results = process_tickets(tickets, **params)
    # print(results)
