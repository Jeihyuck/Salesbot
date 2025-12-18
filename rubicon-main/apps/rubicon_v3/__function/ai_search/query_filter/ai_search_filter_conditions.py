from apps.rubicon_v3.__function.ai_search.query_filter.ai_search_filter_condition import AiSearchFilterCondition


class AiSearchFilterConditions:
    """
    Manages filter conditions for each index.
    This class allows you to add, retrieve, and combine multiple filter conditions associated with different index names.
    """

    def __init__(self):
        self.filter_condition_dict: dict[str | None, list["AiSearchFilterCondition"]] = {}

    def add(self, filter_condition: "AiSearchFilterCondition"):
        self.filter_condition_dict.setdefault(filter_condition.index_name, []).append(
            filter_condition
        )
        return self

    def find(self, index_name: str) -> list["AiSearchFilterCondition"] | None:
        if index_name in self.filter_condition_dict:
            return self.filter_condition_dict[index_name]
        return self.filter_condition_dict.get(None)

    def make_category_filter(self, index_name):
        """
        Combine multiple category filter conditions for the same index into a single filter string.
        Useful for constructing Azure AI Search filter queries.
        Args:
            index_name (str): The index name for which to build the filter.
        Returns:
            str: Azure AI Search filter string or None if no conditions exist.
        """
        filter_list = []
        filter_conditions = self.find(index_name)
        if not filter_conditions:
            return None

        # Build filter strings for each condition and combine them with 'or'.
        for filter_condition in filter_conditions:
            filter_str = filter_condition.make_category_filter()
            if filter_str:
                filter_list.append(filter_str)

        if not filter_list:
            return None

        return "(" + " or ".join(filter_list) + ")"

    def make_model_code_filter(self, index_name):
        """
        Combine multiple model code filter conditions for the same index into a single filter string.
        Useful for constructing Azure AI Search filter queries for model codes.
        Args:
            index_name (str): The index name for which to build the filter.
        Returns:
            str: Azure AI Search filter string or None if no conditions exist.
        """

        filter_list = []
        filter_conditions = self.find(index_name)
        if not filter_conditions:
            return None

        # Build filter strings for each condition and combine them with 'or'.
        for filter_condition in filter_conditions:
            filter_str = filter_condition.make_model_code_filter()
            if filter_str:
                filter_list.append(filter_str)

        if not filter_list:
            return None

        return "(" + " or ".join(filter_list) + ")"

    def make_display_date_filter(self, index_name, date_filter=None):
        """
        Combine multiple display date filter conditions for the same index into a single filter string.
        Useful for constructing Azure AI Search filter queries for display dates.
        Args:
            index_name (str): The index name for which to build the filter.
            date_filter: Optional date filter parameter to pass to each condition.
        Returns:
            str: Azure AI Search filter string or None if no conditions exist.
        """

        filter_list = []
        filter_conditions: list[AiSearchFilterCondition] | None = self.find(index_name)
        if not filter_conditions:
            return None

        # Build filter strings for each condition and combine them with 'or'.
        for filter_condition in filter_conditions:
            filter_str = filter_condition.make_display_date_filter(date_filter)
            if filter_str:
                filter_list.append(filter_str)

        if not filter_list:
            return None

        return "(" + " or ".join(filter_list) + ")"

    def make_reg_date_filter(self, index_name):
        """
        Combine multiple registration date filter conditions for the same index into a single filter string.
        Useful for constructing Azure AI Search filter queries for registration dates.
        Args:
            index_name (str): The index name for which to build the filter.
        Returns:
            str: Azure AI Search filter string or None if no conditions exist.
        """

        filter_list = []
        filter_conditions: list[AiSearchFilterCondition] | None = self.find(index_name)
        if not filter_conditions:
            return None

        # Build filter strings for each condition and combine them with 'or'.
        for filter_condition in filter_conditions:
            filter_str = filter_condition.make_reg_date_filter()
            if filter_str:
                filter_list.append(filter_str)

        if not filter_list:
            return None

        return "(" + " or ".join(filter_list) + ")"


if __name__ == "__main__":
    
    assert AiSearchFilterCondition(category1_list="test").category1_list == ["test"]
    assert AiSearchFilterCondition(category2_list="test").category2_list == ["test"]
    assert AiSearchFilterCondition(category3_list="test").category3_list == ["test"]
    assert AiSearchFilterCondition(category1_list=["test"]).category1_list == ["test"]
    assert AiSearchFilterCondition(category2_list=["test"]).category2_list == ["test"]
    assert AiSearchFilterCondition(category3_list=["test"]).category3_list == ["test"]
    assert AiSearchFilterCondition(category1_list="NA").category1_list == []
    assert AiSearchFilterCondition(category1_list=["NA"]).category1_list == []

    assert (
        AiSearchFilterConditions()
        .add(AiSearchFilterCondition(category1_list="c11"))
        .add(AiSearchFilterCondition(category1_list="c12"))
        .add(AiSearchFilterCondition(category2_list=["c21", "c22"]))
    ).make_category_filter(
        None
    ) == "(((category1 eq 'c11')) or ((category1 eq 'c12')) or ((category2 eq 'c21' or category2 eq 'c22')))"

    assert (
        AiSearchFilterCondition(category1_list="a").make_category_filter()
        == "((category1 eq 'a'))"
    )
    assert (
        AiSearchFilterCondition(category1_list=["a", "b"]).make_category_filter()
        == "((category1 eq 'a' or category1 eq 'b'))"
    )
    assert (
        AiSearchFilterCondition(
            category1_list=["a", "b"], category2_list=["c"]
        ).make_category_filter()
        == "((category1 eq 'a' or category1 eq 'b') and (category2 eq 'c'))"
    )
    assert (
        AiSearchFilterCondition(
            category1_list=["a", "b"], category2_list=["c"], category3_list=["d", "e"]
        ).make_category_filter()
        == "((category1 eq 'a' or category1 eq 'b') and (category2 eq 'c') and (category3 eq 'd' or category3 eq 'e'))"
    )

    assert (
        AiSearchFilterCondition(product_model_codes=["a", "b"]).make_model_code_filter()
        == "(model_code/any(x: x eq 'a') or model_code/any(x: x eq 'b'))"
    )