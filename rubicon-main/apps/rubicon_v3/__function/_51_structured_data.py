import sys

sys.path.append("/www/alpha/")
import os
import django
import json
import pandas as pd
import googlemaps
from datetime import datetime

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "alpha.settings")
django.setup()

from typing import Dict, List
from geopy.distance import geodesic
from django.db import connection, transaction, IntegrityError
from apps.rubicon_v3.__function import __utils as utils
from apps.rubicon_v3.__function import __embedding_rerank
from apps.rubicon_v3.models import Google_Map_Info

GOOGLE_MAP_API_KEY = os.environ.get("GOOGLE_MAP_API_KEY")


"""
Use Google API to retrieve the latitude and longitude coordinates of the specified region
""" 
def get_long_lat_values(location_expression, country_code):
    try:
        message = ""
        gmaps = googlemaps.Client(key=GOOGLE_MAP_API_KEY)
        geo_val = gmaps.geocode(location_expression, language="en")

        if not geo_val or len(geo_val) == 0:
            message = f"No results found for: {location_expression}"
            return None, message, None

        if "geometry" in geo_val[0] and "location" in geo_val[0]["geometry"]:
            location = geo_val[0]["geometry"]["location"]
            address_components = geo_val[0].get('address_components')
            country_code_google = [item['short_name'] for item in address_components if 'country' in item.get('types', [])][0]
            if country_code_google == 'UK':
                country_code_google = 'GB' #  In Rubicon, it is necessary to replace UK with GB. 
                
            if country_code != country_code_google: # Check the country code of the search region and the Rubicon country code
                message = f"Store Invalid. Location: '{location_expression}' is in '{country_code_google}' which is outside of supported country '{country_code}'."
                return None, message, country_code_google
            lat_lng = [location["lat"], location["lng"]]

            return [geo_val, lat_lng], message, country_code_google

        else:
            message = f"Unexpected response structure \n API Response: \n {geo_val}"
            return None, message, None

    except Exception as e:
        message = f"Error in Google Maps API: {str(e)}"
        return None, message, None
    
"""
 Match the top 3 closest stores for expressions identified with the 'location' field in NER.
""" 
def location_match(component, service_center_flag, country_code, samsung_experience_store_flag=False, k=3):
    debug_messages = []
    plaza_df = pd.DataFrame()
    with connection.cursor() as cursor:
        user_location = component.get('expression',"")
        if country_code == "KR":
            user_location_tmp = user_location.replace(" ","").lower()
            
        else:
            user_location_tmp = user_location.lower()
        user_coords = None
        
        map_sql = """
        SELECT pos, google_country_code
        FROM rubicon_v3_google_map_info
        WHERE country_code = %s
        AND keyword = %s
        AND google_country_code = %s
        FOR UPDATE
        """
        cursor.execute(map_sql, [country_code, user_location_tmp, country_code])
        map_results = cursor.fetchall()

        # Search for the given expression in rubicon_v3_google_map_info, and if found, use the stored latitude and longitude.
        if map_results:
            map_df = pd.DataFrame(map_results, columns = [c.name for c in cursor.description])
            user_coords = json.loads(map_df['pos'].iloc[0])
            country_code_google = map_df['google_country_code'].iloc[0]
            
        else:
            # If it is a new expression, perform a Google API search and save the resulting data in the corresponding table
            user_coords, message, country_code_google = get_long_lat_values(user_location_tmp, country_code)
            debug_messages.append(message)
            
            if user_coords:
                user_coords = user_coords[1]
                try: 
                    Google_Map_Info.objects.create(
                    country_code = country_code,
                    keyword = user_location_tmp,
                    pos = user_coords,
                    created_on = datetime.now(),
                    updated_on = datetime.now(),
                    google_country_code = country_code_google
                    )
                except IntegrityError:
                    existing_entry = Google_Map_Info.objects.get(country_code=country_code, keyword=user_location_tmp, google_country_code = country_code_google)
                    existing_entry.updated_on = datetime.now()
                    existing_entry.save()
                    
        if not user_coords:
            return user_location, pd.DataFrame(), debug_messages, country_code_google
    
        if country_code == 'KR':
            if not service_center_flag:
                sql = """
                SELECT litd, lttd, plaza_no
                FROM rubicon_data_plaza_base
                WHERE show_yn = 'Y' 
                AND close_yn = 'N'
                """
            else:
                sql = """
                SELECT lng, lat, gname
                FROM rubicon_data_svc_center_mst
                """
        elif country_code == 'GB':
            if samsung_experience_store_flag:
                # For Samsung Experience Store, filter by storetypes = '1_ses'
                sql = """
                SELECT coordinates_longitude, coordinates_latitude, searchableid
                FROM rubicon_data_uk_store_plaza
                WHERE status = 'active'
                AND storetypes = '1_ses'
                """
            else:
                sql = """
                SELECT coordinates_longitude, coordinates_latitude, searchableid
                FROM rubicon_data_uk_store_plaza
                WHERE status = 'active'
                ORDER BY storetypes
                """
        else:
            raise ValueError(f"Unsupported country code: {country_code}")
        
        cursor.execute(sql)
        plaza_results = cursor.fetchall()
        
        if not plaza_results:
            plaza_df = pd.DataFrame()
        
        else:
            plaza_df = pd.DataFrame(plaza_results, columns = [c.name for c in cursor.description])
            plaza_df.columns = ['longitude','latitude','id']
            #  Calculate the distance based on the searched latitude and longitude using the latitude and longitude of all stores
            plaza_df['distance'] = plaza_df.apply(lambda row: geodesic(user_coords, (row['latitude'], row['longitude'])).kilometers, axis=1)
            plaza_df = plaza_df.sort_values('distance').reset_index(drop=True).iloc[:k]

    return user_location, plaza_df, debug_messages, country_code_google


