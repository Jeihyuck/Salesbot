from apps.rubicon_v3.__function.ai_search.index.index_category_type import (
    IndexCategoryType,
)
from apps.rubicon_v3.__function.ai_search.index.index_info import IndexInfo


class _CountryCode:
    UK = "UK"
    KR = "KR"


# 인덱스 별로 IndexCategoryType별로 분기(조건 검색)를 하기 위한 메타 정보
class AiSearchIndexDefinitions:

    KR_BIXBY = IndexInfo(
        country_code=_CountryCode.KR,
        alias="BIXBY",
        category1_type=IndexCategoryType.PRODUCT_CATEGORY,
        category2_type=IndexCategoryType.PRODUCT_CATEGORY,
        category3_type=IndexCategoryType.PRODUCT_CATEGORY,
        has_model_code=False,
        integration_index_system_name="bixby-v2",
        use_integration_index=True,
    )
    KR_DOT_COM_CPT = IndexInfo(
        country_code=_CountryCode.KR,
        alias="DOT_COM:CPT",
        category1_type=IndexCategoryType.PRODUCT_CATEGORY,
        category2_type=IndexCategoryType.PRODUCT_CATEGORY,
        category3_type=IndexCategoryType.PRODUCT_CATEGORY,
        has_model_code=True,
        integration_index_system_name="cpt-modelgrp-v6",
        use_integration_index=True,
        always_use_in_response=True,
    )
    KR_DOT_COM_CPT_CATEGORY = IndexInfo(
        country_code=_CountryCode.KR,
        alias="DOT_COM:CPT_CATEGORY",
        category1_type=IndexCategoryType.PRODUCT_CATEGORY,
        category2_type=IndexCategoryType.PRODUCT_CATEGORY,
        category3_type=IndexCategoryType.PRODUCT_CATEGORY,
        has_model_code=True,
        integration_index_system_name="cpt-categorygrp-v5",
        use_integration_index=True,
        always_use_in_response=True,
    )
    KR_DOT_COM_SCRAP = IndexInfo(
        country_code=_CountryCode.KR,
        alias="DOT_COM:SCRAP",
        category1_type=IndexCategoryType.SCRP_KR_CATEGORY,
        category2_type=IndexCategoryType.SCRP_KR_CATEGORY,
        category3_type=None,
        integration_index_system_name="scrp-v10",
        use_integration_index=True,
    )
    KR_EX_RE = IndexInfo(
        country_code=_CountryCode.KR,
        alias="EX_RE",
        category1_type=IndexCategoryType.PRODUCT_CATEGORY,
        category2_type=IndexCategoryType.PRODUCT_CATEGORY,
        category3_type=IndexCategoryType.PRODUCT_CATEGORY,
        has_model_code=True,
        integration_index_system_name="exre-v10",
        use_integration_index=True,
    )
    KR_FAQ = IndexInfo(
        country_code=_CountryCode.KR,
        alias="FAQ",
        category1_type=IndexCategoryType.PRODUCT_CATEGORY,
        category2_type=IndexCategoryType.PRODUCT_CATEGORY,
        category3_type=IndexCategoryType.PRODUCT_CATEGORY,
        has_model_code=True,
        integration_index_system_name="pvi-faq-v6",
        use_integration_index=True,
    )
    KR_INSTALLATION = IndexInfo(
        country_code=_CountryCode.KR,
        alias="INSTALLATION",
        category1_type=IndexCategoryType.PRODUCT_CATEGORY,
        category2_type=IndexCategoryType.PRODUCT_CATEGORY,
        category3_type=IndexCategoryType.PRODUCT_CATEGORY,
        has_model_code=True,
        minimum_valid_text_length=10,
        integration_index_system_name="installation-v2",
        use_integration_index=True,
        always_use_in_response=True,
    )
    KR_MANUAL = IndexInfo(
        country_code=_CountryCode.KR,
        alias="MANUAL",
        category1_type=IndexCategoryType.PRODUCT_CATEGORY,
        category2_type=IndexCategoryType.PRODUCT_CATEGORY,
        category3_type=IndexCategoryType.PRODUCT_CATEGORY,
        has_model_code=True,
        integration_index_system_name="scms-v14",
        use_integration_index=True,
        always_use_in_response=True,
    )
    KR_MEDIA_IMAGE = IndexInfo(
        country_code=_CountryCode.KR,
        alias="MEDIA_IMAGE",
        category1_type=IndexCategoryType.PRODUCT_CATEGORY,
        category2_type=IndexCategoryType.PRODUCT_CATEGORY,
        category3_type=IndexCategoryType.PRODUCT_CATEGORY,
        has_model_code=True,
        integration_index_system_name="cpt-media",
        use_integration_index=False,
    )
    KR_MEDIA_VIDEO = IndexInfo(
        country_code=_CountryCode.KR,
        alias="MEDIA_VIDEO",
        category1_type=IndexCategoryType.PRODUCT_CATEGORY,
        category2_type=IndexCategoryType.PRODUCT_CATEGORY,
        category3_type=IndexCategoryType.PRODUCT_CATEGORY,
        integration_index_system_name="ytb-v8",
        use_integration_index=False,
    )
    KR_NEWS = IndexInfo(
        country_code=_CountryCode.KR,
        alias="NEWS",
        integration_index_system_name="news-v5",
        use_integration_index=True,
    )
    KR_PROMOTION = IndexInfo(
        country_code=_CountryCode.KR,
        alias="PROMOTION",
        category1_type=IndexCategoryType.PRODUCT_CATEGORY,
        category2_type=IndexCategoryType.PRODUCT_CATEGORY,
        category3_type=IndexCategoryType.PRODUCT_CATEGORY,
        has_model_code=True,
        has_embedding_chunk=True,
        minimum_valid_text_length=10,
        integration_index_system_name="promotion-v3",
        has_display_date=True,
        use_integration_index=True,
        always_use_in_response=True,
    )
    KR_PROMOTION_COMMON = IndexInfo(
        country_code=_CountryCode.KR,
        alias="PROMOTION:COMMON",
        has_model_code=False,
        has_embedding_chunk=True,
        minimum_valid_text_length=10,
        integration_index_system_name="promotion-common-v3",
        has_display_date=True,
        use_integration_index=True,
        always_use_in_response=True,
    )
    KR_PURCHASE_GUIDE = IndexInfo(
        country_code=_CountryCode.KR,
        alias="PURCHASE_GUIDE",
        category1_type=IndexCategoryType.PRODUCT_CATEGORY,
        category2_type=IndexCategoryType.PRODUCT_CATEGORY,
        category3_type=IndexCategoryType.PRODUCT_CATEGORY,
        has_model_code=True,
        has_embedding_chunk=True,
        minimum_valid_text_length=10,
        integration_index_system_name="purchaseguide-v2",
        use_integration_index=False,
    )
    KR_REP_IMAGE = IndexInfo(
        country_code=_CountryCode.KR,
        alias=None,
        category1_type=IndexCategoryType.PRODUCT_CATEGORY,
        category2_type=IndexCategoryType.PRODUCT_CATEGORY,
        category3_type=IndexCategoryType.PRODUCT_CATEGORY,
        has_model_code=True,
        integration_index_system_name="cpt-rep-image-v2",
        use_integration_index=True,
    )
    KR_SALES_TALK = IndexInfo(
        country_code=_CountryCode.KR,
        alias="SALES_TALK",
        category1_type=IndexCategoryType.PRODUCT_CATEGORY,
        category2_type=IndexCategoryType.PRODUCT_CATEGORY,
        category3_type=IndexCategoryType.PRODUCT_CATEGORY,
        has_model_code=True,
        integration_index_system_name="pvi-v8",
        use_integration_index=True,
    )
    KR_SMARTTHINGS_HTU = IndexInfo(
        country_code=_CountryCode.KR,
        alias="SMARTTHINGS:HTU",
        integration_index_system_name="smt-htu-v2",
        use_integration_index=True,
    )
    KR_SMARTTHINGS_INFO = IndexInfo(
        country_code=_CountryCode.KR,
        alias="SMARTTHINGS:INFO",
        has_model_code=True,
        integration_index_system_name="smt-info-v2",
        use_integration_index=True,
        always_use_in_response=True,
    )
    KR_SMCS = IndexInfo(
        country_code=_CountryCode.KR,
        alias="SMCS",
        integration_index_system_name="smcs-v2",
        use_integration_index=True,
    )
    # KR 통합 인덱스
    KR_INTEGRATION = IndexInfo(
        country_code=_CountryCode.KR,
        alias="INTEGRATION",
        integration_index_system_name=None,
        use_integration_index=False,
    )
    ########################################
    UK_BIXBY = IndexInfo(
        country_code=_CountryCode.UK,
        alias="BIXBY",
        category1_type=IndexCategoryType.PRODUCT_CATEGORY,
        category2_type=IndexCategoryType.PRODUCT_CATEGORY,
        category3_type=IndexCategoryType.PRODUCT_CATEGORY,
        has_model_code=False,
        integration_index_system_name="bixby-v2",
        use_integration_index=True,
    )
    UK_DOT_COM_CPT = IndexInfo(
        country_code=_CountryCode.UK,
        alias="DOT_COM:CPT",
        category1_type=IndexCategoryType.PRODUCT_CATEGORY,
        category2_type=IndexCategoryType.PRODUCT_CATEGORY,
        category3_type=IndexCategoryType.PRODUCT_CATEGORY,
        has_model_code=True,
        integration_index_system_name="pim-v13",
        use_integration_index=True,
        always_use_in_response=True,
    )
    UK_DOT_COM_SCRAP = IndexInfo(
        country_code=_CountryCode.UK,
        alias="DOT_COM:SCRAP",
        category1_type=IndexCategoryType.SCRP_UK_CATEGORY,
        category2_type=IndexCategoryType.SCRP_UK_CATEGORY,
        category3_type=None,
        integration_index_system_name="scrp-v10",
        use_integration_index=True,
    )
    UK_FAQ = IndexInfo(
        country_code=_CountryCode.UK,
        alias="FAQ",
        category1_type=IndexCategoryType.PRODUCT_CATEGORY,
        category2_type=IndexCategoryType.PRODUCT_CATEGORY,
        category3_type=IndexCategoryType.PRODUCT_CATEGORY,
        has_model_code=True,
        integration_index_system_name="pvi-faq-v5",
        use_integration_index=True,
    )
    UK_INSTALLATION = IndexInfo(
        country_code=_CountryCode.UK,
        alias="INSTALLATION",
        category1_type=IndexCategoryType.PRODUCT_CATEGORY,
        category2_type=IndexCategoryType.PRODUCT_CATEGORY,
        category3_type=IndexCategoryType.PRODUCT_CATEGORY,
        has_model_code=True,
        minimum_valid_text_length=10,
        integration_index_system_name="installation-v2",
        use_integration_index=True,
        always_use_in_response=True,
    )
    # UK 통합 인덱스
    UK_INTEGRATION = IndexInfo(
        country_code=_CountryCode.UK,
        alias="INTEGRATION",
        integration_index_system_name=None,
        use_integration_index=False,
    )

    UK_MANUAL = IndexInfo(
        country_code=_CountryCode.UK,
        alias="MANUAL",
        category1_type=IndexCategoryType.PRODUCT_CATEGORY,
        category2_type=IndexCategoryType.PRODUCT_CATEGORY,
        category3_type=IndexCategoryType.PRODUCT_CATEGORY,
        has_model_code=True,
        integration_index_system_name="scms-v13",
        use_integration_index=True,
        always_use_in_response=True,
    )
    UK_MEDIA_VIDEO = IndexInfo(
        country_code=_CountryCode.UK,
        alias="MEDIA_VIDEO",
        category1_type=IndexCategoryType.PRODUCT_CATEGORY,
        category2_type=IndexCategoryType.PRODUCT_CATEGORY,
        category3_type=IndexCategoryType.PRODUCT_CATEGORY,
        integration_index_system_name="ytb-v8",
        use_integration_index=False,
    )
    UK_NEWS = IndexInfo(
        country_code=_CountryCode.UK,
        alias="NEWS",
        integration_index_system_name="news-v5",
        use_integration_index=True,
    )
    UK_PROMOTION = IndexInfo(
        country_code=_CountryCode.UK,
        alias="PROMOTION",
        category1_type=IndexCategoryType.PRODUCT_CATEGORY,
        category2_type=IndexCategoryType.PRODUCT_CATEGORY,
        category3_type=IndexCategoryType.PRODUCT_CATEGORY,
        has_model_code=True,
        has_embedding_chunk=False,
        minimum_valid_text_length=10,
        integration_index_system_name="promotion-v3",
        has_display_date=True,
        use_integration_index=True,
        always_use_in_response=True,
    )
    UK_PURCHASE_GUIDE = IndexInfo(
        country_code=_CountryCode.UK,
        alias="PURCHASE_GUIDE",
        category1_type=IndexCategoryType.PRODUCT_CATEGORY,
        category2_type=IndexCategoryType.PRODUCT_CATEGORY,
        category3_type=IndexCategoryType.PRODUCT_CATEGORY,
        has_model_code=True,
        has_embedding_chunk=True,
        minimum_valid_text_length=10,
        integration_index_system_name="purchaseguide-v2",
        use_integration_index=False,
    )
    UK_REP_IMAGE = IndexInfo(
        country_code=_CountryCode.UK,
        alias="REP_IMAGE",
        category1_type=IndexCategoryType.PRODUCT_CATEGORY,
        category2_type=IndexCategoryType.PRODUCT_CATEGORY,
        category3_type=IndexCategoryType.PRODUCT_CATEGORY,
        has_model_code=True,
        integration_index_system_name="pim-rep-image-v6",
        use_integration_index=True,
    )
    UK_SALES_TALK = IndexInfo(
        country_code=_CountryCode.UK,
        alias="SALES_TALK",
        category1_type=IndexCategoryType.PRODUCT_CATEGORY,
        category2_type=IndexCategoryType.PRODUCT_CATEGORY,
        category3_type=IndexCategoryType.PRODUCT_CATEGORY,
        has_model_code=True,
        integration_index_system_name="pvi-v7",
        use_integration_index=True,
    )
    UK_SMATRTHINGS_HTU = IndexInfo(
        country_code=_CountryCode.UK,
        alias="SMARTTHINGS:HTU",
        integration_index_system_name="smt-htu-v2",
        use_integration_index=True,
    )
    UK_SMARTTHINGS_INFO = IndexInfo(
        country_code=_CountryCode.UK,
        alias="SMARTTHINGS:INFO",
        integration_index_system_name="smt-info-v2",
        use_integration_index=True,
        always_use_in_response=True,
    )

    UK_SMCS = IndexInfo(
        country_code=_CountryCode.UK,
        alias="SMCS",
        integration_index_system_name="smcs-v2",
        use_integration_index=True,
    )

    ALIAS_INTEGRATION = "INTEGRATION"

    @classmethod
    def from_values(cls, country_code: str, alias: str):
        index_fields = [
            name for name, value in vars(cls).items() if isinstance(value, IndexInfo)
        ]
        for name in index_fields:
            item = getattr(cls, name)
            if item.country_code == country_code and item.alias == alias:
                return item
        return None

    @classmethod
    def find(
        cls, always_use_in_response: bool | None = None, country_code: str | None = None
    ):
        index_fields = [
            name for name, value in vars(cls).items() if isinstance(value, IndexInfo)
        ]

        l: list[IndexInfo] = []

        for name in index_fields:
            item: IndexInfo = getattr(cls, name)

            if (
                always_use_in_response is not None
                and item.always_use_in_response != always_use_in_response
            ):
                continue

            if country_code is not None and item.country_code != country_code:
                continue

            l.append(item)
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
