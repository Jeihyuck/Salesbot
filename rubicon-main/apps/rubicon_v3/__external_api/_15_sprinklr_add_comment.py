import sys

sys.path.append("/www/alpha/")

import os
import time
import requests
import urllib.parse

from apps.rubicon_v3.__function.__django_cache import DjangoCacheClient, CacheKey
from apps.rubicon_v3.__external_api.__apiRequest import apiHandler

from alpha.settings import VITE_OP_TYPE, VITE_COUNTRY

cache = DjangoCacheClient()


UK_COMMENT_ENDPOINT = {
    "STG": "https://eudev.ipaas.samsung.com/sec/eu/sprinklr_eu_createcomment_rubicon/1.0/comment/CASE/{CaseId}",
    "PRD": "https://eu.ipaas.samsung.com/sec/eu/sprinklr_eu_createcomment_rubicon/1.0/comment/CASE/{CaseId}",
}
KR_COMMENT_ENDPOINT = {
    "STG": "http://ipaas-scadev.sec.samsung.net/sec/kr/kr_epromoter_createcomment/1.0/comment/CASE/{CaseId}",
    "PRD": "http://ipaas-sca.sec.samsung.net/sec/kr/kr_epromoter_createcomment/1.0/comment/CASE/{CaseId}",
}
SIIS_TOKEN_ENDPOINT = {
    "STG": "https://eudev.ipaas.samsung.com/oauth2/token",
    "PRD": "https://eu.ipaas.samsung.com/oauth2/token",
}


def get_uk_siis_token():
    """
    Function to get the SIIS token for UK.
    """
    full_token = cache.get(CacheKey.siis_rubicon_uk_api_key(VITE_COUNTRY, VITE_OP_TYPE))
    access_token = None
    if full_token:
        access_token = full_token.get("access_token")
    else:
        # If no token is found, fetch a new one
        access_token = get_uk_siis_access_token()

    return access_token


def get_uk_siis_access_token():
    """
    Function to get the SIIS access token for UK.
    """
    payload = {
        "grant_type": "password",
        "username": os.environ.get("SIIS_USERNAME_GB"),
        "password": os.environ.get(f"SIIS_RUBICON_UK_PASSWORD_{VITE_OP_TYPE}"),
        "client_id": os.environ.get(f"SIIS_RUBICON_UK_CLIENT_ID_{VITE_OP_TYPE}"),
        "client_secret": os.environ.get(
            f"SIIS_RUBICON_UK_CLIENT_SECRET_{VITE_OP_TYPE}"
        ),
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
            CacheKey.siis_rubicon_uk_api_key(VITE_COUNTRY, VITE_OP_TYPE),
            response.json(),
            60 * 60 * 24 * 1,  # 1 day
        )
        return response.json().get("access_token")
    else:
        return None


def add_comment(session_id, comment):
    """
    Function to add a comment to a session in Sprinklr.

    Args:
        session_id (str): The ID of the session to which the comment will be added.
        comment (str): The comment text to be added.

    Returns:
        dict: The JSON response from the Sprinklr API.
    """
    endpoint = None
    headers = {
        "Content-Type": "application/json",
        "iPaaS-Backend-Authorization": f"Bearer {os.environ.get(f'SPRINKLR_IPAAS_BACKEND_AUTHORIZATION_{VITE_OP_TYPE}')}",
        "Key": os.environ.get(f"SPRINKLR_ADD_COMMENT_KEY_{VITE_OP_TYPE}"),
    }

    # Determine the endpoint based on the country code and environment
    if VITE_COUNTRY == "UK":
        endpoint = UK_COMMENT_ENDPOINT[VITE_OP_TYPE]

        # Need to generate the Bearer token dynamically for UK
        # Using a separate api handler for UK
        siis_token = get_uk_siis_token()

        headers["Authorization"] = f"Bearer {siis_token}"
    if VITE_COUNTRY == "KR":
        endpoint = KR_COMMENT_ENDPOINT[VITE_OP_TYPE]

        # Need to generate the Bearer token dynamically for KR
        api_handler = apiHandler(VITE_COUNTRY)
        siis_token = api_handler.get_siis_token_sync()

        headers["Authorization"] = f"Bearer {siis_token}"

    # Format the endpoint with the session ID
    endpoint = endpoint.format(CaseId=session_id)

    # Prepare the payload
    payload = {"text": comment}

    response = requests.post(endpoint, json=payload, headers=headers)

    print(f"Response Status Code: {response.status_code}")

    if response.status_code == 200:
        return True, response.json()
    else:
        return False, {"error": response.text}


if __name__ == "__main__":
    # Example usage
    session_id = "113727"
    comment = "This is a test comment 234."
    success, response = add_comment(session_id, comment)
    print(f"Success: {success}, Response: {response}")
