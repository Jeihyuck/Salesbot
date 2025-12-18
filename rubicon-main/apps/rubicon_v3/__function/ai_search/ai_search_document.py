from datetime import datetime
import pydantic
import pytz


class AISearchDocument(pydantic.BaseModel):
    """AI Search Document model representing a search result from Azure AI Search.
    
    This class defines the structure of documents returned from AI search operations,
    including metadata, content, and search-specific fields.
    """
    
    # Basic document identifiers
    id: str  # Unique document identifier
    bu: str | None  # Business unit
    
    # Category hierarchy
    category1: str | None  # Primary category
    category2: str | None  # Secondary category  
    category3: str | None  # Tertiary category
    
    # Content fields
    title: str | None  # Document title
    content: str | None  # Main document content
    answer: str | None  # Answer text for Q&A documents
    blob_path: str | None  # Path to the source blob/file
    chunk: str | None  # Text chunk for RAG operations
    disclaimer: str | None  # Disclaimer text
    
    # Product information
    family_code: list | None  # Product family codes
    family_name: list | None  # Product family names
    file_name: str | None  # Original filename
    
    # Question/Answer metadata
    question: str | None  # Question text
    question_category: str | None  # Category of the question
    type: str | None  # Document type
    
    # Display and ordering
    display_seq: int | None  # Display sequence number
    page_num: int | None  # Page number in source document
    question_num: int | None  # Question number
    section_num: int | None  # Section number
    reg_date: datetime | None  # Registration date
    
    # Product codes and identifiers
    common_code: list[str] | None  # Common product codes
    goods_id: list[str] | None  # Goods identifiers
    goods_nm: list[str] | None  # Goods names
    img_data: list[str] | None  # Image data URLs
    product_model_code: list[str] | None  # Product model codes
    product_model_group_code: list[str] | None  # Product model group codes
    product_model_name: list[str] | None  # Product model names
    product_model: list[str] | None  # Product models
    
    # Vector search fields
    embedding_chunk: list[float] | None  # Vector embeddings for semantic search
    products: list | None  # Related products
    partner_products: list | None  # Partner products
    
    # Display timing
    disp_end_dtm: datetime | None  # Display end datetime
    disp_strt_dtm: datetime | None  # Display start datetime
    is_display: int | None  # Display flag (0/1)

    # Search result metadata (populated by Azure AI Search)
    _search_score: float  # Search relevance score
    _search_reranker_score: float  # Reranker score for vector search
    _search_highlights: None  # Search highlights
    _search_captions: list  # Search result captions

    @pydantic.field_validator(
        "reg_date", "disp_end_dtm", "disp_strt_dtm", mode="before"
    )
    def parse_datetime(cls, value):
        """Parse datetime strings into datetime objects with timezone handling.
        
        Args:
            value: The datetime value to parse (string or datetime object)
            
        Returns:
            datetime: Parsed datetime object with UTC timezone if none specified
        """
        if value is None:
            return value
        if isinstance(value, str):
            # Attempt to parse the ISO-formatted string.
            dt = datetime.fromisoformat(value)
            # If no timezone info, assign a default timezone (UTC in this example).
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=pytz.UTC)
            return dt
        return value

    @classmethod
    def from_result(cls, result_dict):
        """Create an AISearchDocument instance from a search result dictionary.
        
        This method handles the conversion of Azure AI Search result keys that
        contain special characters (@, .) to valid Python attribute names.
        
        Args:
            result_dict (dict): Raw search result dictionary from Azure AI Search
            
        Returns:
            AISearchDocument: Parsed document instance
        """
        result_dict = result_dict.copy()
        del_key_list = []
        add_dict = {}

        # Convert keys with special characters (@, .) to valid attribute names
        for k in result_dict:
            if "@" in k or "." in k:
                norm_key = k.replace("@", "_").replace(".", "_")
                add_dict[norm_key] = result_dict[k]
                del_key_list.append(k)

        result_dict.update(add_dict)
        for k in del_key_list:
            del result_dict[k]

        return cls(**result_dict)