"""
 A function that converts Korean (KR) store names to store IDs, used when store IDs cannot be directly obtained during the code mapping process.
""" 
def switch_to_store_id(df, target):
    sql_df = pd.DataFrame()
    with connection.cursor() as cursor:
        if target == 'store_name':
            sql = """
            SELECT plaza_no, plaza_nm
            FROM rubicon_data_plaza_base
            WHERE plaza_nm = %s
            AND show_yn = 'Y'
            """
        elif target == 'city':
            sql = """
            SELECT plaza_no, plaza_nm
            FROM rubicon_data_plaza_base
            WHERE city_cd = %s
            AND show_yn = 'Y'
            limit 3
            """
            
        elif target == 'district':
            sql = """
            SELECT plaza_no, plaza_nm
            FROM rubicon_data_plaza_base
            WHERE dtrt_cd = %s
            AND show_yn = 'Y'
            limit 3
            """
        cursor.execute(sql, [df['mapping_code'].iloc[0]])
        sql_results = cursor.fetchall()
        
        if sql_results:
            sql_df = pd.DataFrame(sql_results, columns = [c.name for c in cursor.description])
        
    return sql_df


"""
 A function that converts UK store names to store IDs, used when store IDs cannot be directly obtained during the code mapping process. 
""" 
def switch_to_store_id_GB(df, target):
    sql_df = pd.DataFrame()
    with connection.cursor() as cursor:
        if target == 'store_name':
            sql = """
            SELECT searchableid, name
            FROM rubicon_data_uk_store_plaza
            WHERE name = %s
            AND status = 'active'
            """
        elif target == 'city':
            sql = """
            SELECT searchableid, name
            FROM rubicon_data_uk_store_plaza
            WHERE locality = %s
            AND status = 'active'
            limit 3
            """
            
        cursor.execute(sql, [df['mapping_code'].iloc[0]])
        sql_results = cursor.fetchall()
        
        if sql_results:
            sql_df = pd.DataFrame(sql_results, columns = [c.name for c in cursor.description])
        
    return sql_df

