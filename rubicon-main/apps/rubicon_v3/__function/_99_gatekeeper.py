import requests
import os
from datetime import datetime
import zipfile

FILES_TO_COMPRESS = [
        "Category.pdf",
        "Raw data.xlsx",
        "RubiconChatbot_File Description_en_v1.0.pdf",
        "RubiconChatbot_File Description_fr_v1.0.pdf"
    ]

CERT_PATH = (
    os.path.join('/www/alpha/___dev/PCG/cert/pwc.crt'),
    os.path.join('/www/alpha/___dev/PCG/cert/pwc.key')
)

GDPRS_PATH = '/www/alpha/___dev/PCG/GDPRS'

S3_UPLOAD_PATH = 'https://stg-an2a-sapi.samsungcloud.com/link/v1'
CID = 'aSWIBH6RSK'
PARTNER_ID = 'Q47NvN9RGx'

def create_encrypted_zip(file_list, gdprs_folder, service_name, gk_id, password, event_type):
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
        creation_date = datetime.now().strftime('%Y%m%d')
        
        # ticket_type 결정
        ticket_type = "access" if event_type == "A" else "portability"
        
        # 압축 파일 이름 생성
        compressed_file = f"{service_name}_{gk_id}_{creation_date}_{ticket_type}.zip"
        zip_path = os.path.join(gdprs_folder, compressed_file)
        
        # 압축 파일 생성
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            zf.setpassword(password.encode())  # 비밀번호 설정
            
            # 각 파일을 압축
            for file_name in file_list:
                file_path = os.path.join(gdprs_folder, file_name)
                if os.path.exists(file_path):
                    zf.write(file_path, file_name)  # 파일 경로에서 파일명만 저장
                else:
                    print(f"Warning: File not found - {file_path}")
        
        return zip_path
        
    except Exception as e:
        print(f"Error creating zip file: {e}")
        return None
    

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
   try:
       response = requests.get(
           f'{base_url}/v2.0/gatekeeper/service/ticket',
           params={'service_code': service_code},
           auth=(username, password)
       )
       
       if response.status_code == 200:
           return response.json()
       else:
           print(f"Error: {response.status_code}")
           print(f"Response: {response.text}")
           return None
           
   except requests.exceptions.RequestException as e:
       print(f"Request failed: {e}")
       return None

# TODO:has_data는 차후 구현
def has_data(ticket):
    return True

def process_tickets(tickets, base_url, username, password, service_code):
    import base64
    import json
    
    # Basic 인증 헤더 생성
    auth_str = f'{username}:{password}'
    auth_bytes = auth_str.encode('ascii')
    base64_auth = base64.b64encode(auth_bytes).decode('ascii')
    
    results = {}
    
    for ticket in tickets:
        if 'target_service_cd' in ticket:
            continue
            
        try:
            event_type = ticket['event_type']
            
            # A와 P 타입은 완전히 다른 프로세스
            if event_type in ['A', 'P']:
                # 1. 압축 파일 생성
                zip_params = {
                    'file_list': FILES_TO_COMPRESS,
                    'gdprs_folder': GDPRS_PATH,
                    'service_name': 'RubiconChatbot',
                    'gk_id': ticket['gk_id'],
                    'password': ticket['password'],
                    'event_type': event_type
                }
                
                zip_path = create_encrypted_zip(**zip_params)
                if not zip_path:
                    raise Exception("Failed to create zip file")
                
                # 압축 파일 크기 확인
                file_size = str(os.path.getsize(zip_path))
                file_name = os.path.basename(zip_path)
                
                # 2. S3 업로드 처리
                upload_params = {
                    'link': S3_UPLOAD_PATH,
                    'cid': CID,
                    'content_type': "application/zip",
                    'file_path': zip_path,
                    'partner_id': PARTNER_ID,
                    'unit_id': ticket['id_type_guid'],
                    'cert_path': CERT_PATH
                }
                
                upload_result = process_file_upload(**upload_params)
                if not upload_result:
                    raise Exception("Failed to upload file")
                
                # 3. A/P용 결과 API 호출
                result_payload = {
                    "service_code": service_code,
                    "gk_id": ticket['gk_id'],
                    "result_code": "200",
                    "event_type": event_type,
                    "event_sub_type": ticket['event_sub_type'],
                    "password": ticket['password'],
                    "provided_link": [
                        {
                            "link": upload_result['download_info']['url'],
                            "file_name": file_name,
                            "file_size": file_size,
                            "exp_date": str(upload_result['download_info']['expires'])
                        }
                    ]
                }
                
                result_headers = {
                    'Authorization': f'Basic {base64_auth}',
                    'Content-Type': 'application/zip' if event_type == 'A' else 'application/json'
                }
                
                response = requests.post(
                    f'{base_url}/v2.0/gatekeeper/service/result', # TODO:need update
                    headers=result_headers,
                    data=json.dumps(result_payload)
                )
            
            # 나머지 타입들은 단순 API 호출
            else:
                payload = {
                    "service_code": service_code,
                    "gk_id": ticket['gk_id'],
                    "event_type": event_type,
                    "event_sub_type": ticket['event_sub_type'],
                }
                
                headers = {
                    'Authorization': f'Basic {base64_auth}',
                    'Content-Type': 'application/json'
                }
                
                if event_type == 'E':
                    if has_data(ticket):
                        payload.update({"result_code": "200", "reason": ""})
                    else:
                        payload.update({"result_code": "201", "reason": "No Data"})
                
                elif event_type == 'R':
                    payload.update({"result_code": "200"})
                
                elif event_type in ['O', 'U']:
                    payload.update({"result_code": "200"})
                
                response = requests.post(
                    f'{base_url}/v2.0/gatekeeper/service/result', # TODO:need update
                    headers=headers,
                    data=json.dumps(payload)
                )
            
            results[ticket['gk_id']] = {
                'status_code': response.status_code,
                'response': response.text
            }
            
            # A/P 타입인 경우 추가 정보 저장
            if event_type in ['A', 'P']:
                results[ticket['gk_id']].update({
                    'zip_path': zip_path,
                    'upload_result': upload_result
                })
                
        except Exception as e:
            print(f"Error processing ticket {ticket['gk_id']}: {e}")
            results[ticket['gk_id']] = {
                'status_code': None,
                'error': str(e)
            }
    
    return results

