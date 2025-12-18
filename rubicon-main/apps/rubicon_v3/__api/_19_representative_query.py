import sys

sys.path.append("/www/alpha/")
import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "alpha.settings")
django.setup()

import hdbscan
import numpy as np
from uuid import uuid4
from datetime import datetime, timedelta
from pydantic import BaseModel
from typing import List, Dict, Optional, Any
from collections import Counter

from alpha._db import chat_log_collection

from apps.rubicon_v3.__function.definitions import sub_intelligences
from apps.rubicon_v3.__function import (
    __llm_call,
    __embedding_rerank,
    _12_text_guard_rail,
)
from apps.rubicon_v3.__function.__prompts import representative_query_prompt
from apps.rubicon_v3.models import Representative_Query as representative_query_model
from django.db.models import Max


class RepresentativeQuery(BaseModel):
    representative_query: str


def get_query_object_mongodb(
    country_code: Optional[str] = None,
    sub_intelligence_type: Optional[list] = None,
    exclude_errors: bool = True,
    exclude_timeouts: bool = True,
    exclude_thumbs_down: bool = True,
    exclude_exception: bool = True,
    days_back: int = 7,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    limit: Optional[int] = None,
    filters: Optional[Dict[str, Any]] = None,
) -> List[Dict[str, Any]]:

    query = {}

    if country_code:
        query["country_code"] = country_code

    # Add time-based filtering - automatically set dates if not provided
    if start_date is None and end_date is None:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)

    # Add time filter if we have dates
    if start_date or end_date:
        time_filter = {}
        if start_date:
            time_filter["$gte"] = start_date
        if end_date:
            time_filter["$lte"] = end_date
        query["created_on"] = time_filter

    # Add sensitive filters to match stage based on parameters
    if exclude_errors:
        query["dashboard_log.error"] = {"$ne": True}
    if exclude_timeouts:
        query["dashboard_log.timeout"] = {"$ne": True}
    if exclude_thumbs_down:
        query["appraisal.thumbs_up"] = {"$ne": False}
    if exclude_exception:
        query["dashboard_log.exception"] = {"$ne": True}

    # Always exclude guardrail and restricted
    query["dashboard_log.guardrail"] = {"$ne": True}
    query["dashboard_log.restricted"] = {"$ne": True}

    # Handle sub_intelligence filtering
    if sub_intelligence_type is None:
        # Default sub_intelligence list
        target_sub_intelligence_list = [
            sub_intelligences.PRODUCT_FEATURE,
            sub_intelligences.PRODUCT_SPECIFICATION,
            sub_intelligences.PRODUCT_FUNCTION,
            sub_intelligences.PRODUCT_REVIEW,
            sub_intelligences.SAMSUNG_COMPARISON,
            sub_intelligences.COMPETITOR_COMPARISON,
            sub_intelligences.GENERAL_RECOMMENDATION,
            sub_intelligences.CONDITIONAL_RECOMMENDATION,
            sub_intelligences.CONSUMABLES_ACCESSORIES_RECOMMENDATION,
            sub_intelligences.SAMSUNG_STORE_INFORMATION,
            sub_intelligences.IN_STORE_GUIDE,
        ]
        query["dashboard_log.sub_intelligence"] = {"$in": target_sub_intelligence_list}
    else:  # If not None and not empty list
        query["dashboard_log.sub_intelligence"] = {"$in": sub_intelligence_type}

    # Add additional filters if provided
    if filters:
        query.update(filters)

    projection = {"_id": 1, "log": 1, "created_on": 1}

    # Execute the query with match filtering and sort by newest first
    cursor = chat_log_collection.find(query, projection).sort("created_on", -1)

    # Apply limit if specified
    if limit:
        cursor = cursor.limit(limit)

    # Process and extract the required fields from each document
    processed_queries = []

    for doc in cursor:
        try:
            rewritten_query = None

            if "log" in doc and isinstance(doc["log"], list):
                for log_entry in doc["log"]:
                    if (
                        "llm" in log_entry
                        and "output" in log_entry["llm"]
                        and "re_write_query_list" in log_entry["llm"]["output"]
                    ):
                        rewrite_list = log_entry["llm"]["output"]["re_write_query_list"]
                        if rewrite_list:
                            rewritten_query = rewrite_list[0]
                            break

            # Build the processed query entry
            query_entry = {
                "_id": str(doc.get("_id", "")),
                "rewrite_top_query": rewritten_query,
                "created_on": doc.get("created_on", None),
            }

            processed_queries.append(query_entry)

        except Exception as e:
            print(f"Error processing {doc.get('_id', 'unknown')}: {e}")
            continue

    return processed_queries


