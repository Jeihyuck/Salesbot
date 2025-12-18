from django.db import models
from django.contrib.gis.db import models as gis_models
from django.contrib.postgres.fields import ArrayField
from django.contrib.postgres.indexes import GinIndex
from django.contrib.postgres.search import SearchVectorField
from pgvector.django import VectorField


class display_category(models.Model):    
    disp_clsf_no            = models.IntegerField(unique=True, null=False, blank=False, verbose_name="전시 분류 번호")
    st_id                   = models.IntegerField(null=True, blank=True, verbose_name="사이트 아이디")
    comp_no                 = models.IntegerField(null=True, blank=True, verbose_name="업체 번호")
    bnd_no                  = models.IntegerField(null=True, blank=True, verbose_name="브랜드 번호")
    up_disp_clsf_no         = models.IntegerField(null=True, blank=True, verbose_name="상위 전시 분류 번호")
    rdrt_disp_clsf_no       = models.IntegerField(null=True, blank=True, verbose_name="리다이렉트 전시 분류 번호")
    disp_clsf_nm            = models.CharField(max_length=100, null=True, blank=True, verbose_name="전시 분류 명")
    disp_clsf_en_nm         = models.CharField(max_length=200, null=True, blank=True, verbose_name="전시 분류 영문 명")
    disp_clsf_cd            = models.CharField(max_length=10, null=True, blank=True, verbose_name="전시 분류 코드")
    disp_tmpl_tp_cd         = models.CharField(max_length=10, null=True, blank=True, verbose_name="전시 템플릿 유형 코드")
    disp_prior_rank         = models.IntegerField(null=True, blank=True, verbose_name="전시 우선 순위")
    disp_lvl                = models.IntegerField(null=True, blank=True, verbose_name="전시 레벨")
    disp_strtdt             = models.DateTimeField(null=True, blank=True, verbose_name="전시 시작일자")
    disp_enddt              = models.DateTimeField(null=True, blank=True, verbose_name="전시 종료일자")
    leaf_yn                 = models.CharField(max_length=1, null=True, blank=True, verbose_name="최하위 여부")
    tn_img_path             = models.CharField(max_length=100, null=True, blank=True, verbose_name="썸네일 이미지 경로")
    tn_mo_img_path          = models.CharField(max_length=100, null=True, blank=True, verbose_name="썸네일 모바일 이미지 경로")
    menu_sub_title          = models.CharField(max_length=100, null=True, blank=True, verbose_name="메뉴 서브 타이틀")
    tn_img_alt_text         = models.CharField(max_length=500, null= True, blank=True, verbose_name="썸네일 이미지 ALT 텍스트")
    tn_use_yn               = models.CharField(max_length=1, null=True, blank=True, verbose_name="썸네일 사용 여부")
    tn_cta_text             = models.CharField(max_length=100, null=True, blank=True, verbose_name="썸네일 CTA 텍스트")
    tn_link_gb_cd           = models.CharField(max_length=10, null=True, blank=True, verbose_name="썸네일 링크 이동 구분 코드")
    tn_link_url             = models.CharField(max_length=200, null=True, blank=True, verbose_name="썸네일 링크 URL")
    tn_en_nm                = models.CharField(max_length=100, null=True, blank=True, verbose_name="썸네일 영문 명")
    tn_main_yn              = models.CharField(max_length=1, null=True, blank=True, verbose_name="썸네일 메인 여부")    
    tn_tp_txt               = models.CharField(max_length=50, null=True, blank=True, verbose_name="썸네일 타입 텍스트")
    menu_txt_color          = models.CharField(max_length=10, null=True, blank=True, verbose_name="메뉴 텍스트 색상")
    gnb_txt_color_cd        = models.CharField(max_length=10, null=True, blank=True, verbose_name="GNB 텍스트 색상 코드")
    url_input_gb_cd         = models.CharField(max_length=10, null=True, blank=True, verbose_name="URL 입력 구분 코드")    
    link_url                = models.CharField(max_length=200, null=True, blank=True, verbose_name="링크 URL")
    menu_link_gb_cd         = models.CharField(max_length=10, null=True, blank=True, verbose_name="메뉴 링크 이동 구분 코드")
    seo_no                  = models.IntegerField(null=True, blank=True, verbose_name="SEO 번호")
    disp_yn                 = models.CharField(max_length=1, null=True, blank=True, verbose_name="전시 여부")
    del_yn                  = models.CharField(max_length=1, null=True, blank=True, verbose_name="삭제 여부")
    mobile_yn               = models.CharField(max_length=1, null=True, blank=True, verbose_name="모바일 여부")
    sar_disp_yn             = models.CharField(max_length=1, null=True, blank=True, verbose_name="SAR정보 전시 여부")
    mounted_app_disp_yn     = models.CharField(max_length=1, null=True, blank=True, verbose_name="탑재 어플리케이션 전시 여부")
    dup_link_set_yn         = models.CharField(max_length=1, null=True, blank=True, verbose_name="중복 링크 설정 여부")
    dup_link_url            = models.CharField(max_length=200, null=True, blank=True, verbose_name="중복 링크 URL")
    dup_link_icon_path      = models.CharField(max_length=100, null=True, blank=True, verbose_name="중복 링크 아이콘 경로")    
    dup_link_text           = models.CharField(max_length=100, null=True, blank=True, verbose_name="중복 링크 텍스트")
    new_prdt_yn             = models.CharField(max_length=1, null=True, blank=True, verbose_name="신제품 여부")
    acc_yn                  = models.CharField(max_length=1, null=True, blank=True, verbose_name="액세서리 여부")
    sub_menu_gb_cd          = models.CharField(max_length=10, null=True, blank=True, verbose_name="하위 메뉴 구분 코드")
    item_dlvr_gb_cd         = models.CharField(max_length=2, null=True, blank=True, verbose_name="품목별 배송 구분 코드")
    gnb_font_tp_cd          = models.CharField(max_length=10, null=True, blank=True, verbose_name="GNB 폰트 유형 코드")  
    gnb_logo_use_yn         = models.CharField(max_length=1, null=True, blank=True, verbose_name="GNB 로고 사용 여부")
    gnb_logo_pos_cd         = models.CharField(max_length=10, null=True, blank=True, verbose_name="GNB 로고 위치 코드")
    gnb_logo_img_path       = models.CharField(max_length=100, null=True, blank=True, verbose_name="GNB 로고 이미지 경로")
    gnb_align_gb_cd         = models.CharField(max_length=1, null=True, blank=True, verbose_name="GNB 정렬 구분 코드")
    gnb_div_line_yn         = models.CharField(max_length=1, null=True, blank=True, verbose_name="GNB 구분선 여부")
    gnb_badge_use_yn        = models.CharField(max_length=1, null=True, blank=True, verbose_name="GNB 뱃지 사용 여부")
    gnb_badge_color         = models.CharField(max_length=20, null=True, blank=True, verbose_name="GNB 뱃지 색상")
    gnb_badge_text          = models.CharField(max_length=50, null=True, blank=True, verbose_name="GNB 뱃지 텍스트")
    netfunnel_yn            = models.CharField(max_length=1, null=True, blank=True, verbose_name="넷퍼넬 적용 여부")
    netfunnel_act_id        = models.CharField(max_length=100, null=True, blank=True, verbose_name="넷퍼넬 ACT 아이디")
    netfunnel_bnr_yn        = models.CharField(max_length=1, null=True, blank=True, verbose_name="넷퍼넬 배너 적용 여부")
    netfunnel_bnr_act_id    = models.CharField(max_length=100, null=True, blank=True, verbose_name="넷퍼넬 배너 액션 아이디")
    disp_clsf_mo_nm         = models.CharField(max_length=100, null=True, blank=True, verbose_name="전시 분류 모바일 명")    
    sys_reg_dtm             = models.DateTimeField(verbose_name= "시스템 등록 일시", null=True, blank=True)
    sys_upd_dtm             = models.DateTimeField(verbose_name= "시스템 수정 일시", null=True, blank=True)
    cta1_style_cd           = models.CharField(max_length=1, null=True, blank=True, verbose_name="CTA1 스타일 코드")
    cta2_style_cd           = models.CharField(max_length=1, null=True, blank=True, verbose_name="CTA2 스타일 코드")    
    cta1_link_url           = models.CharField(max_length=200, null=True, blank=True, verbose_name="CTA1 링크 URL")
    cta2_link_url           = models.CharField(max_length=200, null=True, blank=True, verbose_name="CTA2 링크 URL")
    cta1_en_nm              = models.CharField(max_length=100, null=True, blank=True, verbose_name="CTA1 영문 명")
    cta2_en_nm              = models.CharField(max_length=100, null=True, blank=True, verbose_name="CTA2 영문 명")    
    cta2_text               = models.CharField(max_length=100, null=True, blank=True, verbose_name="CTA2 텍스트")
    base_ymd                = models.DateField(verbose_name='기준일', null=True, blank=True) 
    ld_dt                   = models.DateTimeField(verbose_name='적재일시', null=True, blank=True)


class display_ctg_add_info(models.Model):    
    disp_clsf_no            = models.IntegerField(verbose_name= "전시 분류 번호", null=False, blank=False)
    add_info_no             = models.IntegerField(verbose_name= "추가 정보 번호", null=False, blank=False)
    url_nm_gb_cd            = models.IntegerField(verbose_name= "URL Name 구분 코드", null=True, blank=True) 
    url_nm                  = models.TextField(verbose_name= "URL", null=True, blank=True)
    disclaimer              = models.TextField(verbose_name= "Disclaimer", null=True, blank=True)
    sale_prc_cclt_rate      = models.DecimalField(verbose_name= "판매 가격 산출 율", max_digits=5, decimal_places=2, null=True, blank=True)
    ctg_ord_limit_use_yn    = models.CharField(max_length=100, verbose_name= "카테고리 주문 제한 사용 여부", null=True, blank=True)
    ctg_ord_limit_qty       = models.CharField(max_length=200, verbose_name= "카테고리 주문 제한 수량", null=True, blank=True)
    ctg_ord_limit_strt_dtm  = models.CharField(max_length=10, verbose_name= "카테고리 주문 제한 시작 일시", null=True, blank=True)
    ctg_ord_limit_end_dtm   = models.CharField(max_length=10, verbose_name= "카테고리 주문 제한 종료 일시", null=True, blank=True)
    sys_reg_dtm             = models.DateTimeField(verbose_name= "시스템 등록 일시", null=True, blank=True)
    sys_upd_dtm             = models.DateTimeField(verbose_name= "시스템 수정 일시", null=True, blank=True)
    cta_nm                  = models.CharField(max_length=100, verbose_name= "CTA 명", null=True, blank=True)    
    cta_use_yn              = models.CharField(max_length=100, verbose_name= "CTA 사용여부", null=True, blank=True)
    cta_url                 = models.CharField(max_length=100, verbose_name= "CTA URL", null=True, blank=True)
    accessibility_yn        = models.CharField(max_length=100, verbose_name= "제품 접근성 사용 여부", null=True, blank = True)
    accessibility_link      = models.CharField(max_length=500, verbose_name= "제품 접근성 LINK", null=True, blank=True)
    time_dlvr_apl_ctg_yn    = models.CharField(max_length=1, verbose_name= "시간맞춤 배송 적용 카테고리 여부", null=True, blank=True)
    same_day_ist_ctg_yn     = models.CharField(max_length=1, verbose_name= "당일 설치 카테고리 여부", null=True, blank=True)
    div_pay_apl_yn          = models.CharField(max_length=1, verbose_name= "분할 결제 적용 여부", null=True, blank=True)  
    prdt_grp_card_yn        = models.CharField(max_length=1, verbose_name= "제품 그룹 카드 여부", null=True, blank=True)
    srch_disp_yn            = models.CharField(max_length=1, verbose_name= "통합 검색 노출 여부", null=True, blank=True)
    aisc_ssb_yn             = models.CharField(max_length=1, verbose_name= "(AI 구독 클럽) 구독 여부", null=True, blank=True)    
    base_ymd                = models.DateField(verbose_name='기준일', null=True, blank=True)
    ld_dt                   = models.DateTimeField(verbose_name='적재일시', null=True, blank=True)

    class Meta:
        unique_together = ('disp_clsf_no', 'add_info_no')


class display_goods(models.Model):
    disp_clsf_no            = models.IntegerField(verbose_name= "전시 분류 번호", null=True, blank=True)
    goods_id                = models.CharField(max_length=15, verbose_name= "상품 번호", null=True, blank=True)
    disp_prior_rank         = models.IntegerField(verbose_name= "전시 우선 순위", null=True, blank=True)
    dlgt_disp_yn            = models.CharField(max_length=1, verbose_name= "대표 전시 여부", null=True, blank=True)    
    stk_excpt_yn            = models.CharField(max_length=1, verbose_name= "재고 예외 여부", null=True, blank=True)    
    sys_reg_dtm             = models.DateTimeField(null=True, blank=True, verbose_name="시스템 등록 일시")
    sys_upd_dtm             = models.DateTimeField(verbose_name= "시스템 수정 일시", null=True, blank=True)    
    base_ymd                = models.DateField(verbose_name='기준일', null=True, blank=True)
    ld_dt                   = models.DateTimeField(verbose_name='적재일시', null=True, blank=True)
    
    class Meta:
        unique_together = ('disp_clsf_no', 'goods_id')


class goods_add_column_info(models.Model):
    goods_id                = models.CharField(max_length=15, verbose_name="상품 아이디", null=True, blank=True)
    goods_col_gb_cd         = models.CharField(max_length=10, verbose_name="상품 컬럼 구분 코드 (code_detail.dtl_cd = goods_col_gb)", null=True, blank=True)
    col_val1                = models.TextField(null=True, blank=True, verbose_name="컬럼 값1")
    col_val2                = models.TextField(null=True, blank=True, verbose_name="컬럼 값2")
    col_val3                = models.TextField(null=True, blank=True, verbose_name="컬럼 값3")
    col_val4                = models.TextField(null=True, blank=True, verbose_name="컬럼 값4")
    use_yn                  = models.CharField(max_length=1, verbose_name="사용 여부", null=True, blank=True)
    sys_reg_dtm             = models.DateTimeField(null=True, blank=True, verbose_name="시스템 등록 일시")
    sys_upd_dtm             = models.DateTimeField(verbose_name= "시스템 수정 일시", null=True, blank=True)    
    base_ymd                = models.DateField(verbose_name='기준일', null=True, blank=True)
    ld_dt                   = models.DateTimeField(verbose_name='적재일시', null=True, blank=True)    

    class Meta:        
        unique_together = ('goods_id', 'goods_col_gb_cd')

        
class goods_base(models.Model):
    goods_id                = models.CharField(unique=True, max_length=15, verbose_name= "상품 아이디", null=True, blank=True)
    goods_nm                = models.CharField(max_length=300, verbose_name= "상품 명", null=True, blank=True)
    goods_stat_cd           = models.CharField(max_length=10, verbose_name= "상품 상태 코드", null=True, blank=True)
    unsold_tp_cd            = models.CharField(max_length=10, verbose_name= "미판매 유형 코드", null=True, blank=True)
    goods_tp_cd             = models.CharField(max_length=10, verbose_name= "상품 유형 코드", null=True, blank=True)
    goods_tp_sub_cd         = models.CharField(max_length=10, verbose_name= "상품 유형 서브 코드", null=True, blank=True)
    comp_no                 = models.IntegerField(verbose_name= "업체 번호", null=True, blank=True, db_index=False)
    mdl_code                = models.CharField(max_length=100, verbose_name= "모델 코드", null=True, blank=True)
    gerp_lnk_yn             = models.CharField(max_length=1, verbose_name= "GERP 연동 여부", null=True, blank=True)
    gerp_amt                = models.DecimalField(verbose_name= "금액1", null=True, blank=True, max_digits=10, decimal_places=0, db_index=False)
    mdl_nm                  = models.CharField(max_length=200, verbose_name= "모델 명", null=True, blank=True)
    kwd                     = models.CharField(max_length=4000, verbose_name= "키워드", null=True, blank=True)
    pr_wds_show_yn          = models.CharField(max_length=1, verbose_name= "홍보 문구 노출 여부", null=True, blank=True)
    pr_wds                  = models.CharField(max_length=1000, verbose_name= "홍보 문구", null=True, blank=True)
    bnd_no                  = models.IntegerField(verbose_name= "브랜드 번호", null=True, blank=True, db_index=False)
    ctr_org                 = models.CharField(max_length=100, verbose_name= "원산지", null=True, blank=True)
    mmft                    = models.CharField(max_length=200, verbose_name= "제조사", null=True, blank=True)
    importer                = models.CharField(max_length=200, verbose_name= "수입사", null=True, blank=True)
    stk_mng_yn              = models.CharField(max_length=1, verbose_name= "재고 관리 여부", null=True, blank=True)    
    tax_gb_cd               = models.CharField(max_length=10, verbose_name= "과세 구분 코드", null=True, blank=True)
    min_ord_qty             = models.DecimalField(verbose_name= "최소 주문 수량", null=True, max_digits=10, decimal_places=0, blank=True, db_index=False)
    max_ord_qty             = models.DecimalField(verbose_name= "최대 주문 수량", null=True, max_digits=10, decimal_places=0, blank=True, db_index=False)
    prpsn_ord_lmt_qty       = models.DecimalField(verbose_name= "1인당 구매 제한 수량", null=True, blank=True, max_digits=10, decimal_places=0, db_index=False)
    prpsn_ord_lmt_strt_dtm  = models.DateTimeField(verbose_name= "1인당 구매 제한 시작 일시", null=True, blank=True)
    prpsn_ord_lmt_end_dtm   = models.DateTimeField(verbose_name= "1인당 구매 제한 종료 일시", null=True, blank=True)
    dlvr_mtd_cd             = models.CharField(max_length=10, verbose_name= "배송 방법 코드", null=True, blank=True)
    rsv_cus_psb_yn          = models.CharField(max_length=1, verbose_name= "예약 상담 가능 여부", null=True, blank=True)
    free_dlvr_yn            = models.CharField(max_length=1, verbose_name= "무료 배송 여부", null=True, blank=True)
    dlvr_plnt_cd            = models.CharField(max_length=10, verbose_name= "Delivering Plant 코드", null=True, blank=True)
    dlvr_opt_cd             = models.CharField(max_length=10, verbose_name= "배송 옵션 코드", null=True, blank=True)
    dlvr_gen_yn             = models.CharField(max_length=1, verbose_name= "배송 일반 여부", null=True, blank=True)
    dlvr_ist_yn             = models.CharField(max_length=1, verbose_name= "배송 설치 여부", null=True, blank=True)
    dlvr_pck_yn             = models.CharField(max_length=1, verbose_name= "배송 픽업 여부", null=True, blank=True)
    dlvr_wkpl_pck_yn        = models.CharField(max_length=1, verbose_name= "배송 사업장 픽업 여부", null=True, blank=True)
    dlvr_itdc_wds           = models.CharField(max_length=1000, verbose_name= "배송 안내 문구", null=True, blank=True)
    dlvrc_plc_no            = models.IntegerField(verbose_name= "배송 정책 번호", null=True, blank=True, db_index=False)
    comp_plc_no             = models.IntegerField(verbose_name= "업체 정책 번호", null=True, blank=True, db_index=False)
    use_stk_cd              = models.CharField(max_length=10, verbose_name= "사용 재고 코드", null=True, blank=True)
    pplrt_rank              = models.DecimalField(verbose_name= "인기 순위", null=True, blank=True, max_digits=10, decimal_places=0, db_index=False)
    pplrt_set_cd            = models.CharField(max_length=10, verbose_name= "인기 설정 코드", null=True, blank=True)
    sale_strt_dtm           = models.DateTimeField(verbose_name= "판매 시작 일시", null=True, blank=True)
    sale_end_dtm            = models.DateTimeField(verbose_name= "판매 종료 일시", null=True, blank=True)
    ntf_id                  = models.CharField(max_length=10, verbose_name= "고시 아이디", null=True, blank=True)
    md_usr_no               = models.IntegerField(verbose_name= "MD 사용자 번호", null=True, blank=True, db_index=False)
    item_mng_yn             = models.CharField(max_length=1, verbose_name= "단품 관리 여부", null=True, blank=True)
    show_yn                 = models.CharField(max_length=1, verbose_name= "노출 여부", null=True, blank=True)
    show_strt_dt            = models.DateField(verbose_name= "노출 시작 일자", null=True, blank=True)
    show_strt_dtm           = models.DateTimeField(verbose_name= "노출 시작 일시", null=True, blank=True)
    rsv_ord_yn              = models.CharField(max_length=1, verbose_name= "예약 주문 여부", null=True, blank=True)
    rsv_ord_dlvr_dt         = models.DateField(verbose_name= "예약 주문 배송 일자", null=True, blank=True)
    rsv_ord_prd_show_yn     = models.CharField(max_length=1, verbose_name= "예약 주문 기간 노출 여부", null=True, blank=True)
    rsv_ord_lmt_qty         = models.DecimalField(verbose_name= "예약 주문 제한 수량", null=True, max_digits=10, decimal_places=0, blank=True, db_index=False)
    rsv_ord_apl_qty         = models.DecimalField(verbose_name= "예약 주문 적용 수량", null=True, blank=True, max_digits=10, decimal_places=0, db_index=False)
    rsv_ord_strt_dtm        = models.DateTimeField(verbose_name= "예약 주문 시작 일시", null=True, blank=True)
    rsv_ord_end_dtm         = models.DateTimeField(verbose_name= "예약 주문 종료 일시", null=True, blank=True)
    arcn_yn                 = models.CharField(max_length=1, verbose_name= "에어컨 여부", null=True, blank=True)
    bspk_goods_yn           = models.CharField(max_length=1, verbose_name= "비스포크 상품 여부", null=True, blank=True)
    watch_goods_yn          = models.CharField(max_length=1, verbose_name= "워치 상품 여부", null=True, blank=True)
    watch_show_yn           = models.CharField(max_length=1, verbose_name= "워치 노출 여부", null=True, blank=True)
    adv_vst_cd              = models.CharField(max_length=10, verbose_name= "사전 방문 코드", null=True, blank=True)
    newprdt_flg_yn          = models.CharField(max_length=1, verbose_name= "신제품 플래그 여부", null=True, blank=True)    
    lmt_flg_yn              = models.CharField(max_length=1, verbose_name= "한정 플래그 여부", null=True, blank=True)
    pplrtprdt_flg_yn        = models.CharField(max_length=1, verbose_name= "인기제품 플래그 여부", null=True, blank=True)
    mcdg_txt                = models.CharField(max_length=1000, verbose_name= "머천다이징 텍스트", null=True, blank=True)
    mcdg_txt2               = models.CharField(max_length=1000, verbose_name= "머천다이징 텍스트2", null=True, blank=True)
    mcdg_txt3               = models.CharField(max_length=1000, verbose_name= "머천다이징 텍스트3", null=True, blank=True)
    door_drct_yn            = models.CharField(max_length=1, verbose_name= "도어 방향 여부", null=True, blank=True)
    grbg_pu_yn              = models.CharField(max_length=1, verbose_name= "폐가전 수거 여부", null=True, blank=True)
    rglr_dlvr_yn            = models.CharField(max_length=1, verbose_name= "정기 배송 여부", null=True, blank=True)
    rglr_dlvr_cycl          = models.CharField(max_length=100, verbose_name= "정기 배송 주기", null=True, blank=True)
    rglr_dlvr_dcrate        = models.DecimalField(verbose_name= "정기 배송 할인율", null=True, blank=True, max_digits=5, decimal_places=2, db_index=False)
    so_crt_excpt_yn         = models.CharField(max_length=1, verbose_name= "SO 생성 제외 여부", null=True, blank=True)    
    mhdj_tg_yn              = models.CharField(max_length=1, verbose_name= "무한도전 대상 여부", null=True, blank=True)
    online_store_only_yn    = models.CharField(max_length=1, verbose_name= "온라인 전용 상품 여부", null=True, blank=True)
    comp_goods_id           = models.CharField(max_length=50, verbose_name= "업체 상품 아이디", null=True, blank=True)
    web_mobile_gb_cd        = models.CharField(max_length=10, verbose_name= "웹 모바일 구분 코드", null=True, blank=True)
    seo_no                  = models.IntegerField(verbose_name= "SEO 번호", null=True, blank=True, db_index=False)
    rtn_psb_yn              = models.CharField(max_length=1, verbose_name= "반품 가능 여부", null=True, blank=True)
    rtn_msg                 = models.CharField(max_length=4000, verbose_name= "반품 메세지", null=True, blank=True)
    bigo                    = models.CharField(max_length=1000, verbose_name= "비고", null=True, blank=True)
    vd_link_url             = models.CharField(max_length=500, verbose_name= "동영상 링크 URL", null=True, blank=True)    
    hits                    = models.IntegerField(verbose_name= "조회수", null=True, blank=True, db_index=False)
    erp_prc_chg_apl_yn      = models.CharField(max_length=10, verbose_name= "ERP 가격 변경 젹용 여부", null=True, blank=True)
    erp_oo_prc              = models.DecimalField(verbose_name= "ERP 출고 가격", null=True, blank=True, max_digits=10, decimal_places=0, db_index=False)
    erp_spl_prc             = models.DecimalField(verbose_name= "ERP 공급 가격", null=True, blank=True, max_digits=10, decimal_places=0, db_index=False)
    erp_dc_prc              = models.DecimalField(verbose_name= "ERP 할인 가격", null=True, blank=True, max_digits=10, decimal_places=0, db_index=False)
    erp_dc_auto_cal_yn      = models.CharField(max_length=1, verbose_name= "ERP 할인 자동 계산 여부", null=True, blank=True)
    mid1                    = models.CharField(max_length=20, verbose_name= "MID1", null=True, blank=True)
    mid1_strt_dtm           = models.DateTimeField(verbose_name= "MID1 시작 일시", null=True, blank=True)
    mid1_end_dtm            = models.DateTimeField(verbose_name= "MID1 종료 일시", null=True, blank=True)
    mid2_strt_dtm           = models.DateTimeField(verbose_name= "MID2 시작 일시", null=True, blank=True)    
    mid2                    = models.CharField(max_length=20, verbose_name= "MID2", null=True, blank=True)
    mid2_end_dtm            = models.DateTimeField(verbose_name= "MID2 종료 일시", null=True, blank=True)
    sys_reg_dtm             = models.DateTimeField(verbose_name= "시스템 등록 일시", null=True, blank=True)    
    sys_upd_dtm             = models.DateTimeField(verbose_name= "시스템 수정 일시", null=True, blank=True)
    custom_goods_yn         = models.CharField(max_length = 1, verbose_name= "커스텀 상품 여부", null=True, blank=True)
    base_ymd                = models.DateField(verbose_name='기준일', null=True, blank=True)
    ld_dt                   = models.DateTimeField(verbose_name='적재일시', null=True, blank=True)

    class Meta:
        indexes = [
        	models.Index(fields=['goods_id', 'goods_stat_cd', 'mid1'], name="r_data_gb_fields_idx"),
        ]

