import sys, os, json, time
import numpy as np
import pandas as pd
from concurrent.futures import ThreadPoolExecutor
from sklearn.metrics.pairwise import cosine_similarity

import django
from django.db import connection

sys.path.append("/www/alpha/")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "alpha.settings")

from apps.rubicon_v3.__function import __embedding_rerank as embedding_rerank
from apps.rubicon_v3.__function.definitions import channels
from alpha import __log as logFunction

import html, re
class ReviewManager:

    def __init__(self, country, query, extended_info_result, site_cd='B2C'):
        self.country = country
        self.query = query
        self.extended_info_result = extended_info_result
        self.revised_extended_info_result = self.doSplitModels() ## split by model series
        self.query_embedding = embedding_rerank.baai_embedding(query, "")
        self.site_cd = site_cd
        self.rep_model_list, self.rep_mapping_code_list = self.getMaxThreeModels()
        self.all_model_list = self.getExtendedModelList()
        self.mapping_code_list = self.getMappingCodeList()
        self.minimum_review_num = 5
        self.total_review_num = 15
        self.target_table_KR = "rubicon_data_goods_comment"
        self.target_table_KR_sum = "rubicon_data_goods_comment_grouped_summary"
        self.target_table_KR_stat = "rubicon_data_goods_comment_grouped_stat"
        #self.target_table_GB = "rubicon_data_uk_product_comment"
        self.target_table_GB_sum = "rubicon_data_uk_product_comment_summary"
        self.target_table_GB_stat = "rubicon_data_uk_product_comment_statistics"
        self.bc_model_list = self.getBCModelCodes()

    def clean_text_static(self, text):
        try:
            """ HTML 태그 및 공백 정리 """
            text = html.unescape(text)
            text = re.sub(r'<[^>]+>', ' ', text)
            text = re.sub(r'\s+', ' ', text).strip()
        except Exception as e:
            text = ''
        return text

    def getExtendedModelList(self):
        total_result = []
        for series in self.revised_extended_info_result:
            result = []
            for ext_info in series:
                if len(ext_info.get('extended_info', [])) > 0:
                    result.extend(ext_info.get('extended_info'))
            total_result.append(result)
        return total_result
    
    def getMappingCodeList(self):
        total_result = []
        for series in self.revised_extended_info_result:
            result = []
            for ext_info in series:
                if len(ext_info.get('mapping_code', "")) > 0:
                    result.append(ext_info.get('mapping_code'))
            total_result.append(result)
        return total_result
    
    def doSplitModels(self):
        groups = []
        current_group = []
        for ext_info in self.extended_info_result:
            if ext_info["id"] == 0 and current_group:  # 새 그룹 시작
                groups.append(current_group)
                current_group = []
            current_group.append(ext_info)
        # 마지막 그룹 추가
        if current_group:
            groups.append(current_group)
        
        return groups
    
    def getAdditionalInfo(self, modelList):
        try:
            with connection.cursor() as cursor:
                if self.country == 'KR':
                    query = f"""
                        SELECT gd.usp_desc 
                        FROM rubicon_data_goods_add_info gd
                        INNER JOIN rubicon_data_goods_base gb
                        ON gd.goods_id = gb.goods_id
                        WHERE gb.mdl_code IN {modelList} AND gb.site_cd = '{self.site_cd}'
                        """
                    cursor.execute(query)
                    result = cursor.fetchall()
                    print
                    return pd.DataFrame(result, columns=['CONTENT']).drop_duplicates()
                elif self.country == 'GB':
                    query = f"""
                        SELECT usp_text 
                        FROM rubicon_data_uk_product_spec_basics
                        WHERE model_code IN {modelList}
                        """
                    cursor.execute(query)
                    result = cursor.fetchall()
                    return pd.DataFrame(result, columns=['CONTENT']).drop_duplicates()
                else:
                    return pd.Dataframe()
        except Exception as e:
            return pd.DataFrame()
        
    def makeTuple(self, modelList):
        if len(modelList) == 1:
            return f"('{modelList[0]}')"
        else:
            return tuple(modelList)
    
    def get_review_sum_stat(self):
        if self.country == 'KR':
            sum_df = pd.DataFrame()
            stat_df = pd.DataFrame()
            category_df = pd.DataFrame()
            for i in range(len(self.rep_model_list)):
                model_tmp_stat_df = pd.DataFrame()
                for j in range(len(self.rep_model_list[i])):
                    tmp_stat_df = self.getStatistics_KR_new(self.rep_model_list[i][j])
                    tmp_stat_df['MAPPING_CODE'] = str(self.rep_mapping_code_list[i][j])
                    model_tmp_stat_df = pd.concat([model_tmp_stat_df, tmp_stat_df], ignore_index=True)
                if self.site_cd == 'B2C':
                    pd_modelList = [model for model in self.all_model_list[i] if model not in self.bc_model_list]
                    bc_modelList = [model for model in self.all_model_list[i] if model in self.bc_model_list]
                    pd_tmp_sum_df = self.getReviews_KR(self.makeTuple(pd_modelList), 1, 'pd')
                    bc_tmp_sum_df = self.getReviews_KR(self.makeTuple(bc_modelList), 1, 'bc')
                    tmp_sum_df = pd.concat([pd_tmp_sum_df, bc_tmp_sum_df], ignore_index=True)
                elif self.site_cd == 'FN':
                    tmp_sum_df = self.getReviews_KR(self.makeTuple(self.all_model_list[i]), 2, 'pd')

                if not tmp_sum_df.empty:
                    review_list = self.makeTuple(tmp_sum_df['GOODS_ESTM_NO'].unique())
                    tmp_category_df = self.getReviewCategory_KR(review_list)
                    tmp_category_df['MAPPING_CODE'] = str(self.mapping_code_list[i])
                    category_df = pd.concat([category_df, tmp_category_df], ignore_index=True)
                    if len(tmp_sum_df) >= self.total_review_num:
                        tmp_sum_df = tmp_sum_df.sort_values(by='SYS_REG_DTM', ascending=False)[:self.total_review_num]

                if len(tmp_sum_df) >= self.minimum_review_num:
                    #tmp_sum_df = tmp_sum_df.sort_values(by='SYS_REG_DTM', ascending=False)[:self.total_review_num]
                    tmp_sum_df['MAPPING_CODE'] = str(self.mapping_code_list[i])
                    sum_df = pd.concat([sum_df, tmp_sum_df], ignore_index=True)
                    stat_df = pd.concat([stat_df, model_tmp_stat_df], ignore_index=True)
                else:
                    tmp_sum_df2 = self.getAdditionalInfo(self.makeTuple(self.all_model_list[i]))
                    tmp_sum_df2['MAPPING_CODE'] = str(self.mapping_code_list[i])
                    sum_df = pd.concat([sum_df, tmp_sum_df2], ignore_index=True)
            stat_df = stat_df.drop_duplicates(subset=["MAPPING_CODE"], keep="first")
            start = time.time()
            sum_df['CONTENT'] = sum_df['CONTENT'].apply(self.clean_text_static)
            return sum_df[['CONTENT', 'MAPPING_CODE']], stat_df, category_df
            
        elif self.country == 'GB':
            sum_df = pd.DataFrame()
            stat_df = pd.DataFrame()
            for i in range(len(self.all_model_list)):
                model_tmp_stat_df = pd.DataFrame()
                for j in range(len(self.rep_model_list[i])):
                    tmp_stat_df = self.getStatistics_GB_new(self.rep_model_list[i][j])
                    tmp_stat_df['MAPPING_CODE'] = str(self.rep_mapping_code_list[i][j])
                    model_tmp_stat_df = pd.concat([model_tmp_stat_df, tmp_stat_df], ignore_index=True)

                tmp_sum_df = self.getReviews_GB(self.makeTuple(self.all_model_list[i]))
                if len(tmp_sum_df) >= self.minimum_review_num:
                    tmp_sum_df['MAPPING_CODE'] = str(self.mapping_code_list[i])
                    sum_df = pd.concat([sum_df, tmp_sum_df], ignore_index=True)
                    stat_df = pd.concat([stat_df, model_tmp_stat_df], ignore_index=True)
                else:
                    tmp_sum_df2 = self.getAdditionalInfo(self.makeTuple(self.all_model_list[i]))
                    tmp_sum_df2['MAPPING_CODE'] = str(self.mapping_code_list[i])
                    sum_df = pd.concat([sum_df, tmp_sum_df2], ignore_index=True)
            stat_df = stat_df.drop_duplicates(subset=["MAPPING_CODE"], keep="first")
            return sum_df[['CONTENT', 'MAPPING_CODE']], stat_df, pd.DataFrame()
        else:
            return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()
    
    def getMaxThreeModels(self):
        model_result = []
        mapping_result = []
        if len(self.revised_extended_info_result) == 1:
            series = self.revised_extended_info_result[0]
            models = []
            mapping_codes = []
            if len(series) == 1:
                if len(series[0].get('extended_info', [])) > 0:
                    if len(series[0].get('extended_info', [])) <= 3:
                        models.extend(series[0].get('extended_info')[:len(series[0].get('extended_info'))])
                        for _ in range(len(series[0].get('extended_info', []))):
                            mapping_codes.append(series[0].get('mapping_code', ''))
                    else:
                        models.extend(series[0].get('extended_info')[:3])
                        for _ in range(3):
                            mapping_codes.append(series[0].get('mapping_code', ''))
            elif len(series) >= 2:
                for ext_info in series:
                    if len(ext_info.get('extended_info', [])) > 0:
                        models.append(ext_info.get('extended_info')[0])
                        mapping_codes.append(ext_info.get('mapping_code', ''))
            model_result.append(models)
            mapping_result.append(mapping_codes)
        elif len(self.revised_extended_info_result) > 1:
            for series in self.revised_extended_info_result:
                models = []
                mapping_codes = []
                for ext_info in series:
                    if len(ext_info.get('extended_info', [])) > 0:
                        models.append(ext_info.get('extended_info')[0])
                        mapping_codes.append(ext_info.get('mapping_code', ''))
                model_result.append(models)
                mapping_result.append(mapping_codes)
                
        return model_result, mapping_result
            
    def getStatistics_KR(self, modelCode, siteCode):
        start = time.time()
        try:
            with connection.cursor() as cursor:
                query = f"""
                WITH base_goods AS (
                    SELECT goods_id
                    FROM rubicon_data_goods_base
                    WHERE mdl_code = '{modelCode}'
                        AND site_cd = '{self.site_cd}'
                ),
                family_goods AS (
                    SELECT A4.goods_id
                    FROM rubicon_data_goods_base A1
                    JOIN rubicon_data_goods_grp_key_map A2 ON A1.goods_id = A2.goods_id
                    JOIN rubicon_data_goods_grp_key_info A3 ON A2.grp_key_no = A3.grp_key_no
                    JOIN rubicon_data_goods_grp_key_map A4 ON A4.grp_key_no = A3.grp_key_no
                    WHERE A1.goods_id IN (SELECT goods_id FROM base_goods)
                        AND A3.grp_key_tp_cd = '20'
                ),
                spring_pkg_goods AS (
                    SELECT GCI.cstrt_goods_id as goods_id
                    FROM rubicon_data_goods_cstrt_info GCI
                    JOIN family_goods FG ON GCI.goods_id = FG.goods_id
                    WHERE GCI.goods_cstrt_gb_cd = '10'
                        AND GCI.dlgt_goods_yn = 'Y'
                        AND GCI.use_yn = 'Y'
                ),
                subscription_goods AS (
                    SELECT AGG_1.ssb_goods_id as goods_id
                    FROM rubicon_data_aisc_goods_grp AGG_1
                    JOIN rubicon_data_aisc_goods_grp AGG_2 ON AGG_2.aisc_grp_no = AGG_1.aisc_grp_no
                    JOIN family_goods FG ON FG.goods_id = AGG_2.mst_goods_id
                ),
                target_goods AS (
                    SELECT goods_id FROM family_goods
                    UNION
                    SELECT goods_id FROM spring_pkg_goods
                    UNION
                    SELECT goods_id FROM subscription_goods
                ),
                expanded_goods AS (
                    SELECT DISTINCT CORE_GB.goods_id
                    FROM rubicon_data_goods_base CORE_GB
                    JOIN rubicon_data_goods_base CORE_GB2
                        ON CORE_GB.mdl_code = CORE_GB2.mdl_code
                        AND CORE_GB.site_cd = '{self.site_cd}'
                        AND CORE_GB2.site_cd = '{self.site_cd}'
                    WHERE CORE_GB2.goods_id IN (SELECT goods_id FROM target_goods)
                )
                SELECT
                    COALESCE(ROUND(AVG(A.estm_score)::numeric, 2), 0.0) AS avg_review_score,
                    COUNT(A.estm_score) AS review_count,
                    '{modelCode}' AS model_code
                FROM public.{self.target_table_KR} A
                JOIN expanded_goods TG ON A.goods_id = TG.goods_id
                WHERE A.sys_del_yn = 'N'
                    AND A.st_id = {siteCode}
                ;
                """
                cursor.execute(query)
                review_result = cursor.fetchall()
                result_df = pd.DataFrame(review_result, columns=['AVG_REVIEW_SCORE', 'REVIEW_COUNT', 'MODEL_CODE'])
            return result_df
        except Exception as e:
            return pd.DataFrame()

    def getStatistics_KR_new(self, modelCode):
        start = time.time()
        try:
            with connection.cursor() as cursor:
                query = f"""
                SELECT avg_review_score, review_count, model_code
                FROM public.{self.target_table_KR_stat}
                WHERE model_code = '{modelCode}'
                AND site_cd = '{self.site_cd}'
                ;
                """
                cursor.execute(query)
                review_result = cursor.fetchall()
                result_df = pd.DataFrame(review_result, columns=['AVG_REVIEW_SCORE', 'REVIEW_COUNT', 'MODEL_CODE'])
            return result_df
        except Exception as e:
            return pd.DataFrame()
    
    def getReviews_KR(self, modelList, siteCode, product_type):
        start = time.time()
        try:
            with connection.cursor() as cursor:
                pd_query = f"""
                SELECT 
                A.goods_id,
                A.goods_estm_no,
                A.content,
                A.sys_reg_dtm
                FROM {self.target_table_KR_sum} A
                INNER JOIN (SELECT DISTINCT CORE_GB.GOODS_ID
                            FROM rubicon_data_goods_base CORE_GB
                            INNER JOIN rubicon_data_goods_base CORE_GB2 ON CORE_GB.MDL_CODE = CORE_GB2.MDL_CODE and CORE_GB2.site_cd = '{self.site_cd}' and CORE_GB.site_cd = '{self.site_cd}'
                            INNER JOIN (SELECT A4.GOODS_ID /* 패밀리 그룹 */
                                        FROM rubicon_data_goods_base A1
                                            , rubicon_data_goods_grp_key_map A2
                                            , rubicon_data_goods_grp_key_info A3
                                            , rubicon_data_goods_grp_key_map A4
                                        WHERE 1 = 1
                                        AND A1.GOODS_ID in (SELECT goods_id FROM rubicon_data_product_category WHERE mdl_code in {modelList} AND site_cd = '{self.site_cd}')
                                        AND A1.GOODS_ID = A2.GOODS_ID
                                        AND A2.GRP_KEY_NO = A3.GRP_KEY_NO
                                        AND A3.GRP_KEY_TP_CD = '20'
                                        AND A4.GRP_KEY_NO = A3.GRP_KEY_NO
                                        UNION
                                        SELECT GCI.CSTRT_GOODS_ID /* 봄 패키지 일 경우 구성품(대표 상품) */
                                        FROM rubicon_data_goods_cstrt_info GCI
                                        INNER JOIN (SELECT A4.GOODS_ID
                                                    FROM rubicon_data_goods_base A1
                                                        , rubicon_data_goods_grp_key_map A2
                                                        , rubicon_data_goods_grp_key_info A3
                                                        , rubicon_data_goods_grp_key_map A4
                                                    WHERE 1 = 1
                                                    AND A1.GOODS_ID in (SELECT goods_id FROM rubicon_data_product_category WHERE mdl_code in {modelList} AND site_cd = '{self.site_cd}')
                                                    AND A1.GOODS_ID = A2.GOODS_ID
                                                    AND A2.GRP_KEY_NO = A3.GRP_KEY_NO
                                                    AND A3.GRP_KEY_TP_CD = '20'
                                                    AND A4.GRP_KEY_NO = A3.GRP_KEY_NO
                                        ) T
                                        --WHERE 1 = 1
                                        on GCI.GOODS_ID = T.GOODS_ID
                                        --AND GCI.GOODS_ID = T.GOODS_ID
                                        AND GCI.GOODS_CSTRT_GB_CD = '10'
                                        AND GCI.DLGT_GOODS_YN = 'Y'
                                        AND GCI.USE_YN = 'Y'
                                        UNION
                                        SELECT GCI2.GOODS_ID /* (구성품이 대표 상품인 경우)구성폼 패밀리의 봄 패키지 */
                                        FROM rubicon_data_goods_cstrt_info GCI2
                                        INNER JOIN rubicon_data_goods_base GB1 ON GB1.GOODS_ID = GCI2.CSTRT_GOODS_ID
                                        INNER JOIN rubicon_data_goods_base GB2 ON GB2.MDL_CODE = GB1.MDL_CODE
                                        INNER JOIN (SELECT A4.GOODS_ID
                                                    FROM rubicon_data_goods_base A1
                                                        , rubicon_data_goods_grp_key_map A2
                                                        , rubicon_data_goods_grp_key_info A3
                                                        , rubicon_data_goods_grp_key_map A4
                                                    WHERE 1 = 1
                                                    AND A1.GOODS_ID in (SELECT goods_id FROM rubicon_data_product_category WHERE mdl_code in {modelList} AND site_cd = '{self.site_cd}')
                                                    AND A1.GOODS_ID = A2.GOODS_ID
                                                    AND A2.GRP_KEY_NO = A3.GRP_KEY_NO
                                                    AND A3.GRP_KEY_TP_CD = '20'
                                                    AND A4.GRP_KEY_NO = A3.GRP_KEY_NO
                                        ) T ON T.GOODS_ID = GB2.GOODS_ID
                                        WHERE 1 = 1
                                        AND GCI2.GOODS_CSTRT_GB_CD = '10'
                                        AND GCI2.DLGT_GOODS_YN = 'Y'
                                        AND GCI2.USE_YN = 'Y'
                                        AND GB2.SITE_CD = '{self.site_cd}'
                                        UNION             -- 구독 그룹
                                        SELECT
                                        AGG_1.SSB_GOODS_ID
                                        FROM rubicon_data_aisc_goods_grp AGG_1
                                        INNER JOIN rubicon_data_aisc_goods_grp AGG_2
                                        ON AGG_2.AISC_GRP_NO = AGG_1.AISC_GRP_NO
                                        INNER JOIN (SELECT A4.GOODS_ID
                                                    FROM rubicon_data_goods_base A1
                                                        , rubicon_data_goods_grp_key_map A2
                                                        , rubicon_data_goods_grp_key_info A3
                                                        , rubicon_data_goods_grp_key_map A4
                                                    WHERE 1 = 1
                                                    AND A1.GOODS_ID in (SELECT goods_id FROM rubicon_data_product_category WHERE mdl_code in {modelList} AND site_cd = '{self.site_cd}')
                                                    AND A1.GOODS_ID = A2.GOODS_ID
                                                    AND A2.GRP_KEY_NO = A3.GRP_KEY_NO
                                                    AND A3.GRP_KEY_TP_CD = '20'
                                                    AND A4.GRP_KEY_NO = A3.GRP_KEY_NO
                                        ) T ON T.GOODS_ID = AGG_2.MST_GOODS_ID
                            ) C ON C.GOODS_ID = CORE_GB2.GOODS_ID
                ) TG
                ON A.GOODS_ID = TG.GOODS_ID
                WHERE A.SYS_DEL_YN = 'N'
                AND A.ST_ID = {siteCode}
                ORDER BY A.sys_reg_dtm DESC;
                """

                bc_query = f"""
                SELECT /* QUERYID(goodsComment.CommentCntAvg)*/ /* BC 상품 상품평 건수, 점수 */
                    A.goods_id,
                    A.goods_estm_no,
                    A.content,
                    A.sys_reg_dtm
                FROM {self.target_table_KR_sum} A
                    INNER JOIN (SELECT DISTINCT CORE_GB.GOODS_ID
                                FROM rubicon_data_goods_base CORE_GB
                                INNER JOIN rubicon_data_goods_base CORE_GB2 ON CORE_GB.MDL_CODE = CORE_GB2.MDL_CODE and CORE_GB.SITE_CD = 'B2C' and CORE_GB2.SITE_CD = 'B2C'
                                INNER JOIN (SELECT GOODS_ID /* BC 패밀리 상품 아이디*/
                                            FROM rubicon_data_bc_goods_map BGM
                                            INNER JOIN rubicon_data_bc_base BB
                                            ON BB.BC_ID = BGM.BC_ID and now() between BB.disp_strt_dtm and BB.disp_end_dtm
                                            WHERE 1 = 1
                                            and BGM.SITE_CD = 'B2C'
                                            and BB.SITE_CD = 'B2C'
                                            and BB.DISP_YN = 'Y'
                                            AND BB.BC_ID in (select distinct BB1.BC_ID 
                                                                from rubicon_data_bc_base BB1 
                                                                inner join rubicon_data_bc_goods_map GBM1 
                                                                on BB1.SITE_CD = 'B2C' 
                                                                    and GBM1.SITE_CD = 'B2C' 
                                                                    and BB1.DISP_YN = 'Y' 
                                                                    and BB1.BC_ID = GBM1.BC_ID 
                                                                    and now() between BB1.disp_strt_dtm and BB1.disp_end_dtm
                                                                where GBM1.GOODS_ID in (select goods_id from rubicon_data_product_category where mdl_code in {modelList} and site_cd = 'B2C'))
                                            UNION
                                            SELECT CSTRT_GOODS_ID AS GOODS_ID /* 봄 패키지 일 경우 BC 구성품(대표 상품) 아이디*/
                                            FROM rubicon_data_goods_cstrt_info GCI
                                            INNER JOIN rubicon_data_bc_goods_map BGM
                                            ON BGM.GOODS_ID = GCI.GOODS_ID and GCI.GOODS_ID in (select goods_id from rubicon_data_product_category where mdl_code in {modelList} and site_cd = 'B2C')
                                            INNER JOIN rubicon_data_bc_base BB
                                            ON BB.BC_ID = BGM.BC_ID AND BB.DISP_YN = 'Y' and now() between BB.disp_strt_dtm and BB.disp_end_dtm
                                            WHERE 1 = 1
                                            AND GCI.GOODS_CSTRT_GB_CD = '10'
                                            AND GCI.DLGT_GOODS_YN = 'Y'
                                            AND GCI.USE_YN = 'Y'
                                            and GCI.SITE_CD = 'B2C'
                                            and BGM.SITE_CD = 'B2C'
                                            AND BB.BC_ID in (select distinct BB1.BC_ID 
                                                                from rubicon_data_bc_base BB1 
                                                                inner join rubicon_data_bc_goods_map GBM1 
                                                                on BB1.SITE_CD = 'B2C' 
                                                                    and GBM1.SITE_CD = 'B2C' 
                                                                    and BB1.DISP_YN = 'Y' 
                                                                    and BB1.BC_ID = GBM1.BC_ID 
                                                                    and now() between BB1.disp_strt_dtm and BB1.disp_end_dtm
                                                                where GBM1.GOODS_ID in (select goods_id from rubicon_data_product_category where mdl_code in {modelList} and site_cd = 'B2C'))
                                ) A ON A.GOODS_ID = CORE_GB2.GOODS_ID
                    ) TG
                ON A.GOODS_ID = TG.GOODS_ID and A.SITE_CD = 'B2C'
                WHERE A.SYS_DEL_YN = 'N'
                AND A.ST_ID = 1
                ORDER BY A.sys_reg_dtm DESC;
                """
                main_query = ""
                if siteCode == 1:
                    if product_type == 'pd':
                        main_query = pd_query
                        #cursor.execute(pd_query)
                    elif product_type == 'bc':
                        main_query = bc_query
                        #cursor.execute(bc_query)
                elif siteCode == 2:             
                    #cursor.execute(pd_query)
                    main_query = pd_query
                if not main_query:
                    return pd.DataFrame()
                cursor.execute(main_query)
                review_result = cursor.fetchall()
                result_df = pd.DataFrame(
                    review_result,
                    columns=['GOODS_ID', 'GOODS_ESTM_NO', 'CONTENT', 'SYS_REG_DTM']
                )
            return result_df
        except Exception as e:
            return pd.DataFrame()
        
    def getReviewCategory_KR(self, review_list):
        try:
            with connection.cursor() as cursor:
                query = f"""SELECT
                        jsonb_object_agg(goods_cmnt_kwd_cd, comment_count ORDER BY goods_cmnt_kwd_cd DESC) AS review_by_category
                    FROM (
                        SELECT
                            goods_id,
                            goods_cmnt_kwd_cd,
                            COUNT(*) AS comment_count
                        FROM (
                            SELECT gc.goods_id, gc.goods_estm_no, gk.goods_cmnt_kwd_cd
                            FROM {self.target_table_KR} gc
                            INNER JOIN rubicon_data_goods_comment_keyword gk
                            ON gc.goods_estm_no = gk.goods_estm_no WHERE gc.goods_estm_no in {review_list}
                        ) subquery
                        GROUP BY goods_id, goods_cmnt_kwd_cd
                    ) subquery"""
                cursor.execute(query)
                review_result = cursor.fetchall()
                category_dicts = []
                for row in review_result:
                    val = row[0]
                    if isinstance(val, str):
                        # 문자열이면 JSON 파싱
                        val = json.loads(val)
                    category_dicts.append(val)
                result_series = pd.Series(category_dicts).apply(lambda x: self.convert_category_to_text_KR(x))
                result_df = pd.DataFrame({'REVIEW_BY_CATEGORY': result_series})
            return result_df
        except Exception as e:
            return pd.DataFrame()
    
    def convert_category_to_text_KR(self, category_dict):
        with connection.cursor() as cursor:
            query = f"""
                    SELECT dtl_cd, dtl_nm FROM rubicon_data_code_detail WHERE grp_cd = 'GOODS_CMNT_KWD'
                    """
            cursor.execute(query)
            review_result = cursor.fetchall()
            code_dict = dict(review_result)
        mapped_review = {code_dict[k]: v for k, v in category_dict.items() if k in code_dict and k != 'G04'}
        return mapped_review
    
    def getRepModel_GB(self, modelCode):
        try:
            with connection.cursor() as cursor:
                query = f"""SELECT r.model_code AS representative_model_code
                            FROM rubicon_data_uk_product_family_list t
                            JOIN rubicon_data_uk_product_family_list r
                            ON t.family_id = r.family_id
                            WHERE t.model_code = '{modelCode}'
                            AND r.key_model_yn = 'Y';"""
                cursor.execute(query)
                key_model = str(cursor.fetchall()[0][0])
            return key_model
        except Exception as e:
            return None
          
    def getReviews_GB(self, modelList):
        try:
            with connection.cursor() as cursor:
                query = f"""SELECT
                                model_code, 
                                review_id, 
                                content,
                                submission_time
                            FROM {self.target_table_GB_sum}
                            WHERE model_code IN {modelList}
                            ORDER BY submission_time DESC
                            limit {self.total_review_num}
                        """
                cursor.execute(query)
                review_result = cursor.fetchall()
                result_df = pd.DataFrame(review_result, columns=['MODEL_CODE', 'REVIEW_ID','CONTENT','SUBMISSION_TIME'])
            return result_df
        except Exception as e:
            return pd.DataFrame()
    
    def getStatistics_GB(self, modelList):
        try:
            with connection.cursor() as cursor:
                query = f"""SELECT
                                AVG(avg_score) as AVG_REVIEW_SCORE,
                                SUM(review_num) as REVIEW_COUNT
                            FROM {self.target_table_GB_stat}
                            WHERE model_code IN {modelList}
                        """
                cursor.execute(query)
                review_result = cursor.fetchall()
                result_df = pd.DataFrame(review_result, columns=['AVG_REVIEW_SCORE', 'REVIEW_COUNT'])
            return result_df
        except Exception as e:
            return pd.DataFrame()
        
    def getStatistics_GB_new(self, modelCode):
        try:
            with connection.cursor() as cursor:
                query = f"""SELECT
                                AVG(avg_score) as AVG_REVIEW_SCORE,
                                SUM(review_num) as REVIEW_COUNT
                            FROM {self.target_table_GB_stat}
                            WHERE model_code = '{modelCode}'
                        """
                cursor.execute(query)
                review_result = cursor.fetchall()
                result_df = pd.DataFrame(review_result, columns=['AVG_REVIEW_SCORE', 'REVIEW_COUNT'])
            return result_df
        except Exception as e:
            return pd.DataFrame()
        
    def getBCModelCodes(self):
        with connection.cursor() as cursor:
            query = f"""
                SELECT DISTINCT pc.mdl_code
                FROM rubicon_data_bc_base BB1
                INNER JOIN rubicon_data_bc_goods_map GBM1
                ON BB1.BC_ID = GBM1.BC_ID
                AND BB1.SITE_CD = 'B2C'
                AND GBM1.SITE_CD = 'B2C'
                AND BB1.DISP_YN = 'Y'
                and now() between BB1.disp_strt_dtm and BB1.disp_end_dtm 
                inner join rubicon_data_product_category pc
                on GBM1.goods_id = pc.goods_id 
                """
            cursor.execute(query)
            review_result = cursor.fetchall()
        return [row[0] for row in review_result]

if __name__ == '__main__':
    django.setup()
    start = time.time()
    query = "갤럭시 S25 평이 어때?"
    extended_info_result = [
          {
            "mapping_code": "갤럭시 워치8 (블루투스, 40mm)",
            "category_lv1": "HHP",
            "category_lv2": "WEARABLE DEVICE VOICE",
            "category_lv3": "Galaxy Watch8",
            "edge": "recommend",
            "meta": "",
            "extended_info": [
              "SM-L320NZSAKOO"
            ],
            "id": 0,
            "expression": "SM-L320NZSAKOO"
          }
        ]
    review_manager = ReviewManager(country='KR', query=query, extended_info_result=extended_info_result, site_cd ='B2C')
    start = time.time()
    #print(review_manager.getBCModelCodes())
    #review_manager.getRepModel_GB('SM-S938BZDHEUB')

    sum_df, stat_df, category_df = review_manager.get_review_sum_stat()
    print(time.time() - start)
    print(sum_df)
    print(stat_df)
    print(category_df)

    