def get_rewritten_queries(
    sub_intelligence_type: Optional[list] = None,
    country_code: str = "KR",
    exclude_errors: bool = True,
    exclude_timeouts: bool = True,
    exclude_thumbs_down: bool = True,
    days_back: int = 7,
    limit: Optional[int] = None,
) -> List[str]:
    """
    Extract rewritten queries using the get_query_object_mongodb function.
    """
    # Get processed queries using the main function
    processed_queries = get_query_object_mongodb(
        # channel=channel, # run for all channels
        country_code=country_code,
        sub_intelligence_type=sub_intelligence_type,
        exclude_errors=exclude_errors,
        exclude_timeouts=exclude_timeouts,
        exclude_thumbs_down=exclude_thumbs_down,
        days_back=days_back,
        limit=limit,
    )

    # Extract rewritten queries
    rewritten_queries = []
    for query_entry in processed_queries:
        rewrite_query = query_entry.get("rewrite_top_query")
        # Only add if it exists and has at least 8 characters
        if rewrite_query and len(rewrite_query) >= 8:
            rewritten_queries.append(rewrite_query)

    return rewritten_queries


def perform_clustering(
    queries,
    min_cluster_size=5,
    min_samples=2,
    metric="euclidean",
    cluster_selection_epsilon=0.5,
    prediction_data=True,
    max_noise_samples=10,
    max_sample_queries=10,
):
    """
    Perform HDBSCAN clustering on queries without visualization.

    Returns:
        tuple: (clusters_data, embeddings, successful_queries, clusterer, cluster_labels,
                noise_info, failed_info)
    """
    from tqdm import tqdm

    # Grab the embeddings
    embeddings = []
    successful_queries = []
    successful_indices = []  # Track original indices of successful embeddings

    for i, query in enumerate(tqdm(queries, desc="Generating embeddings")):
        try:
            embedding = __embedding_rerank.baai_embedding(query, str(uuid4()))
            if embedding:
                embeddings.extend(embedding)
                successful_queries.append(query)
                successful_indices.append(i)  # Store original index
        except Exception as e:
            pass

    if not embeddings:
        print("No embeddings found.")
        return None, None, None, None, None, None, None

    # Convert embeddings list to numpy array
    embeddings = np.array(embeddings)

    # Cluster the embeddings
    clusterer = hdbscan.HDBSCAN(
        min_cluster_size=min_cluster_size,
        min_samples=min_samples,
        metric=metric,
        cluster_selection_epsilon=cluster_selection_epsilon,
        prediction_data=prediction_data,
    )

    cluster_labels = clusterer.fit_predict(embeddings)

    # Get frequency of clusters
    counts = Counter(cluster_labels)
    if -1 in counts:  # Remove noise cluster from counts
        del counts[-1]

    # Sort clusters by frequency (most common first)
    sorted_clusters = sorted(counts.items(), key=lambda x: x[1], reverse=True)

    # Prepare results
    clusters_data = []

    # Get probabilities if available
    probabilities = getattr(clusterer, "probabilities_", None)

    for cluster_id, count in sorted_clusters:
        # Get indices of queries in this cluster (these are indices in the successful_queries list)
        local_cluster_indices = np.where(cluster_labels == cluster_id)[0]

        # Get vectors for this cluster
        cluster_vectors = embeddings[local_cluster_indices]

        # Calculate centroid
        centroid = np.mean(cluster_vectors, axis=0)

        # Calculate distances to centroid for all points in the cluster
        distances = np.linalg.norm(cluster_vectors - centroid, axis=1)

        # Sort local indices by distance to centroid
        sorted_by_distance = np.argsort(distances)
        sorted_local_indices = local_cluster_indices[sorted_by_distance]
        sorted_distances = distances[sorted_by_distance]

        # Map to original query indices
        sorted_original_indices = [successful_indices[i] for i in sorted_local_indices]

        # Get all queries in this cluster (sorted by distance to centroid)
        cluster_queries = [queries[i] for i in sorted_original_indices]

        # Get membership probabilities if available
        cluster_probs = None
        if probabilities is not None:
            cluster_probs = [probabilities[i] for i in sorted_local_indices]

        # Calculate probability statistics for this cluster
        prob_stats = {}
        if cluster_probs is not None:
            prob_stats = {
                "avg_probability": float(np.mean(cluster_probs)),
                "min_probability": float(np.min(cluster_probs)),
                "max_probability": float(np.max(cluster_probs)),
                "std_probability": float(np.std(cluster_probs)),
            }

        exemplar_idx = None
        exemplar_prob = None

        if prediction_data:
            # Find exemplar query (most representative)
            exemplar_idx = clusterer.exemplars_[cluster_id]
            if len(exemplar_idx) > 0:
                # Find the index in the successful embeddings data
                exemplar_distances = np.linalg.norm(
                    embeddings[local_cluster_indices][:, np.newaxis] - exemplar_idx,
                    axis=2,
                )
                exemplar_local_idx = np.argmin(np.min(exemplar_distances, axis=1))
                local_exemplar_idx = local_cluster_indices[exemplar_local_idx]
                # Map to original index
                exemplar_idx = successful_indices[local_exemplar_idx]
                if probabilities is not None:
                    exemplar_prob = probabilities[local_exemplar_idx]

        # If no exemplar found or not requested, use query closest to centroid
        if exemplar_idx is None:
            exemplar_idx = sorted_original_indices[0]  # Already sorted by distance
            if probabilities is not None and cluster_probs:
                exemplar_prob = cluster_probs[0]  # First item in sorted probs

        # Prepare sample queries with probabilities and distances
        sample_queries_with_stats = []
        for i in range(min(max_sample_queries, len(cluster_queries))):
            query_stats = {
                "query": cluster_queries[i],
                "original_index": sorted_original_indices[i],
                "distance_to_centroid": float(sorted_distances[i]),
            }
            if cluster_probs:
                query_stats["probability"] = float(cluster_probs[i])
            sample_queries_with_stats.append(query_stats)

        cluster_info = {
            "cluster_id": int(cluster_id),
            "size": count,
            "representative_query": queries[exemplar_idx],
            "representative_idx": int(exemplar_idx),
            "sample_queries": cluster_queries[:max_sample_queries],  # Original format
            "sample_queries_with_stats": sample_queries_with_stats,  # Enhanced with statistics
            "all_indices": sorted_original_indices,  # Original indices, sorted by distance
        }

        # Add probability for representative query if available
        if exemplar_prob is not None:
            cluster_info["representative_probability"] = float(exemplar_prob)

        # Add overall cluster probability statistics
        if prob_stats:
            cluster_info["probability_stats"] = prob_stats

        clusters_data.append(cluster_info)

    # Information about noise
    local_noise_indices = np.where(cluster_labels == -1)[0]
    # Map to original indices
    original_noise_indices = [successful_indices[i] for i in local_noise_indices]

    # Get noise probabilities if available
    noise_probs = None
    if probabilities is not None and len(local_noise_indices) > 0:
        noise_probs = [probabilities[i] for i in local_noise_indices]

    # Get the actual noise queries with stats (limited to max_noise_samples)
    noise_queries_with_stats = []
    for i in range(min(max_noise_samples, len(original_noise_indices))):
        noise_stat = {
            "query": queries[original_noise_indices[i]],
            "original_index": original_noise_indices[i],
        }
        if noise_probs:
            noise_stat["probability"] = float(noise_probs[i])
        noise_queries_with_stats.append(noise_stat)

    # Simple list of noise queries
    noise_queries = [queries[i] for i in original_noise_indices[:max_noise_samples]]

    # Add a note if we're not showing all noise queries
    noise_samples_note = ""
    if len(original_noise_indices) > max_noise_samples:
        noise_samples_note = f"(showing {max_noise_samples} of {len(original_noise_indices)} noise queries)"

    # Info about failed queries
    failed_indices = [i for i in range(len(queries)) if i not in successful_indices]
    failed_queries = [queries[i] for i in failed_indices[:max_noise_samples]]
    failed_queries_note = ""
    if len(failed_indices) > max_noise_samples:
        failed_queries_note = (
            f"(showing {max_noise_samples} of {len(failed_indices)} failed queries)"
        )

    noise_info = {
        "noise_count": len(original_noise_indices),
        "noise_indices": original_noise_indices,
        "noise_queries": noise_queries,
        "noise_queries_with_stats": noise_queries_with_stats,
        "noise_samples_note": noise_samples_note,
    }

    failed_info = {
        "failed_embedding_count": len(failed_indices),
        "failed_embedding_indices": failed_indices,
        "failed_embedding_queries": failed_queries,
        "failed_embedding_note": failed_queries_note,
    }

    return (
        clusters_data,
        embeddings,
        successful_queries,
        clusterer,
        cluster_labels,
        noise_info,
        failed_info,
    )