class goods_grp_key_info(models.Model):    
    grp_key_no              = models.IntegerField(unique=True, verbose_name= "그룹 키 번호", null=True, blank=True)
    st_id                   = models.IntegerField(verbose_name= "사이트 아이디", null=True, blank=True)    
    grp_key_tp_cd           = models.CharField(max_length=10, verbose_name= "그룹 키 유형 코드", null=True, blank=True)
    grp_key_nm              = models.CharField(max_length = 300, verbose_name= "그룹 키 명", null=True, blank=True)
    sys_reg_dtm             = models.DateTimeField(verbose_name= "시스템 등록 일시", null=True, blank=True)
    sys_upd_dtm             = models.DateTimeField(verbose_name= "시스템 수정 일시", null=True, blank=True)
    base_ymd                = models.DateField(verbose_name='기준일', null=True, blank=True)
    ld_dt                   = models.DateTimeField(verbose_name='적재일시', null=True, blank=True)


class goods_price(models.Model):
    goods_prc_no            = models.IntegerField(unique=True, verbose_name= "상품 가격 번호", null=True, blank=True)
    goods_id                = models.CharField(max_length = 15, verbose_name= "상품 아이디", null=True, blank=True)
    sale_strt_dtm           = models.DateTimeField(verbose_name= "판매 시작 일시", null=True, blank=True)
    sale_end_dtm            = models.DateTimeField(verbose_name= "판매 종료 일시", null=True, blank=True)
    dc_gb_cd                = models.CharField(max_length=10, verbose_name= "할인 구분 코드", null=True, blank=True)
    sale_prc1               = models.DecimalField(verbose_name= "판매 가격1", max_digits=10, decimal_places=0, null=True, blank=True)
    sale_prc2               = models.DecimalField(verbose_name= "판매 가격2", max_digits=10, decimal_places=0, null=True, blank=True)
    sale_prc3               = models.DecimalField(verbose_name= "판매 가격3", max_digits=10, decimal_places=0, null=True, blank=True)
    sale_prc4               = models.DecimalField(verbose_name= "판매 가격4", max_digits=10, decimal_places=0, null=True, blank=True)
    dc_qty1                 = models.DecimalField(verbose_name= "할인 수량1", max_digits=5, decimal_places=0, null=True, blank=True)
    dc_qty2                 = models.DecimalField(verbose_name= "할인 수량2", max_digits=5, decimal_places=0, null=True, blank=True)
    goods_amt_tp_cd         = models.CharField(max_length=10, verbose_name= "상품 금액 유형 코드", null=True, blank=True)
    org_sale_amt            = models.DecimalField(verbose_name= "원 판매 금액", max_digits=10, decimal_places=0, null=True, blank=True)
    sale_amt                = models.DecimalField(verbose_name= "판매 금액", max_digits=10, decimal_places=0, null=True, blank=True)
    amt1                    = models.DecimalField(verbose_name= "금액1", max_digits=10, decimal_places=0, null=True, blank=True)
    amt2                    = models.DecimalField(verbose_name= "금액2", max_digits=10, decimal_places=0, null=True, blank=True)
    amt3                    = models.DecimalField(verbose_name= "금액3", max_digits=10, decimal_places=0, null=True, blank=True)
    fvr_apl_meth_cd         = models.CharField(max_length=10, verbose_name= "혜택 적용 방식 코드", null=True, blank=True)
    fvr_val                 = models.DecimalField(verbose_name= "혜택 값", max_digits=10, decimal_places=2,null=True, blank=True)
    strt_ord_qty            = models.DecimalField(verbose_name= "초기 구매 수량", max_digits=5, decimal_places=0, null=True, blank=True)
    trgt_qty                = models.DecimalField(verbose_name= "목표 수량", max_digits=5, decimal_places=0, null=True, blank=True)    
    min_ord_qty             = models.DecimalField(verbose_name= "최소 구매 수량", max_digits=5, decimal_places=0, null=True, blank=True)
    bulk_ord_end_yn         = models.CharField(max_length=1, verbose_name= "공동구매 종료 여부", null=True, blank=True)
    del_yn                  = models.CharField(max_length=1, verbose_name= "삭제 여부", null=True, blank=True)
    sys_reg_dtm             = models.DateTimeField(verbose_name= "시스템 등록 일시", null=True, blank=True)
    sys_upd_dtm             = models.DateTimeField(verbose_name= "시스템 수정 일시", null=True, blank=True)
    st_id                   = models.IntegerField(verbose_name= "사이트 아이디", null=True, blank=True)
    spl_amt                 = models.DecimalField(verbose_name= "공급 금액", max_digits=10, decimal_places=0, null=True, blank=True)
    cms_rate                = models.DecimalField(verbose_name= "수수료 율", max_digits=5, decimal_places=2,null=True, blank=True)
    base_ymd                = models.DateField(verbose_name='기준일', null=True, blank=True)
    ld_dt                   = models.DateTimeField(verbose_name='적재일시', null=True, blank=True)

    class Meta:
        indexes = [
        	models.Index(fields=['goods_id', 'sale_strt_dtm', 'sale_end_dtm'], name="r_data_gp_fields_idx"),
        ]


class plaza_base(models.Model):
    baemin_str_yn           = models.CharField(max_length = 1, verbose_name= "배민 매장 여부", null=True, blank=True)
    biz_reg_no              = models.CharField(verbose_name= "사업자 등록 번호", null=True, blank=True)
    blog_url                = models.CharField(max_length=100, verbose_name= "블로그 U", null=True, blank=True)
    branch_cd               = models.IntegerField(verbose_name= "지사 코드", null=True, blank=True)    
    builtin_yn              = models.CharField(max_length=1, verbose_name= "빌트인 여부", null=True, blank=True)
    ceo_nm                  = models.CharField(max_length=100, verbose_name= "대표자 명", null=True, blank=True)
    city_cd                 = models.IntegerField(verbose_name= "시/도 코드", null=True, blank=True)        
    closed_day              = models.CharField(max_length=300, verbose_name= "휴점일", null=True, blank=True)
    close_yn                = models.CharField(max_length = 1, verbose_name= "폐업 여부", null=True, blank=True)
    cus_rsv_yn              = models.CharField(max_length = 1, verbose_name= "상담 예약 가능 여부", null=True, blank=True)
    dtrt_cd                 = models.IntegerField(verbose_name= "구/군 코드", null=True, blank=True)
    ecar_chrg_sta_yn        = models.CharField(max_length = 1, verbose_name= "전기차 충전소 여부", null=True, blank=True)
    fax                     = models.CharField(max_length=20,  verbose_name= "팩스", null=True, blank=True)
    gc_yn                   = models.CharField(max_length = 1, verbose_name= "갤럭시 컨설턴트 유무", null=True, blank=True)
    harman_studio_yn        = models.CharField(max_length = 1, verbose_name= "하만 스튜디오 여부", null=True, blank=True)
    litd                    = models.CharField(max_length=20,  verbose_name= "경도", null=True, blank=True)
    lttd                    = models.CharField(max_length=20,  verbose_name= "위도", null=True, blank=True)
    mc_yn                   = models.CharField(max_length = 1, verbose_name= "모바일 상담사 유무", null=True, blank=True)
    oms_send_yn             = models.CharField(max_length = 1, verbose_name= "OMS 전송 여부", null=True, blank=True)
    open_dt                 = models.CharField(max_length = 11, verbose_name= "오픈 일자", null=True, blank=True)
    path_tp_cd              = models.IntegerField(verbose_name= "경로 유형 코드", null=True, blank=True)    
    pickup_yn               = models.CharField(max_length = 1, verbose_name= "픽업 가능 여부", null=True, blank=True)
    plant_code              = models.CharField(max_length=8, verbose_name= "물류 코드", null=True, blank=True)
    plaza_code              = models.CharField(max_length=8, verbose_name= "사업장 코드", null=True, blank=True)
    plaza_img_path          = models.CharField(max_length=100, verbose_name= "매장 이미지 경로", null=True, blank=True)
    plaza_info              = models.CharField(max_length=500, verbose_name= "매장 소개", null=True, blank=True)
    plaza_kind_cd           = models.CharField(max_length=10, verbose_name= "매장 종류 코드", null=True, blank=True)
    plaza_mo_img_path       = models.CharField(max_length=100, verbose_name= "매장 모바일 이미지 경로", null=True, blank=True)
    plaza_nm                = models.CharField(max_length=200, verbose_name= "매장 명", null=True, blank=True)
    plaza_no                = models.IntegerField(unique=True, verbose_name= "매장 번호", null=True, blank=True)
    plaza_scale             = models.IntegerField(verbose_name= "매장 규모", null=True, blank=True)
    plaza_tp_cd             = models.CharField(max_length=10, verbose_name= "매장 유형 코드", null=True, blank=True)
    post_cd                 = models.CharField(max_length=10, verbose_name= "지역 코드", null=True, blank=True)
    post_new                = models.CharField(max_length=7, verbose_name= "우편번호 신", null=True, blank=True)
    post_old                = models.CharField(max_length=7, verbose_name= "우편번호 구", null=True, blank=True)
    prcl_addr               = models.CharField(max_length=500, verbose_name= "지번 주소", null=True, blank=True)
    prcl_dtl_addr           = models.CharField(max_length=500, verbose_name= "지번 상세 주소", null=True, blank=True)
    prc_show_yn             = models.CharField(max_length = 1, verbose_name= "가격 표시제 여부", null=True, blank=True)
    primiere_yn             = models.CharField(max_length = 1, verbose_name= "PRIMIERE 여부", null=True, blank=True)
    public_yn               = models.CharField(max_length = 1, verbose_name= "공개 여부", null=True, blank=True)
    road_addr               = models.CharField(max_length=100, verbose_name= "도로명 주소", null=True, blank=True)
    road_dtl_addr           = models.CharField(max_length=500, verbose_name= "도로명 상세 주소", null=True, blank=True)
    samsung_care_yn         = models.CharField(max_length=1, verbose_name= "SAMSUNG CARE 여부", null=True, blank=True)
    shop_no                 = models.CharField(max_length=15, verbose_name= "거래선 코드", null=True, blank=True)
    show_yn                 = models.CharField(max_length = 1, verbose_name= "노출 여부", null=True, blank=True)
    svc_center_yn           = models.CharField(max_length = 1, verbose_name= "서비스 센터 유무", null=True, blank=True)
    svc_closed_day          = models.CharField(max_length=300,  verbose_name= "서비스센터 휴점일", null=True, blank=True)
    svc_img_path            = models.CharField(max_length=100, verbose_name= "서비스센터 이미지 경로", null=True, blank=True)
    svc_info                = models.CharField(max_length=500, verbose_name= "서비스센터 소개", null=True, blank=True)
    svc_mo_img_path         = models.CharField(max_length=100, verbose_name= "서비스센터 모바일 이미지 경로", null=True, blank=True)
    svc_nm                  = models.CharField(max_length=200, verbose_name= "서비스센터 명", null=True, blank=True)
    svc_prdt_info           = models.CharField(max_length=500, verbose_name= "서비스 제품 안내", null=True, blank=True)
    svc_tel                 = models.CharField(max_length=20,  verbose_name= "서비스센터 전화번호", null=True, blank=True)
    svc_weekday_close_time  = models.IntegerField(verbose_name= "서비스센터 평일 마감 시간", null=True, blank=True)            
    svc_weekday_open_time   = models.IntegerField(verbose_name= "서비스센터 평일 오픈 시간", null=True, blank=True)            
    svc_weekend_close_time  = models.IntegerField(verbose_name= "서비스센터 주말 마감 시간", null=True, blank=True)            
    svc_weekend_open_time   = models.IntegerField(verbose_name= "서비스센터 주말 오픈 시간", null=True, blank=True)            
    tax_rfd_yn              = models.CharField(max_length = 1, verbose_name= "세금 환불 여부", null=True, blank=True)
    tel                     = models.CharField(max_length=20,  verbose_name= "전화", null=True, blank=True)
    vd_cus_rsv_yn           = models.CharField(max_length = 1, verbose_name= "동영상 상담 예약 가능 여부", null=True, blank=True)
    weekday_close_time      = models.IntegerField(verbose_name= "평일 마감 시간", null=True, blank=True)                
    weekday_open_time       = models.IntegerField(verbose_name= "평일 오픈 시간", null=True, blank=True)                
    weekend_close_time      = models.IntegerField(verbose_name= "주말 마감 시간", null=True, blank=True)                
    weekend_open_time       = models.IntegerField(verbose_name= "주말 오픈 시간", null=True, blank=True)                
    with_pet_str_yn         = models.CharField(max_length = 1, verbose_name= "펫 동행 매장 여부", null=True, blank=True)
    sys_reg_dtm             = models.DateTimeField(verbose_name= "시스템 등록 일시", null=True, blank=True)    
    sys_upd_dtm             = models.DateTimeField(verbose_name= "시스템 수정 일시", null=True, blank=True)
    base_ymd                = models.DateField(verbose_name='기준일', null=True, blank=True)
    ld_dt                   = models.DateTimeField(verbose_name='적재일시', null=True, blank=True)


class goods_add_info(models.Model):
    goods_id                        = models.CharField(unique=True, max_length=15, verbose_name= "상품 아이디", null=True, blank=True)
    mdl_grd                         = models.CharField(max_length=10, verbose_name= "모델 등급", null=True, blank=True)
    strtg_goods_yn                  = models.CharField(max_length=1, verbose_name= "전략 상품 여부", null=True, blank=True)
    tn_img_ttl                      = models.CharField(max_length=200, verbose_name= "썸네일 제목", null=True, blank=True)
    tn_img_path                     = models.CharField(max_length=500, verbose_name= "썸네일 이미지 경로", null=True, blank=True)    
    tn_mo_img_path                  = models.CharField(max_length=500, verbose_name= "썸네일 모바일 이미지 경로", null=True, blank=True)
    bnr_img_ttl                     = models.CharField(max_length=200, verbose_name= "구매혜택 배너 제목", null=True, blank=True)    
    bnr_img_en_nm                   = models.CharField(max_length=100, verbose_name= "구매혜택 배너 영문 명", null=True, blank=True)
    bnr_img_path                    = models.CharField(max_length=500, verbose_name= "구매혜택 배너 경로", null=True, blank=True)    
    bnr_link_url                    = models.CharField(max_length=1000, verbose_name= "구매혜택 배너 URL", null=True, blank=True)
    url_link_gb_cd                  = models.CharField(max_length=10, verbose_name= "URL 링크 구분 코드", null=True, blank=True)
    guide_vd_url                    = models.CharField(max_length=1000, verbose_name= "사용가이드 동영상 URL", null=True, blank=True)
    oms_send_yn                     = models.CharField(max_length=1, verbose_name= "OMS 전송 여부", null=True, blank=True)
    goods_ep_block_yn               = models.CharField(max_length=1, verbose_name= "상품 EP 블록 여부", null=True, blank=True)
    goods_add_tp_cd                 = models.CharField(max_length=10, verbose_name= "상품 추가 유형 코드", null=True, blank=True)
    goods_add_tp_sub_cd             = models.CharField(max_length=10, verbose_name= "상품 추가 유형 서브 코드", null=True, blank=True)
    flg_strt_dtm                    = models.DateTimeField(verbose_name= "플래그 시작 일시", null=True, blank=True)
    flg_end_dtm                     = models.DateTimeField(verbose_name= "플래그 종료 일시", null=True, blank=True)
    usp_desc                        = models.CharField(max_length=1000, verbose_name= "USP 설명", null=True, blank=True)
    spec_tp_cd                      = models.CharField(max_length=10, verbose_name= "스펙 유형 코드", null=True, blank=True)
    outside_goods_nm                = models.CharField(max_length=300,  verbose_name= "외부 상품 명", null=True, blank=True)
    goods_ord_tp_cd                 = models.CharField(max_length=10, verbose_name= "상품 주문 타입 코드", null=True, blank=True)
    cnts_bg_black_yn                = models.CharField(max_length=1, verbose_name= "컨텐츠 배경 블랙 여부", null=True, blank=True)
    compare_excpt_yn                = models.CharField(max_length=1, verbose_name= "상품 스펙 비교하기 제외 여부", null=True, blank=True)    
    galaxy_club_yn                  = models.CharField(max_length=1,  verbose_name= "갤럭시 클럽 상품 여부", null=True, blank=True)    
    galaxy_club_tp_cd               = models.CharField(max_length=10, verbose_name= "갤럭시 클럽 유형 코드", null=True, blank=True)
    galaxy_club_enfoceable_yn       = models.CharField(max_length=1, verbose_name= "갤럭시클럽 권리실행 가능 여부", null=True, blank=True)
    mid3                            = models.CharField(max_length=20,  verbose_name= "(갤럭시클럽) MID3", null=True, blank=True)
    mid3_strt_dtm                   = models.DateTimeField(verbose_name= "(갤럭시클럽) MID3 시작 일시", null=True, blank=True)
    mid3_end_dtm                    = models.DateTimeField(verbose_name= "(갤럭시클럽) MID3 종료 일시", null=True, blank=True)    
    mid4                            = models.CharField(max_length=20,  verbose_name= "(갤럭시클럽) MID4", null=True, blank=True)
    mid4_strt_dtm                   = models.DateTimeField(verbose_name= "(갤럭시클럽) MID4 시작 일시", null=True, blank=True)
    mid4_end_dtm                    = models.DateTimeField(verbose_name= "(갤럭시클럽) MID4 종료 일시", null=True, blank=True)
    sys_reg_dtm                     = models.DateTimeField(verbose_name= "시스템 등록 일시", null=True, blank=True)
    sys_upd_dtm                     = models.DateTimeField(verbose_name= "시스템 수정 일시", null=True, blank=True)
    base_ymd                        = models.DateField(verbose_name='기준일', null=True, blank=True)
    ld_dt                           = models.DateTimeField(verbose_name='적재일시', null=True, blank=True)


class rltn_goods_manage(models.Model):    
    seq                             = models.TextField(unique=True, verbose_name="시퀀스 번호입니다.", null=True, blank=True)    
    mdl_code                        = models.TextField(verbose_name="모델에 대한 코드입니다.", null=True, blank=True)
    rltn_mdl_code                   = models.TextField(verbose_name="관련 모델에 대한 코드입니다.", null=True, blank=True)
    rltn_goods_tp_cd                = models.TextField(verbose_name="관련 상품 유형에 대한 코드입니다.", null=True, blank=True)
    fnet_snd_yn                     = models.TextField(verbose_name="데이터가 FNET으로 전송되었는지 여부를 나타냅니다.", null=True, blank=True)
    b2b_snd_yn                      = models.TextField(verbose_name="데이터가 B2B로 전송되었는지 여부를 나타냅니다.", null=True, blank=True)
    b2b2c_snd_yn                    = models.TextField(verbose_name="데이터가 B2B2C로 전송되었는지 여부를 나타냅니다.", null=True, blank=True)    
    del_yn                          = models.TextField(verbose_name="데이터가 삭제되었는지 여부를 나타냅니다.", null=True, blank=True)
    sys_reg_dtm                     = models.TextField(verbose_name="시스템이 등록된 날짜와 시간입니다.", null=True, blank=True)    
    sys_upd_dtm                     = models.TextField(verbose_name="시스템이 마지막으로 업데이트된 날짜와 시간입니다.", null=True, blank=True)
    base_ymd                        = models.DateField(verbose_name='기준일', null=True, blank=True)
    ld_dt                           = models.DateTimeField(verbose_name='적재일시', null=True, blank=True)


class pg_benefit_base(models.Model):
    pg_bnft_no                      = models.IntegerField(unique=True, verbose_name="결제 혜택 번호", null=True, blank=True)
    pg_bnft_nm                      = models.CharField(max_length=100,  verbose_name="결제 혜택 명", null=True, blank=True)    
    st_id                           = models.IntegerField(null=True, blank=True, verbose_name="사이트 아이디")    
    sort_seq                        = models.DecimalField(verbose_name="정렬 순서", max_digits=3, decimal_places=0, null=True, blank=True)
    bnft_tp_cd                      = models.CharField(max_length=2, verbose_name="혜택 유형 코드 (공통코드 : PG_BNFT_TP)", null=True, blank=True)
    bnft_dtl_tp_cd                  = models.CharField(max_length=2, verbose_name="혜택 유형 상세 코드 (공통코드 : PG_BNFT_DTL_TP)", null=True, blank=True)    
    disp_strt_dtm                   = models.DateTimeField(verbose_name="전시 시작 일시", null=True, blank=True)
    disp_end_dtm                    = models.DateTimeField(verbose_name="전시 종료 일시", null=True, blank=True)
    bnft_stat_cd                    = models.CharField(max_length=2, verbose_name="진행 상태 코드 (공통코드 : PG_BNFT_STAT)", null=True, blank=True)
    bnft_stat_dtm                   = models.DateTimeField(verbose_name="진행 상태 일시", null=True, blank=True)    
    cardc_cd                        = models.CharField(max_length=2, verbose_name="카드사 코드", null=True, blank=True)
    pay_means_cd                    = models.CharField(max_length=3, verbose_name="결제 수단 코드", null=True, blank=True)
    pg_bnft_msg                     = models.TextField(verbose_name="결제 혜택 문구", null=True, blank=True)
    chrg_bnft_tp_cd                 = models.CharField(max_length=2, verbose_name="청구할인 혜택 유형 코드 (공통코드 : PG_CHRG_BNFT_TP)", null=True, blank=True)
    chrg_apl_tp_cd                  = models.CharField(max_length=2, verbose_name="청구할인 적용유형 코드 (공통코드 : PG_CHRG_APL_TP)", null=True, blank=True)
    mid                             = models.CharField(max_length=20,  verbose_name="MID", null=True, blank=True)
    sys_reg_dtm                     = models.DateTimeField(verbose_name="시스템 등록 일시", null=True, blank=True)
    sys_upd_dtm                     = models.DateTimeField(verbose_name="시스템 수정 일시", null=True, blank=True)
    base_ymd                        = models.DateField(verbose_name='기준일', null=True, blank=True)
    ld_dt                           = models.DateTimeField(verbose_name='적재일시', null=True, blank=True)

    class Meta:
        indexes = [
        	models.Index(fields=['disp_strt_dtm', 'disp_end_dtm', 'bnft_stat_cd', 'pg_bnft_no', 'mid'], name="r_data_pgbbase_fields_idx"),
        ]

class pg_mid(models.Model):
    mid                             = models.CharField(unique=True, max_length=20, verbose_name="MID", null=True, blank=True)
    mid_ttl                         = models.CharField(max_length=50, verbose_name="MID 제목", null=True, blank=True)
    omni_mid                        = models.CharField(max_length=20, verbose_name="옴니 MID", null=True, blank=True)
    rglraprvl_mid                   = models.CharField(max_length=20, verbose_name="정기결재 MID", null=True, blank=True)
    mid_dc_rate                     = models.IntegerField(verbose_name="MID 할인 율", null=True, blank=True)
    comp_gb_cd                      = models.CharField(max_length=10, verbose_name="업체 구분 코드", null=True, blank=True)
    dlgt_mid                        = models.CharField(max_length=20, verbose_name="대표 MID", null=True, blank=True)    
    mid_tp_cd                       = models.CharField(max_length=10, verbose_name="MID 유형 코드", null=True, blank=True)
    istm_prd                        = models.CharField(max_length=2, verbose_name="할부 기간", null=True, blank=True)
    sys_reg_dtm                     = models.DateTimeField(verbose_name="시스템 등록 일시", null=True, blank=True)
    sys_upd_dtm                     = models.DateTimeField(verbose_name="시스템 수정 일시", null=True, blank=True)
    base_ymd                        = models.DateField(verbose_name='기준일', null=True, blank=True)
    ld_dt                           = models.DateTimeField(verbose_name='적재일시', null=True, blank=True)
        

