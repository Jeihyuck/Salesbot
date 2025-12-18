from django.db import models
# from pgvector.django import HnswIndex
from pgvector.django import HnswIndex, IvfflatIndex
from pgvector.django import VectorField
from django.contrib.postgres.fields import ArrayField
from django.utils.translation import gettext_lazy as _

from apps.alpha_base.views import channel
from apps.alpha_log.views import service


MODULE = [
    ('AUG', _('Augmentation')),
    ('REW', _('Re-Write')),
    ('INT', _('Intelligence Triage')), 
    ('NER', _('NER')),
    ('PSQ', _('Pseudo Query')),
    ('FRS', _('Final Response')),
    ('N/A', _('N/A')),
]

LANGUAGE = [
    ('EN', _('English')),
    ('KO', _('Korean'))
]


class Assistant_Preferred_Recommendation(models.Model):
    id                          = models.AutoField(primary_key=True)
    category                    = models.CharField(verbose_name='Category', null=True, blank=True)
    preferred_recommendation    = models.CharField(verbose_name='Preferred Recommendation', null=True, blank=True)
    product                     = models.CharField(verbose_name='Product', null=True, blank=True)
    spec                        = models.TextField(verbose_name='Specification', null=True, blank=True)
    key_features                = models.TextField(verbose_name='Key Features', null=True, blank=True)
    target_audience             = models.TextField(verbose_name='Target Audience', null=True, blank=True)
    country_code                = models.CharField(verbose_name='Country Code', null=True, blank=True)
    site_cd                     = models.CharField(max_length=10, null=False, blank=False, verbose_name="닷컴 코드", default="B2C")

    class Meta:
        indexes = [
        	models.Index(fields=['country_code'], name="r3_apr_intelligence_idx"),
        ]


class Assistant_Ref_Info(models.Model):
    id                  = models.AutoField(primary_key=True)
    active              = models.BooleanField(verbose_name='Active', default=True)
    update_tag          = models.CharField(verbose_name='Update Tag', blank=True, null=True)
    country_code        = models.CharField(verbose_name='Country Code', null=True, blank=True)
    embedding = VectorField(
        dimensions=1024,  # Changed from 1536 to 1024 for bge-m3
        help_text="BAAI/bge-m3",
        null=True,
        blank=True,
    )
    title               = models.CharField(verbose_name='Title', null=True, blank=True)
    related_question    = models.TextField(verbose_name='Related Question', null=True, blank=True)
    text                = models.TextField(verbose_name='Text', null=True, blank=True)
    created_on          = models.DateTimeField(verbose_name='Create', auto_now_add=True)
    updated_on          = models.DateTimeField(verbose_name='Update', auto_now=True)
    site_cd             = models.CharField(max_length=10, null=False, blank=False, verbose_name="닷컴 코드", default="B2C")

    class Meta:
        indexes = [
        	models.Index(fields=['active', 'country_code'], name="r3_ari_idx"),
            HnswIndex(
                name="r3_ari_vector_idx",
                fields=["embedding"],
                m=16,
                ef_construction=64,
                opclasses=["vector_cosine_ops"],
            )
        ]


class Channel(models.Model):
    id                          = models.AutoField(primary_key=True)
    active                      = models.BooleanField(verbose_name='Active', default=True)    
    front_dev                   = models.BooleanField(verbose_name='Front Dev Active', default=True)
    front_stg                   = models.BooleanField(verbose_name='Front Stg Active', default=True)
    front_prd                   = models.BooleanField(verbose_name='Front Prd Active', default=True)
    country_code                = models.CharField(verbose_name='Country Code', null=True, blank=True)
    channel                     = models.CharField(verbose_name='Channel', blank=True, null=True)
    timezone                    = models.CharField(verbose_name='TimeZone', blank=True, null=True)
    language                    = models.CharField(verbose_name='Language', blank=True, null=True)
    subsidiary                  = models.CharField(verbose_name='Subsidiary', blank=True, null=True)
    created_on                  = models.DateTimeField(verbose_name='Create', auto_now_add=True)
    updated_on                  = models.DateTimeField(verbose_name='Update', auto_now=True)
    country_name                = models.CharField(verbose_name='Country Name', blank=True, null=True)
    locale                      = models.CharField(verbose_name='Locale', blank=True, null=True)
    welcome_msg                 = models.TextField(verbose_name='Welcome Message', blank=True, null=True)
    service                     = models.CharField(verbose_name='Service', blank=True, null=True)
    site_cd                     = models.CharField(max_length=10, null=False, blank=False, verbose_name="닷컴 코드", default="B2C")
    
    class Meta:        
        indexes = [
        	models.Index(fields=['active', 'country_code'], name="r3_c_fields_idx"),
        ]


class Channel_Appraisal(models.Model):
    id                          = models.AutoField(primary_key=True)    
    channel                     = models.CharField(verbose_name='Channel', blank=True, null=True)
    appraisal_selection         = models.JSONField(verbose_name='Appraisal Selection', blank=True, null=True, default=dict)    
    thumb_up                    = models.BooleanField(verbose_name='Thumb Up', default=True)
    created_on                  = models.DateTimeField(verbose_name='Create', auto_now_add=True)
    updated_on                  = models.DateTimeField(verbose_name='Update', auto_now=True)
    site_cd                     = models.CharField(max_length=10, null=False, blank=False, verbose_name="닷컴 코드", default="B2C")


class Complement_Code_Mapping(models.Model):
    id                  = models.AutoField(primary_key=True, serialize=False)
    active              = models.BooleanField(verbose_name='Active', default=True)
    update_tag          = models.CharField(verbose_name='Update Tag', blank=True, null=True)
    country_code        = models.CharField(verbose_name='Country Code', null=True, blank=True)
    embedding = VectorField(
        dimensions=1024,  # Changed from 1536 to 1024 for bge-m3
        help_text="BAAI/bge-m3",
        null=True,
        blank=True,
    )
    expression          = models.TextField(blank=True, null=True, verbose_name='Expression')
    field               = models.CharField(verbose_name='Field', max_length=1024)
    mapping_code        = models.CharField(verbose_name='Mapping Code', max_length=1024)
    type                = models.CharField(verbose_name='Type')
    category_lv1        = models.CharField(verbose_name='Category Lv. 1', blank=True, null=True)
    category_lv2        = models.CharField(verbose_name='Category Lv. 2', blank=True, null=True)
    category_lv3        = models.CharField(verbose_name='Category Lv. 3', blank=True, null=True)
    created_on          = models.DateTimeField(verbose_name='Create', auto_now_add=True)
    updated_on          = models.DateTimeField(verbose_name='Update', auto_now=True)
    site_cd             = models.CharField(max_length=10, null=False, blank=False, verbose_name="닷컴 코드", default="B2C")

    class Meta:
        indexes = [
        	models.Index(fields=['active', 'country_code', 'field', 'type', 'expression', 'category_lv1', 'category_lv2', 'category_lv3'], name="rv3_cm_fields_idx"),
            HnswIndex(
                name="rv3_cm_vector_idx",
                fields=["embedding"],
                m=16,
                ef_construction=64,
                opclasses=["vector_cosine_ops"],
            )
        ]


class Complement_Code_Mapping_Extended(models.Model):
    id                  = models.AutoField(primary_key=True, serialize=False)
    active              = models.BooleanField(verbose_name='Active', default=True)
    update_tag          = models.CharField(verbose_name='Update Tag', blank=True, null=True)
    country_code        = models.CharField(verbose_name='Country Code', null=True, blank=True)
    category_lv1        = models.CharField(verbose_name='Category Lv. 1', blank=True, null=True)
    category_lv2        = models.CharField(verbose_name='Category Lv. 2', blank=True, null=True)
    category_lv3        = models.CharField(verbose_name='Category Lv. 3', blank=True, null=True)
    mapping_code        = models.CharField(verbose_name='Mapping Code', max_length=1024)
    edge                = models.CharField(verbose_name='Edge')
    extended_info       = models.JSONField(verbose_name='Extended Info', blank=True, default=list, null=True)
    created_on          = models.DateTimeField(verbose_name='Create', auto_now_add=True)
    updated_on          = models.DateTimeField(verbose_name='Update', auto_now=True)
    site_cd             = models.CharField(max_length=10, null=False, blank=False, verbose_name="닷컴 코드", default="B2C")

    class Meta:
        indexes = [
        	models.Index(fields=['active', 'country_code', 'category_lv1', 'category_lv2',  'category_lv3',  'mapping_code', 'edge'], name="rv3_cme_fields_idx"),
        ]


# type: int 의 경우
# code_filter (True): 해당 Category 로 식별된 expression 에는 숫자가 있다면, 해당 숫자가 Matching 되어야 함
#   예시 ) expression : "갤럭시 S25" -> "25" l4_identifier : "25" => OK
#   예시 ) expression : "갤럭시 S26" -> "26" l4_identifier : "25" => X


# type: str 의 경우
# code_filter (True): 해당 Category 로 식별된 expression 에는 L4_identifier 가 포함되어야 함
#   예시 ) expression : "갤럭시 S25", l4_identifier : "S25" => OK
#   예시 ) expression : "갤럭시 S256", l4_identifier : "S25" => X
#   예시 ) expression : "갤럭시 S26", l4_identifier : "S25" => X
# product_filter (True): 해당 Category 로 식별된 expression 에 L4_identifier 가 포함된 경우, 해당 제품에 대해 답변할 제품에도 L4_identifier 가 포함되어야 함
#   예시 ) expression : "그랑데 건조기", l4_identifier : "그랑데" => 추천제품에도 high level spec 제품에도 제품명에 "그랑데"가 포함되어야 함.

class Complement_Code_Mapping_l4(models.Model):
    id                  = models.AutoField(primary_key=True, serialize=False)
    active              = models.BooleanField(verbose_name='Active', default=True)
    update_tag          = models.CharField(verbose_name='Update Tag', blank=True, null=True)
    country_code        = models.CharField(verbose_name='Country Code', null=True, blank=True)
    category_lv1        = models.CharField(verbose_name='Category Lv. 1', blank=True, null=True)
    category_lv2        = models.CharField(verbose_name='Category Lv. 2', blank=True, null=True)
    category_lv3        = models.CharField(verbose_name='Category Lv. 3', blank=True, null=True)
    type                = models.CharField(verbose_name='Type', max_length=3)
    condition           = models.CharField(verbose_name='Condition', max_length=10)
    l4_identifier          = models.CharField(verbose_name='L4 identifier', max_length=1024)
    l4_product_expression  = models.CharField(verbose_name='L4 Product Expression', max_length=1024, blank=True, null=True)
    code_filter            = models.BooleanField(verbose_name='Code Filter', default=True) # 표현에 해당 l4_identifier 가 있으면, 맵핑 코드내 l4_identifier 포함 필요, 없을 시 맵핑 실패로 간주
    product_filter         = models.BooleanField(verbose_name='Product Filter', default=True)  # 제품명에 대해 l4_identifier 로 필터
    meta                   = models.JSONField(verbose_name='Meta', blank=True, default=list, null=True)
    created_on          = models.DateTimeField(verbose_name='Create', auto_now_add=True)
    updated_on          = models.DateTimeField(verbose_name='Update', auto_now=True)
    site_cd             = models.CharField(max_length=10, null=False, blank=False, verbose_name="닷컴 코드", default="B2C")
    
    class Meta:
        indexes = [
        	models.Index(fields=['active', 'country_code', 'category_lv1', 'category_lv2',  'category_lv3',  'l4_identifier'], name="rv3_ccml4_fields_idx"),
        ]