def get_clusters(
    queries,
    min_cluster_size=5,
    min_samples=2,
    metric="euclidean",
    cluster_selection_epsilon=0.5,
    prediction_data=True,
    max_noise_samples=10,
    max_sample_queries=10,
    language_data="KR",
    max_queries=50,
    model_name="gpt-4o-mini",
):

    print("Starting clustering process...")
    # Perform clustering
    result = perform_clustering(
        queries=queries,
        min_cluster_size=min_cluster_size,
        min_samples=min_samples,
        metric=metric,
        cluster_selection_epsilon=cluster_selection_epsilon,
        prediction_data=prediction_data,
        max_noise_samples=max_noise_samples,
        max_sample_queries=max_sample_queries,
    )

    if result[0] is None:  # Check if clustering failed
        return {}

    (
        clusters_data,
        embeddings,
        successful_queries,
        clusterer,
        cluster_labels,
        noise_info,
        failed_info,
    ) = result

    # Filter clusters
    clusters_data = (
        clusters_data[:max_queries] if max_queries is not None else clusters_data
    )

    # Generate representative queries using LLM
    llm_representative_queries = get_representative_query_data(
        clusters_data, language_data, model_name
    )

    # Embed LLM queries directly into each cluster's data
    for cluster in clusters_data:
        cluster_id = cluster["cluster_id"]
        cluster["llm_representative_query"] = llm_representative_queries.get(
            cluster_id, ""
        )

    # Return results
    return {
        "clusters": clusters_data,
        "llm_representative_queries": llm_representative_queries,
        "noise_count": noise_info["noise_count"],
        "noise_indices": noise_info["noise_indices"],
        "noise_queries": noise_info["noise_queries"],
        "noise_queries_with_stats": noise_info["noise_queries_with_stats"],
        "noise_samples_note": noise_info["noise_samples_note"],
        "total_queries": len(queries),
        "total_embedded": len(successful_queries),
        "clustered_queries": len(successful_queries) - noise_info["noise_count"],
        "num_clusters": len(clusters_data),
        "failed_embedding_count": failed_info["failed_embedding_count"],
        "failed_embedding_indices": failed_info["failed_embedding_indices"],
        "failed_embedding_queries": failed_info["failed_embedding_queries"],
        "failed_embedding_note": failed_info["failed_embedding_note"],
    }


