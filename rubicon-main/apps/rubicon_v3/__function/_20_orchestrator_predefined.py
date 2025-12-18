import sys

sys.path.append("/www/alpha/")

import os
import django
from django.db import connection

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "alpha.settings")
django.setup()

import uuid

import pandas as pd
import numpy as np

from apps.rubicon_v3.__function import __embedding_rerank
from apps.rubicon_v3.models import Predefined_RAG


def _predefined_query_retriever(
    query: str, embeddings, country_code, channel, message_id
):
    """
    벡터 유사성과 재정렬을 사용하여 사전 정의된 답변을 검색하는 함수
    :param query: 사용자 질의
    :param embeddings: 임베딩 리스트
    :param country_code: 국가 코드
    :param message_id: 메시지 ID
    :return: 재정렬된 결과 DataFrame
    """
    embeddings = list(embeddings)

    # predefined answer 테이블 조건 부여 후 전체 추출
    with connection.cursor() as cursor:
        cursor.execute(
            """SELECT
                    query,
                    category,
                    predefined_answer,
                    channel
                FROM rubicon_v3_predefined_answer
                WHERE country_code = %s
                AND (channel = %s OR channel = '*')
                ORDER BY embedding <=> %s::vector
                LIMIT 10;""",
            [country_code, channel, embeddings],
        )
        results = cursor.fetchall()

    if not results:
        return pd.DataFrame()

    results = pd.DataFrame(
        results, columns=["query", "category", "predefined_answer", "channel"]
    )

    # query 필드 내 '\n' 기준으로 query 분리
    results["query_list"] = results["query"].str.split("\n")
    results = results.explode("query_list", ignore_index=True)
    results = results.drop(columns="query").rename(columns={"query_list": "query"})

    # 분리된 query 별 embedding 생성
    query_embed_ls = []
    for i, row in results.iterrows():
        message_id = str(uuid.uuid4())
        query_embed_ls.append(
            __embedding_rerank.baai_embedding(row["query"], message_id)[0]
        )
    results["query_embedding"] = query_embed_ls

    # 원본 쿼리와 euclidean distance^2(postgresql pgvector 기본 벡터 계산법) 계산 후 최근접 predefined 추출
    emb_matrix = np.vstack(results["query_embedding"].values)
    euclidean_dists = np.linalg.norm(emb_matrix - np.array(embeddings), axis=1)
    results["euclidean_dists"] = euclidean_dists * euclidean_dists

    # euclidean distance^2 기준 0.14 이하이며 값이 작은 순서로 10개 추출
    top_n = 10
    results = (
        results.loc[results["euclidean_dists"] <= 0.14]
        .nsmallest(top_n, "euclidean_dists")
        .reset_index(drop=True)
    )

    if results.empty:
        return pd.DataFrame()

    df = pd.DataFrame(
        results, columns=["query", "category", "predefined_answer", "channel"]
    )

    # 만일 채널이 일치하는 케이스와 '*' 인 케이스가 같이 존재하는 경우 채널명이 지정되어있는 경우를 우선으로 처리
    channels = df["channel"].unique().tolist()
    if "*" in channels and len(channels) > 1:
        df = df[df["channel"] != "*"]

    df_reranked = __embedding_rerank.rerank_db_results(
        user_query=query, df=df, text_column="query", top_k=1
    )

    if df_reranked.empty:
        return pd.DataFrame()

    return df_reranked


def predefined_rag_retriever(query: str, country_code: str, channel: str, site_cd: str):
    """
    This function grabs all the data from the predefined rag table
    and checks for the include keywords and exclude keywords.
    The table is only meant to be used for events and promotions with certain keywords.
    """
    predefined_rag_data = Predefined_RAG.objects.filter(
        active=True,
        country_code=country_code,
        channel_filter__contains=[channel],
        site_cd=site_cd,
    ).values("matching_rule", "contents")

    # Check if the query matches any of the predefined RAG rules
    predefined_contents = []
    predefined_rag_debug = []
    for item in predefined_rag_data:
        matching_rule = item["matching_rule"]
        include_keywords = [
            kw.lower() for kw in matching_rule.get("include_keywords", [])
        ]
        exclude_keywords = [
            kw.lower() for kw in matching_rule.get("exclude_keywords", [])
        ]
        query = query.lower()

        matched_keyword = None
        for keyword in include_keywords:
            if keyword in query:
                matched_keyword = keyword
                break

        if (
            matched_keyword is not None
            and not any(keyword in query for keyword in exclude_keywords)
            and item["contents"]
        ):
            predefined_contents.append(item["contents"])
            predefined_rag_debug.append(matched_keyword)

    return predefined_contents, predefined_rag_debug


def check_predefined(
    processed_query, embeddings, country_code, channel, site_cd, message_id
):
    """
    사전 정의된 답변을 확인하는 함수
    :param processed_query: 처리된 질의
    :param embeddings: 임베딩 리스트
    :param country_code: 국가 코드
    :param message_id: 메시지 ID
    :return: 결과 딕셔너리
    """
    # Get the predefined query dataframe
    predefined_query_df = _predefined_query_retriever(
        processed_query, embeddings, country_code, channel, message_id
    )

    # Convert the dataframe to a dictionary
    predefined_query_data = predefined_query_df.to_dict(orient="records")

    # Get the predefined rag
    predefined_rag_contents, predefined_rag_debug = predefined_rag_retriever(
        processed_query, country_code, channel, site_cd
    )

    # Check if both predefined_query_data and predefined_rag_contents are empty
    if not predefined_query_data and not predefined_rag_contents:
        return {}, {}

    # Combine the results into a single list of dictionaries
    combined_results = {}
    if predefined_query_data and predefined_query_data[0].get("predefined_answer"):
        # If predefined_query_data is not empty and has a predefined_answer
        combined_results.update(
            {"sample_response": predefined_query_data[0]["predefined_answer"]}
        )

    reference_data = []
    for item in predefined_rag_contents:
        reference_data.append(item)
    combined_results.update({"reference_data": reference_data})

    # Clean up the predefined query data for debugging
    for item in predefined_query_data:
        item.pop("predefined_answer", None)

    return combined_results, {
        "predefined_rag_debug": predefined_rag_debug,
        "predefined_query_debug": predefined_query_data,
    }
