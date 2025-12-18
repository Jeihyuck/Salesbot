import sys

sys.path.append("/www/alpha/")

import os
import requests
import time
import json
import urllib.parse

from apps.rubicon_v3.__function.__django_cache import DjangoCacheClient, CacheKey

from alpha.settings import VITE_OP_TYPE, VITE_COUNTRY

cache = DjangoCacheClient()


PRD_ENDPOINT = "https://siis-svc.samsungif.net/svc/kr/gcs_chatbot_svc_agent_connector_kor_150/1.0/agent-messages"
STG_ENDPOINT = "https://siis-svcdev.samsungif.net/svc/kr/gcs_chatbot_svc_agent_connector_kor_150/1.0/agent-messages"

SIIS_TOKEN_ENDPOINT = {
    "DEV": "https://siis-svcdev.samsungif.net/oauth2/token",
    "STG": "https://siis-svcdev.samsungif.net/oauth2/token",
    "PRD": "https://siis-svc.samsungif.net/oauth2/token",
}


def get_svc_siis_token():
    """
    Function to get the SIIS token for UK.
    """
    full_token = cache.get(
        CacheKey.siis_rubicon_svc_api_key(VITE_COUNTRY, VITE_OP_TYPE)
    )
    access_token = None
    if full_token:
        access_token = full_token.get("access_token")
    else:
        # If no token is found, fetch a new one
        access_token = get_svc_siis_access_token()

    return access_token


def get_svc_siis_access_token():
    """
    Function to get the SIIS access token for RUBICON SVC.
    """
    payload = {
        "grant_type": "password",
        "username": os.environ.get("SIIS_RUBICON_SVC_USERNAME"),
        "password": os.environ.get("SIIS_RUBICON_SVC_PASSWORD"),
        "client_id": os.environ.get("SIIS_RUBICON_SVC_CLIENT_ID"),
        "client_secret": os.environ.get("SIIS_RUBICON_SVC_CLIENT_SECRET"),
    }

    payload = urllib.parse.urlencode(payload)

    headers = {"Content-Type": "application/x-www-form-urlencoded"}

    response = requests.post(
        SIIS_TOKEN_ENDPOINT[VITE_OP_TYPE], data=payload, headers=headers
    )

    # Check if the response is successful
    # If successful, store the token in the cache
    if response.status_code == 200:
        cache.store(
            CacheKey.siis_rubicon_svc_api_key(VITE_COUNTRY, VITE_OP_TYPE),
            response.json(),
            60 * 60 * 24 * 1,  # 1 day
        )
        return response.json().get("access_token")
    else:
        return None


def cs_ai_agent(query, message_history):
    """
    Function to handle cs related queries queries using the CS AI AGENT.
    Args:
        query (str): The user query to be processed.
        message_history (list): The history of messages in the conversation.
    Returns:
        dict: The JSON response from the CS AI AGENT.
        str: The content of the response if available, otherwise None.
        str: An error message if the request fails or if no content is found.
    """
    # Get the proper endpoint based on the environment
    url = STG_ENDPOINT
    if VITE_OP_TYPE == "PRD":
        url = PRD_ENDPOINT

    # Get the proper token based on the environment
    siis_token = get_svc_siis_token()

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {siis_token}",
    }

    # Prepare the contents field from the message history
    contents = []
    for message in message_history:
        if message.get("role") == "user":
            contents.append(
                f"USER: {next(item.get('text') for item in message.get('content') if item.get('type') == 'text')}"
            )
        else:
            contents.append(f"AI: {message.get('content')}")

    # Add the user query to the contents
    contents.append(f"USER: {query}")

    body = {
        "agentId": "0197bf84-5594-76be-b2ce-9ed290e166b2",
        "contents": contents,
        "isStream": False,
        "extraParams": {"channel": "rubicon"},
    }

    response = requests.post(url, headers=headers, json=body, timeout=120)
    if response.status_code != 200:
        return {
            "data": {},
            "response": None,
            "message": f"Error: {response.status_code} - {response.text}",
        }

    # Parse the JSON response
    response_json = response.json()

    # Check if the response succeeded
    if not response_json.get("content"):
        return {
            "data": {},
            "response": None,
            "message": "No content found in the response",
        }

    return {
        "data": response_json,
        "response": response_json["content"],
        "message": None,
    }