def get_representative_query_data(
    clusters_data, language_data="KR", model_name="gpt-4o-mini"
):

    print("Starting LLM representative query generation...")
    print(f"Total: {len(clusters_data)} clusters")

    # Create a dictionary to store cluster_id to representative_query mapping
    cluster_to_query_map = {}

    # Skip if no clusters data is provided
    if not clusters_data:
        print("No clusters data provided.")
        return cluster_to_query_map

    # Process each cluster
    for cluster_info in tqdm(
        clusters_data,
        total=len(clusters_data),
        desc="Generating representative queries",
    ):
        cluster_id = cluster_info["cluster_id"]

        # Get sample queries directly from the cluster_info
        examples = cluster_info.get("sample_queries", [])

        instruction_prompt = representative_query_prompt.REPRESENTATIVE_PROMPT

        if examples:

            user_input = f"[Target Language]: {language_data}\n"
            user_input += f"[Examples]: \n{examples}\n"
            user_input += f"Representative sentence:"

            messages = [
                {
                    "role": "system",
                    "content": [{"type": "text", "text": instruction_prompt}],
                },
                {"role": "user", "content": [{"type": "text", "text": user_input}]},
            ]

            try:
                related_questions = __llm_call.open_ai_call_structured(
                    model_name, messages, RepresentativeQuery, 0.7, 0.4
                )
                representative_query = related_questions.get(
                    "representative_query",
                    examples[0] if examples else f"Cluster {cluster_id}",
                )

            except Exception as e:
                print(f"Error generating representative query: {e}")
                representative_query = (
                    examples[0] if examples else f"Cluster {cluster_id}"
                )

        else:
            # Use exemplar query as fall back if fails
            representative_query = cluster_info.get(
                "representative_query", f"Cluster {cluster_id}"
            )

        # Store in our dictionary with cluster_id as the key
        cluster_to_query_map[cluster_id] = representative_query

    return cluster_to_query_map


