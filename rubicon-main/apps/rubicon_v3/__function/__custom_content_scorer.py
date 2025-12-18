import re
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from rank_bm25 import BM25Okapi
# import Levenshtein
import apps.rubicon_v3.__function.__embedding_rerank as embedding_rerank
import uuid


# 1. Normalization
def normalize(text):
    text = text.lower()
    text = re.sub(r"[^a-z0-9가-힣\s]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


# 2. Tokenization
def whitespace_tokenize(text):
    return normalize(text).split()


# def char_ngrams(text, n):
#     s = normalize(text).replace(" ", "_")
#     return [s[i : i + n] for i in range(len(s) - n + 1)]


# 3. Similarity Metrics 우선 이런 저런 방식을 적었으나 tfidf가 가장 구분이 잘되는 편
# def jaccard(a, b):
#     A, B = set(a), set(b)
#     return len(A & B) / len(A | B) if A | B else 0.0


# def dice(a, b):
#     A, B = set(a), set(b)
#     return 2 * len(A & B) / (len(A) + len(B)) if (len(A) + len(B)) else 0.0


# def levenshtein_similarity(a, b):
#     s1 = "".join(a)
#     s2 = "".join(b)
#     max_len = max(len(s1), len(s2), 1)
#     return 1 - Levenshtein.distance(s1, s2) / max_len


def tfidf_cosine(doc, query):
    vectorizer = TfidfVectorizer(analyzer="char_wb", ngram_range=(3, 5))
    tfidf = vectorizer.fit_transform([doc, query])
    return cosine_similarity(tfidf[0:1], tfidf[1:2])[0, 0]


def bm25_score(doc, query):
    tokenized_docs = [whitespace_tokenize(doc)]
    bm25 = BM25Okapi(tokenized_docs)
    return bm25.get_scores(whitespace_tokenize(query))[0]


# 4. Embedding-based Metric
def embedding_similarity(doc, query):
    message_id = str(uuid.uuid4())
    embs_doc = embedding_rerank.baai_embedding(doc, message_id)[0]
    message_id = str(uuid.uuid4())
    embs_query = embedding_rerank.baai_embedding(query, message_id)[0]
    return cosine_similarity(
        np.array(embs_doc).reshape(1, -1), np.array(embs_query).reshape(1, -1)
    )[0][0]


# 5. Two-stage Pipeline
# bm25 api, tfidf, baai embedding을 혼합하여 점수 산출
# embedding만 사용할 경우 상대 거리가 짧게 산출되어 점수 폭을 벌리는 용도로 기타 지표 사용
def two_stage_score(
    query, df, text_column, top_k=20, weights=None, skip_cleaning: bool = False
):
    """
    docs: list of documents
    query: string
    top_k: number of candidates to re-rank
    weights: dict of weights for metrics: {'bm25':, 'tfidf':, 'embed':}
    """

    # Create a data-chunk index map and a dataframe of each chunk
    chunk_list = []
    index_map = {}
    for idx, data in df[text_column].items():  # Changed from iteritems() to items()
        chunks = embedding_rerank.chunk_text(data, skip_cleaning=skip_cleaning)
        for chunk_idx, chunk in enumerate(chunks):
            index_map[len(index_map)] = (idx, chunk_idx)
            chunk_list.append(chunk)

    # First stage: BM25
    tokenized = [whitespace_tokenize(d) for d in chunk_list]
    bm25 = BM25Okapi(tokenized)
    q_tokens = whitespace_tokenize(query)
    bm25_scores = bm25.get_scores(q_tokens)
    candidates = sorted(
        [(idx, score) for idx, score in enumerate(bm25_scores)],
        key=lambda x: x[1],
        reverse=True,
    )
    # Second stage: combine metrics
    w = weights or {"bm25": 0.33, "tfidf": 0.33, "embed": 0.33}
    reranker_scores = []
    for idx, bm in candidates:
        doc = chunk_list[idx]
        s_tfidf = tfidf_cosine(doc, query)
        s_embed = embedding_similarity(doc, query)
        final = w["bm25"] * bm + w["tfidf"] * s_tfidf + w["embed"] * s_embed
        reranker_scores.append(final)

    df_chunk_scored = pd.DataFrame(
        {"chunk": chunk_list, "reranker_score": reranker_scores}
    )

    df_chunk_scored["chunk_id"] = list(range(len(chunk_list)))

    result_rows = []

    # For each ranked chunk
    for _, row in df_chunk_scored.iterrows():
        chunk = row["chunk"]
        chunk_id = row["chunk_id"]  # Use the chunk_id to find original index
        original_idx, _ = index_map[chunk_id]

        # Get the original row and make a copy
        original_row = df.loc[original_idx].copy()

        # Replace the text with the chunk
        original_row[text_column] = chunk

        # Add the reranker score to the row
        original_row["reranker_score"] = row["reranker_score"]

        # Add to the list of result rows
        result_rows.append(original_row)

    # Create the final DataFrame
    result_df = pd.DataFrame(result_rows)

    return result_df


# 6. Example Usage
if __name__ == "__main__":
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
    query = "예시 document"
    scores = two_stage_score(query, df, "text_data")
    print(scores)
    # for idx, query, doc, final in scores:
    #     print(f"Document {doc} score: {final:.4f}")
