import sys

sys.path.append("/www/alpha/")
import os
import django
from django.db.models import Q

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "alpha.settings")
django.setup()

import pytz
import time

from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor, as_completed

from alpha._db import chat_log_collection, search_log_collection
from apps.rubicon_v3.__function import (
    _00_rubicon,
    _02_language_identification,
    _10_rewrite,
    _20_orchestrator_NER_init,
    _21_orchestrator_query_analyzer,
    _21_orchestrator_context_determination,
    _22_orchestrator_intelligence,
    _31_orchestrator_assistant,
    _32_sub_intelligence,
    _30_orchestrator_NER_standardization,
    _71_product_rag_web_search,
    _72_product_rag_ai_search,
    _73_product_rag_specification_check,
)
from apps.rubicon_v3.__function.__encryption_utils import recursive_decrypt_strings
from apps.rubicon_v3.__api.__utils import (
    DashUtils,
    product_filter_preprocessing,
)
from apps.rubicon_v3.__api.search_summary import (
    _00_search_summary,
    _05_query_expansion,
    _10_simple_ai_search,
)
from apps.rubicon_v3.models import Intelligence_V2, Channel, Channel_Appraisal

from alpha.settings import VITE_OP_TYPE


chat_pipeline_modules = {
    "LLM": {
        _02_language_identification.lang_detect_with_gpt.__name__: "Language Detection",
        _10_rewrite.re_write_history.__name__: "Re-write",
        _21_orchestrator_query_analyzer.query_analyzer.__name__: "Query Analyzer",
        _22_orchestrator_intelligence.intelligence.__name__: "Intelligence",
        _20_orchestrator_NER_init.ner.__name__: "NER",
        _21_orchestrator_context_determination.context_determination.__name__: "Context Determination",
        _31_orchestrator_assistant.assistant.__name__: "Assistant",
        _32_sub_intelligence.get_sub_intelligence.__name__: "Sub Intelligence",
        _30_orchestrator_NER_standardization.standardize_ner_expression.__name__: "Standardized NER",
    },
    "MODULE": {
        _71_product_rag_web_search.get_google_search_results.__name__: "Web Search",
        _72_product_rag_ai_search.execute_unstructured_rag.__name__: "AI Search",
        _00_rubicon.ChatFlowSectionNames.MERGE_DATA: "Merge Data",
    },
    "SECTION": {
        _00_rubicon.ChatFlowSectionNames.PARALLEL_REWRITE_LOADING_MESSAGE_TEXT_CLEANUP_LANGUAGE_DETECT_CORRECTION_DETERMINATION: "Parallel: Rewrite + Loading Message + Text Cleanup + Language Detect",
        _00_rubicon.ChatFlowSectionNames.PARALLEL_QUERY_ANALYZER_INTELLIGENCE_NER_CONTEXT_DETERMINATION: "Parallel: Query Analyzer + Intelligence + NER + Context Determination",
        _00_rubicon.ChatFlowSectionNames.PARALLEL_STANDARD_NER_ASSISTANT_SUB_INTELLIGENCE: "Parallel: Standard NER + Assistant + Sub Intelligence",
        _00_rubicon.ChatFlowSectionNames.PARALLEL_STRUCTURED_COMPLEMENT: "Parallel: Structured + Complement",
    },
    "PIPELINE": {
        "RAG Completion Time": "RAG Completion Time",
        "LLM Processing Time": "LLM Processing Time",
        "Start of Stream": "Start of Stream",
        "End of Stream": "End of Stream",
    },
}

search_pipeline_modules = {
    "LLM": {
        _05_query_expansion.query_expansion.__name__: "Query Expansion",
        _22_orchestrator_intelligence.intelligence.__name__: "Intelligence",
    },
    "MODULE": {
        _10_simple_ai_search.execute_cpt_rag.__name__: "Simple AI Search",
        _73_product_rag_specification_check.specification_check.__name__: "Specification Check",
    },
    "SECTION": {
        _00_search_summary.SearchFlowSectionNames.PARALLEL_QUERY_EXPANSION_AI_SEARCH_SPEC_CHECK: "Parallel: Query Expansion + AI Search + Spec Check",
        _00_search_summary.SearchFlowSectionNames.PARALLEL_PREDEFINED_INTELLIGENCE_GUARDRAILS: "Parallel: Predefined Intelligence + Guardrails",
    },
    "PIPELINE": {
        "RAG Completion Time": "RAG Completion Time",
        "LLM Processing Time": "LLM Processing Time",
        "Start of Stream": "Start of Stream",
        "End of Stream": "End of Stream",
    },
}