"""
A function that handles service center mapping since service centers don't have separate ID columns
Service centers use gname (service center name) as both identifier and data
"""
def handle_service_center_mapping(df):
    """
    서비스센터는 별도 ID 컬럼이 없어 gname을 그대로 사용
    switch_to_store_id와 다른 로직으로 처리
    """
    service_center_names = df['mapping_code'].dropna().drop_duplicates().tolist()
    
    # Return in DataFrame format, using mapping_code as 'service_center_id'
    results = []
    for name in service_center_names:
        results.append({'service_center_id': name})
    
    return pd.DataFrame(results) if results else pd.DataFrame()

"""
Search for store names similar to 'Samsung Store' + 'expression' based on existing store names
""" 
def code_retriever_store_name(expression, country_code, message_id):
    # First try exact match
    store_exact_sql = """
        SELECT rcm.mapping_code, rcm.field, rcm.expression
        FROM rubicon_v3_structured_code_mapping rcm
        WHERE rcm.field = 'store_name'
        AND rcm.expression = %s
        AND rcm.country_code = %s
        AND rcm.active = TRUE
        AND rcm.structured = TRUE
        AND rcm.expression_to_code = TRUE;
    """
    
    store_similarity_sql = """
        SELECT 
            rcm.mapping_code,
            rcm.field,
            rcm.expression,
            1 - (rcm.expression_embedding <=> %s::vector) AS similarity_score
        FROM rubicon_v3_structured_code_mapping rcm
        WHERE rcm.field = 'store_name'
        AND rcm.country_code = %s
        AND rcm.active = TRUE
        AND rcm.structured = TRUE
        AND 1 - (rcm.expression_embedding <=> %s::vector) >= 0.9
        ORDER BY similarity_score DESC
        LIMIT 20;
        """

    with connection.cursor() as curs:
        df = pd.DataFrame()
        # Try exact match first
        curs.execute(store_exact_sql, [expression, country_code])
        results = curs.fetchall()
        
        # If exact match found, return it
        if results:
            return pd.DataFrame(results, columns=[c.name for c in curs.description])
        else:
            embedding = __embedding_rerank.baai_embedding(expression, message_id)[0]
            curs.execute(store_similarity_sql, [embedding, country_code, embedding])
            results = curs.fetchall()
            df = pd.DataFrame(results, columns=[c.name for c in curs.description])
        if not df.empty:
            df_reranked = __embedding_rerank.rerank_db_results(expression, df, text_column='expression', top_k=1)
            if df_reranked.empty:
                return pd.DataFrame()
            
            if df_reranked['reranker_score'].iloc[0] < 0:
                return df
            else:
                top_expression = df_reranked['expression'].iloc[0]
                final_df = df[df['expression'] == top_expression]
                return final_df
        else:
            return df
            

"""
If the Google API does not operate, perform code mapping through exact and similar match methods
"""            
def code_retriever_store(expression, embedding, field, country_code, message_id):
    # First try exact match
    exact_sql = """
        SELECT rcm.mapping_code, rcm.field, rcm.expression
        FROM rubicon_v3_structured_code_mapping rcm
        WHERE rcm.field IN %s
        AND rcm.expression = %s
        AND rcm.country_code = %s
        AND rcm.active = TRUE
        AND rcm.structured = TRUE
        AND rcm.expression_to_code = TRUE;
        """
    similarity_sql = """
        SELECT 
            rcm.mapping_code,
            rcm.field,
            rcm.expression,
            1 - (rcm.expression_embedding <=> %s::vector) AS similarity_score
        FROM rubicon_v3_structured_code_mapping rcm
        WHERE rcm.field IN %s
        AND rcm.country_code = %s
        AND rcm.active = TRUE
        AND rcm.structured = TRUE
        ORDER BY similarity_score DESC
        LIMIT 20;
        """

    with connection.cursor() as curs:
        curs.execute(exact_sql, [tuple(field), expression, country_code])
        results = curs.fetchall()
        if results:
            return pd.DataFrame(results, columns=[c.name for c in curs.description])
        
        curs.execute(similarity_sql, [embedding, tuple(field), country_code])
        results = curs.fetchall()
        df = pd.DataFrame(results, columns=[c.name for c in curs.description])
        if not df.empty:
            df_reranked = __embedding_rerank.rerank_db_results(expression, df, text_column='expression', top_k=1)
            if df_reranked.empty or df_reranked['reranker_score'].iloc[0] < 0:
                final_df = df[df['similarity_score']==df['similarity_score'].max()]
                return final_df
            else:
                top_expression = df_reranked['expression'].iloc[0]
                final_df = df[df['expression'] == top_expression]
                return final_df
        else:
            return pd.DataFrame()