def cs_ai_agent_stream(query, message_history):
    """
    Function to handle cs related queries queries using the CS AI AGENT with streaming.
    Args:
        query (str): The user query to be processed.
        message_history (list): The history of messages in the conversation.
    Yields:
        str: Chunks of the response content as they are received.
    """
    # Get the proper endpoint based on the environment
    url = STG_ENDPOINT
    if VITE_OP_TYPE == "PRD":
        url = PRD_ENDPOINT

    # Get the proper token based on the environment
    siis_token = get_svc_siis_token()

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {siis_token}",
    }

    # Prepare the contents field from the message history
    contents = []
    for message in message_history:
        if message.get("role") == "user":
            contents.append(f"USER: {message.get('content')}")
        else:
            contents.append(f"AI: {message.get('content')}")

    # Add the user query to the contents
    contents.append(f"USER: {query}")

    body = {
        "agentId": "0197bf84-5594-76be-b2ce-9ed290e166b2",
        "contents": contents,
        "isStream": True,
        "extraParams": {"channel": "rubicon"},
    }

    with requests.post(url, headers=headers, json=body, stream=True, timeout=120) as r:
        if r.status_code != 200:
            error_msg = f"Error: {r.status_code} - {r.text}"
            if VITE_OP_TYPE == "PRD":
                error_msg = "Error: Failed to connect to the CS AI Agent service."
            raise Exception(error_msg)

        # Stream the response line by line
        for line in r.iter_lines():
            # If line is empty skip it
            if not line:
                continue

            # If line is not bytes raise an error
            if not isinstance(line, bytes):
                error_msg = (
                    f"Error: Invalid line type received in stream - {type(line)}"
                )
                if VITE_OP_TYPE == "PRD":
                    error_msg = "Error: Invalid line type received in stream."
                raise Exception(error_msg)

            # Decode the line
            decoded_line = line.decode("utf-8")

            # If decoded line does not start with "data: " raise an error
            if not decoded_line.startswith("data:"):
                error_msg = f"Error: Invalid line received in stream - {decoded_line}"
                if VITE_OP_TYPE == "PRD":
                    error_msg = "Error: Invalid line received in stream."
                raise Exception(error_msg)

            # If the decoded line is only "data: ", skip it
            if decoded_line.strip() == "data:":
                continue

            # Parse the JSON from the line
            try:
                data = json.loads(decoded_line[5:])  # Remove "data:" prefix
            except json.JSONDecodeError:
                error_msg = f"Error: Invalid JSON received in stream - {decoded_line}"
                if VITE_OP_TYPE == "PRD":
                    error_msg = "Error: Invalid JSON received in stream."
                raise Exception(error_msg)

            # If content is not in data, raise an error
            if "content" not in data:
                error_msg = f"Error: No content found in the stream data - {data}"
                if VITE_OP_TYPE == "PRD":
                    error_msg = "Error: No content found in the stream data."
                raise Exception(error_msg)

            # If response_code is not in data, raise an error
            if "response_code" not in data:
                error_msg = f"Error: No response_code found in the stream data - {data}"
                if VITE_OP_TYPE == "PRD":
                    error_msg = "Error: No response_code found in the stream data."
                raise Exception(error_msg)

            # If the response_code is null, skip this chunk
            if data["response_code"] is not None:
                continue

            # If content is "Stream closed" skip it (It's the last message)
            if data["content"].strip() == "Stream closed":
                continue

            yield data["content"]


if __name__ == "__main__":
    import django

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "alpha.settings")
    django.setup()

    query = "공기청정기에서 지지직 소음과 스파크가 발생해요."
    message_history = []

    start_time = time.time()
    cs_data = cs_ai_agent(query, message_history)
    print(f"Time taken: {time.time() - start_time} seconds")
    print(cs_data.get("data", {}).get("content"))