class Complement_Product_Spec(models.Model):
    id                  = models.AutoField(primary_key=True, serialize=False)
    category_lv1        = models.CharField(verbose_name='Category Lv. 1', blank=True, null=True)
    category_lv2        = models.CharField(verbose_name='Category Lv. 2', blank=True, null=True)
    category_lv3        = models.CharField(verbose_name='Category Lv. 3', blank=True, null=True)
    goods_nm            = models.CharField(max_length=300, verbose_name= "상품 명", null=True, blank=True)
    mdl_code            = models.CharField(max_length=100, verbose_name= "모델 코드", null=True, blank=True)
    seq                 = models.IntegerField(verbose_name="순서", null=True, blank=True)
    disp_nm1            = models.CharField(max_length=200, verbose_name="노출 명1", null=True, blank=True)
    disp_nm2            = models.CharField(max_length=200, verbose_name="노출 명2", null=True, blank=True)    
    value               = models.CharField(max_length=1500, verbose_name= "Value 값", null=True, blank=True) 
    country_code        = models.CharField(verbose_name='Country Code', null=True, blank=True)      
    created_on          = models.DateTimeField(verbose_name='Create', auto_now_add=True)
    updated_on          = models.DateTimeField(verbose_name='Update', auto_now=True)
    site_cd             = models.CharField(max_length=10, null=False, blank=False, verbose_name="닷컴 코드", default="B2C")
    on_sale             = models.CharField(max_length=1, null=True, blank=True, verbose_name="판매 여부")

    class Meta:
        unique_together = ('goods_nm','mdl_code', 'seq', 'country_code', 'site_cd')
        indexes = [
        	models.Index(fields=['country_code', 'disp_nm1', 'disp_nm2', 'category_lv1', 'category_lv2', 'category_lv3', 'value'], name="r3_cpspec_word_idx"),
        	models.Index(fields=['category_lv1', 'category_lv2', 'category_lv3'], name="r3_cpspec_c_word_idx"),
            models.Index(fields=['mdl_code'], name="r3_cpspec_c_fields_idx"),
            models.Index(fields=['site_cd'], name="r3_cpspec_site_idx"),
            models.Index(fields=['mdl_code', 'country_code'], name="r3_cpspec_mdl_country_idx"),
            models.Index(fields=['site_cd', 'country_code'], name="r3_cpspec_site_country_idx"),
            models.Index(fields=['on_sale'], name="r3_cpspec_on_sale_idx"),
        ]


class Complement_Product_Spec_Manual(models.Model):
    id                  = models.AutoField(primary_key=True, serialize=False)
    category_lv1        = models.CharField(verbose_name='Category Lv. 1', blank=True, null=True)
    category_lv2        = models.CharField(verbose_name='Category Lv. 2', blank=True, null=True)
    category_lv3        = models.CharField(verbose_name='Category Lv. 3', blank=True, null=True)
    goods_nm            = models.CharField(max_length=300, verbose_name= "상품 명", null=True, blank=True)
    mdl_code            = models.CharField(max_length=100, verbose_name= "모델 코드", null=True, blank=True)
    seq                 = models.IntegerField(verbose_name="순서", null=True, blank=True)
    disp_nm1            = models.CharField(max_length=200, verbose_name="노출 명1", null=True, blank=True)
    disp_nm2            = models.CharField(max_length=200, verbose_name="노출 명2", null=True, blank=True)    
    value               = models.CharField(max_length=1500, verbose_name= "Value 값", null=True, blank=True) 
    country_code        = models.CharField(verbose_name='Country Code', null=True, blank=True)      
    created_on          = models.DateTimeField(verbose_name='Create', auto_now_add=True)
    updated_on          = models.DateTimeField(verbose_name='Update', auto_now=True)
    site_cd             = models.CharField(max_length=10, null=False, blank=False, verbose_name="닷컴 코드", default="B2C")
    on_sale             = models.CharField(max_length=1, null=True, blank=True, verbose_name="판매 여부")

    class Meta:
        unique_together = ('goods_nm','mdl_code', 'seq', 'country_code', 'site_cd')
        indexes = [
        	models.Index(fields=['country_code', 'disp_nm1', 'disp_nm2', 'category_lv1', 'category_lv2', 'category_lv3', 'value'], name="r3_cpspec_word_idx2"),
        	models.Index(fields=['category_lv1', 'category_lv2', 'category_lv3'], name="r3_cpspec_c_word_idx2"),
            models.Index(fields=['mdl_code'], name="r3_cpspec_c_fields_idx2"),
        ]


class Cpt_Base(models.Model):
    chunkid             = models.CharField(max_length=100, verbose_name= "chunkId", null=True, blank=True)
    title               = models.CharField(max_length=1000, verbose_name= "Title", null=True, blank=True)
    chunk               = models.JSONField(verbose_name='Chunk', null=True, blank=True, default=dict)    
    category_lv1        = models.CharField(verbose_name='Category Lv. 1', blank=True, null=True)
    category_lv2        = models.CharField(verbose_name='Category Lv. 2', blank=True, null=True)
    category_lv3        = models.CharField(verbose_name='Category Lv. 3', blank=True, null=True)
    mdl_code            = models.CharField(max_length=100, verbose_name= "모델 코드", null=True, blank=True)
    goods_nm            = models.CharField(max_length=300, verbose_name= "상품 명", null=True, blank=True)
    clean_chunk         = models.TextField(verbose_name='Clean Chunk', null=True, blank=True)
    sum_chunk           = models.TextField(verbose_name='Sum Chunk', null=True, blank=True)
    feature             = models.TextField(verbose_name= "Feature", null=True, blank=True)    
    update_tag          = models.CharField(verbose_name='Update Tag', blank=True, null=True)    
    created_on          = models.DateTimeField(verbose_name='Create', auto_now_add=True)
    updated_on          = models.DateTimeField(verbose_name='Update', auto_now=True)
    site_cd             = models.CharField(max_length=10, null=False, blank=False, verbose_name="닷컴 코드", default="B2C")

    class Meta:
        indexes = [
        	models.Index(fields=['chunkid', 'mdl_code', 'category_lv1', 'category_lv2', 'category_lv3', 'feature'], name="r3_cpt_base_idx"),
        ]


class Cpt_Desc(models.Model):
    category_lv1        = models.CharField(verbose_name='Category Lv. 1', blank=True, null=True)
    category_lv2        = models.CharField(verbose_name='Category Lv. 2', blank=True, null=True)
    category_lv3        = models.CharField(verbose_name='Category Lv. 3', blank=True, null=True)
    embedding           = VectorField(dimensions=1024, help_text="BAAI/bge-m3", null=True, blank=True)
    clean_chunk         = models.TextField(verbose_name='Clean Chunk', null=True, blank=True)
    chunkid             = models.CharField(max_length=100, verbose_name= "chunkId", null=True, blank=True)
    base_feature        = models.TextField(verbose_name= "Base Feature", null=True, blank=True)
    master_feature      = models.TextField(verbose_name= "Master Feature", null=True, blank=True)
    country_code        = models.CharField(verbose_name='Country Code', null=True, blank=True)
    expression          = models.CharField(verbose_name='Expression', null=True, blank=True)
    created_on          = models.DateTimeField(verbose_name='Create', auto_now_add=True)
    updated_on          = models.DateTimeField(verbose_name='Update', auto_now=True)
    site_cd             = models.CharField(max_length=10, null=False, blank=False, verbose_name="닷컴 코드", default="B2C")

    class Meta:
        indexes = [
        	models.Index(fields=['category_lv1', 'category_lv2', 'category_lv3', 'clean_chunk'], name="r3_cpt_desc_idx"),
            HnswIndex(name="cpt_desc_vector_idx", fields=["embedding"], m=16, ef_construction=64, opclasses=["vector_cosine_ops"])
        ]


class Cpt_Keyword_Kr(models.Model):
    goods_nm   = models.CharField(verbose_name='상품명', max_length=1000, null=True, blank=True)
    keyword    = models.CharField(verbose_name='키워드', max_length=1000, null=True, blank=True)
    created_on = models.DateTimeField(verbose_name='Create', auto_now_add=True)
    updated_on = models.DateTimeField(verbose_name='Update', auto_now=True)    
    site_cd    = models.CharField(max_length=10, null=False, blank=False, verbose_name="닷컴 코드", default="B2C")
    regr_id    = models.CharField(max_length=50, null=False, blank=False, verbose_name="등록자 아이디", default="admin")
    updr_id    = models.CharField(max_length=50, null=False, blank=False, verbose_name="수정자 아이디", default="admin")


class Cpt_Keyword_Gb(models.Model):
    display_name = models.CharField(verbose_name='디스플레이 이름', max_length=1000, null=True, blank=True)
    keyword      = models.CharField(verbose_name='키워드', max_length=1000, null=True, blank=True)
    created_on   = models.DateTimeField(verbose_name='Create', auto_now_add=True)
    updated_on   = models.DateTimeField(verbose_name='Update', auto_now=True)
    country_code = models.CharField(verbose_name='국가 코드', max_length=10, null=True, blank=True) 
    site_cd      = models.CharField(max_length=10, null=False, blank=False, verbose_name="닷컴 코드", default="B2C")
    regr_id      = models.CharField(max_length=50, null=False, blank=False, verbose_name="등록자 아이디", default="admin")
    updr_id      = models.CharField(max_length=50, null=False, blank=False, verbose_name="수정자 아이디", default="admin")


class Cpt_Manual(models.Model):
    business_unit           = models.CharField(verbose_name='Business Unit', max_length=1000, null=True, blank=True)
    product_category_lv1    = models.CharField(verbose_name='Product Category Lv1', max_length=1000, null=True, blank=True)
    product_category_lv2    = models.CharField(verbose_name='Product Category Lv2', max_length=1000, null=True, blank=True)
    product_category_lv3    = models.CharField(verbose_name='Product Category Lv3', max_length=1000, null=True, blank=True)
    model_group_code        = models.CharField(verbose_name='Model Group Code', max_length=1000, null=True, blank=True)
    model_name              = models.CharField(verbose_name='Model Name', max_length=1000, null=True, blank=True)
    product_model           = models.CharField(verbose_name='Product Name', max_length=1000, null=True, blank=True)
    mdl_code                = models.CharField(verbose_name='Mdl Code', max_length=1000, null=True, blank=True)
    goods_id                = models.CharField(verbose_name='상품 번호', max_length=1000, null=True, blank=True)
    goods_nm                = models.CharField(verbose_name='상품명', max_length=1000, null=True, blank=True)    
    disp_clsf_nm            = models.CharField(verbose_name='전시 분류 명', max_length=1000, null=True, blank=True)
    filter_nm               = models.CharField(verbose_name='필터 명', max_length=1000, null=True, blank=True)
    filter_item_nm          = models.CharField(verbose_name='필터 아이템 명', max_length=1000, null=True, blank=True)
    release_date            = models.DateField(verbose_name='출시일', null=True, blank=True)
    set_tp_cd               = models.CharField(verbose_name='세트 유형 코드', max_length=1000, null=True, blank=True)
    created_on              = models.DateTimeField(verbose_name='Create', auto_now_add=True)
    updated_on              = models.DateTimeField(verbose_name='Update', auto_now=True)
    site_cd                 = models.CharField(max_length=10, null=False, blank=False, verbose_name="닷컴 코드", default="B2C")

    class Meta:
        indexes = [
        	models.Index(fields=['product_category_lv1', 'product_category_lv2', 'product_category_lv3', 'goods_id', 'mdl_code', 'filter_nm', 'filter_item_nm'], name="r3_cpt_manual_idx"),]
        

