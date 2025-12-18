import datetime
import pydantic


class AiSearchFilterCondition(pydantic.BaseModel):
    index_name: str | None = None  # Apply to all indexes if None
    category1_list: list[str] | str | None = list()
    category2_list: list[str] | str | None = list()
    category3_list: list[str] | str | None = list()
    display_date: bool | None = None
    product_model_codes: list[str] | str = list()
    always_use_in_response: bool | None = False
    now_utc_str: str | None = None
    country: str | None = None

    @pydantic.field_validator("category1_list", "category2_list", "category3_list")
    def parse_category(cls, value):
        """Always store as a list, even if input is a string 
        
        Args:
            value (str | list): Input value which can be a string or list
        
        Returns:
            list: Parsed list of category values, empty if "NA" is present
        """
        if not value:
            ret = []
        elif isinstance(value, str) and value:
            ret = [value]
        else:
            ret = value

        if "NA" in ret:
            ret = []

        return ret

    def make_category_filter(self):
        filter_list = []

        for name, value in [
            ("category1", self.category1_list),
            ("category2", self.category2_list),
            ("category3", self.category3_list),
        ]:
            if not value:
                continue
            filter_list.append(
                "(" + " or ".join([f"{name} eq '{v}'" for v in value]) + ")"
            )

        if not filter_list:
            return None

        return "(" + " and ".join(filter_list) + ")"

    def make_model_code_filter(self):
        filter_str = None

        if self.product_model_codes:
            filter_str = (
                "("
                + " or ".join(
                    [f"model_code/any(x: x eq '{v}')" for v in self.product_model_codes]
                )
                + ")"
            )

        if not filter_str:
            return None

        return filter_str

    def make_display_date_filter(self, date_filter):
        """Create a filter string for display date based on current time and provided date filter.

        Args:
            date_filter (list): List of datetime strings to filter against, can be empty
            
        Returns:
            str: OData filter string for display date, or None if no display date is set
        """
        if not self.display_date:
            return None

        if self.country == 'KR':
            # Calculate current time in Korea timezone
            now_utc_str = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=9)
            now_str = now_utc_str.strftime(
                "%Y-%m-%dT%H:%M:%SZ"
            )
        else:
            now_str = datetime.datetime.now(datetime.timezone.utc).strftime(
                "%Y-%m-%dT%H:%M:%S.%fZ"
            )
        self.now_utc_str = now_str
        if not date_filter:
            return f"(disp_strt_dtm le {now_str} and disp_end_dtm ge {now_str})"
        else:
            return f"(disp_strt_dtm le {min(date_filter)} or disp_end_dtm ge {max(date_filter)})"

    def make_reg_date_filter(self):
        past_utc_str = (datetime.datetime.now(
            datetime.timezone.utc
        ) - datetime.timedelta(days=365 * 2)).strftime("%Y-%m-%dT%H:%M:%SZ")
        self.now_utc_str = past_utc_str

        return f"(reg_date ge {past_utc_str})"
