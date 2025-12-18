#!/usr/bin/env python3
"""
특정 테이블에 프론트엔드에서 입력받은 값을 INSERT하는 웹 전용 스크립트
"""

import sys
import psycopg2
import os
import traceback

DEFAULT_CONNECTION_CONFIG = {
    'port': os.environ.get("POSTGRESQL_PORT"),
    'user': os.environ.get("POSTGRESQL_ID"),
    'password': os.environ.get("POSTGRESQL_PWD")
}

def get_available_hosts():
    """사용 가능한 Azure PostgreSQL 호스트 목록"""
    return {
        'dev': {
            'name': 'RUBICON-DEV',
            'host': 'dev-postgre-rb-krc.postgres.database.azure.com',
            'region': 'KR'
        },
        'stg-kr': {
            'name': 'RUBICON-STG-KR',
            'host': 'stg-postgre-rb-krc.postgres.database.azure.com',
            'region': 'KR'
        },
        'prd-kr': {
            'name': 'RUBICON-PRD-KR',
            'host': 'prd-postgre-rb-krc.postgres.database.azure.com',
            'region': 'KR'
        },
        'stg-uk': {
            'name': 'RUBICON-STG-UK',
            'host': 'stg-postgre-rb-uks.postgres.database.azure.com',
            'region': 'GB'
        },
        'prd-uk': {
            'name': 'RUBICON-PRD-UK',
            'host': 'prd-postgre-rb-uks.postgres.database.azure.com',
            'region': 'GB'
        }
    }

def get_db_connection_config(env_name, database_name='alpha'):
    """환경별 데이터베이스 연결 설정"""
    base_config = {
        'port': os.environ.get("POSTGRESQL_PORT"),
        'user': os.environ.get("POSTGRESQL_ID"),
        'password': os.environ.get("POSTGRESQL_PWD")
    }
    hosts = get_available_hosts()
    env_key = env_name.lower()
    env_mapping = {
        'dev': 'dev',
        'prd-kr': 'prd-kr',
        'prd-uk': 'prd-uk',
        'stg-kr': 'stg-kr',
        'stg-uk': 'stg-uk'
    }
    mapped_env = env_mapping.get(env_key, env_key)
    if mapped_env in hosts:
        host_config = hosts[mapped_env]
        return {
            **base_config,
            'host': host_config['host'],
            'database': database_name,
            'env_name': host_config['name'],
            'region': host_config['region']
        }
    else:
        raise ValueError(f"지원하지 않는 환경: {env_name}. 사용 가능한 환경: {list(env_mapping.keys())}")

def get_db_connection(config):
    """데이터베이스 연결 생성"""
    try:
        connection = psycopg2.connect(
            host=config['host'],
            port=config['port'],
            database=config['database'],
            user=config['user'],
            password=config['password'],
            connect_timeout=30
        )
        return connection
    except psycopg2.Error:
        return None
    except Exception:
        return None

def parse_table_name(table_name):
    """테이블명에서 스키마와 테이블을 분리"""
    if '.' in table_name:
        schema, table = table_name.split('.', 1)
        return schema, table
    else:
        return 'public', table_name

def get_table_columns(cursor, schema_name, table_only):
    """테이블의 컬럼 정보 조회"""
    cursor.execute("""
        SELECT column_name, data_type 
        FROM information_schema.columns 
        WHERE table_schema = %s AND table_name = %s 
        ORDER BY ordinal_position
    """, (schema_name, table_only))
    return cursor.fetchall()