class Cpt_Master(models.Model):
    chunkid             = models.CharField(max_length=1000, verbose_name= "chunkId", null=True, blank=True)
    mdl_code            = models.CharField(max_length=100, verbose_name= "모델 코드", null=True, blank=True)
    feature             = models.TextField(verbose_name= "Feature", null=True, blank=True)    
    embedding           = VectorField(
        dimensions=1024,  
        help_text="BAAI/bge-m3",
        null=True,
        blank=True,
    )
    update_tag          = models.CharField(verbose_name='Update Tag', blank=True, null=True)    
    created_on          = models.DateTimeField(verbose_name='Create', auto_now_add=True)
    updated_on          = models.DateTimeField(verbose_name='Update', auto_now=True)
    site_cd             = models.CharField(max_length=10, null=False, blank=False, verbose_name="닷컴 코드", default="B2C")

    class Meta:        
        indexes = [models.Index(fields=['chunkid', 'mdl_code', 'update_tag', 'feature'], name="r3_cpt_mst_idx"), 
                   HnswIndex(name="cpt_vector_idx", fields=["embedding"], m=16, ef_construction=64, opclasses=["vector_cosine_ops"])]


class Date_Match(models.Model):
    id                          = models.AutoField(primary_key=True)
    active                      = models.BooleanField(verbose_name='Active', default=True)
    update_tag                  = models.CharField(verbose_name='Update Tag', blank=True, null=True)
    country_code                = models.CharField(verbose_name='Country Code', null=True, blank=True)
    embedding                   = VectorField(dimensions=1024, help_text="BAAI/bge-m3", null=True, blank=True)
    expression                  = models.CharField(verbose_name='Expression', null=True, blank=True)
    mapping_code                = models.CharField(verbose_name='Mapping Code', null=True, blank=True)
    type                        = models.CharField(verbose_name='Type', null=True, blank=True)
    created_on                  = models.DateTimeField(verbose_name='Create', auto_now_add=True)
    updated_on                  = models.DateTimeField(verbose_name='Update', auto_now=True)
    site_cd             = models.CharField(max_length=10, null=False, blank=False, verbose_name="닷컴 코드", default="B2C")


class Disclaimer_Msg(models.Model):
    id                          = models.AutoField(primary_key=True)    
    message                     = models.TextField(verbose_name='Message', null=True, blank=True)
    channel                     = ArrayField(models.CharField(max_length=100), verbose_name= "Channel", null=True, blank=True)
    country_code                = models.CharField(verbose_name='Country Code', null=True, blank=True)
    intelligence                = ArrayField(models.CharField(max_length=100), verbose_name= "Intelligence", null=True, blank=True)
    sub_intelligence            = ArrayField(models.CharField(max_length=100), verbose_name= "Sub Intelligence", null=True, blank=True)    
    created_on                  = models.DateTimeField(verbose_name='Create', auto_now_add=True)
    updated_on                  = models.DateTimeField(verbose_name='Update', auto_now=True)
    site_cd                     = models.CharField(max_length=10, null=False, blank=False, verbose_name="닷컴 코드", default="B2C")


class Exception_Msg(models.Model):
    id                          = models.AutoField(primary_key=True)    
    message                     = models.TextField(verbose_name='Message', null=True, blank=True)
    channel                     = ArrayField(models.CharField(max_length=100), verbose_name= "Channel", null=True, blank=True)
    country_code                = models.CharField(verbose_name='Country Code', null=True, blank=True)
    intelligence                = ArrayField(models.CharField(max_length=100), verbose_name= "Intelligence", null=True, blank=True)
    sub_intelligence            = ArrayField(models.CharField(max_length=100), verbose_name= "Sub Intelligence", null=True, blank=True)
    type                        = models.CharField(verbose_name='Exception Type', max_length=100, null=True, blank=True)    
    created_on                  = models.DateTimeField(verbose_name='Create', auto_now_add=True)
    updated_on                  = models.DateTimeField(verbose_name='Update', auto_now=True)
    site_cd                     = models.CharField(max_length=10, null=False, blank=False, verbose_name="닷컴 코드", default="B2C")


class Event_Map(models.Model):
    event_no                = models.IntegerField(verbose_name= "이벤트 번호", null=False, blank=False)
    event_ctg               = models.TextField(verbose_name= "이벤트 카테고리", null=True, blank=True)
    event_embedding         = VectorField(dimensions=1024, help_text="BAAI/bge-m3", null=True, blank=True)
    event_nm                = models.TextField(verbose_name= "이벤트 명", null=True, blank=True)
    subcopy                 = models.TextField(verbose_name= "서브 카피", null=True, blank=True)
    event_strt_dtm          = models.DateTimeField(verbose_name= "이벤트 시작 일시", null=True, blank=True)
    event_end_dtm           = models.DateTimeField(verbose_name= "이벤트 종료 일시", null=True, blank=True)
    event_url               = models.TextField(verbose_name= "이벤트 URL", null=True, blank=True)
    event_desc              = models.TextField(verbose_name= "이벤트 상세 설명", null=True, blank=True)
    event_caution           = models.TextField(verbose_name= "이벤트 유의사항", null=True, blank=True)
    benefit_embedding       = VectorField(dimensions=1024, help_text="BAAI/bge-m3", null=True, blank=True)
    benefit_nm              = models.TextField(verbose_name= "혜택 명", null=True, blank=True)
    goods_id                = ArrayField(models.CharField(max_length=15, verbose_name= "상품 아이디", null=True, blank=True))
    mdl_code                = ArrayField(models.CharField(max_length=20, verbose_name= "모델 코드", null=True, blank=True))
    benefit_strt_dtm        = models.DateTimeField(verbose_name= "혜택 시작 일시", null=True, blank=True)
    benefit_end_dtm         = models.DateTimeField(verbose_name= "혜택 종료 일시", null=True, blank=True)
    benefit_desc            = models.TextField(verbose_name= "혜택 상세 설명", null=True, blank=True)
    benefit_caution         = models.TextField(verbose_name= "혜택 유의사항", null=True, blank=True)
    all_yn                  = models.CharField(max_length=1, verbose_name= "전체 여부", null=True, blank=True)
    site_cd                 = models.CharField(max_length=10, null=False, blank=False, verbose_name="닷컴 코드", default="B2C")


class Front_Recommend(models.Model):
    active              = models.BooleanField(verbose_name='Active', default=True)
    front_disp_clsf_nm  = models.CharField(verbose_name="프론트엔드 입력 전시 분류 명", max_length=100, null=True, blank=True)
    front_filter_nm     = models.CharField(verbose_name='프론트엔드 필터 명', max_length=1000, null=True, blank=True)
    front_option        = models.CharField(verbose_name="프론트엔드 선택지", max_length=100, null=True, blank=True)
    disp_clsf_nm        = models.CharField(verbose_name="전시 분류 명", max_length=100, null=True, blank=True)
    logic               = models.CharField(verbose_name='적용 로직', blank=True, null=True)
    filter_nm           = models.CharField(verbose_name='필터 명', max_length=1000, null=True, blank=True)
    filter_item_nm      = models.CharField(verbose_name='필터 아이템 명', max_length=1000, null=True, blank=True)
    created_on          = models.DateTimeField(verbose_name='Create', auto_now_add=True)
    updated_on          = models.DateTimeField(verbose_name='Update', auto_now=True)
    site_cd             = models.CharField(max_length=10, null=False, blank=False, verbose_name="닷컴 코드", default="B2C")


class Google_Map_Info(models.Model):
    id                          = models.AutoField(primary_key=True)
    country_code                = models.CharField(verbose_name='Country Code', null=True, blank=True)
    keyword                     = models.CharField(verbose_name='Keyword', null=True, blank=True)
    pos                         = models.CharField(verbose_name='Pos', null=True, blank=True)    
    created_on                  = models.DateTimeField(verbose_name='Create', auto_now_add=True)
    updated_on                  = models.DateTimeField(verbose_name='Update', auto_now=True)
    site_cd                     = models.CharField(max_length=10, null=False, blank=False, verbose_name="닷컴 코드", default="B2C")
    google_country_code         = models.CharField(verbose_name='Google Country Code', null=True, blank=True)    
    

    class Meta:
        unique_together = ('keyword', 'pos', 'country_code')


## 20250527
class Intelligence_V2(models.Model):    
    intelligence        = models.CharField(verbose_name='Intelligence', null=True, blank=True)
    sub_intelligence    = models.CharField(verbose_name='Sub Intelligence', null=True, blank=True)
    intelligence_desc   = models.CharField(verbose_name='Intelligence Desc', null=True, blank=True)
    intelligence_meta   = models.JSONField(verbose_name='Intelligence Meta', null=True, blank=True, default = dict)
    channel             = ArrayField(models.CharField(max_length=100), verbose_name= "Channel", null=True, blank=True)
    product_card        = models.BooleanField(verbose_name='Product Card', default=False)
    related_query       = models.BooleanField(verbose_name='Related Query', default=False)
    hyperlink           = models.BooleanField(verbose_name='Hyperlink', default=False)
    media               = models.BooleanField(verbose_name='Media', default=False)
    map                 = models.BooleanField(verbose_name='Map', default=False)
    base                = models.BooleanField(verbose_name='Base', default=False)
    created_on          = models.DateTimeField(verbose_name='Create', auto_now_add=True)
    updated_on          = models.DateTimeField(verbose_name='Update', auto_now=True)
    site_cd             = models.CharField(max_length=10, null=False, blank=False, verbose_name="닷컴 코드", default="B2C")


class Managed_Response_Index(models.Model):
    id                  = models.AutoField(primary_key=True)
    active              = models.BooleanField(verbose_name='Active', default=True)
    update_tag          = models.CharField(verbose_name='Update Tag', blank=True, null=True)
    country_code        = models.CharField(verbose_name='Country Code', null=True, blank=True)
    category_lv1        = models.CharField(verbose_name='Category Lv1', blank=True, null=True)
    category_lv2        = models.CharField(verbose_name='Category Lv2', blank=True, null=True)
    category_lv3        = models.CharField(verbose_name='Category Lv3', blank=True, null=True)
    product             = models.CharField(verbose_name='Product', blank=True, null=True)
    function            = models.CharField(verbose_name='Function', blank=True, null=True)
    date                = models.CharField(verbose_name='Date', blank=True, null=True)
    managed_response    = models.TextField(verbose_name='Managed Response', blank=True, null=True)
    managed_response_meta   = models.JSONField(verbose_name='Measure Dimension Meta', blank=True, default=dict, null=True)
    managed_only        = models.BooleanField(verbose_name='Managed Only', default=False)
    price               = models.BooleanField(verbose_name='Price', default=False)
    reference           = models.BooleanField(verbose_name='Reference', default=False)
    created_on          = models.DateTimeField(verbose_name='Create', auto_now_add=True)
    updated_on          = models.DateTimeField(verbose_name='Update', auto_now=True)
    site_cd             = models.CharField(max_length=10, null=False, blank=False, verbose_name="닷컴 코드", default="B2C")

    class Meta:
        indexes = [
        	models.Index(fields=['active', 'country_code', 'category_lv1', 'category_lv2', 'category_lv3', 'product', 'function'], name="rv3_mri_fields_idx"),
        ]


