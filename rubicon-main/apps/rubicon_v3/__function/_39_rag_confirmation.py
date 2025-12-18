import sys

sys.path.append("/www/alpha/")

import enum

from apps.rubicon_v3.__function.definitions import (
    intelligences,
    sub_intelligences,
    ner_fields,
)


class RagConfirmationStatus(str, enum.Enum):
    NO_RAG_REQUIRED = "no_rag_required"
    RE_ASKING_REQUIRED = "re_asking_required"
    AI_SUBSCRIPTION = "ai_subscription"
    SUCCESS = "success"


def rag_confirmation(
    deep_queries: list,
    no_rag_queries: list,
    unprocessed_queries: list,
    rewritten_queries: list,
    ner_data: dict,
    intelligence_data: dict,
    sub_intelligence_data: dict,
    assistant_data: dict,
    turns_since_re_asked: int,
    personalization_required: bool,
    no_cache_queries: set,
    error_queries: set,
):
    remove_queries_set = set()
    no_rag_queries_set = set(no_rag_queries)
    re_asking_queries = set()

    # Add all the no RAG queries to the no_cache_queries set
    no_cache_queries.update(no_rag_queries)

    # Check if there are any queries that needs to be AI subscription response
    for query in deep_queries:
        if sub_intelligence_data.get(query) in [
            sub_intelligences.PRICE_EXPLANATION,
            sub_intelligences.PAYMENT_BENEFIT_EXPLANATION,
        ] and any(
            ner_item.get("field") == ner_fields.SUBSCRIPTION
            for ner_item in ner_data.get(query, [])
        ):
            no_cache_queries.add(query)
            return (
                [],
                [],
                no_cache_queries,
                error_queries,
                RagConfirmationStatus.AI_SUBSCRIPTION.value,
            )

    # Check if the sub intelligence requires no caching
    for query, sub_intelligence in sub_intelligence_data.items():
        if sub_intelligence in [
            sub_intelligences.PRICE_EXPLANATION,
            sub_intelligences.PAYMENT_BENEFIT_EXPLANATION,
            sub_intelligences.PROBLEM_SOLVING,
            sub_intelligences.SERVICE_CENTER_INFORMATION,
            sub_intelligences.IN_CENTER_GUIDE,
            sub_intelligences.REPAIR_COST_GUIDE,
            sub_intelligences.ACCOUNT_ACTIVITY,
            sub_intelligences.ACCOUNT_MANAGEMENT_INFORMATION,
            sub_intelligences.ORDER_DELIVERY_TRACKING,
            sub_intelligences.PERSONALIZED_RECOMMENDATION,
            sub_intelligences.PERSONALIZED_COMPARISON,
        ]:
            no_cache_queries.add(query)

    # Check if the sub-intelligence is Product Lineup Recommendation and the turns since re-asked is 0 (i.e. the last query was re-asked)
    # If so, update the sub-intelligence to Conditional Recommendation
    for query in deep_queries:
        if (
            sub_intelligence_data.get(query)
            == sub_intelligences.PRODUCT_LINEUP_RECOMMENDATION
            and turns_since_re_asked == 0
        ):
            sub_intelligence_data[query] = sub_intelligences.CONDITIONAL_RECOMMENDATION

    # Check if the sub-intelligence is Product Lineup related and ner data has any of the fields (spec, option, color)
    # If so, update the sub-intelligence to the non-lineup version
    for query in deep_queries:
        if sub_intelligence_data.get(query) in [
            sub_intelligences.PRODUCT_LINEUP_RECOMMENDATION,
            sub_intelligences.PERSONALIZED_RECOMMENDATION,
            sub_intelligences.PRODUCT_LINEUP_COMPARISON,
            sub_intelligences.PRODUCT_LINEUP_DESCRIPTION,
        ] and any(
            ner_item.get("field")
            in [
                ner_fields.PRODUCT_SPEC,
                ner_fields.PRODUCT_OPTION,
                ner_fields.PRODUCT_COLOR,
            ]
            for ner_item in ner_data.get(query, [])
        ):
            if sub_intelligence_data[query] in (
                sub_intelligences.PRODUCT_LINEUP_RECOMMENDATION,
                sub_intelligences.PERSONALIZED_RECOMMENDATION,
            ):
                sub_intelligence_data[query] = (
                    sub_intelligences.CONDITIONAL_RECOMMENDATION
                )
            elif (
                sub_intelligence_data[query]
                == sub_intelligences.PRODUCT_LINEUP_COMPARISON
            ):
                sub_intelligence_data[query] = sub_intelligences.SAMSUNG_COMPARISON
            elif (
                sub_intelligence_data[query]
                == sub_intelligences.PRODUCT_LINEUP_DESCRIPTION
            ):
                sub_intelligence_data[query] = sub_intelligences.PRODUCT_FEATURE

    # Check if re-asking is required for all of the deep queries
    for query in deep_queries:
        # Check if assistant data deems re-asking is required and previous query was not re-asked
        # Make sure that personalization flag is false for re-asking to be considered
        if (
            assistant_data.get(query, {}).get("re_asking_required") is True
            and not turns_since_re_asked < 5
            and not personalization_required
        ):
            remove_queries_set.add(query)
            re_asking_queries.add(query)
            no_cache_queries.add(query)
            # If all queries need re-asking
            if set(deep_queries).issubset(re_asking_queries):
                return (
                    [],
                    [],
                    no_cache_queries,
                    error_queries,
                    RagConfirmationStatus.RE_ASKING_REQUIRED.value,
                )

    # Check if the all the queries are not suitable for RAG
    if set(unprocessed_queries).issubset(no_rag_queries_set):
        # If all queries are not suitable for RAG, return empty list
        return (
            [],
            no_rag_queries,
            no_cache_queries,
            error_queries,
            RagConfirmationStatus.NO_RAG_REQUIRED.value,
        )

    # Check if all the queries are suitable for RAG
    if set(unprocessed_queries).issubset(set(deep_queries)) and not re_asking_queries:
        # If all queries are suitable for RAG, return the deep queries
        return (
            deep_queries,
            no_rag_queries,
            no_cache_queries,
            error_queries,
            RagConfirmationStatus.SUCCESS.value,
        )

    # Up to this point, there is a mixture of queries that require RAG and those that do not
    # Convert the deep queries with reasking flag to no_rag_queries
    if re_asking_queries:
        no_rag_queries_set.update(re_asking_queries)

    # Up to this point, there are deep queries that require RAG
    deep_queries_set = set(deep_queries) - no_rag_queries_set

    return (
        list(deep_queries_set),
        list(no_rag_queries_set),
        no_cache_queries,
        error_queries,
        RagConfirmationStatus.SUCCESS.value,
    )
