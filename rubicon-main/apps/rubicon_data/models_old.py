from django.db import models
from django.contrib.gis.db import models as gis_models
from django.contrib.postgres.fields import ArrayField

# Create your models here.
# class Goods_Base(models.Model):
#     product_code = models.CharField(verbose_name='제품 코드', max_length=10, primary_key=True)
#     product_name = models.CharField(verbose_name='제품명', max_length=100, null=True, blank=True)
#     model = models.CharField(verbose_name='모델명', max_length=50, null=True, blank=True)
#     column1 = models.CharField(verbose_name='칼럼1', max_length=50, null=True, blank=True)    
#     created_on = models.DateTimeField(verbose_name='Create', auto_now_add=True)
#     updated_on = models.DateTimeField(verbose_name='Update', auto_now=True)

#     class Meta:
#         verbose_name_plural = "01. RAW_GOODS_BASE"
        

# class Goods_Spec_Mast(models.Model):
#     id = models.AutoField(primary_key=True)
#     product = models.CharField(verbose_name='모델 구분', max_length=20, null=True, blank=True)
#     column6 = models.CharField(verbose_name='칼럼6', max_length=20, null=True, blank=True)    
#     column7 = models.CharField(verbose_name='칼럼7', max_length=100, null=True, blank=True)    
#     spec_code2 = models.CharField(verbose_name= '스펙코드2', max_length=100, null=True, blank=True)
#     spec_code = models.CharField(verbose_name='스펙코드', max_length=100, null=True, blank=True)
#     sub_spec_code = models.CharField(verbose_name='스펙코드', max_length=20, null=True, blank=True)
#     spec_name_en = models.TextField(verbose_name='스펙명(영어)', null=True, blank=True)
#     spec_name_ko = models.TextField(verbose_name='스펙명(한글)', null=True, blank=True)
#     column8 = models.CharField(verbose_name='칼럼8', max_length=100, null=True, blank=True)    
#     created_on = models.DateTimeField(verbose_name='Create', auto_now_add=True)
#     updated_on = models.DateTimeField(verbose_name='Update', auto_now=True)
#     column9 = models.CharField(verbose_name='칼럼9', max_length=100, null=True, blank=True)      

#     class Meta:
#         verbose_name_plural = "03. RAW_GOODS_SPEC_MAST"


# class Goods_Spec_Info(models.Model):
#     id = models.AutoField(primary_key=True)
#     model = models.CharField(verbose_name='모델명', max_length=100, null=True, blank=True)
#     column2 = models.CharField(verbose_name='칼럼2', max_length=5, null=True, blank=True)    
#     product = models.CharField(verbose_name='모델 구분', max_length=20, null=True, blank=True)
#     spec_code = models.CharField(verbose_name='스펙코드', max_length=20, null=True, blank=True)
#     spec_code2 = models.CharField(verbose_name= '스펙코드2', max_length=100, null=True, blank=True)
#     column3 = models.CharField(verbose_name='칼럼3', max_length=20, null=True, blank=True)    
#     column4 = models.CharField(verbose_name='칼럼4', max_length=20, null=True, blank=True)    
#     column5 = models.CharField(verbose_name='칼럼5', max_length=20, null=True, blank=True)    
#     created_on = models.DateTimeField(verbose_name='Create', auto_now_add=True)
#     updated_on = models.DateTimeField(verbose_name='Update', auto_now=True)
#     value = models.TextField(verbose_name= 'Spec 값', null=True, blank=True)

#     class Meta:
#         verbose_name_plural = "02. RAW_GOODS_SPEC_INFO"


# class V_Goods_Spec(models.Model):
#     goods_id = models.CharField(verbose_name='GOODS_ID', max_length=20, null=True, blank=True)
#     goods_name = models.CharField(verbose_name='GOODS_NAME', max_length=1000, null=True, blank=True)
#     model_code = models.CharField(verbose_name='MODEL_CODE', max_length=1000, null=True, blank=True)
#     goods_model = models.CharField(verbose_name='GOODS_MODEL', max_length=1000, null=True, blank=True)
#     color = models.CharField(verbose_name='COLOR', max_length=1000, null=True, blank=True)
#     storage = models.CharField(verbose_name='STORAGE', max_length=1000, null=True, blank=True)
#     sales_channel = models.CharField(verbose_name='SALES_CHANNEL', max_length=1000, null=True, blank=True)
#     ssdc_color = models.CharField(verbose_name='SSDC_COLOR', max_length=1000, null=True, blank=True)
#     ssgn_color = models.CharField(verbose_name='SSGN_COLOR', max_length=1000, null=True, blank=True)
#     display_name = models.CharField(verbose_name='DISPLAY_NAME', max_length=1000, null=True, blank=True)
#     spec_value = models.CharField(verbose_name='spec_value', max_length=1000, null=True, blank=True)

#     class Meta:
#         verbose_name_plural = "04. RAW_V_GOODS_SPEC"


class V_Place(models.Model):
    store_name = models.CharField(verbose_name="STORE_NAME", max_length=50, null=True, blank=True)
    store_type_code = models.CharField(verbose_name="STORE_TYPE_CODE", max_length=50, null=True, blank=True)
    road_address = models.CharField(verbose_name="ROAD_ADDRESS", max_length=1000, null=True, blank=True)
    park = models.CharField(verbose_name="PARK", max_length=1000, null=True, blank=True)
    bus = models.CharField(verbose_name="BUS", max_length=1000, null=True, blank=True)
    subway = models.CharField(verbose_name="SUBWAY", max_length=1000, null=True, blank=True)
    taxi = models.CharField(verbose_name="TAXI", max_length=1000, null=True, blank=True)
    phone = models.CharField(verbose_name="PHONE", max_length=20, null=True, blank=True)
    store_size = models.CharField(verbose_name="STORE_SIZE", max_length=50, null=True, blank=True)
    reservation_available = models.CharField(verbose_name="RESERVATION_AVAILABLE", max_length=10, null=True, blank=True)
    weekday_open_time = models.CharField(verbose_name="WEEKDAY_OPEN_TIME", max_length=20, null=True, blank=True)
    weekday_close_time = models.CharField(verbose_name="WEEKDAY_CLOSE_TIME", max_length=20, null=True, blank=True)
    weekend_open_time = models.CharField(verbose_name="WEEKEND_OPEN_TIME", max_length=20, null=True, blank=True)
    weekend_close_time = models.CharField(verbose_name="WEEKEND_CLOSE_TIME", max_length=20, null=True, blank=True)
    holiday_start = models.CharField(verbose_name="HOLIDAY_START", max_length=50, null=True, blank=True)
    holiday_end = models.CharField(verbose_name="HOLIDAY_END", max_length=50, null=True, blank=True)
    geo_data = models.CharField(verbose_name="GEO_DATA", max_length=1000, null=True, blank=True)
    geo_str2 = models.CharField(verbose_name="GEO_STR", max_length=1000, null=True, blank=True)

    class Meta:
        verbose_name_plural = "05. RAW_V_PLACE"
        managed=False

# class V_Sales_Goods(models.Model):
#     goods_id = models.CharField(verbose_name="GOODS_ID", max_length=20, null=True, blank=True)
#     goods_name = models.CharField(verbose_name="GOODS_NAME", max_length=1000, null=True, blank=True)
#     model_code = models.CharField(verbose_name="MODEL_CODE", max_length=50, null=True, blank=True)
#     goods_model = models.CharField(verbose_name="GOODS_MODEL", max_length=20, null=True, blank=True)
#     color = models.CharField(verbose_name="COLOR", max_length=20, null=True, blank=True)
#     storage = models.CharField(verbose_name="STORAGE", max_length=20, null=True, blank=True)
#     sales_channel = models.CharField(verbose_name="SALES_CHANNEL", max_length=20, null=True, blank=True)
#     ssdc_color = models.CharField(verbose_name="SSDC_COLOR", max_length=20, null=True, blank=True)
#     ssgn_color = models.CharField(verbose_name="SSGN_COLOR", max_length=20, null=True, blank=True)
#     standard_price = models.CharField(verbose_name="STANDARD_PRICE", max_length=20, null=True, blank=True)
#     member_price = models.CharField(verbose_name="MEMBER_PRICE", max_length=20, null=True, blank=True)
#     benefit_price = models.CharField(verbose_name="BENEFIT_PRICE", max_length=20, null=True, blank=True)
#     receiving_method = models.CharField(verbose_name="RECEIVING_METHOD", max_length=20, null=True, blank=True)
#     order_month = models.CharField(verbose_name="ORDER_MONTH", max_length=20, null=True, blank=True)
#     age_group = models.CharField(verbose_name="AGE_GROUP", max_length=20, null=True, blank=True)
#     gender = models.CharField(verbose_name="GENDER", max_length=20, null=True, blank=True)
#     total_order_quantity = models.CharField(verbose_name="TOTAL_ORDER_QUANTITY", max_length=20, null=True, blank=True)
#     class Meta:
#         verbose_name_plural = "06. RAW_V_SALES_GOODS"

    
# class V_Sales_Price(models.Model):
#     goods_id = models.CharField(verbose_name="GOODS_ID", max_length=20, null=True, blank=True)
#     goods_name = models.CharField(verbose_name="GOODS_NAME", max_length=1000, null=True, blank=True)
#     model_code = models.CharField(verbose_name="MODEL_CODE", max_length=50, null=True, blank=True)
#     goods_model = models.CharField(verbose_name="GOODS_MODEL", max_length=20, null=True, blank=True)
#     color = models.CharField(verbose_name="COLOR", max_length=20, null=True, blank=True)
#     storage = models.CharField(verbose_name="STORAGE", max_length=20, null=True, blank=True)
#     sales_channel = models.CharField(verbose_name="SALES_CHANNEL", max_length=20, null=True, blank=True)
#     ssdc_color = models.CharField(verbose_name="SSDC_COLOR", max_length=20, null=True, blank=True)
#     ssgn_color = models.CharField(verbose_name="SSGN_COLOR", max_length=20, null=True, blank=True)
#     standard_price = models.CharField(verbose_name="STANDARD_PRICE", max_length=20, null=True, blank=True)
#     member_price = models.CharField(verbose_name="MEMBER_PRICE", max_length=20, null=True, blank=True)
#     benefit_price = models.CharField(verbose_name="BENEFIT_PRICE", max_length=20, null=True, blank=True)
#     discount_price = models.CharField(verbose_name="DISCOUNT_PRICE", max_length=20, null=True, blank=True)
#     receiving_method = models.CharField(verbose_name="RECEIVING_METHOD", max_length=50, null=True, blank=True)
#     stock_quantity = models.CharField(verbose_name="STOCK_QUANTITY", max_length=20, null=True, blank=True)
#     web_access = models.CharField(verbose_name="WEB_ACCESS", max_length=20, null=True, blank=True)
#     app_access = models.CharField(verbose_name="APP_ACCESS", max_length=20, null=True, blank=True)

#     class Meta:
#         verbose_name_plural = "07. RAW_V_SALES_PRICE"


# class V_Review_Goods(models.Model):
#     goods_id = models.CharField(verbose_name="GOODS_ID", max_length=20, null=True, blank=True)
#     goods_name = models.CharField(verbose_name="GOODS_NAME", max_length=1000, null=True, blank=True)
#     model_code = models.CharField(verbose_name="MODEL_CODE", max_length=50, null=True, blank=True)
#     goods_model = models.CharField(verbose_name="GOODS_MODEL", max_length=20, null=True, blank=True)
#     color = models.CharField(verbose_name="COLOR", max_length=20, null=True, blank=True)
#     storage = models.CharField(verbose_name="STORAGE", max_length=20, null=True, blank=True)
#     sales_channel = models.CharField(verbose_name="SALES_CHANNEL", max_length=20, null=True, blank=True)
#     ssdc_color = models.CharField(verbose_name="SSDC_COLOR", max_length=20, null=True, blank=True)
#     ssgn_color = models.CharField(verbose_name="SSGN_COLOR", max_length=20, null=True, blank=True)
#     avg_rating = models.CharField(verbose_name="AVG_RATING", max_length=20, null=True, blank=True)
#     total_review_cnt = models.CharField(verbose_name="TOTAL_REVIEW_CNT", max_length=20, null=True, blank=True)
#     rating_1_cnt = models.CharField(verbose_name="RATING_1_CNT", max_length=20, null=True, blank=True)
#     rating_2_cnt = models.CharField(verbose_name="RATING_2_CNT", max_length=20, null=True, blank=True)
#     rating_3_cnt = models.CharField(verbose_name="RATING_3_CNT", max_length=20, null=True, blank=True)
#     rating_4_cnt = models.CharField(verbose_name="RATING_4_CNT", max_length=20, null=True, blank=True)
#     rating_5_cnt = models.CharField(verbose_name="RATING_5_CNT", max_length=20, null=True, blank=True)

#     class Meta:
#         verbose_name_plural = "08. RAW_V_REVIEW_GOODS"


# class review_comment(models.Model):
#     product_id = models.CharField(verbose_name='product_id', max_length=20, null=True, blank=True)
#     product_type_level_1 = models.CharField(verbose_name='product_type_level_1', max_length=1000, null=True, blank=True)
#     product_type_level_2 = models.CharField(verbose_name='product_type_level_2', max_length=1000, null=True, blank=True)
#     product_fullname = models.CharField(verbose_name='product_fullname', max_length=1000, null=True, blank=True)
#     product_model_code = models.CharField(verbose_name='product_code', max_length=1000, null=True, blank=True)
#     product_model = models.CharField(verbose_name='product_model', max_length=1000, null=True, blank=True)
#     color = models.CharField(verbose_name='color', max_length=1000, null=True, blank=True)
#     storage = models.CharField(verbose_name='storage', max_length=1000, null=True, blank=True)
#     sales_channel = models.CharField(verbose_name='sales_channel', max_length=1000, null=True, blank=True)
#     ssdc_color = models.CharField(verbose_name='ssdc_color', max_length=1000, null=True, blank=True)
#     ssgn_color = models.CharField(verbose_name='ssgn_color', max_length=1000, null=True, blank=True)
#     rating = models.CharField(verbose_name="RATING", max_length=20, null=True, blank=True)
#     review = models.TextField(verbose_name="REVIEW", null=True, blank=True)
#     review_date= models.DateField(verbose_name="REVIEW_DATE", max_length=20, null=True, blank=True)
    
#     class Meta:
#         verbose_name_plural = "09. RAW_V_REVIEW_(null=True, blank=True, verbose_name"


# class product_spec(models.Model):
#     product_id = models.CharField(verbose_name='product_id', max_length=20, null=True, blank=True)
#     product_type_level_1 = models.CharField(verbose_name='product_type_level_1', max_length=1000, null=True, blank=True)
#     product_type_level_2 = models.CharField(verbose_name='product_type_level_2', max_length=1000, null=True, blank=True)
#     product_fullname = models.CharField(verbose_name='product_fullname', max_length=1000, null=True, blank=True)
#     product_model_code = models.CharField(verbose_name='product_code', max_length=1000, null=True, blank=True)
#     product_model = models.CharField(verbose_name='product_model', max_length=1000, null=True, blank=True)
#     color = models.CharField(verbose_name='color', max_length=1000, null=True, blank=True)
#     storage = models.CharField(verbose_name='storage', max_length=1000, null=True, blank=True)
#     sales_channel = models.CharField(verbose_name='sales_channel', max_length=1000, null=True, blank=True)
#     ssdc_color = models.CharField(verbose_name='ssdc_color', max_length=1000, null=True, blank=True)
#     ssgn_color = models.CharField(verbose_name='ssgn_color', max_length=1000, null=True, blank=True)
#     sales_start_datetime= models.DateTimeField(verbose_name='sales_start_datetime', max_length=1000, null=True, blank=True)
#     sales_end_datetime = models.DateTimeField(verbose_name='sales_end_datetime_datetime', max_length=1000, null=True, blank=True)
#     spec_type = models.CharField(verbose_name='spec_type', max_length=1000, null=True, blank=True)
#     spec_name = models.CharField(verbose_name='spec_name', max_length=1000, null=True, blank=True)
#     spec_value = models.CharField(verbose_name='spec_value', max_length=1000, null=True, blank=True)
#     business_unit = models.CharField(verbose_name='business_unit', max_length=1000, null=True, blank=True)
#     class Meta:
#         verbose_name_plural = "10. RAW_PRODUCT_SPEC"


