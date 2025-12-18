import django

from apps.rubicon_v3.__function.ai_search.ai_search_config import AiSearchConfig
from apps.rubicon_v3.__function.ai_search.query_filter.ai_search_filter_conditions import (
    AiSearchFilterConditions,
)
from apps.rubicon_v3.__function.ai_search.index.index_info import IndexInfo


django.setup()
from alpha import settings
from alpha.settings import VITE_OP_TYPE
from apps.__common import multi_threading
from apps.rubicon_v3.__function import __embedding_rerank as embedding_rerank


from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from azure.search.documents.models import VectorizedQuery
from apps.rubicon_v3.__function.definitions import sub_intelligences, channels

from apps.rubicon_v3.__function.ai_search.ai_search_index_definitions import (
    AiSearchIndexDefinitions,
)
from apps.rubicon_v3.models import Unstructured_Index

from alpha import __log


class AzureAiSearch:
    """
    Azure AI Search client for handling multiple search indices with support for both
    vector and traditional keyword search. This class manages search operations across
    multiple indices including integration indices for unified search capabilities.

    The class handles:
    - Multiple search index management
    - Vector search using embeddings
    - Traditional keyword search
    - Filter conditions and date filtering
    - Multi-threaded search execution
    - Integration index consolidation
    """

    def __init__(self, country_code, alias_list: dict[str, str]):
        # Override Azure Search environment settings based on country code
        settings.override_azure_search_env(country_code)
        self._check_azure_search_env()

        # Retrieve all available unstructured index mappings from database
        self.all_alias_to_index_name_dict = self._get_unstructured_index_name_dict(
            country_code
        )
        self.country_code = country_code

        # Integration index information
        self.integration_index_name, self.integration_client = (
            self._get_integration_index(self.all_alias_to_index_name_dict)
        )

        # Filter alias list to include only valid aliases that exist in the database
        alias_to_index_name_dict = {
            alias: self.all_alias_to_index_name_dict[alias]
            for alias in alias_list
            if alias in self.all_alias_to_index_name_dict  # use only valid aliases
        }
        # alias_to_index_name_dict[AiSearchIndexDefinitions.ALIAS_INTEGRATION] = self.integration_index_name

        # Store list of valid aliases for this search session
        self.alias_list = list(alias_to_index_name_dict.keys())

        # self.index_list = index_list
        self.alias_to_index_name_dict = (
            alias_to_index_name_dict  # key: alias, value: index_name
        )

        self.index_name_to_alias_dict = {
            index_name: alias for alias, index_name in alias_to_index_name_dict.items()
        }  # key: index_name, value: alias

        # alias_index_def_dict: key: alias, value: AiSearchIndexDefinitions
        self.alias_index_def_dict = {
            alias: AiSearchIndexDefinitions.from_values(country_code, alias)
            for alias in alias_to_index_name_dict.keys()
        }

        # reference: SearchClient Class https://learn.microsoft.com/ko-kr/python/api/azure-search-documents/azure.search.documents.searchclient?view=azure-python#azure-search-documents-searchclient-search
        self.client_dict: dict[str, SearchClient] = {}
        # Create index-specific clients
        for alias, index_name in self.alias_to_index_name_dict.items():
            self.client_dict[index_name] = self._create_search_client(index_name)

    @classmethod
    def _check_azure_search_env(cls):
        """
        Validate that required Azure Search environment variables are properly configured.

        Raises:
            ValueError: If AZURE_SEARCH_ENDPOINT or AZURE_SEARCH_API_KEY are not defined or invalid
        """
        if not settings.AZURE_SEARCH_ENDPOINT or not isinstance(
            settings.AZURE_SEARCH_ENDPOINT, str
        ):
            raise ValueError("AZURE_SEARCH_ENDPOINT is not defined")

        if not settings.AZURE_SEARCH_API_KEY or not isinstance(
            settings.AZURE_SEARCH_API_KEY, str
        ):
            raise ValueError("AZURE_SEARCH_API_KEY is not defined")

    def _get_integration_index(self, all_alias_to_index_name_dict):
        """
        Setup the integration index which consolidates multiple data sources for unified search.

        The integration index allows searching across multiple systems and versions
        in a single query, improving search efficiency and consistency.

        Args:
            all_alias_to_index_name_dict (dict): Complete mapping of aliases to index names

        Returns:
            tuple: (integration_index_name, integration_client)
        """
        integration_index_name = all_alias_to_index_name_dict[
            AiSearchIndexDefinitions.ALIAS_INTEGRATION
        ]
        integration_client = self._create_search_client(integration_index_name)
        return integration_index_name, integration_client

    @classmethod
    def _create_search_client(cls, index_name):
        """
        Create an Azure Search client for a specific index.

        Args:
            index_name (str): Name of the Azure Search index

        Returns:
            SearchClient: Configured Azure Search client instance
        """
        return SearchClient(
            endpoint=settings.AZURE_SEARCH_ENDPOINT,
            index_name=index_name,
            credential=AzureKeyCredential(settings.AZURE_SEARCH_API_KEY),
        )

    @classmethod
    def _get_unstructured_index_name_dict(cls, country_code):
        """
        Retrieve unstructured index mapping information from the database.

        This method fetches the mapping between alias names and actual Azure Search
        index names for the specified country. This allows for flexible index
        management across different regions and environments.

        Args:
            country_code (str):

        Returns:
            dict:
        """
        # Query database for index mappings filtered by country and operation type
        index_mapping_raw = list(
            Unstructured_Index.objects.filter(
                country_code=country_code, op_type=VITE_OP_TYPE
            ).values("name", "ai_search_index")
        )

        # Convert to dictionary mapping alias -> index name
        alias_to_index_name_dict = {
            item["name"]: item["ai_search_index"] for item in index_mapping_raw
        }

        # TODO: Remove this temporary logic for development integration index
        # alias_to_index_name_dict["INTEGRATION"] = "dev-integration-v5"
        return alias_to_index_name_dict

    def check_index_with_model_code(self):
        """
        Check if any of the configured indices support model code filtering.

        This is used to determine search strategy - if model code filtering is available,
        the search can be more targeted and efficient.

        Returns:
            bool:
        """
        has_index_with_model_code = False
        for alias, index_name in self.alias_to_index_name_dict.items():
            index_def: IndexInfo | None = self.alias_index_def_dict.get(alias)
            if index_def and index_def.has_model_code:
                has_index_with_model_code = True
                break
        return has_index_with_model_code

    def search_multiple_indices(
        self,
        top_query,
        sub_intelligence,
        filter_conditions: "AiSearchFilterConditions",
        country_code,
        select_filed_list,
        top=5,
        is_vector_search=True,
        custom_filter: str | None = None,
        date_filter: list[str] | None = None,
        channel_id: str = "AIbot",
        site_cd: str = "B2C",
    ):
        """
        Execute search across multiple Azure Search indices with support for both
        integration and individual index searching.

        This method orchestrates the entire search process:
        1. Builds search configurations for each index
        2. Determines whether to use integration index or individual indices
        3. Executes searches in parallel using multi-threading
        4. Consolidates and returns results

        Args:
            top_query (str): top query
            sub_intelligence (str): Sub-intelligence
            filter_conditions (AiSearchFilterConditions):
            country_code (str):
            select_filed_list (list):
            top (int): Number of top results to return per index (default: 5)
            is_vector_search (bool): Whether to use vector search or keyword search
            custom_filter (str, optional): Additional custom filter string
            date_filter (list[str], optional): Date range filters

        Returns:
            tuple: (result_list, config_list_dict) containing search results and configurations used
        """
        # Build search configurations for all indices, determining integration vs individual search
        config_list_dict: dict[tuple, list[AiSearchConfig]] = self._build_search_config(
            is_vector_search,
            top_query,
            sub_intelligence,
            top,
            filter_conditions,
            select_filed_list,
            country_code,
            date_filter,
            site_cd,
        )  # Key: (use_integration_index), Value: list of AiSearchConfig objects

        # TODO: Consider exhaustive=True for comprehensive filtering (slower but more thorough)

        # Prepare parameters for multi-threaded search execution
        thread_params = []
        param_dict_list = []
        index_list = []

        # Process each configuration group (integration vs individual indices)
        for use_integration_index, config_list in config_list_dict.items():

            if not config_list:
                continue

            if use_integration_index:
                # Integration index: Search once across multiple systems consolidated in one index
                # This is more efficient when searching across multiple data sources

                filter_list = []
                param_dict = {}
                index_name = None

                # Build combined filter for integration index search
                for config in config_list:
                    if custom_filter:
                        if config.filter_str:
                            config.filter_str = (
                                f"({config.filter_str}) and ({custom_filter})"
                            )
                        else:
                            config.filter_str = f"({custom_filter})"

                    if (
                        not custom_filter
                        and country_code == "GB"
                        and "scrp" in config.integration_index_system_name[0]
                        and channel_id != channels.RETAIL_KX
                    ):
                        if config.filter_str:
                            config.filter_str = (
                                f"({config.filter_str}) and (category3 ne 'KX')"
                            )
                        else:
                            config.filter_str = f"(category3 ne 'KX')"

                    # Build system-specific filter for integration index
                    if config.filter_str:
                        filter_list.append(
                            f"(({config.filter_str}) and system_name eq '{config.integration_index_system_name[0]}' and version eq '{config.integration_index_system_name[1]}')"
                        )
                    else:
                        filter_list.append(
                            f"(system_name eq '{config.integration_index_system_name[0]}' and version eq '{config.integration_index_system_name[1]}')"
                        )
                    index_name = config.index_name
                    param_dict = config.param_dict.copy()

                # param_dict varies only by search type (vector vs BM25), so any config can be used
                # Currently using the last config from the loop
                index_list.append(self.integration_index_name)
                param_dict["filter"] = " or ".join(filter_list)
                param_dict_list.append(param_dict)
                thread_params.append(
                    [
                        self.integration_client.search,
                        (),
                        param_dict,
                    ]
                )

            else:
                # Individual index search: Search each index separately
                # Used when indices don't support integration or need specialized handling
                for config in config_list:
                    client = self.client_dict.get(config.index_name)
                    param_dict = config.param_dict.copy()
                    param_dict["filter"] = config.filter_str
                    index_list.append(config.index_name)
                    param_dict_list.append(param_dict)
                    thread_params.append(
                        [
                            client.search,
                            (),
                            param_dict,
                        ]
                    )

        # Execute all searches in parallel for better performance
        thread_result = multi_threading.run_in_threads_multi_function(thread_params)
        print(thread_result)

        # Combine results with their corresponding index and parameter information
        result_list = list(
            zip(index_list, param_dict_list, [[y for y in x] for x in thread_result])
        )
        return result_list, config_list_dict

    def _build_search_config(
        self,
        is_vector_search: bool,
        top_query: str,
        sub_intelligence: str,
        topk: int,
        filter_conditions: "AiSearchFilterConditions",
        select_field_list: list[str] | None,
        country_code,
        date_filter,
        site_cd,
    ):
        """
        Build search configurations for each index, determining whether to use
        individual indices or the integration index.

        This method is the core logic that determines search strategy:
        - Analyzes each index's capabilities and requirements
        - Builds appropriate filters based on index features
        - Configures vector or keyword search parameters
        - Decides integration vs individual index usage

        Returns:
            _type_: _description_
        """

        # Setup vector queries for semantic search using BAAI embeddings
        vector_queries_baai = []
        if is_vector_search:
            # Create vector queries for both chunk and title embeddings with equal weight
            vector_queries_baai = [
                VectorizedQuery(
                    vector=embedding_rerank.baai_embedding(top_query, None)[0],
                    k_nearest_neighbors=topk * 3,
                    fields="embedding_semantic_bgechunk",
                    weight=0.5,
                ),
                VectorizedQuery(
                    vector=embedding_rerank.baai_embedding(top_query, None)[0],
                    k_nearest_neighbors=topk * 3,
                    fields="embedding_semantic_bgetitle",
                    weight=0.5,
                ),
            ]

        config_list_dict = {}

        # Process each configured index to build search configurations
        for alias, index_name in self.alias_to_index_name_dict.items():

            # Generate all possible filters for this index
            filter_category = filter_conditions.make_category_filter(index_name)
            filter_model_code = filter_conditions.make_model_code_filter(index_name)
            filter_display_date = filter_conditions.make_display_date_filter(
                index_name, date_filter
            )
            filter_reg_date = filter_conditions.make_reg_date_filter(index_name)

            # Get index definition to understand capabilities and requirements
            index_def: IndexInfo | None = self.alias_index_def_dict.get(alias)

            # Determine search strategy and build filters based on index capabilities
            use_integration_index = False
            final_filter = None
            integration_index_system_name = None
            if index_def:
                # Check if this index should use the integration index for unified search
                if (
                    index_def.use_integration_index
                    and index_def.integration_index_system_name
                ):
                    use_integration_index = True
                    integration_index_system_name = (
                        index_def.integration_index_system_name
                    )

                # Apply model code filtering if the index supports it and filter is available
                if index_def.has_model_code and filter_model_code:
                    final_filter = filter_model_code

                # if has_index_with_model_code and filter_model_code:
                #     # 인덱스 중에 모델코드로 검색가능한 인덱스가 있는 경우에는 모델코드로만 검색
                #     if index_def.value.product_model_code:
                #         final_filter = filter_model_code
                #     else:
                #         # 모델코드로 검색하지 못하는 인덱스는 검색하지 않음
                #         continue

                # Special logic for promotion intelligence with SCRP indices
                # Category filters are applied for promotion searches or indices with category support
                if (
                    "PROMOTION" in self.alias_to_index_name_dict.keys()
                    and "scrp" in index_def.integration_index_system_name[0]
                ) or (
                    index_def.category1_type
                    or index_def.category2_type
                    or index_def.category3_type
                ):
                    if final_filter and filter_category is not None:
                        final_filter = f"({final_filter}) and {filter_category}"
                    else:
                        final_filter = filter_category

                # Special case: UK SCRP delivery/installation searches - limit to specific documents
                if (
                    "scrp" in index_def.integration_index_system_name[0]
                    and country_code == "GB"
                    and sub_intelligence
                    in [
                        sub_intelligences.DELIVERY_POLICY,
                        sub_intelligences.INSTALLATION_CONDITIONS_AND_STANDARDS,
                    ]
                ):
                    final_filter = "(category1 eq 'FAQ' and category2 eq 'Delivery and installations')"

                # Apply display date filtering if supported by the index
                if filter_display_date and index_def.has_display_date:
                    if final_filter:
                        final_filter = f"({final_filter}) and {filter_display_date}"
                    else:
                        final_filter = filter_display_date

                # Apply registration date filtering if supported (e.g., for news indices)
                if filter_reg_date and index_def.has_reg_date:
                    if final_filter:
                        final_filter = f"({final_filter}) and {filter_reg_date}"
                    else:
                        final_filter = filter_reg_date

                if index_def.has_types:
                    if final_filter:
                        final_filter = f"({final_filter}) and (type eq '{site_cd}')"
                    else:
                        final_filter = f"(type eq '{site_cd}')"

            if is_vector_search:

                vector_queries = vector_queries_baai
                # if index_def:
                #     if index_def.country_code == "KR" and index_def.alias == AiSearchIndexDefinitions.KR_PROMOTION.alias:
                #         vector_queries = vector_queries_aoai_promotion

                param_dict = {
                    "search_text": top_query,
                    # "filter": final_filter,
                    "top": topk * 3,
                    "vector_queries": vector_queries,
                    "query_type": "semantic",
                    "query_caption": "extractive",
                    "semantic_configuration_name": "my-semantic-config",
                }
            else:
                # Traditional keyword search configuration
                param_dict = {
                    "search_text": top_query,
                    # "filter": final_filter,
                    "top": topk * 3,
                    "query_type": "simple",
                }

            # if select_field_list:
            #     if not use_integration_index:
            #         select_field_list = [
            #             x for x in select_field_list if x not in ["system_name"]
            #         ]

            #     select_fields_str = ",".join(select_field_list)

            #     param_dict["select"] = select_fields_str

            print(final_filter)  # Debug output for filter inspection

            always_use_in_response = (
                index_def.always_use_in_response if index_def else False
            )

            # Add configuration to the appropriate group (integration vs individual)
            config_list_dict.setdefault(use_integration_index, []).append(
                AiSearchConfig(
                    alias=alias,
                    index_name=index_name,
                    integration_index_system_name=integration_index_system_name,
                    always_use_in_response=always_use_in_response,
                    filter_str=final_filter,
                    param_dict=param_dict,
                    is_vector_search=is_vector_search,
                    use_integration_index=use_integration_index,
                    index_def=index_def,
                    query=top_query,
                    filter_conditions=filter_conditions,
                )
            )

        return config_list_dict
