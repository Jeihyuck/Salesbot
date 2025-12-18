import sys

sys.path.append("/www/alpha/")

import os
import django
from django.db.models import Q, F

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "alpha.settings")
django.setup()

import re
import pytz
import math
import time
import traceback

from datetime import datetime, timedelta
from dataclasses import dataclass, fields

from apps.rubicon_v3.__function import __rubicon_log as rubicon_log
from apps.rubicon_v3.__api.search_summary import __search_log as search_log
from apps.rubicon_v3.__external_api._14_azure_email_alert import (
    send_process_error_alert,
)
from apps.rubicon_v3.models import Channel, Channel_Appraisal
from apps.rubicon_data.models import product_category, uk_product_spec_basics

from alpha.settings import VITE_OP_TYPE, VITE_COUNTRY
from alpha._db import chat_log_collection, search_log_collection


class DashUtils:
    @dataclass
    class DashUtilsFilterParams:
        start_date: str
        end_date: str
        locale: str
        timezone: str
        channel: list[str]
        country_code: list[str]
        subsidiary: list[str]
        intelligence: list[str]
        product_line: list[str]
        product_name: list[str]
        thumb_type: str
        thumb_up: list[str]
        status: list[str]

    @classmethod
    def from_params(cls, params):
        """Create BaseFilter instance from any params object with compatible attributes."""
        base_filter_params = {}
        base_filter_field_names = {f.name for f in fields(cls.DashUtilsFilterParams)}

        for field_name in base_filter_field_names:
            base_filter_params[field_name] = (
                getattr(params, field_name) if hasattr(params, field_name) else None
            )

        return cls(cls.DashUtilsFilterParams(**base_filter_params))

    def __init__(self, input_params: DashUtilsFilterParams):
        self.input_params = input_params

    def get_base_filter_criteria_dict(self):
        base_filter_criteria_dict = {}

        # Handle Date Filters
        if self.input_params.start_date or self.input_params.end_date:
            self._add_date_filters(base_filter_criteria_dict)

        # Handle Channel, Country Code, Subsidiary Filters
        if any(
            [
                self.input_params.channel,
                self.input_params.country_code,
                self.input_params.subsidiary,
            ]
        ):
            self._add_channel_country_subsidiary_filters(base_filter_criteria_dict)

        # Handle Intelligence Filters
        if self.input_params.intelligence:
            self._add_list_filter(
                base_filter_criteria_dict,
                "dashboard_log.intelligence",
                self.input_params.intelligence,
            )

        # Handle Product Filters
        if self.input_params.product_line or self.input_params.product_name:
            self._add_product_filters(base_filter_criteria_dict)

        # Handle Thumb Type Filters
        if self.input_params.thumb_type:
            self._add_thumb_type_filter(base_filter_criteria_dict)

        # Handle Thumb Up Filters
        if self.input_params.thumb_up:
            self._add_thumb_up_filter(base_filter_criteria_dict)

        # Handle Status Filters
        if self.input_params.status:
            self._add_status_filter(base_filter_criteria_dict)

        # Always include the message_status.completed filter
        base_filter_criteria_dict["message_status.completed"] = True
        base_filter_criteria_dict["message_status.is_hidden"] = {"$ne": True}
        base_filter_criteria_dict["message_status.multi_input"] = {"$ne": True}

        return base_filter_criteria_dict

    def _add_date_filters(self, criteria_dict: dict):
        """Helper method to add date filters"""
        timezone_str = self.input_params.timezone

        for date_type, date_value in [
            ("start_date", self.input_params.start_date),
            ("end_date", self.input_params.end_date),
        ]:
            if not date_value:
                continue

            # Parse the string to datetime object
            date_obj = datetime.strptime(date_value, "%Y-%m-%d %H:%M:%S")

            # Apply timezone if provided
            if timezone_str:
                try:
                    local_tz = pytz.timezone(timezone_str)
                    date_obj = local_tz.localize(date_obj).astimezone(pytz.UTC)
                except pytz.exceptions.UnknownTimeZoneError:
                    raise ValueError(f"Invalid timezone: {timezone_str}")
            else:
                date_obj = date_obj.replace(tzinfo=pytz.UTC)

            # Set the appropriate operator based on date_type
            operator = "$gte" if date_type == "start_date" else "$lt"
            criteria_dict.setdefault("created_on", {})[operator] = date_obj

    def _add_channel_country_subsidiary_filters(self, criteria_dict: dict):
        """Helper method to add channel, country_code and subsidiary filters"""
        # Build the filter criteria dynamically for channel data
        channel_filter_criteria = Q(active=True)
        if self.input_params.country_code:
            channel_filter_criteria &= Q(
                country_code__in=self.input_params.country_code
            )
        if self.input_params.channel:
            channel_filter_criteria &= Q(channel__in=self.input_params.channel)
        if self.input_params.subsidiary:
            channel_filter_criteria &= Q(subsidiary__in=self.input_params.subsidiary)

        # Retrieve channel data
        channel_data = list(
            Channel.objects.filter(channel_filter_criteria)
            .values("country_code", "subsidiary", "channel")
            .distinct()
        )

        if not channel_data:
            raise ValueError("No channel data found for the given filter criteria")

        # Process channel data to build the filter criteria
        self._add_list_filter(
            criteria_dict,
            "channel",
            list(set(item["channel"] for item in channel_data)),
        )
        self._add_list_filter(
            criteria_dict,
            "country_code",
            list(set(item["country_code"] for item in channel_data)),
        )
        self._add_list_filter(
            criteria_dict,
            "subsidiary",
            list(set(item["subsidiary"] for item in channel_data)),
        )

    def _add_product_filters(self, criteria_dict: dict):
        """Helper method to add product line and product name filters"""
        # Retrieve product category data
        product_category_data = self.retrieve_product_category_data()

        if not product_category_data:
            raise ValueError(
                "No product category data found for the given filter criteria"
            )

        # Process product category data to build the filter criteria
        product_lines = list(
            set(item["product_line"] for item in product_category_data)
        )
        product_names = list(
            set(item["product_name"] for item in product_category_data)
        )

        # Initialize the elemMatch structure
        criteria_dict.setdefault("product_log", {})["$elemMatch"] = {}

        # Add product_line filter if available
        if product_lines:
            self._add_list_filter(
                criteria_dict["product_log"]["$elemMatch"],
                "product_line",
                product_lines,
            )

        # Add product_name filter if available
        if product_names:
            self._add_list_filter(
                criteria_dict["product_log"]["$elemMatch"],
                "product_name",
                product_names,
            )

    def retrieve_product_category_data(self, should_filter=True):
        # Check if locale is provided
        if not self.input_params.locale:
            raise ValueError("Locale is required for product category data")

        product_category_data = None

        if self.input_params.locale.upper() == "KR":
            # Retrieve product category data
            business_units_in = ["R", "E", "W", "D", "NL", "P", "M3", "F", "M"]
            business_units_not_in = [
                "R",
                "E",
                "W",
                "D",
                "NL",
                "P",
                "M3",
                "F",
                "M",
                "HC",
                "HP",
                "DS",
            ]

            queryset1 = (
                product_category.objects.filter(business_unit__in=business_units_in)
                .values(product_line=F("disp_lv2"), product_name=F("disp_lv3"))
                .distinct()
            )

            queryset2 = (
                product_category.objects.filter(
                    ~Q(business_unit__in=business_units_not_in)
                )
                .values(
                    product_line=F("disp_lv2"), product_name=F("product_category_lv3")
                )
                .distinct()
            )

            # Apply additional filters if input_params.product_line or input_params.product_name exist
            if should_filter:
                if self.input_params.product_line:
                    queryset1 = queryset1.filter(
                        product_line__in=self.input_params.product_line
                    )
                    queryset2 = queryset2.filter(
                        product_line__in=self.input_params.product_line
                    )

                if self.input_params.product_name:
                    queryset1 = queryset1.filter(
                        product_name__in=self.input_params.product_name
                    )
                    queryset2 = queryset2.filter(
                        product_name__in=self.input_params.product_name
                    )

            product_category_data = queryset1.union(queryset2)

            # Select only the required fields
            product_category_data = product_category_data.values(
                "product_line", "product_name"
            )

            product_category_data = list(product_category_data)

        else:
            queryset = Q()
            if should_filter:
                if self.input_params.product_line:
                    queryset &= Q(category_lv2__in=self.input_params.product_line)
                if self.input_params.product_name:
                    queryset &= Q(category_lv3__in=self.input_params.product_name)

            product_category_data = (
                uk_product_spec_basics.objects.filter(queryset)
                .values(product_line=F("category_lv2"), product_name=F("category_lv3"))
                .distinct()
            )

            product_category_data = list(product_category_data)

        return product_category_data

    def categorize_product_info(self, product_info):
        """
        Categorize product information into product_line and product_name.
        Parameters:
        - product_info: The product information to categorize
        Returns:
        - A dictionary with 'product_line' and 'product_name'
        """
        # Single loop to collect all product names for duplicates AND identify lines with selected products
        all_product_names = {}
        lines_with_selected_products = set()

        for item in product_info:
            product_name = item.get("product_name")
            product_line = item.get("product_line")

            if product_name:
                # Count occurrences for duplicate detection
                if product_name not in all_product_names:
                    all_product_names[product_name] = 0
                all_product_names[product_name] += 1

                # Check if this product is selected
                if (
                    self.input_params.product_name
                    and product_name in self.input_params.product_name
                ):
                    lines_with_selected_products.add(product_line)

        # Now populate the grouped data with filtering and uniquely identified product names
        grouped_product_data = {}
        for item in product_info:
            product_line = item.get("product_line")
            product_name = item.get("product_name")

            # Skip empty values
            if not product_line or not product_name:
                continue

            # Apply filters based on selection scenario
            if self.input_params.product_name or self.input_params.product_line:
                if product_line in lines_with_selected_products:
                    # This line has specific products selected - only show those
                    # AND make sure the product line is also in the filter
                    if product_name not in self.input_params.product_name:
                        continue
                    if (
                        self.input_params.product_line
                        and product_line not in self.input_params.product_line
                    ):
                        continue
                else:
                    # No specific products selected for this line - check if line is selected
                    if (
                        self.input_params.product_line
                        and product_line not in self.input_params.product_line
                    ):
                        continue

            if product_line not in grouped_product_data:
                grouped_product_data[product_line] = []

            # If this product name appears in multiple product lines in ORIGINAL data,
            # prefix it with the product line
            display_name = product_name
            if all_product_names[product_name] > 1:
                display_name = f"[{product_line}] {product_name}"

            if display_name not in grouped_product_data[product_line]:
                grouped_product_data[product_line].append(display_name)

        return grouped_product_data

    def _add_list_filter(self, criteria_dict: dict, field_name, values):
        """Helper method to add a filter for a list field"""
        if len(values) > 1:
            criteria_dict[field_name] = {"$in": values}
        elif values:
            criteria_dict[field_name] = values[0]

    def _add_thumb_type_filter(self, criteria_dict: dict):
        """Helper method to add thumb type filters"""
        thumb_type_numbers = self._get_thumb_type_number()
        if not thumb_type_numbers:
            raise ValueError("Invalid thumb type")

        # Convert string number values to integers where needed
        thumb_type_number_int = [int(i) for i in thumb_type_numbers]

        # Update criteria with thumb type filter
        criteria_dict.update(
            {
                "appraisal.selection": {
                    "$in": thumb_type_number_int + thumb_type_numbers
                },
            }
        )

    def _get_thumb_type_number(self):
        # Check if channel is not none and not empty
        if not self.input_params.channel:
            raise ValueError("Channel is required for appraisal selection mapping")

        # Check if channel has more than one value
        if len(self.input_params.channel) > 1:
            raise ValueError(
                "Channel should have only one value for appraisal selection mapping"
            )

        # Make sure thumb_up is not None
        if self.input_params.thumb_up is None:
            raise ValueError("Thumb Up/Down value is required for thumb type filtering")

        # Make sure thumb_up is only one value and is either up or down
        if len(self.input_params.thumb_up) > 1:
            raise ValueError("Thumb up filter should have only one value")

        if self.input_params.thumb_up[0] not in ["up", "down"]:
            raise ValueError("Thumb up filter should be either 'up' or 'down'")

        _thumb_up_value = True if self.input_params.thumb_up[0] == "up" else False

        channel_appraisal_selection = (
            Channel_Appraisal.objects.filter(
                channel=self.input_params.channel[0],
                thumb_up=_thumb_up_value,
            )
            .values("appraisal_selection")
            .first()
        )
        return [
            k
            for k, v in channel_appraisal_selection["appraisal_selection"].items()
            if v.get("reason") == self.input_params.thumb_type
        ]

    def _add_thumb_up_filter(self, criteria_dict: dict):
        """Helper method to add thumb_up filters"""
        valid_thumb_up_values = {"up", "down", "na"}

        # Validate thumb_up values
        if not all(
            thumb_up in valid_thumb_up_values for thumb_up in self.input_params.thumb_up
        ):
            raise ValueError("Invalid thumb_up value. Choose from 'up', 'down', 'na'")

        # Convert list to set for easier comparison
        thumb_up_set = set(self.input_params.thumb_up)

        # Skip filtering if all values are selected
        if thumb_up_set == valid_thumb_up_values:
            return

        # Handle filter based on selected values
        if thumb_up_set == {"up"}:
            criteria_dict["appraisal.thumb_up"] = True
        elif thumb_up_set == {"down"}:
            criteria_dict["appraisal.thumb_up"] = False
        elif thumb_up_set == {"na"}:
            criteria_dict["appraisal"] = {}
        elif thumb_up_set == {"up", "down"}:
            criteria_dict["$or"] = [
                {"appraisal.thumb_up": True},
                {"appraisal.thumb_up": False},
            ]
        elif thumb_up_set == {"up", "na"}:
            criteria_dict["$or"] = [{"appraisal.thumb_up": True}, {"appraisal": {}}]
        elif thumb_up_set == {"down", "na"}:
            criteria_dict["$or"] = [{"appraisal.thumb_up": False}, {"appraisal": {}}]

    def _add_status_filter(self, criteria_dict: dict):
        """Helper method to add status filters"""
        valid_statuses = {"success", "error", "timeout", "incomplete"}

        # Validate status values
        if not all(status in valid_statuses for status in self.input_params.status):
            raise ValueError(
                "Invalid status value. Choose from 'success', 'error', 'timeout', 'incomplete'"
            )

        # Convert list to set for easier comparison
        status_set = set(self.input_params.status)

        # Skip filtering if all values are selected
        if status_set == valid_statuses:
            return

        # Handle filter based on selected values
        if status_set == {"success"}:
            criteria_dict["dashboard_log.error"] = False
            criteria_dict["dashboard_log.timeout"] = False
        elif status_set == {"error"}:
            criteria_dict["dashboard_log.error"] = True
        elif status_set == {"timeout"}:
            criteria_dict["dashboard_log.timeout"] = True
        # "incomplete" status represents entries that haven't been fully processed or have undefined status
        # - NOT a success (doesn't have both error=False AND timeout=False)
        # - NOT an error (doesn't have error=True)
        # - NOT a timeout (doesn't have timeout=True)
        # This catches entries with missing/undefined dashboard_log fields or other ambiguous states
        elif status_set == {"incomplete"}:
            criteria_dict["$nor"] = [
                # Not success (both explicitly false)
                {
                    "$and": [
                        {"dashboard_log.error": False},
                        {"dashboard_log.timeout": False},
                    ]
                },
                # Not error
                {"dashboard_log.error": True},
                # Not timeout
                {"dashboard_log.timeout": True},
            ]
        elif status_set == {"success", "error"}:
            criteria_dict["dashboard_log.timeout"] = False
        elif status_set == {"success", "timeout"}:
            criteria_dict["dashboard_log.error"] = False
        elif status_set == {"error", "timeout"}:
            criteria_dict["$or"] = [
                {"dashboard_log.error": True},
                {"dashboard_log.timeout": True},
            ]
        elif status_set == {"success", "incomplete"}:
            criteria_dict["$nor"] = [
                {"dashboard_log.error": True},
                {"dashboard_log.timeout": True},
            ]
        elif status_set == {"error", "incomplete"}:
            criteria_dict["$nor"] = [
                {
                    "$and": [
                        {"dashboard_log.error": False},
                        {"dashboard_log.timeout": False},
                    ]
                },
                {"dashboard_log.timeout": True},
            ]
        elif status_set == {"timeout", "incomplete"}:
            criteria_dict["$nor"] = [
                {
                    "$and": [
                        {"dashboard_log.error": False},
                        {"dashboard_log.timeout": False},
                    ]
                },
                {"dashboard_log.error": True},
            ]
        elif status_set == {"success", "error", "incomplete"}:
            criteria_dict["dashboard_log.timeout"] = {"$ne": True}
        elif status_set == {"success", "timeout", "incomplete"}:
            criteria_dict["dashboard_log.error"] = {"$ne": True}
        elif status_set == {"error", "timeout", "incomplete"}:
            criteria_dict["$nor"] = [
                {
                    "$and": [
                        {"dashboard_log.error": False},
                        {"dashboard_log.timeout": False},
                    ]
                }
            ]

    def fill_missing_dates(self, time_data, interval, default_value=0):
        """
        Fill in missing dates in time series data with a specified default value.
        Modifies the time_data dictionary in place by adding missing dates.

        Parameters:
        - time_data: Dictionary to modify with existing time data (e.g., {"2025-01-01": 5, "2025-01-03": 10})
        - interval: String indicating time grouping ('daily', 'weekly', or 'monthly')
        - default_value: Value to use for missing dates (default: 0)
        """
        # Get start and end dates from input params
        start_date_str = self.input_params.start_date
        end_date_str = self.input_params.end_date

        # Parse the dates
        start_date = datetime.strptime(start_date_str, "%Y-%m-%d %H:%M:%S")
        end_date = datetime.strptime(end_date_str, "%Y-%m-%d %H:%M:%S")

        # Get timezone
        timezone_str = self.input_params.timezone
        tz = pytz.UTC
        if timezone_str:
            try:
                tz = pytz.timezone(timezone_str)
            except pytz.exceptions.UnknownTimeZoneError:
                pass  # Default to UTC if timezone is invalid

        # Localize the dates if they're naive
        if start_date.tzinfo is None:
            start_date = tz.localize(start_date)
        if end_date.tzinfo is None:
            end_date = tz.localize(end_date)

        # Generate all dates in the range and add missing ones to time_data
        current = start_date

        while current <= end_date:
            if interval == "daily":
                key = current.strftime("%Y-%m-%d")
                next_time = current + timedelta(days=1)
            elif interval == "weekly":
                key = current.strftime("%G-W%V")  # ISO week format
                next_time = current + timedelta(days=7)
            elif interval == "monthly":
                key = current.strftime("%Y-%m")
                # Move to first day of next month
                year = current.year + (1 if current.month == 12 else 0)
                month = 1 if current.month == 12 else current.month + 1
                next_time = datetime(year, month, 1, tzinfo=current.tzinfo)
            else:
                key = current.strftime("%Y-%m-%d")  # Default to daily
                next_time = current + timedelta(days=1)

            # Add key with default value if it doesn't exist
            if key not in time_data:
                time_data[key] = default_value

            current = next_time

    def fill_missing_interval_dates(self, time_data, interval, default_value=0):
        """
        Fill in missing time intervals for dashboard response interval API.
        This is specifically for intervals like "1H", "6H", "1D" with ISO datetime keys.
        Modifies the time_data dictionary in place by adding missing intervals.

        Parameters:
        - time_data: Dictionary with ISO datetime keys (e.g., {"2025-08-05T00:00:00": {...}})
        - interval: String ("1H", "6H", "1D")
        - default_value: Value to use for missing intervals (default: 0)
        """
        from datetime import datetime, timedelta
        import pytz

        # Get start and end dates from input params
        start_date_str = self.input_params.start_date
        end_date_str = self.input_params.end_date

        # Parse the dates
        start_date = datetime.strptime(start_date_str, "%Y-%m-%d %H:%M:%S")
        end_date = datetime.strptime(end_date_str, "%Y-%m-%d %H:%M:%S")

        # Handle timezone
        timezone_str = getattr(self.input_params, "timezone", None)
        if timezone_str:
            try:
                user_tz = pytz.timezone(timezone_str)
                # Localize the start and end dates to the user's timezone
                if start_date.tzinfo is None:
                    start_date = user_tz.localize(start_date)
                if end_date.tzinfo is None:
                    end_date = user_tz.localize(end_date)
            except pytz.exceptions.UnknownTimeZoneError:
                # If timezone is invalid, treat as UTC
                start_date = (
                    pytz.UTC.localize(start_date)
                    if start_date.tzinfo is None
                    else start_date
                )
                end_date = (
                    pytz.UTC.localize(end_date) if end_date.tzinfo is None else end_date
                )
        else:
            # If no timezone specified, treat as UTC
            start_date = (
                pytz.UTC.localize(start_date)
                if start_date.tzinfo is None
                else start_date
            )
            end_date = (
                pytz.UTC.localize(end_date) if end_date.tzinfo is None else end_date
            )

        # Generate all expected time buckets within the date range
        current = start_date

        while current <= end_date:
            if interval == "1H":
                # Truncate to hour boundary
                truncated = current.replace(minute=0, second=0, microsecond=0)
                next_time = truncated + timedelta(hours=1)
            elif interval == "6H":
                # Truncate to 6-hour boundary (00:00, 06:00, 12:00, 18:00)
                hour_block = (current.hour // 6) * 6
                truncated = current.replace(
                    hour=hour_block, minute=0, second=0, microsecond=0
                )
                next_time = truncated + timedelta(hours=6)
            elif interval == "1D":
                # Truncate to day boundary
                truncated = current.replace(hour=0, minute=0, second=0, microsecond=0)
                next_time = truncated + timedelta(days=1)
            else:
                # Default to hourly
                truncated = current.replace(minute=0, second=0, microsecond=0)
                next_time = truncated + timedelta(hours=1)

            # Generate the time key to match the format used in the pipeline
            if timezone_str:
                # When timezone is specified, format as local time without timezone suffix
                time_key = truncated.replace(tzinfo=None).strftime("%Y-%m-%dT%H:%M:%S")
            else:
                # When no timezone, format as UTC time without timezone suffix
                utc_time = (
                    truncated.astimezone(pytz.UTC) if truncated.tzinfo else truncated
                )
                time_key = utc_time.replace(tzinfo=None).strftime("%Y-%m-%dT%H:%M:%S")

            # Add missing time bucket if it doesn't exist
            if time_key not in time_data:
                time_data[time_key] = (
                    default_value.copy()
                    if isinstance(default_value, dict)
                    else default_value
                )

            current = next_time

    # def fill_missing_interval_dates(self, time_data, interval, timezone_str=None, default_value=0):


def retry_function(func, *args, max_retries=3, delay=0.1, **kwargs):
    """
    Retries a function up to max_retries times if an exception is raised.

    Args:
        func (callable): The function to retry.
        *args: Positional arguments for the function.
        max_retries (int): Maximum number of retries.
        delay (float): Delay (in seconds) between retries.
        **kwargs: Keyword arguments for the function.

    Returns:
        The result of the function if successful.

    Raises:
        Exception: The last exception raised if the function fails after retries.
    """
    for attempt in range(1, max_retries + 1):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            print(f"Attempt {attempt} failed: {e}")
            if attempt == max_retries:
                raise
            time.sleep(delay)


def extract_selected_list(row):
    """
    Transform the Selected List column based on Channel value and Thumbs Up/Down value, then join with | separator.

    Parameters:
    row: A pandas Series representing a row of the DataFrame

    Returns:
    str: The transformed string with values joined by " | "

    Raises:
    Exception: If Thumbs Up/Down is "na" but Selected List has values
            Or if no mapping dictionary is found for the given Channel and Thumbs Up/Down combination
    """
    selected_list = row["Selected List"]
    channel = row["Channel"]
    thumb_updown = row["Thumbs Up/Down"]  # Get the Thumbs Up/Down value

    # Handle case when selected_list is None
    if isinstance(selected_list, float) and math.isnan(selected_list):
        return ""

    # Ensure selected_list is a list
    if not isinstance(selected_list, list):
        # Convert string representation of list to list
        if isinstance(selected_list, str):
            # Check if it's a string representation of a list (starts with '[' and ends with ']')
            if selected_list.startswith("[") and selected_list.endswith("]"):
                # Remove brackets and split by comma
                selected_list = selected_list.strip("[]").split(",")
            else:
                # Treat it as a comma-separated string
                selected_list = selected_list.split(",")

            # Clean up whitespace for all items
            selected_list = [item.strip() for item in selected_list]
        else:
            # It's a single item (not a string), treat it as a list with one element
            selected_list = [selected_list]

    # If selected_list is empty after parsing
    if len(selected_list) == 0:
        return ""

    # Check for "na" thumb_updown with non-empty selected_list
    if thumb_updown == "na" and len(selected_list) > 0:
        raise Exception(
            f"Thumbs Up/Down is 'na' but Selected List has values: {selected_list} for Channel: {channel}"
        )

    # Determine thumb_up value for filtering
    if thumb_updown == "up":
        thumb_up = True
    elif thumb_updown == "down":
        thumb_up = False
    else:
        # At this point, if thumb_updown is "na", we've already handled all possible cases:
        # - If selected_list was empty, we returned early
        # - If selected_list was not empty with "na", we raised an exception
        # So this must be an invalid value
        raise Exception(
            f"Invalid Thumbs Up/Down value: '{thumb_updown}' for Channel: {channel}"
        )

    # Get the mapping dictionary for this channel and thumb_up value
    mapping_dict = (
        Channel_Appraisal.objects.filter(channel=channel, thumb_up=thumb_up)
        .values("appraisal_selection")
        .first()
    )

    # Check if mapping_dict exists
    if not mapping_dict:
        raise Exception(
            f"No mapping dictionary found for Channel: '{channel}' and Thumbs Up/Down: '{thumb_updown}'"
        )

    # Convert list elements to strings and map to new values
    transformed_values = []
    for item in selected_list:
        # Convert to string
        str_item = str(item)
        # Map to new value using the mapping dictionary
        selection_data = mapping_dict["appraisal_selection"].get(
            str_item, {"reason": str_item}
        )
        mapped_value = selection_data.get("reason", str_item)

        transformed_values.append(mapped_value)

    # Join the transformed values with " | "
    return " | ".join(transformed_values)


def extract_product_info(json_data, field, separator=" | "):
    """
    Extract values from the specified field (product_line or product_name) and join them.

    Parameters:
    - json_data: The JSON data to process
    - field: The field to extract
    - separator: The string to use when joining multiple values (default: " | ")

    Returns:
    - A string with the joined values, or empty string if not found
    """
    if not isinstance(json_data, list):
        return ""

    values = []
    for item in json_data:
        if isinstance(item, dict) and field in item:
            values.append(item[field])

    return separator.join(values)


def extract_response_generation_value(json_data):
    """
    Extract the 'value' from the 'Response Generation' module,
    or return empty string if not found.
    """
    if not isinstance(json_data, list):
        return ""

    for item in json_data:
        if isinstance(item, dict) and item.get("module") == "Response Generation":
            function_output = item.get("function", {}).get("output", [])
            if isinstance(function_output, list) and len(function_output) > 0:
                return function_output[0].get("value", "")

    return ""


def extract_re_write_query(json_data):
    """
    Extract the 're_write_query_list' from the 'Response Generation' module,
    or return empty list if not found.
    """
    if not isinstance(json_data, list):
        return []

    for item in json_data:
        rewrite_list = (
            item.get("llm", {}).get("output", {}).get("re_write_query_list", [])
        )
        if isinstance(rewrite_list, list) and rewrite_list:
            # Flatten nested arrays if needed
            flattened_list = []
            for sublist in rewrite_list:
                if isinstance(sublist, list):
                    flattened_list.extend(sublist)
                else:
                    flattened_list.append(sublist)
            return flattened_list
    return []


def extract_division_info(product_log):
    """Extract division information from product_log"""
    if not product_log or not isinstance(product_log, list):
        return "Not Applicable"

    # Extract all divisions from product_log
    divisions = []
    for log_entry in product_log:
        if isinstance(log_entry, dict) and log_entry.get("product_division"):
            if isinstance(log_entry["product_division"], list):
                divisions.extend(log_entry["product_division"])
            else:
                divisions.append(log_entry["product_division"])

    # Get unique divisions
    unique_divisions = list(set(divisions))

    # Check for major divisions
    major_divisions = ["MX", "VD", "DA"]
    present_major_divisions = [
        div for div in unique_divisions if div in major_divisions
    ]

    if len(present_major_divisions) == 0:
        return "Not Applicable"
    elif len(present_major_divisions) == 1:
        return present_major_divisions[0]
    else:
        return "Cross Product"


def get_product_line_from_product_name(product_name: str, locale: str):
    # Check if locale is provided
    if not locale:
        raise ValueError("Locale is required for product category data")

    product_category_data = None
    if locale.upper() == "KR":
        # Retrieve product category data
        business_units_in = ["R", "E", "W", "D", "NL", "P", "M3", "F", "M"]
        business_units_not_in = [
            "R",
            "E",
            "W",
            "D",
            "NL",
            "P",
            "M3",
            "F",
            "M",
            "HC",
            "HP",
            "DS",
        ]

        queryset1 = (
            product_category.objects.filter(business_unit__in=business_units_in)
            .values(product_line=F("disp_lv2"), product_name=F("disp_lv3"))
            .distinct()
        )

        queryset2 = (
            product_category.objects.filter(~Q(business_unit__in=business_units_not_in))
            .values(product_line=F("disp_lv2"), product_name=F("product_category_lv3"))
            .distinct()
        )

        queryset1 = queryset1.filter(product_name=product_name)
        queryset2 = queryset2.filter(product_name=product_name)

        product_category_data = queryset1.union(queryset2)

        # Select only the required fields
        product_category_data = product_category_data.values("product_line")

        product_category_data = list(product_category_data)

    else:
        queryset = Q(category_lv3=product_name)

        product_category_data = (
            uk_product_spec_basics.objects.filter(queryset)
            .values(product_line=F("category_lv2"))
            .distinct()
        )

        product_category_data = list(product_category_data)

    return product_category_data


def product_filter_preprocessing(
    product_line_list: list[str], product_name_list: list[str], locale: str
):
    if not product_line_list:
        product_line_list = []

    for product_name in product_name_list:
        pattern = r"^\[(.*?)\]\s+(.*)$"
        match = re.match(pattern, product_name)

        if match:
            matched_product_line = match.group(1)
            matched_product_name = match.group(2)

            # Check if the product line is not in the list
            if matched_product_line not in product_line_list:
                # If not, add it to the list
                product_line_list.append(matched_product_line)

            # Update the product name in the list
            product_name_list[product_name_list.index(product_name)] = (
                matched_product_name
            )
        else:
            # Grab the product line from the product name
            product_line = get_product_line_from_product_name(product_name, locale)
            if not product_line:
                raise ValueError(
                    f"Product line not found for product name: {product_name}"
                )

            # If product_line is a list, it means there are multiple product lines for the same product name
            if len(product_line) > 1:
                # Check if the product line is already in the list
                in_list = False
                for pl in product_line:
                    # Check if the product line is in the filter list
                    # If present, nothing to do
                    if pl["product_line"] in product_line_list:
                        in_list = True
                        break

                # There are multiple product lines for the same product name and product line is not in the filter list
                if not in_list:
                    raise ValueError(
                        f"Multiple product lines found for product name: {product_name}"
                    )

            else:
                # If product_line is a single item, just grab the product line
                product_line = product_line[0]["product_line"]

                # Check if the product line is not in the list
                if product_line not in product_line_list:
                    product_line_list.append(product_line)

    return product_line_list, product_name_list


def validate_channel(channel: str):
    """
    Validate if the provided channel exists and is active.
    """
    query = Q(active=True)

    # Add locale filter only for staging and production environments
    if VITE_OP_TYPE in ["STG", "PRD"]:
        locale = VITE_COUNTRY
        # If the vite country is set to UK, we use GB as the locale
        if VITE_COUNTRY == "UK":
            locale = "GB"

        query &= Q(locale=locale)

    valid_channels = list(
        Channel.objects.filter(query).values_list("channel", flat=True).distinct()
    )

    return channel in valid_channels


def update_corresponding_collection_log_by_field(message_id, field, value):
    """
    Function to check both chat log and search log to see which log entry to update.
    If the message_id is found in both logs, it will not update any logs
    """
    try:
        chat_log_entry = chat_log_collection.find_one({"message_id": message_id})
        search_log_entry = search_log_collection.find_one({"message_id": message_id})

        if chat_log_entry and search_log_entry:
            # If found in both logs, do not update
            # Raise an error
            raise ValueError(
                f"Message ID {message_id} found in both chat and search logs. Cannot update."
            )

        if chat_log_entry:
            # Update chat log
            rubicon_log.update_message_log_by_field(message_id, field, value)
        elif search_log_entry:
            # Update search log
            search_log.update_search_log_by_field(message_id, field, value)
        else:
            # If not found in either log, raise an error
            raise ValueError(f"Message ID {message_id} not found in any log.")

    except Exception as e:
        # Alert any errors that occur during the update
        if VITE_OP_TYPE in ["STG", "PRD"]:
            context_data = {
                "Module": "Update Corresponding Log",
                "Message ID": message_id,
            }
            error_type = "process_error"

            send_process_error_alert(
                str(e),
                error_type,
                error_traceback=traceback.format_exc(),
                context_data=context_data,
            )