# class store(models.Model):
#     store_name = models.CharField(verbose_name="store_name", max_length=50, null=True, blank=True)
#     store_type_code = models.CharField(verbose_name="store_type_code", max_length=50, null=True, blank=True)
#     address = models.CharField(verbose_name="address", max_length=1000, null=True, blank=True)
#     full_address = models.CharField(verbose_name="full address", max_length=1000, null=True, blank=True)
#     province = models.CharField(verbose_name="province", max_length=1000, null=True, blank=True)
#     city = models.CharField(verbose_name="city", max_length=1000, null=True, blank=True)
#     gu = models.CharField(verbose_name="gu", max_length=1000, null=True, blank=True)
#     parking = models.CharField(verbose_name="park", max_length=1000, null=True, blank=True)
#     bus = models.CharField(verbose_name="bus", max_length=1000, null=True, blank=True)
#     subway = models.CharField(verbose_name="subway", max_length=1000, null=True, blank=True)
#     taxi = models.CharField(verbose_name="taxi", max_length=1000, null=True, blank=True)
#     phone_number = models.CharField(verbose_name="phone_number", max_length=20, null=True, blank=True)
#     store_size = models.CharField(verbose_name="store_size", max_length=50, null=True, blank=True)
#     reservation_available = models.CharField(verbose_name="reservation_available", max_length=10, null=True, blank=True)
#     weekday_open_time = models.CharField(verbose_name="weekday_open_time", max_length=20, null=True, blank=True)
#     weekday_close_time = models.CharField(verbose_name="weekday_close_time", max_length=20, null=True, blank=True)
#     weekend_open_time = models.CharField(verbose_name="weekend_open_time", max_length=20, null=True, blank=True)
#     weekend_close_time = models.CharField(verbose_name="weekend_close_time", max_length=20, null=True, blank=True)
#     holiday_open_time = models.CharField(verbose_name="holiday_open_time", max_length=50, null=True, blank=True)
#     holiday_close_time = models.CharField(verbose_name="holiday_close_time", max_length=50, null=True, blank=True)
#     geo_data = models.CharField(verbose_name="geo_data", max_length=1000, null=True, blank=True)
#     geo_str2 = models.CharField(verbose_name="geo_str", max_length=1000, null=True, blank=True)
#     geo_str = gis_models.GeometryField(srid=4326, null=True)

#     class Meta:
#         verbose_name_plural = "11. RAW_STORE"

    
# class product_price(models.Model):
#     product_id = models.CharField(verbose_name='product_id', max_length=20, null=True, blank=True)
#     product_type_level_1 = models.CharField(verbose_name='product_type_level_1', max_length=1000, null=True, blank=True)
#     product_type_level_2 = models.CharField(verbose_name='product_type_level_2', max_length=1000, null=True, blank=True)
#     product_fullname = models.CharField(verbose_name='product_fullname', max_length=1000, null=True, blank=True)
#     product_model_code = models.CharField(verbose_name='product_code', max_length=1000, null=True, blank=True)
#     product_model = models.CharField(verbose_name='product_model', max_length=1000, null=True, blank=True)
#     color = models.CharField(verbose_name='color', max_length=1000, null=True, blank=True)
#     storage = models.CharField(verbose_name='storage', max_length=1000, null=True, blank=True)
#     sales_channel = models.CharField(verbose_name='sales_channel', max_length=1000, null=True, blank=True)
#     ssdc_color = models.CharField(verbose_name='ssdc_color', max_length=1000, null=True, blank=True)
#     ssgn_color = models.CharField(verbose_name='ssgn_color', max_length=1000, null=True, blank=True)
#     standard_price = models.CharField(verbose_name="standard_price", max_length=20, null=True, blank=True)
#     member_price = models.CharField(verbose_name="member_price", max_length=20, null=True, blank=True)
#     benefit_price = models.CharField(verbose_name="benefit_price", max_length=20, null=True, blank=True)
#     discount_price = models.CharField(verbose_name="discount_price", max_length=20, null=True, blank=True)
#     sales_start_datetime = models.DateTimeField(verbose_name='sales_start_datetime', max_length=1000, null=True, blank=True)
#     sales_end_datetime = models.DateTimeField(verbose_name='sales_end_datetime_datetime', max_length=1000, null=True, blank=True)
#     receiving_method = models.CharField(verbose_name="receiving_method", max_length=50, null=True, blank=True)
#     stock_quantity = models.CharField(verbose_name="stock_quantity", max_length=20, null=True, blank=True)
#     web_access = models.CharField(verbose_name="web_access", max_length=20, null=True, blank=True)
#     app_access = models.CharField(verbose_name="app_access", max_length=20, null=True, blank=True)
#     business_unit = models.CharField(verbose_name='business_unit', max_length=1000, null=True, blank=True)

#     class Meta:
#         verbose_name_plural = "12. RAW_PRODUCT_PRICE"


# class product_review(models.Model):
#     product_id = models.CharField(verbose_name='product_id', max_length=20, null=True, blank=True)
#     product_type_level_1 = models.CharField(verbose_name='product_type_level_1', max_length=1000, null=True, blank=True)
#     product_type_level_2 = models.CharField(verbose_name='product_type_level_2', max_length=1000, null=True, blank=True)
#     product_fullname = models.CharField(verbose_name='product_fullname', max_length=1000, null=True, blank=True)
#     product_model_code = models.CharField(verbose_name='product_code', max_length=1000, null=True, blank=True)
#     product_model = models.CharField(verbose_name='product_model', max_length=1000, null=True, blank=True)
#     color = models.CharField(verbose_name='color', max_length=1000, null=True, blank=True)
#     storage = models.CharField(verbose_name='storage', max_length=1000, null=True, blank=True)
#     sales_channel = models.CharField(verbose_name='sales_channel', max_length=1000, null=True, blank=True)
#     ssdc_color = models.CharField(verbose_name='ssdc_color', max_length=1000, null=True, blank=True)
#     ssgn_color = models.CharField(verbose_name='ssgn_color', max_length=1000, null=True, blank=True)
#     avg_rating = models.CharField(verbose_name="avg_rating", max_length=20, null=True, blank=True)
#     total_review_count = models.CharField(verbose_name="total_review_count", max_length=20, null=True, blank=True)
#     rating_1_count = models.CharField(verbose_name="rating_1_count", max_length=20, null=True, blank=True)
#     rating_2_count = models.CharField(verbose_name="rating_2_count", max_length=20, null=True, blank=True)
#     rating_3_count = models.CharField(verbose_name="rating_3_count", max_length=20, null=True, blank=True)
#     rating_4_count = models.CharField(verbose_name="rating_4_count", max_length=20, null=True, blank=True)
#     rating_5_count = models.CharField(verbose_name="rating_5_count", max_length=20, null=True, blank=True)

#     class Meta:
#         verbose_name_plural = "13. RAW_PRODUCT_REVIEW"

class unstructured_poc_pdf(models.Model):
    id_id = models.CharField(verbose_name='unstructured_id', max_length=100, null=True, blank=True)
    title = models.CharField(verbose_name='title')
    chunk = models.TextField(verbose_name='chunk')
    name = models.TextField(verbose_name='name')
    location = models.TextField(verbose_name='url link', null=True, blank=True)
    page_num = models.IntegerField(verbose_name='page number', null=True, blank = True)
    img_data = ArrayField(models.CharField(max_length=100), blank=True, null=True)
    created_on          = models.DateTimeField(verbose_name='Create', auto_now_add=True)
    updated_on          = models.DateTimeField(verbose_name='Update', auto_now=True)
    class Meta:
        verbose_name_plural = "14. POC_UNSTRUCTURED_PDF"


class unstructured_chat(models.Model):
    id_id = models.CharField(verbose_name='unstructured_id', max_length=100, null=True, blank=True)
    chunk = models.TextField(verbose_name='chunk')
    name = models.TextField(verbose_name='name')
    content = models.JSONField(verbose_name='query content')
    row_num = models.IntegerField(verbose_name='row', null=True, blank = True)
    page_num = models.IntegerField(verbose_name='page number', null=True, blank = True)
    location = models.TextField(verbose_name='url link', null=True, blank=True)
    answer = models.TextField(verbose_name='answer', null=True, blank=True)
    created_on          = models.DateTimeField(verbose_name='Create', auto_now_add=True)
    updated_on          = models.DateTimeField(verbose_name='Update', auto_now=True)
    class Meta:
        verbose_name_plural = "15. POC_UNSTRUCTURED_CHAT"


class display_category(models.Model):
    id                      = models.AutoField(primary_key=True)
    ACC_YN                  = models.CharField(max_length=1, null=True, blank=True, verbose_name="액세서리 여부")
    BND_NO                  = models.IntegerField(null=True, blank=True, verbose_name="브랜드 번호")
    COMP_NO                 = models.IntegerField(null=True, blank=True, verbose_name="업체 번호")
    CTA1_EN_NM              = models.CharField(max_length=100, null=True, blank=True, verbose_name="CTA1 영문 명")
    CTA1_LINK_URL           = models.CharField(max_length=200, null=True, blank=True, verbose_name="CTA1 링크 URL")
    CTA1_STYLE_CD           = models.CharField(max_length=1, null=True, blank=True, verbose_name="CTA1 스타일 코드")
    CTA2_EN_NM              = models.CharField(max_length=100, null=True, blank=True, verbose_name="CTA2 영문 명")
    CTA2_LINK_URL           = models.CharField(max_length=200, null=True, blank=True, verbose_name="CTA2 링크 URL")
    CTA2_STYLE_CD           = models.CharField(max_length=1, null=True, blank=True, verbose_name="CTA2 스타일 코드")
    CTA2_TEXT               = models.CharField(max_length=100, null=True, blank=True, verbose_name="CTA2 텍스트")
    DEL_YN                  = models.CharField(max_length=1, null=True, blank=True, verbose_name="삭제 여부")
    DISP_CLSF_CD            = models.CharField(max_length=10, null=True, blank=True, verbose_name="전시 분류 코드")
    DISP_CLSF_EN_NM         = models.CharField(max_length=200, null=True, blank=True, verbose_name="전시 분류 영문 명")
    DISP_CLSF_MO_NM         = models.CharField(max_length=100, null=True, blank=True, verbose_name="전시 분류 모바일 명")
    DISP_CLSF_NM            = models.CharField(max_length=100, null=True, blank=True, verbose_name="전시 분류 명")
    DISP_CLSF_NO            = models.CharField(max_length=100, null=True, blank=True, verbose_name="전시 분류 번호")
    DISP_ENDDT              = models.DateTimeField(null=True, blank=True, verbose_name="전시 종료일자")
    DISP_LVL                = models.IntegerField(null=True, blank=True, verbose_name="전시 레벨")
    DISP_PRIOR_RANK         = models.IntegerField(null=True, blank=True, verbose_name="전시 우선 순위")
    DISP_STRTDT             = models.DateTimeField(null=True, blank=True, verbose_name="전시 시작일자")
    DISP_TMPL_TP_CD         = models.CharField(max_length=10, null=True, blank=True, verbose_name="전시 템플릿 유형 코드")
    DISP_YN                 = models.CharField(max_length=1, null=True, blank=True, verbose_name="전시 여부")
    DUP_LINK_ICON_PATH      = models.CharField(max_length=100, null=True, blank=True, verbose_name="중복 링크 아이콘 경로")
    DUP_LINK_SET_YN         = models.CharField(max_length=1, null=True, blank=True, verbose_name="중복 링크 설정 여부")
    DUP_LINK_TEXT           = models.CharField(max_length=100, null=True, blank=True, verbose_name="중복 링크 텍스트")
    DUP_LINK_URL            = models.CharField(max_length=200, null=True, blank=True, verbose_name="중복 링크 URL")
    GNB_ALIGN_GB_CD         = models.CharField(max_length=1, null=True, blank=True, verbose_name="GNB 정렬 구분 코드")
    GNB_BADGE_COLOR         = models.CharField(max_length=20, null=True, blank=True, verbose_name="GNB 뱃지 색상")
    GNB_BADGE_TEXT          = models.CharField(max_length=50, null=True, blank=True, verbose_name="GNB 뱃지 텍스트")
    GNB_BADGE_USE_YN        = models.CharField(max_length=1, null=True, blank=True, verbose_name="GNB 뱃지 사용 여부")
    GNB_DIV_LINE_YN         = models.CharField(max_length=1, null=True, blank=True, verbose_name="GNB 구분선 여부")
    GNB_FONT_TP_CD          = models.CharField(max_length=10, null=True, blank=True, verbose_name="GNB 폰트 유형 코드")
    GNB_LOGO_IMG_PATH       = models.CharField(max_length=100, null=True, blank=True, verbose_name="GNB 로고 이미지 경로")
    GNB_LOGO_POS_CD         = models.CharField(max_length=10, null=True, blank=True, verbose_name="GNB 로고 위치 코드")
    GNB_LOGO_USE_YN         = models.CharField(max_length=1, null=True, blank=True, verbose_name="GNB 로고 사용 여부")
    GNB_TXT_COLOR_CD        = models.CharField(max_length=10, null=True, blank=True, verbose_name="GNB 텍스트 색상 코드")
    ITEM_DLVR_GB_CD         = models.CharField(max_length=2, null=True, blank=True, verbose_name="품목별 배송 구분 코드")
    LEAF_YN                 = models.CharField(max_length=1, null=True, blank=True, verbose_name="최하위 여부")
    LINK_URL                = models.CharField(max_length=200, null=True, blank=True, verbose_name="링크 URL")
    MENU_LINK_GB_CD         = models.CharField(max_length=10, null=True, blank=True, verbose_name="메뉴 링크 이동 구분 코드")
    MENU_SUB_TITLE          = models.CharField(max_length=100, null=True, blank=True, verbose_name="메뉴 서브 타이틀")
    MENU_TXT_COLOR          = models.CharField(max_length=10, null=True, blank=True, verbose_name="메뉴 텍스트 색상")
    MOBILE_YN               = models.CharField(max_length=1, null=True, blank=True, verbose_name="모바일 여부")
    MOUNTED_APP_DISP_YN     = models.CharField(max_length=1, null=True, blank=True, verbose_name="탑재 어플리케이션 전시 여부")
    NETFUNNEL_ACT_ID        = models.CharField(max_length=100, null=True, blank=True, verbose_name="넷퍼넬 ACT 아이디")
    NETFUNNEL_BNR_ACT_ID    = models.CharField(max_length=100, null=True, blank=True, verbose_name="넷퍼넬 배너 액션 아이디")
    NETFUNNEL_BNR_YN        = models.CharField(max_length=1, null=True, blank=True, verbose_name="넷퍼넬 배너 적용 여부")
    NETFUNNEL_YN            = models.CharField(max_length=1, null=True, blank=True, verbose_name="넷퍼넬 적용 여부")
    NEW_PRDT_YN             = models.CharField(max_length=1, null=True, blank=True, verbose_name="신제품 여부")
    RDRT_DISP_CLSF_NO       = models.IntegerField(null=True, blank=True, verbose_name="리다이렉트 전시 분류 번호")
    SAR_DISP_YN             = models.CharField(max_length=1, null=True, blank=True, verbose_name="SAR정보 전시 여부")
    SEO_NO                  = models.IntegerField(null=True, blank=True, verbose_name="SEO 번호")
    ST_ID                   = models.IntegerField(null=True, blank=True, verbose_name="사이트 아이디")
    SUB_MENU_GB_CD          = models.CharField(max_length=10, null=True, blank=True, verbose_name="하위 메뉴 구분 코드")
    TN_CTA_TEXT             = models.CharField(max_length=100, null=True, blank=True, verbose_name="썸네일 CTA 텍스트")
    TN_EN_NM                = models.CharField(max_length=100, null=True, blank=True, verbose_name="썸네일 영문 명")
    TN_IMG_ALT_TEXT         = models.CharField(max_length=500, null= True, blank=True, verbose_name="썸네일 이미지 ALT 텍스트")
    TN_IMG_PATH             = models.CharField(max_length=100, null=True, blank=True, verbose_name="썸네일 이미지 경로")
    TN_LINK_GB_CD           = models.CharField(max_length=10, null=True, blank=True, verbose_name="썸네일 링크 이동 구분 코드")
    TN_LINK_URL             = models.CharField(max_length=200, null=True, blank=True, verbose_name="썸네일 링크 URL")
    TN_MAIN_YN              = models.CharField(max_length=1, null=True, blank=True, verbose_name="썸네일 메인 여부")
    TN_MO_IMG_PATH          = models.CharField(max_length=100, null=True, blank=True, verbose_name="썸네일 모바일 이미지 경로")
    TN_TP_TXT               = models.CharField(max_length=50, null=True, blank=True, verbose_name="썸네일 타입 텍스트")
    TN_USE_YN               = models.CharField(max_length=1, null=True, blank=True, verbose_name="썸네일 사용 여부")
    UP_DISP_CLSF_NO         = models.IntegerField(null=True, blank=True, verbose_name="상위 전시 분류 번호")
    URL_INPUT_GB_CD         = models.CharField(max_length=10, null=True, blank=True, verbose_name="URL 입력 구분 코드")

    class Meta:
        verbose_name_plural = "16. DISPLAY_CATEGORY"
        db_table = 'rubicon_data_display_category'


