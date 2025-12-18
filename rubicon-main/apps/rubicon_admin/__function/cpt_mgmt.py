#!/usr/bin/env python3
"""
CPT 키워드 삭제 및 업데이트 관리 스크립트 (KR/UK)
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
    
def delete_cpt_keyword(env, database, site_cd, keyword, item_value, table_type='kr'):
    """
    CPT 키워드 삭제 (KR: goods_nm, UK: display_name)
    + manual, product_filter 테이블에서도 동일하게 삭제
    + filter_nm = 'CPT_UI' 조건 추가
    """
    try:
        config = get_db_connection_config(env, database)
        conn = get_db_connection(config)
        if not conn:
            return {'success': False, 'error': 'DB 연결 실패'}

        cursor = conn.cursor()
        if table_type == 'gb':
            table_name = 'public.rubicon_v3_cpt_keyword_gb'
            manual_table = 'public.rubicon_v3_uk_cpt_manual'
            filter_table = 'public.rubicon_data_uk_product_filter'
            key_col = 'display_name'
        else:
            table_name = 'public.rubicon_v3_cpt_keyword_kr'
            manual_table = 'public.rubicon_v3_cpt_manual'
            filter_table = 'public.rubicon_data_product_filter'
            key_col = 'goods_nm'

        # 1. 키워드 테이블에서 삭제 (filter_nm 없음)
        sql = f"DELETE FROM {table_name} WHERE {key_col} = %s AND keyword = %s AND site_cd = %s"
        cursor.execute(sql, (item_value, keyword, site_cd))
        deleted = cursor.rowcount

        # 2. manual 테이블에서 삭제 (filter_nm = 'CPT_UI')
        manual_sql = f"DELETE FROM {manual_table} WHERE filter_item_nm = %s AND {key_col} = %s AND site_cd = %s AND filter_nm = 'CPT_UI'"
        cursor.execute(manual_sql, (keyword, item_value, site_cd))

        # 3. product_filter 테이블에서 삭제 (filter_nm = 'CPT_UI')
        filter_sql = f"DELETE FROM {filter_table} WHERE filter_item_nm = %s AND {key_col} = %s AND site_cd = %s AND filter_nm = 'CPT_UI'"
        cursor.execute(filter_sql, (keyword, item_value, site_cd))

        conn.commit()
        cursor.close()
        conn.close()
        return {'success': True, 'deleted': deleted}
    except Exception as e:
        return {'success': False, 'error': str(e)}

def update_cpt_keyword(env, database, site_cd, old_keyword, new_keyword, item_value, table_type='kr', updater=None):
    """
    CPT 키워드 업데이트 (KR: goods_nm, UK: display_name)
    + manual, product_filter 테이블에서도 동일하게 업데이트
    + filter_nm = 'CPT_UI' 조건 추가
    + updater(수정자) 값이 있으면 updr_id 컬럼에 반영
    """
    try:
        config = get_db_connection_config(env, database)
        conn = get_db_connection(config)
        if not conn:
            return {'success': False, 'error': 'DB 연결 실패'}

        cursor = conn.cursor()
        if table_type == 'gb':
            table_name = 'public.rubicon_v3_cpt_keyword_gb'
            manual_table = 'public.rubicon_v3_uk_cpt_manual'
            filter_table = 'public.rubicon_data_uk_product_filter'
            key_col = 'display_name'
        else:
            table_name = 'public.rubicon_v3_cpt_keyword_kr'
            manual_table = 'public.rubicon_v3_cpt_manual'
            filter_table = 'public.rubicon_data_product_filter'
            key_col = 'goods_nm'

        # 1. 키워드 테이블에서 업데이트 (filter_nm 없음)
        # updr_id(수정자)는 필수로 항상 입력되어야 하므로 else 분기 없이 처리
        sql = f"""
            UPDATE {table_name}
            SET keyword = %s, updated_on = now(), updr_id = %s
            WHERE {key_col} = %s AND keyword = %s AND site_cd = %s
        """
        cursor.execute(sql, (new_keyword, updater, item_value, old_keyword, site_cd))
        updated = cursor.rowcount  # 실제 업데이트된 row 수

        # 2. manual 테이블에서 업데이트 (filter_nm = 'CPT_UI')
        manual_sql = f"""
            UPDATE {manual_table}
            SET filter_item_nm = %s, updated_on = now()
            WHERE filter_item_nm = %s AND {key_col} = %s AND site_cd = %s AND filter_nm = 'CPT_UI'
        """
        cursor.execute(manual_sql, (new_keyword, old_keyword, item_value, site_cd))

        # 3. product_filter 테이블에서 업데이트 (filter_nm = 'CPT_UI')
        filter_sql = f"""
            UPDATE {filter_table}
            SET filter_item_nm = %s, updated_on = now()
            WHERE filter_item_nm = %s AND {key_col} = %s AND site_cd = %s AND filter_nm = 'CPT_UI'
        """
        cursor.execute(filter_sql, (new_keyword, old_keyword, item_value, site_cd))

        conn.commit()
        cursor.close()
        conn.close()
        return {'success': True, 'updated': updated}
    except Exception as e:
        return {'success': False, 'error': str(e)}

def get_cpt_keywords(env, database, site_cd, item_value=None, keyword_value=None, table_type='kr'):
    """
    CPT 키워드 조회 (KR: goods_nm, UK: display_name)
    item_value: 제품명
    keyword_value: 키워드
    """
    try:
        config = get_db_connection_config(env, database)
        conn = get_db_connection(config)
        if not conn:
            return {'success': False, 'error': 'DB 연결 실패'}

        cursor = conn.cursor()
        where_clauses = ["site_cd = %s"]
        params = [site_cd]

        if table_type == 'gb':
            table_name = 'public.rubicon_v3_cpt_keyword_gb'
            if item_value:
                where_clauses.append("display_name ILIKE %s")
                params.append(f"%{item_value}%")
            if keyword_value:
                where_clauses.append("keyword ILIKE %s")
                params.append(f"%{keyword_value}%")
            sql = f"SELECT display_name, keyword, site_cd, updated_on FROM {table_name} WHERE {' AND '.join(where_clauses)} ORDER BY display_name DESC"
        else:
            table_name = 'public.rubicon_v3_cpt_keyword_kr'
            if item_value:
                where_clauses.append("goods_nm ILIKE %s")
                params.append(f"%{item_value}%")
            if keyword_value:
                where_clauses.append("keyword ILIKE %s")
                params.append(f"%{keyword_value}%")
            sql = f"SELECT goods_nm, keyword, site_cd, updated_on FROM {table_name} WHERE {' AND '.join(where_clauses)} ORDER BY goods_nm DESC"

        cursor.execute(sql, tuple(params))
        rows = cursor.fetchall()
        cursor.close()
        conn.close()
        result = []
        for row in rows:
            if table_type == 'gb':
                result.append({
                    'goods_nm': row[0],
                    'keyword': row[1],
                    'site_cd': row[2],
                    'updated_on': row[3]
                })
            else:
                result.append({
                    'goods_nm': row[0],
                    'keyword': row[1],
                    'site_cd': row[2],
                    'updated_on': row[3]
                })
        return {'success': True, 'data': result}
    except Exception as e:
        return {'success': False, 'error': str(e)}

def main():
    """
    예시 실행: python _mgmt_cpt.py delete/update env database site_cd keyword item_value [new_keyword] [table_type]
    """
    if len(sys.argv) < 7:
        print("사용법: python _mgmt_cpt.py delete/update env database site_cd keyword item_value [new_keyword] [table_type]")
        sys.exit(1)

    action = sys.argv[1]
    env = sys.argv[2]
    database = sys.argv[3]
    site_cd = sys.argv[4]
    keyword = sys.argv[5]
    item_value = sys.argv[6]
    new_keyword = sys.argv[7] if action == 'update' and len(sys.argv) > 7 else None
    table_type = sys.argv[8] if len(sys.argv) > 8 else 'kr'

    if action == 'delete':
        result = delete_cpt_keyword(env, database, site_cd, keyword, item_value, table_type)
    elif action == 'update':
        if not new_keyword:
            print("update 시 new_keyword 값이 필요합니다.")
            sys.exit(1)
        result = update_cpt_keyword(env, database, site_cd, keyword, new_keyword, item_value, table_type)
    else:
        print("지원하지 않는 action입니다. delete 또는 update만 가능합니다.")
        sys.exit(1)

    print(result)

if __name__ == '__main__':
    main()