class product_detail_spec_info(models.Model):
    mdl_code                        = models.CharField(max_length=100, verbose_name="모델 코드", null=True, blank=True)
    seq                             = models.DecimalField(verbose_name="순번", max_digits=10, decimal_places=0, null=True, blank=True)
    std_schema_id                   = models.CharField(max_length=40, verbose_name="표준 스키마 아이디", null=True, blank=True)
    ps_ver                          = models.CharField(max_length=10, verbose_name="스펙 버전", null=True, blank=True)
    std_schema_key1                 = models.CharField(max_length=40, verbose_name="표준 스키마 항목 키1", null=True, blank=True)
    attr_id1                        = models.CharField(max_length=40, verbose_name="항목 아이디1", null=True, blank=True)
    attr_nm1                        = models.CharField(max_length=200, verbose_name="항목 명1", null=True, blank=True)
    disp_nm1                        = models.CharField(max_length=200, verbose_name="노출 명1", null=True, blank=True)
    sort_seq1                       = models.DecimalField(verbose_name="정렬 순서1", max_digits=10, decimal_places=0, null=True, blank=True)
    std_schema_key2                 = models.CharField(max_length=40, verbose_name="표준 스키마 항목 키2", null=True, blank=True)
    attr_id2                        = models.CharField(max_length=40, verbose_name="항목 아이디2", null=True, blank=True)    
    attr_nm2                        = models.CharField(max_length=200, verbose_name="항목 명2", null=True, blank=True)    
    disp_nm2                        = models.CharField(max_length=200, verbose_name="노출 명2", null=True, blank=True)
    sort_seq2                       = models.DecimalField(verbose_name="정렬 순서2", max_digits=10, decimal_places=0, null=True, blank=True)
    spec_value                      = models.CharField(max_length=2000, verbose_name="스펙 값", null=True, blank=True)
    org_spec_value                  = models.CharField(max_length=2000, verbose_name="원 스펙 값", null=True, blank=True)
    is_trans                        = models.CharField(max_length=1, verbose_name="번역대상 모델여부", null=True, blank=True)
    plm_input_type                  = models.CharField(max_length=50, verbose_name="PLM 항목 유형", null=True, blank=True)
    symbol                          = models.CharField(max_length=30, verbose_name="스펙 단위 명", null=True, blank=True)    
    uom_space                       = models.CharField(max_length=1, verbose_name="단위 공백포함 여부", null=True, blank=True) 
    if_reg_dtm                      = models.DateTimeField(verbose_name="인터페이스 등록 일시", null=True, blank=True)    
    sys_reg_dtm                     = models.DateTimeField(verbose_name="시스템 등록 일시", null=True, blank=True)    
    sys_upd_dtm                     = models.DateTimeField(verbose_name="시스템 수정 일시", null=True, blank=True)
    base_ymd                        = models.DateField(verbose_name='기준일', null=True, blank=True)
    ld_dt                           = models.DateTimeField(verbose_name='적재일시', null=True, blank=True)    

    class Meta:
        unique_together = ('mdl_code', 'seq')
        indexes = [models.Index(fields=['mdl_code', 'spec_value'], name="r_data_pdsi_word_idx")]

class promotion_base(models.Model):
    prmt_no                         = models.IntegerField(unique=True, verbose_name='프로모션 번호', null=True, blank=True)
    prmt_nm                         = models.CharField(max_length=200, verbose_name='프로모션 명', null=True, blank=True)
    prmt_kind_cd                    = models.CharField(max_length=10, verbose_name='프로모션 종류 코드', null=True, blank=True)
    prmt_stat_cd                    = models.CharField(max_length=10, verbose_name='프로모션 상태 코드', null=True, blank=True)
    prmt_apl_cd                     = models.CharField(verbose_name='프로모션 적용 코드', null=True, blank=True)
    apl_val                         = models.DecimalField(verbose_name='적용 값', max_digits=10, decimal_places=2, null=True, blank=True)
    apl_val_2                       = models.DecimalField(verbose_name='적용 값 2', max_digits=10, decimal_places=2, null=True, blank=True)
    qty_section1_from               = models.DecimalField(verbose_name='수량 구간1 시작', max_digits=10, decimal_places=0, null=True, blank=True)
    qty_section1_to                 = models.DecimalField(verbose_name='수량 구간1 종료', max_digits=10, decimal_places=0, null=True, blank=True)
    qty_section2_from               = models.DecimalField(verbose_name='수량 구간2 시작', max_digits=10, decimal_places=0, null=True, blank=True)
    qty_section2_to                 = models.DecimalField(verbose_name='수량 구간2 종료', max_digits=10, decimal_places=0, null=True, blank=True)
    enuli_yn                        = models.CharField(max_length=1, verbose_name='에누리 여부', null=True, blank=True)
    lmt_qty                         = models.DecimalField(verbose_name='한정 수량', max_digits=10, decimal_places=0, null=True, blank=True)
    ord_qty                         = models.DecimalField(verbose_name='주문 수량', max_digits=10, decimal_places=0, null=True, blank=True)
    all_give_yn                     = models.CharField(max_length=1, verbose_name='전체 증정 여부', null=True, blank=True)
    frb_kind_cd                     = models.CharField(max_length=10, verbose_name='사은품 종류 코드', null=True, blank=True)
    target_sale_yn                  = models.CharField(max_length=1, verbose_name='상품 판매 여부 (사은품 재고 소진 시)', null=True, blank=True)    
    frb_content                     = models.TextField(verbose_name='사은품 내용', null=True, blank=True)
    rvs_mrg_pmt_yn                  = models.CharField(max_length=1, verbose_name='역 마진 허용 여부', null=True, blank=True)
    prmt_tg_cd                      = models.CharField(max_length=10, verbose_name='프로모션 대상 코드', null=True, blank=True)
    prmt_code                       = models.CharField(max_length=10, verbose_name='프로모션 코드', null=True, blank=True)
    apl_strt_dtm                    = models.DateTimeField(verbose_name='적용 시작 일시', null=True, blank=True)
    apl_end_dtm                     = models.DateTimeField(verbose_name='적용 종료 일시', null=True, blank=True)
    spl_comp_dvd_rate               = models.DecimalField(verbose_name='공급 업체 분담 율', max_digits=5, decimal_places=2, null=True, blank=True)
    prmt_tp_cd                      = models.CharField(max_length=3, verbose_name='프로모션 유형 코드', null=True, blank=True)
    prmt_tp_etc_cont                = models.CharField(max_length=30, verbose_name='프로모션 유형 기타', null=True, blank=True)
    prmt_bnft_ntc                   = models.TextField(verbose_name='프로모션 혜택 유의사항', null=True, blank=True)
    bndl_dup_apl_yn                 = models.CharField(max_length=1, verbose_name='번들 중복 적용 여부', null=True, blank=True)
    sys_reg_dtm                     = models.DateTimeField(verbose_name='시스템 등록 일시', null=True, blank=True)
    sys_upd_dtm                     = models.DateTimeField(verbose_name='시스템 수정 일시', null=True, blank=True)    
    base_ymd                        = models.DateField(verbose_name='기준일', null=True, blank=True)
    ld_dt                           = models.DateTimeField(verbose_name='적재일시', null=True, blank=True)


class promotion_target(models.Model):
    prmt_no                         = models.IntegerField(verbose_name='프로모션 번호', null=False, blank=False)
    apl_seq                         = models.DecimalField(verbose_name='적용 순번', max_digits=10, decimal_places=0, null=True, blank=True)
    disp_clsf_no                    = models.IntegerField(verbose_name='전시 분류 번호', null=True, blank=True)
    exhbt_no                        = models.IntegerField(verbose_name='기획전 번호', null=True, blank=True)
    goods_id                        = models.CharField(max_length=15, verbose_name='상품 아이디', null=False, blank=False)    
    comp_no                         = models.IntegerField(verbose_name='업체 번호', null=True, blank=True)
    bnd_no                          = models.IntegerField(verbose_name='브랜드 번호', null=True, blank=True)
    sys_reg_dtm                     = models.DateTimeField(verbose_name="시스템 등록 일시", null=True, blank=True)
    sys_upd_dtm                     = models.DateTimeField(verbose_name="시스템 수정 일시", null=True, blank=True)
    base_ymd                        = models.DateField(verbose_name='기준일', null=True, blank=True)
    ld_dt                           = models.DateTimeField(verbose_name='적재일시', null=True, blank=True)

    class Meta:
        unique_together = ('prmt_no', 'goods_id')
        
        
class promotion_freebie(models.Model):
    frb_qty                         = models.DecimalField(verbose_name='사은품 수량', max_digits=10, decimal_places=0, null=True, blank=True)
    frb_rmn_qty                     = models.DecimalField(verbose_name='사은품 잔여 수량', max_digits=10, decimal_places=0, null=True, blank=True)
    goods_id                        = models.CharField(max_length=15, verbose_name='상품 아이디', null=True, blank=True)
    prmt_no                         = models.IntegerField(verbose_name='프로모션 번호', null=True, blank=True)
    restore_yn                      = models.CharField(max_length=1, verbose_name='환원 여부', null=True, blank=True)
    show_yn                         = models.CharField(max_length=1, verbose_name='노출 여부', null=True, blank=True)
    sys_reg_dtm                     = models.DateTimeField(verbose_name="시스템 등록 일시", null=True, blank=True)
    sys_upd_dtm                     = models.DateTimeField(verbose_name="시스템 수정 일시", null=True, blank=True)
    base_ymd                        = models.DateField(verbose_name='기준일', null=True, blank=True)
    ld_dt                           = models.DateTimeField(verbose_name='적재일시', null=True, blank=True)

    class Meta:
        unique_together = ('prmt_no', 'goods_id')
        
        
class goods_grp_key_map(models.Model):
    goods_id                = models.CharField(max_length=15, verbose_name='상품 아이디', null=True, blank=True)
    grp_key_no              = models.IntegerField(verbose_name= "그룹 키 번호", null=True, blank=True)
    disp_prior_rank         = models.IntegerField(verbose_name='전시 우선 순위', null=True, blank=True)
    dlgt_disp_yn            = models.CharField(max_length=1, verbose_name='대표여부', null=True, blank=True)
    sys_reg_dtm             = models.DateTimeField(verbose_name="시스템 등록 일시", null=True, blank=True)
    sys_upd_dtm             = models.DateTimeField(verbose_name="시스템 수정 일시", null=True, blank=True)
    base_ymd                = models.DateField(verbose_name='기준일', null=True, blank=True)
    ld_dt                   = models.DateTimeField(verbose_name='적재일시', null=True, blank=True)    

    class Meta:
        unique_together = ('goods_id', 'grp_key_no')    

        
class uk_updated_model_list(models.Model):
    model_code              = models.CharField(verbose_name='모델코드', null=False, blank=False)
    updated_date            = models.CharField(verbose_name='시스템 변경시각', max_length=14, null=True, blank=True)
    is_use                  = models.CharField(verbose_name='Target 여부', default = 'Y', max_length=1, null=True, blank=True)
    created_on              = models.DateTimeField(verbose_name='Create', auto_now_add=True)
    updated_on              = models.DateTimeField(verbose_name='Update', auto_now=True)
        
    class Meta:
        unique_together = ('model_code',)


class uk_model_price(models.Model):
    model_code              = models.CharField(verbose_name='모델코드', null=False, blank=False)
    price                   = models.FloatField(verbose_name='가격', null=True, blank=True)
    currency                = models.CharField(verbose_name='통화', null=True, blank=True)
    stock                   = models.IntegerField(verbose_name='재고', null=True, blank=True)
    promotion_price         = models.FloatField(verbose_name='프로모션 가격', null=True, blank=True)
    tiered_price            = models.FloatField(verbose_name='티어(tier) 가격', null=True, blank=True)
    created_on              = models.DateTimeField(verbose_name='Create', auto_now_add=True)
    updated_on              = models.DateTimeField(verbose_name='Update', auto_now=True)
    salesstatus             = models.CharField(verbose_name='판매 상태', null=True, blank=True)
    available_services      = models.JSONField(verbose_name='가능한 서비스', null=True, blank=True, default=dict)
    is_value_rounded        = models.BooleanField(verbose_name='가격 반올림 여부', default=True)    
    stock_level_status      = models.CharField(verbose_name='재고 수준 상태', null=True, blank=True)
        
    class Meta:
        unique_together = ('model_code',)
        indexes = [models.Index(fields=['model_code', 'salesstatus'], name="r_data_ukmodelprice_fields_idx")]

        
class uk_product_spec_basics(models.Model):
    model_code              = models.CharField(verbose_name='모델코드', primary_key=True)
    display                 = models.CharField(verbose_name='전시여부', null=True, blank=True)
    site                    = models.CharField(verbose_name='국가', null=True, blank=True)
    is_b2c                  = models.CharField(verbose_name='B2C여부', null=True, blank=True)
    reviewcount             = models.IntegerField(verbose_name='리뷰갯수', null=True, blank=True)
    is_insurance            = models.CharField(verbose_name='보험여부', null=True, blank=True)
    creation_date           = models.DateField(verbose_name='생성일', null=True, blank=True)
    model_name              = models.CharField(verbose_name='모델명', null=True, blank=True)
    launch_date             = models.DateField(verbose_name='발매일', null=True, blank=True)
    product_desc            = models.CharField(verbose_name='제품 설명', null=True, blank=True)
    top_flag                = models.CharField(verbose_name='FLAG', null=True, blank=True)
    top_flag_period_from    = models.DateField(verbose_name='FLAG 시작일', null=True, blank=True)
    top_flag_period_to      = models.DateField(verbose_name='FLAG 종료일', null=True, blank=True)
    display_name            = models.CharField(verbose_name='발매일', null=True, blank=True)
    category_code1          = models.CharField(verbose_name='Category Code 1', null=True, blank=True, max_length=8)
    category_lv1            = models.CharField(verbose_name='Category Lv1', null=True, blank=True)
    category_code2          = models.CharField(verbose_name='Category Code 2', null=True, blank=True, max_length=8)
    category_lv2            = models.CharField(verbose_name='Category Lv2', null=True, blank=True)
    category_code3          = models.CharField(verbose_name='Category Code 3', null=True, blank=True, max_length=8)
    category_lv3            = models.CharField(verbose_name='Category Lv3', null=True, blank=True)
    product_url             = models.CharField(verbose_name='Product URL', null=True, blank=True)
    category                = models.CharField(verbose_name='Category', null=True, blank=True, max_length=8)
    category_name           = models.CharField(verbose_name='Category명', null=True, blank=True)    
    created_on              = models.DateTimeField(verbose_name='Create', auto_now_add=True)
    updated_on              = models.DateTimeField(verbose_name='Update', auto_now=True)
    package_yn              = models.CharField(verbose_name='패키지 여부', null=True, blank=True)
    usp_text                = models.TextField(verbose_name='USP', null=True, blank=True)
    package_products        = models.JSONField(verbose_name='패키지 상품', null=True, blank=True, default=dict)
    rep_image_url           = models.TextField(verbose_name='대표 이미지 URL', null=True, blank=True)
    type                    = models.CharField(verbose_name='모델 타입', null=True, blank=True)
        
    class Meta:
        unique_together = ('model_code',)
        indexes = [models.Index(fields=['category_lv1', 'category_lv2', 'category_lv3', 'model_code', 'display_name'], name="r_data_ukpsbasics_fields_idx")]

        
class uk_product_spec_spec(models.Model):
    model_code              = models.CharField(verbose_name='모델코드')
    types                   = models.CharField(verbose_name='SPEC 구분', null=True, blank=True)
    spec_type               = models.CharField(verbose_name='SPEC TYPE(LV1)', null=True, blank=True)
    spec_name               = models.CharField(verbose_name='SPEC NAME(LV2)', null=True, blank=True)
    spec_detail             = models.CharField(verbose_name='SPEC DETAIL(LV3)', null=True, blank=True)
    spec_value              = models.CharField(verbose_name='SPEC 값', null=True, blank=True)    
    created_on              = models.DateTimeField(verbose_name='Create', auto_now_add=True)
    updated_on              = models.DateTimeField(verbose_name='Update', auto_now=True)

    class Meta:
        unique_together = ('model_code', 'types', 'spec_type', 'spec_name', 'spec_detail','spec_value')
        indexes = [models.Index(fields=['model_code', 'spec_type', 'spec_value'], name="r_data_ukpsspec_fields_idx")]
        
class uk_product_spec_color(models.Model):
    model_code              = models.CharField(verbose_name='모델코드')
    colors                  = models.CharField(verbose_name='색상', null=True, blank=True)
    is_special_color        = models.CharField(verbose_name='Special Color', null=True, blank=True, default=None)
    created_on              = models.DateTimeField(verbose_name='Create', auto_now_add=True)
    updated_on              = models.DateTimeField(verbose_name='Update', auto_now=True)
        
    class Meta: 
        unique_together = ('model_code', 'colors',)
        indexes = [models.Index(fields=['model_code'], name="r_data_ukpscolor_fields_idx")]
        
class uk_product_spec_mannuals(models.Model):
    model_code              = models.CharField(verbose_name='모델코드')
    manual_name             = models.CharField(verbose_name='매뉴얼 구분', null=True, blank=True)
    manual_link             = models.CharField(verbose_name='매뉴얼 링크', null=True, blank=True)
    manual_desc             = models.CharField(verbose_name='매뉴얼 개요', null=True, blank=True)
    created_on              = models.DateTimeField(verbose_name='Create', auto_now_add=True)
    updated_on              = models.DateTimeField(verbose_name='Update', auto_now=True)
        
    class Meta:
        unique_together = ('model_code', 'manual_name', 'manual_link',)
        

class uk_order_cards_info(models.Model):
    model_code              = models.CharField(verbose_name='모델코드')
    code1                   = models.CharField(verbose_name='구매구분', null=True, blank=True)
    code_name               = models.CharField(verbose_name='구매구분 설명', null=True, blank=True)
    code2                   = models.IntegerField(verbose_name='할부 개월수', null=True, blank=True)
    commision               = models.FloatField(verbose_name='커미션', null=True, blank=True)
    min_amount              = models.FloatField(verbose_name='최소구매금액', null=True, blank=True)
    currency                = models.CharField(verbose_name='통화', null=True, blank=True)
    downpayment             = models.FloatField(verbose_name='할인값', null=True, blank=True)
    interestrate            = models.FloatField(verbose_name='이자율', null=True, blank=True)
    originalprice           = models.FloatField(verbose_name='정상가', null=True, blank=True)
    period                  = models.CharField(verbose_name='주기', null=True, blank=True)
    periodvalue             = models.FloatField(verbose_name='월 납입가', null=True, blank=True)
    purchasecost            = models.FloatField(verbose_name='구매가', null=True, blank=True)
    totalcost               = models.FloatField(verbose_name='총판매가', null=True, blank=True)
    totalinterest           = models.FloatField(verbose_name='총이자', null=True, blank=True)
    created_on              = models.DateTimeField(verbose_name='Create', auto_now_add=True)
    updated_on              = models.DateTimeField(verbose_name='Update', auto_now=True)
        
    class Meta:
        unique_together = ('model_code', 'code1', 'code2',)


class uk_store_plaza(models.Model):
    searchableid              = models.CharField(unique=True, verbose_name='검색 가능한 ID', null=True, blank=True)
    tier                      = models.CharField(verbose_name='티어', null=True, blank=True)
    name                      = models.CharField(verbose_name='스토어 명', null=True, blank=True)
    website                   = models.CharField(verbose_name='웹사이트', null=True, blank=True)
    locality                  = models.CharField(verbose_name='지역', null=True, blank=True)
    telephone	              = models.CharField(verbose_name='전화번호', null=True, blank=True)
    email                     = models.CharField(verbose_name='이메일', null=True, blank=True)
    division                  = models.CharField(verbose_name='부서', null=True, blank=True)
    openinghours              = models.CharField(verbose_name='Open/Closed 시각', null=True, blank=True)
    categories                = models.CharField(verbose_name='카테고리', null=True, blank=True)
    storetypes                = models.CharField(verbose_name='스토어 타입', null=True, blank=True)
    producttags               = models.CharField(verbose_name='상품 태그', null=True, blank=True)
    exclusiveproducts         = models.CharField(verbose_name='한정 상품', null=True, blank=True)
    excludedproducts          = models.CharField(verbose_name='제외 상품', null=True, blank=True)
    status                    = models.CharField(verbose_name='상태', null=True, blank=True)
    locationenabled           = models.BooleanField(verbose_name='위치 사용 여부', default=True)
    facebookid                = models.CharField(verbose_name='페이스북 ID', null=True, blank=True)
    instagramid               = models.CharField(verbose_name='인스타그램 ID', null=True, blank=True)
    twitterid                 = models.CharField(verbose_name='트위터 ID', null=True, blank=True)
    segment                   = models.CharField(verbose_name='세그먼트', null=True, blank=True)
    address_zip               = models.CharField(verbose_name='zipcode', null=True, blank=True)
    address_street            = models.CharField(verbose_name='street', null=True, blank=True)
    country_code              = models.CharField(verbose_name='국가 코드', null=True, blank=True)
    country_name              = models.CharField(verbose_name='국가 명', null=True, blank=True)
    country_id                = models.IntegerField(verbose_name='국가 ID', null=True, blank=True)
    coordinates_latitude      = models.FloatField(verbose_name='위도', null=True, blank=True)
    coordinates_longitude     = models.FloatField(verbose_name='경도', null=True, blank=True)
    customfields_store_pickup = models.CharField(verbose_name='픽업 가능 여부', null=True, blank=True)
    customfields_online_order = models.CharField(verbose_name='온라인 주문 가능 여부', null=True, blank=True)
    retailer_name             = models.CharField(verbose_name='리테일러 명', null=True, blank=True)
    retailer_id               = models.CharField(verbose_name='리테일러 ID', null=True, blank=True)  
    created_on                = models.DateTimeField(verbose_name='Create', auto_now_add=True)
    updated_on                = models.DateTimeField(verbose_name='Update', auto_now=True)


class product_category(models.Model):
    disp_lv1                = models.CharField(verbose_name='Display Lv1', max_length=1000, null=True, blank=True)
    disp_lv2                = models.CharField(verbose_name='Display Lv2', max_length=1000, null=True, blank=True)
    disp_lv3                = models.CharField(verbose_name='Display Lv3', max_length=1000, null=True, blank=True)
    business_unit           = models.CharField(verbose_name='Business Unit', max_length=1000, null=True, blank=True)    
    product_category_lv1    = models.CharField(verbose_name='Product Category Lv1', max_length=1000, null=True, blank=True)
    product_category_lv2    = models.CharField(verbose_name='Product Category Lv2', max_length=1000, null=True, blank=True)
    product_category_lv3    = models.CharField(verbose_name='Product Category Lv3', max_length=1000, null=True, blank=True)
    model_group_code        = models.CharField(verbose_name='Model Group Code', max_length=1000, null=True, blank=True)
    model_name              = models.CharField(verbose_name='Model Name', max_length=1000, null=True, blank=True)
    product_model           = models.CharField(verbose_name='Product Name', max_length=1000, null=True, blank=True)
    mdl_code                = models.CharField(verbose_name='Mdl Code', max_length=1000, null=True, blank=True)
    goods_id                = models.CharField(unique=True, verbose_name='Goods Id', max_length=1000, null=True, blank=True)
    goods_nm                = models.CharField(verbose_name='Goods Nm', max_length=1000, null=True, blank=True)
    color                   = models.CharField(verbose_name='Color', max_length=1000, null=True, blank=True)
    release_date            = models.DateField(verbose_name='release_date', null=True, blank=True)
    aisc_yn                 = models.CharField(verbose_name='AI 구독클럽 올인원 대상 여부', max_length=1, null=True, blank=True)
    sc_yn                   = models.CharField(verbose_name='삼성 케어 플러스 대상 여부', max_length=1, null=True, blank=True)
    gc_yn                   = models.CharField(verbose_name='갤럭시 클럽 대상 여부', max_length=1, null=True, blank=True)
    div_pay_apl_yn          = models.CharField(verbose_name='나눠서 결제 서비스 적용 여부', max_length=1, null=True, blank=True)
    goods_tp_cd             = models.CharField(verbose_name='상품 유형 코드', max_length=10, null=True, blank=True)
    goods_stat_cd           = models.CharField(verbose_name='상품 상태 코드', max_length=10, null=True, blank=True)
    show_yn                 = models.CharField(verbose_name='노출 여부', max_length=1, null=True, blank=True)    
    created_on              = models.DateTimeField(verbose_name='Create', auto_now_add=True)
    updated_on              = models.DateTimeField(verbose_name='Update', auto_now=True)
    mid1                    = models.CharField(verbose_name='MID1', max_length=1000, null=True, blank=True)
    mid1_strt_dtm           = models.DateTimeField(verbose_name='MID1 시작 일시', null=True, blank=True)
    mid1_end_dtm            = models.DateTimeField(verbose_name='MID1 종료 일시', null=True, blank=True)
    mid2                    = models.CharField(verbose_name='MID2', max_length=1000, null=True, blank=True)
    mid2_strt_dtm           = models.DateTimeField(verbose_name='MID2 시작 일시', null=True, blank=True)
    mid2_end_dtm            = models.DateTimeField(verbose_name='MID2 종료 일시', null=True, blank=True)
    pd_url                  = models.TextField(verbose_name='상품 PD URL', null=True, blank=True)
    dlgt_img_url            = models.TextField(verbose_name='대표 상품 이미지 URL', null=True, blank=True)
    set_tp_cd               = models.CharField(verbose_name='SET 상품 유형 코드', max_length=10, null=True, blank=True)

    class Meta:
        indexes = [
        	models.Index(fields=['goods_id', 'mdl_code'], name="r_data_pc_fields_idx"),
        ]  