class Managed_Word(models.Model):
    id                  = models.AutoField(primary_key=True)
    active              = models.BooleanField(verbose_name='Active', default=True)
    update_tag          = models.CharField(verbose_name='Update Tag', blank=True, null=True)
    module              = models.CharField(verbose_name='Module', null=True, blank=True)
    type                = models.CharField(verbose_name='Type', null=True, blank=True)
    word                = models.CharField(verbose_name='Word', null=True, blank=True)
    replace_word        = models.CharField(verbose_name='Replace Word', null=True, blank=True)
    processing          = models.CharField(verbose_name='Processing', null=True, blank=True)
    channel             = ArrayField(models.CharField(max_length=100), verbose_name= "Channel", null=True, blank=True)
    created_on          = models.DateTimeField(verbose_name='Create', auto_now_add=True)
    updated_on          = models.DateTimeField(verbose_name='Update', auto_now=True)
    site_cd             = models.CharField(max_length=10, null=False, blank=False, verbose_name="닷컴 코드", default="B2C")

    class Meta:
        indexes = [
        	models.Index(fields=['active', 'module', 'type', 'word'], name="r3_mw_word_idx"),
        ]


class Ner_Expression_Field(models.Model):
    id                  = models.AutoField(primary_key=True)
    field_name          = models.CharField(verbose_name='Field Name', null=True, blank=True)
    field_meta          = models.JSONField(verbose_name='Field Meta', null=True, blank=True, default = dict)
    field_rag_type      = models.CharField(verbose_name='Field Name', null=True, blank=True)
    field_standard_name = models.CharField(verbose_name='Field Name', null=True, blank=True)
    field_description = models.CharField(verbose_name='Field Description', null=True, blank=True)
    country_code        = models.CharField(verbose_name='Country Code', null=True, blank=True)
    active              = models.BooleanField(verbose_name='Active', default=True)
    category            = models.CharField(verbose_name='Category', null=True, blank=True)
    channel             = models.CharField(verbose_name='Channel', null=True, blank=True)
    site_cd             = models.CharField(max_length=10, null=False, blank=False, verbose_name="닷컴 코드", default="B2C")    

    class Meta:
        indexes = [
        	models.Index(fields=['active', 'country_code', 'field_name'], name="r3_ner_expression_field_idx"),
        ]


class NER_Ref(models.Model):
    id                  = models.AutoField(primary_key=True, serialize=False)
    embedding           = VectorField(
        dimensions=1024,  # Changed from 1536 to 1024 for bge-m3
        help_text="BAAI/bge-m3",
        null=True,
        blank=True,
    )
    query               = models.TextField(verbose_name='Query', blank=True, null=True)
    language            = models.CharField(verbose_name='Language', choices=LANGUAGE, max_length=2, blank=True, null=True)
    intelligence        = models.CharField(verbose_name='Intelligence', blank=True, null=True)
    virtual_view        = models.CharField(verbose_name='Virtual View', blank=True, null=True)
    measure_dimension   = models.JSONField(verbose_name='Measure Dimension', blank=True, default=dict, null=True)
    structured          = models.BooleanField(verbose_name='Structured', null=True, blank=True)
    unstructured        = models.BooleanField(verbose_name='UnStructured', null=True, blank=True)
    edit_status         = models.CharField(verbose_name='Edit Status', blank=True, null=True)
    edit_history        = models.JSONField(verbose_name='Edit History', null=True, blank=True, default=dict)
    confirmed           = models.BooleanField(verbose_name='Confirmed',  null=True, blank=True, default=False)
    confirmed_by        = models.CharField(verbose_name='Confirmed By', blank=True, null=True)
    created_on          = models.DateTimeField(verbose_name='Created On', auto_now_add=True )
    updated_on          = models.DateTimeField(verbose_name='Updated On', auto_now=True)
    country_code        = models.CharField(verbose_name='Country Code', null=True, blank=True)
    active              = models.BooleanField(verbose_name='Active', default=True)
    update_tag          = models.CharField(verbose_name='Update Tag', blank=True, null=True)
    site_cd             = models.CharField(max_length=10, null=False, blank=False, verbose_name="닷컴 코드", default="B2C")
    
    class Meta:        
        indexes = [
        	models.Index(fields=['active', 'country_code'], name="ner_country_code_idx"),
            HnswIndex(
                name="ner_vector_idx2",
                fields=["embedding"],
                m=16,
                ef_construction=64,
                opclasses=["vector_cosine_ops"],
            )
        ]


class Ner_Expression_Field_Temp(models.Model):
    id                  = models.AutoField(primary_key=True)
    field_name          = models.CharField(verbose_name='Field Name', null=True, blank=True)
    field_meta          = models.JSONField(verbose_name='Field Meta', null=True, blank=True, default = dict)
    field_rag_type      = models.CharField(verbose_name='Field Name', null=True, blank=True)
    field_standard_name = models.CharField(verbose_name='Field Name', null=True, blank=True)
    field_description = models.CharField(verbose_name='Field Description', null=True, blank=True)
    country_code        = models.CharField(verbose_name='Country Code', null=True, blank=True)
    active              = models.BooleanField(verbose_name='Active', default=True)
    category            = models.CharField(verbose_name='Category', null=True, blank=True)
    channel             = models.CharField(verbose_name='Channel', null=True, blank=True)
    site_cd             = models.CharField(max_length=10, null=False, blank=False, verbose_name="닷컴 코드", default="B2C")    

    class Meta:
        indexes = [
        	models.Index(fields=['active', 'country_code', 'field_name'], name="r3_ner_expression_field2_idx"),
        ]


class NER_Ref_Temp(models.Model):
    id                  = models.AutoField(primary_key=True, serialize=False)
    embedding           = VectorField(
        dimensions=1024,  # Changed from 1536 to 1024 for bge-m3
        help_text="BAAI/bge-m3",
        null=True,
        blank=True,
    )
    query               = models.TextField(verbose_name='Query', blank=True, null=True)
    language            = models.CharField(verbose_name='Language', choices=LANGUAGE, max_length=2, blank=True, null=True)
    intelligence        = models.CharField(verbose_name='Intelligence', blank=True, null=True)
    virtual_view        = models.CharField(verbose_name='Virtual View', blank=True, null=True)
    measure_dimension   = models.JSONField(verbose_name='Measure Dimension', blank=True, default=dict, null=True)
    structured          = models.BooleanField(verbose_name='Structured', null=True, blank=True)
    unstructured        = models.BooleanField(verbose_name='UnStructured', null=True, blank=True)
    edit_status         = models.CharField(verbose_name='Edit Status', blank=True, null=True)
    edit_history        = models.JSONField(verbose_name='Edit History', null=True, blank=True, default=dict)
    confirmed           = models.BooleanField(verbose_name='Confirmed',  null=True, blank=True, default=False)
    confirmed_by        = models.CharField(verbose_name='Confirmed By', blank=True, null=True)
    created_on          = models.DateTimeField(verbose_name='Created On', auto_now_add=True )
    updated_on          = models.DateTimeField(verbose_name='Updated On', auto_now=True)
    country_code        = models.CharField(verbose_name='Country Code', null=True, blank=True)
    active              = models.BooleanField(verbose_name='Active', default=True)
    update_tag          = models.CharField(verbose_name='Update Tag', blank=True, null=True)
    site_cd             = models.CharField(max_length=10, null=False, blank=False, verbose_name="닷컴 코드", default="B2C")
    
    class Meta:        
        indexes = [
        	models.Index(fields=['active', 'country_code'], name="ner_country_code_idx2"),
            HnswIndex(
                name="ner_vector_idx3",
                fields=["embedding"],
                m=16,
                ef_construction=64,
                opclasses=["vector_cosine_ops"],
            )
        ]


class Pipeline_Version_KR(models.Model):
    system_name              = models.TextField(verbose_name="시스템 명", null=True, blank=True)
    seed_cont_last_version   = models.TextField(verbose_name="시드 컨텐츠 마지막 버전", null=True, blank=True)
    seed_cont_last_updated   = models.DateTimeField(verbose_name="시드 컨텐츠 마지막 업데이트", auto_now=True)
    local_last_version       = models.TextField(verbose_name="로컬 마지막 버전", null=True, blank=True)
    local_last_updated       = models.DateTimeField(verbose_name="로컬 마지막 업데이트", auto_now=True)
    integration_last_version = models.TextField(verbose_name="통합 마지막 버전", null=True, blank=True)
    integration_last_updated = models.DateTimeField(verbose_name="통합 마지막 업데이트", auto_now=True)
    search_cont_last_version = models.TextField(verbose_name="검색 컨텐츠 마지막 버전", null=True, blank=True)
    search_cont_last_updated = models.DateTimeField(verbose_name="검색 컨텐츠 마지막 업데이트", auto_now=True)
    seed_cont_name           = models.TextField(verbose_name="시드 컨텐츠 이름", null=True, blank=True)


class Pipeline_Version_Log_KR(models.Model):
    system_name           = models.TextField(verbose_name="시스템 명", null=True, blank=True)
    work_type             = models.TextField(verbose_name="작업 유형", null=True, blank=True)
    version               = models.TextField(verbose_name="버전", null=True, blank=True)
    debug_count           = models.IntegerField(verbose_name="디버그 카운트")
    updated               = models.DateTimeField(verbose_name="업데이트", auto_now=True)
    error_message         = models.TextField(verbose_name="오류 메시지", null=True, blank=True)


class Pipeline_Version_UK(models.Model):
    system_name              = models.TextField(verbose_name="시스템 명", null=True, blank=True)
    seed_cont_last_version   = models.TextField(verbose_name="시드 컨텐츠 마지막 버전", null=True, blank=True)
    seed_cont_last_updated   = models.DateTimeField(verbose_name="시드 컨텐츠 마지막 업데이트", auto_now=True)
    local_last_version       = models.TextField(verbose_name="로컬 마지막 버전", null=True, blank=True)
    local_last_updated       = models.DateTimeField(verbose_name="로컬 마지막 업데이트", auto_now=True)
    integration_last_version = models.TextField(verbose_name="통합 마지막 버전", null=True, blank=True)
    integration_last_updated = models.DateTimeField(verbose_name="통합 마지막 업데이트", auto_now=True)
    search_cont_last_version = models.TextField(verbose_name="검색 컨텐츠 마지막 버전", null=True, blank=True)
    search_cont_last_updated = models.DateTimeField(verbose_name="검색 컨텐츠 마지막 업데이트", auto_now=True)
    seed_cont_name           = models.TextField(verbose_name="시드 컨텐츠 이름", null=True, blank=True)


class Pipeline_Version_Log_UK(models.Model):
    system_name           = models.TextField(verbose_name="시스템 명", null=True, blank=True)
    work_type             = models.TextField(verbose_name="작업 유형", null=True, blank=True)
    version               = models.TextField(verbose_name="버전", null=True, blank=True)
    debug_count           = models.IntegerField(verbose_name="디버그 카운트")
    updated               = models.DateTimeField(verbose_name="업데이트", auto_now=True)
    error_message         = models.TextField(verbose_name="오류 메시지", null=True, blank=True)


class Predefined_Answer(models.Model):
    id                  = models.AutoField(primary_key=True)
    embedding           = VectorField(
        dimensions=1024,  # Changed from 1536 to 1024 for bge-m3
        help_text="BAAI/bge-m3",
        null=True,
        blank=True,
    )
    country_code        = models.CharField(verbose_name='Country Code', null=True, blank=True)
    category            = models.CharField(verbose_name='Category')
    query               = models.CharField(verbose_name='Query')
    channel             = models.CharField(verbose_name='Channel', null=True, blank=True)
    predefined_answer   = models.TextField(verbose_name='Predefined Answer', null=True, blank=True)
    created_on          = models.DateTimeField(verbose_name='Create', auto_now_add=True)
    updated_on          = models.DateTimeField(verbose_name='Update', auto_now=True)
    reraking_queries    = models.JSONField(verbose_name='Reranking queries', null=True, blank=True, default=list)
    site_cd             = models.CharField(max_length=10, null=False, blank=False, verbose_name="닷컴 코드", default="B2C")

    class Meta:
        indexes = [
        	models.Index(fields=['country_code', 'channel'], name="r3_pa_country_code_idx"),
            HnswIndex(
                name="r3_pa_vector_idx",
                fields=["embedding"],
                m=16,
                ef_construction=64,
                opclasses=["vector_cosine_ops"],
            )
        ] 

