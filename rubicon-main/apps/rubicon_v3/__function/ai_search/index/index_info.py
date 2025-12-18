from apps.rubicon_v3.__function.ai_search.index.index_category_type import IndexCategoryType


import pydantic


class IndexInfo(pydantic.BaseModel):
    country_code: str
    alias: str | None
    category1_type: IndexCategoryType | None = None
    category2_type: IndexCategoryType | None = None
    category3_type: IndexCategoryType | None = None
    has_model_code: bool = False
    has_embedding_chunk: bool = True
    has_display_date: bool = False
    has_reg_date: bool = False
    has_types: bool = False
    minimum_valid_text_length: int = (
        400  # 유효 텍스트 길이. 이 길이보다 작은 텍스트는 검색 결과에서 제외됨.
    )
    integration_index_system_name: list | None = (
        None  # integration 인덱스에 해당 인덱스 값이 합쳐져 있는 경우 이를 구분하는 system_name
    )
    use_integration_index: bool = (
        False  # 현재 인덱스를 참조할때 integration 인덱스를 사용할지 여부. True인 경우 integration_index_system_name이 필요함.
    )
    always_use_in_response: bool = False