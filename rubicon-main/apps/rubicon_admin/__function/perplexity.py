import sys
import os
import urllib.parse

sys.path.append("/www/alpha/")

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "alpha.settings")

import requests
import json
import pandas as pd
from datetime import datetime
import pytz
from sqlalchemy import create_engine, text
import psycopg2
import pydantic
import uuid
from pgvector.psycopg2 import register_vector
from apps.rubicon_v3.__function.__embedding_rerank import baai_embedding
from apps.rubicon_v3.__function.__llm_call import open_ai_call_structured
from alpha import __log
from tqdm import tqdm

# IMPORTANT: Replace with your actual Perplexity API key
# For production, use environment variables or a secure key management system
# os.getenv("OUTGEN_PROMPT_PATH")
PERPLEXITY_API_KEY = os.getenv("PERPLEXITY_API_KEY")
API_URL = os.getenv("API_URL")
prompt = """## Rules for Samsung Product Search (as of 2025):
- You must only search for Samsung products/function/technology and answer the product limited to **Samsung**.
- Please focus on Samsung's **latest** products when searching products.
- Please provide information only about **officially announced** Samsung products and technologies. 
## Contents Guideline:
- Even if the user asks a question that compares or evaluates Samsung products against competitor brands(e.g., Apple, LG, Huawei, Xiaomi, BOSS, Dell), **do not directly describe or compliment the competitor brands**.
- Even if the user requests it, avoid providing price info, reviews, promotions, or purchase links. If unavoidable, add a short disclaimer.
- Please provide a clear, objective, and informative explanation based on well-known facts or widely accepted knowledge. Avoid personal opinions or speculative content.
- Give me the maximum amount of information possible.
- Please write your answer with no negative words or weakness about Samsung products. (Always positive tone for Samsung products)
## Format Guideline:
- Respond in the language that matches the user’s question.
- Write in a paragraph format.
- Please write your answer without tables, citations, or reference numbers (e.g., [1], [2]). Do not include any citation markers in the response.
- Please write your answer without summary. (Do not summarize contents using the word '정리하자면', '요약하자면', '결론적으로', etc.)
### Assume this response is for an official Samsung website."""
# DB 접속 정보
DB_HOST = os.getenv("POSTGRESQL_IP")
DB_NAME = os.getenv("POSTGRESQL_DB")
DB_USER = os.getenv("POSTGRESQL_ID")
DB_PASSWORD_local = os.getenv("POSTGRESQL_PWD")
encoded_pwd = DB_PASSWORD_local.replace("@", "%40")
DB_PASSWORD = encoded_pwd
DB_PORT = os.getenv("POSTGRESQL_PORT")

engine = create_engine(
    f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)


class AssistantResult(pydantic.BaseModel):
    processed_content: list[str]


def get_perplexity_response(query, model="sonar"):
    """
    Sends a query to the Perplexity API and returns the response.
    Args:
        query (str): The user's query.
        model (str): The Perplexity model to use.
                     Examples: "sonar-medium-online", "sonar-large-online",
                               "llama-3-sonar-small-32k-online", "llama-3-sonar-large-32k-online".
                               Check Perplexity documentation for the latest models.
    Returns:
        dict: The JSON response from the API, or None if an error occurs.
    """
    if not PERPLEXITY_API_KEY or PERPLEXITY_API_KEY == "YOUR_PERPLEXITY_API_KEY_HERE":
        print("Error: Perplexity API key is not set.")
        print(
            "Please open the script and replace 'YOUR_PERPLEXITY_API_KEY_HERE' with your actual key."
        )
        return None
    headers = {
        "Authorization": f"Bearer {PERPLEXITY_API_KEY}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    # Structure of the payload based on Perplexity API documentation
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": prompt},
            {"role": "user", "content": query},
        ],
        # Optional parameters can be added here, for example:
        # "max_tokens": 1000,  # Maximum number of tokens to generate
        "temperature": 0.01,  # Controls randomness (0.0 to 2.0)
        "top_p": 1,
        # "stream": False,    # Set to True for streaming responses
        "web_search_options": {
            "user_location": {"country": "US"},
        },
        "return_images": False,
    }
    print(f"\nSending query to Perplexity API with model: {model}...")
    print(f"Query: {query}")
    try:
        # Make the POST request to the API
        print(f"{len(json.dumps(payload).encode('utf-8'))} bytes input")
        response = requests.post(API_URL, headers=headers, json=payload)
        # Raise an exception for HTTP errors (4xx or 5xx)
        response.raise_for_status()
        # Parse the JSON response
        print(f"{len(json.dumps(response.json()).encode('utf-8'))} bytes response")
        return response.json()
    except requests.exceptions.HTTPError as http_err:
        print(f"HTTP error occurred: {http_err}")
        print(f"Status Code: {response.status_code}")
        try:
            # Attempt to print more detailed error from API response body
            error_details = response.json()
            print(f"API Error Details: {json.dumps(error_details, indent=2)}")
        except json.JSONDecodeError:
            print(f"Response content (not JSON): {response.text}")
    except requests.exceptions.ConnectionError as conn_err:
        print(f"Connection error occurred: {conn_err}")
        print("Please check your internet connection and the API endpoint.")
    except requests.exceptions.Timeout as timeout_err:
        print(f"Timeout error occurred: {timeout_err}")
        print("The request timed out. Try increasing timeout or check API status.")
    except requests.exceptions.RequestException as req_err:
        print(f"An unexpected request error occurred: {req_err}")
    except json.JSONDecodeError:
        print("Error: Failed to decode JSON response from the API.")
        print(
            f"Response content: {response.text if 'response' in locals() else 'No response object'}"
        )
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
    return None