class display_ctg_add_info(models.Model):
    ACCESSIBILITY_LINK      = models.CharField(max_length=500, verbose_name= "제품 접근성 LINK", null=True, blank=True)
    ACCESSIBILITY_YN        = models.CharField(max_length=100, verbose_name= "제품 접근성 사용 여부", null=True, blank = True)
    ADD_INFO_NO             = models.IntegerField(verbose_name= "추가 정보 번호", null=True, blank=True)
    CTA_NM                  = models.CharField(max_length=100, verbose_name= "CTA 명", null=True, blank=True)
    CTA_URL                 = models.CharField(max_length=100, verbose_name= "CTA URL", null=True, blank=True)
    CTA_USE_YN              = models.CharField(max_length=100, verbose_name= "CTA 사용여부", null=True, blank=True)
    CTG_ORD_LIMIT_END_DTM   = models.CharField(max_length=10, verbose_name= "카테고리 주문 제한 종료 일시", null=True, blank=True)
    CTG_ORD_LIMIT_QTY       = models.CharField(max_length=10, verbose_name= "카테고리 주문 제한 수량", null=True, blank=True)
    CTG_ORD_LIMIT_STRT_DTM  = models.CharField(max_length=10, verbose_name= "카테고리 주문 제한 시작 일시", null=True, blank=True)
    CTG_ORD_LIMIT_USE_YN    = models.CharField(max_length=100, verbose_name= "카테고리 주문 제한 사용 여부", null=True, blank=True)
    DISCLAIMER              = models.TextField(verbose_name= "Disclaimer", null=True, blank=True)
    DISP_CLSF_NO            = models.IntegerField(verbose_name= "전시 분류 번호", null=True, blank=True)
    SALE_PRC_CCLT_RATE      = models.IntegerField(verbose_name= "판매 가격 산출 율", null=True, blank=True)
    URL_NM                  = models.CharField(max_length=500, verbose_name= "URL", null=True, blank=True)
    URL_NM_GB_CD            = models.IntegerField(verbose_name= "URL Name 구분 코드", null=True, blank=True)

    class Meta:
        verbose_name_plural = "17. DISPLAY_CTG_ADD_INFO"
        db_table = 'rubicon_data_display_ctg_add_info' 


   
class display_goods(models.Model):
    DISP_CLSF_NO            = models.IntegerField(verbose_name= "전시 분류 번호", null=True, blank=True)
    DISP_PRIOR_RANK         = models.IntegerField(verbose_name= "전시 우선 순위", null=True, blank=True)
    DLGT_DISP_YN            = models.CharField(max_length=1, verbose_name= "대표 전시 여부", null=True, blank=True)
    GOODS_ID                = models.CharField(max_length=15, verbose_name= "상품 번호", null=True, blank=True)
    STK_EXCPT_YN            = models.CharField(max_length=1, verbose_name= "재고 예외 여부", null=True, blank=True)

    class Meta:
        verbose_name_plural = "18. DISPLAY_GOODS"
        db_table = 'rubicon_data_display_goods' 


class goods_add_column_info(models.Model):
    COL_VAL1                = models.TextField(verbose_name= "컬럼 값1", null=True, blank=True)
    COL_VAL2                = models.TextField(verbose_name= "컬럼 값2", null=True, blank=True)
    COL_VAL3                = models.TextField(verbose_name= "컬럼 값3", null=True, blank=True)
    COL_VAL4                = models.TextField(verbose_name= "컬럼 값4", null=True, blank=True)
    GOODS_COL_GB_CD         = models.CharField(max_length=10, verbose_name= "상품 컬럼 구분 코드 (code_detail.dtl_cd = GOODS_COL_GB)", null=True, blank=True)
    GOODS_ID                = models.CharField(max_length=15, verbose_name= "상품 아이디", null=True, blank=True)
    USE_YN                  = models.CharField(max_length=1, verbose_name= "사용 여부", null=True, blank=True)

    class Meta:
        verbose_name_plural = "19. DISPLAY_ADD_COLUMNS_INFO"
        db_table = 'rubicon_data_display_add_columns_info'

class goods_base_product(models.Model):
    ADV_VST_CD              = models.CharField(max_length=15, verbose_name= "사전 방문 코드", null=True, blank=True)
    ARCN_YN                 = models.CharField(max_length=1, verbose_name= "에어컨 여부", null=True, blank=True)
    BIGO                    = models.CharField(max_length=1000, verbose_name= "비고", null=True, blank=True)
    BND_NO                  = models.IntegerField(verbose_name= "브랜드 번호", null=True, blank=True)
    BSPK_GOODS_YN           = models.CharField(max_length=1, verbose_name= "비스포크 상품 여부", null=True, blank=True)
    COMP_GOODS_ID           = models.CharField(max_length=50, verbose_name= "업체 상품 아이디", null=True, blank=True)
    COMP_NO                 = models.IntegerField(verbose_name= "업체 번호", null=True, blank=True)
    COMP_PLC_NO             = models.IntegerField(verbose_name= "업체 정책 번호", null=True, blank=True)
    CTR_ORG                 = models.CharField(max_length=100, verbose_name= "원산지", null=True, blank=True)
    CUSTOM_GOODS_YN         = models.CharField(max_length = 1, verbose_name= "커스텀 상품 여부", null=True, blank=True) 
    DLVRC_PLC_NO            = models.IntegerField(verbose_name= "배송 정책 번호", null=True, blank=True)
    DLVR_GEN_YN             = models.CharField(max_length=1, verbose_name= "배송 일반 여부", null=True, blank=True)
    DLVR_IST_YN             = models.CharField(max_length=1, verbose_name= "배송 설치 여부", null=True, blank=True)
    DLVR_ITDC_WDS           = models.CharField(max_length=1000, verbose_name= "배송 안내 문구", null=True, blank=True)
    DLVR_MTD_CD             = models.CharField(max_length=10, verbose_name= "배송 방법 코드", null=True, blank=True)
    DLVR_OPT_CD             = models.CharField(max_length=10, verbose_name= "배송 옵션 코드", null=True, blank=True)
    DLVR_PCK_YN             = models.CharField(max_length=1, verbose_name= "배송 픽업 여부", null=True, blank=True)
    DLVR_PLNT_CD            = models.CharField(max_length=10, verbose_name= "Delivering Plant 코드", null=True, blank=True)
    DLVR_WKPL_PCK_YN        = models.CharField(max_length=1, verbose_name= "배송 사업장 픽업 여부", null=True, blank=True)
    DOOR_DRCT_YN            = models.CharField(max_length=1, verbose_name= "도어 방향 여부", null=True, blank=True)
    ERP_DC_AUTO_CAL_YN      = models.CharField(max_length=1, verbose_name= "ERP 할인 자동 계산 여부", null=True, blank=True)
    ERP_DC_PRC              = models.FloatField(verbose_name= "ERP 할인 가격", null=True, blank=True)
    ERP_OO_PRC              = models.FloatField(verbose_name= "ERP 출고 가격", null=True, blank=True)
    ERP_PRC_CHG_APL_YN      = models.CharField(max_length=10, verbose_name= "ERP 가격 변경 젹용 여부", null=True, blank=True)
    ERP_SPL_PRC             = models.FloatField(verbose_name= "ERP 공급 가격", null=True, blank=True)
    FREE_DLVR_YN            = models.CharField(max_length=1, verbose_name= "무료 배송 여부", null=True, blank=True)
    GERP_AMT                = models.FloatField(verbose_name= "금액1", null=True, blank=True)
    GERP_LNK_YN             = models.CharField(max_length=1, verbose_name= "GERP 연동 여부", null=True, blank=True)
    GOODS_ID                = models.CharField(max_length=15, verbose_name= "상품 아이디", null=True, blank=True)
    GOODS_NM                = models.CharField(max_length=300, verbose_name= "상품 명", null=True, blank=True)
    GOODS_STAT_CD           = models.CharField(max_length=10, verbose_name= "상품 상태 코드", null=True, blank=True)
    GOODS_TP_CD             = models.CharField(max_length=10, verbose_name= "상품 유형 코드", null=True, blank=True)
    GOODS_TP_SUB_CD         = models.CharField(max_length=10, verbose_name= "상품 유형 서브 코드", null=True, blank=True)
    GRBG_PU_YN              = models.CharField(max_length=1, verbose_name= "폐가전 수거 여부", null=True, blank=True)
    HITS                    = models.IntegerField(verbose_name= "조회수", null=True, blank=True)
    IMPORTER                = models.CharField(max_length=200, verbose_name= "수입사", null=True, blank=True)
    ITEM_MNG_YN             = models.CharField(max_length=1, verbose_name= "단품 관리 여부", null=True, blank=True)
    KWD                     = models.CharField(max_length=4000, verbose_name= "키워드", null=True, blank=True)
    LMT_FLG_YN              = models.CharField(max_length=1, verbose_name= "한정 플래그 여부", null=True, blank=True)
    MAX_ORD_QTY             = models.FloatField(verbose_name= "최대 주문 수량", null=True, blank=True)
    MCDG_TXT                = models.CharField(max_length=1000, verbose_name= "머천다이징 텍스트", null=True, blank=True)
    MCDG_TXT2               = models.CharField(max_length=1000, verbose_name= "머천다이징 텍스트2", null=True, blank=True)
    MCDG_TXT3               = models.CharField(max_length=1000, verbose_name= "머천다이징 텍스트3", null=True, blank=True)
    MDL_CODE                = models.CharField(max_length=100, verbose_name= "모델 코드", null=True, blank=True)
    MDL_NM                  = models.CharField(max_length=200, verbose_name= "모델 명", null=True, blank=True)
    MD_USR_NO               = models.IntegerField(verbose_name= "MD 사용자 번호", null=True, blank=True)
    MHDJ_TG_YN              = models.CharField(max_length=1, verbose_name= "무한도전 대상 여부", null=True, blank=True)
    MID1                    = models.CharField(max_length=20, verbose_name= "MID1", null=True, blank=True)
    MID1_END_DTM            = models.DateTimeField(verbose_name= "MID1 종료 일시", null=True, blank=True)
    MID1_STRT_DTM           = models.DateTimeField(verbose_name= "MID1 시작 일시", null=True, blank=True)
    MID2                    = models.CharField(max_length=20, verbose_name= "MID2", null=True, blank=True)
    MID2_END_DTM            = models.DateTimeField(verbose_name= "MID2 종료 일시", null=True, blank=True)
    MID2_STRT_DTM           = models.DateTimeField(verbose_name= "MID2 시작 일시", null=True, blank=True)
    MIN_ORD_QTY             = models.FloatField(verbose_name= "최소 주문 수량", null=True, blank=True)
    MMFT                    = models.CharField(max_length=200, verbose_name= "제조사", null=True, blank=True)
    NEWPRDT_FLG_YN          = models.CharField(max_length=1, verbose_name= "신제품 플래그 여부", null=True, blank=True)
    NTF_ID                  = models.CharField(max_length=10, verbose_name= "고시 아이디", null=True, blank=True)
    ONLINE_STORE_ONLY_YN    = models.CharField(max_length=1, verbose_name= "온라인 전용 상품 여부", null=True, blank=True)
    PPLRTPRDT_FLG_YN        = models.CharField(max_length=1, verbose_name= "인기제품 플래그 여부", null=True, blank=True)
    PPLRT_RANK              = models.FloatField(verbose_name= "인기 순위", null=True, blank=True)
    PPLRT_SET_CD            = models.CharField(max_length=10, verbose_name= "인기 설정 코드", null=True, blank=True)
    PRPSN_ORD_LMT_END_DTM   = models.DateTimeField(verbose_name= "1인당 구매 제한 종료 일시", null=True, blank=True)
    PRPSN_ORD_LMT_QTY       = models.FloatField(verbose_name= "1인당 구매 제한 수량", null=True, blank=True)
    PRPSN_ORD_LMT_STRT_DTM  = models.DateTimeField(verbose_name= "1인당 구매 제한 시작 일시", null=True, blank=True)
    PR_WDS                  = models.CharField(max_length=1000, verbose_name= "홍보 문구", null=True, blank=True)
    PR_WDS_SHOW_YN          = models.CharField(max_length=1, verbose_name= "홍보 문구 노출 여부", null=True, blank=True)
    RGLR_DLVR_CYCL          = models.CharField(max_length=100, verbose_name= "정기 배송 주기", null=True, blank=True)
    RGLR_DLVR_DCRATE        = models.FloatField(verbose_name= "정기 배송 할인율", null=True, blank=True)
    RGLR_DLVR_YN            = models.CharField(max_length=1, verbose_name= "정기 배송 여부", null=True, blank=True)
    RSV_CUS_PSB_YN          = models.CharField(max_length=1, verbose_name= "예약 상담 가능 여부", null=True, blank=True)
    RSV_ORD_APL_QTY         = models.FloatField(verbose_name= "예약 주문 적용 수량", null=True, blank=True)
    RSV_ORD_DLVR_DT         = models.DateField(verbose_name= "예약 주문 배송 일자", null=True, blank=True)
    RSV_ORD_END_DTM         = models.DateTimeField(verbose_name= "예약 주문 종료 일시", null=True, blank=True)
    RSV_ORD_LMT_QTY         = models.FloatField(verbose_name= "예약 주문 제한 수량", null=True, blank=True)
    RSV_ORD_PRD_SHOW_YN     = models.CharField(max_length=1, verbose_name= "예약 주문 기간 노출 여부", null=True, blank=True)
    RSV_ORD_STRT_DTM        = models.DateTimeField(verbose_name= "예약 주문 시작 일시", null=True, blank=True)
    RSV_ORD_YN              = models.CharField(max_length=1, verbose_name= "예약 주문 여부", null=True, blank=True)
    RTN_MSG                 = models.CharField(max_length=4000, verbose_name= "반품 메세지", null=True, blank=True)
    RTN_PSB_YN              = models.CharField(max_length=1, verbose_name= "반품 가능 여부", null=True, blank=True)
    SALE_END_DTM            = models.DateTimeField(verbose_name= "판매 종료 일시", null=True, blank=True)
    SALE_STRT_DTM           = models.DateTimeField(verbose_name= "판매 시작 일시", null=True, blank=True)
    SEO_NO                  = models.IntegerField(verbose_name= "SEO 번호", null=True, blank=True)
    SHOW_STRT_DT            = models.DateField(verbose_name= "노출 시작 일자", null=True, blank=True)
    SHOW_STRT_DTM           = models.DateTimeField(verbose_name= "노출 시작 일시", null=True, blank=True)
    SHOW_YN                 = models.CharField(max_length=1, verbose_name= "노출 여부", null=True, blank=True)
    SO_CRT_EXCPT_YN         = models.CharField(max_length=1, verbose_name= "SO 생성 제외 여부", null=True, blank=True)
    STK_MNG_YN              = models.CharField(max_length=1, verbose_name= "재고 관리 여부", null=True, blank=True)
    SYS_REGR_NO             = models.IntegerField(verbose_name= "시스템 등록자 번호", null=True, blank=True)
    SYS_REG_DTM             = models.DateTimeField(verbose_name= "시스템 등록 일시", null=True, blank=True)
    SYS_UPDR_NO             = models.IntegerField(verbose_name= "시스템 수정자 번호", null=True, blank=True)
    SYS_UPD_DTM             = models.DateTimeField(verbose_name= "시스템 수정 일시", null=True, blank=True)
    TAX_GB_CD               = models.CharField(max_length=10, verbose_name= "과세 구분 코드", null=True, blank=True)
    UNSOLD_TP_CD            = models.CharField(max_length=10, verbose_name= "미판매 유형 코드", null=True, blank=True)
    USE_STK_CD              = models.CharField(max_length=10, verbose_name= "사용 재고 코드", null=True, blank=True)
    VD_LINK_URL             = models.CharField(max_length=500, verbose_name= "동영상 링크 URL", null=True, blank=True)
    WATCH_GOODS_YN          = models.CharField(max_length=1, verbose_name= "워치 상품 여부", null=True, blank=True)
    WATCH_SHOW_YN           = models.CharField(max_length=1, verbose_name= "워치 노출 여부", null=True, blank=True)
    WEB_MOBILE_GB_CD        = models.CharField(max_length=10, verbose_name= "웹 모바일 구분 코드", null=True, blank=True)

    class Meta:
        verbose_name_plural = "20. GOODS_BASE_PRODUCT"
        db_table = 'rubicon_data_goods_base_product'


