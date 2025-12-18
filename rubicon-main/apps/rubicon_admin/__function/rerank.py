from apps.__protobuf.alpha_grpc_stub import grpc_stub_function
import pandas as pd
import sys

sys.path.append("/www/alpha/")
from alpha import __log


def calculate_rerank_score(
    user_query: str, table_data: dict, text_column: str = "intelligence"
) -> dict:
    """
    Rerank database results using BAAI reranker based on user query

    Args:
        user_query: The original user query
        table_ata: query result
        text_column: Column name containing the text to rerank against

    Returns:
        DataFrame sorted by reranker score
    """
    text_pairs = []
    for item in table_data:
        # ic(item)
        text_pairs.append([str(user_query), str(item[text_column])])

    # __log.debug(text_pairs)

    # # Create pairs of [query, text] for reranking
    # text_pairs = [[user_query, text] for text in df[text_column].tolist()]

    # # Get reranker scores
    query_dict = {"model": "reranker", "text_pairs": text_pairs}
    rerank_scores = grpc_stub_function("embedding_gpu", "bert", "reranker", query_dict)
    # ic(rerank_scores)
    rerank_scores = grpc_stub_function("embedding_gpu", "bert", "reranker", query_dict)[
        "data"
    ]
    # ic(rerank_scores)

    for index, item in enumerate(table_data):
        # ic(index)
        table_data[index]["rerank_score"] = round(rerank_scores[index], 4)

    sorted_table_data = sorted(
        table_data, key=lambda x: x["rerank_score"], reverse=True
    )
    return sorted_table_data


def calculate_rerank_score_multiline(
    user_query: str, table_data: dict, text_column: str = "intelligence"
) -> dict:
    """
    Rerank database results using BAAI reranker based on user query

    Args:
        user_query: The original user query
        table_ata: query result
        text_column: Column name containing the text to rerank against

    Returns:
        DataFrame sorted by reranker score
    """

    df = pd.DataFrame(table_data)
    df2 = df.drop("related_question", axis=1).join(
        df.related_question.str.split("\n", expand=True)
        .stack()
        .reset_index(drop=True, level=1)
        .rename("related_question")
    )
    df2 = df2.reset_index(drop=True)

    text_pairs = []
    for _, _row in df2.iterrows():
        text_pairs.append([user_query, _row["related_question"]])

    query_dict = {"model": "reranker", "text_pairs": text_pairs}

    rerank_scores = grpc_stub_function("embedding_gpu", "bert", "reranker", query_dict)[
        "data"
    ]

    df2["rerank_score"] = rerank_scores
    df2 = df2.sort_values(by="rerank_score", ascending=False)
    df2 = df2.groupby(["id", "title", "text"])[["rerank_score"]].max().reset_index()
    df2 = df2.sort_values(by="rerank_score", ascending=False)

    return df2.to_dict(orient="records")