def call_perplexity(query):
    model = "sonar-pro"

    if query:
        # Call the function to get the API response
        # You can change the model here if needed, e.g., model="llama-3-sonar-large-32k-online"
        api_response = get_perplexity_response(query, model=model)
        if api_response:
            print("\n--- Perplexity API Response ---")
            # Pretty print the entire JSON response
            # print(json.dumps(api_response, indent=2))
            # Attempt to extract and print the main answer content
            try:
                # The structure of the response typically has the answer in:
                # choices[0].message.content
                if (
                    api_response.get("choices")
                    and len(api_response["choices"]) > 0
                    and api_response["choices"][0].get("message")
                    and api_response["choices"][0]["message"].get("content")
                ):
                    answer = api_response["choices"][0]["message"]["content"]
                    # print("\nAnswer:")
                    # print(answer)
                    __log.debug("Perplexity response success")
                    return "\n".join(api_response["citations"]), answer
                else:
                    print(
                        "\nCould not extract a direct answer using the expected path."
                    )
                    print("Full response for inspection:")
                    return "Not found", "Not found"
            except (IndexError, KeyError, AttributeError) as e:
                print(f"\nError parsing the response structure: {e}")
                print("Full response for inspection:")
                return "Parse Error", "Not found"
        else:
            print("\nFailed to get a valid response from Perplexity API.")
            return "Not found", "Not found"
    else:
        print("No query entered. Exiting.")


def insert_into_table(
    active, url, content, country, user_query, content_embed, update_tag
):
    kst = pytz.timezone("Asia/Seoul")
    # 1) Connect
    conn = psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD_local,
    )
    register_vector(conn)  # enable vector support
    cur = conn.cursor()

    # DB 접속 정보
    try:
        kst_now = datetime.now(kst)
        insert_sql = """
        INSERT INTO public.rubicon_v3_web_clean_cache
        (active, url, content, created_on, country_code, query, title, clean_content, content_embed, summary, source, update_tag)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        cur.execute(
            insert_sql,
            (
                active,
                url,
                content,
                kst_now,
                country,
                user_query,
                user_query,
                content,
                content_embed,
                content,
                "reference",
                update_tag,
            ),
        )
        conn.commit()
        __log.info(f"Insert Query Run Success")

    except Exception as e:
        __log.info(f"An error occurred: {e}")


def post_process_content(content):
    """
    Post-process the content to remove unwanted characters and clean it up.
    Args:
        content (str): The content to be cleaned.
    Returns:
        str: Cleaned content.
    """

    messages = [
        {
            "role": "system",
            "content": f"""
    ## Role Prompt: Samsung e-Promoter Persona
    - You are a **high-performing, customer-centric sales professional at Samsung Electronics**, dedicated to deeply understanding customers, delivering expert guidance, and maximizing both customer satisfaction and sales conversion.
    - Your primary goal is to review a draft answer generated by an LLM. Your task is to refine this answer before it is shown to the user.
    ## Objectives:
    - Remove or replace the below prohibited content from the draft answer.
        - Any mention regarding to **non-Samsung products**. (e.g, recommendation, comparison, or explanation for the competitor products)
        - **Price, promotion, purchase link, review** about Samsung products.
        - Any **uncertain information, negative statements or implications** about Samsung. (e.g, prediction or explaination for new products, weakness of Samsung products)
        - Any summary, conclusion, value judgment, or closing sentence. (e.g., sentences start with 요약하자면~, 결론적으로~, etc.)
        - Any **URLs or external links**
        - Any tables, citations markers, or reference numbers (e.g., [1], [2]).
    - Preserve the original text except for the prohibited content.
    """,
        },
        {
            "role": "user",
            "content": f"""
    [content for interpretation] : {content}
    """,
        },
    ]

    # Remove unwanted characters and clean up the content
    response = open_ai_call_structured(
        "gpt-4.1-mini", messages, AssistantResult, 0, 0.1, 42
    )

    # print(response)

    cleaned_content = " ".join(response["processed_content"])
    return cleaned_content


if __name__ == "__main__":
    user_query = "키친핏과 프리스탠딩의 차이점"
    country = "KR"
    url, content = call_perplexity(user_query)
    processed_content = post_process_content(content)
    content_embed = baai_embedding(processed_content, None)[0]
    print("original content from perplexity: ", content)
    print("processed content from perplexity: ", processed_content)