class goods_comment(models.Model):
    goods_estm_no      = models.IntegerField(verbose_name= "상품 평가 번호", null=True, blank=True)
    st_id  			   = models.IntegerField(verbose_name= "사이트 아이디", null=True, blank=True)
    goods_id  		   = models.CharField(max_length=15, verbose_name="상품 아이디", null=True, blank=True)
    goods_cmnt_tp_cd   = models.CharField(max_length=10, verbose_name="상품평 유형 코드", null=True, blank=True)
    ttl   			   = models.CharField(max_length=300, verbose_name="제목", null=True, blank=True)
    content   		   = models.TextField(null=True, blank=True, verbose_name="내용")
    estm_sbj_cd   	   = models.CharField(max_length=10, verbose_name="평가 주제 코드", null=True, blank=True)
    estm_score   	   = models.DecimalField(verbose_name= "평가 점수", null=True, blank=True, max_digits=1, decimal_places=0)
    rcom_yn   		   = models.CharField(max_length=1, null=True, blank=True, verbose_name="추천 여부")
    best_yn   		   = models.CharField(max_length=1, null=True, blank=True, verbose_name="베스트 상품평 여부")
    hits   			   = models.IntegerField(verbose_name= "조회수", null=True, blank=True)
    estm_mbr_no   	   = models.IntegerField(verbose_name= "평가 회원 번호", null=True, blank=True)
    buy_site_cd   	   = models.CharField(max_length=10, verbose_name="구매처 코드", null=True, blank=True)
    comp_no   		   = models.IntegerField(verbose_name= "업체 번호", null=True, blank=True)
    ord_no   		   = models.CharField(max_length=20, verbose_name="주문 번호", null=True, blank=True)
    comment_type   	   = models.CharField(max_length=2, verbose_name="상품평 유형 코드 02 (공통코드:GOODS_CMNT_TP_02_CD)", null=True, blank=True)
    event_no   		   = models.IntegerField(verbose_name= "이벤트 번호", null=True, blank=True)
    sns_id   		   = models.CharField(max_length=50, verbose_name="SNS 아이디", null=True, blank=True)
    nick_nm   	   	   = models.CharField(max_length=50, verbose_name="닉네임", null=True, blank=True)
    serial_no   	   = models.CharField(max_length=100, verbose_name="시리얼 번호", null=True, blank=True)
    mdl_code   		   = models.CharField(max_length=100, verbose_name="모델 코드", null=True, blank=True)    
    sys_reg_dtm 	   = models.DateTimeField(null=True, blank=True, verbose_name="시스템 등록 일시")    
    sys_upd_dtm 	   = models.DateTimeField(null=True, blank=True, verbose_name="시스템 수정 일시")
    sys_del_yn  	   = models.CharField(max_length=1, null=True, blank=True, verbose_name="시스템 삭제 여부")    
    sys_del_dtm 	   = models.DateTimeField(null=True, blank=True, verbose_name="시스템 삭제 일시")
    sys_del_rsn 	   = models.CharField(max_length=300, verbose_name="시스템 삭제 사유", null=True, blank=True)    
    base_ymd           = models.DateField(verbose_name='기준일', null=True, blank=True)
    ld_dt              = models.DateTimeField(verbose_name='적재일시', null=True, blank=True)

    class Meta:
        unique_together = ('goods_estm_no', 'goods_id')
        indexes = [models.Index(fields=['goods_estm_no'], name="r_data_gcmnt_fields_idx")]


class card_istm_info(models.Model):
    istm_seq                = models.IntegerField(unique=True, verbose_name= "할부 순번", null=True, blank=True)
    sid                     = models.CharField(max_length=10, verbose_name="대표 SID", null=True, blank=True)
    st_id                   = models.IntegerField(verbose_name= "사이트 아이디", null=True, blank=True)
    cardc_cd                = models.CharField(max_length=10, verbose_name="카드사 코드", null=True, blank=True)
    istm_prd                = models.CharField(max_length=50, verbose_name="할부 기간", null=True, blank=True)
    no_itrst_prd            = models.CharField(max_length=50, verbose_name="무이자 기간", null=True, blank=True)
    no_itrst_strt_dt        = models.CharField(max_length=8, verbose_name="무이자 시작 일자", null=True, blank=True)
    no_itrst_end_dt         = models.CharField(max_length=8, verbose_name="무이자 종료 일자", null=True, blank=True)
    no_itrst_std_amt        = models.DecimalField(verbose_name= "무이자 기준 금액", null=True, blank=True, max_digits=10, decimal_places=0)
    long_no_itrst_prd       = models.CharField(max_length=20, verbose_name="장기 무이자 기간", null=True, blank=True)
    long_no_itrst_std_amt   = models.DecimalField(verbose_name= "장기 무이자 기준 금액", null=True, blank=True, max_digits=10, decimal_places=0)    
    sys_reg_dtm             = models.DateTimeField(null=True, blank=True, verbose_name="시스템 등록 일시")    
    sys_upd_dtm             = models.DateTimeField(null=True, blank=True, verbose_name="시스템 수정 일시")
    base_ymd                = models.DateField(verbose_name='기준일', null=True, blank=True)
    ld_dt                   = models.DateTimeField(verbose_name='적재일시', null=True, blank=True)

 
class pg_benefit_detail(models.Model):       
    pg_bnft_no     = models.IntegerField(verbose_name= "결제 혜택 번호", null=True, blank=True)
    pg_bnft_seq    = models.IntegerField(verbose_name= "결제 혜택 순번", null=True, blank=True)
    min_bnft_amt   = models.DecimalField(verbose_name= "최소 혜택 금액", null=True, blank=True, max_digits=10, decimal_places=0)
    max_bnft_amt   = models.DecimalField(verbose_name= "최대 혜택 금액", null=True, blank=True, max_digits=10, decimal_places=0)
    dc_amt         = models.DecimalField(verbose_name= "할인 금액", null=True, blank=True, max_digits=10, decimal_places=0)
    max_dc_amt     = models.DecimalField(verbose_name= "최대 할인 금액", null=True, blank=True, max_digits=10, decimal_places=0)    
    sys_reg_dtm    = models.DateTimeField(null=True, blank=True, verbose_name="시스템 등록 일시")    
    sys_upd_dtm    = models.DateTimeField(null=True, blank=True, verbose_name="시스템 수정 일시")
    base_ymd       = models.DateField(verbose_name='기준일', null=True, blank=True)
    ld_dt          = models.DateTimeField(verbose_name='적재일시', null=True, blank=True)

    class Meta:
        unique_together = ('pg_bnft_no', 'pg_bnft_seq')
        indexes = [models.Index(fields=['pg_bnft_no'], name="r_data_pgbdetail_fields_idx")]

            
class bc_conts_info(models.Model):    
    bc_conts_no     = models.IntegerField(unique=True, verbose_name= "BC 컨텐츠 번호", null=True, blank=True)
    bc_conts_gb_cd  = models.CharField(max_length=3, verbose_name="BC 컨텐츠 구분 코드", null=True, blank=True)
    bc_conts_html   = models.TextField(null=True, blank=True, verbose_name="BC 컨텐츠 HTML")
    use_yn          = models.CharField(max_length=1, null=True, blank=True, verbose_name="사용 여부")    
    sys_reg_dtm     = models.DateTimeField(null=True, blank=True, verbose_name="시스템 등록 일시")    
    sys_upd_dtm     = models.DateTimeField(null=True, blank=True, verbose_name="시스템 수정 일시")
    base_ymd        = models.DateField(verbose_name='기준일', null=True, blank=True)
    ld_dt           = models.DateTimeField(verbose_name='적재일시', null=True, blank=True)
        
        
class bc_base(models.Model):    
    bc_id                   = models.CharField(unique=True, max_length=15, verbose_name="BC 아이디", null=True, blank=True)
    st_id                   = models.IntegerField(verbose_name= "사이트 아이디", null=True, blank=True)
    bc_nm                   = models.CharField(max_length=100, verbose_name="BC 명", null=True, blank=True)
    bc_en_nm                = models.CharField(max_length=100, verbose_name="BC 영문명", null=True, blank=True)
    disp_clsf_no            = models.IntegerField(verbose_name= "전시 분류 번호", null=True, blank=True)
    disp_yn                 = models.CharField(max_length=1, null=True, blank=True, verbose_name="전시 여부")
    disp_strt_dtm           = models.DateTimeField(null=True, blank=True, verbose_name="전시 시작 일시")
    disp_end_dtm            = models.DateTimeField(null=True, blank=True, verbose_name="전시 종료 일시")
    all_cache_use_yn        = models.CharField(max_length=1, null=True, blank=True, verbose_name="전체 캐시 사용 여부")
    goods_cmnt_show_yn      = models.CharField(max_length=1, null=True, blank=True, verbose_name="상품평 노출 여부")
    prsn_attr_show_yn       = models.CharField(max_length=1, null=True, blank=True, verbose_name="개인별 항목 노출 여부")
    fast_dlvr_sign_use_yn   = models.CharField(max_length=1, null=True, blank=True, verbose_name="빠른배송 표시 노출 여부")
    dlvr_info_show_yn       = models.CharField(max_length=1, null=True, blank=True, verbose_name="배송정보 노출 여부")
    add_on_use_yn           = models.CharField(max_length=1, null=True, blank=True, verbose_name="ADD-ON 상품 사용 여부")
    trd_mdl_show_yn         = models.CharField(max_length=1, null=True, blank=True, verbose_name="트레이드인 모델 노출 여부")
    title_tag               = models.CharField(max_length=250, verbose_name="페이지 제목", null=True, blank=True)
    search_keyword          = models.TextField(null=True, blank=True, verbose_name="페이지 키워드")
    inner_search_keyword    = models.TextField(null=True, blank=True, verbose_name="내부 페이지 키워드")
    meta_description_tag    = models.CharField(max_length=1000, verbose_name="페이지 설명", null=True, blank=True)
    meta_img_path           = models.CharField(max_length=500, verbose_name="메타 이미지 경로", null=True, blank=True)
    sys_reg_dtm             = models.DateTimeField(null=True, blank=True, verbose_name="시스템 등록 일시")    
    sys_upd_dtm             = models.DateTimeField(null=True, blank=True, verbose_name="시스템 수정 일시")
    base_ymd                = models.DateField(verbose_name='기준일', null=True, blank=True)
    ld_dt                   = models.DateTimeField(verbose_name='적재일시', null=True, blank=True)

     
class bc_goods_map(models.Model):    
    bc_id         = models.CharField(max_length=15, verbose_name="BC 아이디", null=True, blank=True)
    goods_id      = models.CharField(max_length=15, verbose_name="상품 아이디", null=True, blank=True)
    dlgt_yn       = models.CharField(max_length=1, null=True, blank=True, verbose_name="대표 여부")
    sys_reg_dtm   = models.DateTimeField(null=True, blank=True, verbose_name="시스템 등록 일시")    
    sys_upd_dtm   = models.DateTimeField(null=True, blank=True, verbose_name="시스템 수정 일시")
    base_ymd      = models.DateField(verbose_name='기준일', null=True, blank=True)
    ld_dt         = models.DateTimeField(verbose_name='적재일시', null=True, blank=True)

    class Meta:
        unique_together = ('bc_id', 'goods_id')


class coupon_base(models.Model):   
    cp_no                   = models.IntegerField(unique=True, verbose_name= "쿠폰 번호", null=True, blank=True)
    cp_nm                   = models.CharField(max_length=200, verbose_name="쿠폰 명", null=True, blank=True)
    cp_dscrt                = models.CharField(max_length=2000, verbose_name="쿠폰 설명", null=True, blank=True)
    cp_kind_cd              = models.CharField(max_length=10, verbose_name="쿠폰 종류 코드", null=True, blank=True)
    cp_stat_cd              = models.CharField(max_length=10, verbose_name="쿠폰 상태 코드", null=True, blank=True)
    cp_apl_cd               = models.CharField(max_length=10, verbose_name="쿠폰 적용 코드", null=True, blank=True)
    apl_val                 = models.DecimalField(verbose_name= "적용 값", null=True, blank=True, max_digits=10, decimal_places=0)
    rvs_mrg_pmt_yn          = models.CharField(max_length=1, null=True, blank=True, verbose_name="역 마진 허용 여부")
    cp_tg_cd                = models.CharField(max_length=10, verbose_name="쿠폰 대상 코드", null=True, blank=True)
    vld_prd_cd              = models.CharField(max_length=10, verbose_name="유효 기간 코드", null=True, blank=True)
    vld_prd_strt_dtm        = models.DateTimeField(null=True, blank=True, verbose_name="유효 기간 시작 일시")
    vld_prd_end_dtm         = models.DateTimeField(null=True, blank=True, verbose_name="유효 기간 종료 일시")
    vld_prd_day             = models.DecimalField(verbose_name= "유효 기간 일", null=True, blank=True, max_digits=5, decimal_places=0)
    cp_pvd_mth_cd           = models.CharField(max_length=10, verbose_name="쿠폰 지급 방식 코드", null=True, blank=True)
    serial_omni_yn          = models.CharField(max_length=1, null=True, blank=True, verbose_name="시리얼 옴니 여부")
    easy_pay_psb_yn         = models.CharField(max_length=1, null=True, blank=True, verbose_name="간편 결제 가능 여부")
    serial_autocrt_yn       = models.CharField(max_length=1, null=True, blank=True, verbose_name="시리얼 자동생성 여부")
    serial_prefix           = models.CharField(max_length=20, verbose_name="시리얼 PREFIX", null=True, blank=True)
    serial_cpn_apl_cd       = models.CharField(max_length=2, verbose_name="시리얼 쿠폰 적용 코드", null=True, blank=True)
    duple_use_yn            = models.CharField(max_length=1, null=True, blank=True, verbose_name="중복 사용 여부")
    cp_rstr_yn              = models.CharField(max_length=1, null=True, blank=True, verbose_name="쿠폰 복원 여부")
    web_mobile_gb_cd        = models.CharField(max_length=10, verbose_name="웹 모바일 구분 코드", null=True, blank=True)
    spl_comp_dvd_rate       = models.DecimalField(verbose_name= "공급 업체 분담 율", null=True, blank=True, max_digits=5, decimal_places=2)
    isu_host_cd             = models.CharField(max_length=10, verbose_name="발급 주체 코드", null=True, blank=True)
    cp_isu_cd               = models.CharField(max_length=10, verbose_name="쿠폰 발급 코드", null=True, blank=True)
    cp_isu_qty              = models.DecimalField(verbose_name= "쿠폰 발급 수량", null=True, blank=True, max_digits=10, decimal_places=0)
    min_buy_amt             = models.DecimalField(verbose_name= "최소 구매 금액", null=True, blank=True, max_digits=10, decimal_places=0)
    max_dc_amt              = models.DecimalField(verbose_name= "최대 할인 금액", null=True, blank=True, max_digits=10, decimal_places=0)
    apl_strt_dtm            = models.DateTimeField(null=True, blank=True, verbose_name="적용 시작 일시")
    apl_end_dtm             = models.DateTimeField(null=True, blank=True, verbose_name="적용 종료 일시")
    cp_img_flnm             = models.CharField(max_length=300, verbose_name="쿠폰 이미지 파일명", null=True, blank=True)
    cp_img_pathnm           = models.CharField(max_length=100, verbose_name="쿠폰 이미지 경로명", null=True, blank=True)
    cp_show_yn              = models.CharField(max_length=1, null=True, blank=True, verbose_name="쿠폰존 노출 여부")
    multi_apl_yn            = models.CharField(max_length=1, null=True, blank=True, verbose_name="복수 적용 여부")
    max_use_cnt             = models.IntegerField(verbose_name= "최대 사용 수", null=True, blank=True)
    pvd_dpm_cd              = models.CharField(max_length=30, verbose_name="지급 부서 코드", null=True, blank=True)
    pvd_dpm_nm              = models.CharField(max_length=100, verbose_name="지급 부서 명", null=True, blank=True)
    cp_gb_cd                = models.CharField(max_length=10, verbose_name="쿠폰 구분 코드", null=True, blank=True)
    auto_pvd_dup_yn         = models.CharField(max_length=1, null=True, blank=True, verbose_name="자동지급 중복여부")
    omni_emp_no             = models.CharField(max_length=20, verbose_name="옴니 사원 번호 (라이브커머스 쿠폰 발급 사원)", null=True, blank=True)
    max_rglr_pay_apl_num    = models.IntegerField(verbose_name= "최대 정규 결제 적용 횟수", null=True, blank=True)
    rglr_pay_auto_conv_yn   = models.CharField(max_length=1, null=True, blank=True, verbose_name="정기 결제 자동 전환 여부")
    cp_tp_cd                = models.CharField(max_length=2, verbose_name= "쿠폰 유형 코드", null=True, blank=True)
    trg_mbr_grd_cd          = models.CharField(max_length=10, verbose_name="대상 회원 등급 코드", null=True, blank=True)
    cp_nm_show_yn           = models.CharField(max_length=1, null=True, blank=True, verbose_name="쿠폰 명 노출 여부")
    ios_app_show_yn         = models.CharField(max_length=1, null=True, blank=True, verbose_name="iOS APP 노출 여부")
    dlvrc_dc_yn             = models.CharField(max_length=1, null=True, blank=True, verbose_name="배송비 할인 여부")
    aisc_ssb_yn             = models.CharField(max_length=1, null=True, blank=True, verbose_name="(AI 구독클럽) 구독 여부")
    sys_reg_dtm             = models.DateTimeField(null=True, blank=True, verbose_name="시스템 등록 일시")    
    sys_upd_dtm             = models.DateTimeField(null=True, blank=True, verbose_name="시스템 수정 일시")
    base_ymd                = models.DateField(verbose_name='기준일', null=True, blank=True)
    ld_dt                   = models.DateTimeField(verbose_name='적재일시', null=True, blank=True)


class coupon_target(models.Model):        
    cp_no          = models.IntegerField(verbose_name= "쿠폰 번호", null=True, blank=True)
    apl_seq        = models.DecimalField(verbose_name= "적용 순번", null=True, blank=True, max_digits=5, decimal_places=0)
    disp_clsf_no   = models.IntegerField(verbose_name= "전시 분류 번호", null=True, blank=True)
    exhbt_no       = models.IntegerField(verbose_name= "기획전 번호", null=True, blank=True)
    goods_id       = models.CharField(max_length=15, verbose_name="상품 아이디", null=True, blank=True)
    comp_no        = models.IntegerField(verbose_name= "업체 번호", null=True, blank=True)
    bnd_no         = models.IntegerField(verbose_name= "브랜드 번호", null=True, blank=True)
    dlgt_yn        = models.CharField(max_length=1, null=True, blank=True, verbose_name="대표 여부")
    sys_reg_dtm    = models.DateTimeField(null=True, blank=True, verbose_name="시스템 등록 일시")    
    sys_upd_dtm    = models.DateTimeField(null=True, blank=True, verbose_name="시스템 수정 일시")
    base_ymd       = models.DateField(verbose_name='기준일', null=True, blank=True)
    ld_dt          = models.DateTimeField(verbose_name='적재일시', null=True, blank=True)

    class Meta:
        unique_together = ('cp_no', 'apl_seq')


class display_ctg_caution(models.Model):        
    disp_clsf_no   = models.IntegerField(verbose_name= "전시 분류 번호", null=True, blank=True)
    seq            = models.DecimalField(verbose_name= "순번", null=True, blank=True, max_digits=5, decimal_places=0)
    title          = models.CharField(max_length=100, verbose_name="타이틀", null=True, blank=True)
    content        = models.TextField(null=True, blank=True, verbose_name="내용")
    prior_rank     = models.DecimalField(verbose_name= "우선 순위", null=True, blank=True, max_digits=5, decimal_places=0)    
    sys_reg_dtm    = models.DateTimeField(null=True, blank=True, verbose_name="시스템 등록 일시")    
    sys_upd_dtm    = models.DateTimeField(null=True, blank=True, verbose_name="시스템 수정 일시")
    base_ymd       = models.DateField(verbose_name='기준일', null=True, blank=True)
    ld_dt          = models.DateTimeField(verbose_name='적재일시', null=True, blank=True)

    class Meta:
        unique_together = ('disp_clsf_no', 'seq')


class pf_goods_list(models.Model):            
    up_disp_clsf_no        = models.IntegerField(null=True, blank=True, verbose_name="상위 전시 분류 번호")
    disp_clsf_no           = models.IntegerField(null=True, blank=True, verbose_name="전시 분류 번호")
    goods_id               = models.CharField(max_length=15, verbose_name= "상품 번호", null=True, blank=True)
    goods_nm               = models.CharField(max_length=300, verbose_name= "상품 명", null=True, blank=True)
    goods_tp_cd            = models.CharField(max_length=10, verbose_name= "상품 유형 코드", null=True, blank=True)
    mdl_code               = models.CharField(max_length=100, verbose_name= "모델 코드", null=True, blank=True)
    goods_stat_cd          = models.CharField(max_length=10, verbose_name= "상품 상태 코드", null=True, blank=True)
    comp_no                = models.IntegerField(null=True, blank=True, verbose_name="업체 번호")
    sale_strt_dtm          = models.DateTimeField(verbose_name= "판매 시작 일시", null=True, blank=True)
    hits                   = models.IntegerField(verbose_name= "조회수", null=True, blank=True)
    en_grp_key_no          = models.IntegerField(verbose_name= "영문명 그룹 키 번호", null=True, blank=True)
    disp_grp_key_no        = models.IntegerField(verbose_name= "전시명 그룹 키 번호", null=True, blank=True)
    dlgt_disp_yn           = models.CharField(max_length=1, verbose_name= "대표 전시 여부", null=True, blank=True)
    ctg_rank               = models.IntegerField(verbose_name= "DISPLAY_GOODS 전시 우선 순위", null=True, blank=True)
    disp_prior_rank        = models.IntegerField(null=True, blank=True, verbose_name="goods_grp_key_map 전시 우선 순위")
    f_sort_seq1            = models.IntegerField(null=True, blank=True, verbose_name="MAP-IA 정렬 순서")
    f_sort_seq2            = models.IntegerField(null=True, blank=True, verbose_name="MAP-FMY 정렬 순서")
    bspk_goods_yn          = models.CharField(max_length=1, verbose_name= "비스포크 상품 여부", null=True, blank=True)
    watch_goods_yn         = models.CharField(max_length=1, verbose_name= "워치 상품 여부", null=True, blank=True)
    goods_add_tp_cd        = models.CharField(max_length=1000, verbose_name= "상품 추가 유형 서브 코드", null=True, blank=True)
    usp_desc               = models.CharField(max_length=1000, verbose_name= "USP 설명", null=True, blank=True)
    itdc_msg1              = models.CharField(max_length=1000, verbose_name= "안내 메세지1", null=True, blank=True)
    goods_add_tp_sub_cd    = models.CharField(max_length=10, verbose_name= "상품 추가 유형 서브 코드", null=True, blank=True)
    online_store_only_yn   = models.CharField(max_length=1, verbose_name= "온라인 전용 상품 여부", null=True, blank=True)
    custom_goods_yn        = models.CharField(max_length = 1, verbose_name= "커스텀 상품 여부", null=True, blank=True) 
    use_stk_cd             = models.CharField(max_length=10, verbose_name= "사용 재고 코드", null=True, blank=True)
    sale_stat_cd           = models.CharField(max_length=2, verbose_name= "상품 액티브 상태 코드", null=True, blank=True)
    goods_uppack_info      = models.CharField(max_length=1, verbose_name= "재고 예외 여부", null=True, blank=True)
    st_id                  = models.IntegerField(null=True, blank=True, verbose_name="사이트 아이디")
    dlvr_pck_yn            = models.CharField(max_length=1, verbose_name= "배송 픽업 여부", null=True, blank=True)
    oms_send_yn            = models.CharField(max_length = 1, verbose_name= "OMS 전송 여부", null=True, blank=True)
    mid_dc_rate            = models.IntegerField(verbose_name="MID 할인 율", null=True, blank=True)
    goods_opt_str          = models.TextField(verbose_name= "상품 패밀리 옵션 정보", null=True, blank=True)
    flag_str               = models.CharField(max_length = 1000, verbose_name= "상품 플래그 내용", null=True, blank=True)
    goods_detail_url       = models.CharField(max_length = 1000, verbose_name= "상품 url", null=True, blank=True)
    price_str              = models.CharField(max_length = 1000, verbose_name= "상품 가격 정보", null=True, blank=True)
    stock_qty              = models.IntegerField(null=True, blank=True, verbose_name="상품 재고")
    sale_price             = models.DecimalField(verbose_name= "상품 최종가", null=True, blank=True, max_digits=10, decimal_places=0)
    bspk_add_min_price     = models.DecimalField(verbose_name= "비스포크 추가상품 최저가", null=True, blank=True, max_digits=10, decimal_places=0)
    web_cp_dc_amt          = models.DecimalField(verbose_name= "웹 쿠폰 할인 가격", null=True, blank=True, max_digits=10, decimal_places=0)
    app_cp_dc_amt          = models.DecimalField(verbose_name="앱 쿠폰 할인 가격", null=True, blank=True, max_digits=10, decimal_places=0)
    app_cp_add_dc_amt      = models.DecimalField(verbose_name= "앱 쿠폰 추가 할인 가격", null=True, blank=True, max_digits=10, decimal_places=0)
    avrg_goods_cmnt_score  = models.DecimalField(verbose_name= "평균 상품평 점수", null=True, blank=True, max_digits=10, decimal_places=1)
    tot_goods_cmnt_cnt     = models.IntegerField(verbose_name="전체 상품평 갯수", null=True, blank=True)
    sys_reg_dtm            = models.DateTimeField(null=True, blank=True, verbose_name="시스템 등록 일시")    
    sys_upd_dtm            = models.DateTimeField(null=True, blank=True, verbose_name="시스템 수정 일시")
    base_ymd               = models.DateField(verbose_name='기준일', null=True, blank=True)
    ld_dt                  = models.DateTimeField(verbose_name='적재일시', null=True, blank=True)

    class Meta:
        unique_together = ('disp_clsf_no', 'goods_id')


