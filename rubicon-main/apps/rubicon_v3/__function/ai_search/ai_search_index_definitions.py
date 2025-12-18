import sys

sys.path.append("/www/alpha/")

import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "alpha.settings")
django.setup()


from alpha.settings import VITE_OP_TYPE, VITE_COUNTRY
from apps.rubicon_v3.__function.ai_search.index.index_category_type import (
    IndexCategoryType,
)
from apps.rubicon_v3.__function.ai_search.index.index_info import IndexInfo
from apps.rubicon_v3.models import Unstructured_Index, Pipeline_Version_KR, Pipeline_Version_UK


class _CountryCode:
    GB = "GB"
    KR = "KR"


# Meta information for branching (conditional search) by IndexCategoryType for each index
class AiSearchIndexDefinitions:

    @staticmethod
    def get_system_name(country, optype, alias):
        get_index_name = Unstructured_Index.objects.filter(
            country_code=country, op_type=optype, name=alias
        ).values("ai_search_index")

        system_name = list(get_index_name)[0]["ai_search_index"]
        if 'media' in system_name:
            check_column = 'local_last_version'
        else:
            check_column = 'integration_last_version'

        version_info = None
        if country == _CountryCode.KR:
            # For KR, version information is fetched from Pipeline_Version_KR
            version_info = (
                Pipeline_Version_KR.objects.filter(
                    system_name=system_name
                )
                .values_list(check_column, flat=True)
                .first()
            )
        if country == _CountryCode.GB:
            # For UK, version information is fetched from Pipeline_Version_UK
            version_info = (
                Pipeline_Version_UK.objects.filter(
                    system_name=system_name
                )
                .values_list(check_column, flat=True)
                .first()
            )
            
        return [system_name, version_info]

    @classmethod
    def KR_BIXBY(cls):
        return IndexInfo(
            country_code=_CountryCode.KR,
            alias="BIXBY",
            category1_type=IndexCategoryType.PRODUCT_CATEGORY,
            category2_type=IndexCategoryType.PRODUCT_CATEGORY,
            category3_type=IndexCategoryType.PRODUCT_CATEGORY,
            has_model_code=False,
            integration_index_system_name=cls.get_system_name(
                _CountryCode.KR, VITE_OP_TYPE, "BIXBY"
            ),
            use_integration_index=True,
        )
    
    @classmethod
    def KR_DOT_COM_CPT(cls):
        return IndexInfo(
            country_code=_CountryCode.KR,
            alias="DOT_COM:CPT",
            category1_type=IndexCategoryType.PRODUCT_CATEGORY,
            category2_type=IndexCategoryType.PRODUCT_CATEGORY,
            category3_type=IndexCategoryType.PRODUCT_CATEGORY,
            has_model_code=True,
            integration_index_system_name=cls.get_system_name(
                _CountryCode.KR, VITE_OP_TYPE, "DOT_COM:CPT"
            ),
            use_integration_index=True,
            always_use_in_response=True,
        )
    
    @classmethod
    def KR_DOT_COM_CPT_CATEGORY(cls):
        return IndexInfo(
            country_code=_CountryCode.KR,
            alias="DOT_COM:CPT_CATEGORY",
            category1_type=IndexCategoryType.PRODUCT_CATEGORY,
            category2_type=IndexCategoryType.PRODUCT_CATEGORY,
            category3_type=IndexCategoryType.PRODUCT_CATEGORY,
            has_model_code=True,
            integration_index_system_name=cls.get_system_name(
                _CountryCode.KR, VITE_OP_TYPE, "DOT_COM:CPT_CATEGORY"
            ),
            use_integration_index=True,
            always_use_in_response=True,
        )
    
    @classmethod
    def KR_DOT_COM_SCRAP(cls):
        return IndexInfo(
            country_code=_CountryCode.KR,
            alias="DOT_COM:SCRAP",
            integration_index_system_name=cls.get_system_name(
                _CountryCode.KR, VITE_OP_TYPE, "DOT_COM:SCRAP"
            ),
            use_integration_index=True,
        )
    
    @classmethod
    def KR_FN_SCRAP(cls):
        return IndexInfo(
            country_code=_CountryCode.KR,
            alias="FN:SCRAP",
            integration_index_system_name=cls.get_system_name(
                _CountryCode.KR, VITE_OP_TYPE, "FN:SCRAP"
            ),
            use_integration_index=True,
        )
    
    @classmethod
    def KR_FN_NOTICE(cls):
        return IndexInfo(
            country_code=_CountryCode.KR,
            alias="FN:NOTICE",
            integration_index_system_name=cls.get_system_name(
                _CountryCode.KR, VITE_OP_TYPE, "FN:NOTICE"
            ),
            use_integration_index=True,
        )
    
    @classmethod
    def KR_EX_RE(cls):
        return IndexInfo(
            country_code=_CountryCode.KR,
            alias="EX_RE",
            category1_type=IndexCategoryType.PRODUCT_CATEGORY,
            category2_type=IndexCategoryType.PRODUCT_CATEGORY,
            category3_type=IndexCategoryType.PRODUCT_CATEGORY,
            has_model_code=True,
            has_types=True,
            integration_index_system_name=cls.get_system_name(
                _CountryCode.KR, VITE_OP_TYPE, "EX_RE"
            ),
            use_integration_index=True,
        )
    
    @classmethod
    def KR_FAQ(cls):
        return IndexInfo(
            country_code=_CountryCode.KR,
            alias="FAQ",
            category1_type=IndexCategoryType.PRODUCT_CATEGORY,
            category2_type=IndexCategoryType.PRODUCT_CATEGORY,
            category3_type=IndexCategoryType.PRODUCT_CATEGORY,
            has_model_code=True,
            integration_index_system_name=cls.get_system_name(
                _CountryCode.KR, VITE_OP_TYPE, "FAQ"
            ),
            use_integration_index=True,
        )
    
    @classmethod
    def KR_INSTALLATION(cls):
        return IndexInfo(
            country_code=_CountryCode.KR,
            alias="INSTALLATION",
            category1_type=IndexCategoryType.PRODUCT_CATEGORY,
            category2_type=IndexCategoryType.PRODUCT_CATEGORY,
            category3_type=IndexCategoryType.PRODUCT_CATEGORY,
            has_model_code=True,
            minimum_valid_text_length=10,
            integration_index_system_name=cls.get_system_name(
                _CountryCode.KR, VITE_OP_TYPE, "INSTALLATION"
            ),
            use_integration_index=True,
            always_use_in_response=True,
        )
    
    @classmethod
    def KR_MANUAL(cls):
        return IndexInfo(
            country_code=_CountryCode.KR,
            alias="MANUAL",
            category1_type=IndexCategoryType.PRODUCT_CATEGORY,
            category2_type=IndexCategoryType.PRODUCT_CATEGORY,
            category3_type=IndexCategoryType.PRODUCT_CATEGORY,
            has_model_code=True,
            integration_index_system_name=cls.get_system_name(
                _CountryCode.KR, VITE_OP_TYPE, "MANUAL"
            ),
            use_integration_index=True,
            always_use_in_response=False,
        )
    
    @classmethod
    def KR_MANUAL_N10(cls):
        return IndexInfo(
            country_code=_CountryCode.KR,
            alias="MANUAL:N10",
            category1_type=IndexCategoryType.PRODUCT_CATEGORY,
            category2_type=IndexCategoryType.PRODUCT_CATEGORY,
            category3_type=IndexCategoryType.PRODUCT_CATEGORY,
            has_model_code=True,
            integration_index_system_name=cls.get_system_name(
                _CountryCode.KR, VITE_OP_TYPE, "MANUAL:N10"
            ),
            use_integration_index=False,
            always_use_in_response=False,
        )
    
    @classmethod
    def KR_MEDIA_IMAGE(cls):
        return IndexInfo(
            country_code=_CountryCode.KR,
            alias="MEDIA_IMAGE",
            category1_type=IndexCategoryType.PRODUCT_CATEGORY,
            category2_type=IndexCategoryType.PRODUCT_CATEGORY,
            category3_type=IndexCategoryType.PRODUCT_CATEGORY,
            has_model_code=True,
            integration_index_system_name=cls.get_system_name(
                _CountryCode.KR, VITE_OP_TYPE, "MEDIA_IMAGE"
            ),
            use_integration_index=False,
        )
    
    @classmethod
    def KR_FN_MEDIA_IMAGE(cls):
        return IndexInfo(
            country_code=_CountryCode.KR,
            alias="FN:MEDIA_IMAGE",
            category1_type=IndexCategoryType.PRODUCT_CATEGORY,
            category2_type=IndexCategoryType.PRODUCT_CATEGORY,
            category3_type=IndexCategoryType.PRODUCT_CATEGORY,
            has_model_code=True,
            integration_index_system_name=cls.get_system_name(
                _CountryCode.KR, VITE_OP_TYPE, "FN:MEDIA_IMAGE"
            ),
            use_integration_index=False,
        )
    
    @classmethod
    def KR_MEDIA_VIDEO(cls):
        return IndexInfo(
            country_code=_CountryCode.KR,
            alias="MEDIA_VIDEO",
            category1_type=IndexCategoryType.PRODUCT_CATEGORY,
            category2_type=IndexCategoryType.PRODUCT_CATEGORY,
            category3_type=IndexCategoryType.PRODUCT_CATEGORY,
            integration_index_system_name=cls.get_system_name(
                _CountryCode.KR, VITE_OP_TYPE, "MEDIA_VIDEO"
            ),
            use_integration_index=False,
        )
    
    @classmethod
    def KR_NEWS(cls): 
        return IndexInfo(
            country_code=_CountryCode.KR,
            has_reg_date=True,
            alias="NEWS",
            integration_index_system_name=cls.get_system_name(
                _CountryCode.KR, VITE_OP_TYPE, "NEWS"
            ),
            use_integration_index=True,
        )
    
    @classmethod
    def KR_PROMOTION(cls):
        return IndexInfo(
            country_code=_CountryCode.KR,
            alias="PROMOTION",
            category1_type=IndexCategoryType.PRODUCT_CATEGORY,
            category2_type=IndexCategoryType.PRODUCT_CATEGORY,
            category3_type=IndexCategoryType.PRODUCT_CATEGORY,
            has_model_code=True,
            has_embedding_chunk=True,
            minimum_valid_text_length=10,
            integration_index_system_name=cls.get_system_name(
                _CountryCode.KR, VITE_OP_TYPE, "PROMOTION"
            ),
            has_display_date=True,
            use_integration_index=True,
            always_use_in_response=True,
        )
    
    @classmethod
    def KR_PROMOTION_COMMON(cls):
        return IndexInfo(
            country_code=_CountryCode.KR,
            alias="PROMOTION:COMMON",
            has_model_code=False,
            has_embedding_chunk=True,
            minimum_valid_text_length=10,
            integration_index_system_name=cls.get_system_name(
                _CountryCode.KR, VITE_OP_TYPE, "PROMOTION:COMMON"
            ),
            has_display_date=True,
            use_integration_index=True,
            always_use_in_response=True,
        )
    
    @classmethod
    def KR_FN_PROMOTION(cls):
        return IndexInfo(
            country_code=_CountryCode.KR,
            alias="FN:PROMOTION",
            category1_type=IndexCategoryType.PRODUCT_CATEGORY,
            category2_type=IndexCategoryType.PRODUCT_CATEGORY,
            category3_type=IndexCategoryType.PRODUCT_CATEGORY,
            has_model_code=True,
            has_embedding_chunk=True,
            minimum_valid_text_length=10,
            integration_index_system_name=cls.get_system_name(
                _CountryCode.KR, VITE_OP_TYPE, "FN:PROMOTION"
            ),
            has_display_date=True,
            use_integration_index=True,
            always_use_in_response=True,
        )
    
    @classmethod
    def KR_FN_PROMOTION_COMMON(cls):
        return IndexInfo(
            country_code=_CountryCode.KR,
            alias="FN:PROMOTION:COMMON",
            has_model_code=False,
            has_embedding_chunk=True,
            has_reg_date=True,
            minimum_valid_text_length=10,
            integration_index_system_name=cls.get_system_name(
                _CountryCode.KR, VITE_OP_TYPE, "FN:PROMOTION:COMMON"
            ),
            has_display_date=True,
            use_integration_index=True,
            always_use_in_response=True,
        )
    
    @classmethod
    def KR_PURCHASE_GUIDE(cls):
        return IndexInfo(
            country_code=_CountryCode.KR,
            alias="PURCHASE_GUIDE",
            category1_type=IndexCategoryType.PRODUCT_CATEGORY,
            category2_type=IndexCategoryType.PRODUCT_CATEGORY,
            category3_type=IndexCategoryType.PRODUCT_CATEGORY,
            has_model_code=True,
            has_embedding_chunk=True,
            minimum_valid_text_length=10,
            integration_index_system_name=cls.get_system_name(
                _CountryCode.KR, VITE_OP_TYPE, "PURCHASE_GUIDE"
            ),
            use_integration_index=True,
        )
    
    @classmethod
    def KR_REP_IMAGE(cls):
        return IndexInfo(
            country_code=_CountryCode.KR,
            alias=None,
            category1_type=IndexCategoryType.PRODUCT_CATEGORY,
            category2_type=IndexCategoryType.PRODUCT_CATEGORY,
            category3_type=IndexCategoryType.PRODUCT_CATEGORY,
            has_model_code=True,
            integration_index_system_name=cls.get_system_name(
                _CountryCode.KR, VITE_OP_TYPE, "REP_IMAGE"
            ),
            use_integration_index=True,
        )
    
    @classmethod
    def KR_SALES_TALK(cls):
        return IndexInfo(
            country_code=_CountryCode.KR,
            alias="SALES_TALK",
            category1_type=IndexCategoryType.PRODUCT_CATEGORY,
            category2_type=IndexCategoryType.PRODUCT_CATEGORY,
            category3_type=IndexCategoryType.PRODUCT_CATEGORY,
            has_model_code=True,
            integration_index_system_name=cls.get_system_name(
                _CountryCode.KR, VITE_OP_TYPE, "SALES_TALK"
            ),
            use_integration_index=True,
        )
    
    @classmethod
    def KR_SMARTTHINGS_HTU(cls):
        return IndexInfo(
            country_code=_CountryCode.KR,
            alias="SMARTTHINGS:HTU",
            integration_index_system_name=cls.get_system_name(
                _CountryCode.KR, VITE_OP_TYPE, "SMARTTHINGS:HTU"
            ),
            use_integration_index=True,
        )
    
    @classmethod
    def KR_SMARTTHINGS_INFO(cls):
        return IndexInfo(
            country_code=_CountryCode.KR,
            alias="SMARTTHINGS:INFO",
            has_model_code=True,
            integration_index_system_name=cls.get_system_name(
                _CountryCode.KR, VITE_OP_TYPE, "SMARTTHINGS:INFO"
            ),
            use_integration_index=True,
        )
    
    @classmethod
    def KR_SMARTTHINGS_INFO_EXTENDED(cls):
        return IndexInfo(
            country_code=_CountryCode.KR,
            alias="SMARTTHINGS:INFO_EXT",
            integration_index_system_name=cls.get_system_name(
                _CountryCode.KR, VITE_OP_TYPE, "SMARTTHINGS:INFO_EXT"
            ),
            use_integration_index=True,
        )
    
    @classmethod
    def KR_SMCS(cls):
        return IndexInfo(
            country_code=_CountryCode.KR,
            alias="SMCS",
            integration_index_system_name=cls.get_system_name(
                _CountryCode.KR, VITE_OP_TYPE, "SMCS"
            ),
            use_integration_index=True,
        )
    

    # KR Integration Indexes
    @classmethod
    def KR_INTEGRATION(cls):
        return IndexInfo(
            country_code=_CountryCode.KR,
            alias="INTEGRATION",
            integration_index_system_name=None,
            use_integration_index=False,
        )
    
    @classmethod
    def KR_SOLUTION(cls):
        return IndexInfo(
            country_code=_CountryCode.KR,
            alias="SOLUTION",
            integration_index_system_name=cls.get_system_name(
                _CountryCode.KR, VITE_OP_TYPE, "SOLUTION"
            ),
            use_integration_index=True,
        )
    # KR Integration
    ########################################
    
    @classmethod
    def GB_BIXBY(cls):
        return IndexInfo(
            country_code=_CountryCode.GB,
            alias="BIXBY",
            category1_type=IndexCategoryType.PRODUCT_CATEGORY,
            category2_type=IndexCategoryType.PRODUCT_CATEGORY,
            category3_type=IndexCategoryType.PRODUCT_CATEGORY,
            has_model_code=False,
            integration_index_system_name=cls.get_system_name(
                _CountryCode.GB, VITE_OP_TYPE, "BIXBY"
            ),
            use_integration_index=True,
        )
    
    @classmethod
    def GB_DOT_COM_CPT(cls):
        return IndexInfo(
            country_code=_CountryCode.GB,
            alias="DOT_COM:CPT",
            category1_type=IndexCategoryType.PRODUCT_CATEGORY,
            category2_type=IndexCategoryType.PRODUCT_CATEGORY,
            category3_type=IndexCategoryType.PRODUCT_CATEGORY,
            has_model_code=True,
            integration_index_system_name=cls.get_system_name(
                _CountryCode.GB, VITE_OP_TYPE, "DOT_COM:CPT"
            ),
            use_integration_index=True,
            always_use_in_response=True,
        )
    
    @classmethod
    def GB_DOT_COM_SCRAP(cls):
        return IndexInfo(
            country_code=_CountryCode.GB,
            alias="DOT_COM:SCRAP",
            integration_index_system_name=cls.get_system_name(
                _CountryCode.GB, VITE_OP_TYPE, "DOT_COM:SCRAP"
            ),
            use_integration_index=True,
        )
    
    @classmethod
    def GB_FAQ(cls):
        return IndexInfo(
            country_code=_CountryCode.GB,
            alias="FAQ",
            category1_type=IndexCategoryType.PRODUCT_CATEGORY,
            category2_type=IndexCategoryType.PRODUCT_CATEGORY,
            category3_type=IndexCategoryType.PRODUCT_CATEGORY,
            has_model_code=True,
            integration_index_system_name=cls.get_system_name(
                _CountryCode.GB, VITE_OP_TYPE, "FAQ"
            ),
            use_integration_index=True,
        )
    
    @classmethod
    def GB_INSTALLATION(cls):
        return IndexInfo(
            country_code=_CountryCode.GB,
            alias="INSTALLATION",
            category1_type=IndexCategoryType.PRODUCT_CATEGORY,
            category2_type=IndexCategoryType.PRODUCT_CATEGORY,
            category3_type=IndexCategoryType.PRODUCT_CATEGORY,
            has_model_code=True,
            minimum_valid_text_length=10,
            integration_index_system_name=cls.get_system_name(
                _CountryCode.GB, VITE_OP_TYPE, "INSTALLATION"
            ),
            use_integration_index=True,
            always_use_in_response=True,
        )
    
    # GB Integration Indexes
    @classmethod
    def GB_INTEGRATION(cls):
        return IndexInfo(
            country_code=_CountryCode.GB,
            alias="INTEGRATION",
            integration_index_system_name=None,
            use_integration_index=False,
        )

    @classmethod
    def GB_MANUAL(cls):
        return IndexInfo(
            country_code=_CountryCode.GB,
            alias="MANUAL",
            category1_type=IndexCategoryType.PRODUCT_CATEGORY,
            category2_type=IndexCategoryType.PRODUCT_CATEGORY,
            category3_type=IndexCategoryType.PRODUCT_CATEGORY,
            has_model_code=True,
            integration_index_system_name=cls.get_system_name(
                _CountryCode.GB, VITE_OP_TYPE, "MANUAL"
            ),
            use_integration_index=True,
        )
    
    @classmethod
    def GB_MANUAL_N10(cls):
        return IndexInfo(
            country_code=_CountryCode.GB,
            alias="MANUAL:N10",
            category1_type=IndexCategoryType.PRODUCT_CATEGORY,
            category2_type=IndexCategoryType.PRODUCT_CATEGORY,
            category3_type=IndexCategoryType.PRODUCT_CATEGORY,
            has_model_code=True,
            integration_index_system_name=cls.get_system_name(
                _CountryCode.GB, VITE_OP_TYPE, "MANUAL:N10"
            ),
            use_integration_index=False,
            always_use_in_response=False,
        )
    
    @classmethod
    def GB_MEDIA_IMAGE(cls):
        return IndexInfo(
            country_code=_CountryCode.GB,
            alias="MEDIA_IMAGE",
            has_model_code=True,
            category1_type=IndexCategoryType.PRODUCT_CATEGORY,
            category2_type=IndexCategoryType.PRODUCT_CATEGORY,
            category3_type=IndexCategoryType.PRODUCT_CATEGORY,
            integration_index_system_name=cls.get_system_name(
                _CountryCode.GB, VITE_OP_TYPE, "MEDIA_IMAGE"
            ),
            use_integration_index=False,
        )
    
    @classmethod
    def GB_MEDIA_VIDEO(cls):
        return IndexInfo(
            country_code=_CountryCode.GB,
            alias="MEDIA_VIDEO",
            category1_type=IndexCategoryType.PRODUCT_CATEGORY,
            category2_type=IndexCategoryType.PRODUCT_CATEGORY,
            category3_type=IndexCategoryType.PRODUCT_CATEGORY,
            integration_index_system_name=cls.get_system_name(
                _CountryCode.GB, VITE_OP_TYPE, "MEDIA_VIDEO"
            ),
            use_integration_index=False,
        )
    
    @classmethod
    def GB_NEWS(cls):
        return IndexInfo(
            country_code=_CountryCode.GB,
            alias="NEWS",
            integration_index_system_name=cls.get_system_name(
                _CountryCode.GB, VITE_OP_TYPE, "NEWS"
            ),
            use_integration_index=True,
        )
    
    @classmethod
    def GB_PROMOTION(cls):
        return IndexInfo(
            country_code=_CountryCode.GB,
            alias="PROMOTION",
            category1_type=IndexCategoryType.PRODUCT_CATEGORY,
            category2_type=IndexCategoryType.PRODUCT_CATEGORY,
            category3_type=IndexCategoryType.PRODUCT_CATEGORY,
            has_model_code=True,
            has_embedding_chunk=False,
            minimum_valid_text_length=10,
            integration_index_system_name=cls.get_system_name(
                _CountryCode.GB, VITE_OP_TYPE, "PROMOTION"
            ),
            has_display_date=True,
            use_integration_index=True,
            always_use_in_response=True,
        )
    
    @classmethod
    def GB_PURCHASE_GUIDE(cls):
        return IndexInfo(
            country_code=_CountryCode.GB,
            alias="PURCHASE_GUIDE",
            category1_type=IndexCategoryType.PRODUCT_CATEGORY,
            category2_type=IndexCategoryType.PRODUCT_CATEGORY,
            category3_type=IndexCategoryType.PRODUCT_CATEGORY,
            has_model_code=True,
            has_embedding_chunk=True,
            minimum_valid_text_length=10,
            integration_index_system_name=cls.get_system_name(
                _CountryCode.GB, VITE_OP_TYPE, "PURCHASE_GUIDE"
            ),
            use_integration_index=True,
        )
    
    @classmethod
    def GB_REP_IMAGE(cls):
        return IndexInfo(
            country_code=_CountryCode.GB,
            alias="REP_IMAGE",
            category1_type=IndexCategoryType.PRODUCT_CATEGORY,
            category2_type=IndexCategoryType.PRODUCT_CATEGORY,
            category3_type=IndexCategoryType.PRODUCT_CATEGORY,
            has_model_code=True,
            integration_index_system_name=cls.get_system_name(
                _CountryCode.GB, VITE_OP_TYPE, "REP_IMAGE"
            ),
            use_integration_index=True,
        )
    
    @classmethod
    def GB_SALES_TALK(cls):
        return IndexInfo(
            country_code=_CountryCode.GB,
            alias="SALES_TALK",
            category1_type=IndexCategoryType.PRODUCT_CATEGORY,
            category2_type=IndexCategoryType.PRODUCT_CATEGORY,
            category3_type=IndexCategoryType.PRODUCT_CATEGORY,
            has_model_code=True,
            integration_index_system_name=cls.get_system_name(
                _CountryCode.GB, VITE_OP_TYPE, "SALES_TALK"
            ),
            use_integration_index=True,
        )
    
    @classmethod
    def GB_SMARTTHINGS_HTU(cls):
        return IndexInfo(
            country_code=_CountryCode.GB,
            alias="SMARTTHINGS:HTU",
            integration_index_system_name=cls.get_system_name(
                _CountryCode.GB, VITE_OP_TYPE, "SMARTTHINGS:HTU"
            ),
            use_integration_index=True,
        )
    
    @classmethod
    def GB_SMARTTHINGS_INFO(cls):
        return IndexInfo(
            country_code=_CountryCode.GB,
            alias="SMARTTHINGS:INFO",
            integration_index_system_name=cls.get_system_name(
                _CountryCode.GB, VITE_OP_TYPE, "SMARTTHINGS:INFO"
            ),
            use_integration_index=True,
        )
    
    @classmethod
    def GB_SMARTTHINGS_INFO_EXTENDED(cls):
        return IndexInfo(
            country_code=_CountryCode.GB,
            alias="SMARTTHINGS:INFO_EXT",
            integration_index_system_name=cls.get_system_name(
                _CountryCode.GB, VITE_OP_TYPE, "SMARTTHINGS:INFO_EXT"
            ),
            use_integration_index=True,
        )

    @classmethod
    def GB_SMCS(cls):
        return IndexInfo(
            country_code=_CountryCode.GB,
            alias="SMCS",
            integration_index_system_name=cls.get_system_name(
                _CountryCode.GB, VITE_OP_TYPE, "SMCS"
            ),
            use_integration_index=True,
        )

    ALIAS_INTEGRATION = "INTEGRATION"

    @classmethod
    def from_values(cls, country_code: str, alias: str):
        # Get all method names that return IndexInfo
        index_methods = [
            name for name in dir(cls) 
            if (
                not name.startswith('_') and 
                name not in ['from_values', 'find', 'get_system_name'] and
                callable(getattr(cls, name))
            )
        ]
        
        for method_name in index_methods:
            try:
                item = getattr(cls, method_name)()  # Call the method
                if item.country_code == country_code and item.alias == alias:
                    return item
            except:
                continue  # Skip if method doesn't return IndexInfo
        return None

    @classmethod
    def find(
        cls, always_use_in_response: bool | None = None, country_code: str | None = None
    ):
        # Get all method names that return IndexInfo
        index_methods = [
            name for name in dir(cls) 
            if (
                not name.startswith('_') and 
                name not in ['from_values', 'find', 'get_system_name'] and
                callable(getattr(cls, name))
            )
        ]

        l: list[IndexInfo] = []

        for method_name in index_methods:
            try:
                item: IndexInfo = getattr(cls, method_name)()  # Call the method
                
                if (
                    always_use_in_response is not None
                    and item.always_use_in_response != always_use_in_response
                ):
                    continue

                if country_code is not None and item.country_code != country_code:
                    continue

                l.append(item)
            except:
                continue  # Skip if method doesn't return IndexInfo
                
        return l


if __name__ == "__main__":

    print(AiSearchIndexDefinitions.from_values("KR", "MANUAL"))
    index_fields = [
        name
        for name, value in vars(AiSearchIndexDefinitions).items()
        if isinstance(value, IndexInfo)
    ]

    print(f"\nalways_use_in_response\n{'='*20}")
    for info in AiSearchIndexDefinitions.find(always_use_in_response=True):
        print(f"{info.country_code} {info.alias} {info.integration_index_system_name}")
