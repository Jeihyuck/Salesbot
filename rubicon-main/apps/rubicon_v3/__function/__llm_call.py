import sys

sys.path.append("/www/alpha/")

import os
import openai
import asyncio
import json
import tiktoken

from typing import Union, Dict
from pydantic import BaseModel
from openai import AzureOpenAI, AsyncAzureOpenAI, OpenAI

from apps.rubicon_v3.__function.__prompts import chunk_evaluation

from alpha.settings import (
    VITE_OP_TYPE,
    AZURE_OPENAI_API_KEY,
    AZURE_OPENAI_API_ENDPOINT,
    AZURE_OPENAI_API_VERSION,
)

OPENAI_SEARCH_GPT_API_KEY = os.environ.get("SEARCH_GPT_API_KEY")


def open_ai_call_structured(
    model_name,
    messages,
    response_format,
    temperature: float = openai.NOT_GIVEN,
    top_p: float = openai.NOT_GIVEN,
    seed: int = openai.NOT_GIVEN,
) -> Union[bool, BaseModel]:
    """
    구조화된 OpenAI 호출을 수행합니다.

    Args:
        model_name (str): 모델 이름.
        messages (list): 메시지 목록.
        temperature (float): 온도.
        top_p (float): 상위 p.
        response_format (str): 응답 형식.
        seed (int, optional): 시드 값. 기본값은 openai.NOT_GIVEN.

    Returns:
        Union[bool, BaseModel]: 응답 결과.
    """
    openai_client = AzureOpenAI(
        api_key=AZURE_OPENAI_API_KEY,
        api_version=AZURE_OPENAI_API_VERSION,
        azure_endpoint=AZURE_OPENAI_API_ENDPOINT,
    )

    response = openai_client.beta.chat.completions.parse(
        model=model_name,
        messages=messages,
        temperature=temperature,
        top_p=top_p,
        seed=seed,
        response_format=response_format,
    )

    if response.choices[0].message.refusal:
        raise ValueError(
            "The model refused to answer the question. Please check the input messages and try again."
        )
    else:
        return response.choices[0].message.parsed.model_dump()


def save_messages_to_file(messages, filename):
    with open(f"/www/alpha/__log/final_response_messages/{str(filename)}", "w") as file:
        json.dump(messages, file, ensure_ascii=False, indent=4)


encoding = tiktoken.encoding_for_model("gpt-4o")


def open_ai_call_stream(
    model_name,
    messages,
    temperature: float,
    seed: int,
    stream: bool,
    max_output_tokens: int = openai.NOT_GIVEN,
):
    """
    스트리밍 OpenAI 호출을 수행합니다.

    Args:
        model_name (str): 모델 이름.
        messages (list): 메시지 목록.
        temperature (float): 온도.
        seed (int): 시드 값.
        stream (bool): 스트리밍 여부.
        max_output_tokens (int, optional): 최대 출력 토큰 수.

    Yields:
        str: 응답 결과.
    """
    FALL_BACK_GPT_4_1_TPM = "gpt-4.1-tpm"
    FALL_BACK_GPT_4_1_MINI_TPM = "gpt-4.1-mini-tpm"

    openai_client = AzureOpenAI(
        api_key=AZURE_OPENAI_API_KEY,
        api_version=AZURE_OPENAI_API_VERSION,
        azure_endpoint=AZURE_OPENAI_API_ENDPOINT,
        max_retries=0,  # Disable retries to handle rate limits manually
    )

    try:
        response = openai_client.chat.completions.create(
            model=model_name,
            messages=messages,
            temperature=temperature,
            seed=seed,
            stream=stream,
            max_completion_tokens=max_output_tokens,
        )
    except openai.RateLimitError as e:
        # For environments where we want to use a fallback model
        if VITE_OP_TYPE in ["STG", "PRD"]:
            # Use the fallback model if the rate limit is hit
            if model_name == "gpt-4.1-mini":
                model_name = FALL_BACK_GPT_4_1_MINI_TPM
            elif model_name == "gpt-4.1":
                model_name = FALL_BACK_GPT_4_1_TPM
            # If the model is not one of the above, use gpt 4o mini tpm
            else:
                model_name = FALL_BACK_GPT_4_1_MINI_TPM

            # Retry the request with the fallback model
            response = openai_client.chat.completions.create(
                model=model_name,
                messages=messages,
                temperature=temperature,
                seed=seed,
                stream=stream,
                max_completion_tokens=max_output_tokens,
            )

        # For other environments, raise the error
        else:
            raise

    num_tokens = len(encoding.encode(str(messages)))
    yield f"### LLM CALL META : Token Count : {num_tokens}"

    for chunk in response:
        if len(chunk.choices) > 0 and chunk.choices[0].delta.content is not None:
            yield chunk.choices[0].delta.content


def open_ai_call(
    model_name,
    messages,
    temperature: float,
    seed: int,
    stream: bool,
    message_id,
    top_p=openai.NOT_GIVEN,
    pipeline_start_time=None,
):
    """
    OpenAI 호출을 수행합니다.

    Args:
        model_name (str): 모델 이름.
        messages (list): 메시지 목록.
        temperature (float): 온도.
        stream (bool): 스트리밍 여부.
        pipeline_start_time (float, optional): 파이프라인 시작 시간.
        top_p (float, optional): 상위 p.

    Returns:
        str: 응답 결과.
    """
    openai_client = AzureOpenAI(
        api_key=AZURE_OPENAI_API_KEY,
        api_version=AZURE_OPENAI_API_VERSION,
        azure_endpoint=AZURE_OPENAI_API_ENDPOINT,
    )

    response = openai_client.chat.completions.create(
        model=model_name,
        messages=messages,
        temperature=temperature,
        top_p=top_p,
        seed=seed,
        stream=stream,
    )

    return response.choices[0].message.content


async def _eval_chunk(
    sem: asyncio.Semaphore,
    query: str,
    chunk: Dict,
    idx: int,
    similarity_check=False,
    model_name="gpt-4.1",
) -> tuple[int, int]:
    openai_client = AsyncAzureOpenAI(
        api_key=AZURE_OPENAI_API_KEY,
        api_version=AZURE_OPENAI_API_VERSION,
        azure_endpoint=AZURE_OPENAI_API_ENDPOINT,
    )

    prompt = chunk_evaluation.PROMPT_TEMPLATE.format(query=query, context=chunk)
    if similarity_check:
        prompt = chunk_evaluation.PROMPT_TEMPLATE_SIM.format(
            query=query, ground_truth=chunk[0], response=chunk[1]
        )
    async with sem:
        try:
            resp = await openai_client.chat.completions.create(
                model=model_name,  # ← Azure OpenAI requires `engine=...`
                messages=[
                    {
                        "role": "system",
                        "content": "You are a strict relevance evaluator.",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.0,
                max_tokens=10 if not similarity_check else 100,
            )

            score = resp.choices[0].message.content.strip().upper()
        except Exception as e:
            # catch everything so you see the error
            print(e)
            score = 0
    return idx, score