class product_recommend(models.Model):                
    product_category_lv1 = models.CharField(verbose_name='Product Category Lv1', max_length=1000, null=True, blank=True)
    product_category_lv2 = models.CharField(verbose_name='Product Category Lv2', max_length=1000, null=True, blank=True)
    product_category_lv3 = models.CharField(verbose_name='Product Category Lv3', max_length=1000, null=True, blank=True)
    product_model        = models.CharField(verbose_name='Product Name', max_length=1000, null=True, blank=True)
    disp_clsf_nm         = models.CharField(max_length=100, null=True, blank=True, verbose_name="전시 분류 명")
    mdl_code             = models.CharField(verbose_name='Mdl Code', max_length=1000, null=True, blank=True)
    goods_id             = models.CharField(verbose_name='Goods Id', max_length=1000, null=True, blank=True)
    goods_nm             = models.CharField(verbose_name='Goods Nm', max_length=1000, null=True, blank=True)
    sale_price           = models.DecimalField(verbose_name= "상품 최종가", null=True, blank=True, max_digits=10, decimal_places=0)
    ctg_rank             = models.IntegerField(verbose_name= "DISPLAY_GOODS 전시 우선 순위", null=True, blank=True)
    sale_strt_dtm        = models.DateTimeField(verbose_name= "판매 시작 일시", null=True, blank=True)
    color                = models.CharField(verbose_name='Color', max_length=1000, null=True, blank=True) 
    release_date         = models.DateField(verbose_name='release_date', null=True, blank=True)
    sys_reg_dtm          = models.DateTimeField(null=True, blank=True, verbose_name="시스템 등록 일시")
    set_tp_cd            = models.CharField(max_length=10, verbose_name="세트 유형 코드", null=True, blank=True)
    created_on           = models.DateTimeField(verbose_name='Create', auto_now_add=True)
    updated_on           = models.DateTimeField(verbose_name='Update', auto_now=True)

    class Meta:
        indexes = [models.Index(fields=['product_category_lv1', 'product_category_lv2', 'product_category_lv3', 'mdl_code', 'goods_id', 'disp_clsf_nm', 'ctg_rank'], name="r3_data_pr_idx")]


class cis_tree(models.Model):                
    model_code          = models.CharField(verbose_name='model_code', max_length=1000, null=True, blank=True)
    plant               = models.CharField(verbose_name='plant', max_length=10, null=True, blank=True)
    division            = models.CharField(verbose_name='division', max_length=20, null=True, blank=True)
    product_group_code  = models.CharField(verbose_name='product_group_code', max_length=20, null=True, blank=True)
    product_abbr_code   = models.CharField(verbose_name='product_abbr_code', max_length=30, null=True, blank=True)
    project_code        = models.CharField(verbose_name='project_code', max_length=30, null=True, blank=True)
    model_group_code    = models.CharField(verbose_name='model_group_code', max_length=300, null=True, blank=True)
    dev_project_code    = models.CharField(verbose_name='dev_project_code', max_length=30, null=True, blank=True)
    segment             = models.CharField(verbose_name='segment', max_length=1000, null=True, blank=True)
    dev_model_code      = models.CharField(verbose_name='dev_model_code', max_length=100, null=True, blank=True)
    forecast_model_code = models.CharField(verbose_name='forecast_model_code', max_length=100, null=True, blank=True)
    basic_model         = models.CharField(verbose_name='basic_model', max_length=100, null=True, blank=True)
    material_type       = models.CharField(verbose_name='material_type', max_length=40, null=True, blank=True)
    update_person       = models.CharField(verbose_name='update_person', max_length=100, null=True, blank=True)
    company             = models.CharField(verbose_name='company', max_length=40, null=True, blank=True)
    model_name          = models.CharField(verbose_name='model_name', max_length=100, null=True, blank=True)
    product_group_desc  = models.CharField(verbose_name='product_group_desc', max_length=100, null=True, blank=True)
    product_abbr_desc   = models.CharField(verbose_name='product_abbr_desc', max_length=100, null=True, blank=True)
    product_code        = models.CharField(verbose_name='product_code', max_length=50, null=True, blank=True)
    product_name        = models.CharField(verbose_name='product_name', max_length=100, null=True, blank=True)
    project_name        = models.CharField(verbose_name='project_name', max_length=100, null=True, blank=True)
    dev_model_id        = models.CharField(verbose_name='dev_model_id', max_length=100, null=True, blank=True)
    update_time         = models.DateTimeField(null=True, blank=True, verbose_name="update_time")

    class Meta:
        unique_together = ('model_code', 'plant')


class cis_base(models.Model): 
    model_code              = models.CharField(verbose_name='model_code', max_length=50, null=True, blank=True)
    plant                   = models.CharField(verbose_name='plant', max_length=100, null=True, blank=True)
    company                 = models.CharField(verbose_name='company', max_length=40, null=True, blank=True)
    division                = models.CharField(verbose_name='division', max_length=20, null=True, blank=True)
    model_division          = models.CharField(verbose_name='model_division', max_length=20, null=True, blank=True)
    model_name              = models.CharField(verbose_name='model_name', max_length=40, null=True, blank=True)
    short_desc              = models.TextField(verbose_name= "short_desc", null=True, blank=True)
    long_desc               = models.TextField(verbose_name= "long_desc", null=True, blank=True)
    basic_model             = models.CharField(verbose_name='basic_model', max_length=50, null=True, blank=True) 
    product                 = models.CharField(verbose_name='product', max_length=50, null=True, blank=True) 
    name_e                  = models.CharField(verbose_name= "name_e", max_length=50, null=True, blank=True)
    product_class           = models.CharField(verbose_name='product_class', max_length=40, null=True, blank=True) 
    unit                    = models.CharField(verbose_name='unit', max_length=20, null=True, blank=True) 
    hs_no                   = models.CharField(verbose_name='hs_no', max_length=100, null=True, blank=True) 
    net_weight              = models.CharField(verbose_name='net_weight', max_length=20, null=True, blank=True) 
    gross_weight            = models.CharField(verbose_name='gross_weight', max_length=20, null=True, blank=True) 
    volumn                  = models.CharField(verbose_name='volumn', max_length=20, null=True, blank=True) 
    u_size                  = models.CharField(verbose_name='u_size', max_length=200, null=True, blank=True) 
    status                  = models.CharField(verbose_name='status', max_length=80, null=True, blank=True) 
    dom_exp                 = models.CharField(verbose_name='dom_exp', max_length=80, null=True, blank=True) 
    product_commodity       = models.CharField(verbose_name='product_commodity', max_length=90, null=True, blank=True) 
    sales_type              = models.CharField(verbose_name='sales_type', max_length=100, null=True, blank=True) 
    storage                 = models.CharField(verbose_name='storage', max_length=50, null=True, blank=True) 
    distribution_channel    = models.CharField(verbose_name='distribution_channel', max_length=50, null=True, blank=True) 
    sales_org               = models.CharField(verbose_name='sales_org', max_length=50, null=True, blank=True) 
    account_unit            = models.CharField(verbose_name='account_unit', max_length=20, null=True, blank=True) 
    requester               = models.CharField(verbose_name='requester', max_length=50, null=True, blank=True) 
    request_date            = models.CharField(verbose_name='request_date', max_length=80, null=True, blank=True) 
    approval_employee       = models.CharField(verbose_name='approval_employee', max_length=50, null=True, blank=True) 
    approval_date           = models.CharField(verbose_name='approval_date', max_length=80, null=True, blank=True) 
    update_person           = models.CharField(verbose_name='update_person', max_length=50, null=True, blank=True) 
    update_date             = models.CharField(verbose_name='update_date', max_length=80, null=True, blank=True) 
    inch                    = models.CharField(verbose_name='inch', max_length=50, null=True, blank=True) 
    ean_code                = models.CharField(verbose_name='ean_code', max_length=130, null=True, blank=True) 
    upc_code                = models.CharField(verbose_name='upc_code', max_length=50, null=True, blank=True) 
    confirmed_drop_date     = models.CharField(verbose_name='confirmed_drop_date', max_length=80, null=True, blank=True) 
    svc_confirmed_drop_date = models.CharField(verbose_name='svc_confirmed_drop_date', max_length=80, null=True, blank=True) 
    global_status           = models.CharField(verbose_name='global_status', max_length=50, null=True, blank=True) 
    status_modified_date    = models.CharField(verbose_name='status_modified_date', max_length=80, null=True, blank=True) 
    status_modified_by      = models.CharField(verbose_name='status_modified_by', max_length=50, null=True, blank=True) 
    gpm_code                = models.CharField(verbose_name='gpm_code', max_length=30, null=True, blank=True) 
    product_in_division     = models.CharField(verbose_name='product_in_division', max_length=20, null=True, blank=True) 
    buffer                  = models.CharField(verbose_name='buffer', max_length=500, null=True, blank=True) 
    sra                     = models.CharField(verbose_name='sra', max_length=80, null=True, blank=True) 
    sales_drop_date         = models.CharField(verbose_name='sales_drop_date', max_length=80, null=True, blank=True) 
    global_p_status         = models.CharField(verbose_name='global_p_status', max_length=50, null=True, blank=True) 
    rts                     = models.CharField(verbose_name='rts', max_length=50, null=True, blank=True) 
    rsra                    = models.CharField(verbose_name='rsra', max_length=50, null=True, blank=True) 
    rts_init_date           = models.CharField(verbose_name='rts_init_date', max_length=80, null=True, blank=True) 
    sra_init_date           = models.CharField(verbose_name='sra_init_date', max_length=80, null=True, blank=True) 
    sra_dev_date            = models.CharField(verbose_name='sra_dev_date', max_length=80, null=True, blank=True) 
    rts_com_date            = models.CharField(verbose_name='rts_com_date', max_length=80, null=True, blank=True) 
    sra_com_date            = models.CharField(verbose_name='sra_com_date', max_length=80, null=True, blank=True) 
    rts_update_date         = models.CharField(verbose_name='rts_update_date', max_length=80, null=True, blank=True) 
    sra_update_date         = models.CharField(verbose_name='sra_update_date', max_length=80, null=True, blank=True) 
    buyer_name              = models.CharField(verbose_name='buyer_name', max_length=350, null=True, blank=True) 
    prod_dev_plant          = models.CharField(verbose_name='prod_dev_plant', max_length=100, null=True, blank=True) 
    forecast_model_code     = models.CharField(verbose_name='forecast_model_code', max_length=140, null=True, blank=True) 
    model_group_code        = models.CharField(verbose_name='model_group_code', max_length=210, null=True, blank=True)
    necessity_ehms_app      = models.CharField(verbose_name='necessity_ehms_app', max_length=100, null=True, blank=True)
    ehms_confirm_flag       = models.CharField(verbose_name='ehms_confirm_flag', max_length=50, null=True, blank=True)
    ehms_confirm_date       = models.CharField(verbose_name='ehms_confirm_date', max_length=80, null=True, blank=True)
    ehms_confirm_user       = models.CharField(verbose_name='ehms_confirm_user', max_length=140, null=True, blank=True)
    ehms_issued_vendor      = models.CharField(verbose_name='ehms_issued_vendor', max_length=50, null=True, blank=True)
    global_material_type    = models.CharField(verbose_name='global_material_type', max_length=40, null=True, blank=True)
    non_std_bar             = models.CharField(verbose_name='non_std_bar', max_length=13, null=True, blank=True)
    cm_ind                  = models.CharField(verbose_name='cm_ind', max_length=20, null=True, blank=True)
    product_name_marketing  = models.CharField(verbose_name='product_name_marketing', max_length=350, null=True, blank=True)
    bom_confirmed_date      = models.CharField(verbose_name='bom_confirmed_date', max_length=80, null=True, blank=True)
    fmp_date                = models.CharField(verbose_name='fmp_date', max_length=80, null=True, blank=True)
    u_width                 = models.CharField(verbose_name='u_width', max_length=60, null=True, blank=True)
    u_length                = models.CharField(verbose_name='u_length', max_length=100, null=True, blank=True)
    u_height                = models.CharField(verbose_name='u_height', max_length=60, null=True, blank=True)
    product_hier            = models.CharField(verbose_name='product_hier', max_length=140, null=True, blank=True)
    hs_number_p             = models.CharField(verbose_name='hs_number_p', max_length=50, null=True, blank=True)
    brand_type              = models.CharField(verbose_name='brand_type', max_length=100, null=True, blank=True)
    urgency_order           = models.CharField(verbose_name='urgency_order', max_length=100, null=True, blank=True)
    app_info_flag           = models.CharField(verbose_name='app_info_flag', max_length=100, null=True, blank=True)
    eanyn                   = models.CharField(verbose_name='eanyn', max_length=1, null=True, blank=True)
    upcyn                   = models.CharField(verbose_name='upcyn', max_length=1, null=True, blank=True)
    create_person           = models.CharField(verbose_name='create_person', max_length=50, null=True, blank=True)
    create_date             = models.CharField(verbose_name='create_date', max_length=80, null=True, blank=True)
    search_vector           = SearchVectorField(null=True)
    update_time             = models.DateTimeField(null=True, blank=True, verbose_name="update_time")

    class Meta:
        unique_together = ('model_code', 'plant')     
        indexes = [
            models.Index(fields=['model_code','model_group_code'], name="cis_base_idx"),
            # GinIndex(fields=['search_vector'], name='model_group_code_fts_idx')  # Full Text Search 인덱스 추가
        ]


class uk_product_recommend_org(models.Model): 
    site_cd = models.CharField(verbose_name='site_cd', max_length=2, null=True, blank=True)
    type_name = models.CharField(verbose_name='type_name', max_length=26, null=True, blank=True)
    subtype_name = models.CharField(verbose_name='subtype_name', max_length=7, null=True, blank=True)
    family_name = models.CharField(verbose_name='family_name', max_length=121, null=True, blank=True)
    marketing_name = models.CharField(verbose_name='marketing_name', max_length=125, null=True, blank=True)
    representative_model = models.CharField(verbose_name='representative_model', max_length=20, null=True, blank=True)
    sorting_no = models.IntegerField(verbose_name='sorting_no', null=True, blank=True)  

    class Meta:
        unique_together = ('type_name', 'representative_model')  


class uk_product_recommend(models.Model): 
    site_cd = models.CharField(verbose_name='site_cd', max_length=2, null=True, blank=True)
    type_name = models.CharField(verbose_name='type_name', max_length=26, null=True, blank=True)
    subtype_name = models.CharField(verbose_name='subtype_name', max_length=7, null=True, blank=True)
    family_name = models.CharField(verbose_name='family_name', max_length=121, null=True, blank=True)
    marketing_name = models.CharField(verbose_name='marketing_name', max_length=125, null=True, blank=True)
    representative_model = models.CharField(verbose_name='representative_model', max_length=20, null=True, blank=True)
    sorting_no = models.IntegerField(verbose_name='sorting_no', null=True, blank=True)    
    category_lv1 = models.CharField(verbose_name='Category Lv1', null=True, blank=True)    
    category_lv2 = models.CharField(verbose_name='Category Lv2', null=True, blank=True)    
    category_lv3 = models.CharField(verbose_name='Category Lv3', null=True, blank=True)
    launch_date = models.DateField(verbose_name='Launch Date', null=True, blank=True)

    class Meta:
        unique_together = ('type_name', 'representative_model')
        indexes = [models.Index(fields=['category_lv1', 'category_lv2', 'category_lv3', 'marketing_name', 'representative_model', 'sorting_no'], name="r_data_uk_pr_idx")]


class aisc_goods_base(models.Model): 
    ssb_goods_id = models.CharField(unique=True, verbose_name='구독 상품 아이디', max_length=15, null=True, blank=True)
    mdl_code     = models.CharField(verbose_name='모델 코드', max_length=20, null=True, blank=True)
    seg_cd1      = models.CharField(verbose_name='세그먼트 코드1', max_length=2, null=True, blank=True)
    seg_cd2      = models.CharField(verbose_name='세그먼트 코드2', max_length=2, null=True, blank=True)
    seg_cd3      = models.CharField(verbose_name='세그먼트 코드3', max_length=2, null=True, blank=True)
    mst_goods_id = models.CharField(verbose_name='마스터 상품 아이디', max_length=15, null=True, blank=True)
    comp_no      = models.IntegerField(verbose_name="업체 번호", null=True, blank=True)
    sys_reg_dtm  = models.DateTimeField(null=True, blank=True, verbose_name="시스템 등록 일시")    
    sys_upd_dtm  = models.DateTimeField(null=True, blank=True, verbose_name="시스템 수정 일시")
    base_ymd     = models.DateField(verbose_name='기준일', null=True, blank=True)
    ld_dt        = models.DateTimeField(verbose_name='적재일시', null=True, blank=True)
 

class aisc_service_goods_base(models.Model): 
    ssb_svc_seq    = models.IntegerField(verbose_name='구독 서비스 순번', null=True, blank=True)    
    svc_goods_id   = models.CharField(verbose_name='서비스 상품 아이디', max_length=15, null=True, blank=True)    
    svc_mdl_code   = models.CharField(verbose_name='서비스 상품 모델 코드', max_length=100, null=True, blank=True)    
    ssb_goods_id   = models.CharField(verbose_name='구독 상품 아이디', max_length=15, null=True, blank=True)    
    svc_no         = models.IntegerField(verbose_name='서비스 번호', null=True, blank=True)    
    cntr_prd       = models.IntegerField(verbose_name='계약 기간', null=True, blank=True)    
    svc_tp_cd      = models.CharField(verbose_name='서비스 유형 코드', max_length=10, null=True, blank=True)    
    svc_term       = models.IntegerField(verbose_name='서비스 주기', null=True, blank=True)    
    svc_goods_desc = models.TextField(verbose_name='서비스 상품 설명', null=True, blank=True)    
    sale_prc       = models.IntegerField(verbose_name='판매 가', null=True, blank=True)    
    sys_reg_dtm    = models.DateTimeField(null=True, blank=True, verbose_name="시스템 등록 일시")    
    sys_upd_dtm    = models.DateTimeField(null=True, blank=True, verbose_name="시스템 수정 일시")
    base_ymd       = models.DateField(verbose_name='기준일', null=True, blank=True)
    ld_dt          = models.DateTimeField(verbose_name='적재일시', null=True, blank=True)  

    class Meta:
        unique_together = ('ssb_svc_seq', 'svc_goods_id')


class aisc_goods_price(models.Model): 
    ssb_prc_no     = models.IntegerField(verbose_name='구독 가격 번호', null=True, blank=True)    
    ssb_goods_id   = models.CharField(verbose_name='구독 상품 아이디', max_length=15, null=True, blank=True)    
    cntr_prd       = models.IntegerField(verbose_name='계약 기간', null=True, blank=True)    
    svc_tp_cd      = models.CharField(verbose_name='서비스 유형 코드', max_length=10, null=True, blank=True)    
    svc_term       = models.IntegerField(verbose_name='서비스 주기', null=True, blank=True)    
    tot_ssb_prc    = models.DecimalField(verbose_name='총 구독 료', max_digits=10, decimal_places=0, null=True, blank=True)    
    prd_ssb_prc    = models.DecimalField(verbose_name='제품 구독 료', max_digits=10, decimal_places=0, null=True, blank=True)    
    ssb_fvr_prc    = models.DecimalField(verbose_name='구독 료 혜택 가', max_digits=10, decimal_places=0, null=True, blank=True)    
    goods_sale_prc = models.DecimalField(verbose_name='상품 판매가 (일시불)', max_digits=10, decimal_places=0, null=True, blank=True)    
    rtn_prc        = models.DecimalField(verbose_name='회수 비', max_digits=10, decimal_places=0, null=True, blank=True)    
    prd_sale_amt   = models.DecimalField(verbose_name='제품 매출 금액', max_digits=10, decimal_places=0, null=True, blank=True)    
    adv_rvn_amt    = models.DecimalField(verbose_name='선수 수익 금액', max_digits=10, decimal_places=0, null=True, blank=True)    
    sys_reg_dtm    = models.DateTimeField(null=True, blank=True, verbose_name="시스템 등록 일시")    
    sys_upd_dtm    = models.DateTimeField(null=True, blank=True, verbose_name="시스템 수정 일시")
    base_ymd       = models.DateField(verbose_name='기준일', null=True, blank=True)
    ld_dt          = models.DateTimeField(verbose_name='적재일시', null=True, blank=True)

    class Meta:
        unique_together = ('ssb_prc_no', 'ssb_goods_id')           


class goods_cstrt_info(models.Model): 
    goods_id               = models.CharField(verbose_name='상품 아이디', max_length=15, null=True, blank=True)    
    goods_cstrt_gb_cd      = models.CharField(verbose_name='상품 구성 구분 코드', max_length=10, null=True, blank=True)    
    cstrt_goods_id         = models.CharField(verbose_name='구성 상품 아이디', max_length=15, null=True, blank=True)    
    cstrt_qty              = models.DecimalField(verbose_name='구독 상품 아이디', max_digits=5, decimal_places=0, null=True, blank=True)    
    use_yn                 = models.CharField(verbose_name='사용 여부', max_length=1, null=True, blank=True)    
    disp_prior_rank        = models.IntegerField(verbose_name='전시 순서', null=True, blank=True)    
    dlgt_goods_yn          = models.CharField(verbose_name='대표 상품 여부', max_length=1, null=True, blank=True)    
    cstrt_disp_goods_nm    = models.CharField(verbose_name='구성품의 전시 상품 명', max_length=300, null=True, blank=True)    
    conts_show_yn          = models.CharField(verbose_name='컨텐츠 노출 여부', max_length=1, null=True, blank=True)    
    sys_reg_dtm            = models.DateTimeField(verbose_name="시스템 등록 일시", null=True, blank=True)
    adv_vst_yn             = models.CharField(verbose_name='사전 방문 여부', max_length=1, null=True, blank=True)    
    cstrt_goods_ord_lmt_yn = models.CharField(verbose_name='구성 상품 주문 제한 여부', max_length=1, null=True, blank=True)    
    sys_upd_dtm            = models.DateTimeField(verbose_name= "시스템 수정 일시", null=True, blank=True)
    sale_prc               = models.DecimalField(verbose_name='판매가 (패넷)', max_digits=10, decimal_places=0, null=True, blank=True)    
    erp_prc                = models.DecimalField(verbose_name='ERP 출고가', max_digits=10, decimal_places=0, null=True, blank=True)    
    base_ymd               = models.DateField(verbose_name='기준일', null=True, blank=True)
    ld_dt                  = models.DateTimeField(verbose_name='적재일시', null=True, blank=True)

    class Meta:
        unique_together = ('goods_id', 'goods_cstrt_gb_cd', 'cstrt_goods_id') 
        indexes = [models.Index(fields=['goods_id'], name="r3_cstrt_fields_idx")]      


class code_detail(models.Model): 
    grp_cd       = models.CharField(verbose_name='그룹 코드', max_length=30, null=True, blank=True)
    dtl_cd       = models.CharField(verbose_name='상세 코드', max_length=20, null=True, blank=True)
    dtl_nm       = models.CharField(verbose_name='상세 명', max_length=50, null=True, blank=True)
    dtl_sht_nm   = models.CharField(verbose_name='상세 약어 명', max_length=30, null=True, blank=True)
    sort_seq     = models.DecimalField(verbose_name='정렬 순서', max_digits=5, decimal_places=0, null=True, blank=True)
    use_yn       = models.CharField(verbose_name='사용 여부', max_length=1, null=True, blank=True)
    usr_dfn1_val = models.TextField(verbose_name='사용자 정의1 값', null=True, blank=True)
    usr_dfn2_val = models.TextField(verbose_name='사용자 정의2 값', null=True, blank=True)
    usr_dfn3_val = models.TextField(verbose_name='사용자 정의3 값', null=True, blank=True)
    usr_dfn4_val = models.TextField(verbose_name='사용자 정의4 값', null=True, blank=True)
    usr_dfn5_val = models.TextField(verbose_name='사용자 정의5 값', null=True, blank=True)
    sys_reg_dtm  = models.DateTimeField(null=True, blank=True, verbose_name="시스템 등록 일시")    
    sys_upd_dtm  = models.DateTimeField(null=True, blank=True, verbose_name="시스템 수정 일시")
    sys_del_yn   = models.CharField(verbose_name='시스템 삭제 여부', max_length=1, null=True, blank=True)    
    sys_del_dtm  = models.DateTimeField(verbose_name='시스템 삭제 일시', null=True, blank=True)
    base_ymd     = models.DateField(verbose_name='기준일', null=True, blank=True)
    ld_dt        = models.DateTimeField(verbose_name='적재일시', null=True, blank=True)

    class Meta:
        unique_together = ('grp_cd', 'dtl_cd')     