def search_product_filter(env, database, keyword, channel, table_type='kr'):
    """
    KR/GB 버튼에 따라 다른 테이블과 쿼리 사용
    """
    try:
        config = get_db_connection_config(env, database)
        conn = get_db_connection(config)
        if not conn:
            return {'success': False, 'error': 'DB 연결 실패'}

        cursor = conn.cursor()

        if table_type == 'gb':
            schema_name, table_only = parse_table_name('rubicon_data_uk_product_filter')
            sql = f"""
                SELECT DISTINCT display_name as goods_nm FROM {schema_name}.{table_only}
                WHERE display_name ILIKE %s
                AND site_cd = %s
                AND model_code !~ '^F-'
                AND category_lv2 NOT IN ('Computer Accessories', 'Display Accessories', 'Home Appliance Accessories', 'Mobile Accessories', 'Projector Accessories', 'SmartThings', 'TV Accessories', 'TV Audio Accessories')
                ORDER BY display_name DESC
            """
            cursor.execute(sql, (f'%{keyword}%', channel))
            rows = cursor.fetchall()
            results = [{'goods_nm': row[0]} for row in rows]
        else:
            schema_name, table_only = parse_table_name('rubicon_data_product_filter')
            sql = f"""
                SELECT distinct goods_nm FROM {schema_name}.{table_only}
                WHERE goods_nm ILIKE %s
                AND site_cd = %s
                AND set_tp_cd in ('00', '10')
                AND product_category_lv3 NOT IN ('Accessory Kit', 'Adapter', 'Band', 'Battery', 'Cable', 'Camera', 'Cartridges', 'Case', 'Charger', 'Cover', 'Film', 'Installation Kit', 'Keyboard', 'Kimchi Container', 'Mouse', 'Panel', 'Remote Controller', 'Shelf', 'Stand', 'Tray','Box','Brush','Connector','Container','Dispenser','Dust Bag','Filter','Foucet','Hanger','Kettle','Memory','Mircrophone','Mop','Paper','Station','Storage','Weight', 'Plate', 'Card', 'Strap', 'Pouch')
                ORDER BY goods_nm DESC
            """
            cursor.execute(sql, (f'%{keyword}%', channel))
            rows = cursor.fetchall()
            results = [{'goods_nm': row[0]} for row in rows]

        cursor.close()
        conn.close()

        return {'success': True, 'results': results}

    except Exception as e:
        traceback.print_exc()
        return {'success': False, 'error': str(e)}

def insert_cpt_keyword_kr_web(form_data):
    """
    KR용 public.rubicon_v3_cpt_keyword_kr 테이블에 값 INSERT (웹 버전)
    중복 키워드(goods_nm, keyword, site_cd)가 이미 있으면 INSERT하지 않음
    """
    try:
        env = form_data.get('env')
        database = form_data.get('database', 'alpha')
        site_cd = form_data.get('site_cd')
        keyword = form_data.get('keyword')
        goods_nm = form_data.get('goods_nm')
        registrant = form_data.get('registrant')  # 등록자 처리

        config = get_db_connection_config(env, database)
        conn = get_db_connection(config)
        if not conn:
            return {'success': False, 'error': 'DB 연결 실패'}

        cursor = conn.cursor()
        table_name = 'public.rubicon_v3_cpt_keyword_kr'
        # 필수 값 체크
        if not (goods_nm and keyword and site_cd):
            cursor.close()
            conn.close()
            return {'success': False, 'error': '필수 값 누락'}

        # 중복 체크
        check_sql = f"""
            SELECT 1 FROM {table_name}
            WHERE goods_nm = %s AND keyword = %s AND site_cd = %s
            LIMIT 1
        """
        cursor.execute(check_sql, (goods_nm, keyword, site_cd))
        exists = cursor.fetchone()
        if exists:
            cursor.close()
            conn.close()
            return {'success': False, 'error': '이미 등록된 키워드입니다.', 'duplicate': True}

        # regr_id, updr_id 모두 registrant 값으로 insert
        sql = f"""
            INSERT INTO {table_name} (goods_nm, keyword, created_on, updated_on, site_cd, regr_id, updr_id)
            VALUES (%s, %s, now(), now(), %s, %s, %s)
        """
        cursor.execute(sql, (goods_nm, keyword, site_cd, registrant, registrant))

        conn.commit()
        cursor.close()
        conn.close()

        return {'success': True, 'action': 'inserted'}

    except Exception as e:
        traceback.print_exc()
        return {'success': False, 'error': str(e)}