class Dashboard:
    @dataclass
    class DashboardParams:
        api_type: str
        service: str
        start_date: str
        end_date: str
        timezone: str
        channel: list[str]
        intelligence: list[str]
        country_code: list[str]
        subsidiary: list[str]
        product_line: list[str]
        product_name: list[str]
        thumb_type: str
        thumb_up: list[str]
        interval: str
        locale: str

    def __init__(self, input_params: DashboardParams):
        # Determine which mongo collection to use based on service
        # Also get the appropriate module mapping
        if input_params.service == "chat":
            self.mongo_collection = chat_log_collection
            self.module_mapping = chat_pipeline_modules
        elif input_params.service == "search":
            self.mongo_collection = search_log_collection
            self.module_mapping = search_pipeline_modules
        else:
            raise ValueError("Invalid service type. Must be 'chat' or 'search'.")

        # Preprocess input parameters (product name)
        if input_params.product_name:
            input_params.product_line, input_params.product_name = (
                product_filter_preprocessing(
                    input_params.product_line,
                    input_params.product_name,
                    input_params.locale,
                )
            )
        self.input_params = input_params
        self.dash_utils_class = DashUtils.from_params(input_params)
        self.base_filter_criteria: dict = (
            self.dash_utils_class.get_base_filter_criteria_dict()
        )

    def dashboard_api_mux(self):
        # Possible Types: "status", "overview", "queries", "thumbs", "users", "thumbsDetail", "response"
        if self.input_params.api_type == "status":
            return self.dashboard_status()
        elif self.input_params.api_type == "rawStatus":
            return self.dashboard_raw_status()
        elif self.input_params.api_type == "overview":
            return self.dashboard_overview()
        elif self.input_params.api_type == "queries":
            return self.dashboard_queries_v2()
        elif self.input_params.api_type == "thumbs":
            return self.dashboard_thumbs_v3()
        elif self.input_params.api_type == "users":
            return self.dashboard_users()
        elif self.input_params.api_type == "divisions":
            return self.dashboard_divisions()
        elif self.input_params.api_type == "thumbsDetail":
            return self.dashboard_thumbs_detail()
        elif self.input_params.api_type == "response":
            return self.dashboard_response()
        elif self.input_params.api_type == "responseInterval":
            return self.dashboard_response_interval()
        else:
            raise ValueError("Invalid API type")

    def dashboard_status(self):
        """
        Dashboard status API
        """
        # Make sure locale is not None
        if not self.input_params.locale:
            raise ValueError("Locale is required for dashboard status")

        # Make sure locale is either "KR" or "GB"
        if self.input_params.locale.upper() not in ["KR", "GB"]:
            raise ValueError("Locale must be either 'KR' or 'GB'")

        # Build the filter criteria dynamically
        intelligence_filter_criteria = Q()

        # If channel is provided, filter by it
        if self.input_params.channel:
            intelligence_filter_criteria &= Q(
                channel__contains=self.input_params.channel
            )
        # Else get all distinct active channels for the locale and service
        else:
            distinct_channel_filter_criteria = Q(active=True)
            distinct_channel_filter_criteria &= Q(service=self.input_params.service)
            if VITE_OP_TYPE != "DEV":
                distinct_channel_filter_criteria &= Q(locale=self.input_params.locale)

            distinct_channels = (
                Channel.objects.filter(distinct_channel_filter_criteria)
                .values_list("channel", flat=True)
                .distinct()
            )

            # Update the filter criteria to include all distinct channels
            intelligence_filter_criteria &= Q(channel__overlap=list(distinct_channels))

        intelligence_data = list(
            Intelligence_V2.objects.filter(intelligence_filter_criteria)
            .values("intelligence")
            .distinct()
            .order_by("intelligence")
        )

        # Build the filter criteria dynamically for channel data
        channel_filter_criteria = Q(active=True)
        channel_filter_criteria &= Q(service=self.input_params.service)
        if VITE_OP_TYPE != "DEV":
            channel_filter_criteria &= Q(locale=self.input_params.locale)
        if self.input_params.country_code:
            channel_filter_criteria &= Q(
                country_code__in=self.input_params.country_code
            )
        if self.input_params.channel:
            channel_filter_criteria &= Q(channel__in=self.input_params.channel)
        if self.input_params.subsidiary:
            channel_filter_criteria &= Q(subsidiary__in=self.input_params.subsidiary)
        if VITE_OP_TYPE == "DEV":
            channel_filter_criteria &= Q(front_dev=True)
        elif VITE_OP_TYPE == "STG":
            channel_filter_criteria &= Q(front_stg=True)
        elif VITE_OP_TYPE == "PRD":
            channel_filter_criteria &= Q(front_prd=True)
        else:
            raise ValueError("Invalid VITE_OP_TYPE")

        # Retrieve channel data
        channel_data = list(
            Channel.objects.filter(channel_filter_criteria)
            .values("channel")
            .distinct()
            .order_by("channel")
        )

        # Retrieve distinct country_name and country_code pairs
        country_data = list(
            Channel.objects.filter(channel_filter_criteria)
            .values("country_name", "country_code")
            .distinct()
            .order_by("country_name")
        )

        # Retrieve distinct subsidiary values
        subsidiary_data = list(
            Channel.objects.filter(channel_filter_criteria)
            .values("subsidiary")
            .distinct()
            .order_by("subsidiary")
        )

        # Retrieve product category data
        product_category_data = self.dash_utils_class.retrieve_product_category_data(
            should_filter=False
        )

        # Retrieve grouped product data
        grouped_product_data = self.dash_utils_class.categorize_product_info(
            product_category_data
        )

        return {
            "success": True,
            "data": {
                "intelligence": intelligence_data,
                "channel": channel_data,
                "country": country_data,
                "subsidiary": subsidiary_data,
                "product_category": grouped_product_data,
            },
            "message": "",
        }

    def dashboard_raw_status(self):
        """
        Dashboard raw status API
        """
        # Make sure locale is not None
        if not self.input_params.locale:
            raise ValueError("Locale is required for dashboard raw status")

        # Make sure locale is either "KR" or "GB"
        if self.input_params.locale.upper() not in ["KR", "GB"]:
            raise ValueError("Locale must be either 'KR' or 'GB'")

        # Get all the distinct active channels for the locale and service
        distinct_channel_filter_criteria = Q(active=True)
        distinct_channel_filter_criteria &= Q(service=self.input_params.service)
        if VITE_OP_TYPE != "DEV":
            distinct_channel_filter_criteria &= Q(locale=self.input_params.locale)

        distinct_channels = (
            Channel.objects.filter(distinct_channel_filter_criteria)
            .values_list("channel", flat=True)
            .distinct()
        )

        # Build the filter criteria dynamically
        intelligence_data = list(
            Intelligence_V2.objects.filter(Q(channel__overlap=list(distinct_channels)))
            .values("intelligence", "intelligence_desc")
            .distinct()
            .order_by("intelligence")
        )

        # Retrieve channel data
        channel_filter_criteria = Q(active=True)
        channel_filter_criteria &= Q(service=self.input_params.service)
        if VITE_OP_TYPE != "DEV":
            channel_filter_criteria &= Q(locale=self.input_params.locale)
        channel_data = list(
            Channel.objects.filter(channel_filter_criteria)
            .values("channel")
            .distinct()
            .order_by("channel")
        )

        # Retrieve distinct country_name and country_code pairs
        country_data = list(
            Channel.objects.filter(channel_filter_criteria)
            .values("country_name", "country_code")
            .distinct()
            .order_by("country_name")
        )

        # Retrieve distinct subsidiary values
        subsidiary_data = list(
            Channel.objects.filter(channel_filter_criteria)
            .values("subsidiary")
            .distinct()
            .order_by("subsidiary")
        )

        # Retrieve product category data
        product_category_data = self.dash_utils_class.retrieve_product_category_data(
            should_filter=False
        )

        # Retrieve grouped product data
        grouped_product_data = self.dash_utils_class.categorize_product_info(
            product_category_data
        )

        return {
            "success": True,
            "data": {
                "intelligence": intelligence_data,
                "channel": channel_data,
                "country": country_data,
                "subsidiary": subsidiary_data,
                "product_category": grouped_product_data,
            },
            "message": "",
        }

    def dashboard_overview(self):
        """
        Dashboard overview API
        """
        base_filter_criteria_indexed = self.base_filter_criteria

        default_output = {
            "totalQueries": 0,
            "totalUsers": 0,
            "totalThumbDown": 0,
            "totalThumbUp": 0,
            "queriesPerUser": 0,
            "errorRatio": 0,
            "timeoutRatio": 0,
            "thumbsDownRatio": 0,
            "thumbsUpRatio": 0,
            "avgResponseTime": 0,
        }

        pipeline = [
            {"$match": base_filter_criteria_indexed},
            {
                "$facet": {
                    "totalChats": [{"$count": "count"}],
                    "totalError": [
                        {"$match": {"dashboard_log.error": True}},
                        {"$count": "count"},
                    ],
                    "totalTimeout": [
                        {"$match": {"dashboard_log.timeout": True}},
                        {"$count": "count"},
                    ],
                    "totalThumbsDown": [
                        {"$match": {"appraisal.thumb_up": False}},
                        {"$count": "count"},
                    ],
                    "totalThumbsUp": [
                        {"$match": {"appraisal.thumb_up": True}},
                        {"$count": "count"},
                    ],
                    "averageResponseTime": [
                        {
                            "$group": {
                                "_id": None,
                                "averageElapsedTime": {"$avg": "$elapsed_time"},
                            }
                        }
                    ],
                    "totalUsers": [
                        {
                            "$match": {
                                "user_hash": {"$exists": True, "$nin": ["", None]}
                            }
                        },
                        {
                            "$group": {
                                "_id": None,
                                "distinctUsers": {"$addToSet": "$user_hash"},
                            }
                        },
                        {"$project": {"count": {"$size": "$distinctUsers"}}},
                    ],
                }
            },
            {
                "$addFields": {
                    "totalChats": {
                        "$ifNull": [{"$arrayElemAt": ["$totalChats.count", 0]}, 0]
                    },
                    "totalError": {
                        "$ifNull": [{"$arrayElemAt": ["$totalError.count", 0]}, 0]
                    },
                    "totalTimeout": {
                        "$ifNull": [{"$arrayElemAt": ["$totalTimeout.count", 0]}, 0]
                    },
                    "totalThumbsDown": {
                        "$ifNull": [{"$arrayElemAt": ["$totalThumbsDown.count", 0]}, 0]
                    },
                    "totalThumbsUp": {
                        "$ifNull": [{"$arrayElemAt": ["$totalThumbsUp.count", 0]}, 0]
                    },
                    "averageElapsedTime": {
                        "$ifNull": [
                            {
                                "$arrayElemAt": [
                                    "$averageResponseTime.averageElapsedTime",
                                    0,
                                ]
                            },
                            0,
                        ]
                    },
                    "totalUsers": {
                        "$ifNull": [{"$arrayElemAt": ["$totalUsers.count", 0]}, 0]
                    },
                }
            },
            {
                "$addFields": {
                    # Use safe denominators and default to 0 if division result is null
                    "errorRatio": {
                        "$ifNull": [
                            {
                                "$divide": [
                                    {"$ifNull": ["$totalError", 0]},
                                    {
                                        "$cond": [
                                            {"$eq": ["$totalChats", 0]},
                                            None,
                                            "$totalChats",
                                        ]
                                    },
                                ]
                            },
                            0,
                        ]
                    },
                    "timeoutRatio": {
                        "$ifNull": [
                            {
                                "$divide": [
                                    {"$ifNull": ["$totalTimeout", 0]},
                                    {
                                        "$cond": [
                                            {"$eq": ["$totalChats", 0]},
                                            None,
                                            "$totalChats",
                                        ]
                                    },
                                ]
                            },
                            0,
                        ]
                    },
                    "thumbsDownRatio": {
                        "$ifNull": [
                            {
                                "$divide": [
                                    {"$ifNull": ["$totalThumbsDown", 0]},
                                    {
                                        "$cond": [
                                            {"$eq": ["$totalChats", 0]},
                                            None,
                                            "$totalChats",
                                        ]
                                    },
                                ]
                            },
                            0,
                        ]
                    },
                    "thumbsUpRatio": {
                        "$ifNull": [
                            {
                                "$divide": [
                                    {"$ifNull": ["$totalThumbsUp", 0]},
                                    {
                                        "$cond": [
                                            {"$eq": ["$totalChats", 0]},
                                            None,
                                            "$totalChats",
                                        ]
                                    },
                                ]
                            },
                            0,
                        ]
                    },
                    "avgResponseTime": {"$multiply": ["$averageElapsedTime", 1000]},
                    "queriesPerUser": {
                        "$ifNull": [
                            {
                                "$divide": [
                                    {"$ifNull": ["$totalChats", 0]},
                                    {
                                        "$cond": [
                                            {"$eq": ["$totalUsers", 0]},
                                            None,
                                            "$totalUsers",
                                        ]
                                    },
                                ]
                            },
                            0,
                        ]
                    },
                }
            },
            {
                "$project": {
                    "_id": 0,
                    "totalQueries": "$totalChats",
                    "totalUsers": 1,
                    "totalThumbDown": "$totalThumbsDown",
                    "totalThumbUp": "$totalThumbsUp",
                    "queriesPerUser": 1,
                    "errorRatio": 1,
                    "timeoutRatio": 1,
                    "thumbsDownRatio": 1,
                    "thumbsUpRatio": 1,
                    "avgResponseTime": 1,
                }
            },
        ]

        # Run the aggregation pipeline
        result = list(self.mongo_collection.aggregate(pipeline))

        # If result is empty, return default output
        if not result:
            return {
                "success": True,
                "data": default_output,
                "message": "No data available from the selected criteria",
            }

        # Otherwise return the first result
        return {"success": True, "data": result[0], "message": ""}

    # ======================================================

    # Define different status determination functions
    def get_appraisal_status_expression(self):
        """Status based on appraisal with thumb_up/down"""
        return {
            "$cond": [
                {
                    "$eq": [{"$type": "$appraisal"}, "object"]
                },  # Check if appraisal exists and is an object
                {
                    "$cond": [
                        {
                            "$eq": [{"$objectToArray": "$appraisal"}, []]
                        },  # Check if appraisal is empty
                        "na",
                        {
                            "$cond": [
                                {"$eq": ["$appraisal.thumb_up", True]},
                                "up",
                                "down",
                            ]
                        },
                    ]
                },
                "na",  # If appraisal doesn't exist or isn't an object
            ]
        }

    def get_dashboard_status_expression(self):
        """Status based on dashboard_log error and timeout flags"""
        return {
            "$cond": [
                # First check for explicit success case - both flags are false
                {
                    "$and": [
                        {"$eq": ["$dashboard_log.error", False]},
                        {"$eq": ["$dashboard_log.timeout", False]},
                    ]
                },
                "success",
                # Otherwise, determine specific error type or default to incomplete
                {
                    "$cond": [
                        {"$eq": ["$dashboard_log.error", True]},
                        "error",
                        {
                            "$cond": [
                                {"$eq": ["$dashboard_log.timeout", True]},
                                "timeout",
                                "incomplete",  # Default when conditions aren't explicitly defined
                            ]
                        },
                    ]
                },
            ]
        }

    def get_product_division_status_expression(self):
        """Returns a MongoDB aggregation expression to determine product status based on divisions"""
        return {
            "$let": {
                "vars": {
                    # Get distinct divisions from product_log
                    "distinctDivisions": {
                        "$setUnion": [
                            {
                                "$reduce": {
                                    "input": {
                                        "$map": {
                                            "input": {"$ifNull": ["$product_log", []]},
                                            "as": "log",
                                            "in": {
                                                "$ifNull": [
                                                    "$$log.product_division",
                                                    [],
                                                ]
                                            },
                                        }
                                    },
                                    "initialValue": [],
                                    "in": {"$concatArrays": ["$$value", "$$this"]},
                                }
                            },
                            [],
                        ]
                    }
                },
                "in": {
                    "$let": {
                        "vars": {
                            # Find which major divisions are present - hardcode the array here
                            "presentMajorDivisions": {
                                "$setIntersection": [
                                    "$$distinctDivisions",
                                    ["MX", "VD", "DA"],
                                ]
                            }
                        },
                        "in": {
                            "$switch": {
                                "branches": [
                                    {
                                        "case": {
                                            "$eq": [
                                                {"$size": "$$presentMajorDivisions"},
                                                0,
                                            ]
                                        },
                                        "then": "Not Applicable",
                                    },
                                    {
                                        "case": {
                                            "$eq": [
                                                {"$size": "$$presentMajorDivisions"},
                                                1,
                                            ]
                                        },
                                        "then": {
                                            "$arrayElemAt": [
                                                "$$presentMajorDivisions",
                                                0,
                                            ]
                                        },
                                    },
                                ],
                                "default": "Cross Product",
                            }
                        },
                    }
                },
            }
        }

    # 1. Factory function to create counts aggregation pipeline
    def create_total_counts_pipeline(self, status_func):
        """Create a pipeline factory with the given status determination function

        Args:
            status_func: Function to determine status
            output_key: Key name for the output object. Defaults to "total".
        """

        def get_total_counts_pipeline(base_filter_criteria, output_key="total"):
            return [
                {"$match": base_filter_criteria},
                {"$project": {"status": status_func}},
                {"$group": {"_id": "$status", "count": {"$sum": 1}}},
                {
                    "$group": {
                        "_id": None,
                        "counts": {"$push": {"k": "$_id", "v": "$count"}},
                    }
                },
                {"$project": {"_id": 0, **{output_key: {"$arrayToObject": "$counts"}}}},
            ]

        return get_total_counts_pipeline

    # 2. Factory function to create time aggregation pipeline
    def create_time_aggregation_pipeline(self, status_func, interval):
        """
        Create a time-based pipeline with the given status determination function

        Parameters:
        - status_func: Function to determine status
        - interval: String indicating time grouping ('daily', 'weekly', or 'monthly')
        """

        def get_time_format(interval):
            if interval == "daily":
                return "%Y-%m-%d"
            elif interval == "weekly":
                # Group by week (using ISO week format YYYY-WW)
                return "%G-W%V"
            elif interval == "monthly":
                # Group by month (YYYY-MM)
                return "%Y-%m"
            else:
                raise ValueError(
                    "Invalid interval. Must be 'daily', 'weekly', or 'monthly'"
                )

        def get_time_label(interval):
            """Returns a human-readable name for the format"""
            if interval == "daily":
                return "date"
            elif interval == "weekly":
                return "week"
            elif interval == "monthly":
                return "month"
            else:
                raise ValueError(
                    "Invalid interval. Must be 'daily', 'weekly', or 'monthly'"
                )

        # Set default interval if not provided
        if interval is None:
            interval = "daily"

        time_format = get_time_format(interval)
        time_label = get_time_label(interval)

        def get_time_aggregation_pipeline(base_filter_criteria, output_key="byTime"):
            # Get timezone from input params, default to UTC
            timezone_str = getattr(self.input_params, "timezone", None)

            # Prepare the date formatting options
            date_to_string_options = {"format": time_format, "date": "$created_on"}

            # Validate and add timezone parameter if specified
            if timezone_str:
                try:
                    # Verify timezone is valid
                    pytz.timezone(timezone_str)
                    # If valid, add to options
                    date_to_string_options["timezone"] = timezone_str
                except pytz.exceptions.UnknownTimeZoneError:
                    # Handle invalid timezone
                    raise ValueError(f"Invalid timezone: '{timezone_str}'")

            return [
                {"$match": base_filter_criteria},
                {"$project": {"created_on": 1, "status": status_func}},
                {
                    "$group": {
                        "_id": {
                            time_label: {"$dateToString": date_to_string_options},
                            "status": "$status",
                        },
                        "count": {"$sum": 1},
                    }
                },
                {
                    "$group": {
                        "_id": f"$_id.{time_label}",
                        "stats": {
                            "$push": {"status": "$_id.status", "count": "$count"}
                        },
                    }
                },
                {"$project": {"_id": 0, time_label: "$_id", "statusCounts": "$stats"}},
                {
                    "$project": {
                        time_label: 1,
                        "statusValues": {
                            "$arrayToObject": {
                                "$map": {
                                    "input": "$statusCounts",
                                    "as": "item",
                                    "in": {"k": "$$item.status", "v": "$$item.count"},
                                }
                            }
                        },
                    }
                },
                {
                    "$group": {
                        "_id": None,
                        "entries": {
                            "$push": {"k": f"${time_label}", "v": "$statusValues"}
                        },
                    }
                },
                {
                    "$project": {
                        "_id": 0,
                        **{output_key: {"$arrayToObject": "$entries"}},
                    }
                },
            ]

        return get_time_aggregation_pipeline

    # 3. Factory function for field-based aggregation
    def create_field_aggregation_pipeline(self, status_func):
        """Create a field aggregation pipeline factory with the given status determination function (optimized)"""

        def get_field_aggregation_pipeline(
            base_filter_criteria, field_name, output_key
        ):

            return [
                {"$match": base_filter_criteria},
                {"$match": {field_name: {"$exists": True, "$nin": ["", None]}}},
                {
                    "$project": {
                        "field_value": f"${field_name}",
                        "status": status_func,
                        "user_hash": "$user_hash",
                    }
                },
                {
                    "$group": {
                        "_id": {"field_value": "$field_value", "status": "$status"},
                        "count": {"$sum": 1},
                        "user_hashes": {"$addToSet": "$user_hash"},
                    }
                },
                {
                    "$group": {
                        "_id": "$_id.field_value",
                        "statusCounts": {"$push": {"k": "$_id.status", "v": "$count"}},
                        "all_user_hashes": {"$push": "$user_hashes"},
                    }
                },
                {
                    "$project": {
                        "_id": 0,
                        "field_value": "$_id",
                        "statusValues": {"$arrayToObject": "$statusCounts"},
                        "user_count": {
                            "$size": {
                                "$setUnion": {
                                    "$reduce": {
                                        "input": "$all_user_hashes",
                                        "initialValue": [],
                                        "in": {"$setUnion": ["$$value", "$$this"]},
                                    }
                                }
                            },
                        },
                    }
                },
                {
                    "$group": {
                        "_id": None,
                        "entries": {
                            "$push": {
                                "k": "$field_value",
                                "v": {
                                    "$mergeObjects": [
                                        "$statusValues",
                                        {"user_count": "$user_count"},
                                    ]
                                },
                            }
                        },
                    }
                },
                {
                    "$project": {
                        "_id": 0,
                        **{output_key: {"$arrayToObject": "$entries"}},
                    }
                },
            ]

        return get_field_aggregation_pipeline

    # 4. Factory function for product field aggregation with unique value counting
    def create_product_field_aggregation_pipeline(self, status_func):
        """Create a product field aggregation pipeline factory with the given status determination function"""

        def get_product_field_aggregation_pipeline(
            base_filter_criteria, field_path, output_key
        ):
            return [
                {"$match": base_filter_criteria},
                {
                    "$match": {
                        "product_log": {
                            "$exists": True,
                            "$type": "array",
                            "$nin": [None, []],
                        }
                    }
                },
                {
                    "$project": {
                        "status": status_func,
                        "user_hash": "$user_hash",
                        # Extract unique values for the specified field
                        "unique_values": {
                            "$setUnion": {
                                "$map": {
                                    "input": "$product_log",
                                    "as": "item",
                                    "in": f"$$item.{field_path}",
                                }
                            }
                        },
                    }
                },
                # Unwind the unique values instead of the whole product_log
                {
                    "$unwind": {
                        "path": "$unique_values",
                        "preserveNullAndEmptyArrays": True,
                    }
                },
                # Filter out documents where the field doesn't exist or is '' (empty string)
                {
                    "$match": {
                        "unique_values": {
                            "$exists": True,
                            "$nin": ["", None],
                        }
                    }
                },
                {
                    "$project": {
                        "field_value": "$unique_values",
                        "status": "$status",
                        "user_hash": "$user_hash",
                    }
                },
                # The rest is the same pattern as the original pipeline
                {
                    "$group": {
                        "_id": {
                            "field_value": "$field_value",
                            "status": "$status",
                        },
                        "count": {"$sum": 1},
                        "user_hashes": {"$addToSet": "$user_hash"},
                    }
                },
                {
                    "$group": {
                        "_id": "$_id.field_value",
                        "stats": {
                            "$push": {"status": "$_id.status", "count": "$count"}
                        },
                        "all_user_hashes": {"$push": "$user_hashes"},
                    }
                },
                {
                    "$project": {
                        "_id": 0,
                        "field_value": "$_id",
                        "statusCounts": "$stats",
                        "user_count": {
                            "$size": {
                                "$setUnion": {
                                    "$reduce": {
                                        "input": "$all_user_hashes",
                                        "initialValue": [],
                                        "in": {"$setUnion": ["$$value", "$$this"]},
                                    }
                                }
                            },
                        },
                    }
                },
                {
                    "$project": {
                        "field_value": 1,
                        "statusValues": {
                            "$arrayToObject": {
                                "$map": {
                                    "input": "$statusCounts",
                                    "as": "item",
                                    "in": {"k": "$$item.status", "v": "$$item.count"},
                                }
                            }
                        },
                        "user_count": 1,
                    }
                },
                {
                    "$group": {
                        "_id": None,
                        "entries": {
                            "$push": {
                                "k": "$field_value",
                                "v": {
                                    "$mergeObjects": [
                                        "$statusValues",
                                        {"user_count": "$user_count"},
                                    ]
                                },
                            }
                        },
                    }
                },
                {
                    "$project": {
                        "_id": 0,
                        **{output_key: {"$arrayToObject": "$entries"}},
                    }
                },
            ]

        return get_product_field_aggregation_pipeline

    def create_recent_query_aggregation_pipeline(self):
        """Create a recent query aggregation pipeline factory"""

        def get_recent_query_aggregation_pipeline(
            base_filter_criteria, output_key="recentQuery"
        ):
            return [
                # Stage 1: Match documents based on filter criteria
                {"$match": base_filter_criteria},
                # Stage 2: Sort by created_on in descending order (most recent first)
                {"$sort": {"created_on": -1}},
                # Stage 3: Limit to the 100 most recent documents
                {"$limit": 100},
                # Stage 4: Project the fields we want to collect
                {
                    "$project": {
                        "_id": 0,
                        "message": 1,
                        "user_content": "$log.user_content",
                        "response": "$log.full_response",
                        "comment": {"$ifNull": ["$appraisal.comment", ""]},
                    }
                },
                # Stage 5: Group all documents to create the array
                {
                    "$group": {
                        "_id": None,
                        **{
                            output_key: {
                                "$push": {
                                    "message": "$message",
                                    "user_content": "$user_content",
                                    "response": "$response",
                                    "comment": "$comment",
                                }
                            }
                        },
                    }
                },
                # Stage 6: Project to exclude _id field
                {"$project": {"_id": 0}},
            ]

        return get_recent_query_aggregation_pipeline

    def create_distinct_count_by_time_pipeline(self, field_name, interval):
        """
        Factory function that creates a pipeline generator for counting distinct users by time interval.

        Parameters:
        - field_name: The field to count distinct values of
        - interval: String indicating time grouping ('daily', 'weekly', or 'monthly')

        Returns a pipeline that produces:
        {"byTime": {"2025-02-15": 2, "2025-02-16": 3, ...}} for daily
        {"byTime": {"2025-05": 120, "2025-06": 145, ...}} for monthly
        {"byTime": {"2025-01": 47, "2025-02": 53, ...}} for weekly (ISO week format)
        """

        def get_time_format(interval):
            if interval == "daily":
                return "%Y-%m-%d"
            elif interval == "weekly":
                return "%G-W%V"  # ISO week year and week number
            elif interval == "monthly":
                return "%Y-%m"
            else:
                raise ValueError(
                    "Invalid interval. Must be 'daily', 'weekly', or 'monthly'"
                )

        # Set default interval if not provided
        if interval is None:
            interval = "daily"

        time_format = get_time_format(interval)

        def get_distinct_count_by_time_pipeline(
            base_filter_criteria, output_key="byTime"
        ):
            # Get timezone from input params, default to UTC
            timezone_str = getattr(self.input_params, "timezone", None)

            # Prepare the date formatting options
            date_to_string_options = {"format": time_format, "date": "$created_on"}

            # Validate and add timezone parameter if specified
            if timezone_str:
                try:
                    # Verify timezone is valid
                    pytz.timezone(timezone_str)
                    # If valid, add to options
                    date_to_string_options["timezone"] = timezone_str
                except pytz.exceptions.UnknownTimeZoneError:
                    # Handle invalid timezone
                    raise ValueError(f"Invalid timezone: '{timezone_str}'")

            return [
                {"$match": base_filter_criteria},
                {"$match": {field_name: {"$exists": True, "$nin": ["", None]}}},
                # Group by date interval and collect unique field values
                {
                    "$group": {
                        "_id": {"$dateToString": date_to_string_options},
                        "count": {"$addToSet": f"${field_name}"},
                    }
                },
                # Count unique values and format for output
                {"$project": {"_id": 0, "k": "$_id", "v": {"$size": "$count"}}},
                # Group all into a single document
                {"$group": {"_id": None, "pairs": {"$push": {"k": "$k", "v": "$v"}}}},
                # Convert to desired output format
                {"$project": {"_id": 0, **{output_key: {"$arrayToObject": "$pairs"}}}},
            ]

        return get_distinct_count_by_time_pipeline

    # ======================================================

    def ensure_required_queries_keys(self, d, skip_keys=None):
        if skip_keys is None:
            skip_keys = []

        required_keys = {"success": 0, "error": 0, "timeout": 0, "incomplete": 0}

        # Check if the current dict has any dict values
        has_nested_dict = any(isinstance(v, dict) for v in d.values())

        if not has_nested_dict:
            # This is a lowest-level dict, ensure required keys exist
            for key, default_value in required_keys.items():
                if key not in d:
                    d[key] = default_value
        else:
            # Recursively process nested dicts
            for key, value in d.items():
                if isinstance(value, dict):
                    if key not in skip_keys or value != {}:
                        self.ensure_required_queries_keys(value, skip_keys)

    def dashboard_queries_v2(self):
        """
        Dashboard queries API
        """
        base_filter_criteria_indexed = self.base_filter_criteria

        status_func = self.get_dashboard_status_expression()
        total_pipeline_generator = self.create_total_counts_pipeline(status_func)
        # time_pipeline_generator = self.create_time_aggregation_pipeline(status_func)
        # field_pipeline_generator = self.create_field_aggregation_pipeline(status_func)

        pipelines = {
            "total": total_pipeline_generator(base_filter_criteria_indexed),
            # "byTime": time_pipeline_generator(base_filter_criteria),
            # "byCountry": field_pipeline_generator(
            #     base_filter_criteria, "country_code", "byCountry"
            # ),
            # "byIntelligence": field_pipeline_generator(
            #     base_filter_criteria, "dashboard_log.intelligence", "byIntelligence"
            # ),
        }

        combined_result = {}

        for key, pipeline in pipelines.items():
            result = list(self.mongo_collection.aggregate(pipeline))
            if result:
                combined_result.update(result[0])
            else:
                combined_result[key] = (
                    {"success": 0, "error": 0, "timeout": 0, "incomplete": 0}
                    if key == "total"
                    else {}
                )

        self.ensure_required_queries_keys(combined_result)
        return {"success": True, "data": combined_result, "message": ""}

    def ensure_required_thumb_keys(self, d, skip_keys=None):
        if skip_keys is None:
            skip_keys = []

        required_keys = {"up": 0, "down": 0, "na": 0}

        # Check if the current dict has any dict values
        has_nested_dict = any(isinstance(v, dict) for v in d.values())

        if not has_nested_dict:
            # This is a lowest-level dict, ensure required keys exist
            for key, default_value in required_keys.items():
                if key not in d:
                    d[key] = default_value
        else:
            # Recursively process nested dicts
            for key, value in d.items():
                if isinstance(value, dict):
                    if key not in skip_keys or value != {}:
                        self.ensure_required_thumb_keys(value, skip_keys)

    def dashboard_thumbs_v3(self):
        """
        Dashboard thumbs API with parallel pipeline execution using ThreadPoolExecutor
        """
        base_filter_criteria_indexed = self.base_filter_criteria

        # Generate all pipeline functions
        status_func = self.get_appraisal_status_expression()
        total_pipeline_generator = self.create_total_counts_pipeline(status_func)
        time_pipeline_generator = self.create_time_aggregation_pipeline(
            status_func, self.input_params.interval
        )
        field_pipeline_generator = self.create_field_aggregation_pipeline(status_func)
        product_field_pipeline_generator = (
            self.create_product_field_aggregation_pipeline(status_func)
        )
        recent_query_pipeline_generator = (
            self.create_recent_query_aggregation_pipeline()
        )

        # Create the dictionary of pipelines to run
        pipelines = {
            "total": total_pipeline_generator(base_filter_criteria_indexed),
            "byTime": time_pipeline_generator(base_filter_criteria_indexed),
            "byCountry": field_pipeline_generator(
                base_filter_criteria_indexed, "country_code", "byCountry"
            ),
            "byIntelligence": field_pipeline_generator(
                base_filter_criteria_indexed,
                "dashboard_log.intelligence",
                "byIntelligence",
            ),
            "byChannel": field_pipeline_generator(
                base_filter_criteria_indexed, "channel", "byChannel"
            ),
            "bySubsidiary": field_pipeline_generator(
                base_filter_criteria_indexed, "subsidiary", "bySubsidiary"
            ),
            "byProductLine": product_field_pipeline_generator(
                base_filter_criteria_indexed, "product_line", "byProductLine"
            ),
            "byProductName": product_field_pipeline_generator(
                base_filter_criteria_indexed, "product_name", "byProductName"
            ),
            "recentQuery": recent_query_pipeline_generator(
                base_filter_criteria_indexed
            ),
        }

        # Function to execute a single pipeline and handle its result
        def execute_pipeline(key, pipeline):
            # Let exceptions propagate up
            result = list(self.mongo_collection.aggregate(pipeline))
            if result:
                if key == "byTime":
                    self.dash_utils_class.fill_missing_dates(
                        result[0]["byTime"],
                        self.input_params.interval,
                        {"up": 0, "down": 0, "na": 0},
                    )
                return result[0]
            else:
                # For total, return a default structure
                if key == "total":
                    # Ensure we always have the required keys
                    return {"total": {"up": 0, "down": 0, "na": 0}}
                # For recentQuery, return an empty array
                if key == "recentQuery":
                    return {key: []}
                # For other keys, return an empty dict
                return {key: {}}

        # Execute all pipelines in parallel using ThreadPoolExecutor
        combined_result = {}

        # Limit max workers to avoid overwhelming MongoDB connections
        max_workers = min(len(pipelines), 10)

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Process results in same order as keys
            results = executor.map(
                lambda k: execute_pipeline(k, pipelines[k]), pipelines.keys()
            )
            for result in results:
                combined_result.update(result)

        self.ensure_required_thumb_keys(
            combined_result,
            [
                "byTime",
                "byCountry",
                "byIntelligence",
                "byChannel",
                "bySubsidiary",
                "byProductLine",
                "byProductName",
                "recentQuery",
            ],
        )

        # Decrypt the combined result
        decrypted_combined_result = recursive_decrypt_strings(combined_result)
        return {"success": True, "data": decrypted_combined_result, "message": ""}

    def dashboard_users(self):
        """
        Dashboard users API
        """
        base_filter_criteria_indexed = self.base_filter_criteria

        # Add user_hash filter to the base criteria
        base_filter_criteria_indexed_total_copy = base_filter_criteria_indexed.copy()
        base_filter_criteria_indexed_total_copy["user_hash"] = {
            "$exists": True,
            "$nin": ["", None],
        }

        total_distinct_user_count = len(
            self.mongo_collection.distinct(
                "user_hash", base_filter_criteria_indexed_total_copy
            )
        )
        distinct_count_by_time_generator = self.create_distinct_count_by_time_pipeline(
            "user_hash", self.input_params.interval
        )

        pipelines = {
            "byTime": distinct_count_by_time_generator(base_filter_criteria_indexed),
        }

        combined_result = {"total": total_distinct_user_count}

        for key, pipeline in pipelines.items():
            result = list(self.mongo_collection.aggregate(pipeline))
            if result:
                if key == "byTime":
                    self.dash_utils_class.fill_missing_dates(
                        result[0]["byTime"], self.input_params.interval, 0
                    )
                combined_result.update(result[0])
            else:
                combined_result[key] = 0 if key == "total" else {}

        return {"success": True, "data": combined_result, "message": ""}

    def dashboard_divisions(self):
        """
        Dashboard divisions API

        Returns a dictionary with counts of documents grouped by product division categories.
        """
        base_filter_criteria_indexed = self.base_filter_criteria

        default_output = {
            "total": 0,
            "byDivision": {
                "MX": 0,
                "VD": 0,
                "DA": 0,
                "Cross Product": 0,
                "Not Applicable": 0,
            },
        }

        # Get the total count of documents matching the base filter criteria
        total_count = self.mongo_collection.count_documents(
            base_filter_criteria_indexed
        )

        # If no documents match the criteria, return default output
        if total_count == 0:
            return {"success": True, "data": default_output, "message": ""}

        # Get the product division status expression and create pipeline using total_counts_pipeline
        status_func = self.get_product_division_status_expression()
        division_pipeline_generator = self.create_total_counts_pipeline(status_func)

        # Generate and run the pipeline
        pipeline = division_pipeline_generator(
            base_filter_criteria_indexed, "byDivision"
        )

        result = list(self.mongo_collection.aggregate(pipeline))

        # If no results, return default output
        if not result or "byDivision" not in result[0]:
            return {
                "success": True,
                "data": default_output,
                "message": "Division data not found",
            }

        # Create ordered result using default output structure
        result[0]["byDivision"] = {
            key: result[0]["byDivision"].get(key, 0)
            for key in default_output["byDivision"].keys()
        }

        # Combine the total count with the division counts
        combined_result = {
            "total": total_count,
            "byDivision": result[0]["byDivision"],
        }

        return {"success": True, "data": combined_result, "message": ""}

    def dashboard_thumbs_detail_dict_formatting(self, result, thumb_up):
        """
        Format the result of the dashboard_thumbs_detail result into a more readable format,
        grouping reasons by categories
        Args:
            result: The aggregation result
            thumb_up: The thumb up value to filter for (True for up, False for down, None for both)
        """
        # Check if channel is not none and not empty
        if not self.input_params.channel:
            raise ValueError("Channel is required for thumbs detail")

        # Check if channel has more than one value
        if len(self.input_params.channel) > 1:
            raise ValueError("Channel should have only one value for thumbs detail")

        # Initialize structure to collect data by category
        categorized_data = {}
        error_message = ""

        # Process thumbs down selections if needed
        if thumb_up is None or thumb_up is False:
            # Get the thumbs down selection mapping
            down_mapping = (
                Channel_Appraisal.objects.filter(
                    channel=self.input_params.channel[0], thumb_up=False
                )
                .values("appraisal_selection")
                .first()
            )

            if down_mapping and down_mapping.get("appraisal_selection"):
                for original_key, new_key_data in down_mapping[
                    "appraisal_selection"
                ].items():
                    reason = new_key_data.get("reason", original_key)
                    category = new_key_data.get("category", "default")
                    value = result.get(f"down_{original_key}", 0)

                    # Initialize category dict if it doesn't exist
                    if category not in categorized_data:
                        categorized_data[category] = {}

                    # Add or update reason count in the appropriate category
                    categorized_data[category][reason] = (
                        categorized_data[category].get(reason, 0) + value
                    )

            elif thumb_up is False:
                error_message = (
                    "No thumbs down selection mapping found for this channel"
                )

        # Process thumbs up selections if needed
        if thumb_up is None or thumb_up is True:
            # Get the thumbs up selection mapping
            up_mapping = (
                Channel_Appraisal.objects.filter(
                    channel=self.input_params.channel[0], thumb_up=True
                )
                .values("appraisal_selection")
                .first()
            )

            if up_mapping and up_mapping.get("appraisal_selection"):
                for original_key, new_key_data in up_mapping[
                    "appraisal_selection"
                ].items():
                    reason = new_key_data.get("reason", original_key)
                    category = new_key_data.get("category", "default")
                    value = result.get(f"up_{original_key}", 0)

                    # Initialize category dict if it doesn't exist
                    if category not in categorized_data:
                        categorized_data[category] = {}

                    # Add or update reason count in the appropriate category
                    categorized_data[category][reason] = (
                        categorized_data[category].get(reason, 0) + value
                    )

            elif thumb_up is True:
                error_message = "No thumbs up selection mapping found for this channel"

        # If thumb type was specified in the input params, filter to only that category
        if self.input_params.thumb_type:
            # Check if we should filter by category
            matching_categories = {
                k: v
                for k, v in categorized_data.items()
                if k == self.input_params.thumb_type
            }
            if matching_categories:
                categorized_data = matching_categories
            else:
                # If no matching category, look for a reason that matches
                for category, reasons in list(categorized_data.items()):
                    if self.input_params.thumb_type in reasons:
                        # Keep only this reason
                        categorized_data[category] = {
                            self.input_params.thumb_type: reasons[
                                self.input_params.thumb_type
                            ]
                        }
                    else:
                        # Remove categories without the requested thumb_type
                        del categorized_data[category]

        return categorized_data, error_message

    def dashboard_thumbs_detail(self):
        """
        Dashboard thumbs detail API - supports both thumbs up and thumbs down data
        """
        base_filter_criteria_indexed = self.base_filter_criteria

        thumb_up = None

        # Ensure channel is specified in the input params
        if not self.input_params.channel:
            raise ValueError("Channel is required for thumbs detail")

        # Ensure channel has only one value
        if len(self.input_params.channel) > 1:
            raise ValueError("Channel should have only one value for thumbs detail")

        # Make sure thumb up value is either up or down and only one value
        if self.input_params.thumb_up:
            if len(self.input_params.thumb_up) > 1:
                raise ValueError("Thumb up filter should have only one value")

            if self.input_params.thumb_up[0] not in ["up", "down"]:
                raise ValueError("Thumb up filter should be either 'up' or 'down'")

            # Convert thumb_up value to boolean
            thumb_up = True if self.input_params.thumb_up[0] == "up" else False

            # Apply thumb_up filter
            base_filter_criteria_indexed["appraisal.thumb_up"] = thumb_up

        # Ensure appraisal.selection is treated as an array in the query
        if "appraisal.selection" not in base_filter_criteria_indexed:
            base_filter_criteria_indexed["appraisal.selection"] = {
                "$type": "array",
            }

        # Define the aggregation pipeline
        pipeline = [
            {
                "$match": base_filter_criteria_indexed,
            },
            {
                "$facet": {
                    "total": [{"$count": "count"}],
                    "selections": [
                        {
                            "$project": {
                                "_id": 0,
                                "selection_group": {
                                    "$cond": [
                                        {"$eq": [{"$size": "$appraisal.selection"}, 0]},
                                        ["no_selection"],
                                        "$appraisal.selection",
                                    ]
                                },
                                "thumb_up": "$appraisal.thumb_up",
                            }
                        },
                        {"$unwind": "$selection_group"},
                        {
                            "$group": {
                                "_id": {
                                    "selection": "$selection_group",
                                    "thumb_up": "$thumb_up",
                                },
                                "count": {"$sum": 1},
                            }
                        },
                        {"$sort": {"_id.selection": 1}},
                        {
                            "$project": {
                                "_id": 0,
                                "key": {
                                    "$concat": [
                                        {"$cond": ["$_id.thumb_up", "up_", "down_"]},
                                        {"$toString": "$_id.selection"},
                                    ]
                                },
                                "count": "$count",
                            }
                        },
                        {
                            "$group": {
                                "_id": None,
                                "counts": {"$push": {"k": "$key", "v": "$count"}},
                            }
                        },
                        {"$replaceRoot": {"newRoot": {"$arrayToObject": "$counts"}}},
                    ],
                }
            },
            {
                "$project": {
                    "total": {"$first": "$total.count"},
                    "selections": {"$first": "$selections"},
                }
            },
            {
                "$replaceRoot": {
                    "newRoot": {"$mergeObjects": ["$selections", {"total": "$total"}]}
                }
            },
        ]

        result = list(self.mongo_collection.aggregate(pipeline))

        # Format the result (empty dict if no results)
        formatted_result, error_message = self.dashboard_thumbs_detail_dict_formatting(
            result[0] if result else {}, thumb_up
        )

        # Return the final result
        return {
            "success": True,
            "data": formatted_result,
            "message": error_message
            or (
                "No data available from the selected criteria"
                if not result or result[0].get("total") is None
                else ""
            ),
        }

    def dashboard_response_dict_formatting(self, result):
        """
        Format the result of the dashboard_response result into a more readable format
        """
        # Initialize ordered result structure
        new_result = {
            "byStep": {"LLM": {}, "Module": {}, "Section": {}, "Pipeline": {}}
        }

        # Process existing data first
        result_data = result.get("byStep", {})

        # Handle total data (Start of Stream equivalent)
        if "total" in result and result["total"]:
            result_data["Start of Stream"] = result["total"]

        # Build ordered results using for loops to maintain dictionary order
        # LLM modules in order
        for key, display_name in self.module_mapping["LLM"].items():
            new_result["byStep"]["LLM"][display_name] = result_data.get(
                key, {"min": 0, "max": 0, "avg": 0}
            )

        # Module modules in order
        for key, display_name in self.module_mapping["MODULE"].items():
            new_result["byStep"]["Module"][display_name] = result_data.get(
                key, {"min": 0, "max": 0, "avg": 0}
            )

        # Section modules in order
        for key, display_name in self.module_mapping["SECTION"].items():
            new_result["byStep"]["Section"][display_name] = result_data.get(
                key, {"min": 0, "max": 0, "avg": 0}
            )

        # Pipeline modules in order
        for key, display_name in self.module_mapping["PIPELINE"].items():
            new_result["byStep"]["Pipeline"][display_name] = result_data.get(
                key, {"min": 0, "max": 0, "avg": 0}
            )

        return new_result

    def dashboard_response(self):
        """
        Dashboard response API
        """
        base_filter_criteria_indexed = self.base_filter_criteria

        # Modify the base filter criteria to include only documents with no error or timeout
        base_filter_criteria_indexed.update(
            {
                "dashboard_log.error": {"$eq": False},
                "dashboard_log.timeout": {"$eq": False},
            }
        )

        # Combine all module names for the filter
        all_modules = (
            list(self.module_mapping["LLM"].keys())
            + list(self.module_mapping["MODULE"].keys())
            + list(self.module_mapping["SECTION"].keys())
            + list(self.module_mapping["PIPELINE"].keys())
        )
        filter_modules = {"timing_log.name": {"$in": all_modules}}

        pipeline = [
            {"$match": base_filter_criteria_indexed},
            {
                "$facet": {
                    "steps_data": [  # Using a consistent internal name
                        {"$unwind": "$timing_log"},
                        {"$unwind": "$timing_log.executions"},
                        # Filter out null duration values and ensure it's a number
                        {
                            "$match": {
                                "timing_log.executions.duration": {
                                    "$exists": True,
                                    "$ne": None,
                                    "$type": "number",
                                }
                            }
                        },
                        # Apply module filter if provided
                        *([{"$match": filter_modules}] if filter_modules else []),
                        {
                            "$group": {
                                "_id": "$timing_log.name",
                                "min": {"$min": "$timing_log.executions.duration"},
                                "max": {"$max": "$timing_log.executions.duration"},
                                "avg": {"$avg": "$timing_log.executions.duration"},
                            }
                        },
                        {
                            "$group": {
                                "_id": None,
                                "steps": {
                                    "$push": {
                                        "k": "$_id",
                                        "v": {
                                            "min": {
                                                "$round": [
                                                    {"$ifNull": ["$min", 0]},
                                                    4,
                                                ]
                                            },
                                            "max": {
                                                "$round": [
                                                    {"$ifNull": ["$max", 0]},
                                                    4,
                                                ]
                                            },
                                            "avg": {
                                                "$round": [
                                                    {"$ifNull": ["$avg", 0]},
                                                    4,
                                                ]
                                            },
                                        },
                                    }
                                },
                            }
                        },
                        {
                            "$project": {
                                "_id": 0,
                                "data": {"$arrayToObject": "$steps"},
                            }
                        },
                    ],
                    "total": [
                        # Also ensure we filter null or invalid elapsed_time values
                        {
                            "$match": {
                                "elapsed_time": {
                                    "$exists": True,
                                    "$ne": None,
                                    "$type": "number",
                                }
                            }
                        },
                        {
                            "$group": {
                                "_id": None,
                                "min": {"$min": "$elapsed_time"},
                                "max": {"$max": "$elapsed_time"},
                                "avg": {"$avg": "$elapsed_time"},
                            }
                        },
                        {
                            "$project": {
                                "_id": 0,
                                "min": {"$round": [{"$ifNull": ["$min", 0]}, 4]},
                                "max": {"$round": [{"$ifNull": ["$max", 0]}, 4]},
                                "avg": {"$round": [{"$ifNull": ["$avg", 0]}, 4]},
                            }
                        },
                    ],
                }
            },
            {
                "$project": {
                    **{"byStep": {"$ifNull": [{"$first": "$steps_data.data"}, {}]}},
                    "total": {
                        "$ifNull": [
                            {"$first": "$total"},
                            {"min": 0, "max": 0, "avg": 0},
                        ]
                    },
                }
            },
        ]

        # Execute the pipeline
        result = list(self.mongo_collection.aggregate(pipeline))

        # Process the result
        if result:
            formatted_result = self.dashboard_response_dict_formatting(result[0])
            return {"success": True, "data": formatted_result, "message": ""}
        else:
            # Return default output when no results found
            default_output = {
                "byStep": {"LLM": {}, "Module": {}, "Section": {}, "Pipeline": {}}
            }
            return {
                "success": True,
                "data": default_output,
                "message": "No data available from the selected criteria",
            }

    def dashboard_response_interval(self):
        """
        Dashboard response interval API - returns time-based pipeline latency data
        """
        base_filter_criteria_indexed = self.base_filter_criteria

        # Modify the base filter criteria to include only documents with no error or timeout
        base_filter_criteria_indexed.update(
            {
                "dashboard_log.error": {"$eq": False},
                "dashboard_log.timeout": {"$eq": False},
            }
        )

        # Define all the module names to filter
        module_list = [
            "RAG Completion Time",
            "LLM Processing Time",
            "Start of Stream",
            "End of Stream",
        ]
        filter_modules = {"timing_log.name": {"$in": module_list}}

        # Get time format based on interval
        def get_time_format(interval):
            if interval == "1H":
                return "%Y-%m-%dT%H:00:00"
            elif interval == "6H":
                return "%Y-%m-%dT%H:00:00"
            elif interval == "1D":
                return "%Y-%m-%dT00:00:00"
            else:
                raise ValueError("Invalid interval. Must be '1H', '6H', or '1D'")

        # Set default interval if not provided
        if self.input_params.interval is None:
            self.input_params.interval = "6H"

        time_format = get_time_format(self.input_params.interval)
        timezone_str = getattr(self.input_params, "timezone", None) or "UTC"
        try:
            pytz.timezone(timezone_str)
            # Handle different time formats
            if self.input_params.interval == "6H":
                # For 6H with timezone, first convert to timezone, then do the math
                date_expression = {
                    "$dateToString": {
                        "format": time_format,
                        "timezone": timezone_str,
                        "date": {
                            "$dateFromParts": {
                                "year": {
                                    "$year": {
                                        "date": "$created_on",
                                        "timezone": timezone_str,
                                    }
                                },
                                "month": {
                                    "$month": {
                                        "date": "$created_on",
                                        "timezone": timezone_str,
                                    }
                                },
                                "day": {
                                    "$dayOfMonth": {
                                        "date": "$created_on",
                                        "timezone": timezone_str,
                                    }
                                },
                                "hour": {
                                    "$multiply": [
                                        {
                                            "$floor": {
                                                "$divide": [
                                                    {
                                                        "$hour": {
                                                            "date": "$created_on",
                                                            "timezone": timezone_str,
                                                        }
                                                    },
                                                    6,
                                                ]
                                            }
                                        },
                                        6,
                                    ]
                                },
                                "timezone": timezone_str,
                            }
                        },
                    }
                }

            else:
                # For 1H and 1D intervals, use standard dateToString
                date_expression = {
                    "$dateToString": {
                        "format": time_format,
                        "timezone": timezone_str,
                        "date": "$created_on",
                    }
                }

        except pytz.exceptions.UnknownTimeZoneError:
            raise ValueError(f"Invalid timezone: '{timezone_str}'")

        # Create the aggregation pipeline
        pipeline = [
            {"$match": base_filter_criteria_indexed},
            {"$unwind": "$timing_log"},
            {"$unwind": "$timing_log.executions"},
            # Filter out null duration values and ensure it's a number
            {
                "$match": {
                    "timing_log.executions.duration": {
                        "$exists": True,
                        "$ne": None,
                        "$type": "number",
                    }
                }
            },
            # Apply module filter if provided
            {"$match": filter_modules},
            # Group by time interval and module name
            {
                "$group": {
                    "_id": {
                        "time_interval": date_expression,
                        "module_name": "$timing_log.name",
                    },
                    "avg_duration": {"$avg": "$timing_log.executions.duration"},
                }
            },
            # Group by time interval to create nested structure
            {
                "$group": {
                    "_id": "$_id.time_interval",
                    "modules": {
                        "$push": {
                            "k": "$_id.module_name",
                            "v": {"$round": ["$avg_duration", 2]},
                        }
                    },
                }
            },
            # Convert modules array to object and format final structure
            {
                "$project": {
                    "_id": 0,
                    "k": "$_id",
                    "v": {"$arrayToObject": "$modules"},
                }
            },
            # Group all time intervals into final structure
            {
                "$group": {
                    "_id": None,
                    "time_data": {"$push": {"k": "$k", "v": "$v"}},
                }
            },
            # Final projection to create the desired output structure
            {
                "$project": {
                    "_id": 0,
                    "pipelineLatency": {"$arrayToObject": "$time_data"},
                }
            },
        ]

        # Execute the pipeline
        result = list(self.mongo_collection.aggregate(pipeline))

        # Process the result
        if result:
            data = result[0].get("pipelineLatency", {})
            # Fill missing intervals with empty dict for each missing time slot
            self.dash_utils_class.fill_missing_interval_dates(
                data,
                self.input_params.interval,
                default_value={
                    "RAG Completion Time": 0,
                    "LLM Processing Time": 0,
                    "Start of Stream": 0,
                    "End of Stream": 0,
                },
            )
            return {"success": True, "data": {"pipelineLatency": data}, "message": ""}
        else:
            # Return default output when no results found
            default_output = {
                "pipelineLatency": {
                    "RAG Completion Time": 0,
                    "LLM Processing Time": 0,
                    "Start of Stream": 0,
                    "End of Stream": 0,
                }
            }
            return {
                "success": True,
                "data": default_output,
                "message": "No data available from the selected criteria",
            }