class code_group(models.Model): 
    grp_cd      = models.CharField(unique=True, verbose_name='그룹 코드', max_length=30, null=True, blank=True)
    grp_nm      = models.CharField(verbose_name='그룹 명', max_length=50, null=True, blank=True)
    usr_dfn1_nm = models.CharField(verbose_name='사용자 정의1 명', max_length=50, null=True, blank=True)
    usr_dfn2_nm = models.CharField(verbose_name='사용자 정의2 명', max_length=50, null=True, blank=True)
    usr_dfn3_nm = models.CharField(verbose_name='사용자 정의3 명', max_length=50, null=True, blank=True)
    usr_dfn4_nm = models.CharField(verbose_name='사용자 정의4 명', max_length=50, null=True, blank=True)
    usr_dfn5_nm = models.CharField(verbose_name='사용자 정의5 명', max_length=50, null=True, blank=True)    
    sys_reg_dtm = models.DateTimeField(verbose_name='시스템 등록 일시', null=True, blank=True)    
    sys_upd_dtm = models.DateTimeField(verbose_name='시스템 수정 일시', null=True, blank=True)
    sys_del_yn  = models.CharField(verbose_name='시스템 삭제 여부', max_length=1, null=True, blank=True)    
    sys_del_dtm = models.DateTimeField(verbose_name='시스템 삭제 일시', null=True, blank=True)
    base_ymd    = models.DateField(verbose_name='기준일', null=True, blank=True) 
    ld_dt       = models.DateTimeField(verbose_name='적재일시', null=True, blank=True)


class goods_opt_item_map(models.Model):
    goods_id         = models.CharField(max_length=15, verbose_name= "상품 아이디", null=True, blank=True)
    prdt_opt_item_no = models.IntegerField(verbose_name= "상품 옵션 아이템 번호", null=True, blank=True)
    color_disp_yn    = models.CharField(max_length=1, verbose_name= "색상 표시 여부", null=True, blank=True)
    disp_opt_nm      = models.CharField(max_length=50, verbose_name= "표시 옵션 명", null=True, blank=True)
    show_seq         = models.IntegerField(verbose_name= "노출 순서", null=True, blank=True)
    sys_reg_dtm      = models.DateTimeField(null=True, blank=True, verbose_name="시스템 등록 일시")        
    base_ymd         = models.DateField(verbose_name='기준일', null=True, blank=True)
    ld_dt            = models.DateTimeField(verbose_name='적재일시', null=True, blank=True)

    class Meta:
        unique_together = ('goods_id', 'prdt_opt_item_no')


class st_prdt_opt(models.Model):
    prdt_opt_no    = models.IntegerField(unique=True, verbose_name= "상품 옵션 번호", null=True, blank=True)
    st_id          = models.IntegerField(verbose_name= "사이트 아이디", null=True, blank=True)
    prdt_opt_nm    = models.CharField(max_length=100, verbose_name= "상품 옵션 명", null=True, blank=True)
    prdt_opt_en_nm = models.CharField(max_length=100, verbose_name= "상품 옵션 영문 명", null=True, blank=True)
    opt_tp_cd      = models.CharField(max_length=10, verbose_name= "옵션 유형 코드", null=True, blank=True)
    pkg_opt_yn     = models.CharField(max_length=1, verbose_name= "패키지 옵션 여부", null=True, blank=True)    
    sys_reg_dtm    = models.DateTimeField(null=True, blank=True, verbose_name="시스템 등록 일시")    
    sys_upd_dtm    = models.DateTimeField(null=True, blank=True, verbose_name="시스템 수정 일시")
    base_ymd       = models.DateField(verbose_name='기준일', null=True, blank=True)
    ld_dt          = models.DateTimeField(verbose_name='적재일시', null=True, blank=True)


class st_prdt_opt_item(models.Model):
    prdt_opt_item_no    = models.IntegerField(unique=True, verbose_name= "상품 옵션 아이템 번호", null=True, blank=True)
    prdt_opt_no         = models.IntegerField(verbose_name= "상품 옵션 번호", null=True, blank=True)
    prdt_opt_item_nm    = models.CharField(max_length=100, verbose_name= "상품 옵션 아이템 명", null=True, blank=True)
    prdt_opt_item_en_nm = models.CharField(max_length=100, verbose_name= "상품 옵션 아이템 영문 명", null=True, blank=True)
    usr_dfn_val         = models.CharField(max_length=100, verbose_name= "사용자 정의 값", null=True, blank=True)
    show_seq            = models.IntegerField(verbose_name= "노출 순서", null=True, blank=True)    
    sys_reg_dtm         = models.DateTimeField(null=True, blank=True, verbose_name="시스템 등록 일시")    
    sys_upd_dtm         = models.DateTimeField(null=True, blank=True, verbose_name="시스템 수정 일시")
    base_ymd            = models.DateField(verbose_name='기준일', null=True, blank=True)
    ld_dt               = models.DateTimeField(verbose_name='적재일시', null=True, blank=True)


class tradein_used_price_info(models.Model):
    model       = models.CharField(max_length=100, verbose_name= "모델", null=True, blank=True)
    grade       = models.CharField(max_length=100, verbose_name= "등급", null=True, blank=True)
    used_prc    = models.DecimalField(verbose_name= "중고 가격", max_digits=10, decimal_places=0, null=True, blank=True)
    use_yn      = models.CharField(max_length=1, verbose_name= "사용 여부", null=True, blank=True)
    sys_reg_dtm = models.DateTimeField(null=True, blank=True, verbose_name="시스템 등록 일시")    
    sys_upd_dtm = models.DateTimeField(null=True, blank=True, verbose_name="시스템 수정 일시")
    base_ymd    = models.DateField(verbose_name='기준일', null=True, blank=True)
    ld_dt       = models.DateTimeField(verbose_name='적재일시', null=True, blank=True)

    class Meta:
        unique_together = ('model', 'grade')


class display_clsf_filter_item(models.Model):
    disp_clsf_no         = models.IntegerField(verbose_name= "전시 분류 번호", null=True, blank=True)
    filter_no            = models.IntegerField(verbose_name= "필터 번호", null=True, blank=True)
    filter_item_no       = models.IntegerField(verbose_name= "필터 아이템 번호", null=True, blank=True)
    filter_item_nm       = models.CharField(max_length=100, verbose_name= "필터 아이템 명", null=True, blank=True)
    filter_item_en_nm    = models.CharField(max_length=100, verbose_name= "필터 아이템 영문 명", null=True, blank=True)
    sort_seq             = models.IntegerField(verbose_name= "정렬 순서", null=True, blank=True)
    color_hex_val        = models.CharField(max_length=7, verbose_name= "컬러 HEX 값", null=True, blank=True)
    filter_icon_gb_cd    = models.CharField(max_length=2, verbose_name= "PF 필터 아이콘 구분 코드", null=True, blank=True)
    filter_icon_img_path = models.CharField(max_length=500, verbose_name= "PF 필터 아이콘 이미지 경로", null=True, blank=True)
    filter_pop_gb_cd     = models.CharField(max_length=2, verbose_name= "필터 팝업 구분 코드", null=True, blank=True)
    filter_pop_ttl       = models.CharField(max_length=100, verbose_name= "필터 타이틀", null=True, blank=True)
    filter_pop_html      = models.TextField(verbose_name= "필터 HTML", null=True, blank=True)
    filter_pop_fl_path   = models.CharField(max_length=500, verbose_name= "필터 팝업 파일 경로", null=True, blank=True)
    min_val              = models.CharField(verbose_name= "최소 값", max_length=20, null=True, blank=True)
    max_val              = models.CharField(verbose_name= "최대 값", max_length=20, null=True, blank=True)
    use_yn               = models.CharField(max_length=1, verbose_name= "사용 여부", null=True, blank=True)    
    sys_reg_dtm          = models.DateTimeField(null=True, blank=True, verbose_name="시스템 등록 일시")    
    sys_upd_dtm          = models.DateTimeField(null=True, blank=True, verbose_name="시스템 수정 일시")
    base_ymd             = models.DateField(verbose_name='기준일', null=True, blank=True)
    ld_dt                = models.DateTimeField(verbose_name='적재일시', null=True, blank=True)

    class Meta:
        unique_together = ('disp_clsf_no', 'filter_no', 'filter_item_no')
        indexes = [models.Index(fields=['disp_clsf_no', 'filter_no', 'filter_item_no', 'use_yn'], name="r_data_disp_item_idx")]


class filter_item_prdt_map(models.Model):
    disp_clsf_no     = models.IntegerField(verbose_name= "전시 분류 번호", null=True, blank=True)
    filter_no        = models.IntegerField(verbose_name= "필터 번호", null=True, blank=True)
    filter_item_no   = models.IntegerField(verbose_name= "필터 아이템 번호", null=True, blank=True)
    filter_map_tp_cd = models.CharField(max_length=10, verbose_name= "필터 맵 유형 코드", null=True, blank=True)
    tg_no            = models.IntegerField(verbose_name= "대상 번호", null=True, blank=True)
    sys_reg_dtm      = models.DateTimeField(null=True, blank=True, verbose_name="시스템 등록 일시")        
    base_ymd         = models.DateField(verbose_name='기준일', null=True, blank=True)
    ld_dt            = models.DateTimeField(verbose_name='적재일시', null=True, blank=True)

    class Meta:
        unique_together = ('disp_clsf_no', 'filter_no', 'filter_item_no', 'tg_no')
        indexes = [models.Index(fields=['filter_map_tp_cd', 'disp_clsf_no', 'filter_no', 'filter_item_no'], name="r_data_filter_item_idx")]

class display_clsf_filter(models.Model):
    disp_clsf_no         = models.IntegerField(verbose_name= "전시 분류 번호", null=True, blank=True)
    filter_no            = models.IntegerField(verbose_name= "필터 번호", null=True, blank=True)
    filter_nm            = models.CharField(max_length=100, verbose_name= "필터 명", null=True, blank=True)
    filter_en_nm         = models.CharField(max_length=100, verbose_name= "필터 영문 명", null=True, blank=True)
    sort_seq             = models.IntegerField(verbose_name= "정렬 순서", null=True, blank=True)
    multi_sel_yn         = models.CharField(max_length=1, verbose_name= "다중 선택 여부", null=True, blank=True)
    pf_show_yn           = models.CharField(max_length=1, verbose_name= "PF 노출 여부", null=True, blank=True)
    filter_map_tp_cd     = models.CharField(max_length=10, verbose_name= "필터 맵 유형 코드", null=True, blank=True)
    filter_icon_gb_cd    = models.CharField(max_length=2, verbose_name= "PF 필터 아이콘 구분 코드", null=True, blank=True)
    filter_icon_img_path = models.CharField(max_length=500, verbose_name= "PF 필터 아이콘 이미지 경로", null=True, blank=True)
    filter_icon_mo_ttl   = models.CharField(max_length=100, verbose_name= "PF 필터 아이콘 마우스 오버 타이틀", null=True, blank=True)
    filter_pop_gb_cd     = models.CharField(max_length=2, verbose_name= "필터 팝업 구분 코드", null=True, blank=True)
    filter_pop_ttl       = models.CharField(max_length=100, verbose_name= "필터 타이틀", null=True, blank=True)
    filter_pop_html      = models.TextField(verbose_name= "필터 HTML", null=True, blank=True)
    filter_pop_fl_path   = models.CharField(max_length=500, verbose_name= "필터 팝업 파일 경로", null=True, blank=True)
    color_chip_yn        = models.CharField(max_length=1, verbose_name= "컬러칩 여부", null=True, blank=True)
    srch_sort_seq        = models.DecimalField(verbose_name= "검색 정렬 순서", max_digits=3, decimal_places=0, null=True, blank=True)
    srch_show_yn         = models.CharField(max_length=1, verbose_name= "검색 노출 여부", null=True, blank=True)
    sys_reg_dtm          = models.DateTimeField(null=True, blank=True, verbose_name="시스템 등록 일시")    
    sys_upd_dtm          = models.DateTimeField(null=True, blank=True, verbose_name="시스템 수정 일시")
    base_ymd             = models.DateField(verbose_name='기준일', null=True, blank=True)
    ld_dt                = models.DateTimeField(verbose_name='적재일시', null=True, blank=True)

    class Meta:
        unique_together = ('disp_clsf_no', 'filter_no')


class product_filter(models.Model):
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

    class Meta:
        indexes = [
        	models.Index(fields=['product_category_lv1', 'product_category_lv2', 'product_category_lv3', 'goods_id', 'mdl_code'], name="r_data_pfilter_idx"),
        	models.Index(fields=['filter_nm', 'filter_item_nm'], name="r_data_pfilter_filter_idx"),
            
        ]


class uk_product_filter(models.Model):
    model_code              = models.CharField(verbose_name='모델코드', max_length=255, null=True, blank=True)
    display_name            = models.CharField(verbose_name='발매일', max_length=255, null=True, blank=True)
    category_lv1            = models.CharField(verbose_name='Category Lv1', max_length=255, null=True, blank=True)
    category_lv2            = models.CharField(verbose_name='Category Lv2', max_length=255, null=True, blank=True)
    category_lv3            = models.CharField(verbose_name='Category Lv3', max_length=255, null=True, blank=True)
    filter_nm               = models.CharField(verbose_name='필터명', max_length=255, null=True, blank=True)
    filter_item_nm          = models.CharField(verbose_name='필터값', max_length=255, null=True, blank=True)
    launch_date             = models.DateField(verbose_name='출시일', null=True, blank=True)
    created_on              = models.DateTimeField(verbose_name='Create', auto_now_add=True)
    updated_on              = models.DateTimeField(verbose_name='Update', auto_now=True)
    
    class Meta:
        unique_together = ('model_code', 'filter_nm', 'filter_item_nm')
        indexes = [
        	models.Index(fields=['category_lv1', 'category_lv2', 'category_lv3', 'model_code'], name="r_data_uk_pf_idx"),
        ]


class aisc_goods_std_info(models.Model): 
    std_seq       = models.IntegerField(unique=True, verbose_name= "기준 순번", null=True, blank=True)    
    seg1          = models.CharField(max_length=100, verbose_name= "세그먼트1", null=True, blank=True)
    seg_cd1       = models.CharField(max_length=100, verbose_name= "세그먼트 코드1", null=True, blank=True)
    seg2          = models.CharField(max_length=100, verbose_name= "세그먼트2", null=True, blank=True)
    seg_cd2       = models.CharField(max_length=100, verbose_name= "세그먼트 코드2", null=True, blank=True)
    seg3          = models.CharField(max_length=100, verbose_name= "세그먼트3", null=True, blank=True)
    seg_cd3       = models.CharField(max_length=100, verbose_name= "세그먼트 코드3", null=True, blank=True)
    mdl_code      = models.CharField(max_length=100, verbose_name= "모델 코드", null=True, blank=True)
    goods_nm      = models.CharField(max_length=300, verbose_name= "상품 명(구독 / 서비스)", null=True, blank=True)
    ssb_goods_id  = models.CharField(max_length=15, verbose_name= "구독 상품 아이디", null=True, blank=True)
    svc_grp_tp_cd = models.CharField(max_length=100, verbose_name= "서비스 그룹 유형 코드 (공통코드: AI_SSB_SVC_TP)", null=True, blank=True)
    svc_goods_id  = models.CharField(max_length=15, verbose_name= "서비스 상품 아이디", null=True, blank=True)
    svc_no        = models.IntegerField(verbose_name= "서비스 순번", null=True, blank=True)
    cntr_prd      = models.IntegerField(verbose_name= "계약 기간", null=True, blank=True)
    svc_tp_cd     = models.CharField(max_length=100, verbose_name= "서비스 유형 코드 (공통코드: AI_SSB_SVC_TP)", null=True, blank=True)
    svc_term      = models.IntegerField(verbose_name= "서비스 주기", null=True, blank=True)
    sale_prc      = models.DecimalField(verbose_name= "판매 가 (VAT 포함)", max_digits=10, decimal_places=0, null=True, blank=True)
    rtn_prc       = models.DecimalField(verbose_name= "회수 비", max_digits=10, decimal_places=0, null=True, blank=True)
    prd_ssb_prc   = models.DecimalField(verbose_name= "제품 구독료", max_digits=10, decimal_places=0, null=True, blank=True)
    tot_ssb_prc   = models.DecimalField(verbose_name= "총 구독료", max_digits=10, decimal_places=0, null=True, blank=True)
    ssb_fvr_prc   = models.DecimalField(verbose_name= "구독료 혜택가", max_digits=10, decimal_places=0, null=True, blank=True)
    prd_sale_amt  = models.DecimalField(verbose_name= "제품 매출 금액", max_digits=10, decimal_places=0, null=True, blank=True)
    adv_rvn_amt   = models.DecimalField(verbose_name= "선수 수익 금액", max_digits=10, decimal_places=0, null=True, blank=True)
    mst_goods_id  = models.CharField(max_length=100, verbose_name= "마스터 상품 아이디", null=True, blank=True)
    comp_no       = models.IntegerField(verbose_name= "업체 번호", null=True, blank=True)
    use_yn        = models.CharField(max_length=1, verbose_name= "사용 여부", null=True, blank=True)
    sys_reg_dtm   = models.DateTimeField(null=True, blank=True, verbose_name="시스템 등록 일시")    
    sys_upd_dtm   = models.DateTimeField(null=True, blank=True, verbose_name="시스템 수정 일시")
    base_ymd      = models.DateField(verbose_name='기준일', null=True, blank=True)
    ld_dt         = models.DateTimeField(verbose_name='적재일시', null=True, blank=True)


class promotion_bundle_group(models.Model):
    prmt_no       = models.IntegerField(verbose_name= "프로모션 번호", null=True, blank=True)
    grp_seq       = models.DecimalField(verbose_name= "그룹 순번", max_digits=5, decimal_places=0, null=True, blank=True)
    bndl_grp_nm   = models.CharField(max_length=100, verbose_name= "번들 그룹 명", null=True, blank=True)
    sort_seq      = models.DecimalField(verbose_name= "정렬 순서",  max_digits=3, decimal_places=0, null=True, blank=True)    
    main_goods_yn = models.CharField(max_length=1, verbose_name= "메인 상품 여부", null=True, blank=True)
    lmt_qty       = models.DecimalField(verbose_name= "제한 수량",  max_digits=5, decimal_places=0, null=True, blank=True) 
    sys_reg_dtm   = models.DateTimeField(null=True, blank=True, verbose_name="시스템 등록 일시")    
    sys_upd_dtm   = models.DateTimeField(null=True, blank=True, verbose_name="시스템 수정 일시")
    base_ymd      = models.DateField(verbose_name='기준일', null=True, blank=True)
    ld_dt         = models.DateTimeField(verbose_name='적재일시', null=True, blank=True)   

    class Meta:
        unique_together = ('prmt_no', 'grp_seq')


class promotion_bundle_target(models.Model):
    prmt_no     = models.IntegerField(verbose_name= "프로모션 번호", null=True, blank=True)
    grp_seq     = models.DecimalField(verbose_name= "그룹 순번",  max_digits=5, decimal_places=0, null=True, blank=True)
    apl_seq     = models.DecimalField(verbose_name= "적용 순번",  max_digits=10, decimal_places=0, null=True, blank=True)
    prmt_apl_cd = models.CharField(max_length=10, verbose_name= "프로모션 적용 코드", null=True, blank=True)
    apl_val     = models.DecimalField(verbose_name= "적용 값",  max_digits=10, decimal_places=2, null=True, blank=True)
    sys_reg_dtm = models.DateTimeField(null=True, blank=True, verbose_name="시스템 등록 일시")    
    sys_upd_dtm = models.DateTimeField(null=True, blank=True, verbose_name="시스템 수정 일시")
    base_ymd    = models.DateField(verbose_name='기준일', null=True, blank=True)
    ld_dt       = models.DateTimeField(verbose_name='적재일시', null=True, blank=True)

    class Meta:
        unique_together = ('prmt_no', 'grp_seq', 'apl_seq')


class goods_add_on_base(models.Model):
    add_on_no       = models.IntegerField(unique=True, verbose_name= "ADD-ON 번호", null=True, blank=True)
    add_on_ttl      = models.CharField(max_length=100, verbose_name= "ADD-ON 타이틀", null=True, blank=True)
    add_on_nm       = models.CharField(max_length=100, verbose_name= "ADD-ON 명", null=True, blank=True)
    add_on_sub_copy = models.CharField(max_length=100, verbose_name= "ADD-ON 서브 카피", null=True, blank=True)
    sys_reg_dtm     = models.DateTimeField(null=True, blank=True, verbose_name="시스템 등록 일시")
    sys_upd_dtm     = models.DateTimeField(null=True, blank=True, verbose_name="시스템 수정 일시")
    base_ymd        = models.DateField(verbose_name='기준일', null=True, blank=True)
    ld_dt           = models.DateTimeField(verbose_name='적재일시', null=True, blank=True)        


class goods_add_on_category(models.Model):
    add_on_no        = models.IntegerField(unique=True, verbose_name= "ADD-ON 번호", null=True, blank=True)
    add_on_ctg_no    = models.IntegerField(verbose_name= "ADD-ON 분류 번호", null=True, blank=True)
    add_on_ctg_en_nm = models.CharField(max_length=100, verbose_name= "ADD-ON 분류 영문 명", null=True, blank=True)
    add_on_ctg_nm    = models.CharField(max_length=100, verbose_name= "ADD-ON 분류 명", null=True, blank=True)
    show_seq         = models.IntegerField(verbose_name= "노출 순서", null=True, blank=True)    
    sys_reg_dtm      = models.DateTimeField(null=True, blank=True, verbose_name="시스템 등록 일시")
    sys_upd_dtm      = models.DateTimeField(null=True, blank=True, verbose_name="시스템 수정 일시")
    base_ymd         = models.DateField(verbose_name='기준일', null=True, blank=True)
    ld_dt            = models.DateTimeField(verbose_name='적재일시', null=True, blank=True)

    class Meta:
        unique_together = ('add_on_no', 'add_on_ctg_no')


class goods_add_on_ctg_map(models.Model):  
    goods_id      = models.CharField(max_length=15, verbose_name= "상품 아이디", null=True, blank=True)  
    add_on_ctg_no = models.IntegerField(verbose_name= "ADD-ON 분류 번호", null=True, blank=True)    
    show_seq      = models.IntegerField(verbose_name= "노출 순서", null=True, blank=True)    
    sys_reg_dtm   = models.DateTimeField(null=True, blank=True, verbose_name="시스템 등록 일시")
    sys_upd_dtm   = models.DateTimeField(null=True, blank=True, verbose_name="시스템 수정 일시")
    base_ymd      = models.DateField(verbose_name='기준일', null=True, blank=True)
    ld_dt         = models.DateTimeField(verbose_name='적재일시', null=True, blank=True)

    class Meta:
        unique_together = ('goods_id', 'add_on_ctg_no')


class goods_comment_opinion(models.Model):  
    goods_estm_no = models.IntegerField(verbose_name= "상품평 번호", null=True, blank=True)
    mbr_no        = models.IntegerField(verbose_name= "회원 번호", null=True, blank=True)
    gc_opnn_gb_cd = models.CharField(max_length=10, verbose_name= "상품평 의견 구분 코드", null=True, blank=True)
    sys_reg_dtm   = models.DateTimeField(null=True, blank=True, verbose_name="시스템 등록 일시")    
    base_ymd      = models.DateField(verbose_name='기준일', null=True, blank=True)
    ld_dt         = models.DateTimeField(verbose_name='적재일시', null=True, blank=True)

    class Meta:
        unique_together = ('goods_estm_no', 'mbr_no', 'gc_opnn_gb_cd')


class goods_comment_keyword(models.Model):  
    goods_estm_no     = models.IntegerField(verbose_name= "상품평 번호", null=True, blank=True)
    goods_cmnt_kwd_cd = models.CharField(max_length=3, verbose_name= "상품평 키워드 코드", null=True, blank=True)    
    sys_reg_dtm       = models.DateTimeField(null=True, blank=True, verbose_name="시스템 등록 일시")   
    base_ymd          = models.DateField(verbose_name='기준일', null=True, blank=True)
    ld_dt             = models.DateTimeField(verbose_name='적재일시', null=True, blank=True)

    class Meta:
        unique_together = ('goods_estm_no', 'goods_cmnt_kwd_cd')


class goods_comment_summary(models.Model):  
    goods_id      = models.CharField(max_length=15, verbose_name= "상품 아이디", null=True, blank=True)        
    goods_estm_no = models.IntegerField(unique=True, verbose_name= "상품평 번호", null=True, blank=True)
    content       = models.TextField(verbose_name= "내용", null=True, blank=True)
    updated_on     = models.DateTimeField(verbose_name='Update', auto_now=True)
    embedding     = models.JSONField(verbose_name= "Embedding", null=True, blank=True, default=dict)