def create_upload_url(link, cid, content_type, content_length, partner_id, unit_id, cert_path):
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
        'x-sc-content-type': content_type,
        'x-sc-content-length': str(content_length),
        'x-sc-partner-id': partner_id,
        'x-sc-unit-id': unit_id
    }
    
    params = {'cid': cid}
    
    try:
        response = requests.post(
            endpoint,
            headers=headers,
            params=params,
            cert=cert_path
        )
        print(f"cert_path: {cert_path}")
        print(f"create upload url: {response.json()}")
        if response.status_code == 200:
            
            return response.json()
        else:
            print(f"Error: {response.status_code}")
            print(f"Response: {response.text}")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
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
       with open(file_path, 'rb') as f:
           headers = {'Content-Type': content_type}
           response = requests.put(
               upload_info['upload_info']['url'],
               data=f,
               headers=headers
           )
       if response.status_code == 200:
           return response
       else:
           print(f"Error: {response.status_code}")
           print(f"Response: {response.text}")
           return None
   except Exception as e:
       print(f"Upload failed: {e}")
       return None

# Get Download URL API
def get_signed_url(link, object_id, cid, partner_id, unit_id, filename, content_type, cert_path):
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
   endpoint = f"{link}objects/{object_id}/signed"
   
   headers = {
       'x-sc-partner-id': partner_id,
       'x-sc-unit-id': unit_id,
       'x-sc-response-filename': filename,
       'x-sc-response-content-type': content_type
   }
   
   params = {'cid': cid}
   
   try:
       response = requests.get(
           endpoint,
           headers=headers,
           params=params,
           cert=cert_path
       )
       
       if response.status_code == 200:
           return response.json()
       else:
           print(f"Error: {response.status_code}")
           print(f"Response: {response.text}")
           return None
           
   except requests.exceptions.RequestException as e:
       print(f"Request failed: {e}")
       return None

def process_file_upload(
   link, cid, content_type, file_path, partner_id, unit_id, cert_path, content_length=None
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
        cert_path=cert_path
    )
    
    if not upload_info:
        print("Failed to get upload URL")
        return None
        
    print("Upload URL created successfully")
    
    # 2. S3에 파일 업로드
    upload_response = upload_to_s3(
        upload_info=upload_info,
        file_path=file_path,
        content_type=content_type
    )
    
    if not upload_response:
        print("Failed to upload file to S3")
        return None
        
    print("File uploaded to S3 successfully")
    
    # 3. Signed URL 획득
    filename = os.path.basename(file_path)
    signed_url = get_signed_url(
        link=link,
        object_id=upload_info['object_id'],
        cid=cid,
        partner_id=partner_id,
        unit_id=unit_id,
        filename=filename,
        content_type=content_type,
        cert_path=cert_path
    )
    
    if not signed_url:
        print("Failed to get signed URL")
        return None
        
    print("Signed URL obtained successfully")
    return signed_url