class goods_grp_key_info(models.Model):
    GRP_KEY_NM              = models.CharField(max_length = 300, verbose_name= "그룹 키 명", null=True, blank=True)
    GRP_KEY_NO              = models.IntegerField(verbose_name= "그룹 키 번호", null=True, blank=True)
    GRP_KEY_TP_CD           = models.CharField(max_length=10, verbose_name= "그룹 키 유형 코드", null=True, blank=True)
    ST_ID                   = models.IntegerField(verbose_name= "사이트 아이디", null=True, blank=True)
    SYS_REG_DTM             = models.DateTimeField(verbose_name= "시스템 등록 일시", null=True, blank=True)
    SYS_UPD_DTM             = models.DateTimeField(verbose_name= "시스템 수정 일시", null=True, blank=True)
    DISP_PRIOR_RANK         = models.IntegerField(verbose_name= "전시 우선 순위", null=True, blank=True)
    DLGT_DISP_YN            = models.CharField(max_length = 1, verbose_name= "대표여부", null=True, blank=True)
    GOODS_ID                = models.CharField(max_length = 15, verbose_name= "상품 아이디", null=True, blank=True)
    GRP_KEY_NO              = models.IntegerField(verbose_name= "그룹 키 번호", null=True, blank=True)
    SYS_REG_DTM             = models.DateTimeField(verbose_name= "시스템 등록 일시", null=True, blank=True)
    SYS_UPD_DTM             = models.DateTimeField(verbose_name= "시스템 수정 일시", null=True, blank=True)
    COLOR_DISP_YN           = models.CharField(max_length = 1, verbose_name= "컬러 전시 여부", null=True, blank=True)
    DISP_OPT_NM             = models.CharField(max_length=50, verbose_name= "전시 옵션 명", null=True, blank=True)
    GOODS_ID                = models.CharField(max_length = 15, verbose_name= "상품 아이디", null=True, blank=True)
    PRDT_OPT_ITEM_NO        = models.IntegerField(verbose_name= "제품 옵션 아이템 번호", null=True, blank=True)
    SYS_REG_DTM             = models.DateTimeField(verbose_name= "시스템 등록 일시", null=True, blank=True)

    class Meta:
        verbose_name_plural = "21. GOODS_GRP_KEY_INFO"
        db_table = 'rubicon_data_goods_grp_key_info'


class goods_price(models.Model):
    AMT1                    = models.FloatField(verbose_name= "금액1", null=True, blank=True)
    AMT2                    = models.FloatField(verbose_name= "금액2", null=True, blank=True)
    AMT3                    = models.FloatField(verbose_name= "금액3", null=True, blank=True)
    BULK_ORD_END_YN         = models.CharField(max_length=1, verbose_name= "공동구매 종료 여부", null=True, blank=True)
    CMS_RATE                = models.FloatField(verbose_name= "수수료 율", null=True, blank=True)
    DC_GB_CD                = models.CharField(max_length=10, verbose_name= "할인 구분 코드", null=True, blank=True)
    DC_QTY1                 = models.FloatField(verbose_name= "할인 수량1", null=True, blank=True)
    DC_QTY2                 = models.FloatField(verbose_name= "할인 수량2", null=True, blank=True)
    DEL_YN                  = models.CharField(max_length=1, verbose_name= "삭제 여부", null=True, blank=True)
    FVR_APL_METH_CD         = models.CharField(max_length=10, verbose_name= "혜택 적용 방식 코드", null=True, blank=True)
    FVR_VAL                 = models.FloatField(verbose_name= "혜택 값", null=True, blank=True)
    GOODS_AMT_TP_CD         = models.CharField(max_length=10, verbose_name= "상품 금액 유형 코드", null=True, blank=True)
    GOODS_ID                = models.CharField(max_length = 15, verbose_name= "상품 아이디", null=True, blank=True)
    GOODS_PRC_NO            = models.IntegerField(verbose_name= "상품 가격 번호", null=True, blank=True)
    MIN_ORD_QTY             = models.FloatField(verbose_name= "최소 구매 수량", null=True, blank=True)
    ORG_SALE_AMT            = models.FloatField(verbose_name= "원 판매 금액", null=True, blank=True)
    SALE_AMT                = models.FloatField(verbose_name= "판매 금액", null=True, blank=True)
    SALE_END_DTM            = models.DateTimeField(verbose_name= "판매 종료 일시", null=True, blank=True)
    SALE_PRC1               = models.FloatField(verbose_name= "판매 가격1", null=True, blank=True)
    SALE_PRC2               = models.FloatField(verbose_name= "판매 가격2", null=True, blank=True)
    SALE_PRC3               = models.FloatField(verbose_name= "판매 가격3", null=True, blank=True)
    SALE_PRC4               = models.FloatField(verbose_name= "판매 가격4", null=True, blank=True)
    SALE_STRT_DTM           = models.DateTimeField(verbose_name= "판매 시작 일시", null=True, blank=True)
    SPL_AMT                 = models.FloatField(verbose_name= "공급 금액", null=True, blank=True)
    STRT_ORD_QTY            = models.FloatField(verbose_name= "초기 구매 수량", null=True, blank=True)
    ST_ID                   = models.IntegerField(verbose_name= "사이트 아이디", null=True, blank=True)
    SYS_REG_DTM             = models.DateTimeField(verbose_name= "시스템 등록 일시", null=True, blank=True)
    SYS_UPD_DTM             = models.DateTimeField(verbose_name= "시스템 수정 일시", null=True, blank=True)
    TRGT_QTY                = models.FloatField(verbose_name= "목표 수량", null=True, blank=True)

    class Meta:
        verbose_name_plural = "22. GOODS_PRICE"
        db_table = 'rubicon_data_goods_price'


class goods_spec_info_product(models.Model):
    ATTR_ID                 = models.CharField(max_length=40, verbose_name= "항목 아이디", null=True, blank=True)   
    ATTR_NM                 = models.CharField(max_length=1000, verbose_name= "항목 명", null=True, blank=True)
    DISP_LVL                = models.IntegerField(verbose_name= "전시 레벨", null=True, blank=True)
    MDL_CODE                = models.CharField(max_length=100, verbose_name= "모델 코드", null=True, blank=True)
    PS_VER                  = models.CharField(max_length=10, verbose_name= "스펙 버전", null=True, blank=True)
    SEQ                     = models.FloatField(verbose_name= "순번", null=True, blank=True)
    SGL_SCHEMA_ID           = models.CharField(max_length=40, verbose_name= "싱글 스키마 아이디", null=True, blank=True)
    SORT_SEQ                = models.FloatField(verbose_name= "정렬 순서", null=True, blank=True)
    SPEC_STAT_CD            = models.CharField(max_length=10, verbose_name= "스펙 상태 코드", null=True, blank=True)
    SPEC_VALUE              = models.CharField(max_length=2000, verbose_name= "스펙 값", null=True, blank=True)
    STD_SCHEMA_ID           = models.CharField(max_length=40, verbose_name= "표준 스키마 아이디", null=True, blank=True)
    STD_SCHEMA_KEY          = models.CharField(max_length=40, verbose_name= "표준 스키마 항목 키", null=True, blank=True)
    SYMBOL                  = models.CharField(max_length=30, verbose_name= "스펙 단위 명", null=True, blank=True)
    SYS_REG_DTM             = models.DateTimeField(verbose_name= "시스템 등록 일시", null=True, blank=True)
    SYS_UPD_DTM             = models.DateTimeField(verbose_name= "시스템 수정 일시", null=True, blank=True)
    UOM_SPACE               = models.CharField(max_length=1, verbose_name= "단위 공백포함 여부", null=True, blank=True)

    class Meta:
        verbose_name_plural = "23. GOODS_SPEC_INFO_PRODUCT"
        db_table = 'rubicon_data_goods_spec_info_product'


class plaza_base(models.Model):
    BAEMIN_STR_YN           = models.CharField(max_length = 1, verbose_name= "배민 매장 여부", null=True, blank=True)
    BIZ_REG_NO              = models.CharField(verbose_name= "사업자 등록 번호", null=True, blank=True)
    BLOG_URL                = models.CharField(max_length=100, verbose_name= "블로그 U", null=True, blank=True)
    BRANCH_CD               = models.CharField(max_length=10, verbose_name= "지사 코드", null=True, blank=True)
    BUILTIN_YN              = models.CharField(max_length=1, verbose_name= "빌트인 여부", null=True, blank=True)
    CEO_NM                  = models.CharField(max_length=100, verbose_name= "대표자 명", null=True, blank=True)
    CITY_CD                 = models.CharField(max_length=10, verbose_name= "시/도 코드", null=True, blank=True)
    CLOSED_DAY              = models.CharField(max_length=300, verbose_name= "휴점일", null=True, blank=True)
    CLOSE_YN                = models.CharField(max_length = 1, verbose_name= "폐업 여부", null=True, blank=True)
    CUS_RSV_YN              = models.CharField(max_length = 1, verbose_name= "상담 예약 가능 여부", null=True, blank=True)
    DTRT_CD                 = models.CharField(max_length=10, verbose_name= "구/군 코드", null=True, blank=True)
    ECAR_CHRG_STA_YN        = models.CharField(max_length = 1, verbose_name= "전기차 충전소 여부", null=True, blank=True)
    FAX                     = models.CharField(max_length=20,  verbose_name= "팩스", null=True, blank=True)
    GC_YN                   = models.CharField(max_length = 1, verbose_name= "갤럭시 컨설턴트 유무", null=True, blank=True)
    HARMAN_STUDIO_YN        = models.CharField(max_length = 1, verbose_name= "하만 스튜디오 여부", null=True, blank=True)
    LITD                    = models.CharField(max_length=20,  verbose_name= "경도", null=True, blank=True)
    LTTD                    = models.CharField(max_length=20,  verbose_name= "위도", null=True, blank=True)
    MC_YN                   = models.CharField(max_length = 1, verbose_name= "모바일 상담사 유무", null=True, blank=True)
    OMS_SEND_YN             = models.CharField(max_length = 1, verbose_name= "OMS 전송 여부", null=True, blank=True)
    OPEN_DT                 = models.CharField(max_length = 8, verbose_name= "오픈 일자", null=True, blank=True)
    PATH_TP_CD              = models.CharField(max_length=10, verbose_name= "경로 유형 코드", null=True, blank=True)
    PICKUP_YN               = models.CharField(max_length = 1, verbose_name= "픽업 가능 여부", null=True, blank=True)
    PLANT_CODE              = models.CharField(max_length=4, verbose_name= "물류 코드", null=True, blank=True)
    PLAZA_CODE              = models.CharField(max_length=4, verbose_name= "사업장 코드", null=True, blank=True)
    PLAZA_IMG_PATH          = models.CharField(max_length=100, verbose_name= "매장 이미지 경로", null=True, blank=True)
    PLAZA_INFO              = models.CharField(max_length=500, verbose_name= "매장 소개", null=True, blank=True)
    PLAZA_KIND_CD           = models.CharField(max_length=10, verbose_name= "매장 종류 코드", null=True, blank=True)
    PLAZA_MO_IMG_PATH       = models.CharField(max_length=100, verbose_name= "매장 모바일 이미지 경로", null=True, blank=True)
    PLAZA_NM                = models.CharField(max_length=200, verbose_name= "매장 명", null=True, blank=True)
    PLAZA_NO                = models.IntegerField(verbose_name= "매장 번호", null=True, blank=True)
    PLAZA_SCALE             = models.IntegerField(verbose_name= "매장 규모", null=True, blank=True)
    PLAZA_TP_CD             = models.CharField(max_length=10, verbose_name= "매장 유형 코드", null=True, blank=True)
    POST_CD                 = models.CharField(max_length=10, verbose_name= "지역 코드", null=True, blank=True)
    POST_NEW                = models.CharField(max_length=7, verbose_name= "우편번호 신", null=True, blank=True)
    POST_OLD                = models.CharField(max_length=7, verbose_name= "우편번호 구", null=True, blank=True)
    PRCL_ADDR               = models.CharField(max_length=500, verbose_name= "지번 주소", null=True, blank=True)
    PRCL_DTL_ADDR           = models.CharField(max_length=500, verbose_name= "지번 상세 주소", null=True, blank=True)
    PRC_SHOW_YN             = models.CharField(max_length = 1, verbose_name= "가격 표시제 여부", null=True, blank=True)
    PRIMIERE_YN             = models.CharField(max_length = 1, verbose_name= "PRIMIERE 여부", null=True, blank=True)
    PUBLIC_YN               = models.CharField(max_length = 1, verbose_name= "공개 여부", null=True, blank=True)
    ROAD_ADDR               = models.CharField(max_length=100, verbose_name= "도로명 주소", null=True, blank=True)
    ROAD_DTL_ADDR           = models.CharField(max_length=500, verbose_name= "도로명 상세 주소", null=True, blank=True)
    SAMSUNG_CARE_YN         = models.CharField(max_length=1, verbose_name= "SAMSUNG CARE 여부", null=True, blank=True)
    SHOP_NO                 = models.CharField(max_length=15, verbose_name= "거래선 코드", null=True, blank=True)
    SHOW_YN                 = models.CharField(max_length = 1, verbose_name= "노출 여부", null=True, blank=True)
    SVC_CENTER_YN           = models.CharField(max_length = 1, verbose_name= "서비스 센터 유무", null=True, blank=True)
    SVC_CLOSED_DAY          = models.CharField(max_length=300,  verbose_name= "서비스센터 휴점일", null=True, blank=True)
    SVC_IMG_PATH            = models.CharField(max_length=100, verbose_name= "서비스센터 이미지 경로", null=True, blank=True)
    SVC_INFO                = models.CharField(max_length=500, verbose_name= "서비스센터 소개", null=True, blank=True)
    SVC_MO_IMG_PATH         = models.CharField(max_length=100, verbose_name= "서비스센터 모바일 이미지 경로", null=True, blank=True)
    SVC_NM                  = models.CharField(max_length=200, verbose_name= "서비스센터 명", null=True, blank=True)
    SVC_PRDT_INFO           = models.CharField(max_length=500, verbose_name= "서비스 제품 안내", null=True, blank=True)
    SVC_TEL                 = models.CharField(max_length=20,  verbose_name= "서비스센터 전화번호", null=True, blank=True)
    SVC_WEEKDAY_CLOSE_TIME              = models.CharField(max_length=4, verbose_name= "서비스센터 평일 마감 시간", null=True, blank=True)
    SVC_WEEKDAY_OPEN_TIME               = models.CharField(max_length=4, verbose_name= "서비스센터 평일 오픈 시간", null=True, blank=True)
    SVC_WEEKEND_CLOSE_TIME              = models.CharField(max_length=4, verbose_name= "서비스센터 주말 마감 시간", null=True, blank=True)
    SVC_WEEKEND_OPEN_TIME               = models.CharField(max_length=4, verbose_name= "서비스센터 주말 오픈 시간", null=True, blank=True)
    TAX_RFD_YN                      = models.CharField(max_length = 1, verbose_name= "세금 환불 여부", null=True, blank=True)
    TEL                             = models.CharField(max_length=20,  verbose_name= "전화", null=True, blank=True)
    VD_CUS_RSV_YN                   = models.CharField(max_length = 1, verbose_name= "동영상 상담 예약 가능 여부", null=True, blank=True)
    WEEKDAY_CLOSE_TIME              = models.CharField(max_length=4, verbose_name= "평일 마감 시간", null=True, blank=True)
    WEEKDAY_OPEN_TIME               = models.CharField(max_length=4, verbose_name= "평일 오픈 시간", null=True, blank=True)
    WEEKEND_CLOSE_TIME              = models.CharField(max_length=4, verbose_name= "주말 마감 시간", null=True, blank=True)
    WEEKEND_OPEN_TIME               = models.CharField(max_length=4, verbose_name= "주말 오픈 시간", null=True, blank=True)
    WITH_PET_STR_YN                 = models.CharField(max_length = 1, verbose_name= "펫 동행 매장 여부", null=True, blank=True)

    class Meta:
        verbose_name_plural = "24. PLAZA_BASE"
        db_table = 'rubicon_data_plaza_base'


class recommend_display_goods(models.Model):
    DISP_CLSF_NO                    = models.IntegerField(verbose_name= "전시 분류 번호", null=True, blank=True)
    DISP_PRIOR_RANK                 = models.IntegerField(verbose_name= "전시 우선 순위", null=True, blank=True)
    DLGT_DISP_YN                    = models.CharField(max_length=1, verbose_name= "전시 우선 여부", null=True, blank=True)
    GOODS_ID                        = models.CharField(max_length=15, verbose_name= "상품 번호", null=True, blank=True)
    SYS_REG_DTM                     = models.DateTimeField(verbose_name= "시스템 등록 일시", null=True, blank=True)
    SYS_UPD_DTM                     = models.DateTimeField(verbose_name= "시스템 수정 일시", null=True, blank=True)
    class Meta:
        verbose_name_plural = "25. RECOMMEND_DISPLAY_GOODS"
        db_table = 'rubicon_data_recommend_display_goods'