def insert_cpt_keyword_uk_web(form_data):
    """
    GB public.rubicon_v3_cpt_keyword_uk 테이블에 값 INSERT (웹 버전)
    중복 키워드(display_name, keyword, site_cd)가 이미 있으면 INSERT하지 않음
    """
    try:
        env = form_data.get('env')
        database = form_data.get('database', 'alpha')
        site_cd = form_data.get('site_cd')
        keyword = form_data.get('keyword')
        display_name = form_data.get('display_name')
        registrant = form_data.get('registrant')  # 등록자 처리

        config = get_db_connection_config(env, database)
        conn = get_db_connection(config)
        if not conn:
            return {'success': False, 'error': 'DB 연결 실패'}

        cursor = conn.cursor()
        table_name = 'public.rubicon_v3_cpt_keyword_gb'
        # 필수 값 체크
        if not (display_name and keyword and site_cd):
            cursor.close()
            conn.close()
            return {'success': False, 'error': '필수 값 누락'}

        # 중복 체크
        check_sql = f"""
            SELECT 1 FROM {table_name}
            WHERE display_name = %s AND keyword = %s AND site_cd = %s
            LIMIT 1
        """
        cursor.execute(check_sql, (display_name, keyword, site_cd))
        exists = cursor.fetchone()
        if exists:
            cursor.close()
            conn.close()
            return {'success': False, 'error': '이미 등록된 키워드입니다.', 'duplicate': True}

        # regr_id, updr_id 모두 registrant 값으로 insert
        sql = f"""
            INSERT INTO {table_name} (display_name, keyword, created_on, updated_on, country_code, site_cd, regr_id, updr_id)
            VALUES (%s, %s, now(), now(), 'GB', %s, %s, %s)
        """
        cursor.execute(sql, (display_name, keyword, site_cd, registrant, registrant))

        conn.commit()
        cursor.close()
        conn.close()

        return {'success': True, 'action': 'inserted'}

    except Exception as e:
        return {'success': False, 'error': str(e)}

