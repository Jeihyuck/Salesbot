# line 2 ~ 7 테스트 시 주석 해제
import sys
sys.path.append('/www/alpha/')
import os
import re
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'alpha.settings')

import re
import time
import pandas as pd
from datetime import datetime, timedelta, timezone
from dateutil.relativedelta import relativedelta
from django.db import connection

from apps.rubicon_v3.__function import __embedding_rerank as embedding_rerank


def extract_date_operator(op_s):
    pattern = r'\(op\)([-=*~])(\d*)([ymwdqDsS])'
    match = re.search(pattern, op_s)

    if match:
        operator = match.group(1)
        number = match.group(2)
        unit = match.group(3)

        number = int(number) if number else None

        return operator, number, unit
    else:
        return None, None, None

def extract_number(text):
    match = re.search(r'(\d+)', text)
    if match:
        return int(match.group(1))
    return None

def get_weekday_sequence(date_str, number):
    parts = date_str.split('-')
    if len(parts) == 3:
        date_obj = datetime.strptime(date_str, '%Y-%m-%d')
        if date_obj.weekday() == number:
            return[date_obj.strftime('%Y-%m-%d')]
        return []

    if len(parts) == 2:
        year, month = map(int, parts)
        start_date = datetime(year, month, 1)
        end_date = start_date + relativedelta(months=1) - timedelta(days=1)
    else:
        year = int(parts[0])
        start_date = datetime(year, 1, 1)
        end_date = datetime(year, 12, 31)
    
    days_until_first = (number - start_date.weekday()) % 7
    first_occurence = start_date + timedelta(days=days_until_first)

    days_since_last = (end_date.weekday() - number) % 7
    last_occurence = end_date - timedelta(days=days_since_last)

    if first_occurence > last_occurence:
        return []
    
    result = []
    current_date = first_occurence

    num_occurences = ((last_occurence - first_occurence).days // 7) + 1
    for i in range(num_occurences):
        result.append((first_occurence + timedelta(days=i*7)).strftime('%Y-%m-%d'))

    return result


def match_and_parse_datetime(standardized_ner, country_code, message_id, promo_yn = False):
    date_result_list = []
    if promo_yn:
        ner_date = [d for d in standardized_ner if d.get('field') == 'promotion_date']
    else:
        ner_date = [d for d in standardized_ner if d.get('field') == 'product_release_date']

    for ner_part in ner_date:
        # ner_date = [d for d in ner_part if d.get('field') == 'date']
        tz = timezone(timedelta(hours=9)) if country_code == 'KR' else timezone(timedelta(hours=0))
        current_date = datetime.now(tz)

        # original_date_list =  sum([d.get('expression').split(sep=' ') for d in ner_part if d.get('field') == 'date'], [])
        original_date_list = sum([ner_part.get('expression', '').split(sep=' ')], [])
        year_list = [s for s in original_date_list if isinstance(s, str) and re.match(r'^\d+(?:년|연|년도|YY|년식)$', s)]
        month_list = [s for s in original_date_list if isinstance(s, str) and re.match(r'^\d+(?:월|MM)$', s)]
        day_list = [s for s in original_date_list if isinstance(s, str) and re.match(r'^\d+(?:일|DD)$', s)]
        nl_dates = year_list + month_list + day_list
        remained_date_list = list(set(original_date_list) - set(nl_dates))
        full_date_list = []
        dow = None
        recent_key = False

        with connection.cursor() as curs:
            for s in remained_date_list:
                match_expression = re.search(r'\d+', s)
                if match_expression:
                    s_num = match_expression.group()
                    st, ed = match_expression.span()
                    s_text = s[:st] + s[ed:]
                    s = s_text
                else:
                    s_num = None

                embedded_datetime_value = embedding_rerank.baai_embedding(s, message_id)[0]
                exact_query = f"""
                                SELECT * FROM rubicon_v3_date_match
                                WHERE expression = '{str(s)}'
                                AND country_code = '{country_code}'
                                AND active = TRUE
                                """
                similarity_query = f"""
                                SELECT DISTINCT
                                    dm.mapping_code,
                                    dm.expression,
                                    dm.type,
                                    subq.distance
                                FROM (
                                    SELECT 
                                        expression,
                                        mapping_code,
                                        type,
                                        country_code,
                                        embedding <=> '{str(embedded_datetime_value)}' AS distance
                                    FROM rubicon_v3_date_match
                                    WHERE active = TRUE
                                    AND country_code = '{country_code}'
                                    ORDER BY distance
                                    LIMIT 3
                                ) subq
                                JOIN rubicon_v3_date_match dm 
                                    ON dm.expression = subq.expression
                                    AND dm.active = TRUE
                                    AND dm.country_code = subq.country_code
                                    AND dm.type = subq.type
                                ORDER BY subq.distance
                                LIMIT 12
                                """
                curs.execute(exact_query)
                res_date = curs.fetchall()
                if res_date:
                    date_df = pd.DataFrame(res_date, columns=[c.name for c in curs.description])
                    date_mc = date_df['mapping_code'].unique().tolist()
                    date_expr = date_df['expression'].iloc[0]
                    date_type = date_df['type'].iloc[0]

                else:
                    curs.execute(similarity_query)
                    res_date = curs.fetchall()
                    if res_date:
                        date_df = pd.DataFrame(res_date, columns=[c.name for c in curs.description])
                        min_dist = date_df['distance'].min()
                        filtered_df = date_df[date_df['distance'] == min_dist]
                        date_mc = filtered_df['mapping_code'].unique().tolist()
                        date_expr = filtered_df['expression'].iloc[0]
                        date_type = filtered_df['type'].iloc[0]
                    else:
                        # return 'ERROR'
                        continue
                # if date_expr in ['최신', 'mostrecent', '최근', '근래', '새로운', 'latest', 'recently', 'new', '요새', '요즘', 'thesedays', 'nowadays', 'lately']:
                #     recent_key = True
                if '(op)~12m' in date_mc:
                    recent_key = True

                if date_type == 'D':
                    dow = date_mc
                    continue
                if not any('op' in s for s in date_mc if isinstance(s, str)): 
                    if date_type == 'y':
                        year_list.extend(date_mc)
                    elif date_type == 'm':
                        month_list.extend(date_mc)
                    elif date_type == 'd':
                        day_list.extend(date_mc)
                else:
                    for op_s in date_mc:
                        operator, number, unit = extract_date_operator(op_s)
                        if operator == '=':
                            if unit == 'y':
                                year_list.extend([f"{current_date.year}년"])
                                # full_date_list.append(current_date.strftime('%Y'))
                            elif unit == 'm':
                                month_list.extend([f"{current_date.month:02d}월"])
                                # full_date_list.append(current_date.strftime('%Y-%m'))
                            elif unit == 'd':
                                day_list.extend([f"{current_date.day:02d}일"])
                                # full_date_list.append(current_date.strftime('%Y-%m-%d'))
                            elif unit == 'w':
                                nth_day_of_week = current_date.weekday()
                                first_day_of_week = current_date - timedelta(days = nth_day_of_week)
                                this_week_dates = [(first_day_of_week + timedelta(days = i)).strftime('%Y-%m-%d') for i in range(7)]
                                full_date_list.extend(this_week_dates)
                            elif unit == 'q':
                                first_month_of_quarter = ((current_date.month - 1) // 3) * 3 + 1
                                months_in_quarter = [first_month_of_quarter + i for i in range(3)]
                                quarter_months = [f"{current_date.year}-{month:02d}" for month in months_in_quarter]
                                full_date_list.extend(quarter_months)

                        else: 
                            if number is None:
                                if s_num:
                                    number = int(s_num)
                                else:
                                    number = 0 
                            if operator == "*" and date_type == 'q':
                                first_month_of_quarter = number * 3 - 2
                                months_in_quarter = [str(first_month_of_quarter + i) for i in range(3)]
                                month_list.extend(months_in_quarter)
                            elif operator == "*" and date_type == 's':
                                if number == 1:
                                    month_list.extend(['3', '4', '5', '6'])
                                elif number == 2:
                                    month_list.extend(['9', '10', '11', '12'])
                            # elif operator == "*" and date_type == 'S':
                            #     if number == 1:
                            #         month_list.extend(['9', '10', '11', '12'])
                            #     elif number == 2:
                            #         month_list.extend(['1', '2', '3'])
                            #     elif number == 3:
                            #         month_list.extend(['4', '5', '6'])
                            elif operator == '~':
                                number = -number + 1
                                current = current_date
                                unit_mapping = {
                                    'y': {'years': number},
                                    'm': {'months': number},
                                    'w': {'weeks': number},
                                    'd': {'days': number},
                                }

                                delta_params = unit_mapping.get(unit, {'days': 0})
                                date_fin = current_date + relativedelta(**delta_params)
                                period_list = []

                                if unit == 'y':
                                    increment = lambda d: d + relativedelta(years = 1)
                                    date_format = '%Y'
                                elif unit == 'm':
                                    increment = lambda d: d + relativedelta(months = 1)
                                    date_format = '%Y-%m'
                                elif unit == 'd':
                                    increment = lambda d: d + relativedelta(days = 1)
                                    date_format = '%Y-%m-%d'
                                elif unit == 'w':
                                    increment = lambda d: d + relativedelta(weeks = 1)
                                    date_format = '%Y-W%U'
                                
                                while date_fin <= current:
                                    period_list.append(date_fin.strftime(date_format))
                                    date_fin = increment(date_fin)
                                
                                full_date_list.extend(period_list)

                            elif operator == '-':
                                number = -number
                            
                                unit_mapping = {
                                    'y': {'years': number},
                                    'm': {'months': number},
                                    'w': {'weeks': number},
                                    'd': {'days': number},
                                }

                                delta_params = unit_mapping.get(unit, {'days': 0})
                                date_fin = current_date + relativedelta(**delta_params)
                                if unit == 'y':
                                    year_list.extend([f"{date_fin.year}년"])
                                elif unit == 'm':
                                    month_list.extend([f"{date_fin.month:02d}월"])
                                elif unit == 'd':
                                    day_list.extend([f"{date_fin.day:02d}일"])
                                elif unit == 'w':
                                    nth_day_of_week = date_fin.weekday()
                                    first_day_of_week = date_fin - timedelta(days = nth_day_of_week)
                                    this_week_dates = [(first_day_of_week + timedelta(days = i)).strftime('%Y-%m-%d') for i in range(7)]
                                    full_date_list.extend(this_week_dates)
                                elif unit == "q":
                                    first_month_of_quarter = (number + (current_date.month - 1) // 3) * 3 + 1
                                    first_year_of_quarter = current_date.year
                                    if first_month_of_quarter < 0:
                                        first_month_of_quarter += 12
                                        first_year_of_quarter -= 1
                                    months_in_quarter = [first_month_of_quarter + i for i in range(3)]
                                    quarter_months = [f"{first_year_of_quarter}-{month:02d}" for month in months_in_quarter]
                                    full_date_list.extend(quarter_months)
        if not any([year_list, month_list, day_list]):
            result_temp = []
        else:
            if day_list and (not year_list or not month_list):
                if not year_list:
                    year_list = [f"{current_date.year}년"]
                if not month_list:
                    month_list = [f"{current_date.month}월"]
            elif month_list and not year_list:
                year_list = [f"{current_date.year}년"]


            result_temp = []

            if year_list and not month_list and not day_list:
                for year_text in year_list:
                    year = extract_number(year_text)
                    if year:
                        result_temp.append(f"{year}")
            
            elif year_list and month_list and not day_list:
                for year_text in year_list:
                    year = extract_number(year_text)
                    if year:
                        for month_text in month_list:
                            month = extract_number(month_text)
                            if month:
                                result_temp.append(f"{year}-{month:02d}")

            elif year_list and month_list and day_list:
                for year_text in year_list:
                    year = extract_number(year_text)
                    if year:
                        for month_text in month_list:
                            month = extract_number(month_text)
                            if month:
                                for day_text in day_list:
                                    day = extract_number(day_text)
                                    if day:
                                        result_temp.append(f"{year}-{month:02d}-{day:02d}")
            

        full_date_list.extend(result_temp)
        dow_filter_list = []
        # print(f"dow: {dow}")
        # print(f"full_date_list: {full_date_list}")
        if dow:
            for op_s in dow:
                operator, number, unit = extract_date_operator(op_s)
                # print(operator)
                # print(number)
                # print(unit)
                if full_date_list and operator == '=':
                    for date_str in full_date_list:
                        dow_filter_list.extend(get_weekday_sequence(date_str, number))
                
                elif not full_date_list and operator == '=':
                    current_weekday = current_date.weekday()
                    delta = current_weekday - number
                    t_date = current_date - timedelta(days=delta)
                    dow_filter_list.append(t_date.strftime('%Y-%m-%d'))

                elif not full_date_list and operator == '-':
                    current_weekday = current_date.weekday()
                    delta = current_weekday - number
                    if number >= current_weekday:
                        delta += 7
                    t_date = current_date - timedelta(days=delta)
                    dow_filter_list.append(t_date.strftime('%Y-%m-%d'))


        if dow_filter_list:
            full_date_list = dow_filter_list
        
        if recent_key:
            full_date_list.append('NEWEST')
        
        date_result_list.append(
            {
                'expression': ner_part.get('expression', ''),
                'date_list': full_date_list
            }
        )
    
    return date_result_list


if __name__ == '__main__':
    django.setup()
    country_code = 'KR'
    expr = '이번'
    ner_date = [{
            "field": "product_release_date",
            "expression": expr,
            "operator": "in"
        }]
    # ner_date = [{
    #         "field": "date",
    #         "expression": '2025년 1월',
    #         "operator": "in"
    #     },
    #     {
    #         "field": "date",
    #         "expression": '2025년 4월',
    #         "operator": "in"
    #     }
    #     ]
    start_time = time.time()
    res = match_and_parse_datetime(ner_date, country_code, "")
    elapsed_time = time.time() - start_time
    print(f"matching date time: {elapsed_time}")
    print(res)