class event_base(models.Model):
    APL_END_DTM                     = models.DateTimeField(verbose_name= "적용 종료 일시", null=True, blank=True)
    APL_STRT_DTM                    = models.DateTimeField(verbose_name= "적용 시작 일시", null=True, blank=True)
    CONTENT                         = models.TextField(verbose_name= "내용", null=True, blank=True)
    DISP_STRT_DTM                   = models.DateTimeField(verbose_name= "전시 시작 일시", null=True, blank=True)
    DLGT_IMG_PATH                   = models.CharField(max_length=150, verbose_name= "대표 이미지 경로", null=True, blank=True)
    ENTRY_END_DTM                   = models.DateTimeField(verbose_name= "응모 종료 일시", null=True, blank=True)
    ENTRY_STRT_DTM                  = models.DateTimeField(verbose_name= "응모 시작 일시", null=True, blank=True)
    EVENT_BNFTS                     = models.CharField(max_length=200, verbose_name= "이벤트 혜택", null=True, blank=True)
    EVENT_DSCRT                     = models.CharField(max_length=1000, verbose_name= "이벤트 설명", null=True, blank=True)
    EVENT_GB_CD                     = models.CharField(max_length=10, verbose_name= "이벤트 구분 코드", null=True, blank=True)
    EVENT_NO                        = models.IntegerField(verbose_name= "이벤트 번호", null=True, blank=True)
    EVENT_PRIOR_RANK                = models.IntegerField(verbose_name= "이벤트 우선 순위", null=True, blank=True)
    EVENT_STAT_CD                   = models.CharField(max_length=10, verbose_name= "이벤트 상태 코드", null=True, blank=True)
    EVENT_SUB_NM                    = models.CharField(max_length=200, verbose_name= "이벤트 서브 명", null=True, blank=True)
    EVENT_TP_CD                     = models.CharField(max_length=10, verbose_name= "이벤트 유형 코드", null=True, blank=True)
    EVENT_TYPE_CD                   = models.CharField(max_length=18, verbose_name= "이벤트 타입 코드", null=True, blank=True)
    FOOTER_CONTENT                  = models.TextField(verbose_name="하단 내용", null=True, blank=True)
    GALCAMS_PLTF_CD                 = models.CharField(max_length=2, verbose_name= "갤캠스 플랫폼 코드", null=True, blank=True)
    GALCAMS_TRGT_LVL                = models.CharField(max_length=10, verbose_name= "갤캠스 대상 레벨", null=True, blank=True)
    ICON_DSCRT1                     = models.CharField(max_length=500, verbose_name= "아이콘 설명1", null=True, blank=True)
    ICON_DSCRT2                     = models.CharField(max_length=500, verbose_name= "아이콘 설명2", null=True, blank=True)
    ICON_DSCRT3                     = models.CharField(max_length=500, verbose_name= "아이콘 설명3", null=True, blank=True)
    ICON_DSCRT4                     = models.CharField(max_length=500, verbose_name= "아이콘 설명4", null=True, blank=True)
    ICON_IMG1_PATH                  = models.CharField(max_length=100, verbose_name= "아이콘 이미지1 경로", null=True, blank=True)
    ICON_IMG2_PATH                  = models.CharField(max_length=100, verbose_name= "아이콘 이미지2 경로", null=True, blank=True)
    ICON_IMG3_PATH                  = models.CharField(max_length=100, verbose_name= "아이콘 이미지3 경로", null=True, blank=True)
    ICON_IMG4_PATH                  = models.CharField(max_length=100, verbose_name= "아이콘 이미지4 경로", null=True, blank=True)
    INSIDE_LNK_YN                   = models.CharField(max_length = 1, verbose_name= "내부 링크 여부", null=True, blank=True)
    LNK_URL                         = models.CharField(max_length=500, verbose_name= "링크 URL", null=True, blank=True)
    LNK_URL_TARGET                  = models.CharField(max_length=50, verbose_name= "링크 URL 대상", null=True, blank=True)
    MIG_EVENT_NO                    = models.IntegerField(verbose_name= "MIG 이번트 번호", null=True, blank=True)
    MIG_POPUP_SEQ                   = models.IntegerField(verbose_name= "MIG 팝업 순번", null=True, blank=True)
    PLCY_ALT_YN                     = models.CharField(max_length = 1, verbose_name= "처리 방침 알림 여부", null=True, blank=True)
    POPUP_SHOW_YN                   = models.CharField(max_length = 1, verbose_name= "팝업 노출 여부", null=True, blank=True)
    PRTCP_PSB_CNT                   = models.IntegerField(verbose_name= "참여 가능 수", null=True, blank=True)
    PRTCP_PSB_GB_CD                 = models.CharField(max_length=10, verbose_name= "참여 가능 구분 코드", null=True, blank=True)
    SEO_NO                          = models.IntegerField(verbose_name= "SEO 번호", null=True, blank=True)
    SHOW_YN                         = models.CharField(max_length = 1, verbose_name= "노출 여부", null=True, blank=True)
    SYS_REG_DTM                     = models.DateTimeField(verbose_name= "시스템 등록 일시", null=True, blank=True)
    SYS_UPD_DTM                     = models.DateTimeField(verbose_name= "시스템 수정 일시", null=True, blank=True)
    TTL                             = models.CharField(max_length=300,  verbose_name= "제목", null=True, blank=True)
    WIN_ANN_DTM                     = models.DateTimeField(verbose_name= "당첨자 발표 일시", null=True, blank=True)

    class Meta:
        verbose_name_plural = "26. EVENT_BASE"
        db_table = 'rubicon_data_event_base'


class goods_add_info(models.Model):
    BNR_IMG_EN_NM                   = models.CharField(max_length=100, verbose_name= "구매혜택 배너 영문 명", null=True, blank=True)
    BNR_IMG_PATH                    = models.CharField(max_length=500, verbose_name= "구매혜택 배너 경로", null=True, blank=True)
    BNR_IMG_TTL                     = models.CharField(max_length=200, verbose_name= "구매혜택 배너 제목", null=True, blank=True)
    BNR_LINK_URL                    = models.CharField(max_length=1000, verbose_name= "구매혜택 배너 URL", null=True, blank=True)
    CNTS_BG_BLACK_YN                = models.CharField(max_length = 1, verbose_name= "컨텐츠 배경 블랙 여부", null=True, blank=True)
    COMPARE_EXCPT_YN                = models.CharField(max_length = 1, verbose_name= "상품 스펙 비교하기 제외 여부", null=True, blank=True)
    FLG_END_DTM                     = models.DateTimeField(verbose_name= "플래그 종료 일시", null=True, blank=True)
    FLG_STRT_DTM                    = models.DateTimeField(verbose_name= "플래그 시작 일시", null=True, blank=True)
    GALAXY_CLUB_ENFOCEABLE_YN       = models.CharField(max_length=1, verbose_name= "갤럭시클럽 권리실행 가능 여부", null=True, blank=True)
    GALAXY_CLUB_TP_CD               = models.CharField(max_length=10, verbose_name= "갤럭시 클럽 유형 코드", null=True, blank=True)
    GALAXY_CLUB_YN                  = models.CharField(max_length=1,  verbose_name= "갤럭시 클럽 상품 여부", null=True, blank=True)
    GOODS_ADD_TP_CD                 = models.CharField(max_length=10, verbose_name= "상품 추가 유형 코드", null=True, blank=True)
    GOODS_ADD_TP_SUB_CD             = models.CharField(max_length=10, verbose_name= "상품 추가 유형 서브 코드", null=True, blank=True)
    GOODS_EP_BLOCK_YN               = models.CharField(max_length = 1, verbose_name= "상품 EP 블록 여부", null=True, blank=True)
    GOODS_ID                        = models.CharField(max_length=15, verbose_name= "상품 아이디", null=True, blank=True)
    GOODS_ORD_TP_CD                 = models.CharField(max_length=10, verbose_name= "상품 주문 타입 코드", null=True, blank=True)
    GUIDE_VD_URL                    = models.CharField(max_length=1000, verbose_name= "사용가이드 동영상 URL", null=True, blank=True)
    MDL_GRD                         = models.CharField(max_length=10, verbose_name= "모델 등급", null=True, blank=True)
    MID3                            = models.CharField(max_length=20,  verbose_name= "(갤럭시클럽) MID3", null=True, blank=True)
    MID3_END_DTM                    = models.DateTimeField(verbose_name= "(갤럭시클럽) MID3 종료 일시", null=True, blank=True)
    MID3_STRT_DTM                   = models.DateTimeField(verbose_name= "(갤럭시클럽) MID3 시작 일시", null=True, blank=True)
    MID4                            = models.CharField(max_length=20,  verbose_name= "(갤럭시클럽) MID4", null=True, blank=True)
    MID4_END_DTM                    = models.DateTimeField(verbose_name= "(갤럭시클럽) MID4 종료 일시", null=True, blank=True)
    MID4_STRT_DTM                   = models.DateTimeField(verbose_name= "(갤럭시클럽) MID4 시작 일시", null=True, blank=True)
    OMS_SEND_YN                     = models.CharField(max_length = 1, verbose_name= "OMS 전송 여부", null=True, blank=True)
    OUTSIDE_GOODS_NM                = models.CharField(max_length=300,  verbose_name= "외부 상품 명", null=True, blank=True)
    SPEC_TP_CD                      = models.CharField(max_length=10, verbose_name= "스펙 유형 코드", null=True, blank=True)
    STRTG_GOODS_YN                  = models.CharField(max_length = 1, verbose_name= "전략 상품 여부", null=True, blank=True)
    SYS_REG_DTM                     = models.DateTimeField(verbose_name= "시스템 등록 일시", null=True, blank=True)
    SYS_UPD_DTM                     = models.DateTimeField(verbose_name= "시스템 수정 일시", null=True, blank=True)
    TN_IMG_PATH                     = models.CharField(max_length=500, verbose_name= "썸네일 이미지 경로", null=True, blank=True)
    TN_IMG_TTL                      = models.CharField(max_length=200, verbose_name= "썸네일 제목", null=True, blank=True)
    TN_MO_IMG_PATH                  = models.CharField(max_length=500, verbose_name= "썸네일 모바일 이미지 경로", null=True, blank=True)
    URL_LINK_GB_CD                  = models.CharField(max_length=10, verbose_name= "URL 링크 구분 코드", null=True, blank=True)
    USP_DESC                        = models.CharField(max_length=1000, verbose_name= "USP 설명", null=True, blank=True)

    class Meta:
        verbose_name_plural = "27. GOODS_ADD_INFO"
        db_table = 'rubicon_data_goods_add_info'

class goods_add_info_detail(models.Model):
    BNR_IMG_EN_NM                   = models.CharField(max_length=100, verbose_name= "구매혜택 배너 영문 명", null=True, blank=True)
    BNR_IMG_PATH                    = models.CharField(max_length=500, verbose_name= "구매혜택 배너 경로", null=True, blank=True)
    BNR_IMG_TTL                     = models.CharField(max_length=200, verbose_name= "구매혜택 배너 제목", null=True, blank=True)
    BNR_LINK_URL                    = models.CharField(max_length=1000, verbose_name= "구매혜택 배너 URL", null=True, blank=True)
    GOODS_DTL_SEQ                   = models.IntegerField(verbose_name= "상품 상세 순번", null=True, blank=True)
    GOODS_DTL_TP_CD                 = models.CharField(max_length=2, verbose_name= "상품 상세 타입 코드", null=True, blank=True)
    GOODS_ID                        = models.CharField(max_length=15, verbose_name= "상품 아이디", null=True, blank=True)
    SYS_REG_DTM                     = models.DateTimeField(verbose_name= "시스템 등록 일시", null=True, blank=True)
    SYS_UPD_DTM                     = models.DateTimeField(verbose_name= "시스템 수정 일시", null=True, blank=True)
    URL_LINK_GB_CD                  = models.CharField(max_length=10, verbose_name= "URL 링크 구분 코드", null=True, blank=True)

    class Meta:
        verbose_name_plural = "28. GOODS_ADD_INFO_DETAIL"
        db_table = 'rubicon_data_goods_add_info_detail'


class pay_base(models.Model):
    ACCT_NO                         = models.CharField(max_length=50, verbose_name= "계좌 번호", null=True, blank=True)
    BANK_CD                         = models.CharField(max_length=10, verbose_name= "은행 코드", null=True, blank=True)
    CARDC_CD                        = models.CharField(max_length=10, verbose_name= "카드사 코드", null=True, blank=True)
    CFM_DTM                         = models.DateTimeField(verbose_name= "승인 일시", null=True, blank=True)
    CFM_NO                          = models.CharField(max_length=50, verbose_name= "승인 번호", null=True, blank=True)
    CFM_RST_CD                      = models.CharField(max_length=10, verbose_name= "승인 결과 코드", null=True, blank=True)
    CFM_RST_MSG                     = models.CharField(max_length=300,  verbose_name= "승인 결과 메세지", null=True, blank=True)
    CHRG_DC_YN                      = models.CharField(max_length = 1, verbose_name= "청구 할인 여부", null=True, blank=True)
    CLM_NO                          = models.CharField(max_length=20,  verbose_name= "클레임 번호", null=True, blank=True)
    CNC_YN                          = models.CharField(max_length = 1, verbose_name= "취소 여부", null=True, blank=True)
    DEAL_NO                         = models.CharField(max_length=50, verbose_name= "거래 번호", null=True, blank=True)
    DPSTR_NM                        = models.CharField(max_length=50, verbose_name= "입금자 명", null=True, blank=True)
    DPST_CHECK_MSG                  = models.CharField(max_length=300,  verbose_name= "입금 확인 메세지", null=True, blank=True)
    DPST_SCHD_AMT                   = models.FloatField(verbose_name= "입금 예정 금액", null=True, blank=True)
    DPST_SCHD_DT                    = models.CharField(max_length = 8, verbose_name= "입금 예정 일자", null=True, blank=True)
    ISTM_PRD                        = models.CharField(max_length=2, verbose_name= "할부 기간", null=True, blank=True)
    NO_ITRST_YN                     = models.CharField(max_length = 1, verbose_name= "무이자 여부", null=True, blank=True)
    OOA_NM                          = models.CharField(max_length=50, verbose_name= "예금주 명", null=True, blank=True)
    ORD_CLM_GB_CD                   = models.CharField(max_length=10, verbose_name= "주문 클레임 구분 코드", null=True, blank=True)
    ORD_NO                          = models.CharField(max_length=20,  verbose_name= "주문 번호", null=True, blank=True)
    ORG_PAY_NO                      = models.IntegerField(verbose_name= "원 결제 번호", null=True, blank=True)
    PAY_AMT                         = models.FloatField(verbose_name= "결제 금액", null=True, blank=True)
    PAY_CPLT_DTM                    = models.DateTimeField(verbose_name= "결제 완료 일시", null=True, blank=True)
    PAY_GB_CD                       = models.CharField(max_length=10, verbose_name= "결제 구분 코드", null=True, blank=True)
    PAY_MEANS_CD                    = models.CharField(max_length=10, verbose_name= "결제 수단 코드", null=True, blank=True)
    PAY_NO                          = models.IntegerField(verbose_name= "결제 번호", null=True, blank=True)
    PAY_STAT_CD                     = models.CharField(max_length=10, verbose_name= "결제 상태 코드", null=True, blank=True)
    PAY_TOKEN                       = models.CharField(max_length=100, verbose_name= "결제 토큰", null=True, blank=True)
    PG_TP_CD                        = models.CharField(max_length=10, verbose_name= "PG사 구분 코드", null=True, blank=True)
    PURCHASE_STATUS                 = models.CharField(max_length=2, verbose_name= "매입 전송 상태 (00:대기, 10:배송정보전송 , 20:구매정보확정수신, 30:구매확정정보전송, 40:빌정보수신 , 50:매입전송)", null=True, blank=True)
    PURCHASE_YN                     = models.CharField(max_length=1, verbose_name= "구매 확정 여부 (Y:확정, N:거절), null=True, blank=True")
    STR_ID                          = models.CharField(max_length=20, verbose_name= "상점 아이디", null=True, blank=True)
    UPDATE_YN                       = models.CharField(max_length=1, null=True, blank=True) 
    class Meta:
        verbose_name_plural = "29. PAY_BASE"
        db_table = 'rubicon_data_pay_base'


