import sys

sys.path.append("/www/alpha/")
import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "alpha.settings")
django.setup()

import pandas as pd
import pytz

from dataclasses import dataclass

from apps.rubicon_v3.__function.__encryption_utils import recursive_decrypt_strings
from apps.rubicon_v3.__api.__utils import (
    DashUtils,
    extract_selected_list,
    extract_product_info,
)
from apps.rubicon_v3.models import Channel

from alpha._db import chat_log_collection, search_log_collection


class AppraisalCheck:
    @dataclass
    class AppraisalCheckParams:
        service: str
        start_date: str
        end_date: str
        timezone: str
        channel: list[str]
        thumb_up: list[str]
        status: list[str]
        page: int
        items_per_page: int

    def __init__(self, input_params: AppraisalCheckParams):
        # Determine which mongo collection to use based on service
        if input_params.service == "chat":
            self.mongo_collection = chat_log_collection
        elif input_params.service == "search":
            self.mongo_collection = search_log_collection
        else:
            raise ValueError("Invalid service type. Must be 'chat' or 'search'.")

        self.input_params = input_params
        self.base_filter_class = DashUtils.from_params(input_params)
        self.base_filter_criteria: dict = (
            self.base_filter_class.get_base_filter_criteria_dict()
        )

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

    def get_appraisal_data(self):
        base_filter_criteria_indexed = self.base_filter_criteria

        # Define the aggregation pipeline
        pipeline = None
        combined_columns = None
        # Calculate skip value for pagination
        skip = (self.input_params.page - 1) * self.input_params.items_per_page
        if self.input_params.service == "chat":
            pipeline = [
                {"$match": base_filter_criteria_indexed},
                {"$sort": {"created_on": -1}},  # Sort by the original field name
                {
                    "$facet": {
                        "metadata": [{"$count": "total"}],
                        "data": [
                            {"$skip": skip},
                            {"$limit": self.input_params.items_per_page},
                            {
                                "$project": {
                                    "_id": 0,
                                    "Message ID": "$message_id",
                                    "Session ID": "$session_id",
                                    "Created On": {
                                        "$dateToString": self.get_date_format_options()
                                    },
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
                                    "Thumbs Up/Down": {
                                        "$cond": [
                                            {
                                                "$eq": [
                                                    {"$objectToArray": "$appraisal"},
                                                    [],
                                                ]
                                            },
                                            "na",
                                            {
                                                "$cond": [
                                                    {
                                                        "$eq": [
                                                            "$appraisal.thumb_up",
                                                            True,
                                                        ]
                                                    },
                                                    "up",
                                                    "down",
                                                ]
                                            },
                                        ]
                                    },
                                    "Selected List": {
                                        "$ifNull": ["$appraisal.selection", []]
                                    },
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
                                                    {
                                                        "$eq": [
                                                            "$dashboard_log.error",
                                                            True,
                                                        ]
                                                    },
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
                        ],
                    }
                },
            ]
            combined_columns = [
                "Message ID",
                "Session ID",
                "Created On",
                "Elapsed Time",
                "Channel",
                "Department",
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
                "Thumbs Up/Down",
                "Selected List",
                "Comment",
                "Status",
            ]
        elif self.input_params.service == "search":
            pipeline = [
                {"$match": base_filter_criteria_indexed},
                {"$sort": {"created_on": -1}},  # Sort by the original field name
                {
                    "$facet": {
                        "metadata": [{"$count": "total"}],
                        "data": [
                            {"$skip": skip},
                            {"$limit": self.input_params.items_per_page},
                            {
                                "$project": {
                                    "_id": 0,
                                    "Message ID": "$message_id",
                                    "Created On": {
                                        "$dateToString": self.get_date_format_options()
                                    },
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
                                    "Thumbs Up/Down": {
                                        "$cond": [
                                            {
                                                "$eq": [
                                                    {"$objectToArray": "$appraisal"},
                                                    [],
                                                ]
                                            },
                                            "na",
                                            {
                                                "$cond": [
                                                    {
                                                        "$eq": [
                                                            "$appraisal.thumb_up",
                                                            True,
                                                        ]
                                                    },
                                                    "up",
                                                    "down",
                                                ]
                                            },
                                        ]
                                    },
                                    "Selected List": {
                                        "$ifNull": ["$appraisal.selection", []]
                                    },
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
                                                    {
                                                        "$eq": [
                                                            "$dashboard_log.error",
                                                            True,
                                                        ]
                                                    },
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
                        ],
                    }
                },
            ]
            combined_columns = [
                "Message ID",
                "Created On",
                "Elapsed Time",
                "Channel",
                "Department",
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
                "Thumbs Up/Down",
                "Selected List",
                "Comment",
                "Status",
            ]

        # Execute the chat_pipeline
        result = list(self.mongo_collection.aggregate(pipeline))

        # Return early if no results found
        if not result:
            return {
                "success": True,
                "data": [],
                "meta": {
                    "headers": combined_columns,
                },
                "pagination": {"page": self.input_params.page, "total_items": 0},
                "message": "No data found for the given filter criteria",
            }

        # Extract the paginated data and total count
        paginated_data = result[0]["data"] if result else []
        total_count = (
            result[0]["metadata"][0]["total"] if result and result[0]["metadata"] else 0
        )

        # Decrypt the paginated data
        decrypted_paginated_data = recursive_decrypt_strings(paginated_data)

        # Convert to DataFrame
        df = pd.DataFrame(data=decrypted_paginated_data, columns=combined_columns)

        # Extract product information
        df["Product Line"] = df["Product Line"].apply(
            lambda x: extract_product_info(x, "product_line")
        )
        df["Product Name"] = df["Product Name"].apply(
            lambda x: extract_product_info(x, "product_name")
        )

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

        # Convert the DataFrame to a list of dictionaries
        data = df.to_dict(orient="records")

        return {
            "success": True,
            "data": data,
            "meta": {
                "headers": combined_columns,
            },
            "pagination": {
                "page": self.input_params.page,
                "total_items": total_count,
            },
            "message": "Data fetched successfully",
        }
