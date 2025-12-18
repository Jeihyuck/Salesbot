# import sys
# import psycopg2
# import os
# import traceback

from alpha import __log
from django.core.paginator import Paginator

from apps.rubicon_admin.__function.cpt_mgmt import get_cpt_keywords, update_cpt_keyword, delete_cpt_keyword

def read_cpt_upd_del_data(request_dict):  
    __log.debug(f"read_cpt_keyword_data: {request_dict}")  
    query = request_dict['query']
    paging = request_dict.get('paging', {})
    page = int(paging.get('page', 1))
    items_per_page = int(paging.get('itemsPerPage', 25))

    return_data_list = get_cpt_keywords(
        query.get('op_type'),
        'alpha',
        query.get('channel'),
        query.get('product'),
        query.get('keyword'),
        table_type=query.get('country_code', 'kr').lower()
    )
    results = return_data_list.get('data', [])

    # 각 row에 고유 id 부여 (예: goods_nm가 고유하다면 그것을 id로 사용)
    for idx, row in enumerate(results):
        if 'id' not in row or row['id'] is None:
            # goods_nm가 고유하다면 row['id'] = row['goods_nm']
            # 아니면 아래처럼 인덱스 사용
            row['id'] = row.get('id') or idx

    # ✅ 페이징 처리 추가
    paginator = Paginator(results, items_per_page)
    page_data = list(paginator.page(page))

    return True, page_data, [{'itemCount': paginator.count}], {'type': 'success', 'title': 'Success', 'text': 'Product/CPT Keywords list has retrieved.'}


def update_cpt_upd_del_data(request_dict):
    __log.debug(f"update_cpt_keyword_data: {request_dict}")
    query = request_dict['query']
    cpt_filter = query.get('cpt_filter', {})
    country_code = cpt_filter.get('country_code', {}).get('selected', 'kr').lower()
    updater_email = request_dict.get('user', {}).get('username', '-')
    results = []
    for item in query.get('cpt_update', []):
        result = update_cpt_keyword(
            cpt_filter.get('op_type', {}).get('selected'),
            'alpha',
            cpt_filter.get('channel', {}).get('selected'),
            item.get('keyword'),                              # old_keyword (기존 값)
            item.get('cpt_keyword'),                          # new_keyword (변경할 값)
            item.get('goods_nm'),                             # 제품명 or display_name
            table_type=country_code,
            updater=updater_email                             # 이메일 자동 전달
        )
        results.append(result)
    __log.debug(f"return_data: {results}")

    return True, results, [{'itemCount': len(results)}], {'type': 'success', 'title': 'Success', 'text': 'CPT Keyword updated.'}


def delete_cpt_upd_del_data(request_dict):
    __log.debug(f"delete_cpt_keyword_data: {request_dict}")
    query = request_dict['query']
    cpt_filter = query.get('cpt_filter', {})
    results = []
    all_success = True
    error_messages = []

    for item in query.get('cpt_delete', []):
        if not isinstance(item, dict):
            __log.warning(f"delete_cpt_upd_del_data: item is not dict: {item}")
            all_success = False
            error_messages.append(f"Invalid item: {item}")
            continue
        result = delete_cpt_keyword(
            cpt_filter.get('op_type', {}).get('selected'),
            'alpha',
            cpt_filter.get('channel', {}).get('selected'),
            item.get('keyword'),
            item.get('goods_nm'),
            table_type=cpt_filter.get('country_code', {}).get('selected', 'kr').lower()
        )
        results.append(result)
        # result가 dict이고, 실패시 'success': False를 반환한다고 가정
        # deleted가 0이면 실패로 간주
        if not result.get('success', True) or result.get('deleted', 1) == 0:
            all_success = False
            error_messages.append(result.get('error', 'Delete failed'))

    __log.debug(f"delete_return_data: {results}")

    if not all_success:
        return False, results, [{'itemCount': len(results)}], {
            'type': 'error',
            'title': 'Delete Failed',
            'text': '; '.join(error_messages) or 'Some items failed to delete'
        }
    return True, results, [{'itemCount': len(results)}], {
        'type': 'success',
        'title': 'Success',
        'text': 'CPT Keyword deleted.'
    }


