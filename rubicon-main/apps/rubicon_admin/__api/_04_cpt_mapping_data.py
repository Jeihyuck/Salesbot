# import sys
# import psycopg2
# import os
# import traceback

from alpha import __log
from django.core.paginator import Paginator

from apps.rubicon_admin.__function.cpt_mapping import search_product_filter, insert_cpt_keyword_kr_web, insert_cpt_manual_from_keyword_kr, insert_cpt_keyword_uk_web, insert_cpt_uk_manual_from_keyword_uk

def read_cpt_mapping_data(request_dict):
    __log.debug(f"read_cpt_mapping_data: {request_dict}")    
    query = request_dict['query']
    return_data_list = search_product_filter(
        query.get('op_type'),
        'alpha',
        query.get('product', ''),      # get() 사용, 없으면 빈 문자열
        query.get('channel', ''),      # get() 사용, 없으면 빈 문자열
        table_type=query.get('country_code', 'kr').lower()
    )
    __log.debug(f"return_data_list: {return_data_list}")

    results = return_data_list['results']

    # ✅ 각 row에 고유 id 부여 (goods_nm가 고유하다면 그것을 id로 사용)
    for idx, row in enumerate(results):
        if 'id' not in row or row['id'] is None:
            row['id'] = row.get('goods_nm') or idx

    # 페이징 정보 추출
    paging = request_dict.get('paging', {})
    page = int(paging.get('page', 1))
    items_per_page = int(paging.get('itemsPerPage', 25))

    # 페이징 처리
    paginator = Paginator(results, items_per_page)
    page_data = list(paginator.page(page))

    return True, page_data, [{'itemCount': paginator.count}], {
        'type': 'success',
        'title': 'Success',
        'text': 'Product list has retrieved.'
    }

def insert_cpt_keyword(request_dict):
    __log.debug(f"insert_cpt_keyword: {request_dict}")
    cpt_filter = request_dict['query']['cpt_filter']
    country_code = cpt_filter.get('country_code', {}).get('selected', 'KR').lower()
    # 등록자 이메일을 user에서 자동으로 사용
    registrant_email = request_dict.get('user', {}).get('username', '-')
    form_data_base = {
        'env': cpt_filter['op_type']['selected'],
        'database': 'alpha',
        'site_cd': cpt_filter['channel']['selected'],
        'registrant': registrant_email,
        'country_code': country_code
    }

    for item in request_dict['query']['cpt_mapping']:
        if not item.get('cpt_keyword'):  # CPT Keyword가 없는 row는 건너뜀
            continue
        form_data = form_data_base.copy()
        if country_code == 'gb':
            form_data['keyword'] = item.get('cpt_keyword')
            form_data['display_name'] = item.get('goods_nm')
            insert_cpt_keyword_uk_web(form_data)
        else:
            form_data['keyword'] = item.get('cpt_keyword')
            form_data['goods_nm'] = item.get('goods_nm')
            insert_cpt_keyword_kr_web(form_data)
            __log.debug(f"insert_cpt_keyword: {form_data}")

    # manual 테이블 동기화
    if country_code == 'gb':
        return_data_list = insert_cpt_uk_manual_from_keyword_uk(form_data_base['env'], form_data_base['database'])
    else:
        return_data_list = insert_cpt_manual_from_keyword_kr(form_data_base['env'], form_data_base['database'], form_data_base['site_cd'])
    __log.debug(return_data_list)

    return True, {'message': 'CPT Keyword inserted successfully'}, None, {'type': 'success', 'title': 'Success', 'text' : 'CPT Keywords inserted successfully.'}
