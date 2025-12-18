from sqlalchemy import create_engine, Column, Integer, String, text, Table, MetaData, update, select, func, and_, distinct, UniqueConstraint, TIMESTAMP
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

import json
import os, sys

sys.path.append("/www/alpha/")
from apps.rubicon_v3.__external_api.__apiRequest import apiHandler

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "alpha.settings")
from alpha.settings import POSTGRESQL_DB, POSTGRESQL_ID, POSTGRESQL_IP, POSTGRESQL_PORT, POSTGRESQL_PWD
from urllib.parse import quote_plus

import datetime

class CIS_Category:                      

    def __init__(self):
        db_pwd = quote_plus(POSTGRESQL_PWD)
        self.DATABASE_URL = f"postgresql+psycopg2://{POSTGRESQL_ID}:{db_pwd}@{POSTGRESQL_IP}:{POSTGRESQL_PORT}/{POSTGRESQL_DB}"
        self.TABLE_NM_CIS_TREE = "rubicon_data_cis_tree_temp"
        self.SCHEMA_NAME = "tmp"

        self.apiRequester = apiHandler("KR")
        self.opType = self.apiRequester.opType
        self.engine = create_engine(self.DATABASE_URL)
        self.connection = self.engine.connect()
        Session = sessionmaker(bind=self.engine)
        self.session = Session()
        self.metadata = MetaData()
        self.base = declarative_base()
        self.update_time = datetime.datetime.now() 

    def upsert_product(self, data_list):
        done = True
        msg = ""
        try:
            table = Table(self.TABLE_NM_CIS_TREE, self.metadata, autoload_with=self.engine, schema=self.SCHEMA_NAME)
            db_columns = {col.name for col in table.columns}
            for insert_data in data_list:
                # 키를 소문자로 변환 후 빈 문자열은 None으로 처리
                lower_data = {
                    (k.lower()): v
                    for k, v in insert_data.items()
                }
                lower_data = {k: (None if v == "" else v) for k, v in lower_data.items()}
                lower_data['update_time'] = self.update_time
                # 실제 테이블에 존재하는 컬럼만 필터링 (추후 컬럼 삭제 시에도 안전)
                filtered_data = {k: v for k, v in lower_data.items() if k in db_columns}
                # Upsert 쿼리 생성
                stmt = insert(table).values(**filtered_data)
                self.session.execute(stmt)
            self.session.commit()
            msg = "Update Proceeded Successfully"
        except Exception as e:
            self.session.rollback()
            #print("Error in upsert_product:", e)
            done = False
            msg = f"Update Failed: {e}"
        finally:
            self.session.close()
            return done, msg

if __name__ == "__main__":
    json_data = {"dataList": [
    {
      "MODEL_CODE": "SANGHO",
      "PLANT": "SANG",
      "DIVISION": "Q",
      "PRODUCT_GROUP_CODE": "GH",
      "PRODUCT_ABBR_CODE": "GSM",
      "PROJECT_CODE": "RDR0112FE",
      "MODEL_GROUP_CODE": "MSM-N900",
      "DEV_PROJECT_CODE": "RDR0112FE-08CS",
      "SEGMENT": "H ALL GSM DX",
      "DEV_MODEL_CODE": "SM-N900_SEA_DX",
      "FORECAST_MODEL_CODE": "BSM-N900/M32",
      "BASIC_MODEL": "BSM-N900/M32",
      "MATERIAL_TYPE": "HAWA",
      "UPDATE_PERSON": "26123",
      "COMPANY": "C540",
      "MODEL_NAME": "SM-N900",
      "PRODUCT_GROUP_DESC": "HHP",
      "PRODUCT_ABBR_DESC": "GSM HHP FOR EC",
      "PRODUCT_CODE": "EBG3A",
      "PRODUCT_NAME": "GSM 3.xG MAIN",
      "PROJECT_NAME": "H ALL GSM",
      "DEV_MODEL_ID": "001XN0BWCtPMWL1000"
    }]}  
    
    tree = CIS_Category()
    tree.upsert_product(json_data)