class Predefined_RAG(models.Model):
    id                  = models.AutoField(primary_key=True)
    active              = models.BooleanField(verbose_name='Active', default=True)
    country_code        = models.CharField(verbose_name='Country Code', null=True, blank=True)
    site_cd             = models.CharField(max_length=10, null=False, blank=False, verbose_name="닷컴 코드", default="B2C")
    channel_filter      = ArrayField(models.CharField(max_length=100), verbose_name= "channel_filter", null=True, blank=True)
    matching_rule       = models.JSONField(verbose_name='Matching Rule', null=True, blank=True, default=list)
    contents            = models.TextField(verbose_name='Predefined RAG', null=True, blank=True)
    description         = models.CharField(verbose_name='Description', null=True, blank=True)
    created_on          = models.DateTimeField(verbose_name='Create', auto_now_add=True)
    updated_on          = models.DateTimeField(verbose_name='Update', auto_now=True)

    class Meta:
        indexes = [
        	models.Index(fields=['country_code', 'channel_filter', 'site_cd'], name="r3_pr_ccs_idx"),
        ]


class Prompt_Template(models.Model):
    id                          = models.AutoField(primary_key=True)
    active                      = models.BooleanField(verbose_name='Active', default=True)
    country_code                = models.CharField(verbose_name='Country Code', null=True, blank=True)
    channel_filter              = ArrayField(models.CharField(max_length=100), verbose_name= "channel_filter", null=True, blank=True)
    response_type               = models.CharField(verbose_name='Response Type', null=True, blank=True)
    category_lv1                = models.CharField(verbose_name='Category Lv1', null=True, blank=True)
    category_lv2                = models.CharField(verbose_name='Category Lv2', null=True, blank=True)
    prompt                      = models.TextField(verbose_name='Prompt', null=True, blank=True)
    tag                         = models.CharField(verbose_name='tag', null=True, blank=True)
    description                 = models.CharField(verbose_name='Description', null=True, blank=True)
    created_on                  = models.DateTimeField(verbose_name='Created On', auto_now_add=True)
    updated_on                  = models.DateTimeField(verbose_name='Updated On', auto_now=True)
    site_cd                     = models.CharField(max_length=10, null=False, blank=False, verbose_name="닷컴 코드", default="B2C")

    class Meta:
        indexes = [
        	models.Index(fields=['active', 'country_code', 'response_type', 'category_lv1', 'category_lv2'], name="r3_pt_fields_idx"),
        ]


class Related_Query(models.Model):
    country_code     = models.CharField(verbose_name='Country Code', null=True, blank=True)
    intelligence     = models.CharField(verbose_name='Intelligence', null=True, blank=True)
    sub_intelligence = models.CharField(verbose_name='Sub Intelligence', null=True, blank=True)
    display_order    = models.IntegerField(verbose_name='Display Order', null=True, blank=True)
    query            = models.CharField(verbose_name='Query', null=True, blank=True)
    active           = models.BooleanField(verbose_name='Active', default=True)
    site_cd          = models.CharField(max_length=10, null=False, blank=False, verbose_name="닷컴 코드", default="B2C")


class Representative_Query(models.Model):    
    batch_group         = models.CharField(verbose_name='Batch Group', null=True, blank=True)
    display_order       = models.IntegerField(verbose_name='Display Order', null=True, blank=True)
    country_code        = models.CharField(verbose_name='Country Code', null=True, blank=True)
    channel             = models.CharField(verbose_name='Channel', null=True, blank=True)
    query               = models.CharField(verbose_name='Query', null=True, blank=True)
    active              = models.BooleanField(verbose_name='Active', default=True)
    created_on          = models.DateTimeField(verbose_name='Create', auto_now_add=True)
    updated_on          = models.DateTimeField(verbose_name='Update', auto_now=True)    
    site_cd             = models.CharField(max_length=10, null=False, blank=False, verbose_name="닷컴 코드", default="B2C")


class Spec_Table_Meta(models.Model):
    id                          = models.AutoField(primary_key=True)    
    country_code                = models.CharField(verbose_name='Country Code', null=True, blank=True)    
    category_lv1                = models.CharField(verbose_name='Category Lv1', null=True, blank=True)
    category_lv2                = models.CharField(verbose_name='Category Lv2', null=True, blank=True)
    category_lv3                = models.CharField(verbose_name='Category Lv3', null=True, blank=True)
    model_code                  = models.CharField(verbose_name='Model Code', null=True, blank=True)
    spec_lv1                    = models.CharField(verbose_name='Spec Lv1', null=True, blank=True)
    spec_lv2                    = models.CharField(verbose_name='Spec Lv2', null=True, blank=True)
    spec_value                  = models.CharField(verbose_name='Spec Value', null=True, blank=True)
    created_on                  = models.DateTimeField(verbose_name='Created On', auto_now_add=True)
    updated_on                  = models.DateTimeField(verbose_name='Updated On', auto_now=True)
    site_cd                     = models.CharField(max_length=10, null=False, blank=False, verbose_name="닷컴 코드", default="B2C")

    class Meta:        
        indexes = [
        	models.Index(fields=['country_code', 'category_lv1', 'category_lv2', 'category_lv3', 'spec_lv1', 'spec_lv2', 'model_code'], name="r3_stmeta_fields_idx"),
        ]


class Structured_Code_Mapping(models.Model):
    id                  = models.AutoField(primary_key=True, serialize=False)
    country_code        = models.CharField(verbose_name='Country Code', null=True, blank=True)
    expression_embedding = VectorField(
        dimensions=1024,  # Changed from 1536 to 1024 for bge-m3
        help_text="BAAI/bge-m3",
        null=True,
        blank=True,
    )
    expression          = models.TextField(blank=True, null=True, verbose_name='Expression')    
    field               = models.CharField(verbose_name='Field', max_length=1024)
    mapping_code        = models.CharField(verbose_name='Mapping Code', max_length=1024)
    expression_to_code  = models.BooleanField(verbose_name='Expression to Code', null=True, blank=True)
    structured          = models.BooleanField(verbose_name='Structured', null=True, blank=True)
    active              = models.BooleanField(verbose_name='Active', default=True)    
    created_on          = models.DateTimeField(verbose_name='Create', auto_now_add=True)
    updated_on          = models.DateTimeField(verbose_name='Update', auto_now=True)
    site_cd             = models.CharField(max_length=10, null=False, blank=False, verbose_name="닷컴 코드", default="B2C")

    class Meta:
        indexes = [
        	models.Index(fields=['field', 'expression', 'country_code', 'structured', 'site_cd'], name="r3_cm_fields_idx"),
            HnswIndex(
                name="r3_cm_vector_idx",
                fields=["expression_embedding"],
                m=16,
                ef_construction=64,
                opclasses=["vector_cosine_ops"],
            )
        ]


class Uk_Cpt_Manual(models.Model):    
    model_code           = models.CharField(verbose_name='모델코드', max_length=1000, null=False, blank=False)
    display_name         = models.CharField(verbose_name='Display Name', max_length=1000, null=True, blank=True)
    category_lv1         = models.CharField(verbose_name='Category Lv1', max_length=1000, null=True, blank=True)
    category_lv2         = models.CharField(verbose_name='Category Lv2', max_length=1000, null=True, blank=True)
    category_lv3         = models.CharField(verbose_name='Category Lv3', max_length=1000, null=True, blank=True)
    filter_nm            = models.CharField(verbose_name='Filter Name', max_length=1000, null=True, blank=True)
    filter_item_nm       = models.CharField(verbose_name='Filter Item Name', max_length=1000, null=True, blank=True)
    created_on           = models.DateTimeField(verbose_name='Create', auto_now_add=True)
    updated_on           = models.DateTimeField(verbose_name='Update', auto_now=True)
    launch_date          = models.DateField(verbose_name='Launch Date', null=True, blank=True)
    country_code         = models.CharField(verbose_name='국가코드', max_length=2, null=False, blank=False, default='GB')
    site_cd              = models.CharField(max_length=10, null=False, blank=False, verbose_name="닷컴 코드", default="B2C")

    class Meta:
        indexes = [
        	models.Index(fields=['model_code', 'category_lv1', 'category_lv2', 'category_lv3', 'filter_nm', 'filter_item_nm'], name="r3_uk_cpt_manual_idx"),]
        

class uk_product_division_map(models.Model):
    model_code    = models.CharField(max_length=300, verbose_name= "모델 코드", null=False, blank=False)
    category_lv1  = models.CharField(max_length=300, verbose_name= "카테고리 레벨1", null=True, blank=True)
    category_lv2  = models.CharField(max_length=300, verbose_name= "카테고리 레벨2", null=True, blank=True)
    category_lv3  = models.CharField(max_length=300, verbose_name= "카테고리 레벨3", null=True, blank=True)
    display_name  = models.CharField(max_length=300, verbose_name= "디스플레이 명", null=True, blank=True)
    division      = models.CharField(max_length=300, verbose_name= "디비전", null=True, blank=True)    
    created_on    = models.DateTimeField(verbose_name='Create', auto_now_add=True)
    updated_on    = models.DateTimeField(verbose_name='Update', auto_now=True)
    country_code  = models.CharField(max_length=10, null=False, blank=False, verbose_name="Country Code", default='GB')
    site_cd       = models.CharField(max_length=10, null=False, blank=False, verbose_name="닷컴 코드", default="B2C")

    class Meta:
        unique_together = ('model_code', 'country_code', 'site_cd')

        
class Unstructured_Index(models.Model):
    id                  = models.AutoField(primary_key=True)
    country_code        = models.CharField(verbose_name='Country Code', null=True, blank=True)
    op_type             = models.CharField(verbose_name='OP Type')
    name                = models.CharField(verbose_name='Index Name')
    ai_search_index     = models.CharField(verbose_name='AI Search Index', null=True, blank=True)
    created_on          = models.DateTimeField(verbose_name='Create', auto_now_add=True)
    updated_on          = models.DateTimeField(verbose_name='Update', auto_now=True)
    site_cd             = models.CharField(max_length=10, null=False, blank=False, verbose_name="닷컴 코드", default="B2C")
    
    class Meta:
        indexes = [
        	models.Index(fields=['country_code', 'op_type', 'name'], name="r3_rv_ui_fields_idx"),
        ]


class View_Config(models.Model):
    id                  = models.AutoField(primary_key=True)
    country_code        = models.CharField(verbose_name='Country Code', null=True, blank=True)
    virtual_view        = models.CharField(verbose_name='Virtual View', null=True, blank=True)
    config_type         = models.CharField(verbose_name='Config Type', null=True, blank=True)
    data_source         = models.CharField(verbose_name='Data Source',  null=True, blank=True)
    config              = models.JSONField(verbose_name='Config', null=True, blank=True, default = dict)
    created_on          = models.DateTimeField(verbose_name='Create', auto_now_add=True)
    updated_on          = models.DateTimeField(verbose_name='Update', auto_now=True)
    site_cd             = models.CharField(max_length=10, null=False, blank=False, verbose_name="닷컴 코드", default="B2C")

    class Meta:
        indexes = [
        	models.Index(fields=['country_code'], name="r3_vc_country_code_idx"),
        ]