def insert_cpt_manual_from_keyword_kr(env, database='alpha', site_cd='B2C'):
    """
    rubicon_v3_cpt_keyword_kr → rubicon_v3_cpt_manual, rubicon_data_product_filter 신규 데이터 INSERT (동일 쿼리 결과)
    """
    try:
        config = get_db_connection_config(env, database)
        conn = get_db_connection(config)
        if not conn:
            return {'success': False, 'error': 'DB 연결 실패'}

        cursor = conn.cursor()

        select_sql = f"""
        SELECT DISTINCT aa.business_unit, aa.product_category_lv1, aa.product_category_lv2, aa.product_category_lv3, aa.model_group_code, aa.model_name, aa.product_model,
            aa.mdl_code, aa.goods_id, aa.goods_nm, aa.disp_clsf_nm, aa.filter_nm, aa.filter_item_nm, aa.release_date, aa.set_tp_cd, aa.created_on, aa.updated_on, aa.site_cd
        FROM (
            SELECT DISTINCT r.business_unit, r.product_category_lv1, r.product_category_lv2, r.product_category_lv3, r.model_group_code, r.model_name, r.product_model, 
                r.mdl_code, r.goods_id, c.goods_nm, r.disp_clsf_nm, 'CPT_UI' AS filter_nm, c.keyword as filter_item_nm, r.release_date, r.set_tp_cd, c.created_on, c.updated_on, c.site_cd
            FROM public.rubicon_v3_cpt_keyword_kr c
            INNER JOIN public.rubicon_data_product_filter r ON c.goods_nm = r.goods_nm
            	and r.site_cd = %s
        ) aa
        WHERE NOT EXISTS (
            SELECT 1
            FROM public.rubicon_v3_cpt_manual r2
            WHERE aa.mdl_code = r2.mdl_code
              AND aa.filter_item_nm = r2.filter_item_nm
              AND aa.goods_nm = r2.goods_nm 
              AND r2.site_cd = %s
        );
        """
        cursor.execute(select_sql, (site_cd, site_cd))
        rows = cursor.fetchall()

        if not rows:
            cursor.close()
            conn.close()
            return {'success': True, 'inserted': 0, 'message': '신규 데이터 없음'}

        insert_manual_sql = """
        INSERT INTO public.rubicon_v3_cpt_manual (
            business_unit, product_category_lv1, product_category_lv2, product_category_lv3, model_group_code, model_name, product_model,
            mdl_code, goods_id, goods_nm, disp_clsf_nm, filter_nm, filter_item_nm, release_date, set_tp_cd, created_on, updated_on, site_cd
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        for row in rows:
            cursor.execute(insert_manual_sql, row)

        insert_filter_sql = """
        INSERT INTO public.rubicon_data_product_filter (
            business_unit, product_category_lv1, product_category_lv2, product_category_lv3, model_group_code, model_name, product_model,
            mdl_code, goods_id, goods_nm, disp_clsf_nm, filter_nm, filter_item_nm, release_date, set_tp_cd, created_on, updated_on, site_cd
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        for row in rows:
            cursor.execute(insert_filter_sql, row)

        conn.commit()
        inserted_count = len(rows)
        cursor.close()
        conn.close()
        return {'success': True, 'inserted': inserted_count}

    except Exception as e:
        traceback.print_exc()
        return {'success': False, 'error': str(e)}

def insert_cpt_uk_manual_from_keyword_uk(env, database='alpha'):
    """
    rubicon_v3_cpt_keyword_uk → rubicon_v3_uk_cpt_manual, rubicon_data_uk_product_filter 신규 데이터 INSERT (동일 쿼리 결과, UK용)
    """
    try:
        config = get_db_connection_config(env, database)
        conn = get_db_connection(config)
        if not conn:
            return {'success': False, 'error': 'DB 연결 실패'}

        cursor = conn.cursor()

        select_sql = """
        SELECT DISTINCT aa.model_code, aa.display_name, aa.category_lv1, aa.category_lv2, aa.category_lv3, aa.filter_nm, aa.filter_item_nm, aa.created_on, aa.updated_on, aa.launch_date, aa.country_code, aa.site_cd
        FROM (
            SELECT DISTINCT r.model_code, c.display_name, r.category_lv1, r.category_lv2, r.category_lv3, 'CPT_UI' AS filter_nm, c.keyword as filter_item_nm, c.created_on, c.updated_on, r.launch_date, c.country_code, c.site_cd
            FROM public.rubicon_v3_cpt_keyword_gb c
            INNER JOIN public.rubicon_data_uk_product_filter r ON c.display_name = r.display_name
        ) aa
        WHERE NOT EXISTS (
            SELECT 1
            FROM public.rubicon_v3_uk_cpt_manual r2
            WHERE aa.model_code = r2.model_code
              AND aa.filter_item_nm = r2.filter_item_nm
        )
        """
        cursor.execute(select_sql)
        rows = cursor.fetchall()

        if not rows:
            cursor.close()
            conn.close()
            return {'success': True, 'inserted': 0, 'message': '신규 데이터 없음'}

        insert_manual_sql = """
        INSERT INTO public.rubicon_v3_uk_cpt_manual (
            model_code, display_name, category_lv1, category_lv2, category_lv3, filter_nm, filter_item_nm, created_on, updated_on, launch_date, country_code, site_cd
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        for row in rows:
            cursor.execute(insert_manual_sql, row)

        insert_filter_sql = """
        INSERT INTO public.rubicon_data_uk_product_filter (
            model_code, display_name, category_lv1, category_lv2, category_lv3, filter_nm, filter_item_nm, created_on, updated_on, launch_date, country_code, site_cd
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        for row in rows:
            cursor.execute(insert_filter_sql, row)

        conn.commit()
        inserted_count = len(rows)
        cursor.close()
        conn.close()
        return {'success': True, 'inserted': inserted_count}

    except Exception as e:
        traceback.print_exc()
        return {'success': False, 'error': str(e)}

def main():
    """웹 모드 전용 메인 실행 함수"""
    try:
        import json
        env = os.environ.get('ENV')
        database = os.environ.get('DATABASE', 'alpha')
        mdl_code = os.environ.get('MDL_CODE')
        goods_nm = os.environ.get('GOODS_NM')
        keyword = os.environ.get('KEYWORD')
        site_cd = os.environ.get('SITE_CD')

        form_data = {
            'env': env,
            'database': database,
            'mdl_code': mdl_code,
            'goods_nm': goods_nm,
            'keyword': keyword,
            'site_cd': site_cd
        }

        result = insert_cpt_keyword_kr_web(form_data)
        print(result)

    except Exception as e:
        sys.exit(1)

if __name__ == '__main__':
    main()
