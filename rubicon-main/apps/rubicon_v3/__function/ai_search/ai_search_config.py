import pydantic

from apps.rubicon_v3.__function.ai_search.index.index_info import IndexInfo
from apps.rubicon_v3.__function.ai_search.query_filter.ai_search_filter_conditions import AiSearchFilterConditions


class AiSearchConfig(pydantic.BaseModel):
    """Configuration class for AI search operations.
    
    This class defines the configuration parameters used for executing
    AI search queries against Azure AI Search indices.
    """
    
    alias: str  # Alias name of the search index
    index_name: str  # Actual name of the search index
    integration_index_system_name: list | None = None  # System names for integration index

    filter_str: str | None  # OData filter string for search queries
    param_dict: dict  # Dictionary of additional parameters for the search
    is_vector_search: bool  # Whether to use vector search or keyword search
    use_integration_index: bool  # Whether to use the integration index
    always_use_in_response: bool  # Whether results should always be included in response
    index_def: IndexInfo | None = None  # Index definition and metadata
    query: str  # The search query string
    filter_conditions: AiSearchFilterConditions  # Filter conditions for the search

    class Config:
        arbitrary_types_allowed = True

    def model_post_init(self, context):
        """Post-initialization hook for additional setup if needed."""
        pass