class conts_info(models.Model):  
    conts_no      = models.IntegerField(unique=True, verbose_name= "컨텐츠 번호", null=True, blank=True)
    conts_nm      = models.CharField(max_length=100, verbose_name= "컨텐츠 명", null=True, blank=True)
    conts_en_nm   = models.CharField(max_length=100, verbose_name= "컨텐츠 영문 명", null=True, blank=True)
    conts_kwd     = models.CharField(max_length=500, verbose_name= "컨텐츠 키워드", null=True, blank=True)
    conts_stat_cd = models.CharField(max_length=10, verbose_name= "컨텐츠 상태 코드", null=True, blank=True)
    lck_yn        = models.CharField(max_length=1, verbose_name= "잠금 여부", null=True, blank=True)
    lck_dtm       = models.DateTimeField(verbose_name= "잠금 일시", null=True, blank=True)
    lck_usr_no    = models.IntegerField(verbose_name= "잠금 사용자 번호", null=True, blank=True)
    conts_tp_cd   = models.CharField(max_length=10, verbose_name= "컨텐츠 유형 코드", null=True, blank=True)
    conts_kind_cd = models.CharField(max_length=10, verbose_name= "컨텐츠 종류 코드", null=True, blank=True)
    goods_cpt_yn  = models.CharField(max_length=1, verbose_name= "상품 컴포넌트 포함 여부", null=True, blank=True)
    htmlstr       = models.TextField(verbose_name= "HTML STR", null=True, blank=True)
    st_id         = models.IntegerField(verbose_name= "사이트 아이디", null=True, blank=True)
    disp_clsf_no  = models.IntegerField(verbose_name= "전시 분류 번호", null=True, blank=True)
    disp_strt_dtm = models.DateTimeField(verbose_name= "전시 시작 일시", null=True, blank=True)
    disp_end_dtm  = models.DateTimeField(verbose_name= "전시 종료 일시", null=True, blank=True)
    sys_reg_dtm   = models.DateTimeField(null=True, blank=True, verbose_name="시스템 등록 일시")
    sys_upd_dtm   = models.DateTimeField(null=True, blank=True, verbose_name="시스템 수정 일시")
    base_ymd      = models.DateField(verbose_name='기준일', null=True, blank=True)
    ld_dt         = models.DateTimeField(verbose_name='적재일시', null=True, blank=True)

    class Meta:
        indexes = [models.Index(fields=['conts_no'], name="r_data_conts_idx")]


class goods_conts_map(models.Model):  
    goods_id           = models.CharField(max_length=15, verbose_name= "상품 아이디", null=True, blank=True)
    conts_no           = models.IntegerField(verbose_name= "컨텐츠 번호", null=True, blank=True)
    mig_cnncl_link_url = models.CharField(max_length=1024, verbose_name= "마이그레이션 취소 링크 URL", null=True, blank=True)
    sys_reg_dtm        = models.DateTimeField(null=True, blank=True, verbose_name="시스템 등록 일시")
    base_ymd           = models.DateField(verbose_name='기준일', null=True, blank=True)
    ld_dt              = models.DateTimeField(verbose_name='적재일시', null=True, blank=True)

    class Meta:
        unique_together = ('goods_id', 'conts_no')
        indexes = [models.Index(fields=['goods_id', 'conts_no'], name="r_data_goods_conts_map_idx")]


class conts_cstrt_info(models.Model):  
    conts_cstrt_no = models.IntegerField(unique=True, verbose_name= "컨텐츠 구성 번호", null=True, blank=True)
    conts_no       = models.IntegerField(verbose_name= "컨텐츠 번호", null=True, blank=True)
    cpt_no         = models.IntegerField(verbose_name= "컴포넌트 번호", null=True, blank=True)
    cstrt_seq      = models.DecimalField(verbose_name= "구성 순번", null=True, blank=True, max_digits=5, decimal_places=0)
    ref_gb_cd      = models.CharField(max_length=10, verbose_name= "참조 구분 코드", null=True, blank=True)
    sys_reg_dtm    = models.DateTimeField(null=True, blank=True, verbose_name="시스템 등록 일시")
    sys_upd_dtm    = models.DateTimeField(null=True, blank=True, verbose_name="시스템 수정 일시")
    base_ymd       = models.DateField(verbose_name='기준일', null=True, blank=True)
    ld_dt          = models.DateTimeField(verbose_name='적재일시', null=True, blank=True)

    class Meta:        
        indexes = [models.Index(fields=['conts_no', 'cpt_no'], name="r_data_conts_cstrt_idx")]


class cpt(models.Model):  
    cpt_no               = models.IntegerField(unique=True, verbose_name= "컴포넌트 번호", null=True, blank=True)
    cpt_lyt_no           = models.IntegerField(verbose_name= "컴포넌트 레이아웃 번호", null=True, blank=True)
    cpt_nm               = models.CharField(max_length=300, verbose_name= "컴포넌트 명", null=True, blank=True)
    cpt_en_nm            = models.CharField(max_length=300, verbose_name= "컴포넌트 영문 명", null=True, blank=True)
    cpt_kwd              = models.CharField(max_length=300, verbose_name= "컴포넌트 키워드", null=True, blank=True)
    del_yn               = models.CharField(max_length=1, verbose_name= "삭제 여부", null=True, blank=True)
    lck_yn               = models.CharField(max_length=1, verbose_name= "잠금 여부", null=True, blank=True)
    lck_dtm              = models.DateTimeField(verbose_name= "잠금 일시", null=True, blank=True)    
    jsonstr              = models.TextField(verbose_name= "JSON STR", null=True, blank=True)
    htmlstr              = models.TextField(verbose_name= "HTML STR", null=True, blank=True)
    st_id                = models.IntegerField(verbose_name= "사이트 이름", null=True, blank=True)
    up_cpt_no            = models.IntegerField(verbose_name= "상위 컴포넌트 번호", null=True, blank=True)
    mig_ftrs_item_id     = models.IntegerField(verbose_name= "마이그 아이템 아이디", null=True, blank=True)
    mig_ftrs_scr_type_cd = models.CharField(max_length=20, verbose_name= "마이그 레이아웃 번호", null=True, blank=True)
    cpt_disp_tp_cd       = models.CharField(max_length=2, verbose_name= "컴포넌트 노출 유형 코드", null=True, blank=True)
    sys_reg_dtm          = models.DateTimeField(null=True, blank=True, verbose_name="시스템 등록 일시")
    sys_upd_dtm          = models.DateTimeField(null=True, blank=True, verbose_name="시스템 수정 일시")
    cpt_reg_gb_cd        = models.CharField(max_length=2, verbose_name= "컴포넌트 등록 구분 코드", null=True, blank=True)
    task_id              = models.CharField(max_length=15, verbose_name= "작업 아이디", null=True, blank=True)
    task_dtl_no          = models.IntegerField(verbose_name= "작업 상세 번호", null=True, blank=True)
    page_gb_cd           = models.CharField(max_length=2, verbose_name= "페이지 구분 코드", null=True, blank=True)
    base_ymd             = models.DateField(verbose_name='기준일', null=True, blank=True)
    ld_dt                = models.DateTimeField(verbose_name='적재일시', null=True, blank=True)

    class Meta:
        indexes = [models.Index(fields=['cpt_no'], name="r_data_cpt_idx")]


class uk_product_trade_in(models.Model):
    buying_model_code  = models.CharField(verbose_name='구매모델코드', max_length=255, null=True, blank=True)
    category           = models.CharField(verbose_name='카테고리', max_length=255, null=True, blank=True)
    brand              = models.CharField(verbose_name='브랜드', max_length=255, null=True, blank=True)
    memory             = models.CharField(verbose_name='메모리', max_length=255, null=True, blank=True)
    model              = models.CharField(verbose_name='모델', max_length=255, null=True, blank=True)
    tenant_id          = models.CharField(verbose_name='테넌트ID', max_length=255, null=True, blank=True)
    discount_min       = models.IntegerField(verbose_name='할인최소', null=True, blank=True)
    discount_max       = models.IntegerField(verbose_name='할인최대', null=True, blank=True)    
    total_discount_min = models.IntegerField(verbose_name='총할인최소', null=True, blank=True)
    total_discount_max = models.IntegerField(verbose_name='총할인최대', null=True, blank=True)
    exchange_min       = models.IntegerField(verbose_name='교환최소', null=True, blank=True)
    exchange_max       = models.IntegerField(verbose_name='교환최대', null=True, blank=True)
    total_exchange_min = models.IntegerField(verbose_name='총교환최소', null=True, blank=True)
    total_exchange_max = models.IntegerField(verbose_name='총교환최대', null=True, blank=True)
    overall_total      = models.IntegerField(verbose_name='총합계', null=True, blank=True)
    created_on         = models.DateTimeField(verbose_name='Create', auto_now_add=True)
    updated_on         = models.DateTimeField(verbose_name='Update', auto_now=True)

    class Meta:
        unique_together = ('buying_model_code', 'category', 'brand', 'memory', 'model')


class goods_comment_statistics(models.Model):
    goods_id           = models.CharField(unique=True, max_length=15, verbose_name= "상품 아이디", null=True, blank=True)
    avg_score          = models.DecimalField(verbose_name= "평균 점수", max_digits=5, decimal_places=2, null=True, blank=True)
    review_num         = models.IntegerField(verbose_name= "리뷰 수", null=True, blank=True)
    review_by_category = models.JSONField(verbose_name= "카테고리별 리뷰 수", null=True, blank=True)
    review_by_score    = models.JSONField(verbose_name= "점수별 리뷰 수", null=True, blank=True)
    updated_on         = models.DateTimeField(verbose_name='Update', auto_now=True)


class goods_notify(models.Model):
    ntf_item_id = models.CharField(max_length=15, verbose_name= "고시 항목 아이디", null=True, blank=True)
    goods_id    = models.CharField(max_length=15, verbose_name= "상품 아이디", null=True, blank=True)
    item_val    = models.CharField(max_length=1000, verbose_name= "아이템 값", null=True, blank=True)
    sys_reg_dtm = models.DateTimeField(null=True, blank=True, verbose_name="시스템 등록 일시")
    sys_upd_dtm = models.DateTimeField(null=True, blank=True, verbose_name="시스템 수정 일시")
    base_ymd     = models.DateField(verbose_name='기준일', null=True, blank=True)
    ld_dt        = models.DateTimeField(verbose_name='적재일시', null=True, blank=True)

    class Meta:
        unique_together = ('ntf_item_id', 'goods_id')


class notify_item(models.Model):
    ntf_item_id  = models.CharField(max_length=15, verbose_name= "고시 항목 아이디", null=True, blank=True)
    ntf_id       = models.CharField(max_length=15, verbose_name= "고시 아이디", null=True, blank=True)
    item_nm      = models.CharField(max_length=100, verbose_name= "항목 명", null=True, blank=True)
    input_mtd_cd = models.CharField(max_length=10, verbose_name= "입력 방법 코드", null=True, blank=True)
    dscrt        = models.CharField(max_length=100, verbose_name= "설명", null=True, blank=True)
    bigo         = models.CharField(max_length=1000, verbose_name= "비고", null=True, blank=True)
    show_seq     = models.IntegerField(verbose_name= "노출 순서", null=True, blank=True)
    sys_reg_dtm  = models.DateTimeField(null=True, blank=True, verbose_name="시스템 등록 일시")
    sys_upd_dtm  = models.DateTimeField(null=True, blank=True, verbose_name="시스템 수정 일시")
    base_ymd     = models.DateField(verbose_name='기준일', null=True, blank=True)
    ld_dt        = models.DateTimeField(verbose_name='적재일시', null=True, blank=True)

    class Meta:
        unique_together = ('ntf_item_id', 'ntf_id')


class activate_model_base(models.Model):
    mdl_code       = models.CharField(unique=True, max_length=100, verbose_name= "모델 코드", null=True, blank=True)
    key_mdl_code   = models.CharField(max_length=100, verbose_name= "키 모델 코드", null=True, blank=True)
    dlgt_mdl_code  = models.CharField(max_length=100, verbose_name= "대표 모델 코드", null=True, blank=True)
    rlvnt_mdl_code = models.CharField(max_length=100, verbose_name= "연관 모델 코드", null=True, blank=True)
    key_mdl_nm     = models.CharField(max_length=100, verbose_name= "키 모델 명", null=True, blank=True)
    use_yn         = models.CharField(max_length=1, verbose_name= "사용 여부", null=True, blank=True)
    sys_reg_dtm    = models.DateTimeField(null=True, blank=True, verbose_name="시스템 등록 일시")
    sys_upd_dtm    = models.DateTimeField(null=True, blank=True, verbose_name="시스템 수정 일시")
    base_ymd       = models.DateField(verbose_name='기준일', null=True, blank=True)
    ld_dt          = models.DateTimeField(verbose_name='적재일시', null=True, blank=True)


class activate_key_model_price(models.Model):
    key_mdl_code        = models.CharField(max_length=100, verbose_name= "키 모델 코드", null=True, blank=True)
    carrier_cd          = models.CharField(max_length=10, verbose_name= "통신사 코드", null=True, blank=True)
    m_pt_cd             = models.CharField(max_length=10, verbose_name= "요금제 코드", null=True, blank=True)
    plan_data_tp_cd     = models.CharField(max_length=10, verbose_name= "요금제 데이터 유형 코드", null=True, blank=True)
    plan_join_tp_cd     = models.CharField(max_length=10, verbose_name= "요금제 가입 유형 코드", null=True, blank=True)
    plan_dc_tp_cd       = models.CharField(max_length=10, verbose_name= "요금제 할인 유형 코드", null=True, blank=True)
    istm_prd_cd         = models.CharField(max_length=10, verbose_name= "할부 기간", null=True, blank=True)
    actv_phone_plan_seq = models.IntegerField(unique=True, verbose_name= "개통폰 요금제 정책 순번", null=True, blank=True)
    actv_phone_plan_ver = models.CharField(max_length=100, verbose_name= "개통폰 요금제 정책 버전", null=True, blank=True)
    org_prc             = models.DecimalField(verbose_name= "출고가", max_digits=10, decimal_places=0, null=True, blank=True)
    carrier_dc_amt      = models.DecimalField(verbose_name= "공시지원금", max_digits=10, decimal_places=0, null=True, blank=True)
    extra_dc_amt        = models.DecimalField(verbose_name= "추가지원금", max_digits=10, decimal_places=0, null=True, blank=True)
    change_dc_amt       = models.DecimalField(verbose_name= "전환지원금", max_digits=10, decimal_places=0, null=True, blank=True)
    dvc_org_prc         = models.DecimalField(verbose_name= "단말기 할부 원금", max_digits=10, decimal_places=0, null=True, blank=True)
    tot_itrst_amt       = models.DecimalField(verbose_name= "총 할부 수수료", max_digits=10, decimal_places=0, null=True, blank=True)
    plan_amt            = models.DecimalField(verbose_name= "통신요금", max_digits=10, decimal_places=0, null=True, blank=True)
    plan_dc_amt         = models.DecimalField(verbose_name= "요금제 할인액", max_digits=10, decimal_places=0, null=True, blank=True)
    istm_fee            = models.DecimalField(verbose_name= "할부금", max_digits=10, decimal_places=0, null=True, blank=True)
    pay_amt             = models.DecimalField(verbose_name= "납부 금액", max_digits=10, decimal_places=0, null=True, blank=True)
    sys_reg_dtm         = models.DateTimeField(null=True, blank=True, verbose_name="시스템 등록 일시")
    sys_upd_dtm         = models.DateTimeField(null=True, blank=True, verbose_name="시스템 수정 일시")    
    base_ymd            = models.DateField(verbose_name='기준일', null=True, blank=True)
    ld_dt               = models.DateTimeField(verbose_name='적재일시', null=True, blank=True)


class uk_product_comment_summary(models.Model):
    model_code       = models.CharField(max_length=1000, verbose_name= "모델 코드", null=True, blank=True)
    content          = models.TextField(verbose_name= "내용", null=True, blank=True)
    review_id        = models.IntegerField(unique=True, verbose_name= "리뷰 아이디", null=True, blank=True)
    embedding        = models.JSONField(verbose_name= "Embedding", null=True, blank=True)
    updated_on       = models.DateTimeField(verbose_name='Update', auto_now=True)


class uk_product_comment(models.Model):
    review_id        = models.IntegerField(unique=True, verbose_name= "리뷰 아이디", null=True, blank=True)
    model_code       = models.CharField(max_length=100, verbose_name= "모델 코드", null=True, blank=True)
    model_name       = models.CharField(max_length=1000, verbose_name= "모델 명", null=True, blank=True)
    submission_time  = models.DateTimeField(verbose_name= "제출 시간", null=True, blank=True)
    rating           = models.IntegerField(verbose_name= "평점", null=True, blank=True)
    content          = models.TextField(verbose_name= "내용", null=True, blank=True)
    title            = models.TextField(verbose_name= "제목", null=True, blank=True)
    user_nickname    = models.CharField(max_length=100, verbose_name= "사용자 닉네임", null=True, blank=True)
    features         = models.IntegerField(verbose_name= "특징", null=True, blank=True)
    performance      = models.IntegerField(verbose_name= "성능", null=True, blank=True)
    design           = models.IntegerField(verbose_name= "디자인", null=True, blank=True)
    value            = models.IntegerField(verbose_name= "가치", null=True, blank=True)
    photo_urls       = models.CharField(max_length=1000, verbose_name= "사진 URL", null=True, blank=True)
    is_recommended   = models.CharField(max_length=5, verbose_name= "추천 여부", null=True, blank=True)


class uk_product_comment_statistics(models.Model):
    model_code       = models.CharField(unique=True, max_length=100, verbose_name= "모델 코드", null=True, blank=True)
    model_name       = models.CharField(max_length=1000, verbose_name= "모델 명", null=True, blank=True)
    avg_score        = models.DecimalField(verbose_name= "평균 점수", max_digits=5, decimal_places=2, null=True, blank=True)
    review_num       = models.IntegerField(verbose_name= "리뷰 수", null=True, blank=True)
    recommended_cnt  = models.IntegerField(verbose_name= "추천 수", null=True, blank=True)
    not_recommended_cnt = models.IntegerField(verbose_name= "비추천 수", null=True, blank=True)
    review_by_score  = models.JSONField(verbose_name= "점수별 리뷰 수", null=True, blank=True)
    avg_features     = models.DecimalField(verbose_name= "평균 특징", max_digits=5, decimal_places=2, null=True, blank=True)
    avg_performance  = models.DecimalField(verbose_name= "평균 성능", max_digits=5, decimal_places=2, null=True, blank=True)
    avg_value        = models.DecimalField(verbose_name= "평균 가치", max_digits=5, decimal_places=2, null=True, blank=True)
    avg_design       = models.DecimalField(verbose_name= "평균 디자인", max_digits=5, decimal_places=2, null=True, blank=True)
    incentivized_yes = models.IntegerField(verbose_name= "인센티브 수", null=True, blank=True)
    incentivized_no  = models.IntegerField(verbose_name= "비인센티브 수", null=True, blank=True)
    updated_on       = models.DateTimeField(verbose_name='Update', auto_now=True)


class uk_product_cstrt_info(models.Model):
    model_code       = models.CharField(max_length=300, verbose_name= "모델 코드", null=True, blank=True)
    cstrt_model_code = models.CharField(max_length=300, verbose_name= "구성 모델 코드", null=True, blank=True)
    cstrt_qty        = models.IntegerField(verbose_name= "구성 수량", null=True, blank=True)
    dlgt_model_yn    = models.CharField(max_length=1, verbose_name= "대표 모델 여부", null=True, blank=True)
    created_on       = models.DateTimeField(verbose_name='Create', auto_now_add=True)
    updated_on       = models.DateTimeField(verbose_name='Update', auto_now=True)

    class Meta:
        unique_together = ('model_code', 'cstrt_model_code')


class uk_product_rltn(models.Model):
    model_code       = models.CharField(max_length=300, verbose_name= "모델 코드", null=True, blank=True)
    rltn_model_code  = models.CharField(max_length=300, verbose_name= "연관 모델 코드", null=True, blank=True)
    grp_code         = models.CharField(max_length=300, verbose_name= "그룹 코드", null=True, blank=True)    
    created_on       = models.DateTimeField(verbose_name='Create', auto_now_add=True)
    updated_on       = models.DateTimeField(verbose_name='Update', auto_now=True)

    class Meta:
        unique_together = ('model_code', 'rltn_model_code')


class aisc_goods_grp(models.Model):
    aisc_grp_no     = models.IntegerField(verbose_name= "구독 그룹 번호", null=True, blank=True)
    ssb_goods_id    = models.CharField(unique=True, max_length=15, verbose_name= "구독 상품 아이디", null=True, blank=True)
    mst_goods_id    = models.CharField(max_length=15, verbose_name= "마스터 상품 아이디", null=True, blank=True)
    ssb_tp_cd       = models.CharField(max_length=10, verbose_name= "구독 타입 코드 (공통코드 : AISC_SSB_TP)", null=True, blank=True)
    st_id           = models.IntegerField(verbose_name= "사이트 아이디", null=True, blank=True)
    disp_prior_rank = models.IntegerField(verbose_name= "전시 우선 순위", null=True, blank=True)
    dlgt_disp_yn    = models.CharField(max_length=1, verbose_name= "대표 전시 여부", null=True, blank=True)
    sys_reg_dtm     = models.DateTimeField(null=True, blank=True, verbose_name="시스템 등록 일시")
    sys_upd_dtm     = models.DateTimeField(null=True, blank=True, verbose_name="시스템 수정 일시")
    base_ymd        = models.DateField(verbose_name='기준일', null=True, blank=True)
    ld_dt           = models.DateTimeField(verbose_name='적재일시', null=True, blank=True)

    class Meta:        
        indexes = [models.Index(fields=['ssb_goods_id', 'mst_goods_id'], name="r_data_aisc_goods_grp_idx")]
        

class careplus_goods_category(models.Model):
    goods_id         = models.CharField(max_length=15, verbose_name= "상품 아이디 (부모상품)", null=True, blank=True)
    cpls_ctgry_cd    = models.CharField(max_length=10, verbose_name= "케어플러스 카테고리 코드", null=True, blank=True)
    use_prd_tp_cd    = models.CharField(max_length=10, verbose_name= "사용 기간 유형 코드", null=True, blank=True)
    svc_tp_cd        = models.CharField(max_length=10, verbose_name= "서비스 유형 코드 (공통코드: CPLS_SSB_SVC_TP)", null=True, blank=True)
    cntr_prd         = models.CharField(max_length=10, verbose_name= "계약 기간", null=True, blank=True)
    svc_term         = models.CharField(max_length=10, verbose_name= "서비스 주기", null=True, blank=True)
    imd_pay_goods_id = models.CharField(max_length=15, verbose_name= "즉시 결제 상품 아이디", null=True, blank=True)
    svc_prd_tp_cd    = models.CharField(max_length=10, verbose_name= "서비스 기간 유형 코드 (Y3:3년, Y5:5년)", null=True, blank=True)
    use_yn           = models.CharField(max_length=1, verbose_name= "사용 여부", null=True, blank=True)
    sys_reg_dtm      = models.DateTimeField(null=True, blank=True, verbose_name="시스템 등록 일시")
    sys_upd_dtm      = models.DateTimeField(null=True, blank=True, verbose_name="시스템 수정 일시")
    base_ymd         = models.DateField(verbose_name='기준일', null=True, blank=True)
    ld_dt            = models.DateTimeField(verbose_name='적재일시', null=True, blank=True)

    class Meta:
        unique_together = ('goods_id', 'cpls_ctgry_cd', 'use_prd_tp_cd')
        indexes = [models.Index(fields=['goods_id', 'cpls_ctgry_cd'], name="r_data_cpls_goods_idx")]


class careplus_model_category(models.Model):
    mdl_code        = models.CharField(unique=True, max_length=100, verbose_name= "모델 코드", null=True, blank=True)
    cpls_ctgry_cd   = models.CharField(max_length=10, verbose_name= "케어플러스 카테고리 코드", null=True, blank=True)
    use_yn          = models.CharField(max_length=1, verbose_name= "사용 여부", null=True, blank=True)
    sys_reg_dtm     = models.DateTimeField(null=True, blank=True, verbose_name="시스템 등록 일시")
    sys_upd_dtm     = models.DateTimeField(null=True, blank=True, verbose_name="시스템 수정 일시")
    base_ymd        = models.DateField(verbose_name='기준일', null=True, blank=True)
    ld_dt           = models.DateTimeField(verbose_name='적재일시', null=True, blank=True)

    class Meta:
        indexes = [models.Index(fields=['mdl_code', 'cpls_ctgry_cd'], name="r_data_cpls_model_idx")]


