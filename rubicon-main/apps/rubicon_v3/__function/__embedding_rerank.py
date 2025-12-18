import sys

sys.path.append("/www/alpha")

import time
import numpy as np
import pandas as pd

from alpha import __log
from typing import Union, List

import django

django.setup()
from apps.rubicon_v3.__function.__utils import clean_chunk, retry_function

from apps.__protobuf.alpha_grpc_stub import grpc_stub_function


def baai_embedding(text: Union[str, List[str]], message_id) -> np.ndarray:
    """
    BAAI bge-m3를 사용하여 단일 문자열 또는 문자열 목록에 대한 임베딩을 가져옵니다.

    Args:
        text (Union[str, List[str]]): 임베딩할 입력 텍스트 또는 텍스트 목록.
        message_id (str): 메시지 ID.

    Returns:
        np.ndarray: 임베딩의 Numpy 배열.
    """
    # Convert single string to list if needed
    if isinstance(text, str):
        text = [text]

    query_dict = {"model": "bge-m3", "sentence_list": text}

    def grpc_call():
        grpc_return = grpc_stub_function(
            "embedding_gpu", "bert", "embedding", query_dict
        )
        if "data" not in grpc_return:
            raise ValueError("Missing 'data' in grpc response")
        return grpc_return["data"]

    # Retry the entire grpc_call, including extracting "data"
    embeddings = retry_function(grpc_call, max_retries=3, delay=0.2)

    return embeddings


def chunk_text(text, chunk_size=512, overlap=128, skip_cleaning=False):
    """
    - chunk_size 문자 크기로 나누되 overlap 유지
    - 다음 chunk가 이전 chunk의 마지막 overlap 문자를 포함하도록 함
    """
    # First clean the chunk
    if not skip_cleaning:
        cleaned_text = clean_chunk(text)
    else:
        cleaned_text = text

    chunks = []
    for i in range(0, len(cleaned_text), chunk_size - overlap):
        chunk = cleaned_text[i : i + chunk_size]
        chunks.append(chunk)

    return chunks


def rerank_db_results(
    user_query: str,
    df: pd.DataFrame,
    text_column: str,
    top_k: int = 5,
    score_threshold: float = -10,
    skip_threshold: bool = False,
    skip_cleaning: bool = False,
    multiple_cols: bool = False,
) -> pd.DataFrame:
    if df.empty:
        return df

    if not multiple_cols:
        # Create a data-chunk index map and a dataframe of each chunk
        chunk_list = []
        index_map = {}
        for idx, data in df[text_column].items():  # Changed from iteritems() to items()
            chunks = chunk_text(data, skip_cleaning=skip_cleaning)
            for chunk_idx, chunk in enumerate(chunks):
                index_map[len(index_map)] = (idx, chunk_idx)
                chunk_list.append(chunk)

    else:
        # Handle multiple columns by concatenating their values
        chunk_list = []
        title_list = []
        index_map = {}
        for idx, row in df.iterrows():
            chunks = chunk_text(row[text_column], skip_cleaning=skip_cleaning)
            for chunk_idx, chunk in enumerate(chunks):
                if chunk.strip() != "":
                    index_map[len(index_map)] = (idx, chunk_idx)
                    chunk_list.append(chunk)
                    title_list.append(row["title"])
    # Get reranker scores
    query_dict = {
        "model": "reranker",
        "text_pairs": [[user_query, chunk] for chunk in chunk_list],
    }

    def grpc_call():
        grpc_return = grpc_stub_function(
            "embedding_gpu", "bert", "reranker", query_dict
        )
        if "data" not in grpc_return:
            raise ValueError("Missing 'data' in grpc response")
        return grpc_return["data"]

    reranker_scores = retry_function(grpc_call, max_retries=3, delay=0.2)
    # Add scores to dataframe
    if not multiple_cols:
        df_chunk_scored = pd.DataFrame(
            {"chunk": chunk_list, "reranker_score": reranker_scores}
        )
    else:
        df_chunk_scored = pd.DataFrame(
            {
                "chunk": chunk_list,
                "reranker_score": reranker_scores,
                "title": title_list,
            }
        )

    # Add chunk_id to track original position in index_map
    df_chunk_scored["chunk_id"] = list(range(len(chunk_list)))

    # Apply threshold filtering only if skip_threshold is False
    if skip_threshold:
        df_chunk_ranked = df_chunk_scored.sort_values(
            "reranker_score", ascending=False
        ).head(top_k)
    else:
        df_chunk_ranked = (
            df_chunk_scored[df_chunk_scored["reranker_score"] >= score_threshold]
            .sort_values("reranker_score", ascending=False)
            .head(top_k)
        )
    # Return an empty DataFrame if df_chunk_ranked is empty
    if df_chunk_ranked.empty:
        return pd.DataFrame()

    # Merge the chunk scores back to the original dataframe
    result_rows = []

    # For each ranked chunk
    for _, row in df_chunk_ranked.iterrows():
        chunk = row["chunk"]
        chunk_id = row["chunk_id"]  # Use the chunk_id to find original index
        original_idx, _ = index_map[chunk_id]

        # Get the original row and make a copy
        original_row = df.loc[original_idx].copy()

        # Replace the text with the chunk

        if multiple_cols:
            # Add the title to the row if multiple columns are used
            if row.get("title", ""):
                title = row.get("title", "")
            else:
                title = ""
            original_row[text_column] = title + ": " + chunk

        # Add the reranker score to the row
        original_row["reranker_score"] = row["reranker_score"]

        # Add to the list of result rows
        result_rows.append(original_row)

    # Create the final DataFrame
    result_df = pd.DataFrame(result_rows)
    return result_df