class rltn_goods_manage(models.Model):
    P_SYS_UPD_DTM                   = models.DateTimeField(verbose_name="p_sys_upd_dtm이 기록된 날짜입니다.", null=True, blank=True)
    SDW_BASE_YMD                    = models.TextField(verbose_name="베이스 ymd가 기록된 날짜입니다.", null=True, blank=True)
    SDW_LD_DT                       = models.TextField(verbose_name="sdw_ld_dt가 기록된 날짜입니다.", null=True, blank=True)
    B2B2C_SND_YN                    = models.TextField(verbose_name="데이터가 B2B2C로 전송되었는지 여부를 나타냅니다.", null=True, blank=True)
    B2B_SND_YN                      = models.TextField(verbose_name="데이터가 B2B로 전송되었는지 여부를 나타냅니다.", null=True, blank=True)
    DEL_YN                          = models.TextField(verbose_name="데이터가 삭제되었는지 여부를 나타냅니다.", null=True, blank=True)
    FNET_SND_YN                     = models.TextField(verbose_name="데이터가 FNET으로 전송되었는지 여부를 나타냅니다.", null=True, blank=True)
    MDL_CODE                        = models.TextField(verbose_name="모델에 대한 코드입니다.", null=True, blank=True)
    RLTN_GOODS_TP_CD                = models.TextField(verbose_name="관련 상품 유형에 대한 코드입니다.", null=True, blank=True)
    RLTN_MDL_CODE                   = models.TextField(verbose_name="관련 모델에 대한 코드입니다.", null=True, blank=True)
    SEQ                             = models.TextField(verbose_name="시퀀스 번호입니다.", null=True, blank=True)
    SYS_REGR_NO                     = models.TextField(verbose_name="시스템 등록 번호입니다.", null=True, blank=True)
    SYS_REG_DTM                     = models.TextField(verbose_name="시스템이 등록된 날짜와 시간입니다.", null=True, blank=True)
    SYS_UPDR_NO                     = models.TextField(verbose_name="시스템 업데이트 번호입니다.", null=True, blank=True)
    SYS_UPD_DTM                     = models.TextField(verbose_name="시스템이 마지막으로 업데이트된 날짜와 시간입니다.", null=True, blank=True)
    class Meta:
        verbose_name_plural = '30. RLTN_GOODS_MANAGE'
        db_table = 'rubicon_data_rltn_goods_manage'


class delivery(models.Model):
    BILL_ITEM_NO                    = models.CharField(max_length =6, verbose_name="ERP BILL ITEM 번호", null=True, blank=True)
    BILL_NO                         = models.CharField(max_length=10, verbose_name="ERP BILL 번호", null=True, blank=True)
    DLVR_CMD_DTM                    = models.DateTimeField(verbose_name="배송 옵션 코드", null=True, blank=True)
    DLVR_CPLT_DTM                   = models.DateTimeField(verbose_name="배송 완료 일시", null=True, blank=True)
    DLVR_GB_CD                      = models.CharField(max_length=10, verbose_name="배송 구분 코드", null=True, blank=True)
    DLVR_NO                         = models.IntegerField(verbose_name="배송 번호", null=True, blank=True)
    DLVR_PRCS_TP_CD                 = models.CharField(max_length=10, verbose_name="배송 처리 유형 코드", null=True, blank=True)
    DLVR_TP_CD                      = models.CharField(max_length=10, verbose_name="배송 유형 코드", null=True, blank=True)
    DO_ITEM_NO                      = models.CharField(verbose_name="ERP DO ITEM 번호", null=True, blank=True)
    DO_NO                           = models.CharField(max_length=10, verbose_name="ERP DO 번호", null=True, blank=True)
    DUMMY                           = models.TextField(verbose_name="UTF-8 이슈로 인한 더미데이터", null=True, blank=True)
    HDC_CD                          = models.CharField(max_length=13, verbose_name="택배사 코드", null=True, blank=True)
    INV_NO                          = models.CharField(max_length=30,  verbose_name="송장 번호", null=True, blank=True)
    OO_CPLT_DTM                     = models.DateTimeField(verbose_name="출고 완료 일시", null=True, blank=True)
    ORD_CLM_GB_CD                   = models.CharField(max_length=10, verbose_name="주문 클레임 구분 코드", null=True, blank=True)
    ORD_DLVRA_NO                    = models.IntegerField(verbose_name="주문 배송지 번호", null=True, blank=True)
    BILL_UPDATE_FLAG                = models.CharField(max_length=1, verbose_name="빌정보 업데이트 여부 (Y/N)", null=True, blank=True)
    DLVR_OPT_CD                     = models.CharField(max_length = 10, verbose_name="배송 옵션 코드", null=True, blank=True)
    SYS_REG_DTM                     = models.DateTimeField(verbose_name="시스템 등록 일시", null=True, blank=True)
    SYS_UPD_DTM                     = models.DateTimeField(verbose_name="시스템 수정 일시", null=True, blank=True)
    class Meta:
        verbose_name_plural = '31. DELIVERY'
        db_table = 'rubicon_data_delivery'


class pg_benefit_base(models.Model):
    ST_ID                           = models.IntegerField(null=True, blank=True, verbose_name="사이트 아이디")    
    BNFT_DTL_TP_CD                  = models.CharField(max_length=2, verbose_name="혜택 유형 상세 코드 (공통코드 : PG_BNFT_DTL_TP)", null=True, blank=True)
    BNFT_STAT_CD                    = models.CharField(max_length=2, verbose_name="진행 상태 코드 (공통코드 : PG_BNFT_STAT)", null=True, blank=True)
    BNFT_STAT_DTM                   = models.DateTimeField(verbose_name="진행 상태 일시", null=True, blank=True)
    BNFT_TP_CD                      = models.CharField(max_length=2, verbose_name="혜택 유형 코드 (공통코드 : PG_BNFT_TP)", null=True, blank=True)
    CARDC_CD                        = models.CharField(max_length=2, verbose_name="카드사 코드", null=True, blank=True)
    CHRG_APL_TP_CD                  = models.CharField(max_length=2, verbose_name="청구할인 적용유형 코드 (공통코드 : PG_CHRG_APL_TP)", null=True, blank=True)
    CHRG_BNFT_TP_CD                 = models.CharField(max_length=2, verbose_name="청구할인 혜택 유형 코드 (공통코드 : PG_CHRG_BNFT_TP)", null=True, blank=True)
    DISP_END_DTM                    = models.DateTimeField(verbose_name="전시 종료 일시", null=True, blank=True)
    DISP_STRT_DTM                   = models.DateTimeField(verbose_name="전시 시작 일시", null=True, blank=True)
    MID                             = models.CharField(max_length=20,  verbose_name="MID", null=True, blank=True)
    PAY_MEANS_CD                    = models.CharField(max_length=3, verbose_name="결제 수단 코드", null=True, blank=True)
    PG_BNFT_MSG                     = models.TextField(verbose_name="결제 혜택 문구", null=True, blank=True)
    PG_BNFT_NM                      = models.CharField(max_length=100,  verbose_name="결제 혜택 명", null=True, blank=True)
    PG_BNFT_NO                      = models.IntegerField(verbose_name="결제 혜택 번호", null=True, blank=True)
    SORT_SEQ                        = models.FloatField(verbose_name="정렬 순서", null=True, blank=True)

    class Meta:
        verbose_name_plural = '32. PG_BENEFIT_BASE'
        db_table = 'rubicon_data_pg_benefit_base'

class pg_mid(models.Model):

    COMP_GB_CD                      = models.CharField(max_length=10, verbose_name="업체 구분 코드", null=True, blank=True)
    DLGT_MID                        = models.CharField(max_length=20, verbose_name="대표 MID", null=True, blank=True)
    ISTM_PRD                        = models.CharField(max_length=2, verbose_name="할부 기간", null=True, blank=True)
    MID                             = models.CharField(max_length=20, verbose_name="MID", null=True, blank=True)
    MID_DC_RATE                     = models.IntegerField(verbose_name="MID 할인 율", null=True, blank=True)
    MID_TP_CD                       = models.CharField(max_length=10, verbose_name="MID 유형 코드", null=True, blank=True)
    MID_TTL                         = models.CharField(max_length=50, verbose_name="MID 제목", null=True, blank=True)
    OMNI_MID                        = models.CharField(max_length=20, verbose_name="옴니 MID", null=True, blank=True)
    RGLRAPRVL_MID                   = models.CharField(max_length=20, verbose_name="정기결재 MID", null=True, blank=True)

    class Meta:
        verbose_name_plural = '33. PG_MID'
        db_table = 'rubicon_data_pg_mid'

class pg_mid_msg(models.Model):

    DISP_END_DTM                    = models.DateTimeField(verbose_name="전시 종료 일시", null=True, blank=True)
    DISP_STRT_DTM                   = models.DateTimeField(verbose_name="전시 시작 일시", null=True, blank=True)
    ITDC_MSG1                       = models.CharField(max_length = 1024, verbose_name="안내 메세지1", null=True, blank=True)
    ITDC_MSG2                       = models.CharField(max_length = 1024, verbose_name="안내 메세지2", null=True, blank=True)
    MID                             = models.CharField(max_length=20, verbose_name="MID", null=True, blank=True)

    class Meta:
        verbose_name_plural = '34. PG_MID_MSG'
        db_table = 'rubicon_data_pg_mid_msg'

    
class product_detail_spec_info(models.Model):
    ATTR_ID1                        = models.CharField(max_length=40, verbose_name="항목 아이디1", null=True, blank=True)
    ATTR_ID2                        = models.CharField(max_length=40, verbose_name="항목 아이디2", null=True, blank=True)
    ATTR_NM1                        = models.CharField(max_length=200, verbose_name="항목 명1", null=True, blank=True)
    ATTR_NM2                        = models.CharField(max_length=200, verbose_name="항목 명2", null=True, blank=True)
    DISP_NM1                        = models.CharField(max_length=200, verbose_name="노출 명1", null=True, blank=True)
    DISP_NM2                        = models.CharField(max_length=200, verbose_name="노출 명2", null=True, blank=True)
    IF_REG_DTM                      = models.DateTimeField(verbose_name="인터페이스 등록 일시", null=True, blank=True)
    IS_TRANS                        = models.CharField(max_length=1, verbose_name="번역대상 모델여부", null=True, blank=True)
    MDL_CODE                        = models.CharField(max_length=100, verbose_name="모델 코드", null=True, blank=True)
    ORG_SPEC_VALUE                  = models.CharField(max_length=2000, verbose_name="원 스펙 값", null=True, blank=True)
    PLM_INPUT_TYPE                  = models.CharField(max_length=50, verbose_name="PLM 항목 유형", null=True, blank=True)
    PS_VER                          = models.CharField(max_length=10, verbose_name="스펙 버전", null=True, blank=True)
    SEQ                             = models.FloatField(verbose_name="순번", null=True, blank=True)
    SORT_SEQ1                       = models.FloatField(verbose_name="정렬 순서1", null=True, blank=True)
    SORT_SEQ2                       = models.FloatField(verbose_name="정렬 순서2", null=True, blank=True)
    SPEC_VALUE                      = models.CharField(max_length=2000, verbose_name="스펙 값", null=True, blank=True)
    STD_SCHEMA_ID                   = models.CharField(max_length=40, verbose_name="표준 스키마 아이디", null=True, blank=True)
    STD_SCHEMA_KEY1                 = models.CharField(max_length=40, verbose_name="표준 스키마 항목 키1", null=True, blank=True)
    STD_SCHEMA_KEY2                 = models.CharField(max_length=40, verbose_name="표준 스키마 항목 키2", null=True, blank=True)
    SYMBOL                          = models.CharField(max_length=30, verbose_name="스펙 단위 명", null=True, blank=True)
    SYS_REGR_NO                     = models.IntegerField(verbose_name="시스템 등록자 번호", null=True, blank=True)
    SYS_REG_DTM                     = models.DateTimeField(verbose_name="시스템 등록 일시", null=True, blank=True)
    SYS_UPDR_NO                     = models.IntegerField(verbose_name="시스템 수정자 번호", null=True, blank=True)
    SYS_UPD_DTM                     = models.DateTimeField(verbose_name="시스템 수정 일시", null=True, blank=True)
    UOM_SPACE                       = models.CharField(max_length=1, verbose_name="단위 공백포함 여부", null=True, blank=True)
    p_sys_upd_dtm                   = models.DateTimeField(verbose_name="시스템이 마지막으로 업데이트된 날짜 및 시간입니다.", null=True, blank=True)
    sdw_base_ymd                    = models.CharField(verbose_name="데이터 웨어하우스의 기준 연월일입니다.", null=True, blank=True)
    sdw_ld_dt                       = models.CharField(verbose_name="데이터가 데이터 웨어하우스에 로드된 날짜입니다.", null=True, blank=True)

    class Meta:
        verbose_name_plural = '35. PRODUCT_DETAIL_SPEC_INFO'
        db_table = 'rubicon_data_product_detail_spec_info'
        
        
class promotion_base(models.Model):
    ALL_GIVE_YN                     = models.CharField(max_length=1, verbose_name='전체 증정 여부', null=True, blank=True)
    APL_END_DTM                     = models.DateTimeField(verbose_name='적용 종료 일시', null=True, blank=True)
    APL_STRT_DTM                    = models.DateTimeField(verbose_name='적용 시작 일시', null=True, blank=True)
    APL_VAL                         = models.FloatField(verbose_name='적용 값', null=True, blank=True)
    APL_VAL_2                       = models.FloatField(verbose_name='적용 값 2', null=True, blank=True)
    ENULI_YN                        = models.CharField(max_length=1, verbose_name='에누리 여부', null=True, blank=True)
    FRB_CONTENT                     = models.TextField(verbose_name='사은품 내용', null=True, blank=True)
    FRB_KIND_CD                     = models.CharField(verbose_name='사은품 종류 코드', null=True, blank=True)
    LMT_QTY                         = models.FloatField(verbose_name='한정 수량', null=True, blank=True)
    ORD_QTY                         = models.FloatField(verbose_name='주문 수량', null=True, blank=True)
    PRMT_APL_CD                     = models.CharField(verbose_name='프로모션 적용 코드', null=True, blank=True)
    PRMT_BNFT_NTC                   = models.TextField(verbose_name='프로모션 혜택 유의사항', null=True, blank=True)
    PRMT_KIND_CD                    = models.CharField(verbose_name='프로모션 종류 코드', null=True, blank=True)
    PRMT_NM                         = models.CharField(max_length=200, verbose_name='프로모션 명', null=True, blank=True)
    PRMT_NO                         = models.IntegerField(verbose_name='프로모션 번호', null=True, blank=True)
    PRMT_STAT_CD                    = models.CharField(verbose_name='프로모션 상태 코드', null=True, blank=True)
    PRMT_TG_CD                      = models.CharField(verbose_name='프로모션 대상 코드', null=True, blank=True)
    PRMT_TP_CD                      = models.CharField(max_length=3, verbose_name='프로모션 유형 코드', null=True, blank=True)
    PRMT_TP_ETC_CONT                = models.CharField(max_length=30, verbose_name='프로모션 유형 기타', null=True, blank=True)
    QTY_SECTION1_FROM               = models.FloatField(verbose_name='수량 구간1 시작', null=True, blank=True)
    QTY_SECTION1_TO                 = models.FloatField(verbose_name='수량 구간1 종료', null=True, blank=True)
    QTY_SECTION2_FROM               = models.FloatField(verbose_name='수량 구간2 시작', null=True, blank=True)
    QTY_SECTION2_TO                 = models.FloatField(verbose_name='수량 구간2 종료', null=True, blank=True)
    RVS_MRG_PMT_YN                  = models.CharField(max_length=1, verbose_name='역 마진 허용 여부', null=True, blank=True)
    SPL_COMP_DVD_RATE               = models.FloatField(verbose_name='공급 업체 분담 율', null=True, blank=True)
    SYS_REG_DTM                     =  models.DateTimeField(  verbose_name='시스템 등록 일시', null=True, blank=True)
    SYS_UPD_DTM                     =  models.DateTimeField(  verbose_name='시스템 수정 일시', null=True, blank=True)
    TARGET_SALE_YN                  = models.CharField(max_length=1, verbose_name='상품 판매 여부 (사은품 재고 소진 시)', null=True, blank=True)

    class Meta:
        verbose_name_plural = '36. PROMOTION_BASE'
        db_table = 'rubicon_data_promotion_base'
        
class promotion_target(models.Model):
    APL_SEQ                         = models.FloatField(verbose_name='적용 순번', null=True, blank=True)
    BND_NO                          = models.IntegerField(verbose_name='브랜드 번호', null=True, blank=True)
    COMP_NO                         = models.IntegerField(verbose_name='업체 번호', null=True, blank=True)
    DISP_CLSF_NO                    = models.IntegerField(verbose_name='전시 분류 번호', null=True, blank=True)
    EXHBT_NO                        = models.IntegerField(verbose_name='기획전 번호', null=True, blank=True)
    GOODS_ID                        = models.CharField(max_length=15, verbose_name='상품 아이디', null=True, blank=True)
    PRMT_NO                         = models.IntegerField(verbose_name='프로모션 번호', null=True, blank=True)
    SYS_REG_DTM                     = models.DateTimeField(verbose_name='시스템 등록 일시', null=True, blank=True)
    SYS_UPD_DTM                     = models.DateTimeField(verbose_name='시스템 수정 일시', null=True, blank=True)

    class Meta:
        verbose_name_plural = '37. PROMOTION_TARGET'
        db_table = 'rubicon_data_promotion_target'
        
        