class Virtual_View(models.Model):
    id                  = models.AutoField(primary_key=True)
    country_code        = models.CharField(verbose_name='Country Code', null=True, blank=True)
    intelligence        = models.CharField(verbose_name='Intelligence')
    virtual_view        = models.CharField(verbose_name='Virtual View', null=True, blank=True)
    virtual_view_type   = models.CharField(verbose_name='Virtaul View Type')
    virtual_view_description   = models.CharField(verbose_name='Virtaul View Description')
    created_on          = models.DateTimeField(verbose_name='Create', auto_now_add=True)
    updated_on          = models.DateTimeField(verbose_name='Update', auto_now=True)
    site_cd             = models.CharField(max_length=10, null=False, blank=False, verbose_name="닷컴 코드", default="B2C")
    
    class Meta:        
        indexes = [
        	models.Index(fields=['country_code'], name="r3_vv_country_code_idx"),
        ]


class Virtual_View_Field(models.Model):
    id                  = models.AutoField(primary_key=True)
    country_code        = models.CharField(verbose_name='Country Code', null=True, blank=True)
    virtual_view_id     = models.ForeignKey(Virtual_View, verbose_name='Virtual_View', on_delete=models.PROTECT)
    order               = models.IntegerField(verbose_name='Order', default=0)
    field_name          = models.CharField(verbose_name='Field Name')
    field_type          = models.CharField(verbose_name='Field Type')
    field_description   = models.CharField(verbose_name='Field Description')
    created_on          = models.DateTimeField(verbose_name='Create', auto_now_add=True)
    updated_on          = models.DateTimeField(verbose_name='Update', auto_now=True)
    site_cd             = models.CharField(max_length=10, null=False, blank=False, verbose_name="닷컴 코드", default="B2C")


class Virtual_View_Field_Meta(models.Model):
    id                  = models.AutoField(primary_key=True)
    country_code        = models.CharField(verbose_name='Country Code', null=True, blank=True)
    virtual_view        = models.CharField(verbose_name='virtual_view')
    virtual_view_field  = models.CharField(verbose_name='virtual_view_Field')
    embedding           = VectorField(
        dimensions=1024,  # Changed from 1536 to 1024 for bge-m3
        help_text="BAAI/bge-m3",
        null=True,
        blank=True,
    )
    query               = models.CharField(verbose_name='Query', null=True, blank=True)
    field_processing_meta = models.JSONField(verbose_name='Field Processing Meta', null=True, blank=True, default = dict)
    created_on          = models.DateTimeField(verbose_name='Create', auto_now_add=True)
    updated_on          = models.DateTimeField(verbose_name='Update', auto_now=True)
    site_cd             = models.CharField(max_length=10, null=False, blank=False, verbose_name="닷컴 코드", default="B2C")

    class Meta:        
        indexes = [
        	models.Index(fields=['country_code'], name="r3_vvfm_country_code_idx"),
            HnswIndex(
                name="r3_vvfm_vector_idx",
                fields=["embedding"],
                m=16,
                ef_construction=64,
                opclasses=["vector_cosine_ops"],
            )
        ]


class Web_Cache(models.Model):
    country_code       = models.CharField(verbose_name='Country Code', null=True, blank=True)   ## TODO : Create Search Keyword
    query              = models.CharField(verbose_name='Query', null=True, blank=True)
    title              = models.CharField(verbose_name='Title', null=True, blank=True)
    url                = models.TextField(verbose_name='URL')
    content            = models.TextField(verbose_name='Content')
    created_on         = models.DateTimeField(verbose_name='Created On', auto_now_add=True)
    site_cd            = models.CharField(max_length=10, null=False, blank=False, verbose_name="닷컴 코드", default="B2C")

    class Meta:
        indexes = [
        	models.Index(fields=['country_code', 'query', 'url'], name="r3_wc_idx"),
        ]


class web_clean_cache(models.Model):    
    active                  = models.BooleanField(verbose_name='Active', default=True)
    update_tag              = models.CharField(verbose_name='Update Tag', blank=True, null=True)
    url                     = models.TextField(verbose_name='URL', null=True, blank=True)
    content                 = models.TextField(verbose_name='Content', null=True, blank=True)
    country_code            = models.CharField(verbose_name='Country Code', null=True, blank=True)
    query                   = models.CharField(verbose_name='Query', null=True, blank=True)
    title                   = models.CharField(verbose_name='Title', null=True, blank=True)
    clean_content           = models.TextField(verbose_name='Clean Content', null=True, blank=True)
    # tokenized_content = models.TextField(verbose_name='Tokenized Content', null=True, blank=True)
    content_embed           = VectorField(dimensions=1024, help_text="BAAI/bge-m3", null=True, blank=True)
    summary                 = models.TextField(verbose_name='Summary', null=True, blank=True)
    source                  = models.CharField(verbose_name='Source', max_length=10, null=True, blank=True)
    domain                  = models.CharField(verbose_name='Domain', max_length=255, null=True, blank=True)
    date                    = models.DateTimeField(verbose_name='Date',null=True, blank=True)
    intelligence_filter     = ArrayField(models.CharField(max_length=100), verbose_name= "Intelligence Filter", null=True, blank=True)
    sub_intelligence_filter = ArrayField(models.CharField(max_length=100), verbose_name= "Sub Intelligence Filter", null=True, blank=True)
    created_on              = models.DateTimeField(verbose_name='Create', auto_now_add=True)


    class Meta:
        indexes = [
        	models.Index(fields=['active', 'country_code', 'source', 'title'], name="web_db_fields_idx"),
            HnswIndex(
                name='web_db_vector_index',
                fields=['content_embed'],
                m=16,
                ef_construction=64,
                opclasses=['vector_l2_ops']
            )
            # # or
            # IvfflatIndex(
            #     name='my_index',
            #     fields=['embedding'],
            #     lists=100,
            #     opclasses=['vector_l2_ops']
            # )
        ]

        
class Web_Link(models.Model):
    id = models.AutoField(primary_key=True, serialize=False) # 기본 필드
    product_line = models.CharField(verbose_name='Product Line', null=True, blank=True)
    link = models.CharField(verbose_name='Link', null=True, blank=True)
    description = models.CharField(verbose_name='Description', null=True, blank=True)
    channel = ArrayField(models.CharField(max_length=100), verbose_name= "Channel", null=True, blank=True)
    ner_field = ArrayField(models.CharField(max_length=100), verbose_name= "Ner Field", null=True, blank=True)
    intelligence = ArrayField(models.CharField(max_length=100), verbose_name= "Intelligence", null=True, blank=True)
    sub_intelligence = ArrayField(models.CharField(max_length=100), verbose_name= "Sub Intelligence", null=True, blank=True)
    country_code = models.CharField(verbose_name='Country Code', null=True, blank=True)
    created_on          = models.DateTimeField(verbose_name='Create', auto_now_add=True)
    updated_on          = models.DateTimeField(verbose_name='Update', auto_now=True)
    site_cd             = models.CharField(max_length=10, null=False, blank=False, verbose_name="닷컴 코드", default="B2C")
    
    class Meta:        
        indexes = [
        	models.Index(fields=['product_line'], name="r3_wl_idx"),
        ]


# class Actual_Data_Source(models.Model):
#     id                  = models.AutoField(primary_key=True)
#     type                = models.CharField(verbose_name='Type') # Table, API
#     data_source_id      = models.CharField(verbose_name='Data Source ID')
#     data_source_name    = models.CharField(verbose_name='Data Source Name')
#     data_source_description   = models.CharField(verbose_name='Data Source Description', null=True, blank=True)
#     data_source_endpoint      = models.CharField(verbose_name='Data Source Endpoint', null=True, blank=True)
#     data_source_request_spec  = models.TextField(verbose_name='Request Spec', null=True, blank=True)
#     created_on          = models.DateTimeField(verbose_name='Create', auto_now_add=True)
#     updated_on          = models.DateTimeField(verbose_name='Update', auto_now=True)
#     country_code        = models.CharField(verbose_name='Country Code', null=True, blank=True)


# class Query_Master(models.Model):
#     id                  = models.AutoField(primary_key=True)
#     main_code           = models.CharField(verbose_name='Main Query Code', max_length=11)
#     main_query          = models.TextField(verbose_name='Main Query', null=False, blank=True)
#     sub_code            = models.IntegerField(verbose_name='Sub Query Code')
#     sub_query           = models.TextField(verbose_name='Sub Single Query')
#     created_on          = models.DateTimeField(verbose_name='Create', auto_now_add=True)

#     updated_on          = models.DateTimeField(verbose_name='Update', auto_now=True)    
#     class Meta:
#         unique_together = ('main_code', 'sub_code',)
#         verbose_name_plural = "99. Query Master"            


# # edit history 는 최근 3 번의 변경에 대해 기록
# # [ {'user' : 'A', 'datetime': datatime, 'context': '마지막 수정 버젼, 현재 시스템 버젼과 같음' }]

# class Prompt_Template(models.Model):
#     id                  = models.AutoField(primary_key=True)
#     language            = models.CharField(verbose_name='Language', choices=LANGUAGE, max_length=2)
#     module              = models.CharField(verbose_name='Module', choices=MODULE, null=True, blank=True)
#     intelligence        = models.CharField(verbose_name='Intelligence', null=True, blank=True)
#     prompt_template_id  = models.CharField(verbose_name='Prompt Template ID', max_length=50)
#     prompt_template_description    = models.CharField(verbose_name='Prompt Template Discription', max_length=50)
#     prompt_template     = models.TextField(verbose_name='Prompt Template', null=True, blank=True)
#     current_edit_user   = models.CharField(verbose_name='Current Edit User', null=True, blank=True)
#     edit_history        = models.JSONField(verbose_name='Edit History', null=True, blank=True, default = dict)
#     active              = models.BooleanField(verbose_name='Active', default=False)
#     created_on          = models.DateTimeField(verbose_name='Create', auto_now_add=True)
#     updated_on          = models.DateTimeField(verbose_name='Update', auto_now=True)

#     class Meta:
#         verbose_name_plural = "01. Prompt Template"


# class Intelligence(models.Model):
#     id                  = models.AutoField(primary_key=True)
#     country_code        = models.CharField(verbose_name='Country Code', null=True, blank=True)
#     index_priority      = models.JSONField(verbose_name='Unstructured Index Priority', null=True, blank=True, default = dict)
#     category            = models.CharField(verbose_name='Category', null=True, blank=True)
#     intelligence        = models.CharField(verbose_name='Intelligence', null=True, blank=True)
#     intelligence_desc   = models.CharField(verbose_name='Intelligence Desc', null=True, blank=True)
#     intelligence_meta   = models.JSONField(verbose_name='Intelligence Meta', null=True, blank=True, default = dict)
#     cache               = models.BooleanField(verbose_name='Cache', default=False)
#     created_on          = models.DateTimeField(verbose_name='Create', auto_now_add=True)
#     updated_on          = models.DateTimeField(verbose_name='Update', auto_now=True)

#     class Meta:
#         verbose_name_plural = "02. Intelligence"
#         indexes = [
#         	models.Index(fields=['intelligence'], name="i_intelligence_idx"),
#         ]


