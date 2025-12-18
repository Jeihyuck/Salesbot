import sys

sys.path.append("/www/alpha/")
import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "alpha.settings")
django.setup()

import pandas as pd
import pytz

from dataclasses import dataclass

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
    extract_selected_list,
    extract_product_info,
    extract_division_info,
)
from apps.rubicon_v3.__api.search_summary import (
    _00_search_summary,
    _05_query_expansion,
    _10_simple_ai_search,
)
from apps.rubicon_v3.models import Channel


chat_pipeline_modules = {
    "LLM": {
        _02_language_identification.lang_detect_with_gpt.__name__: "(LLM) Language Detection",
        _10_rewrite.re_write_history.__name__: "(LLM) Re-write",
        _21_orchestrator_query_analyzer.query_analyzer.__name__: "(LLM) Query Analyzer",
        _22_orchestrator_intelligence.intelligence.__name__: "(LLM) Intelligence",
        _20_orchestrator_NER_init.ner.__name__: "(LLM) NER",
        _21_orchestrator_context_determination.context_determination.__name__: "(LLM) Context Determination",
        _31_orchestrator_assistant.assistant.__name__: "(LLM) Assistant",
        _32_sub_intelligence.get_sub_intelligence.__name__: "(LLM) Sub Intelligence",
        _30_orchestrator_NER_standardization.standardize_ner_expression.__name__: "(LLM) Standardized NER",
    },
    "MODULE": {
        _71_product_rag_web_search.get_google_search_results.__name__: "(Module) Web Search",
        _72_product_rag_ai_search.execute_unstructured_rag.__name__: "(Module) AI Search",
        _00_rubicon.ChatFlowSectionNames.MERGE_DATA: "(Module) Merge Data",
    },
    "SECTION": {
        _00_rubicon.ChatFlowSectionNames.PARALLEL_REWRITE_LOADING_MESSAGE_TEXT_CLEANUP_LANGUAGE_DETECT_CORRECTION_DETERMINATION: "(Section) Parallel: Rewrite + Loading Message + Text Cleanup + Language Detect",
        _00_rubicon.ChatFlowSectionNames.PARALLEL_QUERY_ANALYZER_INTELLIGENCE_NER_CONTEXT_DETERMINATION: "(Section) Parallel: Query Analyzer + Intelligence + NER + Context Determination",
        _00_rubicon.ChatFlowSectionNames.PARALLEL_STANDARD_NER_ASSISTANT_SUB_INTELLIGENCE: "(Section) Parallel: Standard NER + Assistant + Sub Intelligence",
        _00_rubicon.ChatFlowSectionNames.PARALLEL_STRUCTURED_COMPLEMENT: "(Section) Parallel: Structured + Complement",
    },
    "PIPELINE": {
        "RAG Completion Time": "(Pipeline) RAG Completion Time",
        "LLM Processing Time": "(Pipeline) LLM Processing Time",
        "Start of Stream": "(Pipeline) Start of Stream",
        "End of Stream": "(Pipeline) End of Stream",
    },
}

search_pipeline_modules = {
    "LLM": {
        _05_query_expansion.query_expansion.__name__: "(LLM) Query Expansion",
        _22_orchestrator_intelligence.intelligence.__name__: "(LLM) Intelligence",
    },
    "MODULE": {
        _10_simple_ai_search.execute_cpt_rag.__name__: "(Module) Simple AI Search",
        _73_product_rag_specification_check.specification_check.__name__: "(Module) Specification Check",
    },
    "SECTION": {
        _00_search_summary.SearchFlowSectionNames.PARALLEL_QUERY_EXPANSION_AI_SEARCH_SPEC_CHECK: "(Section) Parallel: Query Expansion + AI Search + Spec Check",
        _00_search_summary.SearchFlowSectionNames.PARALLEL_PREDEFINED_INTELLIGENCE_GUARDRAILS: "(Section) Parallel: Predefined Intelligence + Guardrails",
    },
    "PIPELINE": {
        "RAG Completion Time": "(Pipeline) RAG Completion Time",
        "LLM Processing Time": "(Pipeline) LLM Processing Time",
        "Start of Stream": "(Pipeline) Start of Stream",
        "End of Stream": "(Pipeline) End of Stream",
    },
}