class promotion_freebie(models.Model):
    FRB_QTY                         = models.FloatField(verbose_name='사은품 수량', null=True, blank=True)
    FRB_RMN_QTY                     = models.FloatField(verbose_name='사은품 잔여 수량', null=True, blank=True)
    GOODS_ID                        = models.CharField(max_length=15, verbose_name='상품 아이디', null=True, blank=True)
    PRMT_NO                         = models.IntegerField(verbose_name='프로모션 번호', null=True, blank=True)
    RESTORE_YN                      = models.CharField(max_length=1, verbose_name='환원 여부', null=True, blank=True)
    SHOW_YN                         = models.CharField(max_length=1, verbose_name='노출 여부', null=True, blank=True)
    SYS_REG_DTM                     = models.DateTimeField(verbose_name='시스템 등록 일시', null=True, blank=True)
    SYS_UPD_DTM                     = models.DateTimeField(verbose_name='시스템 수정 일시', null=True, blank=True)
    class Meta:
        verbose_name_plural = '38. PROMOTION_FREEBIE'
        db_table = 'rubicon_data_promotion_freebie'
        
class order_base(models.Model):
    CHNL_ID                         = models.IntegerField(verbose_name='채널 아이디', null=True, blank=True)
    DATA_STAT_CD                    = models.CharField(max_length=15, verbose_name='데이터 상태 코드', null=True, blank=True)
    DLVR_START_SEND_FLAG            = models.CharField(max_length=1, verbose_name='배송 시작 전송 여부 (Y:완료,N:미완료)', null=True, blank=True)
    MBR_GRD_CD                      = models.CharField(max_length=15, verbose_name='회원 등급 코드', null=True, blank=True)
    MBR_NO                          = models.IntegerField(verbose_name='회원 번호', null=True, blank=True)
    ORDR_EMAIL                      = models.CharField(max_length=100, verbose_name='주문자 이메일', null=True, blank=True)
    ORDR_ID                         = models.CharField(max_length=100, verbose_name='주문자 아이디', null=True, blank=True)
    ORDR_IP                         = models.CharField(max_length=20, verbose_name='주문자 IP', null=True, blank=True)
    ORDR_MOBILE                     = models.CharField(max_length=20, verbose_name='주문자 휴대폰', null=True, blank=True)
    ORDR_TEL                        = models.CharField(max_length=20, verbose_name='주문자 전화', null=True, blank=True)
    ORD_ACPT_DTM                    = models.DateTimeField(verbose_name='주문 접수 일시', null=True, blank=True)
    ORD_CPLT_DTM                    = models.DateTimeField(verbose_name='주문 완료 일시', null=True, blank=True)
    ORD_DTL_CNT                     = models.FloatField(verbose_name='주문 상품 수', null=True, blank=True)
    ORD_MDA_CD                      = models.CharField(max_length=15, verbose_name='주문 매체 코드', null=True, blank=True)
    ORD_NM                          = models.CharField(max_length=100, verbose_name='주문자 명', null=True, blank=True)
    ORD_NO                          = models.CharField(max_length=20, verbose_name='주문 번호', null=True, blank=True)
    ORD_PRCS_RST_CD                 = models.CharField(max_length=15, verbose_name='주문 처리 결과 코드', null=True, blank=True)
    ORD_PRCS_RST_MSG                = models.CharField(max_length=500, verbose_name='주문 처리 결과 메세지', null=True, blank=True)
    ORD_STAT_CD                     = models.CharField(max_length=15, verbose_name='주문 상태 코드', null=True, blank=True)
    OUTSIDE_ORD_NO                  = models.CharField(max_length=20, verbose_name='외부 주문 번호', null=True, blank=True)
    RGLR_DLVR_NO                    = models.IntegerField(verbose_name='정기 배송 번호', null=True, blank=True)
    ST_ID                           = models.IntegerField(verbose_name='사이트 아이디', null=True, blank=True)
    SYS_REG_DTM                     = models.DateTimeField(verbose_name='시스템 등록 일시', null=True, blank=True)
    SYS_UPD_DTM                     = models.DateTimeField(verbose_name='시스템 수정 일시', null=True, blank=True)
    SYS_REGR_NO                     = models.IntegerField(verbose_name='시스템 등록자 번호', null=True, blank=True)
    SYS_UPDR_NO                     = models.IntegerField(verbose_name='시스템 수정자 번호', null=True, blank=True)
    updateYn                        = models.CharField(max_length=1, verbose_name='업데이트 여부', null=True, blank=True)
        
    class Meta:
        verbose_name_plural = '39. ORDER_BASE'
        db_table = 'rubicon_data_order_base'
        
class order_detail(models.Model):
    ACTFLG                          = models.CharField(max_length=1, verbose_name='(프리미엄 상품) 활성화 여부', null=True, blank=True)
    BSPK_GRP_KEY                    = models.CharField(max_length=50, verbose_name='비스포크 그룹 키', null=True, blank=True)
    BUY_LMT_APL_YN                  = models.CharField(max_length=1, verbose_name='구매 한도 반영 여부', null=True, blank=True)
    CART_ID                         = models.CharField(max_length=20, verbose_name='카트 아이디', null=True, blank=True)
    CART_MNL_USR_NO                 = models.IntegerField(verbose_name='장바구니 수기 등록자 번호', null=True, blank=True)
    CMS = models.FloatField(verbose_name='수수료', null=True, blank=True)
    CNC_QTY = models.FloatField(verbose_name='취소 수량', null=True, blank=True)
    COMP_GOODS_ID = models.CharField(max_length=50, verbose_name='업체 상품 번호', null=True, blank=True)
    COMP_ITEM_ID = models.CharField(max_length=50, verbose_name='업체 단품 번호', null=True, blank=True)
    COMP_NO = models.IntegerField(verbose_name='업체 번호', null=True, blank=True)
    DEAL_GOODS_ID = models.CharField(max_length=15, verbose_name='딜 상품 아이디', null=True, blank=True)
    DISP_CLSF_NO = models.IntegerField(verbose_name='전시 분류 번호', null=True, blank=True)
    DLVRC_NO = models.IntegerField(verbose_name='배송비 번호', null=True, blank=True)
    DLVR_DELAY_SEND_FLAG = models.CharField(max_length=1, verbose_name='배송 지연 알림 여부 (Y:완료, N:미완료)', null=True, blank=True)
    DLVR_NO = models.IntegerField(verbose_name='배송 번호', null=True, blank=True)
    DLVR_OPT_CD = models.CharField(max_length=15, verbose_name='배송 옵션 코드 (마이그 백업용)', null=True, blank=True)
    ERP_DC_PRC = models.FloatField(verbose_name='ERP 할인 가격', null=True, blank=True)
    ERP_OO_PRC = models.FloatField(verbose_name='ERP 출고 가격', null=True, blank=True)
    ERP_SPL_PRC = models.FloatField(verbose_name='ERP 공급 가격', null=True, blank=True)
    EXCPT_NO = models.IntegerField(verbose_name='구매 한도 적용 예외 번호', null=True, blank=True)
    FN_SPRT_AMT = models.FloatField(verbose_name='회사 지원 금액', null=True, blank=True)
    FREE_DLVR_YN = models.CharField(max_length=1, verbose_name='무료 배송 여부', null=True, blank=True)
    GOODS_CMSN_RT = models.FloatField(verbose_name='상품 수수료 율', null=True, blank=True)
    GOODS_ESTM_NO = models.IntegerField(verbose_name='상품평 번호', null=True, blank=True)
    GOODS_ESTM_REG_YN = models.CharField(max_length=1, verbose_name='상품평 등록 여부', null=True, blank=True)
    GOODS_ID = models.CharField(max_length=15, verbose_name='상품 아이디', null=True, blank=True)
    GOODS_NM = models.CharField(max_length=300, verbose_name='상품 명', null=True, blank=True)
    GOODS_PRC_NO = models.IntegerField(verbose_name='상품 가격 번호', null=True, blank=True)
    HOT_DEAL_YN = models.CharField(max_length=1, verbose_name='핫딜 상품 여부', null=True, blank=True)
    IST_HOPE_DT =  models.CharField(max_length=8, verbose_name='설치 희망 일자', null=True, blank=True)
    IST_SCHD_DT =  models.CharField(max_length=8, verbose_name='설치 예정 일자', null=True, blank=True)
    ITEM_NM =  models.CharField(max_length=200, verbose_name='단품 명', null=True, blank=True)
    ITEM_NO = models.IntegerField(verbose_name='단품 번호', null=True, blank=True)
    MBR_NO = models.IntegerField(verbose_name='회원 번호', null=True, blank=True)
    MD_USR_NO = models.IntegerField(verbose_name='MD 사용자 번호', null=True, blank=True)
    MEMBERSHIP_NO = models.CharField(verbose_name='멤버십 번호', null=True, blank=True)
    NETPR =  models.FloatField(verbose_name='NET 가격', null=True, blank=True)
    ORD_DLVRA_NO = models.IntegerField(verbose_name='주문 배송지 번호', null=True, blank=True)
    ORD_DTL_SEQ =  models.IntegerField(verbose_name='주문 상세 순번', null=True, blank=True)
    ORD_DTL_STAT_CD = models.CharField(max_length=15, verbose_name='주문 상세 상태 코드', null=True, blank=True)
    ORD_NO =  models.CharField(max_length=20, verbose_name='주문 번호', null=True, blank=True)
    ORD_QTY = models.FloatField(verbose_name='주문 수량', null=True, blank=True)
    ORD_SVMN = models.FloatField(verbose_name='부여 적립금', null=True, blank=True)
    OUTSIDE_ORD_DTL_NO = models.CharField(max_length=50, verbose_name='외부 주문 상세 번호', null=True, blank=True)
    PAY_AMT = models.FloatField(verbose_name='결제 금액', null=True, blank=True)
    PCK_STR_NO = models.CharField(verbose_name='픽업 매장 번호', null=True, blank=True)
    RMN_ORD_QTY = models.FloatField(verbose_name='잔여 주문 수량', null=True, blank=True)
    RMN_PAY_AMT = models.FloatField(verbose_name='잔여 결제 금액', null=True, blank=True)
    RTN_QTY = models.FloatField(verbose_name='반품 수량', null=True, blank=True)
    SALE_AMT = models.FloatField(verbose_name='판매 금액', null=True, blank=True)
    SLIP_NO = models.CharField(max_length=30, verbose_name='기표 번호', null=True, blank=True)
    SLIP_STAT_CD = models.CharField(max_length=15, verbose_name='기표 상태 코드', null=True, blank=True)
    SO_ITEM_NO = models.CharField(max_length=6, verbose_name='ERP SO ITEM 번호', null=True, blank=True)
    SO_NO = models.CharField(max_length=15, verbose_name='ERP SO 번호', null=True, blank=True)
    STL_NO = models.IntegerField(verbose_name='업체 정산 번호', null=True, blank=True)
    SVMN_VLD_PRD = models.IntegerField(verbose_name='적립금 유효 기간', null=True, blank=True)
    SVMN_VLD_PRD_CD = models.CharField(max_length=15, verbose_name='적립금 유효 기간 코드', null=True, blank=True)
    TAX_GB_CD = models.CharField(max_length=15, verbose_name='과세 구분 코드', null=True, blank=True)
    UP_COMP_NO = models.IntegerField(verbose_name='상위 업체 번호', null=True, blank=True)
    UP_ORD_DTL_GB_CD = models.CharField(max_length=15, verbose_name='상위 주문 상세 구분 코드', null=True, blank=True)
    UP_ORD_DTL_SEQ = models.FloatField(verbose_name='상위 주문 상세 순번', null=True, blank=True)
    WRHS_NO = models.IntegerField(verbose_name='웨어하우스 번호', null=True, blank=True)
    LOGIN_ID = models.CharField(verbose_name='로그인 아이디', null=True, blank=True)
    MDL_CODE = models.CharField(verbose_name='모델 코드', null=True, blank=True)
    SYS_REGR_NO = models.IntegerField(verbose_name='시스템 등록자 번호', null=True, blank=True)
    SYS_REG_DTM = models.DateTimeField(verbose_name='시스템 등록 일시', null=True, blank=True)
    SYS_UPDR_NO = models.IntegerField(verbose_name='시스템 수정자 번호', null=True, blank=True)
    SYS_UPD_DTM = models.DateTimeField(verbose_name='시스템 수정 일시', null=True, blank=True)
    updateYn = models.CharField(max_length=1, verbose_name='업데이트 여부', null=True, blank=True)
    class Meta:
        verbose_name_plural = '40. ORDER_DETAIL'
        db_table = 'rubicon_data_order_detail'
        
class goods_grp_key_map(models.Model):
    DISP_PRIOR_RANK         = models.IntegerField(verbose_name='전시 우선 순위', null=True, blank=True)
    DLGT_DISP_YN            = models.CharField(max_length=1, verbose_name='대표여부', null=True, blank=True)
    GOODS_ID                = models.CharField(max_length=15, verbose_name='상품 아이디', null=True, blank=True)
    GRP_KEY_NO              = models.IntegerField(verbose_name= "그룹 키 번호", null=True, blank=True)
    SYS_REG_DTM             = models.DateTimeField(verbose_name= "시스템 등록 일시", null=True, blank=True)
    SYS_UPD_DTM             = models.DateTimeField(verbose_name='시스템 수정 일시', null=True, blank=True)
    created_on = models.DateTimeField(verbose_name='Create', auto_now_add=True)
    updated_on = models.DateTimeField(verbose_name='Update', auto_now=True)

    class Meta:
        verbose_name_plural = "41. GOODS_GRP_KEY_MAP"
        db_table = 'rubicon_data_goods_grp_key_map'
        
class uk_updated_model_list(models.Model):
    MODEL_CODE              = models.CharField(verbose_name='모델코드', null=False, blank=False)
    UPDATED_DATE            = models.CharField(verbose_name='시스템 변경시각', max_length=14, null=True, blank=True)
    IS_USE                  = models.CharField(verbose_name='Target 여부', default = 'Y', max_length=1, null=True, blank=True)
    created_on              = models.DateTimeField(verbose_name='Create', auto_now_add=True)
    updated_on              = models.DateTimeField(verbose_name='Update', auto_now=True)
        
    class Meta:
        verbose_name_plural = "42. UK_UPDATED_MODEL_LIST"
        db_table = 'rubicon_data_uk_updated_model_list'
        unique_together = ('MODEL_CODE',)
                
class uk_model_price(models.Model):
    MODEL_CODE              = models.CharField(verbose_name='모델코드', null=False, blank=False)
    PRICE                   = models.FloatField(verbose_name='가격', null=True, blank=True)
    CURRENCY                = models.CharField(verbose_name='통화', null=True, blank=True)
    STOCK                   = models.IntegerField(verbose_name='재고', null=True, blank=True)
    PROMOTION_PRICE         = models.FloatField(verbose_name='프로모션 가격', null=True, blank=True)
    TIERED_PRICE            = models.FloatField(verbose_name='티어(tier) 가격', null=True, blank=True)
    created_on              = models.DateTimeField(verbose_name='Create', auto_now_add=True)
    updated_on              = models.DateTimeField(verbose_name='Update', auto_now=True)
        
    class Meta:
        verbose_name_plural = "43. UK_MODEL_PRICE"
        db_table = 'rubicon_data_uk_model_price'    
        unique_together = ('MODEL_CODE',)
        
class uk_product_spec_basics(models.Model):
    MODEL_CODE              = models.CharField(verbose_name='모델코드', primary_key=True)
    DISPLAY                 = models.CharField(verbose_name='전시여부', null=True, blank=True)
    SITE                    = models.CharField(verbose_name='국가', null=True, blank=True)
    IS_B2C                  = models.CharField(verbose_name='B2C여부', null=True, blank=True)
    REVIEWCOUNT             = models.IntegerField(verbose_name='리뷰갯수', null=True, blank=True)
    IS_INSURANCE            = models.CharField(verbose_name='보험여부', null=True, blank=True)
    CREATION_DATE           = models.DateField(verbose_name='생성일', null=True, blank=True)
    MODEL_NAME              = models.CharField(verbose_name='모델명', null=True, blank=True)
    LAUNCH_DATE             = models.DateField(verbose_name='발매일', null=True, blank=True)
    PRODUCT_DESC            = models.CharField(verbose_name='제품 설명', null=True, blank=True)
    TOP_FLAG                = models.CharField(verbose_name='FLAG', null=True, blank=True)
    TOP_FLAG_PERIOD_FROM    = models.DateField(verbose_name='FLAG 시작일', null=True, blank=True)
    TOP_FLAG_PERIOD_TO      = models.DateField(verbose_name='FLAG 종료일', null=True, blank=True)
    DISPLAY_NAME            = models.CharField(verbose_name='발매일', null=True, blank=True)
    CATEGORY_CODE1          = models.CharField(verbose_name='Category Code 1', null=True, blank=True, max_length=8)
    CATEGORY_LV1            = models.CharField(verbose_name='Category Lv1', null=True, blank=True)
    CATEGORY_CODE2          = models.CharField(verbose_name='Category Code 2', null=True, blank=True, max_length=8)
    CATEGORY_LV2            = models.CharField(verbose_name='Category Lv2', null=True, blank=True)
    CATEGORY_CODE3          = models.CharField(verbose_name='Category Code 3', null=True, blank=True, max_length=8)
    CATEGORY_LV3            = models.CharField(verbose_name='Category Lv3', null=True, blank=True)
    PRODUCT_URL             = models.CharField(verbose_name='Product URL', null=True, blank=True)
    CATEGORY                = models.CharField(verbose_name='Category', null=True, blank=True, max_length=8)
    CATEGORY_NAME           = models.CharField(verbose_name='Category명', null=True, blank=True)    
    created_on              = models.DateTimeField(verbose_name='Create', auto_now_add=True)
    updated_on              = models.DateTimeField(verbose_name='Update', auto_now=True)
        
    class Meta:
        verbose_name_plural = "44. UK_PRODUCT_SPEC_BASICS"
        db_table = 'rubicon_data_uk_product_spec_basics'    
        unique_together = ('MODEL_CODE',)
        
        