"""
Perform NER code mapping
""" 
def code_mapping_store(item: List, country_code, message_id) -> List[Dict[str, str]]:
    results = []
    location_target = [
            result
            for result in item
            if result['field']=='location'
        ]
    
    service_center_flag = any(result['field']=='service_center_name' for result in item)
    
    # Samsung Experience Store detection
    samsung_experience_store_flag = False
    if country_code == "GB":
        for component in item:
            expression = component.get('expression', '').lower()
            if 'samsung experience store' in expression or 'experience store' in expression:
                samsung_experience_store_flag = True
                break
    
    debug_messages = []
    df = pd.DataFrame()        
    for component in location_target:
        #  Map the 3 nearest stores based on the latitude and longitude values from the Google API.
        user_location, plaza_df, debug_message, country_code_google = location_match(component, service_center_flag, country_code, samsung_experience_store_flag)
        debug_messages = debug_messages + debug_message
        
        if country_code_google is not None and country_code_google != country_code:
            return results, debug_messages, service_center_flag, samsung_experience_store_flag
        
        if plaza_df.empty:
            continue
        
        store_name = plaza_df['id'].tolist()
        if service_center_flag:
            field = 'service_center_id'
        else:
            field = 'store_id'
    
        results.append({
            'field':field,
            'mapping_code': store_name
        })
        
        # store + name search 
        if not service_center_flag and country_code == 'KR':
            expression = '삼성스토어 ' + component.get('expression',"")
            df = code_retriever_store_name(expression, country_code, message_id)
            if not df.empty:
                swithced_df = switch_to_store_id(df, "store_name")
                results.append({
                    'field': 'store_id',
                    'mapping_code': swithced_df['plaza_no'].dropna().drop_duplicates().tolist() if swithced_df is not None and not swithced_df.empty else None,
                })
        
        item = [comp for comp in item if not (comp.get('field') == 'location' and comp.get('expression') in user_location)]
        item = [comp for comp in item if not (comp.get('field') == field)]
        
    if len(results) < 1 or len(item) >= 2:
        for component in item:
            expression = component.get('expression','')
            field = component.get('field','')
            field = ['city','district'] if field == 'location' else [field]
            
            embedded_expression_value = __embedding_rerank.baai_embedding(expression, message_id)
            embedded_expression_value = embedded_expression_value[0]
            
            df = code_retriever_store(expression, embedded_expression_value, field, country_code, message_id)
            if not df.empty:
                if df['mapping_code'].iloc[0] != '*' and country_code == 'KR':
                    if service_center_flag:
                        # Use separate processing logic for service centers
                        service_center_df = handle_service_center_mapping(df)
                        results.append({
                            'field': 'service_center_id',  # Special field name for service centers
                            'mapping_code': service_center_df['service_center_id'].dropna().drop_duplicates().tolist() if not service_center_df.empty else None,
                        })
                    else:
                        switched_df = switch_to_store_id(df, df['field'].iloc[0])
                        # Add the original field mapping
                        results.append({
                            'field': 'store_id',
                            'mapping_code': switched_df['plaza_no'].dropna().drop_duplicates().tolist() if switched_df is not None and not switched_df.empty else None,
                        })
                elif df['mapping_code'].iloc[0] != '*' and country_code == 'GB':
                    switched_df = switch_to_store_id_GB(df, df['field'].iloc[0])
                    results.append({
                            'field': 'store_id',
                            'mapping_code': switched_df['searchableid'].dropna().drop_duplicates().tolist() if switched_df is not None and not switched_df.empty else None,
                        })
                else:
                    results.append({
                        'field': df['field'].iloc[0],
                        'mapping_code': df['mapping_code'].dropna().drop_duplicates().tolist() if df is not None and not df.empty else None,
                    })
            else:
                debug_messages.append(f"Store Invalid. Location: '{expression}' is in '{country_code_google}' which is outside of supported country '{country_code}'")
    
    return results, debug_messages, service_center_flag, samsung_experience_store_flag