all_chat_modules_mapping = {
    **chat_pipeline_modules["LLM"],
    **chat_pipeline_modules["MODULE"],
    **chat_pipeline_modules["SECTION"],
    **chat_pipeline_modules["PIPELINE"],
}

all_search_modules_mapping = {
    **search_pipeline_modules["LLM"],
    **search_pipeline_modules["MODULE"],
    **search_pipeline_modules["SECTION"],
    **search_pipeline_modules["PIPELINE"],
}


class DashboardExport:
    @dataclass
    class DashboardExportParams:
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
        locale: str
        status: list[str]

    def __init__(self, input_params: DashboardExportParams):
        # Determine which mongo collection to use based on service
        # Also get the appropriate module mapping
        if input_params.service == "chat":
            self.mongo_collection = chat_log_collection
            self.module_mapping = all_chat_modules_mapping
        elif input_params.service == "search":
            self.mongo_collection = search_log_collection
            self.module_mapping = all_search_modules_mapping
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

    def dashboard_export_api_mux(self):
        # Possible Types: queries, thumbsDetail, response, appraisalCheck
        if self.input_params.api_type == "queries":
            return self.export_queries()
        elif self.input_params.api_type == "thumbsDetail":
            return self.export_thumbs_detail()
        elif self.input_params.api_type == "response":
            return self.export_response()
        elif self.input_params.api_type == "appraisalCheck":
            return self.export_appraisal_check()
        else:
            raise ValueError("Invalid API type")

    def get_date_format_options(
        self, date_field="$created_on", date_format="%Y-%m-%d %H:%M:%S"
    ):
        """Return date formatting options with timezone if specified"""
        options = {"format": date_format, "date": date_field}

        # Add timezone if provided and valid
        if self.input_params.timezone:
            try:
                # Verify timezone is valid
                pytz.timezone(self.input_params.timezone)
                options["timezone"] = self.input_params.timezone
            except pytz.exceptions.UnknownTimeZoneError:
                raise ValueError(f"Invalid timezone: '{self.input_params.timezone}'")

        return options

    def extract_executions_to_columns(self, df, job_name_mapping):
        """
        Extract execution data from timing_log column and create new columns based on job name mapping.
        Optimized for performance with large DataFrames.

        Parameters:
        df: pandas DataFrame containing a 'timing_log' column with list of dictionaries
        job_name_mapping: dictionary mapping job_names to new column names

        Returns:
        pandas.DataFrame: DataFrame with new columns added based on the mapping
        """

        # Create a copy to avoid modifying the original DataFrame
        result_df = df.copy()

        # Initialize new columns with None values
        for column_name in job_name_mapping.values():
            result_df[column_name] = None

        # Function to process a single timing_log entry
        def process_row(row):
            timing_log = row["timing_log"]
            result = {}

            # Skip if timing_log is None or not a list
            if timing_log is None or not isinstance(timing_log, list):
                return row

            # Process each job entry in the timing_log
            for job_entry in timing_log:
                # Skip if entry is not a dictionary or doesn't have required keys
                if (
                    not isinstance(job_entry, dict)
                    or "name" not in job_entry
                    or "executions" not in job_entry
                ):
                    continue

                job_name = job_entry["name"]
                executions = job_entry["executions"]

                # Check if this job_name is in our mapping
                if job_name in job_name_mapping:
                    column_name = job_name_mapping[job_name]
                    # Set the executions list in the new column
                    row[column_name] = executions

            return row

        # Apply the processing function to each row
        result_df = result_df.apply(process_row, axis=1)

        return result_df

    def export_queries(self):
        base_filter_criteria_indexed = self.base_filter_criteria

        # Define the aggregation pipeline
        pipeline = [
            {"$match": base_filter_criteria_indexed},
            {
                "$project": {
                    "_id": 0,
                    "Message ID": "$message_id",
                    "Created On": {"$dateToString": self.get_date_format_options()},
                    "Channel": "$channel",
                    "Subsidiary": "$subsidiary",
                    "Country": "$country_code",
                    "User": "$user_id",
                    "Query": "$message",
                    "Response": "$log.full_response",
                    "Thumbs Up/Down": {
                        "$cond": [
                            {"$eq": [{"$objectToArray": "$appraisal"}, []]},
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
                    "Intelligence": "$dashboard_log.intelligence",
                    "Product Line": "$product_log",
                    "Product Name": "$product_log",
                    "Division": "$product_log",
                    "User Logged In": {
                        "$cond": [
                            {
                                "$eq": [
                                    {"$type": "$dashboard_log.user_logged_in"},
                                    "bool",
                                ]
                            },
                            {
                                "$cond": [
                                    {"$eq": ["$dashboard_log.user_logged_in", True]},
                                    "yes",
                                    "no",
                                ]
                            },
                            "na",
                        ]
                    },
                    "Status": {
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
                    },
                }
            },
            {"$sort": {"Created On": -1}},
        ]

        # Execute the pipeline
        result = list(self.mongo_collection.aggregate(pipeline))

        # Return early if no results found
        if not result:
            return pd.DataFrame(
                columns=[
                    "Message ID",
                    "Created On",
                    "Channel",
                    "Subsidiary",
                    "Country",
                    "User",
                    "Query",
                    "Response",
                    "Thumbs Up/Down",
                    "Intelligence",
                    "Product Line",
                    "Product Name",
                    "Division",
                    "User Logged In",
                    "Status",
                ]
            )

        # Decrypt the result
        decrypted_result = recursive_decrypt_strings(result)

        # Convert to DataFrame
        df = pd.DataFrame(decrypted_result)

        # Extract product information
        df["Product Line"] = df["Product Line"].apply(
            lambda x: extract_product_info(x, "product_line")
        )
        df["Product Name"] = df["Product Name"].apply(
            lambda x: extract_product_info(x, "product_name")
        )

        # Extract the division from product_log
        df["Division"] = df["Division"].apply(extract_division_info)

        # Grab the country_code to country_name map
        countries_data = Channel.objects.values(
            "country_code", "country_name"
        ).distinct("country_code")
        country_map = {
            item["country_code"]: item["country_name"] for item in countries_data
        }

        # Convert the country_code to country names
        df["Country"] = df["Country"].map(country_map).fillna(df["Country"])

        return df

    def export_thumbs_detail(self):
        base_filter_criteria_indexed = self.base_filter_criteria

        # Return early if channel is not specified in the filter criteria
        if not base_filter_criteria_indexed.get("channel"):
            return pd.DataFrame(
                columns=[
                    "Message ID",
                    "Created On",
                    "Channel",
                    "Subsidiary",
                    "Country",
                    "Query",
                    "Intelligence",
                    "Product Line",
                    "Product Name",
                    "Division",
                    "Thumbs Up/Down",
                    "User Logged In",
                    "Selected List",
                    "Comment",
                ]
            )

        # Define the aggregation pipeline
        pipeline = [
            {"$match": base_filter_criteria_indexed},
            {
                "$project": {
                    "_id": 0,
                    "Message ID": "$message_id",
                    "Created On": {"$dateToString": self.get_date_format_options()},
                    "Channel": "$channel",
                    "Subsidiary": "$subsidiary",
                    "Country": "$country_code",
                    "Query": "$message",
                    "Response": "$log.full_response",
                    "Intelligence": "$dashboard_log.intelligence",
                    "Product Line": "$product_log",
                    "Product Name": "$product_log",
                    "Division": "$product_log",
                    "Thumbs Up/Down": {
                        "$cond": [
                            {"$eq": [{"$objectToArray": "$appraisal"}, []]},
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
                    "User Logged In": {
                        "$cond": [
                            {
                                "$eq": [
                                    {"$type": "$dashboard_log.user_logged_in"},
                                    "bool",
                                ]
                            },
                            {
                                "$cond": [
                                    {"$eq": ["$dashboard_log.user_logged_in", True]},
                                    "yes",
                                    "no",
                                ]
                            },
                            "na",
                        ]
                    },
                    "Selected List": "$appraisal.selection",
                    "Comment": "$appraisal.comment",
                }
            },
            {"$sort": {"Created On": -1}},
        ]

        # Execute the pipeline
        result = list(self.mongo_collection.aggregate(pipeline))

        # Return early if no results found
        if not result:
            return pd.DataFrame(
                columns=[
                    "Message ID",
                    "Created On",
                    "Channel",
                    "Subsidiary",
                    "Country",
                    "Query",
                    "Intelligence",
                    "Product Line",
                    "Product Name",
                    "Division",
                    "Thumbs Up/Down",
                    "User Logged In",
                    "Selected List",
                    "Comment",
                ]
            )

        # Decrypt the result
        decrypted_result = recursive_decrypt_strings(result)

        # Convert to DataFrame
        df = pd.DataFrame(decrypted_result)

        # Extract product information
        df["Product Line"] = df["Product Line"].apply(
            lambda x: extract_product_info(x, "product_line")
        )
        df["Product Name"] = df["Product Name"].apply(
            lambda x: extract_product_info(x, "product_name")
        )

        # Extract the division from product_log
        df["Division"] = df["Division"].apply(extract_division_info)

        # Extract the selection type from the appraisal based on channel
        df["Selected List"] = df.apply(extract_selected_list, axis=1)

        # Drop the Thumbs Up/Down column as it was for Selected List extraction
        df.drop(columns=["Thumbs Up/Down"], inplace=True)

        # Grab the country_code to country_name map
        countries_data = Channel.objects.values(
            "country_code", "country_name"
        ).distinct("country_code")
        country_map = {
            item["country_code"]: item["country_name"] for item in countries_data
        }

        # Convert the country_code to country names
        df["Country"] = df["Country"].map(country_map).fillna(df["Country"])

        return df

    def export_response(self):
        base_filter_criteria_indexed = self.base_filter_criteria

        # Define the aggregation pipeline
        pipeline = None
        combined_columns = None
        if self.input_params.service == "chat":
            pipeline = [
                {"$match": base_filter_criteria_indexed},
                {
                    "$project": {
                        "_id": 0,
                        "Message ID": "$message_id",
                        "Session ID": "$session_id",
                        "Created On": {"$dateToString": self.get_date_format_options()},
                        "Channel": "$channel",
                        "Subsidiary": "$subsidiary",
                        "Country": "$country_code",
                        "Query": "$message",
                        "Response": "$log.full_response",
                        "timing_log": "$timing_log",
                    }
                },
                {"$sort": {"Created On": -1}},
            ]
            combined_columns = [
                "Message ID",
                "Session ID",
                "Created On",
                "Channel",
                "Subsidiary",
                "Country",
                "Query",
                "Response",
            ]
        elif self.input_params.service == "search":
            pipeline = [
                {"$match": base_filter_criteria_indexed},
                {
                    "$project": {
                        "_id": 0,
                        "Message ID": "$message_id",
                        "Created On": {"$dateToString": self.get_date_format_options()},
                        "Channel": "$channel",
                        "Subsidiary": "$subsidiary",
                        "Country": "$country_code",
                        "Query": "$message",
                        "Response": "$log.full_response",
                        "timing_log": "$timing_log",
                    }
                },
                {"$sort": {"Created On": -1}},
            ]
            combined_columns = [
                "Message ID",
                "Created On",
                "Channel",
                "Subsidiary",
                "Country",
                "Query",
                "Response",
            ]

        # Execute the pipeline
        result = list(self.mongo_collection.aggregate(pipeline))

        # Return early if no results found
        if not result:
            function_names = list(self.module_mapping.values())
            combined_columns.extend(function_names)
            return pd.DataFrame(columns=combined_columns)

        # Decrypt the result
        decrypted_result = recursive_decrypt_strings(result)

        # Convert to DataFrame
        df = pd.DataFrame(decrypted_result)

        # Grab the country_code to country_name map
        countries_data = Channel.objects.values(
            "country_code", "country_name"
        ).distinct("country_code")
        country_map = {
            item["country_code"]: item["country_name"] for item in countries_data
        }

        # Convert the country_code to country names
        df["Country"] = df["Country"].map(country_map).fillna(df["Country"])

        # Extract executions data from timing_log
        df = self.extract_executions_to_columns(df, self.module_mapping)

        # Drop the timing_log column
        df.drop(columns=["timing_log"], inplace=True)

        return df

    def export_appraisal_check(self):
        base_filter_criteria_indexed = self.base_filter_criteria

        # Define the aggregation pipeline
        pipeline = None
        combined_columns = None
        if self.input_params.service == "chat":
            pipeline = [
                {"$match": base_filter_criteria_indexed},
                {
                    "$project": {
                        "_id": 0,
                        "Message ID": "$message_id",
                        "Session ID": "$session_id",
                        "Created On": {"$dateToString": self.get_date_format_options()},
                        "Elapsed Time": "$elapsed_time",
                        "Channel": "$channel",
                        "Department": "$department",
                        "Subsidiary": "$subsidiary",
                        "Country": "$country_code",
                        "User": "$user_id",
                        "Query": "$message",
                        "User Content": "$log.user_content",
                        "Response": "$log.full_response",
                        "Intelligence": "$dashboard_log.intelligence",
                        "Sub-Intelligence": "$dashboard_log.sub_intelligence",
                        "Product Line": "$product_log",
                        "Product Name": "$product_log",
                        "Division": "$product_log",
                        "User Logged In": {
                            "$cond": [
                                {
                                    "$eq": [
                                        {"$type": "$dashboard_log.user_logged_in"},
                                        "bool",
                                    ]
                                },
                                {
                                    "$cond": [
                                        {
                                            "$eq": [
                                                "$dashboard_log.user_logged_in",
                                                True,
                                            ]
                                        },
                                        "yes",
                                        "no",
                                    ]
                                },
                                "na",
                            ]
                        },
                        "Thumbs Up/Down": {
                            "$cond": [
                                {"$eq": [{"$objectToArray": "$appraisal"}, []]},
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
                        "Selected List": {"$ifNull": ["$appraisal.selection", []]},
                        "Comment": {"$ifNull": ["$appraisal.comment", ""]},
                        "Status": {
                            "$cond": [
                                # First check for explicit success case - both flags are false
                                {
                                    "$and": [
                                        {
                                            "$eq": [
                                                "$dashboard_log.error",
                                                False,
                                            ]
                                        },
                                        {
                                            "$eq": [
                                                "$dashboard_log.timeout",
                                                False,
                                            ]
                                        },
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
                                                {
                                                    "$eq": [
                                                        "$dashboard_log.timeout",
                                                        True,
                                                    ]
                                                },
                                                "timeout",
                                                "incomplete",  # Default when conditions aren't explicitly defined
                                            ]
                                        },
                                    ]
                                },
                            ]
                        },
                    }
                },
                {"$sort": {"Created On": -1}},
            ]
            combined_columns = [
                "Message ID",
                "Session ID",
                "Created On",
                "Elapsed Time",
                "Channel",
                "Subsidiary",
                "Country",
                "User",
                "Query",
                "User Content",
                "Response",
                "Intelligence",
                "Sub-Intelligence",
                "Product Line",
                "Product Name",
                "Division",
                "User Logged In",
                "Thumbs Up/Down",
                "Selected List",
                "Comment",
                "Status",
            ]
        elif self.input_params.service == "search":
            pipeline = [
                {"$match": base_filter_criteria_indexed},
                {
                    "$project": {
                        "_id": 0,
                        "Message ID": "$message_id",
                        "Created On": {"$dateToString": self.get_date_format_options()},
                        "Elapsed Time": "$elapsed_time",
                        "Channel": "$channel",
                        "Department": "$department",
                        "Subsidiary": "$subsidiary",
                        "Country": "$country_code",
                        "User": "$user_id",
                        "Query": "$message",
                        "Search Results": "$input_log.searchData.searchResults",
                        "User Content": "$log.user_content",
                        "Response": "$log.full_response",
                        "Intelligence": "$dashboard_log.intelligence",
                        "Product Line": "$product_log",
                        "Product Name": "$product_log",
                        "Division": "$product_log",
                        "User Logged In": {
                            "$cond": [
                                {
                                    "$eq": [
                                        {"$type": "$dashboard_log.user_logged_in"},
                                        "bool",
                                    ]
                                },
                                {
                                    "$cond": [
                                        {
                                            "$eq": [
                                                "$dashboard_log.user_logged_in",
                                                True,
                                            ]
                                        },
                                        "yes",
                                        "no",
                                    ]
                                },
                                "na",
                            ]
                        },
                        "Thumbs Up/Down": {
                            "$cond": [
                                {"$eq": [{"$objectToArray": "$appraisal"}, []]},
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
                        "Selected List": {"$ifNull": ["$appraisal.selection", []]},
                        "Comment": {"$ifNull": ["$appraisal.comment", ""]},
                        "Status": {
                            "$cond": [
                                # First check for explicit success case - both flags are false
                                {
                                    "$and": [
                                        {
                                            "$eq": [
                                                "$dashboard_log.error",
                                                False,
                                            ]
                                        },
                                        {
                                            "$eq": [
                                                "$dashboard_log.timeout",
                                                False,
                                            ]
                                        },
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
                                                {
                                                    "$eq": [
                                                        "$dashboard_log.timeout",
                                                        True,
                                                    ]
                                                },
                                                "timeout",
                                                "incomplete",  # Default when conditions aren't explicitly defined
                                            ]
                                        },
                                    ]
                                },
                            ]
                        },
                    }
                },
                {"$sort": {"Created On": -1}},
            ]
            combined_columns = [
                "Message ID",
                "Created On",
                "Elapsed Time",
                "Channel",
                "Subsidiary",
                "Country",
                "User",
                "Query",
                "Search Results",
                "User Content",
                "Response",
                "Intelligence",
                "Product Line",
                "Product Name",
                "Division",
                "User Logged In",
                "Thumbs Up/Down",
                "Selected List",
                "Comment",
                "Status",
            ]

        # Execute the pipeline
        result = list(self.mongo_collection.aggregate(pipeline))

        # Return early if no results found
        if not result:
            return pd.DataFrame(columns=combined_columns)

        # Decrypt the result
        decrypted_result = recursive_decrypt_strings(result)

        # Convert to DataFrame
        df = pd.DataFrame(decrypted_result)

        # Extract product information
        df["Product Line"] = df["Product Line"].apply(
            lambda x: extract_product_info(x, "product_line")
        )
        df["Product Name"] = df["Product Name"].apply(
            lambda x: extract_product_info(x, "product_name")
        )

        # Extract the division from product_log
        df["Division"] = df["Division"].apply(extract_division_info)

        # Extract the selection type from the appraisal based on channel
        df["Selected List"] = df.apply(extract_selected_list, axis=1)

        # Grab the country_code to country_name map
        countries_data = Channel.objects.values(
            "country_code", "country_name"
        ).distinct("country_code")
        country_map = {
            item["country_code"]: item["country_name"] for item in countries_data
        }

        # Convert the country_code to country names
        df["Country"] = df["Country"].map(country_map).fillna(df["Country"])

        # Make sure there are no NaN values in the DataFrame
        df = df.fillna("")

        return df