class uk_product_spec_specs(models.Model):
    MODEL_CODE              = models.CharField(verbose_name='모델코드')
    TYPES                   = models.CharField(verbose_name='SPEC 구분', null=True, blank=True)
    SPEC_TYPE               = models.CharField(verbose_name='SPEC TYPE(LV1)', null=True, blank=True)
    SPEC_NAME               = models.CharField(verbose_name='SPEC NAME(LV2)', null=True, blank=True)
    SPEC_DETAIL             = models.CharField(verbose_name='SPEC DETAIL(LV3)', null=True, blank=True)
    SPEC_VALUE              = models.CharField(verbose_name='SPEC 값', null=True, blank=True)    
    created_on              = models.DateTimeField(verbose_name='Create', auto_now_add=True)
    updated_on              = models.DateTimeField(verbose_name='Update', auto_now=True)
        
    class Meta:
        verbose_name_plural = "45. UK_PRODUCT_SPEC_SPEC"
        db_table = 'rubicon_data_uk_product_spec_spec'    
        unique_together = ('MODEL_CODE', 'TYPES', 'SPEC_TYPE', 'SPEC_NAME', 'SPEC_DETAIL')
        
class uk_product_spec_color(models.Model):
    MODEL_CODE              = models.CharField(verbose_name='모델코드')
    COLORS                  = models.CharField(verbose_name='색상', null=True, blank=True)
    IS_SPECIAL_COLOR        = models.CharField(verbose_name='Special Color', null=True, blank=True, default=None)
    created_on              = models.DateTimeField(verbose_name='Create', auto_now_add=True)
    updated_on              = models.DateTimeField(verbose_name='Update', auto_now=True)
        
    class Meta:
        verbose_name_plural = "46. UK_PRODUCT_SPEC_COLOR"
        db_table = 'rubicon_data_uk_product_spec_color'    
        unique_together = ('MODEL_CODE', 'COLORS',)
        
        
class uk_product_spec_mannuals(models.Model):
    MODEL_CODE              = models.CharField(verbose_name='모델코드')
    MANUAL_NAME             = models.CharField(verbose_name='매뉴얼 구분', null=True, blank=True)
    MANUAL_LINK             = models.CharField(verbose_name='매뉴얼 링크', null=True, blank=True)
    MANUAL_DESC             = models.CharField(verbose_name='매뉴얼 개요', null=True, blank=True)
    created_on              = models.DateTimeField(verbose_name='Create', auto_now_add=True)
    updated_on              = models.DateTimeField(verbose_name='Update', auto_now=True)
        
    class Meta:
        verbose_name_plural = "47. UK_PRODUCT_SPEC_MANUAL"
        db_table = 'rubicon_data_uk_product_spec_manuals'    
        unique_together = ('MODEL_CODE', 'MANUAL_NAME', 'MANUAL_LINK',)
        
class uk_order_cards_info(models.Model):
    MODEL_CODE              = models.CharField(verbose_name='모델코드')
    CODE1                   = models.CharField(verbose_name='구매구분', null=True, blank=True)
    CODE_NAME               = models.CharField(verbose_name='구매구분 설명', null=True, blank=True)
    CODE2                   = models.IntegerField(verbose_name='할부 개월수', null=True, blank=True)
    COMMISION               = models.FloatField(verbose_name='커미션', null=True, blank=True)
    MIN_AMOUNT              = models.FloatField(verbose_name='최소구매금액', null=True, blank=True)
    CURRENCY                = models.CharField(verbose_name='통화', null=True, blank=True)
    DOWNPAYMENT             = models.FloatField(verbose_name='할인값', null=True, blank=True)
    INTERESTRATE            = models.FloatField(verbose_name='이자율', null=True, blank=True)
    ORIGINALPRICE           = models.FloatField(verbose_name='정상가', null=True, blank=True)
    PERIOD                  = models.CharField(verbose_name='주기', null=True, blank=True)
    PERIODVALUE             = models.FloatField(verbose_name='월 납입가', null=True, blank=True)
    PURCHASECOST            = models.FloatField(verbose_name='구매가', null=True, blank=True)
    TOTALCOST               = models.FloatField(verbose_name='총판매가', null=True, blank=True)
    TOTALINTEREST           = models.FloatField(verbose_name='총이자', null=True, blank=True)
    created_on              = models.DateTimeField(verbose_name='Create', auto_now_add=True)
    updated_on              = models.DateTimeField(verbose_name='Update', auto_now=True)
        
    class Meta:
        verbose_name_plural = "48. UK_ORDER_CARDS_INFO"
        db_table = 'rubicon_data_uk_order_cards_info'    
        unique_together = ('MODEL_CODE', 'CODE1', 'CODE2',)
        
        
class uk_store_plaza(models.Model):
    STOREID                 = models.CharField(verbose_name='스토어 id', primary_key=True)
    SITE                    = models.CharField(verbose_name='지역', null=True, blank=True)
    DISPLAY	                = models.CharField(verbose_name='Display', null=True, blank=True)
    STORENAME               = models.CharField(verbose_name='스토어 명', null=True, blank=True)
    STORETYPE               = models.CharField(verbose_name='스토어 구분', null=True, blank=True)
    LONGITUDE               = models.CharField(verbose_name='경도', null=True, blank=True)
    LATITUDE                = models.CharField(verbose_name='위도', null=True, blank=True)
    DETAIL                  = models.CharField(verbose_name='위치 세부사항', null=True, blank=True)
    CITY                    = models.CharField(verbose_name='도시', null=True, blank=True)
    COUNTRY                 = models.CharField(verbose_name='국가', null=True, blank=True)
    ZIPCODE                 = models.CharField(verbose_name='zipcode', null=True, blank=True)
    TELEPHONE	            = models.CharField(verbose_name='전화번호', null=True, blank=True)
    ONLINEWEBSITE	        = models.CharField(verbose_name='Website', null=True, blank=True)
    STOREWEBSITE            = models.CharField(verbose_name='스토어 웹사이트', null=True, blank=True)
    EMAIL                   = models.CharField(verbose_name='이메일', null=True, blank=True)
    OPENINGHOUR             = models.TextField(verbose_name='Open/Closed 시각', null=True, blank=True)
    created_on              = models.DateTimeField(verbose_name='Create', auto_now_add=True)
    updated_on              = models.DateTimeField(verbose_name='Update', auto_now=True)
        
    class Meta:
        verbose_name_plural = "49. UK_STORE_PLAZA"
        db_table = 'rubicon_data_uk_store_plaza'
        

class product_category(models.Model):
    business_unit = models.CharField(verbose_name='Business Unit', max_length=1000, null=True, blank=True)
    product_category_lv1 = models.CharField(verbose_name='Product Category Lv1', max_length=1000, null=True, blank=True)
    product_category_lv2 = models.CharField(verbose_name='Product Category Lv2', max_length=1000, null=True, blank=True)
    product_category_lv3 = models.CharField(verbose_name='Product Category Lv3', max_length=1000, null=True, blank=True)
    model_name = models.CharField(verbose_name='Model Name', max_length=1000, null=True, blank=True)
    mdl_code = models.CharField(verbose_name='Mdl Code', max_length=1000, null=True, blank=True)
    goods_id = models.CharField(verbose_name='Goods Id', max_length=1000, null=True, blank=True)
    goods_nm = models.CharField(verbose_name='Goods Nm', max_length=1000, null=True, blank=True)
    color = models.CharField(verbose_name='Color', max_length=1000, null=True, blank=True)
    option1 = models.CharField(verbose_name='Option1', max_length=1000, null=True, blank=True)
    option2 = models.CharField(verbose_name='Option2', max_length=1000, null=True, blank=True)
    option3 = models.CharField(verbose_name='Option3', max_length=1000, null=True, blank=True)
    class Meta:
        verbose_name_plural = "50. RAW_PRODUCT_CATEGORY"
        db_table = 'rubicon_data_product_category'


class conts_cstrt_info(models.Model):
    CONTS_CSTRT_NO   = models.IntegerField(verbose_name= "컨텐츠 구성 번호", null=True, blank=True)
    CONTS_NO   = models.IntegerField(verbose_name= "컨텐츠 번호", null=True, blank=True)
    CPT_NO   = models.IntegerField(verbose_name= "컴포넌트 번호", null=True, blank=True)
    CSTRT_SEQ   = models.DecimalField(verbose_name= "구성 순번", null=True, blank=True, max_digits=5, decimal_places=0)
    REF_GB_CD   = models.CharField(max_length=10, verbose_name="참조 구분 코드", null=True, blank=True)
    SYS_REGR_NO   = models.IntegerField(verbose_name= "시스템 등록자 번호", null=True, blank=True)
    SYS_REG_DTM   = models.DateTimeField(null=True, blank=True, verbose_name="시스템 등록 일시")
    SYS_UPDR_NO   = models.IntegerField(verbose_name= "시스템 수정자 번호", null=True, blank=True)
    SYS_UPD_DTM   = models.DateTimeField(null=True, blank=True, verbose_name="시스템 수정 일시")

    class Meta:
        verbose_name_plural = "51. CONTS_CSTRT_INFO"
        db_table = 'rubicon_data_conts_cstrt_info'

class conts_info(models.Model):
    CONTS_NO   = models.IntegerField(verbose_name= "컨텐츠 번호", null=True, blank=True)
    CONTS_NM   = models.CharField(max_length=100, verbose_name="컨텐츠 명", null=True, blank=True)
    CONTS_EN_NM   = models.CharField(max_length=100, verbose_name="컨텐츠 영문 명", null=True, blank=True)
    CONTS_KWD   = models.CharField(max_length=500, verbose_name="컨텐츠 키워드", null=True, blank=True)
    CONTS_STAT_CD   = models.CharField(max_length=10, verbose_name="컨텐츠 상태 코드", null=True, blank=True)
    LCK_YN   = models.CharField(max_length=1, null=True, blank=True, verbose_name="잠금 여부")
    LCK_DTM   = models.DateTimeField(null=True, blank=True, verbose_name="잠금 일시")
    LCK_USR_NO   = models.IntegerField(verbose_name= "잠금 사용자 번호", null=True, blank=True)
    CONTS_TP_CD   = models.CharField(max_length=10, verbose_name="컨텐츠 유형 코드", null=True, blank=True)
    CONTS_KIND_CD   = models.CharField(max_length=10, verbose_name="컨텐츠 종류 코드", null=True, blank=True)
    GOODS_CPT_YN   = models.CharField(max_length=1, null=True, blank=True, verbose_name="상품 컴포넌트 포함 여부")
    HTMLSTR   = models.TextField(null=True, blank=True, verbose_name="HTML STR")
    ST_ID   = models.IntegerField(verbose_name= "사이트 아이디", null=True, blank=True)
    DISP_CLSF_NO   = models.IntegerField(verbose_name= "전시 분류 번호", null=True, blank=True)
    DISP_STRT_DTM   = models.DateTimeField(null=True, blank=True, verbose_name="전시 시작 일시")
    DISP_END_DTM   = models.DateTimeField(null=True, blank=True, verbose_name="전시 종료 일시")
    SYS_REGR_NO   = models.IntegerField(verbose_name= "시스템 등록자 번호", null=True, blank=True)
    SYS_REG_DTM   = models.DateTimeField(null=True, blank=True, verbose_name="시스템 등록 일시")
    SYS_UPDR_NO   = models.IntegerField(verbose_name= "시스템 수정자 번호", null=True, blank=True)
    SYS_UPD_DTM   = models.DateTimeField(null=True, blank=True, verbose_name="시스템 수정 일시")

    class Meta:
        verbose_name_plural = "52. CONTS_INFO"
        db_table = 'rubicon_data_conts_info'


class cpt(models.Model):
    CPT_NO   = models.IntegerField(verbose_name= "컴포넌트 번호", null=True, blank=True)
    CPT_LYT_NO   = models.IntegerField(verbose_name= "컴포넌트 레이아웃 번호", null=True, blank=True)
    CPT_NM   = models.CharField(max_length=300, verbose_name="컴포넌트 명", null=True, blank=True)
    CPT_EN_NM   = models.CharField(max_length=300, verbose_name="컴포넌트 영문 명", null=True, blank=True)
    CPT_KWD   = models.CharField(max_length=300, verbose_name="컴포넌트 키워드", null=True, blank=True)
    DEL_YN   = models.CharField(max_length=1, null=True, blank=True, verbose_name="삭제 여부")
    LCK_YN   = models.CharField(max_length=1, null=True, blank=True, verbose_name="잠금여부")
    LCK_DTM   = models.DateTimeField(null=True, blank=True, verbose_name="잠금 일시")
    LCK_USR_NO   = models.IntegerField(verbose_name= "잠금 사용자 번호", null=True, blank=True)
    JSONSTR   = models.TextField(null=True, blank=True, verbose_name="JSON STR")
    HTMLSTR   = models.TextField(null=True, blank=True, verbose_name="HTML STR")
    ST_ID   = models.IntegerField(verbose_name= "사이트 아이디", null=True, blank=True)
    UP_CPT_NO   = models.IntegerField(verbose_name= "상위 컴포넌트 번호", null=True, blank=True)
    MIG_FTRS_ITEM_ID   = models.IntegerField(verbose_name= "마이그 아이템 아이디", null=True, blank=True)
    MIG_FTRS_SCR_TYPE_CD   = models.CharField(max_length=20, verbose_name="마이그 레이아웃 번호", null=True, blank=True)
    CPT_DISP_TP_CD   = models.CharField(max_length=20, verbose_name="컴포넌트 노출 유형 코드", null=True, blank=True) # SHW 실데이터가 달라서 length 변환 models.CharField(max_length=2, verbose_name="컴포넌트 노출 유형 코드", null=True, blank=True)
    SYS_REGR_NO   = models.IntegerField(verbose_name= "시스템 등록자 번호", null=True, blank=True)
    SYS_REG_DTM   = models.DateTimeField(null=True, blank=True, verbose_name="시스템 등록 일시")
    SYS_UPDR_NO   = models.IntegerField(verbose_name= "시스템 수정자 번호", null=True, blank=True)
    SYS_UPD_DTM   = models.DateTimeField(null=True, blank=True, verbose_name="시스템 수정 일시")
    CPT_REG_GB_CD   = models.CharField(max_length=20, verbose_name="컴포넌트 등록 구분 코드", null=True, blank=True) # SHW 실데이터가 달라서 length 변환 models.CharField(max_length=2, verbose_name="컴포넌트 등록 구분 코드", null=True, blank=True)
    TASK_ID   = models.CharField(max_length=15, verbose_name="작업 아이디", null=True, blank=True)
    TASK_DTL_NO   = models.IntegerField(verbose_name= "작업 상세 번호", null=True, blank=True)

    class Meta:
        verbose_name_plural = "53. CPT"
        db_table = 'rubicon_data_cpt'


class goods_conts_map(models.Model):
    GOODS_ID   = models.CharField(max_length=15, verbose_name="상품 아이디", null=True, blank=True)
    CONTS_NO   = models.IntegerField(verbose_name= "컨텐츠 번호", null=True, blank=True)
    MIG_CNNCL_LINK_URL   = models.CharField(max_length=1024, verbose_name="MIG_CNNCL_LINK_URL", null=True, blank=True)
    SYS_REGR_NO   = models.IntegerField(verbose_name= "시스템 등록자 번호", null=True, blank=True)
    SYS_REG_DTM   = models.DateTimeField(null=True, blank=True, verbose_name="시스템 등록 일시")

    class Meta:
        verbose_name_plural = "54. GOODS_CONTS_MAP"
        db_table = 'rubicon_data_goods_conts_map'