"""
 Data retrieval through code mapping results
""" 
def get_data_store(plaza_ids, country_code, service_center_flag, samsung_experience_store_flag=False):
    store_data = []
    if country_code == "KR":
        if not service_center_flag:
            sql = """
            SELECT plaza_no, plaza_nm as store_name, road_addr as road_address, road_dtl_addr as full_road_address, tel as telephone, weekday_open_time, weekday_close_time, weekend_open_time, weekend_close_time, closed_day
            FROM rubicon_data_plaza_base
            WHERE show_yn = 'Y' 
            AND close_yn = 'N'
            AND plaza_no in %s
            """
        else:
            sql = """
            SELECT gname as service_center_name, rcode1, rcode2, doroname, address_doro, weekday_start as service_center_weekday_open_time, weekday_end as service_center_weekday_close_time, saturday_start as service_center_weekend_open_time, saturday_end as service_center_weekend_close_time, holiday_start as service_center_holiday_open_time, holiday_end as service_center_holiday_close_time
            FROM rubicon_data_svc_center_mst
            WHERE gname in %s
            """
    elif country_code == "GB":
        sql = """
            SELECT searchableid as plaza_no, name as store_name, address_street as road_address, locality as city, telephone, openinghours
            FROM rubicon_data_uk_store_plaza
            WHERE status = 'active'
            AND searchableid in %s
            """
            
    with connection.cursor() as curs:
        curs.execute(sql, [tuple(plaza_ids)])
        results = curs.fetchall()
        if results:
            store_df = pd.DataFrame(results, columns=[c.name for c in curs.description])
            order = {value:i for i, value in enumerate(plaza_ids)}
            
            if service_center_flag:
                # Sort by service_center_name for service centers
                store_df['order'] = store_df['service_center_name'].map(order).fillna(-1)
                store_df = store_df.sort_values(by='order').drop(['order'],axis=1)
            else:
                # Sort by plaza_no for general stores
                store_df['order'] = store_df['plaza_no'].map(order).fillna(-1)
                store_df = store_df.sort_values(by='order').drop(['order','plaza_no'],axis=1)
            
            store_data = store_df.to_dict('records')
        
    return store_data


def store(ner_value: List, country_code, message_id):
    debug_messages = []
    store_data = []
    target_results, debug_messages, service_center_flag, samsung_experience_store_flag = code_mapping_store(
        ner_value,
        country_code,
        message_id)
    
    target_results = [item if item.get('mapping_code') else {**item, 'mapping_code': ['*']} for item in target_results]
    if all(item.get("mapping_code") for item in target_results):
        # Collect service center and general store IDs separately
        if service_center_flag:
            plaza_ids = [code for d in target_results for code in d['mapping_code'] if d['field']=='service_center_id']
        else:
            plaza_ids = [code for d in target_results for code in d['mapping_code'] if d['field']=='store_id']
            
        if all(code=='*' for code in plaza_ids):
            debug_messages.append('Unlimited Data') #  If all mapping codes are '*', there is no data to filter, so the process cannot proceed
        else:
            plaza_ids_tmp = [item for item in plaza_ids if item != '*']
            store_data = get_data_store(plaza_ids_tmp, country_code, service_center_flag, samsung_experience_store_flag) # Query the desired data based on the store ID.
        

    return store_data, debug_messages, target_results

if __name__ == "__main__":
    flattened_results = store([
        # {
        #     "field":"location",
        #     "expression": "liverpool"
        # },
        {
            "field":"location",
            "expression": "*",
            "operator":"in"
        },
          {
              "field": "store",
              "expression": "삼성스토어",
              "operator":"in"
          }
        ],"KR","test")
    
    print(flattened_results)