# class Training_Intelligence_Triage_Revised(models.Model):
#     id                  = models.AutoField(primary_key=True)
#     embedding = VectorField(
#         dimensions=1024,  # Changed from 1536 to 1024 for bge-m3
#         help_text="BAAI/bge-m3",
#         null=True,
#         blank=True,
#     )
#     query               = models.TextField(verbose_name='Query', null=True, blank=True)
#     language            = models.CharField(verbose_name='Language', choices=LANGUAGE, max_length=2)
#     intelligence        = models.CharField(verbose_name='Intelligence', null=True, blank=True)
#     rag_type            = models.CharField(verbose_name='RAG Type', max_length=20)
#     virtual_view        = models.CharField(verbose_name='Virtual View', null=True, blank=True)
#     edit_history        = models.JSONField(verbose_name='Edit History', null=True, blank=True, default = dict)
#     created_on          = models.DateTimeField(verbose_name='Create', auto_now_add=True)
#     updated_on          = models.DateTimeField(verbose_name='Update', auto_now=True)
#     country_code        = models.CharField(verbose_name='Country Code', null=True, blank=True)

#     class Meta:
#         indexes = [
#         	models.Index(fields=['country_code'], name="it_country_code_idx"),
#         ]

#         indexes = [
#             HnswIndex(
#                 name="it_vector_idx",
#                 fields=["embedding"],
#                 m=16,
#                 ef_construction=64,
#                 opclasses=["vector_cosine_ops"],
#             )
#         ]
#         verbose_name_plural = "02. (Training) Intelligence Triage Revised Embedding"
#         db_table = "rubicon_training_intelligence_triage_revised"


# class Intelligence_Triage(models.Model):
#     id                  = models.AutoField(primary_key=True)
#     embedding = VectorField(
#         dimensions=1024,  # Changed from 1536 to 1024 for bge-m3
#         help_text="BAAI/bge-m3",
#         null=True,
#         blank=True,
#     )
#     query               = models.TextField(verbose_name='Query', null=True, blank=True)
#     language            = models.CharField(verbose_name='Language', choices=LANGUAGE, max_length=2)
#     intelligence        = models.CharField(verbose_name='Intelligence', null=True, blank=True)
#     rag_type            = models.CharField(verbose_name='RAG Type', max_length=20)
#     virtual_view        = models.CharField(verbose_name='Virtual View', null=True, blank=True)
#     created_on          = models.DateTimeField(verbose_name='Create', auto_now_add=True)
#     updated_on          = models.DateTimeField(verbose_name='Update', auto_now=True)
#     country_code        = models.CharField(verbose_name='Country Code', null=True, blank=True)

#     class Meta:
#         indexes = [
#         	models.Index(fields=['country_code'], name="it_fields_idx"),
#         ]

#         indexes = [
#             HnswIndex(
#                 name="it_2nd_vector_idx",
#                 fields=["embedding"],
#                 m=16,
#                 ef_construction=64,
#                 opclasses=["vector_cosine_ops"],
#             )
#         ]
#         verbose_name_plural = "02. Intelligence Triage"
        

# class Virtual_View(models.Model):
#     id                  = models.AutoField(primary_key=True)
#     country_code        = models.CharField(verbose_name='Country Code', null=True, blank=True)
#     intelligence        = models.CharField(verbose_name='Intelligence')
#     virtual_view        = models.CharField(verbose_name='Virtual View', null=True, blank=True)
#     virtual_view_type   = models.CharField(verbose_name='Virtaul View Type')
#     virtual_view_description   = models.CharField(verbose_name='Virtaul View Description')
#     created_on          = models.DateTimeField(verbose_name='Create', auto_now_add=True)
#     updated_on          = models.DateTimeField(verbose_name='Update', auto_now=True)
    
#     class Meta:
#         verbose_name_plural = "03. Virtual View"
#         indexes = [
#         	models.Index(fields=['country_code'], name="vv_country_code_idx"),
#         ]


# class Unstructured_Index(models.Model):
#     id                  = models.AutoField(primary_key=True)
#     country_code        = models.CharField(verbose_name='Country Code', null=True, blank=True)
#     op_type             = models.CharField(verbose_name='OP Type')
#     name                = models.CharField(verbose_name='Index Name')
#     ai_search_index     = models.CharField(verbose_name='AI Search Index', null=True, blank=True)
#     created_on          = models.DateTimeField(verbose_name='Create', auto_now_add=True)
#     updated_on          = models.DateTimeField(verbose_name='Update', auto_now=True)
    
#     class Meta:
#         indexes = [
#         	models.Index(fields=['country_code', 'name'], name="ui_fields_idx"),
#         ]


# class Virtual_View_Field(models.Model):
#     id                  = models.AutoField(primary_key=True)
#     country_code        = models.CharField(verbose_name='Country Code', null=True, blank=True)
#     virtual_view_id     = models.ForeignKey(Virtual_View, verbose_name='Virtual_View', on_delete=models.PROTECT)
#     order               = models.IntegerField(verbose_name='Order', default=0)
#     field_name          = models.CharField(verbose_name='Field Name')
#     field_type          = models.CharField(verbose_name='Field Type')
#     field_description   = models.CharField(verbose_name='Field Description')
#     created_on          = models.DateTimeField(verbose_name='Create', auto_now_add=True)
#     updated_on          = models.DateTimeField(verbose_name='Update', auto_now=True)
    
#     class Meta:
#         verbose_name_plural = "03. Virtual View"


# class Actual_Data_Source(models.Model):
#     id                  = models.AutoField(primary_key=True)
#     type                = models.CharField(verbose_name='Type') # Table, API
#     data_source_id      = models.CharField(verbose_name='Data Source ID')
#     data_source_name    = models.CharField(verbose_name='Data Source Name')
#     data_source_description   = models.CharField(verbose_name='Data Source Description', null=True, blank=True)
#     data_source_endpoint      = models.CharField(verbose_name='Data Source Endpoint', null=True, blank=True)
#     data_source_request_spec  = models.TextField(verbose_name='Request Spec', null=True, blank=True)
#     created_on          = models.DateTimeField(verbose_name='Create', auto_now_add=True)
#     updated_on          = models.DateTimeField(verbose_name='Update', auto_now=True)
#     country_code        = models.CharField(verbose_name='Country Code', null=True, blank=True)
    
#     class Meta:
#         verbose_name_plural = "04. Actual Data Source"


# class Actual_Data_Source_Field(models.Model):
#     id                  = models.AutoField(primary_key=True)
#     data_source_id      = models.ForeignKey(Actual_Data_Source, verbose_name='Actual Data Source', on_delete=models.PROTECT)
#     order               = models.IntegerField(verbose_name='Order', default=0)
#     field_name          = models.CharField(verbose_name='Field Name')
#     field_type          = models.CharField(verbose_name='Field Type')
#     field_description   = models.CharField(verbose_name='Field Description')
#     virtual_view_field_id   = models.ForeignKey(Virtual_View, verbose_name='Virtual View Field', null=True, blank=True, on_delete=models.PROTECT)
#     created_on          = models.DateTimeField(verbose_name='Create', auto_now_add=True)
#     updated_on          = models.DateTimeField(verbose_name='Update', auto_now=True)
#     country_code        = models.CharField(verbose_name='Country Code', null=True, blank=True)

#     class Meta:
#         verbose_name_plural = "05. Actual Data Source Field"


# class View_Config_Revised(models.Model):
#     id                  = models.AutoField(primary_key=True)
#     country_code        = models.CharField(verbose_name='Country Code', null=True, blank=True)
#     virtual_view        = models.CharField(verbose_name='Virtual View', null=True, blank=True)
#     config_type         = models.CharField(verbose_name='Config Type', null=True, blank=True)
#     data_source         = models.CharField(verbose_name='Data Source',  null=True, blank=True)
#     config              = models.JSONField(verbose_name='Config', null=True, blank=True, default = dict)
#     created_on          = models.DateTimeField(verbose_name='Create', auto_now_add=True)
#     updated_on          = models.DateTimeField(verbose_name='Update', auto_now=True)

#     class Meta:
#         verbose_name_plural = "02. View Config Revised"
#         db_table = "rubicon_view_config_revised"
#         indexes = [
#         	models.Index(fields=['country_code'], name="vc_country_code_idx"),
#         ]


# class Code_Mapping(models.Model):
#     id                  = models.AutoField(primary_key=True, serialize=False)
#     country_code        = models.CharField(verbose_name='Country Code', null=True, blank=True)
#     expression_embedding = VectorField(
#         dimensions=1024,  # Changed from 1536 to 1024 for bge-m3
#         help_text="BAAI/bge-m3",
#         null=True,
#         blank=True,
#     )
#     expression          = models.TextField(blank=True, null=True, verbose_name='Expression')
#     virtual_view        = models.CharField(blank=True, null=True, verbose_name='Virtual View', max_length=1024)
#     field               = models.CharField(verbose_name='Field', max_length=1024)
#     mapping_code        = models.CharField(verbose_name='Mapping Code', max_length=1024)
#     expression_to_code  = models.BooleanField(verbose_name='Expression to Code', null=True, blank=True)
#     structured          = models.BooleanField(verbose_name='Structured', null=True, blank=True)
#     unstructured        = models.BooleanField(verbose_name='UnStructured', null=True, blank=True)
#     category_lv1 = models.CharField(verbose_name='Category Lv. 1', blank=True, null=True)
#     category_lv2 = models.CharField(verbose_name='Category Lv. 2', blank=True, null=True)
#     category_lv3 = models.CharField(verbose_name='Category Lv. 3', blank=True, null=True)
#     active              = models.BooleanField(verbose_name='Active', default=True)
#     update_tag          = models.CharField(verbose_name='Update Tag', blank=True, null=True)
#     created_on          = models.DateTimeField(verbose_name='Create', auto_now_add=True)
#     updated_on          = models.DateTimeField(verbose_name='Update', auto_now=True)

#     class Meta:
#         indexes = [
#         	models.Index(fields=['field', 'expression', 'country_code', 'structured', 'unstructured'], name="cm_fields_idx"),
#         ]
#         indexes = [
#             HnswIndex(
#                 name="cm_vector_idx",
#                 fields=["expression_embedding"],
#                 m=16,
#                 ef_construction=64,
#                 opclasses=["vector_cosine_ops"],
#             )
#         ]
#         verbose_name_plural = '05. Mapping Code Table Master Revised Embedding' 
#         db_table = "rubicon_code_mapping" 
        

# class Predefined_Answer(models.Model):
#     id                  = models.AutoField(primary_key=True)
#     embedding           = VectorField(
#         dimensions=1024,  # Changed from 1536 to 1024 for bge-m3
#         help_text="BAAI/bge-m3",
#         null=True,
#         blank=True,
#     )
#     category            = models.CharField(verbose_name='Category')
#     query               = models.CharField(verbose_name='Query')
#     predefined_type     = models.CharField(verbose_name='Predefined Type', null=True, blank=True)
#     predefined_query    = models.JSONField(verbose_name='Predefined Query', null=True, blank=True, default = dict)
#     predefined_answer   = models.TextField(verbose_name='Predefined Answer', null=True, blank=True)
#     created_on          = models.DateTimeField(verbose_name='Create', auto_now_add=True)
#     updated_on          = models.DateTimeField(verbose_name='Update', auto_now=True)
#     country_code        = models.CharField(verbose_name='Country Code', null=True, blank=True)
    