class activate_phone_plan(models.Model):
    actv_phone_plan_seq                = models.IntegerField(unique=True, verbose_name= "개통폰 요금제 정책 순번", null=True, blank=True)
    actv_phone_plan_ver                = models.CharField(max_length=100, verbose_name= "개통폰 요금제 정책 버전", null=True, blank=True)
    key_mdl_code                       = models.CharField(max_length=100, verbose_name= "키 모델 코드", null=True, blank=True)
    carrier_cd                         = models.CharField(max_length=3, verbose_name= "통신사 코드 (공통코드: ACTV_PHONE_CARRIER)", null=True, blank=True)
    plan_data_tp_cd                    = models.CharField(max_length=2, verbose_name= "요금제 데이터 유형 코드 (공통코드: ACTV_PHONE_DATA_TP)", null=True, blank=True)
    plan_join_tp_cd                    = models.CharField(max_length=2, verbose_name= "요금제 가입 유형 코드 (공통코드: ACTV_PHONE_JOIN_TP)", null=True, blank=True)
    plan_dc_tp_cd                      = models.CharField(max_length=2, verbose_name= "요금제 할인 유형 코드 (공통코드: ACTV_PHONE_DC_TP)", null=True, blank=True)
    max_istm_prd                       = models.CharField(max_length=2, verbose_name= "최대 할부 기간", null=True, blank=True)
    rcmd_seq                           = models.IntegerField(verbose_name= "추천 순위", null=True, blank=True)
    key_model                          = models.CharField(max_length=100, verbose_name= "키 모델", null=True, blank=True)
    makerx                             = models.CharField(max_length=10, verbose_name= "사업자 코드", null=True, blank=True)
    m_pt_cd                            = models.CharField(max_length=10, verbose_name= "요금제 코드", null=True, blank=True)
    m_pt_nm                            = models.CharField(max_length=100, verbose_name= "요금제 코드 명", null=True, blank=True)
    f_codekey1                         = models.CharField(max_length=10, verbose_name= "요금제 구분 코드", null=True, blank=True)
    f_codenm1                          = models.CharField(max_length=100, verbose_name= "요금제 구분 코드 명", null=True, blank=True)
    contract                           = models.CharField(max_length=2, verbose_name= "약정 개월 수", null=True, blank=True)
    monthly                            = models.CharField(max_length=2, verbose_name= "할부 개월 수", null=True, blank=True)
    pt_amt                             = models.DecimalField(verbose_name= "통신요금 (기본요금)", max_digits=10, decimal_places=0, null=True, blank=True)
    pt_support_discount                = models.DecimalField(verbose_name= "요금 할인 금액", max_digits=10, decimal_places=0, null=True, blank=True)
    pt_support_discount24month         = models.DecimalField(verbose_name= "24개월 요금 할인 금액", max_digits=10, decimal_places=0, null=True, blank=True)
    subside_cd                         = models.CharField(max_length=10, verbose_name= "부가서비스 코드", null=True, blank=True)
    subside_nm                         = models.CharField(max_length=100, verbose_name= "부가서비스 명", null=True, blank=True)
    surtax_amt                         = models.DecimalField(verbose_name= "부가서비스 금액", max_digits=10, decimal_places=0, null=True, blank=True)
    tel_link_url                       = models.TextField(verbose_name= "개통 신청서 URL", null=True, blank=True)
    danga_amt2                         = models.DecimalField(verbose_name= "개통 요청용 금액", max_digits=10, decimal_places=0, null=True, blank=True)
    data_status                        = models.CharField(max_length=1, verbose_name= "데이터 상태", null=True, blank=True)
    so_scode                           = models.CharField(max_length=2, verbose_name= "소분류 코드 (공통코드: ACTV_PHONE_DC_DTL)", null=True, blank=True)
    so_scode_nm                        = models.CharField(max_length=100, verbose_name= "소분류 코드 명", null=True, blank=True)
    maker_support_discount             = models.DecimalField(verbose_name= "공시 지원금", max_digits=10, decimal_places=0, null=True, blank=True)
    extra_support_discount             = models.DecimalField(verbose_name= "추가 지원금", max_digits=10, decimal_places=0, null=True, blank=True)
    change_subsidy_amt                 = models.DecimalField(verbose_name= "전환 지원금", max_digits=10, decimal_places=0, null=True, blank=True)
    factory_price                      = models.DecimalField(verbose_name= "출고가", max_digits=10, decimal_places=0, null=True, blank=True)
    use_m_d_l_mobile_monthly_principal = models.DecimalField(verbose_name= "할부 원금 CPI_Phonenumber", max_digits=10, decimal_places=0, null=True, blank=True)
    use_mobile_distribution_law        = models.CharField(max_length=1, verbose_name= "단통법 적용 여부", null=True, blank=True)
    date_of_publication                = models.DateField(verbose_name= "공시일", null=True, blank=True)
    maker_code                         = models.CharField(max_length=3, verbose_name= "통신사", null=True, blank=True)
    maker_name                         = models.CharField(max_length=10, verbose_name= "통신사 명", null=True, blank=True)
    pet_name                           = models.CharField(max_length=100, verbose_name= "펫 네임", null=True, blank=True)
    site_code                          = models.CharField(max_length=5, verbose_name= "사이트 코드", null=True, blank=True)
    specialcompany                     = models.CharField(max_length=10, verbose_name= "특판 협력 업체", null=True, blank=True)
    tile_text1                         = models.TextField(verbose_name= "타일 노출 정보1 (ex:월할부금)", null=True, blank=True)
    tile_text2                         = models.TextField(verbose_name= "타일 노출 정보2 (ex:월할부금)", null=True, blank=True)
    free_tel                           = models.CharField(max_length=100, verbose_name= "기본 전화", null=True, blank=True)
    free_mms                           = models.CharField(max_length=100, verbose_name= "기본 MMS", null=True, blank=True)
    free_data                          = models.CharField(max_length=100, verbose_name= "기본제공 데이터 + 추가데이터", null=True, blank=True)
    standard_yn                        = models.IntegerField(verbose_name= "추천 요금제 순위", null=True, blank=True)
    charge_cd                          = models.CharField(max_length=3, verbose_name= "요금제 종류", null=True, blank=True)
    base_data                          = models.CharField(max_length=10, verbose_name= "기본 제공 데이터", null=True, blank=True)
    add_data                           = models.CharField(max_length=10, verbose_name= "추가 데이터", null=True, blank=True)    
    sys_reg_dtm                        = models.DateTimeField(null=True, blank=True, verbose_name="시스템 등록 일시")    
    sys_upd_dtm                        = models.DateTimeField(null=True, blank=True, verbose_name="시스템 수정 일시")
    base_ymd                           = models.DateField(verbose_name='기준일', null=True, blank=True)
    ld_dt                              = models.DateTimeField(verbose_name='적재일시', null=True, blank=True)


class product_card(models.Model):
    goods_id         = models.CharField(unique=True, max_length=15, verbose_name= "상품 아이디", null=True, blank=True)
    grouped_products = ArrayField(models.CharField(max_length=300), verbose_name= "그룹 상품", null=True, blank=True)
    goods_nm         = models.CharField(max_length=300, verbose_name= "상품 명", null=True, blank=True)
    disp_lv1         = models.CharField(max_length=100, verbose_name= "1차 전시 카테고리", null=True, blank=True)
    disp_lv2         = models.CharField(max_length=100, verbose_name= "2차 전시 카테고리", null=True, blank=True)
    disp_lv3         = models.CharField(max_length=100, verbose_name= "3차 전시 카테고리", null=True, blank=True)
    discount         = models.DecimalField(verbose_name= "할인 금액", max_digits=5, decimal_places=2, null=True, blank=True)
    release_date     = models.DateField(verbose_name= "출시일", null=True, blank=True)
    hits             = models.IntegerField(verbose_name= "조회 수", null=True, blank=True)
    color            = models.CharField(max_length=100, verbose_name= "색상", null=True, blank=True)
    sale_prc1        = models.DecimalField(verbose_name= "판매가1", max_digits=10, decimal_places=0, null=True, blank=True)
    sale_prc2        = models.DecimalField(verbose_name= "판매가2", max_digits=10, decimal_places=0, null=True, blank=True)
    sale_prc3        = models.DecimalField(verbose_name= "판매가3", max_digits=10, decimal_places=0, null=True, blank=True)
    mdl_code         = models.CharField(max_length=100, verbose_name= "모델 코드", null=True, blank=True)
    model_name       = models.CharField(max_length=100, verbose_name= "모델 명", null=True, blank=True)
    usp_desc         = ArrayField(models.CharField(max_length=1000), verbose_name= "USP 설명", null=True, blank=True)
    estm_score       = models.DecimalField(verbose_name= "예상 점수", max_digits=5, decimal_places=2, null=True, blank=True)
    pd_url           = models.CharField(max_length=1000, verbose_name= "상품 URL", null=True, blank=True)
    img_url          = models.CharField(max_length=1000, verbose_name= "이미지 URL", null=True, blank=True)
    goods_stat_cd    = models.CharField(max_length=2, verbose_name= "상품 상태 코드", null=True, blank=True)
    show_yn          = models.CharField(max_length=1, verbose_name= "전시 여부", null=True, blank=True)
    base_ymd         = models.DateField(verbose_name='기준일', null=True, blank=True)
    ld_dt            = models.DateTimeField(verbose_name='적재일시', null=True, blank=True)
    review_num       = models.IntegerField(verbose_name= "리뷰 수", null=True, blank=True)


class uk_product_card(models.Model):
    model_code       = models.CharField(unique=True, max_length=300, verbose_name= "모델 코드", null=True, blank=True)
    display_name     = models.CharField(max_length=300, verbose_name= "디스플레이 명", null=True, blank=True)
    category_lv1     = models.CharField(max_length=300, verbose_name= "카테고리 레벨1", null=True, blank=True)
    category_lv2     = models.CharField(max_length=300, verbose_name= "카테고리 레벨2", null=True, blank=True)
    category_lv3     = models.CharField(max_length=300, verbose_name= "카테고리 레벨3", null=True, blank=True)
    price            = models.DecimalField(verbose_name= "판매가", max_digits=10, decimal_places=1, null=True, blank=True)
    promotion_price  = models.DecimalField(verbose_name= "프로모션 가격", max_digits=10, decimal_places=1, null=True, blank=True)
    discount         = models.DecimalField(verbose_name= "할인 금액", max_digits=5, decimal_places=2, null=True, blank=True)
    launch_date      = models.DateField(verbose_name= "출시일", null=True, blank=True)
    hits             = models.IntegerField(verbose_name= "조회 수", null=True, blank=True)
    colors           = ArrayField(models.CharField(max_length=100), verbose_name= "색상", null=True, blank=True)
    model_name       = models.CharField(max_length=100, verbose_name= "모델 명", null=True, blank=True)
    usp_text         = ArrayField(models.CharField(max_length=1000), verbose_name= "USP 설명", null=True, blank=True)
    avg_score        = models.DecimalField(verbose_name= "예상 점수", max_digits=5, decimal_places=2, null=True, blank=True)
    pd_url           = models.CharField(max_length=1000, verbose_name= "상품 URL", null=True, blank=True)
    image_url        = models.CharField(max_length=1000, verbose_name= "이미지 URL", null=True, blank=True)
    grouped_products = ArrayField(models.CharField(max_length=300), verbose_name= "그룹 상품", null=True, blank=True)
    salesstatus      = models.CharField(max_length=100, verbose_name= "판매 상태", null=True, blank=True)
    display          = models.CharField(max_length=3, verbose_name= "전시 여부", null=True, blank=True)
    base_ymd         = models.DateField(verbose_name='기준일', null=True, blank=True)
    ld_dt            = models.DateTimeField(verbose_name='적재일시', null=True, blank=True)
    review_num       = models.IntegerField(verbose_name= "리뷰 수", null=True, blank=True)


class uk_product_visual_contents(models.Model):
    model_code        = models.CharField(max_length=300, verbose_name= "모델 코드", null=True, blank=True)
    img_type          = models.CharField(max_length=50, verbose_name= "이미지 타입", null=True, blank=True)
    sorting_no        = models.IntegerField(verbose_name= "정렬 번호", null=True, blank=True)
    type              = models.CharField(max_length=100, verbose_name= "타입", null=True, blank=True)
    is_representative = models.CharField(max_length=10, verbose_name= "대표 여부", null=True, blank=True)
    multi_color_fl    = models.CharField(max_length=10, verbose_name= "다중 색상 여부", null=True, blank=True)
    multi_color       = models.CharField(max_length=100, verbose_name= "다중 색상", null=True, blank=True)
    color             = models.CharField(max_length=100, verbose_name= "색상", null=True, blank=True)
    color_type        = models.CharField(max_length=100, verbose_name= "색상 타입", null=True, blank=True)
    image_set_no      = models.CharField(max_length=100, verbose_name= "이미지 세트 번호", null=True, blank=True)
    size_type         = models.CharField(max_length=100, verbose_name= "사이즈 타입", null=True, blank=True)
    short_desc        = models.TextField(verbose_name= "짧은 설명", null=True, blank=True)
    url               = models.TextField(verbose_name= "URL", null=True, blank=True)
    player_type       = models.CharField(max_length=50, verbose_name= "플레이어 타입", null=True, blank=True)
    media_type        = models.CharField(max_length=50, verbose_name= "미디어 타입", null=True, blank=True)
    video_id          = models.CharField(max_length=50, verbose_name= "비디오 아이디", null=True, blank=True)
    source_image_size = models.CharField(max_length=100, verbose_name= "소스 이미지 사이즈", null=True, blank=True)
    image_orientation = models.CharField(max_length=50, verbose_name= "이미지 방향", null=True, blank=True)
    created_on        = models.DateTimeField(verbose_name='Create', auto_now_add=True)
    updated_on        = models.DateTimeField(verbose_name='Update', auto_now=True)

    class Meta:
        unique_together = ('model_code', 'img_type', 'sorting_no')


class product_images(models.Model):
    goods_id       = models.CharField(max_length=15, verbose_name= "상품 아이디", null=True, blank=True)
    mdl_code       = models.CharField(max_length=300, verbose_name= "모델 코드", null=True, blank=True)
    type           = models.CharField(max_length=10, verbose_name= "타입", null=True, blank=True)
    dlgt_yn        = models.CharField(max_length=1, verbose_name= "대표 여부", null=True, blank=True)
    img_url        = models.CharField(max_length=1000, verbose_name= "이미지 URL", null=True, blank=True)
    img_content    = models.TextField(verbose_name= "이미지 내용", null=True, blank=True)
    site_cd        = models.CharField(max_length=5, verbose_name= "사이트 코드", null=True, blank=True)
    show_seq       = models.IntegerField(verbose_name= "전시 순서", null=True, blank=True)
    pd_url         = models.TextField(verbose_name= "상품 URL", null=True, blank=True)
    created_on     = models.DateTimeField(verbose_name='Create', auto_now_add=True)
    updated_on     = models.DateTimeField(verbose_name='Update', auto_now=True)    

    class Meta:
        unique_together = ('goods_id', 'site_cd', 'img_url')


class ai_smart_mst(models.Model):
    mst_goods_id         = models.CharField(max_length=15, verbose_name= "마스터 상품 아이디", null=True, blank=True)
    ssb_goods_id         = models.CharField(max_length=15, verbose_name= "구독 상품 아이디", null=True, blank=True)
    product_category_lv1 = models.CharField(max_length=100, verbose_name= "상품 카테고리 레벨1", null=True, blank=True)
    product_category_lv2 = models.CharField(max_length=100, verbose_name= "상품 카테고리 레벨2", null=True, blank=True)
    product_category_lv3 = models.CharField(max_length=100, verbose_name= "상품 카테고리 레벨3", null=True, blank=True)
    mdl_code             = models.CharField(max_length=100, verbose_name= "모델 코드", null=True, blank=True)
    goods_nm             = models.CharField(max_length=100, verbose_name= "상품 명", null=True, blank=True)
    goods_stat_cd        = models.CharField(max_length=2, verbose_name= "상품 상태 코드", null=True, blank=True)
    show_yn              = models.CharField(max_length=1, verbose_name= "전시 여부", null=True, blank=True)
    mid5                 = models.CharField(max_length=15, verbose_name= "전시 여부", null=True, blank=True)
    mid5_strt_dtm        = models.DateTimeField(verbose_name='전시 시작 일시', null=True, blank=True)
    mid5_end_dtm         = models.DateTimeField(verbose_name='전시 종료 일시', null=True, blank=True)
    created_on           = models.DateTimeField(verbose_name='Create', auto_now_add=True)
    updated_on           = models.DateTimeField(verbose_name='Update', auto_now=True)

    class Meta:
        unique_together = ('mst_goods_id', 'ssb_goods_id')


class ai_smart_svc(models.Model):
    svc_goods_id         = models.CharField(max_length=15, verbose_name= "서비스 상품 아이디", null=True, blank=True)    
    ssb_goods_id         = models.CharField(max_length=15, verbose_name= "구독 상품 아이디", null=True, blank=True)
    svc_mdl_code         = models.CharField(max_length=100, verbose_name= "서비스 모델 코드", null=True, blank=True)
    cntr_prd             = models.CharField(max_length=10, verbose_name= "계약 기간", null=True, blank=True)
    svc_tp_cd            = models.CharField(max_length=10, verbose_name= "서비스 유형 코드", null=True, blank=True)
    svc_term             = models.CharField(max_length=10, verbose_name= "서비스 주기", null=True, blank=True)
    svc_goods_desc       = models.TextField(verbose_name= "서비스 상품 설명", null=True, blank=True)
    svc_sale_prc         = models.DecimalField(verbose_name= "서비스 판매가", max_digits=10, decimal_places=0, null=True, blank=True)
    created_on           = models.DateTimeField(verbose_name='Create', auto_now_add=True)
    updated_on           = models.DateTimeField(verbose_name='Update', auto_now=True)

    class Meta:
        unique_together = ('svc_goods_id', 'ssb_goods_id')


class ai_aio_mst(models.Model):
    mst_goods_id         = models.CharField(max_length=15, verbose_name= "마스터 상품 아이디", null=True, blank=True)
    ssb_goods_id         = models.CharField(max_length=15, verbose_name= "구독 상품 아이디", null=True, blank=True)
    product_category_lv1 = models.CharField(max_length=100, verbose_name= "상품 카테고리 레벨1", null=True, blank=True)
    product_category_lv2 = models.CharField(max_length=100, verbose_name= "상품 카테고리 레벨2", null=True, blank=True)
    product_category_lv3 = models.CharField(max_length=100, verbose_name= "상품 카테고리 레벨3", null=True, blank=True)
    mdl_code             = models.CharField(max_length=100, verbose_name= "모델 코드", null=True, blank=True)
    goods_nm             = models.CharField(max_length=100, verbose_name= "상품 명", null=True, blank=True)
    goods_stat_cd        = models.CharField(max_length=2, verbose_name= "상품 상태 코드", null=True, blank=True)
    show_yn              = models.CharField(max_length=1, verbose_name= "전시 여부", null=True, blank=True)
    created_on           = models.DateTimeField(verbose_name='Create', auto_now_add=True)
    updated_on           = models.DateTimeField(verbose_name='Update', auto_now=True)

    class Meta:
        unique_together = ('mst_goods_id', 'ssb_goods_id')


class web_clean_cache(models.Model):    
    url           = models.TextField(verbose_name='URL', null=True, blank=True)
    content       = models.TextField(verbose_name='Content', null=True, blank=True)
    created_on    = models.DateTimeField(verbose_name='Create', auto_now_add=True)
    country_code  = models.CharField(verbose_name='Country Code', null=True, blank=True)
    query         = models.CharField(verbose_name='Query', null=True, blank=True)
    title         = models.CharField(verbose_name='Title', null=True, blank=True)
    clean_content = models.TextField(verbose_name='Clean Content', null=True, blank=True)    
    content_embed = VectorField(dimensions=1024, help_text="BAAI/bge-m3", null=True, blank=True)
    summary       = models.TextField(verbose_name='Summary', null=True, blank=True)
    source        = models.CharField(verbose_name='Source', max_length=10, null=True, blank=True)    


class prd_mst_hist(models.Model):    
    disp_lv1                = models.CharField(verbose_name='Display Lv1', max_length=1000, null=True, blank=True)
    disp_lv2                = models.CharField(verbose_name='Display Lv2', max_length=1000, null=True, blank=True)
    disp_lv3                = models.CharField(verbose_name='Display Lv3', max_length=1000, null=True, blank=True)
    business_unit           = models.CharField(verbose_name='Business Unit', max_length=1000, null=True, blank=True)    
    product_category_lv1    = models.CharField(verbose_name='Product Category Lv1', max_length=1000, null=True, blank=True)
    product_category_lv2    = models.CharField(verbose_name='Product Category Lv2', max_length=1000, null=True, blank=True)
    product_category_lv3    = models.CharField(verbose_name='Product Category Lv3', max_length=1000, null=True, blank=True)    
    mdl_code                = models.CharField(verbose_name='Mdl Code', max_length=1000, null=True, blank=True)
    model_name              = models.CharField(verbose_name='Model Name', max_length=1000, null=True, blank=True)
    goods_id                = models.CharField(unique=True, verbose_name='Goods Id', max_length=1000, null=True, blank=True)
    goods_nm                = models.CharField(verbose_name='Goods Nm', max_length=1000, null=True, blank=True)    
    release_date            = models.DateField(verbose_name='release_date', null=True, blank=True)
    created_on             = models.DateTimeField(verbose_name='Create', auto_now_add=True)
    updated_on             = models.DateTimeField(verbose_name='Update', auto_now=True)


class cpt_manual(models.Model):
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

    class Meta:
        indexes = [
        	models.Index(fields=['product_category_lv1', 'product_category_lv2', 'product_category_lv3', 'goods_id', 'mdl_code', 'filter_nm', 'filter_item_nm'], name="r_data_cpt_manual_idx"),]

    
class st_goods_sale_summary(models.Model):
    st_id            = models.IntegerField(verbose_name= "사이트 아이디", null=True, blank=True)
    goods_id         = models.CharField(max_length=15, verbose_name= "상품 아이디", null=True, blank=True)
    tot_sale_qty     = models.IntegerField(verbose_name= "총 판매 수량", null=True, blank=True)
    tot_sale_amt     = models.DecimalField(verbose_name= "총 판매 금액", max_digits=10, decimal_places=0, null=True, blank=True)
    sale_rank        = models.IntegerField(verbose_name= "판매 순위", null=True, blank=True)
    sys_regr_no      = models.CharField(max_length=20, verbose_name="시스템 등록자 번호", null=True, blank=True)
    sys_reg_dtm      = models.DateTimeField(verbose_name='시스템 등록 일시', auto_now_add=True)

    class Meta:
        unique_together = ('st_id', 'goods_id')


class uk_product_smc_info(models.Model):
    model_code                             = models.CharField(max_length=300, verbose_name= "모델 코드", null=False, blank=False)
    title                                  = models.TextField(verbose_name= "제목", null=True, blank=True)
    summary                                = models.TextField(verbose_name= "요약", null=True, blank=True)
    smc_img_url                            = models.TextField(verbose_name= "SMC 이미지 URL", null=True, blank=True)
    smc_code                               = models.CharField(max_length=100, verbose_name= "SMC 코드", null=False, blank=False)
    price                                  = models.FloatField(verbose_name= "가격", null=True, blank=True)
    promotion_price                        = models.FloatField(verbose_name= "프로모션 가격", null=True, blank=True)
    period                                 = models.CharField(max_length=100, verbose_name= "기간", null=True, blank=True)
    payment_cycle                          = models.CharField(max_length=100, verbose_name= "지불 주기", null=True, blank=True)
    duration                               = models.IntegerField(verbose_name= "기간(개월)", null=True, blank=True)
    term_and_cond                          = models.TextField(verbose_name= "약관 및 조건", null=True, blank=True)
    product_short_description              = models.TextField(verbose_name= "상품 짧은 설명", null=True, blank=True)
    preselected                            = models.BooleanField(verbose_name= "사전 선택 여부", default=False)
    breakdown_price                        = models.FloatField(verbose_name= "세부 가격", null=True, blank=True)
    download_tnc_url                       = models.TextField(verbose_name= "다운로드 약관 URL", null=True, blank=True)
    was_price                              = models.FloatField(verbose_name= "이전 가격", null=True, blank=True)
    theft                                  = models.BooleanField(verbose_name= "도난 여부", default=False)
    yearly_subscription                    = models.CharField(max_length=100, verbose_name= "연간 구독", null=True, blank=True)
    replenishment_subscription_frequencies = models.CharField(max_length=100, verbose_name= "보충 구독 빈도", null=True, blank=True)
    combined_with_service_type             = models.TextField(verbose_name= "서비스 유형과 결합", null=True, blank=True)
    min_price                              = models.FloatField(verbose_name= "최소 가격", null=True, blank=True)
    max_price                              = models.FloatField(verbose_name= "최대 가격", null=True, blank=True)
    created_on                             = models.DateTimeField(verbose_name='Create', auto_now_add=True)
    updated_on                             = models.DateTimeField(verbose_name='Update', auto_now=True)
    country_code                           = models.CharField(max_length=10, verbose_name="국가 코드", null=False, blank=False)
    site_cd                                = models.CharField(max_length=5, verbose_name="닷컴 코드", null=False, blank=False)

    class Meta:        
        unique_together = ('model_code', 'smc_code', 'country_code', 'site_cd')

    
class uk_product_order(models.Model): 
    country_code         = models.CharField(max_length=10, verbose_name="국가 코드", null=False, blank=False)
    type_name            = models.CharField(verbose_name='type_name', max_length=26, null=True, blank=True)    
    family_name          = models.CharField(verbose_name='family_name', max_length=125, null=True, blank=True)
    marketing_name       = models.CharField(verbose_name='marketing_name', max_length=125, null=True, blank=True)
    representative_model = models.CharField(verbose_name='representative_model', max_length=20, null=True, blank=True)
    sort_type            = models.CharField(verbose_name='sort_type', max_length=20, null=False, blank=False)
    sorting_no           = models.IntegerField(verbose_name='sorting_no', null=True, blank=True)    
    category_lv1         = models.CharField(verbose_name='Category Lv1', null=True, blank=True)    
    category_lv2         = models.CharField(verbose_name='Category Lv2', null=True, blank=True)    
    category_lv3         = models.CharField(verbose_name='Category Lv3', null=True, blank=True)
    launch_date          = models.DateField(verbose_name='Launch Date', null=True, blank=True)
    site_cd              = models.CharField(max_length=5, verbose_name="닷컴 코드", null=False, blank=False)
    created_on           = models.DateTimeField(verbose_name='Create', auto_now_add=True)

    class Meta:
        unique_together = ('type_name', 'representative_model', 'sort_type', 'country_code', 'site_cd')