def generate_representative_queries(
    clusters_data, country_code="KR", site_cd="B2C", save_count=30, push_db=True
):

    if not clusters_data or len(clusters_data) == 0:
        raise ValueError(
            f"Clusters data is empty or None. Cannot save representative queries to database."
        )

    channel = "baseline"  # Default channel, can be modified if needed

    # Date data YYYYMMDDBB
    # check if batch exists
    now = datetime.now()
    base_batch = now.year * 1000000 + now.month * 10000 + now.day * 100
    base_batch_str = str(base_batch)
    upper_limit_str = str(base_batch + 100)

    # Find max batch_group for current day, country, and channel combination
    max_batch = representative_query_model.objects.filter(
        batch_group__gt=base_batch_str,
        batch_group__lt=upper_limit_str,
        country_code=country_code,
        channel=channel,
    ).aggregate(max_bg=Max("batch_group"))["max_bg"]

    if max_batch is None:
        batch_group = str(base_batch + 1)
    else:
        run_number = (int(max_batch) % 100) + 1

        if run_number > 99:
            raise ValueError(
                f"Too many runs ({run_number}) for {country_code}-{channel} on {now.strftime('%Y-%m-%d')}"
            )

        batch_group = str(base_batch + run_number)

    # Cluster Data
    clusters_to_save = (
        clusters_data[:save_count] if save_count is not None else clusters_data
    )

    query_count = 0
    current_display_order = 1

    for cluster_info in tqdm(clusters_to_save, desc="Checking TextGuardrail"):

        llm_query = cluster_info.get("llm_representative_query", "")

        # Fallback to exemplar/representative query if LLM query is empty
        if not llm_query:
            llm_query = cluster_info.get("representative_query")

        # Run Textguardrailget_query_object_mongodb
        if llm_query:
            guardrail_result = _12_text_guard_rail.rubicon_text_guardrail(
                query=llm_query, message_history=[]
            )

            if guardrail_result.get("decision", "") == "BENIGN":

                # Create a new Representative_Query instance
                rep_query = representative_query_model(
                    batch_group=batch_group,
                    display_order=current_display_order,
                    country_code=country_code,
                    channel=channel,
                    query=llm_query,
                    active=False,
                    site_cd=site_cd,
                )

                if push_db:
                    # Save to the database
                    rep_query.save()

                    query_count += 1
                    current_display_order += 1

        print(f"Saved {query_count} representative queries to the database.")


def update_representative_query_db(
    country_code="KR",
    model_name="gpt-4o-mini",
    generate_count=50,
    save_count=30,
    push_db=True,
):

    if country_code == "KR":
        language_data = "KR"
    else:
        language_data = "EN"

    filtered_rewritten_queries = get_rewritten_queries(
        country_code=country_code,
        exclude_errors=True,
        exclude_timeouts=True,
        days_back=7,
    )

    clusters = get_clusters(
        filtered_rewritten_queries,
        min_cluster_size=5,
        min_samples=2,
        metric="euclidean",
        cluster_selection_epsilon=0.5,
        prediction_data=True,
        max_noise_samples=10,
        max_sample_queries=10,
        language_data=language_data,
        max_queries=generate_count,
        model_name=model_name,
    )

    generate_representative_queries(
        clusters_data=clusters["clusters"],
        country_code=country_code,
        site_cd="B2C",
        save_count=save_count,
        push_db=push_db,
    )


if __name__ == "__main__":
    from rich import print as rich_print
    from tqdm import tqdm

    all_country_codes = ["KR", "GB"]
    model_name = "gpt-4o-mini"  # For rewriting representative query

    for country_code in all_country_codes:
        channels_to_cluster = []

        query_objects = get_query_object_mongodb(country_code=country_code, days_back=7)

        object_count = len(query_objects)

        rich_print(f"[green]{country_code}: {object_count} queries found[/green]")

        try:
            update_representative_query_db(
                country_code=country_code,
                model_name=model_name,
                generate_count=50,
                save_count=30,
                push_db=True,
            )

        except Exception as e:
            rich_print(f"[red]Error processing {country_code}: {e}[/red]")
            rich_print(f"[red]Error: {e}[/red]")