# def rerank_db_results(
#     user_query: str,
#     df: pd.DataFrame,
#     text_column: str = "intelligence",
#     top_k: int = 5,
#     score_threshold: float = -10,
#     skip_threshold: bool = False,
# ) -> pd.DataFrame:
#     """
#     사용자 쿼리를 기반으로 BAAI 리랭커를 사용하여 데이터베이스 결과를 리랭크합니다.

#     Args:
#         user_query (str): 원본 사용자 쿼리.
#         df (pd.DataFrame): 데이터베이스 결과가 포함된 DataFrame.
#         text_column (str, optional): 재랭크할 텍스트가 포함된 열 이름.
#         top_k (int, optional): 반환할 상위 결과 수.
#         score_threshold (float, optional): 결과에 포함할 최소 재랭커 점수 (0과 1 사이).
#         skip_threshold (bool, optional): True인 경우 임계값 필터링을 건너뜁니다.

#     Returns:
#         pd.DataFrame: 재랭커 점수로 정렬된 DataFrame, 임계값 이상인 결과만 포함 (skip_threshold가 True인 경우 제외).
#     """
#     if df.empty:
#         return df

#     # Create pairs of [query, text] for reranking
#     text_pairs = [[user_query, text] for text in df[text_column].tolist()]

#     # Get reranker scores
#     query_dict = {"model": "reranker", "text_pairs": text_pairs}

#     def grpc_call():
#         grpc_return = grpc_stub_function(
#             "embedding_gpu", "bert", "reranker", query_dict
#         )
#         if "data" not in grpc_return:
#             raise ValueError("Missing 'data' in grpc response")
#         return grpc_return["data"]

#     reranker_scores = retry_function(grpc_call, max_retries=3, delay=0.2)

#     # Add scores to dataframe
#     df_scored = df.copy()
#     df_scored["reranker_score"] = reranker_scores

#     # Apply threshold filtering only if skip_threshold is False
#     if skip_threshold:
#         df_ranked = df_scored.sort_values("reranker_score", ascending=False).head(top_k)
#     else:
#         df_ranked = (
#             df_scored[df_scored["reranker_score"] >= score_threshold]
#             .sort_values("reranker_score", ascending=False)
#             .head(top_k)
#         )

#     # Return an empty DataFrame if df_ranked is empty
#     if df_ranked.empty:
#         return pd.DataFrame()

#     return df_ranked


def rerank_list(reference_text: str, lst: list) -> list:
    """
    사용자 쿼리를 기반으로 BAAI 재랭커를 사용하여 목록 결과를 재랭크합니다.

    Args:
        reference_text (str): 참조 텍스트.
        list (list): 재랭크할 텍스트 목록.

    Returns:
        list: 재랭크된 텍스트 목록.
    """
    # Create pairs of [query, text] for reranking
    text_pairs = [[reference_text, text] for text in lst]

    # Get reranker scores
    query_dict = {"model": "reranker", "text_pairs": text_pairs}
    # import pprint as p
    reranker_scores = grpc_stub_function(
        "embedding_gpu", "bert", "reranker", query_dict
    )
    # print("reranker_scores", 'data' in reranker_scores )
    # p.pprint(reranker_scores)
    reranker_scores = reranker_scores["data"]

    zip_list = []
    for index, score in enumerate(reranker_scores):
        zip_list.append({"text": lst[index], "score": score})

    sorted_data_with_score = sorted(zip_list, key=lambda x: x["score"], reverse=True)

    sorted_data_with_no_score = []
    for item in sorted_data_with_score:
        sorted_data_with_no_score.append(item["text"])

    return sorted_data_with_no_score, sorted_data_with_score


def main():
    """
    baai_embedding 함수를 테스트합니다.
    """
    # print(len(baai_embedding("안녕하세요", "")))
    # print(
    #     len(baai_embedding(["안녕하세요", "안녕하세요"], "")),
    #     len(baai_embedding(["안녕하세요", "안녕하세요"], "")[0]),
    # )

    df = pd.DataFrame(
        [
            {
                "text_data": "안녕하세요. 반갑습니다. 오늘은 날씨가 좋네요.",
            },
            {
                "text_data": "안녕하세요. 반갑습니다. 오늘은 날씨가 좋네요.",
            },
            {
                "text_data": "testing",
            },
            {
                "text_data": "testing",
            },
        ]
    )
    df1 = rerank_db_results("테스트", df, "text_data", 10, -10)

    print(df1)


if __name__ == "__main__":
    main()