#     class Meta:
#         indexes = [
#         	models.Index(fields=['country_code'], name="pa_country_code_idx"),
#         ]
#         indexes = [
#             HnswIndex(
#                 name="pa_vector_idx",
#                 fields=["embedding"],
#                 m=16,
#                 ef_construction=64,
#                 opclasses=["vector_cosine_ops"],
#             )
#         ]
#         verbose_name_plural = "06. Predefined Answer Table Revised Embedding"
#         db_table = "rubicon_predefined_answer_revised"
        
        
# class NER(models.Model):
#     id                  = models.AutoField(primary_key=True, serialize=False)
#     embedding           = VectorField(
#         dimensions=1024,  # Changed from 1536 to 1024 for bge-m3
#         help_text="BAAI/bge-m3",
#         null=True,
#         blank=True,
#     )
#     query               = models.TextField(verbose_name='Query', blank=True, null=True)
#     language            = models.CharField(verbose_name='Language', choices=LANGUAGE, max_length=2, blank=True, null=True)
#     intelligence        = models.CharField(verbose_name='Intelligence', blank=True, null=True)
#     virtual_view        = models.CharField(verbose_name='Virtual View', blank=True, null=True)
#     measure_dimension   = models.JSONField(verbose_name='Measure Dimension', blank=True, default=dict, null=True)
#     structured          = models.BooleanField(verbose_name='Structured', null=True, blank=True)
#     unstructured        = models.BooleanField(verbose_name='UnStructured', null=True, blank=True)
#     edit_status         = models.CharField(verbose_name='Edit Status', blank=True, null=True)
#     edit_history        = models.JSONField(verbose_name='Edit History', null=True, blank=True, default=dict)
#     confirmed           = models.BooleanField(verbose_name='Confirmed',  null=True, blank=True, default=False)
#     confirmed_by        = models.CharField(verbose_name='Confirmed By', blank=True, null=True)
#     created_on          = models.DateTimeField(verbose_name='Created On', auto_now_add=True )
#     updated_on          = models.DateTimeField(verbose_name='Updated On', auto_now=True)
#     country_code        = models.CharField(verbose_name='Country Code', null=True, blank=True)

#     class Meta:
#         indexes = [
#         	models.Index(fields=['country_code'], name="r3_ner_country_code_idx"),
#         ]
#         indexes = [
#             HnswIndex(
#                 name="ner_vector_idx",
#                 fields=["embedding"],
#                 m=16,
#                 ef_construction=64,
#                 opclasses=["vector_cosine_ops"],
#             )
#         ]
        

# class Virtual_View_Field_Meta(models.Model):
#     id                  = models.AutoField(primary_key=True)
#     country_code        = models.CharField(verbose_name='Country Code', null=True, blank=True)
#     virtual_view        = models.CharField(verbose_name='virtual_view')
#     virtual_view_field  = models.CharField(verbose_name='virtual_view_Field')
#     embedding           = VectorField(
#         dimensions=1024,  # Changed from 1536 to 1024 for bge-m3
#         help_text="BAAI/bge-m3",
#         null=True,
#         blank=True,
#     )
#     query               = models.CharField(verbose_name='Query', null=True, blank=True)
#     field_processing_meta = models.JSONField(verbose_name='Field Processing Meta', null=True, blank=True, default = dict)
#     created_on          = models.DateTimeField(verbose_name='Create', auto_now_add=True)
#     updated_on          = models.DateTimeField(verbose_name='Update', auto_now=True)

#     class Meta:
#         indexes = [
#         	models.Index(fields=['country_code'], name="vvfm_country_code_idx"),
#         ]
#         indexes = [
#             HnswIndex(
#                 name="vvfm_vector_idx",
#                 fields=["embedding"],
#                 m=16,
#                 ef_construction=64,
#                 opclasses=["vector_cosine_ops"],
#             )
#         ]
        

# class Pseudo_Query(models.Model):
#     id                  = models.AutoField(primary_key=True, serialize=False)
#     embedding           = VectorField(
#         dimensions=1024,  # Changed from 1536 to 1024 for bge-m3
#         help_text="BAAI/bge-m3",
#         null=True,
#         blank=True,
#     )
#     query               = models.TextField(verbose_name='Query', null=True, blank=True)
#     country_code        = models.CharField(verbose_name='Country Code', null=True, blank=True)
#     language            = models.CharField(verbose_name='Language', choices=LANGUAGE, max_length=2, blank=True, null=True)
#     intelligence        = models.CharField(verbose_name='Intelligence', null=True, blank=True)
#     virtual_view        = models.CharField(verbose_name='Virtual View', null=True, blank=True)
#     data_source         = models.CharField(verbose_name='Data Source', null=True, blank=True)
#     ner_code_mapping    = models.JSONField(verbose_name='NER / Code Mapping', null=True, blank=True, default=dict)
#     pseudo_query        = models.JSONField(verbose_name='Pseudo Query', null=True, blank=True, default=dict)
#     created_on          = models.DateTimeField(verbose_name='Created On', auto_now_add=True)
#     updated_on          = models.DateTimeField(verbose_name='Updated On', auto_now=True)

#     class Meta:
#         indexes = [
#         	models.Index(fields=['country_code'], name="ps_country_code_idx"),
#         ]
#         indexes = [
#             HnswIndex(
#                 name="pseudo_vector_idx",
#                 fields=["embedding"],
#                 m=16,
#                 ef_construction=64,
#                 opclasses=["vector_cosine_ops"],
#             )
#         ]


# class Product_Meta(models.Model):
#     id                  = models.AutoField(primary_key=True)
#     country_code        = models.CharField(verbose_name='Country Code', null=True, blank=True)
#     product_category_lv1    = models.CharField(verbose_name='Product Category Lv1', blank=True, null=True)
#     product_category_lv2    = models.CharField(verbose_name='Product Category Lv2', blank=True, null=True)
#     product_category_lv3    = models.CharField(verbose_name='Product Category Lv3', blank=True, null=True)
#     product_model           = models.CharField(verbose_name='Product Model', blank=True, null=True)
#     # product_code            = models.CharField(verbose_name='Product Code', blank=True, null=True)
#     feature_name            = models.CharField(verbose_name='Feature Name', blank=True, null=True)
#     feature_description     = models.TextField(verbose_name='Feature Description', blank=True, null=True)
#     feature_type            = models.CharField(verbose_name='Feature Type', blank=True, null=True)
#     feature_priority_order  = models.IntegerField(verbose_name='Feature Priority Order', null=True)
#     created_on          = models.DateTimeField(verbose_name='Create', auto_now_add=True)
#     updated_on          = models.DateTimeField(verbose_name='Update', auto_now=True)

#     class Meta:
#         db_table = "rubicon_product_meta"
#         indexes = [
#         	models.Index(fields=['country_code', 'product_model'], name="pm_fields_idx"),
#         ]

        
# class Response_Layout(models.Model):
#     id                  = models.AutoField(primary_key=True, serialize=False)
#     embedding           = VectorField(
#         dimensions=1024,  # Changed from 1536 to 1024 for bge-m3
#         help_text="BAAI/bge-m3",
#         null=True,
#         blank=True,
#     )
#     query               = models.TextField(verbose_name='Query', null=True, blank=True)
#     response_layout     = models.CharField(verbose_name='Response Layout', blank=True, null=True)
#     country_code        = models.CharField(verbose_name='Country Code', null=True, blank=True)
#     created_on          = models.DateTimeField(verbose_name='Created On', auto_now_add=True)
#     updated_on          = models.DateTimeField(verbose_name='Updated On', auto_now=True)
    
#     class Meta:
#         verbose_name_plural = "08. Response Layout Reference Table"
#         db_table = "rubicon_resp_layout_ref"
#         indexes = [
#         	models.Index(fields=['country_code'], name="rl_country_code_idx"),
#         ]
#         indexes = [
#             HnswIndex(
#                 name="rl_vector_idx",
#                 fields=["embedding"],
#                 m=16,
#                 ef_construction=64,
#                 opclasses=["vector_cosine_ops"],
#             )
#         ]
        
        
# class Response_Layout_Ref_v2(models.Model):
#     id                  = models.AutoField(primary_key=True, serialize=False)
#     intelligence        = models.CharField(verbose_name='Intelligence', null=True, blank=True)
#     response_layout     = models.CharField(verbose_name='Response Layout', blank=True, null=True)
#     country_code        = models.CharField(verbose_name='Country Code', null=True, blank=True)
#     created_on          = models.DateTimeField(verbose_name='Created On', auto_now_add=True)
#     updated_on          = models.DateTimeField(verbose_name='Updated On', auto_now=True)
    
#     class Meta:
#         verbose_name_plural = "08. Response Layout Reference Table"
#         db_table = "rubicon_resp_layout_ref_v2"
#         indexes = [
#         	models.Index(fields=['country_code'], name="rl_country_code_idx_v2"),
#         ]


# class NER_Ref_Test(models.Model):
#     id                  = models.AutoField(primary_key=True, serialize=False)
#     embedding           = VectorField(
#         dimensions=1024,  # Changed from 1536 to 1024 for bge-m3
#         help_text="BAAI/bge-m3",
#         null=True,
#         blank=True,
#     )
#     query               = models.TextField(verbose_name='Query', blank=True, null=True)
#     language            = models.CharField(verbose_name='Language', choices=LANGUAGE, max_length=2, blank=True, null=True)
#     intelligence        = models.CharField(verbose_name='Intelligence', blank=True, null=True)
#     virtual_view        = models.CharField(verbose_name='Virtual View', blank=True, null=True)
#     measure_dimension   = models.JSONField(verbose_name='Measure Dimension', blank=True, default=dict, null=True)
#     structured          = models.BooleanField(verbose_name='Structured', null=True, blank=True)
#     unstructured        = models.BooleanField(verbose_name='UnStructured', null=True, blank=True)
#     edit_status         = models.CharField(verbose_name='Edit Status', blank=True, null=True)
#     edit_history        = models.JSONField(verbose_name='Edit History', null=True, blank=True, default=dict)
#     confirmed           = models.BooleanField(verbose_name='Confirmed',  null=True, blank=True, default=False)
#     confirmed_by        = models.CharField(verbose_name='Confirmed By', blank=True, null=True)
#     created_on          = models.DateTimeField(verbose_name='Created On', auto_now_add=True )
#     updated_on          = models.DateTimeField(verbose_name='Updated On', auto_now=True)
#     country_code        = models.CharField(verbose_name='Country Code', null=True, blank=True)
#     active              = models.BooleanField(verbose_name='Active', default=True)
#     update_tag          = models.CharField(verbose_name='Update Tag', blank=True, null=True)
    
#     class Meta:        
#         indexes = [
#         	models.Index(fields=['country_code'], name="ner_country_code_idx2"),
#             HnswIndex(
#                 name="ner_vector_idx3",
#                 fields=["embedding"],
#                 m=16,
#                 ef_construction=64,
#                 opclasses=["vector_cosine_ops"],
#             )
#         ]


# class Query_Master(models.Model):
#     id                  = models.AutoField(primary_key=True)
#     main_code           = models.CharField(verbose_name='Main Query Code', max_length=11)
#     main_query          = models.TextField(verbose_name='Main Query', null=False, blank=True)
#     sub_code            = models.IntegerField(verbose_name='Sub Query Code')
#     sub_query           = models.TextField(verbose_name='Sub Single Query')
#     created_on          = models.DateTimeField(verbose_name='Create', auto_now_add=True)
#     updated_on          = models.DateTimeField(verbose_name='Update', auto_now=True)    

    
#     class Meta:
#         unique_together = ('main_code', 'sub_code',)            


# edit history 는 최근 3 번의 변경에 대해 기록
# [ {'user' : 'A', 'datetime': datatime, 'context': '마지막 수정 버젼, 현재 시스템 버젼과 같음' }]