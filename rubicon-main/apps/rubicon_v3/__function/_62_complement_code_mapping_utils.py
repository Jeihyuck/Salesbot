import re
import ast
import pandas as pd
import networkx as nx
import numpy as np
import time

from copy import deepcopy
from functools import reduce
from alpha import __log
from django.db import connection

from apps.rubicon_v3.__function import __embedding_rerank as embedding_rerank

class NetworkUnitConverter:
    def __init__(self):
        self.conversion_graph = nx.DiGraph()
        
        self.unit_groups = {
            "length": {"base_unit": "M", "units": ["MM", "CM", "M", "INCH", "INCHES", "FT", "\u0022"]},
            "volume": {"base_unit": "L", "units": ["ML", "L", "GALLON", "ℓ"]},
            "data": {"base_unit": "MB", "units": ["MB", "GB", "TB"]},
            "area": {"base_unit": "㎡", "units": ["㎡", "평", "M²", "평형"]},
            "weight": {"base_unit": "KG", "units": ["G", "KG", "T", "LB", "LBS", "OZ"]},
            "power": {"base_unit": "W", "units": ["W", "KW"]},
            "charge": {"base_unit": "MAH", "units": ["MAH", "AH"]},
            "induction": {"base_unit": "구", "units": ["구", "EA"]},
            "intensity": {"base_unit": "DB", "units": ["DB"]},
            "pcount": {"base_unit": "인용", "units": ["인용", "인"]},
            "time": {"base_unit": "분", "units": ["분", "MIN", "시간", "H", "HOUR", "HOURS", "일"]},
            "frequency": {"base_unit": "HZ", "units": ["HZ"]}
        }

        # 길이 단위 설정 (M 기준)
        self.add_base_conversion("length", "MM", 0.001)
        self.add_base_conversion("length", "CM", 0.01)
        self.add_base_conversion("length", "INCH", 0.0254)
        self.add_base_conversion("length", "INCHES", 0.0254)
        self.add_base_conversion("length", "\u0022", 0.0254)
        self.add_base_conversion("length", "FT", 0.3048)
        
        # 부피 단위 설정 (L 기준)
        self.add_base_conversion("volume", "ℓ", 1)
        self.add_base_conversion("volume", "ML", 0.001)
        self.add_base_conversion("volume", "GALLON", 3.78541)
        
        # 데이터 크기 단위 설정 (MB 기준)
        self.add_base_conversion("data", "GB", 1024)
        self.add_base_conversion("data", "TB", 1024 * 1024)
        
        # 면적 단위 설정 (㎡ 기준)
        self.add_base_conversion("area", "평", 3.3058)  # 1평 = 3.3058㎡
        self.add_base_conversion("area", "평형", 3.3058)  # 1평 = 3.3058㎡
        self.add_base_conversion("area", "M²", 1)  # 1평 = 3.3058㎡
        
        # 무게 단위 설정 (KG 기준)
        self.add_base_conversion("weight", "G", 0.001)  # 1G = 0.001KG
        self.add_base_conversion("weight", "T", 1000)   # 1T = 1000KG
        self.add_base_conversion("weight", "LB", 0.45359237)  # 1LB = 0.45359237KG
        self.add_base_conversion("weight", "LBS", 0.45359237)  # 1LB = 0.45359237KG
        self.add_base_conversion("weight", "OZ", 0.028349523125)  # 1OZ = 0.028349523125KG
        
        # 전력 단위 설정 (W 기준)
        self.add_base_conversion("power", "KW", 1000)  # 1KW = 1000W
        
        # 전하량 단위 설정 (MAH 기준)
        self.add_base_conversion("charge", "AH", 1000) 

        # 인덕션 화구 단위 설정 (구 기준)
        self.add_base_conversion("induction", "EA", 1)

        # 인용 단위 설정 (인용 기준)
        self.add_base_conversion("pcount", "인", 1)
        
        # 시간 단위 설정 (초 기준)
        self.add_base_conversion("time", "MIN", 1)
        self.add_base_conversion("time", "시간", 60)
        self.add_base_conversion("time", "H", 60)
        self.add_base_conversion("time", "HOUR", 60)
        self.add_base_conversion("time", "HOURS", 60)
        self.add_base_conversion("time", "일", 1440)
    
    def add_base_conversion(self, group, unit, factor_to_base):
        """
        기준 단위와의 관계를 정의하고 모든 필요한 변환 관계를 자동으로 생성
        
        Parameters:
        group (str): 단위 그룹 (예: "length", "volume")
        unit (str): 추가할 단위
        factor_to_base (float): 이 단위에서 기준 단위로 변환하는 계수
        """
        if group not in self.unit_groups:
            raise ValueError(f"Unknown unit group: {group}")
            
        base_unit = self.unit_groups[group]["base_unit"]
        
        if unit not in self.unit_groups[group]["units"]:
            self.unit_groups[group]["units"].append(unit)
        
        self.conversion_graph.add_edge(unit, base_unit, factor=factor_to_base)
        self.conversion_graph.add_edge(base_unit, unit, factor=1.0/factor_to_base)
        
    def add_custom_conversion(self, from_unit, to_unit, factor):
        """직접적인 단위 변환 관계 추가 (필요한 경우)"""
        self.conversion_graph.add_edge(from_unit, to_unit, factor=factor)
    
    def get_conversion_factor(self, from_unit, to_unit):
        """두 단위 간의 변환 계수 계산"""
        if from_unit == to_unit:
            return 1.0
            
        if self.conversion_graph.has_edge(from_unit, to_unit):
            return self.conversion_graph[from_unit][to_unit]["factor"]
        
        try:
            path = nx.shortest_path(self.conversion_graph, from_unit, to_unit)
            if not path:
                return None
                
            factor = 1.0
            for i in range(len(path) - 1):
                factor *= self.conversion_graph[path[i]][path[i+1]]["factor"]
            return factor
            
        except (nx.NetworkXNoPath, nx.NodeNotFound):
            return None
    
    def get_related_units(self, unit):
        """주어진 단위와 같은 그룹에 속한 단위들 반환"""
        for group_name, group_info in self.unit_groups.items():
            if unit.upper() in group_info["units"]:
                return group_info["units"]
        return []
        
    def convert(self, value, from_unit, to_unit):
        """값 변환"""
        factor = self.get_conversion_factor(from_unit, to_unit)
        if factor is not None:
            return value * factor
        return None
        
    def add_new_unit(self, group, unit, factor_to_base):
        """
        새로운 단위를 추가하는 간편한 메소드
        
        Parameters:
        group (str): 단위 그룹 (예: "length", "volume")
        unit (str): 추가할 단위
        factor_to_base (float): 이 단위에서 기준 단위로 변환하는 계수
        """
        self.add_base_conversion(group, unit, factor_to_base)
    
    def create_new_unit_group(self, group_name, base_unit, base_unit_factor=1.0):
        """
        새로운 단위 그룹 생성
        
        Parameters:
        group_name (str): 새 그룹 이름 (예: "weight")
        base_unit (str): 기준 단위 (예: "kg")
        base_unit_factor (float): 기준 단위의 변환 계수 (일반적으로 1.0)
        """
        if group_name in self.unit_groups:
            raise ValueError(f"Unit group already exists: {group_name}")
            
        self.unit_groups[group_name] = {"base_unit": base_unit, "units": [base_unit]}
        
        self.conversion_graph.add_edge(base_unit, base_unit, factor=1.0)
        
    def expand_dataframe(self, df):
        """
        데이터프레임의 단위를 변환하여 새로운 행 추가
        """
        # 모든 행을 저장할 리스트
        all_rows = []
        
        for _, row in df.iterrows():
            # 원본 행 추가
            all_rows.append(row.to_dict())
            
            value = row['extracted_number']
            unit = row['extracted_unit'].upper()
            
            # 관련 단위 찾기
            related_units = self.get_related_units(unit)
            
            # 관련 단위가 있으면 변환
            for target_unit in related_units:
                if target_unit != unit:  # 원래 단위와 다른 경우만
                    converted_value = self.convert(value, unit, target_unit)
                    if converted_value is not None:
                        # 새 행 생성
                        new_row = row.to_dict()  # 모든 컬럼 값 복사
                        new_row['extracted_number'] = converted_value
                        new_row['extracted_unit'] = target_unit
                        all_rows.append(new_row)
        
        # 마지막에 한 번만 데이터프레임 생성
        result_df = pd.DataFrame(all_rows)
        return result_df

# HC1
# embedding, rerank 과정에서 약어가 다른 스펙명으로 매핑되는 경우에 올바른 스펙명으로 매핑

# HC2
# 갤럭시 워치 제품군의 경우, 일반적으로 베젤을 포함한 크기로 인식하나 spec table에는 베젤을 제외한 크기로 입력되어 있으므로 베젤 포함한 사이즈로 매핑

# HC3
# 어떤 매핑이 라인업인지 구분하기 위해서 생성(답변정책)

# HC4
# embedding과 rerank는 단편적으로 입력된 색상에 대한 구분을 하지 못하며 삼성 제품들에는 굉장히 다양한 색상명이 존재
# 같은 군의 색상명에 대해서 매핑하는 list의 list 생성
# 예: 빨간색 핸드폰 -> 코랄레드 핸드폰

# HC5
# 가장 큰/작은/etc 에 대응 하기 위해서 보편적으로 가장이라는 수식어에 알맞는 스펙을 매핑
# 예: 가장 큰 핸드폰 -> 크기 (Main Display)가 가장 큰 핸드폰

# HC6
# 동일 제품군에 제품별로 스펙명이 상이한 경우가 존재하여, 해당 제품군들 내 올바른 비교를 위하여 여러 스펙명을 매핑

# HC7
# 일부 스펙의 value가 온전하지 못하므로 보정

# HC8
# 특정 스펙을 질의에 명시하지 않았으나 보편적으로 어떤 스펙을 요구하는지에 대한 매핑

# HC9
# 동제품종 간 다른 라인업을 비교할 때 동일한 대표적인 특징을 가진 제품을 비교하기 위한 매핑
# 예: Neo QLED TV와 Crystal UHD TV 비교에서 동일한 화면크기의 제품을 비교

# HC10
# spec table에서 value가 있음/없음 등으로 표현되어 있을 때, 긍정에 대한 표현이 과도하게 다양하기 때문에 부정에 대한 표현을 정리하고 부정이 아닌 값을 긍정으로 처리

# HC1
MANAGE_SPEC_NAME = {
    'Internet Usage Time(Wi-Fi) (Hours)': 'Video Playback Time (Hours)',
    'Freezing Capacity': 'Gross Total(Litre)',
    '화면비율': '화면사이즈 (cm)'
}

# HC2
WATCH_SIZE_REPLACE = {
    'Galaxy Watch5': [('30.4', '40'), ('34.6', '44')],
    'Galaxy Watch5 Pro': [('34.6', '45')],
    'Galaxy Watch6': [('33.3', '40'), ('37.3', '44')],
    'Galaxy Watch6 Classic': [('33.3', '43'), ('37.3', '47')],
    'Galaxy Watch7': [('33.3', '40'), ('37.3', '44')],
    'Galaxy Watch8': [('34', '40'), ('37.3', '44')],
    'Galaxy Watch8 Classic': [('34', '46')],
    'Galaxy Watch Ultra': [('37.3', '47')]
}
# HC2
WATCH_GB_REPLACE = {
    'Watch4': [('30.4', '40')],
    'Watch5 Pro': [('34.6', '45')],
    'Watch6': [('33.3', '40'), ('37.3', '44')],
    'Watch6 Classic': [('33.3', '43'), ('37.3', '47')],
    'Watch7': [('33.3', '40'), ('37.3', '44')],
    'Watch FE': [('30.4', '40')],
    'Watch Ultra': [('37.3', '47')]
}

# HC3
LINEUP_LIST = ['Bespoke', 'BESPOKE AI', 'Infinite AI', 'Infinite Line', '그랑데', '그랑데 AI', '비스포크 그랑데', '인피니트', 
               '갤럭시', '비스포크 큐브', '청소기', '큐커', 'SSD', 'TV', 'USB', '가습기', '갤럭시 북', '갤럭시 워치', '갤럭시 탭', 
               '갤럭시 핏', '건조기', '공기 청정기', '김치냉장고', '내장 SSD', '냉동고', '냉장고', '노트북', '다리미', '데스크탑', 
               '로봇청소기', '레이저 빔', '리시버', '마사지기', '마이크', '마이크로SD', '메모리카드', '모니터', '무선 청소기', '복합기', 
               '갤럭시 버즈', '비데', '사운드바', '사운드타워', '서큘레이터', '선풍기', '세탁기', '슈드레서', '스피커', '식기세척기', 
               '에어드레서', '에어컨', '에어프라이어', '오디오', '오븐', '와인 냉장고', '외장 SSD', '외장하드', '워치', '웨어러블', 
               '이어폰', '인덕션', '전기 밥솥', '전기 주전자', '전자레인지', '정수기', '제습기', '조리기기', '조명', '주방 가전', 
               '컴퓨터', '태블릿', '포터블 스크린', '프로젝터', '프린터', '핸드폰', '헤드셋', '헤드폰', '환풍기', '후드', 'BESPOKE 키친핏', 
               'AI 건조기', 'AI 김치플러스', 'AI 무풍콤보 에어컨', 'AI 세탁기', 'AI 청소기', 'B & C 시리즈 사운드바', 'Bespoke AI 건조기', 
               'Bespoke AI 김치플러스', 'BESPOKE AI 냉동고', 'BESPOKE AI 냉장고', 'BESPOKE AI 무풍 갤러리', 'BESPOKE AI 무풍 클래식', 
               'Bespoke AI 무풍콤보', 'BESPOKE AI 무풍콤보 갤러리', 'BESPOKE AI 스팀', 'Bespoke AI 에어드레서', 'Bespoke AI 원바디', 
               'BESPOKE AI 제트', 'BESPOKE AI 콤보', 'Bespoke AI 패밀리허브', 'BESPOKE AI 하이브리드', 'Bespoke AI 후드', 'BESPOKE 그랑데 건조기 AI', 
               'BESPOKE 그랑데 AI 원바디', 'Bespoke 김치플러스', 'BESPOKE 냉장고', 'BESPOKE 드럼 세탁기 AI', 'BESPOKE 로봇 청소기', 'BESPOKE 무풍 갤러리', 
               'BESPOKE 무풍 클래식', 'BESPOKE 슈드레서', 'BESPOKE 스팀', 'BESPOKE 슬림', 'BESPOKE 식기세척기', 'BESPOKE 에어컨', 'BESPOKE 오븐', 'BESPOKE 인덕션', 
               'BESPOKE 전자레인지', 'BESPOKE 정수기', 'BESPOKE 제트', 'BESPOKE 청소기', 'BESPOKE 큐브 Air', 'BESPOKE 큐커', 'BESPOKE 큐커 오븐', 'BESPOKE 키친핏 김치냉장고', 
               'BESPOKE 키친핏 냉장고', 'BESPOKE 패밀리허브', 'BESPOKE 후드 Air', 'Crystal UHD TV', 'FHD TV', 'HD TV', 'Infinite AI 공기청정기', 'Infinite AI 무풍 시스템에어컨', 
               'Infinite Line 무풍 시스템에어컨', 'Infinite Line 식기세척기', 'Infinite Line 인덕션', 'Infinite Line 김치냉장고', 'Infinite Line 와인냉장고', 'Infinite Line 오븐', 
               'Infinite Line 냉장고', 'LCD 모니터', 'LED 조명', 'LED TV', 'Micro LED', 'Neo QLED', 'Neo QLED 4K TV', 'Neo QLED 8K TV', 'OLED TV', 'Q 시리즈 사운드바', 'QHD 모니터', 
               'QLED', 'QLED 4K TV', 'QLED 8K', 'S 시리즈 사운드바', 'The Frame', 'The Frame Pro', 'The Premiere', 'The Serif', 'The Sero', 'The Terrace', 'UHD', '갤럭시 S 시리즈', 
               '갤럭시 Z 시리즈', '갤럭시 Z 폴드', '갤럭시 Z 플립', '갤럭시 링', '갤럭시 버즈', '갤럭시 북 360', '갤럭시 북 Edge', '갤럭시 북 Pro', '갤럭시 북 프로 360', '갤럭시 북 울트라', 
               '갤럭시 북4 시리즈', '갤럭시 북5 시리즈', '갤럭시 탭 A', '갤럭시 탭 S', '갤럭시 폰 A', '게이밍 모니터', '고해상도 모니터', '그랑데 건조기', '그랑데 세탁기', '그랑데 세탁기 AI', 
               '김치플러스 뚜껑형', '김치플러스 스탠드형', '더 프리스타일', '데스크탑 Slim', '데스크탑 Tower', '드럼 세탁기', '무빙스타일', '무빙스타일 Crystal UHD', '무빙스타일 OLED', 
               '무빙스타일 QLED', '무풍 벽걸이 에어컨', '무풍 시스템에어컨', '무풍 에어컨', '벽걸이 에어컨', '뷰피니티', '블루스카이 공기청정기', '블루스카이', '비스포크 AI 무풍콤보', 
               '비스포크 AI 세탁기', '비스포크 건조기', '비스포크 공기청정기', '비스포크 그랑데 AI 세탁기', '비스포크 그랑데 건조기', '비스포크 그랑데 세탁기', '비스포크 김치냉장고', 
               '비스포크 냉장고', '비스포크 세탁기', '비스포크 에어드레서', '상업용 무풍 시스템에어컨', '상업용 스탠딩 에어컨', '상업용 에어컨', '셰프컬렉션 냉장고', '슈퍼 슬림 사운드바', 
               '스마트 모니터', '스탠드 에어컨', '시스템 에어컨', '싱글 에어컨', '에센셜 모니터', '올인원 PC', '정수기 냉장고', '제트', '중대형 에어컨', '진공청소기', '창문형 에어컨', 
               '커브드 모니터', '큐브 냉장고', '큐커 멀티', '큐커 멀티/오븐', '통버블 세탁기', '파워모션',
               'Galaxy Book 360', 'Galaxy Book Edge', 'Galaxy Book Go', 'Galaxy Book Pro', 'Galaxy Book Ultra', 'Galaxy Watch Pro', 'Galaxy Watch Ultra', 
               'High Resolution Monitor', 'Neo QLED 4K TV', 'Neo QLED 8K TV', 'QLED 4K TV', 'BESPOKE AI', 'Bespoke AI All-in-One', 'BESPOKE Jet', 
               'Bespoke Jet AI', 'BESPOKE Jet Bot', 'Bespoke Jet Bot AI', 'Chromebook', 'CombiHob', 'Microwave Combi', 'Galaxy', 'Jet', 'Jet AI', 'Jet Bot', 
               'Jet Bot AI', 'Jet Plus', 'Jet Ultra', 'Galaxy Z Flip', 'Galaxy Z Fold', 'DQHD Monitor', 'FHD Monitor', 'Mini LED Monitor', 'OLED Monitor', 'QHD Monitor', 
               'UHD Monitor', 'UWQHD Monitor', 'WQHD Monitor', 'BESPOKE AI Fridge Freezer', 'BESPOKE AI Refrigerator', 'Bespoke AI Tumble Dryer', 'BESPOKE AI Washers', 
               'BESPOKE Fridge Freezer', 'BESPOKE Refrigerator', 'BESPOKE Vacuum Cleaner', 'BESPOKE Washing Machines', 'Active Tablets', 'AI Fridge Freezer', 'AirDresser', 
               'AI Refrigerator', 'AI TV', 'AI Washer Dryers', 'AI Washers', 'American-Style Fridge Freezer', 'American-Style Refrigerator', 'Audio', 'Bar-Type Smartphone', 'Blu-Ray Player', 
               'Bottom Mount Freezer', 'Business Monitor', 'Canister VC', 'Compact Oven', 'Compact Soundbar', 'Computer', 'Cooker Hood', 'Cooking Appliances', 'Cook Oven', 'Cordless Vacuum Cleaner', 
               'Crystal UHD TV', 'Curved Monitor', 'Dishwasher', 'Dryer', 'DVD Player', 'Earbuds', 'Earphones', 'Essential Monitor', 'Flat Monitor', 'Foldable Phone', 'Freezer', 'French-Style Fridge Freezer', 
               'French-Style Refrigerator', 'Fridge Freezer', 'Front-Load Washer Dryer', 'Front-load Washing Machines', 'Full HD TV', 'Galaxy A Series', 'Galaxy Book', 'Galaxy Buds', 'Galaxy Fit', 'Galaxy Ring', 
               'Galaxy S Series', 'Galaxy Tab', 'Galaxy Tab Active', 'Galaxy Tab A Series', 'Galaxy Tab S Series', 'Galaxy Watch', 'Galaxy Z Series', 'Gaming Monitor', 'Handheld Stick', 'Hob', 'Integrated Freezer', 
               'Integrated Fridge', 'Integrated Fridge Freezer', 'Internal SSD', 'Laptop', 'MicroSD Card', 'Microwave Oven', 'Monitor', 'Music Frame', 'Neo QLED TV', 'Odyssey Monitor', 'OLED TV', 'Outdoor TV', 
               'Oven', 'PC', 'Projector', 'QLED TV', 'Refrigerator', 'Robot Vacuum Cleaner', 'Samsung Jet', 'Soundbar', 'Sound System', 'Sound Tower', 'Speaker', 'Heating System', 'SSD', 'Stick Vacuum Cleaner', 
               'Storage', 'Stretched Display', 'Tablet', 'The Frame', 'The Freestyle', 'The Premiere', 'The Serif', 'The Sero', 'The Terrace', 'The Wall', 'TV', 'UHD TV', 'Ultra', 'Upright VC', 'USB Flash Drive', 
               'Vacuum Cleaners', 'Video Player', 'Video Wall', 'ViewFinity Monitor', 'Warming Drawer', 'Washer', 'Washer Dryer Combo', 'watch', 'Wearable']

# HC4
COLOR_MAP_KR = [
        ['레드', '로즈', '와인', '버건디', '다크 레드', '브릭레드', '코랄레드', '코랄 레드', '오로라 레드', '퓨어 버건디', '메탈릭 레드', 'Pure Burgundy', '빨간색'],
        ['피치', '핑크', '핑크골드', '라이트 핑크', '미스틱 핑크', '글램핑크', '글램 핑크', '새틴 핑크', '로즈 골드', '메탈릭 로즈골드', '알루 로즈골드', '티타늄 핑크골드', 
         '스탠드 에센셜 샴페인', '에센셜 샴페인', '미스티 핑크 미러', '핑크 화이트', '핑크 골드', '선셋 핑크', 'Alu Rose Gold', 'Sunset Pink', 'SUNSET PINK', '미스틱 브론즈', '마젠타', '스카이코랄','분홍색'],
        ['코랄', '딥 이브닝 코랄', '브론즈', '탠', '탄', '월넛', '카멜', '토프', '에토프', '브라운', '캔버스 우드', '트러플 브라운', '이브닝 코랄', '글램 딥이브닝코랄', '브라운 메탈', '트러플 메탈', 
         '트러플 메탈(골드)', 'TRUFFLE METAL', '헤링본', '테라코타(전면패널, 스트라이프)', '테라코타(전면패널, 헤링본)', '쉐브론 라이트', '쉐브론 다크', '티크', '다크타프', '어스 브라운', '카퍼', '갈색'],
        ['오렌지', '탠저린', '샌드스톤 오렌지', '티타늄 오렌지', '주황색'],
        ['살구', '옐로우', '머스터드', '티타늄 옐로우', '쉐브론 썬옐로우', '앰버 옐로우', '엠버 옐로우', '글램 썬옐로우', '글램 썬 옐로우', '코타 썬 옐로우', '썬 옐로우', '노란색'],
        ['그린', '라임', '민트', '다크그린', '다크 그린', '라이트 그린', '미스틱 그린', '세이지', '세이지 그린', '제이드 그린', '티타늄 그린', '쉐브론 그리너리', '티타늄 제이드그린', 
         '메탈릭 세이지 그린', '제습기 세이지 그린', '새틴 그린', '어썸 라임', '우디 그린', '글램 딥그린', '새틴 그리너리', '코타 그리너리', '새틴 세이지그린', '글램 그리너리 ', 
         '새틴 세이지 그린', '새틴 펀 그린', '코타 펀 그린', '그리너리', '딥그린', '딥그린(전면패널, 스트라이프)', '딥그린(전면패널, 헤링본)', '제주 그리너리', '스프링 그린', 
         '올리브', '초록색', 'Spring Green', 'SPRING GREEN', '카키', '블루 그린', '글램 그리너리', '연두색'],
        ['블루', '#0000ff', 'Blue', '네이비', '인디고', '사파이어 블루', '미스틱 블루', '블루핑크', '인디고 블루', '티타늄 블루', '다크 블루', '새틴 마린', '글램 네이비', '블루 쉐도우',
         '어썸 네이비', '혼드 네이비', '어스 블루', '블루코럴', '바이탈리티 블루', '미드나잇 블루', '마레 블루', '데이라이트 블루', '네이비블루', '다크 네이비', 'NAVY BLUE', '데님 블루',
         'Glam Navy (우측 상단), 그 외 AP (Panel Ready)', 'Vitality Blue', 'Mare Blue (카퍼 엣지 프레임)', 'Earth Blue', 'Daylight Blue', 'DAYLIGHT BLUE', 'COTTON BLUE', '파란색'],
        ['블루', '사이안', '사파이어', '새틴스카이블루', '라이트 블루', '스카이 블루', '아이스 블루', '아이스블루', '티타늄 아이스블루', '아이스  블루', '모닝 블루', '글램 딥모닝블루', 
         '어썸 아이스블루', '새틴 스카이 블루', '블루 화이트', '티타늄 실버블루', '블루 그린', '코랄블루', '블루 (바디 색상)', '하늘색'],
        ['퍼플', '라벤더', '바이올렛', '블루베리', '세린 퍼플', '다크 바이올렛', '라벤더그레이', '메탈릭 라벤더', '코발트 바이올렛', '티타늄 바이올렛', '글램 라벤더', '어썸 라벤더', 
         '어썸 라일락', '어썸 바이올렛', '보라 퍼플', 'MERLOT PURPLE', '자주색', '보라색'],
        ['새틴 그레이지', '그레이지', '그레이지 (Greige)', 'Timeless Greige', '크림', '화이트', '크림 화이트', '프로스트 화이트', '샴페인', '샴페인 ', '화이트 샌드', '티타늄 화이트', 
         '블루 화이트', '핑크 화이트', '내추럴화이트', '내추럴 화이트', '미스티 화이트', '에센셜 화이트', '에센셜 화이트 ', '스탠드 에센셜 화이트', '스탠드 에센셜 화이트 ', '글램화이트', '글램 화이트', 
         '새틴 화이트', '세라 화이트', '어썸 화이트', '코타화이트', '코타 화이트', '클린화이트', '클린 화이트', '팬텀 화이트', '코타 화이트 ', '매트 멜로우 화이트', '메탈 화이트(바람문 White)', 
         ' 화이트', 'Natural White', 'DA White', 'White', 'WHITE', 'Warm White', 'WARM WHITE', '플랫화이트', '화이트 (글래스)', '코타PCM 화이트(메탈)', '코타PCM 화이트', '코타 화이트(메탈)', 
         '코타 화이트 (Cotta White)', '코타 화이트 (Cotta Metal)', '코타 PCM 화이트', '웜화이트', '웜 화이트', '오프 화이트', '오프화이트', '에어본(화이트)', '에어본 쿠퍼(화이트)', '알루 화이트', 
         '스노우 화이트(메탈)', '스노우 화이트', '새틴 화이트(글래스)', '새틴 화이트 (Satin Glass)', '새틴 화이트  (Satin Glass)', '미스틱 화이트', '메탈 화이트(바람문 Blue)', 
         '메탈 화이트', '매트 멜로우 화이트 (Mellow White Metal)', '글램 화이트 (글래스)', '글램 화이트 (Glam Glass)', 'SPACE WHITE', 'Glam White (우측 상단), 그 외 AP (Panel Ready)', 
         'DA WHITE', 'Cotta White', 'CLOUD WHITE', 'Alu White', '클래식 화이트', '백색 무광', '백색 반광', '페블 화이트', '화이트 (바디 색상)', '흰색'],
        ['샌드', '베이지', '산토리니 베이지', '메탈릭 베이지', '에센셜 베이지', '제습기 산토리니 베이지', '스탠드 에센셜 베이지', '스탠드 에센셜 사틴베이지', '글램 바닐라', '글램베이지', '글램 베이지', 
         '새틴 베이지', '코타 베이지', '혼드 베이지', '새틴 아이보리', '새틴 라이트베이지', '매트 크리미 베이지', '새틴 라이트 베이지', '샴페인 베이지', '베이지(전면패널, 스트라이프)', '사틴 베이지',
         '베이지(전면패널, 헤링본)', '샌드골드', '샌드 골드', '베이지 (글래스)', '멜로우 베이지', '매트 크리미 베이지(Creamy Metal)', '에센셜 베이지(메탈)', '아이보리', 'Essential Beige'],
        ['실버', '건메탈', '그라파이트', '플래티넘 실버', '라이트 실버', '미스틱 실버', '티타늄 실버', '메탈', '실버스틸', '리얼스테인리스 메탈', '크리스탈 미러', '티타늄 실버블루', 
         '티타늄 화이트실버', '새틴 실버', '세린 실버', '어썸 실버', '파인 실버', '혼드 실버', '실버 쉐도우', '실버(글로시)', '에센셜 다크메탈', '에센셜 다크 메탈', '리파인드 이녹스(메탈)', 
         '내츄럴(메탈)', 'Refined Inox(메탈)', 'Refined Inox(리얼메탈)', '스테인리스 아트 스틸', 'Real Stainless(STS)', ' 파인 실버', '다크스틸', '다크 메탈', '럭스 메탈', '이녹스', 
         '리파인드 이녹스', '엘레강트 이녹스', '미스티 마린 미러', '젠틀실버(메탈)', '젠틀실버', '젠틀 실버(메탈)', '젠틀 실버', '샴페인 실버', '브라우니 실버', 'Silver', 'SILVER', 
         'Metal Silver', 'Mercury silver', 'MERCURY SILVER', 'Eclipse Silver', 'ECLIPSE SILVER', 'CARBON SILVER', 'Bronish Silver (Metal)', 'BRIGHT SILVER', '리파인드 이녹스 (Metal)', 
         '리얼 스테인리스', 'Muted Metal', '다크실버스틸', '은색', '내츄럴', 'RGB CARBON SILVER', '루미 웜 실버', '실버(스텐)', '회색'],
        ['타임리스 그레이지', '그레이', '그레이핑크', '라이트 그레이', '어썸 라이트그레이', '문스톤 그레이', '미스틱 그레이', '티타늄 그레이', '다크 그레이', '차콜', '딥차콜', '사틴 차콜', '풀그레이', '베르사유그레이', 
         '다크그레이 (디스플레이 색상)', '타임리스 차콜', '옥스포드 그레이', '크리스탈 그레이', '바람문 그레이', '스모키 그레이', '제습기 그레이', '캔버스 그레이', '스탠드 에센셜 그레이', 
         '바이브 다크 그레이', '그레이(전면패널, 스트라이프)', '그레이(전면패널, 헤링본)', '글램 차콜', '새틴 차콜', '쉬머 차콜', '코타 차콜', '글램 그레이', '마블 그레이', '새틴 그레이', 
         '시크 그레이', '페블 그레이', '어썸 그라파이트', '코타 차콜 ', '다크 블루 그레이', '에센셜 블루 그레이', ' 에센셜 블루 그레이', 'Essential Blue Gray', 'Dark Blue Gray', '솝스톤 차콜', '사틴 그레이지',
         '타이탄 그레이', '빅토리 그레이', '바이브 다크 그레이(메탈)', '다크그레이', '뉴트럴 그레이', '네츄럴 그레이', '내추럴 그레이', '그레이 티타늄', '글램 딥 차콜', '스노우 포레스트', 
         'Warm Gray', 'TITAN GRAY', 'Neutral Gray', 'Muted Dark Gray', 'Dark Gray', '에어본 그레이', '차콜그레이', '차콜 그레이', '스모키 그레이(Smoky Grey)', '펄그레이', '회색'],
        ['블랙', '앱솔루트 블랙', '매트 블랙', '블루 블랙', '블루블랙', '제트블랙', '블랙캐비어', '크래프티드 블랙', '미스틱 블랙', '오닉스 블랙', '티타늄 블랙', '티타늄 제트블랙', '새틴 블랙', 
         '세라 블랙', '어썸 블랙', '젠틀 블랙', '팬텀 블랙', '퓨어 블랙', '블랙 쉐도우', '블랙 캐비어', '블랙 케비어', '피아노블랙', '타이탄 블랙', '코타 블랙', '젠틀블랙(메탈)', '젠틀블랙', 
         '젠틀 블랙(메탈)', '오프 블랙', '알루 블랙', '블랙네온', '블랙 티타늄', '블랙 크로메탈', 'TITAN BLACK', 'SLATE BLACK', 'GRAPHITE BLACK', 'CHARCOAL BLACK', 'BLACK(HAIR LINE)', 
         'Black', 'BLACK', 'Alu Black', '오닉스', '다크 티탄', '다크 타이탄', '블랙오렌지', '블랙 오렌지', 'Blue Black', '오로라 블랙', '피아노 블랙', '블랙 무광', '블랙 반광', '흑색 무광', '검정색', '검은색'],
        ['골드', '클래식 골드', '골드 메탈', '금색', '티타늄 골드', '샴페인 골드', '샴페인 골드(Champagne Gold)', '골드 카퍼'],
        ['투명'],
        ['패널 레디', '패널 선택형'] 
    ]
# HC4
COLOR_MAP_UK = [
    ['Awesome Black', 'Awesome Graphite', 'BESPOKE - Black Metal','BESPOKE - Clean Black','black','Black','BLACK','Black Doi','Black DOI','BLACK DOI','Black Glass','Black Silver','Black Stainless','Black Stainless finish','Blacktitanium','Black Titanium','Clean Black','CLEAN BLACK','Clean Black2','Clean Black(Clean Glass)','Crafted Black','Frost Black','Gentle Black Matt','Graphite Black','Jetblack','Matt Black Stainless','Mystic Black','New Empire Black','Onyx Black','Phantom Black','Prism Black','Stainless Steel with Black Glass','Titan Black','Titanium Black','Titanium Jetblack', 'Black Chrometal', 'BLACK CHROMETAL', 'Black high Glossy+Etching', 'block onyx', 'Block Onyx', 'Charcoal Black', 'Cotta Black'],
    ['Awesome Lightgrey','Graphite','gray','Gray','Graytitanium','Gray White','Grey','Grey ','Grey Titanium','Light Gray','Light Grey','Marble Grey','Moonstone Grey','Mystic Gray','Oxford Grey','Pebble Grey','Phantom Grey','Satin Grey','Slate Grey','Titan Grey','titanium gray','Titanium Gray','Titanium Grey','Bespoke Charcoal','Charcoal','Dark Grey','Dark Steel','Titan', 'CLEAN Deep charcoal', 'Space Gray', 'Titan Gray'],
    ['Refined Inox','REFINED INOX','Aluminium', 'Clean Steel','Crystal Mirror','Ez Clean Steel',' Matte Stainless','Matte Stainless','Metal Graphite','Mirror','MIRROR','Real Stainless','REAL STAINLESS','Refined Inox (Matt DOI Metal)','Refined Inox(Matt DOI Metal)','SILVERMIRROR','Stainless Steel','Stainless Steel finish','Titanium Silver', 'SILVER', 'silver', 'Silver', 'Awesome Silver','BESPOKE - Silver Metal', 'Gentle Silver Matt', 'MATT DOI METAL', 'Mercury silver','MERCURY SILVER', 'Mystic silver', 'Mystic Silver', 'Platinumsilver', 'Platinum Silver', 'Silver Shadow', 'Light Silver', 'Platinum', 'Stainless', 'Stardust'],
    ['Angola Blue','Angora Blue','Arctic Blue','Awesome Iceblue','Blue White','Cloud Blue','Cotta Sky Blue','Cotta Skyblue(Metal)','Cotton Blue','Dodger Blue','Earth blue','Icyblue','Ice Blue','Icy Blue','Light Blue','Satin Sky Blue','Satin Skyblue(Satin Glass)','Sky Blue','Titanium Blue','Titanium Icyblue','Titanium Silverblue', 'Dark Blue Gray', 'Sapphire'],
    ['Awesome Navy','Blue','Blueblack','Blue Black','Blue Grey','Blue Shadow','Brandeis Blue','Clean Navy','Dark Blue','DARK BLUE GRAY','Duke Blue','Glam Navy','Glam Navy (Glam Glass)','Glam Navy(Glam Glass)','Indigo Blue','Midnight','Mystic Navy','Navy','Navy blue','Navy Blue','Neptune Blue','Sapphire Blue','Vitality Blue', 'Mystic Blue'],
    ['Awesome Lavender','Awesome Lilac','Awesome Violet','Blueberry','Cobalt Violet','Cotta Lavender','Cotta Lavender(Metal)','Dark Violet','Fresh Lavender','Lavender','Mauve','Titanium Violet','Violet', 'Bora Purple', 'Indigo', 'Purple', 'Serenepurple'],
    ['Awesome Lime','Awesome Olive','Black and Green','Forest Green','Glam Greenery','Green','Jade Green','Light Green','Lime','Mint','Mystic Green','Olive','Olive Green','Sage Green','Titanium Green','Titanium Jadegreen', 'Spring Green', 'Sage'],
    ['Apricot','Awesome Peach','Clean Peach','Desert','Orange','Peach','Sandstone Orange','Tangerine','Titanium Orange'],
    ['Amber Yellow','Awesome Lemon','Butter Yellow','Clean Vanilla','Titanium Yellow','Vivid Lemon','Yellow', 'Mustard', 'Cream'],
    ['Gold', 'Titanium Gold'],
    ['Awesome Pink','Blossom Pink','Indian Pink','Mystic Pink','Neutral Pink','Pink','Pinkgold','Pink Gold','Pink White','DESSERT TABLE','Titanium Pinkgold'],
    ['Airborne (White)','Awesome White','BESPOKE - Clean White','Clean White','Clean White2','Clean White(Clean Glass)','Clean White(Glass)','Cloudwhite','Cloud White','Common white','Cotta White','Cotta White(Metal)','Essential White','Gray White','Ivory White','Snow White','Titanium White','Titanium Whitesilver','Warm White','white','White','White Sand', 'Misty White', 'Satin Greige', 'WARM WHITE', 'WHITE'],
    ['Beige','Beige Wood','BESPOKE - Satin Beige','Clay Beige','Cotta Beige','Cotta Beige(Metal)','Coyote Beige','Sand','Sand Gold','Santorini Beige','Satin Beige','Satin Beige (Satin Glass)','Satin Beige(Satin Glass)','Teak'],
    ['Brown','Camel','Phantom Brown', 'Tan'],
    ['Burgundy','Copper','Coralred','Dark Red','Glow Red','Lipstick','LIPSTICKS','Metallic Red','Red','RED','Rose','ROSES','Vitality Red', 'Wine'],
    ['Etoupe','Taupe'],
    ['Transparent']
]

def adjust_code_in_model(original_ner_result, unstructured_ner_result):
    original_code = [d.get('expression') for d in original_ner_result if d.get('field') == 'product_code']
    original_model = [d.get('expression') for d in original_ner_result if d.get('field') == 'product_model']
    standardized_code = [d.get('expression') for d in unstructured_ner_result if d.get('field') == 'product_code']
    standardized_model = [d.get('expression') for d in unstructured_ner_result if d.get('field') == 'product_model']
    remove_original = []
    remove_standardized = []
    for s1, s2 in zip(original_model, standardized_model):
        if any([c in s1 for c in original_code]):
            remove_original.append(s1)
        if any([c in s2 for c in standardized_code]):
            remove_standardized.append(s2)
    adjusted_original_ner_result = [d for d in original_ner_result if d.get('expression') not in remove_original]
    adjusted_unstructured_ner_result = [d for d in unstructured_ner_result if d.get('expression') not in remove_standardized]
    # __log.debug(adjusted_original_ner_result)
    # __log.debug(adjusted_unstructured_ner_result)

    return adjusted_original_ner_result, adjusted_unstructured_ner_result






def sort_ner_by_position(rquery, original_ner, new_ner):
    """
    원본 쿼리에서 원본 NER의 표현이 등장하는 순서대로 
    original_ner과 new_ner을 함께 정렬하는 함수
    
    Args:
        rquery (str): rewrite query
        original_ner (list): original ner
        new_ner (list): standardized ner
    
    Returns:
        tuple: (정렬된 original_ner, 정렬된 new_ner)
    """
    if len(original_ner) != len(new_ner):
        raise ValueError("original_ner과 new_ner의 길이가 일치해야 합니다.")

    # 쿼리에서 모든 표현식의 등장 위치 찾기
    all_expressions = {}  # expr -> [위치1, 위치2, ...]
    
    # 먼저 표현식을 길이 기준으로 내림차순 정렬 (긴 것부터 처리)
    sorted_items = sorted(original_ner, key=lambda x: len(x['expression']), reverse=True)
    
    # 각 표현식의 모든 등장 위치와 범위 찾기
    expression_ranges = []  # [(시작위치, 끝위치, 표현식), ...]
    
    for item in sorted_items:
        expr = item['expression']
        if expr not in all_expressions:
            all_expressions[expr] = []
            
            # 이 표현식의 모든 등장 위치 찾기
            start_pos = 0
            while True:
                pos = rquery.find(expr, start_pos)
                if pos == -1:
                    break
                end_pos = pos + len(expr) - 1
                all_expressions[expr].append(pos)
                expression_ranges.append((pos, end_pos, expr))
                start_pos = pos + 1

    
    # 긴 표현식이 차지하는 범위 내부에 있는 짧은 표현식의 위치 필터링
    filtered_positions = {}
    
    for expr, positions in all_expressions.items():
        filtered_positions[expr] = []
        
        for pos in positions:
            # 이 위치가 긴 표현식 내부에 있는지 확인
            is_inside_longer = False
            end_pos = pos + len(expr) - 1
            
            for start, end, longer_expr in expression_ranges:
                # 자기 자신과는 비교하지 않음
                if longer_expr == expr and start == pos:
                    continue
                
                # 이 위치가 긴 표현식 내부에 완전히 포함되는지 확인
                if start <= pos and end_pos <= end:
                    is_inside_longer = True
                    break
            
            # 긴 표현식 내부에 있지 않은 경우에만 추가
            if not is_inside_longer:
                filtered_positions[expr].append(pos)
    
    # print(f"filtered_positions: {filtered_positions}")
    
    # 사용한 위치 추적
    used_positions = set()
    
    # 각 NER 항목에 위치 할당
    ner_with_positions = []
    
    for i, (orig, new_item) in enumerate(zip(original_ner, new_ner)):
        expr = orig['expression']
        
        # 이 표현식의 필터링된 위치
        positions = filtered_positions.get(expr, [])
        
        # 아직 사용하지 않은 가장 앞선 위치 찾기
        best_pos = float('inf')
        for pos in positions:
            if pos not in used_positions:
                best_pos = pos
                used_positions.add(pos)
                break
        
        # 위치를 찾지 못했다면 무한대로 설정
        if best_pos == float('inf'):
            # 이미 모든 위치가 사용됐다면, 가장 마지막 위치 다음으로 설정
            if positions:
                best_pos = max(positions) + 1000 + i  # 순서 보존을 위해 인덱스 추가
            else:
                # 필터링된 위치가 없는 경우, 원래 위치 중 사용되지 않은 것 사용
                orig_positions = all_expressions.get(expr, [])
                for pos in orig_positions:
                    if pos not in used_positions:
                        best_pos = pos
                        used_positions.add(pos)
                        break
                
                # 여전히 위치를 찾지 못했다면
                if best_pos == float('inf') and orig_positions:
                    best_pos = max(orig_positions) + 1000 + i
                elif best_pos == float('inf'):
                    best_pos = 10000 + i  # 임의의 큰 값
        
        ner_with_positions.append((best_pos, i, (orig, new_item)))
    
    # 위치 기준 정렬
    ner_with_positions.sort(key=lambda x: (x[0], x[1]))
    
    # 정렬된 NER 목록 생성
    sorted_original = []
    sorted_new = []
    
    for _, _, (orig, new_item) in ner_with_positions:
        sorted_original.append(orig)
        sorted_new.append(new_item)
    
    return sorted_original, sorted_new

def split_ner_by_conjunction(rquery, original_ner, new_ner, conjunction_list=['와', '과', '랑', '의', 'and', 'or']):
    """
    원본 쿼리와 NER 정보를 사용하여 접속사 또는 모델 기준으로 NER 항목을 분리하는 함수
    
    Args:
        rquery: 원본 쿼리 문자열
        original_ner: 원본 NER 리스트 (쿼리에 등장하는 그대로의 표현)
        new_ner: 표준화된 NER 리스트
        conjunction_list: 접속사 목록
        
    Returns:
        모델별로 분리된 NER 그룹 리스트
    """
    # 각 entity의 위치 정보 찾기
    entity_positions = []
    search_start = 0
    
    for i, entity in enumerate(original_ner):
        expression = entity['expression']
        field = entity['field']
        
        start_idx = rquery.find(expression, search_start)
        
        if start_idx != -1:
            entity_positions.append({
                'index': i,
                'expression': expression,
                'field': field,
                'start': start_idx,
                'end': start_idx + len(expression)
            })
            search_start = start_idx + len(expression)
    
    # 위치 순서대로 정렬
    entity_positions.sort(key=lambda x: x['start'])
    
    # 모델 필드에 해당하는 entity만 필터링
    model_fields = ['product_model', 'product_code']
    product_models = [item for item in entity_positions if item['field'] in model_fields]
    
    # 모델이 하나만 있으면 분리할 필요 없음
    if len(product_models) <= 1:
        return [new_ner]
    
    # 모델 사이에 접속사가 있는지 확인
    has_conjunction = False
    
    for i in range(len(product_models) - 1):
        current_model = product_models[i]
        next_model = product_models[i+1]
        
        between_text = rquery[current_model['end']:next_model['start']]
        
        for conj in conjunction_list:
            if conj in between_text:
                has_conjunction = True
                break
        
        if has_conjunction:
            break
    
    # 접속사가 있으면 일반적인 접속사 기반 분리 로직 사용
    if has_conjunction:
        return split_with_conjunction(rquery, original_ner, new_ner, entity_positions, product_models, conjunction_list)
    
    # 접속사가 없으면 각 모델을 기준으로 분리
    return split_by_models(rquery, original_ner, new_ner, entity_positions, product_models)

def split_with_conjunction(rquery, original_ner, new_ner, entity_positions, product_models, conjunction_list):
    """
    접속사를 기준으로 NER 항목을 분리하는 함수
    """
    # 모델 사이의 접속사 찾기
    conjunctions = []
    
    for i in range(len(product_models) - 1):
        current_model = product_models[i]
        next_model = product_models[i+1]
        
        between_text = rquery[current_model['end']:next_model['start']]
        
        for conj in conjunction_list:
            conj_idx = between_text.find(conj)
            if conj_idx != -1:
                conjunctions.append({
                    'model_indices': (i, i+1),
                    'conjunction': conj,
                    'start': current_model['end'] + conj_idx,
                    'end': current_model['end'] + conj_idx + len(conj)
                })
    
    # 모델 직후의 접속사 찾기
    for i, model in enumerate(product_models):
        model_end = model['end']
        
        after_text = rquery[model_end:model_end + 5]  # 최대 5글자까지 확인
        
        for conj in conjunction_list:
            if after_text.startswith(conj):
                conjunctions.append({
                    'model_index': i,
                    'conjunction': conj,
                    'start': model_end,
                    'end': model_end + len(conj)
                })
    
    if not conjunctions:
        return [new_ner]
    
    # 접속사를 위치 순서대로 정렬
    conjunctions.sort(key=lambda x: x['start'])
    
    # 접속사 사이에 있는 모든 모델을 개별 그룹으로 분리
    connected_models = set()
    
    for conj in conjunctions:
        if 'model_indices' in conj:
            # 모델 사이 접속사인 경우
            connected_models.add(conj['model_indices'][0])  # 앞 모델 추가
            connected_models.add(conj['model_indices'][1])  # 뒤 모델 추가
        elif 'model_index' in conj:
            # 모델 직후 접속사인 경우
            connected_models.add(conj['model_index'])
            if conj['model_index'] < len(product_models) - 1:
                connected_models.add(conj['model_index'] + 1)
    
    # 접속사로 연결된 모든 모델을 개별 그룹으로 처리
    if connected_models:
        split_models = list(range(len(product_models)))
    else:
        # 접속사가 없는 경우 기본 로직 (첫 번째 모델만 포함)
        split_models = [0]
    
    # 중복 제거 및 정렬
    split_models = sorted(set(split_models))
    
    # 분리 지점에 따라 그룹 생성
    return create_groups_from_splits(rquery, original_ner, new_ner, entity_positions, product_models, split_models, conjunctions)

def split_by_models(rquery, original_ner, new_ner, entity_positions, product_models):
    """
    접속사가 없을 때 모델을 기준으로 NER 항목을 분리하는 함수
    """
    # 첫 번째 모델 앞에 스펙이 있는지 확인
    first_model = product_models[0]
    first_model_start = first_model['start']
    
    has_spec_before_first_model = False
    for pos in entity_positions:
        if pos['end'] <= first_model_start and pos['field'] not in ['product_model', 'product_code']:
            has_spec_before_first_model = True
            break
    
    # 결과 그룹 초기화
    groups = [[] for _ in range(len(product_models))]
    
    # 각 모델을 해당 그룹에 추가
    for i, model in enumerate(product_models):
        groups[i].append(new_ner[model['index']])
    
    # 모델 앞에 스펙이 있는 경우 (스펙-모델 패턴)
    if has_spec_before_first_model:
        # 스펙-모델 / 스펙-모델 패턴으로 처리
        for pos in entity_positions:
            if pos['field'] in ['product_model', 'product_code']:
                continue  # 모델은 이미 처리됨
                
            # 각 모델의 앞에 있는 스펙 찾기
            for i, model in enumerate(product_models):
                model_start = model['start']
                
                # 이전 모델의 끝 위치 (없으면 0)
                prev_end = 0
                if i > 0:
                    prev_end = product_models[i-1]['end']
                
                # 이전 모델 이후, 현재 모델 이전의 스펙
                if pos['start'] >= prev_end and pos['end'] <= model_start:
                    groups[i].append(new_ner[pos['index']])
                    break
        
        # 마지막 모델 이후의 항목들 처리
        last_model_end = product_models[-1]['end']
        for pos in entity_positions:
            if pos['field'] in ['product_model', 'product_code']:
                continue
                
            if pos['start'] >= last_model_end:
                groups[-1].append(new_ner[pos['index']])
    else:
        # 모델-스펙 / 모델-스펙 패턴으로 처리
        for pos in entity_positions:
            if pos['field'] in ['product_model', 'product_code']:
                continue  # 모델은 이미 처리됨
                
            # 각 모델의 뒤에 있는 스펙 찾기
            for i, model in enumerate(product_models):
                model_end = model['end']
                
                # 다음 모델의 시작 위치 (없으면 쿼리 끝)
                next_start = len(rquery)
                if i < len(product_models) - 1:
                    next_start = product_models[i+1]['start']
                
                # 현재 모델 이후, 다음 모델 이전의 스펙
                if pos['start'] >= model_end and pos['start'] < next_start:
                    groups[i].append(new_ner[pos['index']])
                    break
    
    return groups

def create_groups_from_splits(rquery, original_ner, new_ner, entity_positions, product_models, split_models, conjunctions=None):
    """
    분리 지점에 따라 NER 항목을 그룹화하는 함수
    """
    # 첫 번째 모델 앞에 스펙이 있는지 확인
    first_model = product_models[0]
    first_model_start = first_model['start']
    
    has_spec_before_first_model = False
    for pos in entity_positions:
        if pos['end'] <= first_model_start and pos['field'] not in ['product_model', 'product_code']:
            has_spec_before_first_model = True
            break
    
    # 그룹 초기화
    groups = [[] for _ in range(len(split_models))]
    
    # 각 모델을 해당 그룹에 추가
    for i, model_idx in enumerate(split_models):
        model = product_models[model_idx]
        groups[i].append(new_ner[model['index']])
    
    # 접속사 정보가 있는 경우 접속사 기준으로 스펙 할당
    if conjunctions:
        # 접속사 위치를 기준으로 스펙 할당
        for pos in entity_positions:
            if pos['field'] in ['product_model', 'product_code']:
                continue  # 모델은 이미 처리됨
            
            # 첫 번째 접속사를 기준으로 앞/뒤 판단
            first_conj = conjunctions[0]
            conj_start = first_conj['start']
            
            # 스펙이 접속사 앞에 있는지 뒤에 있는지 확인
            if pos['start'] < conj_start:
                # 접속사 앞 - 첫 번째 그룹에 할당
                groups[0].append(new_ner[pos['index']])
            else:
                # 접속사 뒤 - 해당하는 그룹 찾기
                # 스펙이 어느 모델과 가장 가까운지 확인
                for i in range(1, len(split_models)):
                    model_idx = split_models[i]
                    model = product_models[model_idx]
                    
                    # 다음 그룹이 있는지 확인
                    if i < len(split_models) - 1:
                        next_model_idx = split_models[i + 1]
                        next_model = product_models[next_model_idx]
                        # 현재 모델과 다음 모델 사이에 있는 스펙
                        if pos['start'] < next_model['start']:
                            groups[i].append(new_ner[pos['index']])
                            break
                    else:
                        # 마지막 그룹
                        groups[i].append(new_ner[pos['index']])
                        break
    
    # 접속사 정보가 없는 경우 기존 로직 사용
    else:
        # 모델 앞에 스펙이 있는 경우 (스펙-모델 패턴)
        if has_spec_before_first_model:
            # 스펙-모델 패턴으로 처리
            for pos in entity_positions:
                if pos['field'] in ['product_model', 'product_code']:
                    continue  # 모델은 이미 처리됨
                    
                # 각 분할 지점의 모델 앞에 있는 스펙 찾기
                for i, model_idx in enumerate(split_models):
                    model = product_models[model_idx]
                    model_start = model['start']
                    
                    # 이전 분할 지점의 끝 위치 (없으면 0)
                    prev_end = 0
                    if i > 0:
                        prev_model_idx = split_models[i-1]
                        prev_end = product_models[prev_model_idx]['end']
                    
                    # 이전 모델 이후, 현재 모델 이전의 스펙
                    if pos['start'] >= prev_end and pos['end'] <= model_start:
                        groups[i].append(new_ner[pos['index']])
                        break
        else:
            # 모델-스펙 패턴으로 처리
            for i, model_idx in enumerate(split_models):
                model = product_models[model_idx]
                model_end = model['end']
                
                # 다음 분할 지점 또는 쿼리 끝까지
                next_start = len(rquery)
                if i < len(split_models) - 1:
                    next_model_idx = split_models[i+1]
                    next_start = product_models[next_model_idx]['start']
                
                # 현재 모델 이후, 다음 모델 이전의 스펙 찾기
                for pos in entity_positions:
                    if pos['field'] in ['product_model', 'product_code']:
                        continue
                        
                    if pos['start'] >= model_end and pos['start'] < next_start:
                        groups[i].append(new_ner[pos['index']])
    
    return groups

def augment_query_and_ner(top_query, original_ner_result, unstructured_ner_result, grouped_ner_list, assistant_result):
    """
    rewtire query와 NER 결과를 증강하는 함수
    
    Parameters:
    - top_query: rewrite query
    - original_ner_result: NER 
    - unstructured_ner_result: 표준화된 NER 
    - grouped_ner_list: 그룹화된 NER
    - assistant_result: assistant 결과(필요한 list[dict{}] 만)
    
    Returns:
    - augmented_top_query: 증강된 rewrite 쿼리
    - augmented_original_ner_result: 증강된 NER
    - augmented_unstructured_ner_result: 증강된 표준화 NER
    - augmented_grouped_ner_list: 증강된 그룹화된 NER
    """
    # 원본 그룹 정보 저장
    original_grouped = deepcopy(grouped_ner_list)
    
    # 1. grouped_ner_list 증강
    # 모델 타입의 expression 찾기
    expressions = [d.get('expression') for d in unstructured_ner_result if d.get('field') == 'product_model']
    
    # 각 expression의 등장 횟수 계산
    expression_counts = {}
    for expr in expressions:
        if expr in expression_counts:
            expression_counts[expr] += 1
        else:
            expression_counts[expr] = 1
    
    # expression별 현재 처리 인덱스 추적
    expression_current_idx = {expr: 0 for expr in expression_counts.keys()}
    
    augmented_grouped_list = []
    
    # 원본 항목을 대체할 그룹들 기록
    original_groups_to_replace = set()
    
    # 그룹별로 처리
    for group_idx, group in enumerate(original_grouped):
        # 그룹에서 product_model 항목 찾기
        model_items = [item for item in group if item['field'] == 'product_model']
        if not model_items:
            augmented_grouped_list.append(deepcopy(group))  # 모델 항목이 없는 그룹은 그대로 유지
            continue
        
        model_item = model_items[0]
        model_expression = model_item['expression']
        
        # 해당 모델의 현재 인덱스 가져오기
        current_idx = expression_current_idx[model_expression]
        
        # 해당 모델과 인덱스에 맞는 assistant 결과 찾기
        matching_assistant_items = [
            item for item in assistant_result 
            if item['expressions'] == model_expression
        ]
        
        if current_idx < len(matching_assistant_items) and matching_assistant_items[current_idx]['assistant']:
            assistant_prod = matching_assistant_items[current_idx]['assistant']
            
            # 인덱스 업데이트
            expression_current_idx[model_expression] += 1
            
            # 이 그룹을 대체 대상으로 표시
            original_groups_to_replace.add(group_idx)
            
            # 그룹 증강
            for sa in assistant_prod:
                nlist_temp = deepcopy(group)
                nlist_temp = [{**d, 'expression': sa if d['expression'] == model_expression else d['expression']} 
                             for d in nlist_temp]
                augmented_grouped_list.append(nlist_temp)
        else:
            # 매칭되는 assistant 항목이 없는 경우, 그룹 그대로 유지
            augmented_grouped_list.append(deepcopy(group))
    
    # 2. top_query 증강 - 단순하고 명확한 접근법
    augmented_top_query = top_query
    
    # 표준화된 표현식 -> 원본 표현식 매핑
    unstr_to_orig = {}
    for i in range(min(len(original_ner_result), len(unstructured_ner_result))):
        unstr_to_orig[unstructured_ner_result[i]['expression']] = original_ner_result[i]['expression']
    
    # 모델 별 그룹 매칭
    model_to_groups = {}
    for i, group in enumerate(original_grouped):
        model_items = [item for item in group if item['field'] == 'product_model']
        if not model_items:
            continue
            
        model_expr = model_items[0]['expression']
        if model_expr not in model_to_groups:
            model_to_groups[model_expr] = []
        model_to_groups[model_expr].append((i, group))
    
    # 모델 별 assistant 결과 매핑
    model_to_assistants = {}
    for asst in assistant_result:
        model_expr = asst['expressions']
        if model_expr not in model_to_assistants:
            model_to_assistants[model_expr] = []
        model_to_assistants[model_expr].append(asst['assistant'])
    
    # 처리 정보 추적
    replacements = []  # (시작위치, 끝위치, 원본세그먼트, 교체할세그먼트)
    
    # 모델 별로 처리
    for model_expr, groups in model_to_groups.items():
        # 모델의 원본 표현식
        orig_model_expr = unstr_to_orig.get(model_expr, model_expr)
        
        # assistant 결과 가져오기
        if model_expr not in model_to_assistants:
            continue
            
        assistants = model_to_assistants[model_expr]
        
        # 각 모델 그룹을 순서대로 처리
        for i, (group_idx, group) in enumerate(groups):
            if i >= len(assistants):
                continue
                
            asst_values = assistants[i]
            
            # 이 그룹에 포함된 모든 원본 표현식 찾기
            group_orig_exprs = []
            for item in group:
                expr = item['expression']
                orig_expr = unstr_to_orig.get(expr, expr)
                group_orig_exprs.append(orig_expr)
            
            # 이 그룹의 모든 표현식이 등장하는 위치 찾기
            expr_positions = []
            for expr in group_orig_exprs:
                # 원본 쿼리에서 해당 표현식의 모든 등장 위치 찾기
                start_pos = 0
                while True:
                    pos = augmented_top_query.find(expr, start_pos)
                    if pos == -1:
                        break
                    expr_positions.append((pos, pos + len(expr), expr))
                    start_pos = pos + 1
            
            if not expr_positions:
                continue
                
            # 위치 기준 정렬
            expr_positions.sort(key=lambda x: x[0])
            
            # 이 그룹의 표현식들이 가까이 있는 경우 찾기
            candidate_segments = []
            
            # 모든 가능한 시작-끝 조합 검사
            for start_idx in range(len(expr_positions)):
                for end_idx in range(start_idx + 1, len(expr_positions) + 1):
                    if end_idx - start_idx < len(group_orig_exprs):
                        continue  # 모든 표현식을 포함하지 않음
                        
                    segment_start = expr_positions[start_idx][0]
                    segment_end = expr_positions[end_idx - 1][1]
                    
                    # 세그먼트가 너무 길면 건너뛰기 (합리적인 범위 설정)
                    if segment_end - segment_start > 50:
                        continue
                        
                    # 세그먼트 추출
                    segment = augmented_top_query[segment_start:segment_end]
                    
                    # 이 세그먼트가 그룹의 모든 표현식을 포함하는지 확인
                    if all(expr in segment for expr in group_orig_exprs):
                        # 세그먼트 크기와 모든 표현식 포함 여부를 함께 저장
                        included_exprs = sum(1 for expr in group_orig_exprs if expr in segment)
                        segment_size = segment_end - segment_start
                        candidate_segments.append((segment_start, segment_end, segment, included_exprs, segment_size))
            
            # 모든 표현식을 포함하는 가장 짧은 세그먼트 선택
            if candidate_segments:
                # 포함된 표현식 수 내림차순, 세그먼트 크기 오름차순 정렬
                candidate_segments.sort(key=lambda x: (-x[3], x[4]))
                best_segment = candidate_segments[0]
                segment_start, segment_end, segment = best_segment[:3]
                
                # 이 세그먼트가 모델 표현식을 포함하는지 확인
                if orig_model_expr in segment:
                    # 증강된 세그먼트 생성
                    aug_segments = []
                    for asst_value in asst_values:
                        aug_segment = segment.replace(orig_model_expr, asst_value)
                        aug_segments.append(aug_segment)
                    
                    if aug_segments:
                        replacement = ", ".join(aug_segments)
                        replacements.append((segment_start, segment_end, segment, replacement))
    
    # 위치 기준 정렬 (앞에서부터 처리)
    replacements.sort(key=lambda x: x[0])
    
    # 교체 진행 (오프셋 고려)
    offset = 0
    for start_pos, end_pos, segment, replacement in replacements:
        # 현재 오프셋 적용
        adjusted_start = start_pos + offset
        adjusted_end = end_pos + offset
        
        # 교체 진행
        before = augmented_top_query[:adjusted_start]
        after = augmented_top_query[adjusted_end:]
        augmented_top_query = before + replacement + after
        
        # 오프셋 업데이트
        offset += len(replacement) - (adjusted_end - adjusted_start)
    
    # 3. original_ner_result와 unstructured_ner_result 증강 (기존 코드 유지)
    augmented_original_ner_result = []
    augmented_unstructured_ner_result = []
    
    # 모든 assistant 값 수집
    assistant_values = []
    for item in assistant_result:
        assistant_values.extend(item['assistant'])
    
    # 증강된 그룹의 모든 항목 추가
    for group in augmented_grouped_list:
        for item in group:
            expr = item['expression']
            field = item['field']
            
            # unstructured_ner에 추가
            augmented_unstructured_ner_result.append(item.copy())
            
            # original_ner에도 추가 (원본 표현식으로 변환 또는 assistant 값 그대로)
            if expr in unstr_to_orig:
                # 표준화된 표현식의 원본 값 사용
                orig_expr = unstr_to_orig[expr]
                augmented_original_ner_result.append({
                    'expression': orig_expr,
                    'field': field,
                    'operator': item['operator']
                })
            else:
                # assistant 값이면 그대로 사용
                augmented_original_ner_result.append(item.copy())
    
    # 그룹화되지 않은 항목 추가 (예: 추천)
    grouped_exprs = set()
    for group in original_grouped:
        for item in group:
            grouped_exprs.add((item['expression'], item['field']))
    
    for i in range(min(len(original_ner_result), len(unstructured_ner_result))):
        orig_item = original_ner_result[i]
        unstr_item = unstructured_ner_result[i]
        
        expr_pair = (unstr_item['expression'], unstr_item['field'])
        if expr_pair not in grouped_exprs:
            augmented_original_ner_result.append(orig_item.copy())
            augmented_unstructured_ner_result.append(unstr_item.copy())
    
    # 결과 정렬
    try:
        augmented_original_ner_result, augmented_unstructured_ner_result = sort_ner_by_position(
            augmented_top_query, augmented_original_ner_result, augmented_unstructured_ner_result
        )
    except ValueError as e:
        print(f"정렬 중 오류 발생: {e}")

    return augmented_top_query, augmented_original_ner_result, augmented_unstructured_ner_result, augmented_grouped_list

def check_valid_product(expression, results, country_code):
    check_result = ""
    expr_split = expression.lower().split(' ')
    num_in_expr = [num for s in expr_split for num in re.findall(r'\d+', s)]

    code_filter_str = None
    code_filter_int = None
    product_filter = []
    # negative_l4_product_filter insert 0611
    negative_product_filter = []


    model_category_lv1 = []
    model_category_lv2 = []
    model_category_lv3 = []
    
    if 'category_lv1' in results:
        model_category_lv1.extend(results['category_lv1'])
    
    if 'category_lv2' in results:
        model_category_lv2.extend(results['category_lv2'])
    
    if 'category_lv3' in results:
        model_category_lv3.extend(results['category_lv3'])

    model_category_lv1_placeholders = None
    model_category_lv2_placeholders = None
    model_category_lv3_placeholders = None

    if model_category_lv1:
        model_category_lv1_placeholders = ", ".join(
            "'" + _ + "'" for _ in model_category_lv1 if 'NA' != _
        )
    if model_category_lv2:
        model_category_lv2_placeholders = ", ".join(
            "'" + _ + "'" for _ in model_category_lv2 if 'NA' != _
        )
    if model_category_lv3:
        model_category_lv3_placeholders = ", ".join(
            "'" + _ + "'" for _ in model_category_lv3 if 'NA' != _
        )

    if ((model_category_lv1_placeholders or 'NA' in model_category_lv1)
        and (model_category_lv2_placeholders  or 'NA' in model_category_lv2)
        and (model_category_lv3_placeholders or 'NA' in model_category_lv3)
        ):
        # negative_l4_product_filter insert 0611
        l4_query = f"""
                        SELECT l4_identifier, l4_product_expression, code_filter, product_filter, type, condition FROM rubicon_v3_complement_code_mapping_l4
                        WHERE country_code = '{str(country_code)}'
                        AND active = TRUE
                    """
        if model_category_lv1_placeholders:
            l4_query += f"AND category_lv1 in ({model_category_lv1_placeholders})"
        if model_category_lv2_placeholders:
            l4_query += f"AND category_lv2 in ({model_category_lv2_placeholders})"
        if model_category_lv3_placeholders:
            l4_query += f"AND category_lv3 in ({model_category_lv3_placeholders})"

        with connection.cursor() as curs:
            curs.execute(l4_query)
            results = curs.fetchall()

            if results:
                df_l4 = pd.DataFrame(results, columns=[c.name for c in curs.description])
                code_filter_str = df_l4[(df_l4['code_filter']) & (df_l4['type'] == 'str') & (df_l4['condition'] == 'positive')]['l4_identifier'].str.lower().tolist()
                code_filter_int = df_l4[(df_l4['code_filter']) & (df_l4['type'] == 'int') & (df_l4['condition'] == 'positive')]['l4_identifier'].str.lower().tolist()
                # negative_l4_product_filter insert 0611
                product_filter_ner = df_l4[(df_l4['product_filter']) & (df_l4['condition'] == 'positive')]['l4_identifier'].str.lower().tolist()
                product_filter_goods_nm = df_l4[(df_l4['product_filter']) & (df_l4['condition'] == 'positive')]['l4_product_expression'].str.lower().tolist()
                neg_product_filter_ner = df_l4[(df_l4['product_filter']) & (df_l4['condition'] == 'negative')]['l4_identifier'].str.lower().tolist()
                neg_product_filter_goods_nm = df_l4[(df_l4['product_filter']) & (df_l4['condition'] == 'negative')]['l4_product_expression'].str.lower().tolist()

                if code_filter_str:
                    code_filter_str = list(set(code_filter_str))
                if code_filter_int:
                    code_filter_int = list(set(code_filter_int))
                
                code_check_str = any(set(code_filter_str) & set(expr_split))
                code_check_int = any(set(code_filter_int) & set(num_in_expr)) or not num_in_expr
                # product_check = any([s in expression.lower() for s in product_filter])

                # __log.debug('------------ product_filter_ner, product_filter_goods_nm ----------------------------------------')
                # __log.debug(product_filter_ner)
                # __log.debug(product_filter_goods_nm)

                expression_lower = expression.lower()

                for n, gn in zip(product_filter_ner, product_filter_goods_nm):
                    if n in expression_lower:
                        product_filter.append(gn)
                
                if product_filter:
                    product_filter = list(set(product_filter))

                # negative_l4_product_filter insert 0611
                for n, gn in zip(neg_product_filter_ner, neg_product_filter_goods_nm):
                    # negative_l4_product_filter 고도화 0614
                    if n[0] == '[':
                        list_ = ast.literal_eval(n)
                        if any(nn in expression_lower for nn in set(list_)):
                            continue
                        else:
                            negative_product_filter.append(gn)
                    elif n not in expression_lower:
                        negative_product_filter.append(gn)
                
                if negative_product_filter:
                    negative_product_filter = list(set(negative_product_filter))

                if code_filter_str or code_filter_int:
                    if not (code_check_str or code_check_int):
                        check_result += "code filter failed"
                
                # if product_filter and not product_check:
                #     check_result += "product filter failed;"
    # __log.debug('------------ expression ----------------------------------------')
    # __log.debug(expression)
    # __log.debug('------------ code_filter_str ----------------------------------------')
    # __log.debug(code_filter_str)
    # __log.debug('------------ code_filter_int ----------------------------------------')
    # __log.debug(code_filter_int)
    # __log.debug('------------ product_filter ----------------------------------------')
    # __log.debug(product_filter)
    # __log.debug('------------ negative_product_filter ----------------------------------------')
    # __log.debug(negative_product_filter)

    # negative_l4_product_filter insert 0611
    filters = {
        'expression': expression,  
        'code_filter_str': code_filter_str,
        'code_filter_int': code_filter_int,
        'product_filter': product_filter,
        'negative_product_filter': negative_product_filter
        }

    return check_result, filters

def adjust_arguments_set_product(original_ner_list, ner_list, grouped_ner_list, code_mapping_results_model):
    non_target_product = [d.get('expression') for d in code_mapping_results_model if d.get('category_lv1') == ['NA'] and d.get('category_lv2') == ['NA'] and d.get('category_lv3') == ['NA']]
    new_code_mapping_results_model= [d for d in code_mapping_results_model if d.get('expression') not in non_target_product]
    new_grouped_ner = [
        l for l in grouped_ner_list 
        if not any(d.get('expression') in non_target_product for d in l)
    ]
    new_original_ner = [
        d for d in original_ner_list 
        if d.get('expression') in [d.get('expression') for l in new_grouped_ner for d in l]
    ]
    new_ner_list = [
        d for d in ner_list 
        if d.get('expression') in [d.get('expression') for l in new_grouped_ner for d in l]
    ]
    return new_original_ner, new_ner_list, new_grouped_ner, new_code_mapping_results_model

def match_rewrite_cpt_option(rewrite_query, ner, model_category_lv1, model_category_lv2, model_category_lv3, country_code, site_cd, message_id):
    # start_time = time.time()
    model_category_lv1_placeholders = None
    model_category_lv2_placeholders = None
    model_category_lv3_placeholders = None
    expression = ner.get("expression")

    res = {}
    cpt_flag = False

    spec_df = get_spec_name(expression, 'product_option', model_category_lv1, model_category_lv2, model_category_lv3,
                            country_code, site_cd, message_id)
    # __log.debug(f"spec_df: {spec_df}")
    if not spec_df.empty:
        return res, cpt_flag

    if model_category_lv1:
        model_category_lv1_placeholders = ", ".join(
            "'" + _ + "'" for _ in model_category_lv1 if 'NA' != _
        )
    if model_category_lv2:
        model_category_lv2_placeholders = ", ".join(
            "'" + _ + "'" for _ in model_category_lv2 if 'NA' != _
        )
    if model_category_lv3:
        model_category_lv3_placeholders = ", ".join(
            "'" + _ + "'" for _ in model_category_lv3 if 'NA' != _
        )

    embedded_rewrite_query = embedding_rerank.baai_embedding(rewrite_query, message_id)[0]
    # __log.debug(f"embedding: {time.time() - start_time}")

    rewrite_query_sql = f"""
                        SELECT DISTINCT
                            rcp.clean_chunk,
                            rcp.base_feature,
                            rcp.category_lv1,
                            rcp.category_lv2,
                            rcp.category_lv3,
                            rcp.chunkid,
                            subq.distance
                        FROM (
                            SELECT DISTINCT
                                clean_chunk,
                                base_feature,
                                country_code,
                                embedding <=> '{str(embedded_rewrite_query)}' AS distance
                            FROM rubicon_v3_cpt_desc
                            WHERE country_code = '{country_code}'
    """
    if model_category_lv1_placeholders:
        rewrite_query_sql += f"AND category_lv1 in ({model_category_lv1_placeholders})"
    if model_category_lv2_placeholders:
        rewrite_query_sql += f"AND category_lv2 in ({model_category_lv2_placeholders})"
    if model_category_lv3_placeholders:
        rewrite_query_sql += f"AND category_lv3 in ({model_category_lv3_placeholders})"
    rewrite_query_sql += """
                            ORDER BY distance
                            LIMIT 50
                        ) subq
                        JOIN rubicon_v3_cpt_desc rcp 
                            ON rcp.clean_chunk = subq.clean_chunk
                            AND rcp.country_code = subq.country_code
    """
    if model_category_lv1_placeholders:
        rewrite_query_sql += f"AND rcp.category_lv1 in ({model_category_lv1_placeholders})"
    if model_category_lv2_placeholders:
        rewrite_query_sql += f"AND rcp.category_lv2 in ({model_category_lv2_placeholders})"
    if model_category_lv3_placeholders:
        rewrite_query_sql += f"AND rcp.category_lv3 in ({model_category_lv3_placeholders})"
    rewrite_query_sql += "LIMIT 50"

    with connection.cursor() as curs:
        curs.execute(rewrite_query_sql)
        results = curs.fetchall()
        # __log.debug(f"sql query time: {time.time() - start_time}")
        if results:
            rewrite_option_df = pd.DataFrame(results, columns=[c.name for c in curs.description])
            # __log.debug(rewrite_option_df)
            if not rewrite_option_df.empty:
                df_reranked = embedding_rerank.rerank_db_results(
                rewrite_query, rewrite_option_df, text_column="clean_chunk", top_k=20, #score_threshold=0
            )
                mapping_code = df_reranked.iloc[0]['base_feature'].split('|')
                mapping_code = [s.strip() for s in mapping_code]
                # __log.debug(f"mapping_code: {mapping_code}")
                cpt_flag = True
        
    if cpt_flag:
        res = {
            'expression': expression,
            'field': 'product_option',
            'operator': [ner.get('operator')] * len(mapping_code),
            'mapping_code': mapping_code,
            'type': ['CPT_D'],
            'category_lv1': model_category_lv1,
            'category_lv2': model_category_lv2,
            'category_lv3': model_category_lv3,
            'original_expression': expression,
        }


    # __log.debug(f'end time: {time.time() - start_time}')
    return res, cpt_flag

def preprocess_ner_value(ner_value):
    """
    ner_value에서 마지막 연속된 os 항목들을 식별하고 제거
    
    Args:
        ner_value: NER
        
    Returns:
        tuple: (필터링된 ner_value, 제거된 마지막 os 항목들)
    """
    last_os_start_idx = len(ner_value)
    
    for i in range(len(ner_value)-1, -1, -1):
        item = ner_value[i]
        if not (item.get('field') == 'product_option' and item.get('operator') in ['in', 'greater_than', 'less_than']
                # or (item.get('field') == 'product_model') # TODO 확실한가?
                ):
            last_os_start_idx = i + 1
            break
    
    if last_os_start_idx == len(ner_value):
        return ner_value, []
    
    filtered_ner = ner_value[:last_os_start_idx]
    removed_os = ner_value[last_os_start_idx:]
    
    return filtered_ner, removed_os

def preprocess_ner_value_front(ner_value):
    """
    ner_value에서 맨 앞의 연속된 os 항목들을 식별하고 제거
    
    Args:
        ner_value: NER
        
    Returns:
        tuple: (필터링된 ner_value, 제거된 앞부분 os 항목들)
    """
    first_non_os_idx = 0
    
    for i, item in enumerate(ner_value):
        if not (item.get('field') == 'product_option' and item.get('operator') == 'in'):
            first_non_os_idx = i
            break
        
        if i == len(ner_value) - 1:
            first_non_os_idx = len(ner_value)
    
    if first_non_os_idx == 0:
        return ner_value, []
    
    removed_os = ner_value[:first_non_os_idx]
    filtered_ner = ner_value[first_non_os_idx:]
    
    return filtered_ner, removed_os

def process_spec_options(spec_name, purchasable_key, product_category_lv1, product_category_lv2, product_category_lv3, country_code, site_cd, message_id, exist_nonexist_flag, cm_mc, code_mapping_results):
    """
    spec_name 목록에서 옵션을 처리하고 해당 단위 정보를 함께 추출
    
    Args:
        spec_name: option과 color 필드를 가진 spec 목록
        product_categories: (product_category_lv1, product_category_lv2, product_category_lv3) 튜플
        country_code: 국가 코드
        message_id: 메시지 ID
    
    Returns:
        tuple: (옵션-단위 매핑 딕셔너리, 매핑된 옵션 목록)
    """
    # 기본 정보 추출
    filtered_specs = [s for s in spec_name if s.get('expression') and s.get('field') and s.get('operator')]

    # __log.debug(f"Filtered specs: {filtered_specs}")
    
    # 결과 저장 변수
    option_unit_map = {}  # 옵션 이름 -> 단위 리스트 매핑
    option_df_map = {}
    mapped_spec_list = []
    
    # 단일 루프로 처리
    for spec in filtered_specs:
        expression = spec.get('expression')
        field = spec.get('field')
        operator = spec.get('operator')
        
        # 옵션 교정 및 정보 가져오기
        spec_df = get_spec_name(expression, field, product_category_lv1, product_category_lv2, 
                               product_category_lv3, country_code, site_cd, message_id)
        
        # __log.debug(f'spec_df: {spec_df}')
        
        if not spec_df.empty:
            # 매핑 코드 처리
            mapping_code = (get_value_bounds(product_category_lv1, product_category_lv2, product_category_lv3, country_code) 
                           if spec_df['mapping_code'] == 'DEFAULT' else spec_df['mapping_code'])
            # __log.debug(f"mapping_code{mapping_code}")
            
            if ('Mobile' in product_category_lv1 or 'Refrigerators' in product_category_lv2 or 'LCD Monitor' in product_category_lv2) and mapping_code in MANAGE_SPEC_NAME.keys():
                mapping_code = MANAGE_SPEC_NAME.get(mapping_code)

            # 매핑된 정보 저장
            mapped_info = {
                'expression': expression,
                'field': field,
                'operator': operator,
                'mapping_code': [mapping_code],
                'category_lv1': product_category_lv1,
                'category_lv2': product_category_lv2,
                'category_lv3': product_category_lv3
            }
            mapped_spec_list.append(mapped_info)

            # product_option인 경우, 단위 정보 추출
            if field == 'product_option':
                # 해당 옵션에 사용 가능한 단위 정보 가져오기
                # SQL 쿼리 또는 다른 함수를 통해 가져온다고 가정
                # print("********************")
                # __log.debug(mapping_code)
                # print("********************")
                
                # exist_nonexist insert 0613 (parameter 추가 - operator, exist_nonexist_flag)
                os_df, os_units, exist_nonexist_flag = get_units_for_option(mapping_code, purchasable_key, product_category_lv1, product_category_lv2, product_category_lv3, country_code, site_cd, operator, exist_nonexist_flag, cm_mc, code_mapping_results)
                option_df_map[mapping_code] = os_df
                option_unit_map[mapping_code] = os_units
    
    return option_unit_map, option_df_map, mapped_spec_list, exist_nonexist_flag

def get_spec_name(spec_name, spec_field, product_category_lv1, product_category_lv2, product_category_lv3, country_code, site_cd, message_id):
    # get_spec_name_start_time = time.time()
    spec_name_embedding = list(embedding_rerank.baai_embedding(spec_name, message_id)[0])

    product_category_lv1_placeholders = ", ".join(
        "'" + _ + "'" for _ in product_category_lv1
    )
    product_category_lv2_placeholders = ", ".join(
        "'" + _ + "'" for _ in product_category_lv2
    )
    product_category_lv3_placeholders = ", ".join(
        "'" + _ + "'" for _ in product_category_lv3
    )
    
    
    exact_option_field_query = """
                        SELECT DISTINCT 
                            mapping_code,
                            field,
                            expression,
                            category_lv1,
                            category_lv2,
                            category_lv3,
                            type
                        FROM rubicon_v3_complement_code_mapping
                        WHERE expression = %s
                        AND type != 'func'
                        AND type != 'CPT'
                        AND field = %s
                        AND country_code = %s
                        AND active = True
    """
    
    exact_option_field_query += f"AND site_cd = '{site_cd}'"
    

    if "NA" not in product_category_lv1:
        exact_option_field_query += f"AND category_lv1 in ({product_category_lv1_placeholders}) "
    if "NA" not in product_category_lv2:
        exact_option_field_query += f"AND category_lv2 in ({product_category_lv2_placeholders}) "
    if "NA" not in product_category_lv3:
        exact_option_field_query += f"AND category_lv3 in ({product_category_lv3_placeholders}) "


    similarity_option_field_query = """
                        SELECT DISTINCT 
                            rcm.mapping_code,
                            rcm.field,
                            rcm.expression,
                            rcm.category_lv1,
                            rcm.category_lv2,
                            rcm.category_lv3,
                            rcm.type,
                            subq.distance
                        FROM (
                            SELECT DISTINCT
                                expression,
                                field,
                                embedding <=> %s::vector AS distance
                            FROM rubicon_v3_complement_code_mapping
                            WHERE field = %s
                            AND type != 'func'
                            AND type != 'CPT'
                            AND country_code = %s
    """

    similarity_option_field_query == f"AND site_cd = '{site_cd}' "
    if "NA" not in product_category_lv1:
        similarity_option_field_query += f"AND category_lv1 in ({product_category_lv1_placeholders})"
    if "NA" not in product_category_lv2:
        similarity_option_field_query += f"AND category_lv2 in ({product_category_lv2_placeholders})"
    if "NA" not in product_category_lv3:
        similarity_option_field_query += f"AND category_lv3 in ({product_category_lv3_placeholders})"


    similarity_option_field_query += f"""AND active = True
                            ORDER BY distance
                            LIMIT 50
                        ) subq
                        JOIN rubicon_v3_complement_code_mapping rcm
                            ON rcm.expression = subq.expression
                            AND rcm.field = subq.field
                            AND rcm.active = True
    """
    similarity_option_field_query == f"AND site_cd = '{site_cd}' "
    if "NA" not in product_category_lv1:
        similarity_option_field_query += f"AND rcm.category_lv1 in ({product_category_lv1_placeholders})"
    if "NA" not in product_category_lv2:
        similarity_option_field_query += f"AND rcm.category_lv2 in ({product_category_lv2_placeholders})"
    if "NA" not in product_category_lv3:
        similarity_option_field_query += f"AND rcm.category_lv3 in ({product_category_lv3_placeholders})"

    similarity_option_field_query += """ORDER BY subq.distance
                                        LIMIT 10
    """

    with connection.cursor() as curs:
        curs.execute(exact_option_field_query, [spec_name, spec_field, country_code])
        results = curs.fetchall()
        # __log.debug(f"exact_option_field_query: {exact_option_field_query}")
        # __log.debug(f"{[spec_name, spec_field, country_code]}")
        result_df = pd.DataFrame(results, columns = [c.name for c in curs.description])
        # elapsed_time = time.time() - get_spec_name_start_time
        # __log.debug(f'complement: _code_mapping: unstructured_code_mapping: get_spec_name: exact match: {round(elapsed_time, 4)}')
        
        if not result_df.empty:
            # __log.debug(f"exact_option_field_query: {exact_option_field_query}")
            return result_df.iloc[0]
        
        else:
            # __log.debug(f"similarity_option_field_query: {similarity_option_field_query}")
            curs.execute(similarity_option_field_query, [spec_name_embedding, spec_field, country_code])
            results = curs.fetchall()
            result_df = pd.DataFrame(results, columns = [c.name for c in curs.description])
            # elapsed_time = time.time() - get_spec_name_start_time
            # __log.debug(f'complement: _code_mapping: unstructured_code_mapping: get_spec_name: similarity match: {round(elapsed_time, 4)}')

            # df_reranked = embedding_rerank.rerank_db_results(
            #     spec_name, result_df, text_column="expression", top_k=5, score_threshold=2
            # )
            # # __log.debug(df_reranked.columns.tolist())
            # # Return empty DataFrame if reranked results are empty
            # if df_reranked.empty:
            #     result_df = df_reranked
            # else:
            #     df_reranked = df_reranked.loc[df_reranked['reranker_score'] == df_reranked['reranker_score'].max()]
            #     __log.debug(df_reranked)
            #     result_df = df_reranked
            # print(result_df)
            result_df = result_df[result_df['distance'] < 0.38]
            if result_df.empty:
                return result_df
            result_df = result_df.iloc[0]
            
            
    return result_df

def get_value_bounds(product_category_lv1, product_category_lv2, product_category_lv3, country_code):
    # HC5
    if country_code == 'KR':
        CATEGORY_SPEC_UNITS = {
            'HHP': {
                'NEW RADIO MOBILE (5G SMARTPHONE)': '크기 (Main Display)',
                'LTE HHP': '크기 (Main Display)',
                'TABLET': '크기 (Main Display)',
                'WEARABLE DEVICE VOICE': '크기(Main)'},
            'PC': {
                'NOTE':'디스플레이',
                'AIO':'디스플레이'              ## 1. 추가
                },
            'ELECTRIC WASHER': {
                'FCD': '건조 용량',
                'FWM': '세탁 용량',
                'OWM': '세탁 용량',
                'FWM/FCD': '세탁 용량'
                },
            '냉장고': '전체 용량',
            '김치냉장고': '전체 용량',
            'AIR CONDITIONER': {
                'FAC': '냉방 면적',
                'RAC': '냉방 면적',
                'WAC': '냉방 면적',
                'ACR': '사용 면적',
                },
            'DISH WASHER': '용량',
            'Flat Panel Displayer': {
                'LCD Monitor': '화면사이즈 (cm)',
                'LED TV': '화면크기',
                'MICROLED SCREEN': '화면크기',
                'QLED TV': '화면크기',
                'OLED SCREEN': '화면크기',
            },
            # '진공청소기': ['최대흡입력', 'W'],
            'COOKING GOODS': '소비전력',
            ## 3. 추가
            'BRAND SOLUTION': {
                'PERSONAL CLOUD DRIVE': 'Capacity',
                'BRAND SSD': '용량',
                'BRAND CARD': 'Capacity'
            },
            ## 4. 추가
            'CONSUMER AUDIO': '크기',
            # 'HOME AUDIO': '본체 크기 (가로x높이x깊이)',
            'MERCHANDISING': {
                'BIDET': '제품크기',
                'HARMAN AUDIO': '크기',
                'SAMSUNG BIDET': '제품크기',
                # 'SAMSUNG EXTERNAL HDD': '크기(가로x깊이x높이)',
                # 'SAMSUNG HOME APPLIANCES OPTION': '크기(가로 × 높이 × 깊이)'
            },
            # '정수기':'크기(가로 × 높이 × 깊이)'

        }
    elif country_code == 'GB':
        CATEGORY_SPEC_UNITS = {
            'Mobile': {
                'Smartphones': 'Size (Main_Display)',
                'Tablets': 'Size (Main_Display)', ## 추가 1. 화면 관련 스펙이 있음
                'Watches': 'Size (Main Display)',
                # 'Rings': None, # 모든 spec에 단위가 disp_nm2에 있음
            },
            'Computers' : {
                'Computers': 'Display'
            },
            'Home Appliances' : {
                'Washers and Dryers': {
                    'Dryers': 'Drying Capacity (kg)',
                    'Washer Dryer Combo': 'Washing Capacity (kg)',
                    'Washing Machines': 'Washing Capacity (kg)'
                },
                'Refrigerators': 'Gross Total(Litre)',
                'Dishwashers': 'Capacity (Place Setting)',
                'Microwave Ovens': 'Oven Capacity',
                ## 추가 2.
                'Cooking Appliances': 'Oven Capacity', ## 다른 모델 코드에 대해서 'Usable Capacity'와 같이 다른 표현 사용하기도 함
                'Vacuum Cleaners': 'Dust Capacity',          
            },
            'Television': {
                'TV': 'Screen Size',
                'Lifestyle TV': 'Screen Size',
                ## 추가 3.
                'Business TV': 'Diagonal Size (Inch)',
                'Projectors': 'Screen Size'
            },
            'Display': 'Screen Size (Class)', # Class가 단위
            ## 추가 4.
            'Memory and Storage': 'Capacity'
        }

    f_val = CATEGORY_SPEC_UNITS.get(product_category_lv1[0])
    temp = []
    if 'Washers and Dryers' in product_category_lv2 and country_code == 'GB':
        if 'Washer Dryer Combo' in product_category_lv3 or 'Washing Machines' in product_category_lv3:
            return 'Washing Capacity (kg)'
        else:
            return 'Drying Capacity (kg)'

    if isinstance(f_val, str):
        return f_val
    elif isinstance(f_val, dict):
        for c in product_category_lv2:
            temp.append(f_val.get(c))
        temp = [s for s in temp if s is not None]
        f_val = max(set(temp), key = temp.count)
        return f_val
    else:
        return None
    
# 단위 정보를 가져오는 함수 (SQL 쿼리 사용)
def get_units_for_option(option_name, purchasable_key, product_category_lv1, product_category_lv2, product_category_lv3, country_code, site_cd, operator, exist_nonexist_flag, cm_mc, code_mapping_results):
    """특정 옵션에 사용 가능한 단위 목록 가져오기"""

    product_category_lv1_placeholders = ", ".join(
        "'" + _ + "'" for _ in product_category_lv1
    )
    product_category_lv2_placeholders = ", ".join(
        "'" + _ + "'" for _ in product_category_lv2
    )
    product_category_lv3_placeholders = ", ".join(
        "'" + _ + "'" for _ in product_category_lv3
    )
    os_placeholder = "'" + option_name + "'"

    # HC6    
    # TODO: 일관성 없는 스펙명의 경우 여기서 조치
    if option_name == '전체 용량' or option_name == '전체 용량(Liter)':
        os_placeholder = "'전체 용량', '전체 용량(Liter)'"
    if option_name == '비디오 재생 시간 (Hours)' or option_name == '비디오 재생 시간 (Hours, Wireless)':
        os_placeholder = "'비디오 재생 시간 (Hours, Wireless)', '비디오 재생 시간 (Hours)'"
    if option_name == '사용 면적(청정)' or option_name == '사용 면적':
        os_placeholder = "'사용 면적(청정)', '사용 면적'"
    if option_name == '출력 레벨':
        os_placeholder = "'전체 출력'"
    if option_name == '용량':
        os_placeholder = "'용량', 'Capacity'" # 0626 inserted by hsm
    if option_name == '소비전력' or option_name == '소비 전력(kWh/월)':
        os_placeholder = "'소비전력', '소비 전력(kWh/월)'"  #0701 inserted by yji
    if option_name == '스피커 수' or option_name == '스피커수':
        os_placeholder = "'스피커 수', '스피커수'"
    if option_name == '크기 (Main Display)' or option_name == '크기(Main)' and 'WEARABLE DEVICE VOICE' in product_category_lv2:
        os_placeholder = "'크기 (Main Display)', '크기(Main)'"
    if option_name == '배터리 용량 (Typical, mAh)' or option_name == '배터리 용량 (Typical)' or option_name == '배터리 용량 (mAh, Typical)':
        os_placeholder = "'배터리 용량 (Typical, mAh)', '배터리 용량 (Typical)', '배터리 용량 (mAh, Typical)'"  
    if option_name == 'Water Consumption (cycle)' or option_name == 'Water Consumption (cycle, wash only)' and 'Washer Dryer Combo' in product_category_lv3:
        os_placeholder = "'Water Consumption (cycle)', 'Water Consumption (cycle, wash only)'"
    if (option_name == '본체 무게 (g)' or option_name == '무게') and 'WEARABLE DEVICE VOICE' in product_category_lv2:
        os_placeholder = "'본체 무게 (g)', '무게'"
    # 20250704 insert yji
    if option_name == '배터리 용량 (이어버드, Typical)' or option_name == '이어버드 배터리 용량 (Typical, mAh)' and 'MODULE' in product_category_lv2:
        os_placeholder = "'배터리 용량 (이어버드, Typical)', '이어버드 배터리 용량 (Typical, mAh)'"
    # if option_name == '연속 통화시간(2G CDMA) (Hours)' or option_name == '연속 통화시간(2G GSM) (Hours)' or option_name == '연속 통화시간(3G WCDMA) (Hours)':
    #     os_placeholder = "'연속 통화시간(4G LTE) (Hours)'"
    if option_name == '재생시간' or option_name == '음악재생시간' and 'HOME AUDIO' in product_category_lv2 and 'Speaker' in product_category_lv3:
        os_placeholder = "'재생시간', '음악재생시간'"
    
    with connection.cursor() as curs:
        os_query = f"""
            SELECT category_lv1, category_lv2, category_lv3, goods_nm, mdl_code, disp_nm1, disp_nm2, value
            FROM rubicon_v3_complement_product_spec
            WHERE (disp_nm1 in ({os_placeholder}) or disp_nm2 in ({os_placeholder}))
            AND site_cd = '{site_cd}'
            AND on_sale not like 'X'
            """

        if "NA" not in product_category_lv1:
            os_query += f"AND category_lv1 in ({product_category_lv1_placeholders})"
        if "NA" not in product_category_lv2:
            os_query += f"AND category_lv2 in ({product_category_lv2_placeholders})"
        if "NA" not in product_category_lv3:
            os_query += f"AND category_lv3 in ({product_category_lv3_placeholders})"
        if purchasable_key:
            os_query += f"AND on_sale = 'Y'"

        curs.execute(os_query)
        os_result = curs.fetchall()
        os_df = pd.DataFrame(os_result, columns = [c.name for c in curs.description])
        # __log.debug(os_query)
        # __log.debug(os_df)
        
        # HC7
        # 워치 크기 처리
        if option_name == '크기 (Main Display)' or option_name == '크기(Main)' and 'WEARABLE DEVICE VOICE' in product_category_lv2:
            for c3, r in WATCH_SIZE_REPLACE.items():
                mask = os_df['category_lv3'] == c3
                for ov, nv in r:
                    os_df.loc[mask, 'value'] = os_df.loc[mask, 'value'].str.replace(ov, nv)
        if option_name == 'Size (Main Display)' and 'Galaxy Watch' in product_category_lv3:
            os_df['cat'] = os_df['goods_nm'].apply(extract_watch_category)
            os_df['value'] = os_df['value'].apply(extract_mm_value)
            for c, r in WATCH_GB_REPLACE.items():
                mask = os_df['cat'] == c
                for ov, nv in r:
                    os_df.loc[mask, 'value'] = os_df.loc[mask, 'value'].str.replace(ov, nv)
            os_df = os_df.drop('cat', axis = 1)
        # 워치 배터리 처리
        if option_name == '배터리 용량 (Typical)' or option_name == '배터리 용량 (Typical, mAh)' and 'WEARABLE DEVICE VOICE' in product_category_lv2:
            os_df['value'] = os_df['value'].apply(lambda x: x if 'mAh' in x else x + ' mAh')
        # 워치 무게 처리
        if (option_name == '본체 무게 (g)' or option_name == '무게') and 'WEARABLE DEVICE VOICE' in product_category_lv2:
            os_df['value'] = os_df['value'].apply(lambda x: x if 'g' in x else x + ' g')
        # 저장용량 처리
        if option_name == '스토리지(저장 용량) (GB)':
            os_df['value'] = os_df['value'].fillna('1024 GB')
        if option_name in ['이어버드 무게 (g)', '본체 무게 (g)', '무게 (g)']:
            os_df['value'] = os_df['value'] + ' g'
        if option_name == 'Screen Size (Class)':
            os_df['value'] = os_df['value'] + ' inch'
        if (option_name in ['해상도', 'Resolution'] or 
        (option_name == 'Display' and 'Computers' in product_category_lv1 and 'Computers' in product_category_lv2) or 
        (option_name == '디스플레이' and 'PC' in product_category_lv1)):
            resolution_pattern = r'(\d{1,3}(,\d{3})*)\s*[xX]\s*(\d{1,3}(,\d{3})*)'
            os_df['value'] = os_df['value'].apply(lambda x: str(re.search(resolution_pattern, x).group(1).replace(',', '')) + ' r' if (isinstance(x, str) and re.search(resolution_pattern, x)) else None)
        # 배터리 용량 처리
        if option_name in ['배터리 용량 (Typical, mAh)', '배터리 용량 (Typical)', '배터리 용량 (mAh, Typical)']:
            os_df['value'] = os_df['value'].apply(
                lambda x: x if 'mAh' in x else x + ' mAh'
            )
        # 스피커 수 처리
        if option_name in ['스피커 수', '스피커수']:
            os_df['value'] = os_df['value'].apply(
                lambda x: x if '개' in x else x + ' 개'
            )
        if option_name == '재생시간' or option_name == '음악재생시간' and 'HOME AUDIO' in product_category_lv2 and 'Speaker' in product_category_lv3:
            os_df['value'] = os_df['value'].apply(lambda x: x if '시간' in x else re.sub(r'^(\d+).*', r'\1시간', x))
        if option_name == '소비전력' and 'E-COOK TOP' in product_category_lv2:
            os_df['value'] = os_df['value'].apply(
                lambda x: x.replace(',', '') if isinstance(x, str) and x.endswith(' W') else x
            )

        # 사용시간 처리
        if ((os_df['category_lv1'] == 'HHP') & (os_df['disp_nm1'] == '배터리')).any():
            condition = (os_df['category_lv1'] == 'HHP') & (os_df['disp_nm1'] == '배터리')
            
            os_df.loc[condition, 'extracted_number'] = os_df.loc[condition, 'value'].apply(
                lambda x: x.split('최대 ')[1] if isinstance(x, str) and '최대 ' in x else None
            )
            
            
            hours_mask = condition & os_df['disp_nm2'].str.contains('Hours', na=False)
            if hours_mask.any():
                os_df.loc[hours_mask, 'value'] = os_df.loc[hours_mask, 'extracted_number'] + ' H'
            
            days_mask = condition & os_df['disp_nm2'].str.contains('일', na=False)
            if days_mask.any():
                os_df.loc[days_mask, 'value'] = os_df.loc[days_mask, 'extracted_number'] + ' 일'
            
            os_df = os_df.drop('extracted_number', axis=1)
        # GB Flip Fold 처리
        gb_flip_key = any(['Flip' in s for s in cm_mc])
        gb_fold_key = any(['Fold' in s for s in cm_mc])
        if 'Galaxy Z' in product_category_lv3 and option_name in ['Size (Main_Display)', 'Battery Capacity (mAh, Typical)', 'Storage (GB)', 'Weight (g)']:
            if gb_flip_key and gb_fold_key:
                pass
            elif gb_flip_key:
                os_df = os_df[os_df['goods_nm'].str.contains('Flip')]
            elif gb_fold_key:
                os_df = os_df[os_df['goods_nm'].str.contains('Fold')]
        #0710 insert, 0721 modified
        l4_input = code_mapping_results[0]
        expression = code_mapping_results[0]["expression"]
        l4_check, l4_filters = check_valid_product(expression, l4_input, country_code)
        product_filter = l4_filters["product_filter"]
        negative_product_filter = l4_filters["negative_product_filter"]
        # __log.debug(f"product filter: {product_filter} ")
        # __log.debug(f"negative_product_filter: {negative_product_filter} ")
        os_df = os_df[os_df["goods_nm"].astype(str).str.lower().apply(lambda x: all((keyword in x) if not keyword.startswith('[') else any(item in x for item in set(ast.literal_eval(keyword))) for keyword in product_filter))]
        os_df = os_df[~os_df['goods_nm'].astype(str).str.lower().apply(lambda x: any(keyword in x for keyword in negative_product_filter))]

        # 20250603 insert 
        # 배터리 용량 GB 처리
        if option_name == 'Battery Capacity (mAh, Typical)' and 'Mobile' in product_category_lv1:
            os_df['value'] = os_df['value'] + ' mAh'
        # Watch 신제품 무게 처리
        if option_name == 'Body Weight (g)' and 'Watches' in product_category_lv2:
            os_df['value'] = os_df['value'].apply(lambda x: x if 'g' in x else x + ' g')
        # Flip fold 신제품 무게 처리
        if option_name == 'Weight (g)' and 'Smartphones' in product_category_lv2:
            os_df['value'] = os_df['value'] + ' g'
        if option_name == 'Weight (g)' and 'Tablets' in product_category_lv2:
            os_df['value'] = os_df['value'] + ' g'
        # 20250704 insert yji
        if option_name in ['이어버드 배터리 용량 (Typical, mAh)', '배터리 용량 (이어버드, Typical)'] and 'MODULE' in product_category_lv2:
            os_df['value'] = os_df['value'].apply(lambda x: x if 'mAh' in x else x + ' mAh')

        # 사용시간 GB 처리
        if ((os_df['category_lv1'] == 'Mobile') & (os_df['disp_nm1'] == 'Battery')).any():
            condition = (os_df['category_lv1'] == 'Mobile') & (os_df['disp_nm1'] == 'Battery')
            
            os_df.loc[condition, 'extracted_number'] = os_df.loc[condition, 'value'].apply(
                lambda x: x.split('Up to ')[1] if isinstance(x, str) and 'Up to ' in x else None
            )
            
            
            hours_mask = condition & os_df['disp_nm2'].str.contains('Hours', na=False)
            if hours_mask.any():
                os_df.loc[hours_mask, 'value'] = os_df.loc[hours_mask, 'extracted_number'] + ' H'
            
            days_mask = condition & os_df['disp_nm2'].str.contains('Days', na=False)
            if days_mask.any():
                os_df.loc[days_mask, 'value'] = os_df.loc[days_mask, 'extracted_number'] + ' Days'
            
            os_df = os_df.drop('extracted_number', axis=1)
        # Crystal UHD 화면크기 처리
        if ((os_df['category_lv3'] == 'Crystal UHD') & (os_df['disp_nm2'] == '화면크기')).any():
            condition = (os_df['category_lv3'] == 'Crystal UHD') & (os_df['disp_nm2'] == '화면크기') & (os_df['mdl_code'].isin(['KU60UD7050FXKR','KU65UD7050FXKR','KU65UD7030FXKR']))

            os_df.loc[condition, 'value'] = os_df.loc[condition, 'value'].str.replace('60', '152')
            os_df.loc[condition, 'value'] = os_df.loc[condition, 'value'].str.replace('65', '163')

        os_df_explode = os_df.copy().dropna(subset='value')
        os_df_explode['number_unit_pairs'] = os_df_explode['value'].apply(lambda x: extract_number_and_unit(x))
        os_df_exploded = os_df_explode.explode('number_unit_pairs')

        os_df_exploded['extracted_number'] = os_df_exploded['number_unit_pairs'].apply(lambda x: x[0] if x else None)
        os_df_exploded['extracted_unit'] = os_df_exploded['number_unit_pairs'].apply(lambda x: x[1] if x else None)
        os_df_exploded = os_df_exploded.dropna(subset = ['extracted_number', 'extracted_unit'], how = 'any')

        os_units = os_df_exploded['extracted_unit'].unique().tolist()
        
        converter = NetworkUnitConverter()

        os_units = list(set([item for x in os_units for item in converter.get_related_units(x)]))
        
        # exist_nonexist insert 0613 (있음/없음 처리)
        if not os_df.empty and os_df_exploded.empty:
            os_exist_df, exist_nonexist_flag = hard_coding_df_retriever(os_df, operator)
            os_df_exploded = os_exist_df
    
    return os_df_exploded, os_units, exist_nonexist_flag  # 해당 옵션에 사용 가능한 단위 리스트


def split_ner_by_categories(ner_value):
    split_lists = []
    
    split_indices = []
    
    for i, item in enumerate(ner_value):
        field = item.get('field')
        operator = item.get('operator')
        
        if field in ['product_color', 'product_model', 'product_code'] or (field == 'product_option' and operator in ['min', 'max']):
            split_indices.append(i)
    
    if not split_indices:
        return [ner_value]
    
    start = 0
    for idx in split_indices:
        if start < idx:
            split_lists.append(ner_value[start:idx])
        
        split_lists.append([ner_value[idx]])
        
        start = idx + 1
    
    if start < len(ner_value):
        split_lists.append(ner_value[start:])
    
    return split_lists

def categorize_split_lists(split_lists):
    c_items = []
    m_items = []
    om_items = []
    other_lists = []
    
    for sublist in split_lists:
        if len(sublist) == 1:
            item = sublist[0]
            field = item.get('field')
            operator = item.get('operator')
            
            if field == 'product_color':
                c_items.append(item)
            elif field == 'product_model' or field == 'product_code':
                m_items.append(item)
            elif field == 'product_option' and operator in ['min', 'max']:
                om_items.append(item)
            else:
                other_lists.append(sublist)
        else:
            other_lists.append(sublist)
    
    return c_items, m_items, om_items, other_lists

def extract_number_and_unit(value):
    value_str = str(value)

    number_character_mixed = bool(re.search(r'\d', value_str)) and bool(re.search(r'[^\d\s]', value_str))
    
    if number_character_mixed:
        # 1. 괄호가 있는 경우를 처리
        bracket_match = re.search(r"\(([\d.]+)\s*([^\d\s]+)\)", value_str)
        if bracket_match:
            try:
                number = float(bracket_match.group(1))
                unit = bracket_match.group(2).strip()
                return [(number, unit)]
            except:
                pass
        
        # 2. 먼저 치수 패턴을 모두 찾아서 제외
        # 여러 종류의 치수 패턴 처리 (2D, 3D, 특수문자 포함)
        dimension_patterns = [
            # 3D 치수 패턴 (x가 2개인 경우)
            r"\d+(?:\.\d+)?\s*[xX×]\s*\d+(?:\.\d+)?\s*[xX×]\s*\d+(?:\.\d+)?\s*[^\d\s]+",
            # 특수문자가 포함된 패턴 (x*)
            r"\d+(?:\.\d+)?\s*x\*\s*\d+(?:\.\d+)?\s*(?:x\*\s*\d+(?:\.\d+)?)?\s*[^\d\s]+",
            # 일반 2D 치수 패턴
            r"\d+(?:\.\d+)?\s*[xX×]\s*\d+(?:\.\d+)?\s*[^\d\s]+"
        ]
        
        # 모든 치수 패턴 위치 찾기
        excluded_ranges = []
        for pattern in dimension_patterns:
            for match in re.finditer(pattern, value_str):
                excluded_ranges.append((match.start(), match.end()))
        
        # 3. 일반적인 숫자-단위 패턴 찾기
        matches = re.finditer(r"([\d.]+)\s*([^\d\s]+)", value_str)
        results = []
        
        for match in matches:
            start_pos = match.start()
            end_pos = match.end()
            
            # 제외 범위에 포함되는지 확인
            is_excluded = False
            for ex_start, ex_end in excluded_ranges:
                if (ex_start <= start_pos < ex_end):
                    is_excluded = True
                    break
            
            if not is_excluded:
                try:
                    number = float(match.group(1))
                    unit = match.group(2).strip()
                    results.append((number, unit))
                except:
                    pass
    
    
        return results if results else [(None, None)]
    else:
        return [(None, None)]

def specify_unknown_spec(expression_unit, related_expression_units, product_category_lv1, product_category_lv2, product_category_lv3, country_code):
    spec_name = None
    spec_unit = None
    # HC8
    if country_code == 'KR':
        if '냉장고' in product_category_lv1 and 'L' in related_expression_units:
            spec_name = ['전체 용량']
        if 'HHP' in product_category_lv1 and 'M' in related_expression_units:
            if 'NEW RADIO MOBILE (5G SMARTPHONE)' in product_category_lv2 or any(set(['Galaxy Watch7', 'Galaxy Watch Ultra', 'Galaxy Watch8', 'Galaxy Watch8 Classic']) & set(product_category_lv3)):
                spec_name = ['크기 (Main Display)']
            elif 'WEARABLE DEVICE VOICE' in product_category_lv2:
                spec_name = ['크기(Main)']
        if 'TABLET' in product_category_lv2 and 'M' in related_expression_units:
            spec_name = ['크기 (Main Display)']
        if any(set(['LTE HHP', 'NEW RADIO MOBILE (5G SMARTPHONE)']) & set(product_category_lv2)) and 'HZ' in related_expression_units:
            spec_name = ['최대 주사율 (Main Display)']
        if any(set(['LTE HPP', 'NEW RADIO MOBILE (5G SMARTPHONE)', 'TABLET']) & set(product_category_lv2)) and 'G' in related_expression_units:
            spec_name = ['무게 (g)']
            spec_unit = 'G'
        if 'WEARABLE DEVICE VOICE' in product_category_lv2 and 'G' in related_expression_units:
            spec_name = ['본체 무게 (g)', '무게']
        elif 'MAH' in related_expression_units:
            if any(set(['LTE HPP', 'NEW RADIO MOBILE (5G SMARTPHONE)', 'TABLET']) & set(product_category_lv2)) or any(set(['Galaxy Watch7', 'Galaxy Watch Ultra', 'Galaxy Ring', 'Galaxy Watch8', 'Galaxy Watch8 Classic']) & set(product_category_lv3)):
                spec_name = ['배터리 용량 (Typical, mAh)', '배터리 용량 (Typical)', '배터리 용량 (mAh, Typical)']
                spec_unit = 'MAH'
            elif 'WEARABLE DEVICE VOICE' in product_category_lv2 and not any(set(['Galaxy Watch7', 'Galaxy Watch Ultra', 'Galaxy Watch8', 'Galaxy Watch8 Classic']) & set(product_category_lv3)):
                spec_name = ['배터리 용량 (Typical)', '배터리 용량 (Typical, mAh)', '배터리 용량 (mAh, Typical)']
                spec_unit = 'MAH'
        if 'Flat Panel Displayer' in product_category_lv1:
            if 'M' in related_expression_units:
                spec_name = ['화면크기', '화면사이즈 (cm)']
                spec_unit = 'cm'
            elif 'KG' in related_expression_units:
                if any(set(['LED TV', 'OLED SCREEN', 'QLED TV']) & set(product_category_lv2)):
                    spec_name = ['스탠드 포함 (kg)']
            elif 'W' in related_expression_units:
                spec_name = ['소비전력 (Typical)', '정격소비전력']
                    # spec_name = '소비전력 (Max)'
                    # Question: 정격소비전력과 완벽히 align 되는 value가 어떤건지 모르겠음
        if 'ELECTRIC WASHER' in product_category_lv1:
            if 'KG' in related_expression_units:
                if any(set(['FWM', 'OWM', 'FWM/FCD']) & set(product_category_lv2)):
                    spec_name = ['세탁 용량']
                elif 'FCD' in product_category_lv2 and not any(set(['FWM', 'OWM', 'FWM/FCD']) & set(product_category_lv2)):
                    spec_name = ['건조 용량']
            # 추가 6: W (소비전력) 추가
            elif 'W' in related_expression_units and 'PEDESTAL' not in product_category_lv2:
                spec_name = ['소비전력']
            elif 'M' in related_expression_units:
                spec_name = ['디스플레이']
 # 추가 7: 흡입력 있는 category_lv3만 축소 + 먼지용량 추가
        if '진공청소기' in product_category_lv1:
            if 'W' in related_expression_units and any(set(['Robot Vacuum Cleaner', 'Bespoke Jet V/C', 'Bespoke Slim V/C', 'Jet V/C']) & set(product_category_lv3)):
                spec_name = ['흡입력']
            elif 'Bespoke Jet AI' in product_category_lv3:
                spec_name = ['흡입력']
                spec_unit = 'W'
            # elif 'L' in related_expression_units and 'VC HANDY' not in product_category_lv2:
            #     spec_name = ['먼지용량']
        # 추가 8: 김치냉장고 추가
        if '김치냉장고' in product_category_lv1:
            if 'L' in related_expression_units and any(set(['Bespoke Kimchi Refrigerator', 'Kimchi Container', 'Panel', 'Kimchi Refrigerator']) & set(product_category_lv3)):
                spec_name = ['전체 용량']
        # 추가 9: 에어컨 추가
        if 'AIR CONDITIONER' in product_category_lv1 and '㎡' in related_expression_units:
            # 250508 spec_name 추가
            if 'ACR' in product_category_lv2 and any(set(['Air Purifier', 'Bespoke Cube Air Purifier']) & set(product_category_lv3)):
                spec_name = ['사용 면적(청정)', '사용 면적']
            if 'FAC' in product_category_lv2 and not any(set(['Filter', 'Remote Controller']) & set(product_category_lv3)):
                spec_name = ['냉방 면적']
            elif 'RAC' in product_category_lv2 and 'Room Air Conditioner' in product_category_lv3:
                spec_name = ['냉방 면적']
            elif 'WAC' in product_category_lv2 and 'Bespoke Window Air Conditioner' in product_category_lv3:
                spec_name = ['냉방 면적']
        # 추가 10: COOKING GOODS 추가
        if 'COOKING GOODS' in product_category_lv1:
            if 'W' in related_expression_units:
                if 'OVEN(SPEED COMPACT)' in product_category_lv2 and 'Oven' in product_category_lv3:
                    spec_name = ['MWO출력']
                elif 'OVEN(SPEED COMPACT)' in product_category_lv2 and 'Oven' not in product_category_lv3:
                    spec_name = ['MWO 출력']
                elif not any(set(['E-COOK TOP', 'HOOD']) & set(product_category_lv2)):
                    spec_name = ['MWO 출력']
                elif 'E-COOK TOP' in product_category_lv2 and any(set(['Bespoke Induction Cooktop', 'Electric Range']) & set(product_category_lv3)):
                    spec_name = ['전체 출력']
                elif 'E-OVEN' in product_category_lv2:
                    spec_name = ['소비전력']
            elif '구' in related_expression_units and 'E-COOK TOP' in product_category_lv2 and any(set(['Bespoke Induction Cooktop', 'Electric Range']) & set(product_category_lv3)):
                spec_name = ['화구 수']
            elif 'L' in related_expression_units and any(set(['MWO(COMMON)', 'OVEN(SPEED COMPACT)']) & set(product_category_lv2)):
                spec_name = ['용량']
        # 추가 11: AUDIO 추가
        if 'HOME AUDIO' in product_category_lv1 and 'KG' in related_expression_units:
            if 'AV RECEIVER' in product_category_lv2:
                spec_name = ['본체 무게']
            elif 'MINI COMPONENT' in product_category_lv2:
                spec_name = ['전체 무게']
        if 'CONSUMER AUDIO' in product_category_lv1 and 'KG' in related_expression_units:
            if 'PORTABLE AUDIO' in product_category_lv2:
                spec_name = ['Weight (kg)', '중량']
            elif 'Luxury Audio' in product_category_lv2:
                if 'AV Receiver' in product_category_lv3:
                    spec_name = ['중량']
                elif 'Speaker' in product_category_lv3:
                    spec_name = ['무게정보']
            elif 'HOME AUDIO' in product_category_lv2:
                if 'Speaker' in product_category_lv3:
                    spec_name = ['Weight']
                elif 'Soundbar' in product_category_lv3:
                    spec_name = ['무게정보']
        if 'PRO-AUDIO' in product_category_lv1 and 'KG' in related_expression_units:
            spec_name = ['무게']
        # # 추가 11: MERCHANDISING 추가
        # if 'MERCHANDISING' in product_category_lv1:
        #     if 'Cable' in product_category_lv3 and 'M' in related_expression_units:
        #         spec_name = '케이블 길이'
        #     elif 'HARMAN AUDIO' in product_category_lv2 and 'Earphone' in product_category_lv3 and 'M' in related_expression_units:
        #         spec_name = '케이블 길이'
        #     elif 'MB' in related_expression_units and 'SAMSUNG EXTERNAL HDD' in product_category_lv2:
        #         spec_name = '용량'
        #     elif 'Kimchi Container' in product_category_lv3 and 'L' in related_expression_units:
        #         spec_name = '전체 용량' 
        #     elif 'W' in related_expression_units and 'HARMAN AUDIO' in product_category_lv2 and 'Speaker' in product_category_lv3:
        #         spec_name = '출력'
        # # 추가 12: Optical Visual Display 추가
        # if 'Optical Visual Display' in product_category_lv1:
        #     if 'KG' in related_expression_units:
        #         spec_name = '중량'
        #     elif 'M' in related_expression_units:
        #         spec_name = '화면크기'
        #     elif 'W' in related_expression_units:
        #         spec_name = '정격소비전력'
        #     elif 'DB' in related_expression_units:
        #         spec_name = '소음 (dB)'
        # # 추가 13: CONSUMER AUDIO, pro audio
        # if 'CONSUMER AUDIO' in product_category_lv1 and 'DB' in related_expression_units:
        #     if 'Headphones' in product_category_lv2 and any(set(['Earphone', 'Headphone', 'Wireless']) & set(product_category_lv3)):
        #         spec_name = '최대 SPL'
        #     elif 'Luxury Audio' in product_category_lv2 and 'Headphone' in product_category_lv3:
        #         spec_name = '최대 SPL'
        # if 'PRO-AUDIO' in product_category_lv1 and 'Loudspeaker system' in product_category_lv2 and 'Speaker' in product_category_lv3:
        #     if 'KG' in related_expression_units:
        #         spec_name = '무게'
        #     elif 'W' in related_expression_units:
        #         spec_name = '출력'
        #     elif 'DB' in related_expression_units:
        #         spec_name = '감도 (Sensitivity)'
        # 추가 15: PC
        if 'PC' in product_category_lv1:
            if 'KG' in related_expression_units:
                spec_name = ['무게']
            elif 'MB' in related_expression_units:
                spec_name = ['저장장치']
            elif 'M' in related_expression_units and 'DT' not in product_category_lv2:
                spec_name = ['디스플레이']
        if 'Ultra Slim Soundbar' in product_category_lv3 and '채널' in related_expression_units:
            spec_name = ['채널 수']
            spec_unit = '채널'
        # if 'Air Purifier' in product_category_lv3 and '평' in related_expression_units:
        #     spec_name = '사용 면적(청정)'
        # 20250704 insert yji
        if 'MODULE' in product_category_lv2 and 'MAH' in related_expression_units:
            spec_name = ['이어버드 배터리 용량 (Typical, mAh)', '배터리 용량 (이어버드, Typical)']
    elif country_code == 'GB':
        if 'Mobile' in product_category_lv1 and 'Mobile Accessories' not in product_category_lv2:
            # GB 추가 1. Watches also have storage data
            if 'MB' in related_expression_units:
                if any(set(['Smartphones', 'Tablets']) & set(product_category_lv2)):
                    spec_name = ['Storage (GB)']
                elif 'Watches' in product_category_lv2:
                    if 'Galaxy Fit' in product_category_lv3:
                        spec_name = ['Storage (MB)']
                    else:
                        spec_name = ['Storage (GB)']
                elif 'Rings' in product_category_lv2:
                    spec_name = ['Storage (MB)']
            # GB 추가 2. battery capacity to mobile
            elif 'MAH' in related_expression_units:
                if 'Audio' not in product_category_lv2:
                    spec_name = ['Battery Capacity (mAh, Typical)']
                    spec_unit = 'MAH'
                elif 'Audio' in product_category_lv2:
                    spec_name = ['Case Battery Capacity (mAh, Typical)']
            if 'KG' in related_expression_units:
                if any(set(['Watches', 'Rings']) & set(product_category_lv2)):
                    spec_name = ['Body Weight (g)']
                elif 'Smartphones' in product_category_lv2 or 'Tablets' in product_category_lv2:
                    spec_name = ['Weight (g)']
            if 'M' in related_expression_units:            
                if any(set(['Tablets', 'Smartphones']) & set(product_category_lv2)) and 'M' in related_expression_units:
                    spec_name = ['Size (Main_Display)']
                elif 'Watches' in product_category_lv2:
                    spec_name = ['Size (Main Display)']
        if 'Display' in product_category_lv1 and 'Display Monitors' in product_category_lv2 and 'M' in related_expression_units:
                spec_name = ['Screen Size (Class)']
                spec_unit = 'INCH'
        # GB 추가 3: Home appliances, TV 보강
        if 'Home Appliances' in product_category_lv1:
            if 'KG' in related_expression_units and 'Washers and Dryers' in product_category_lv2 and any(set(['Washer Dryer Combo', 'Washing Machines']) & set(product_category_lv3)):
                spec_name = ['Washing Capacity (kg)']
            elif 'KG' in related_expression_units and 'Washers and Dryers' in product_category_lv2 and 'Dryers' in product_category_lv3:
                spec_name = ['Drying Capacity (kg)']
            elif 'L' in related_expression_units:
                if 'Refrigerators' in product_category_lv2:
                    spec_name = ['Gross Total(Litre)']
                # 250508 spec_name 추가
                elif 'Cooking Appliances' in product_category_lv2 and 'Ovens' in product_category_lv3:
                    spec_name = ['Oven Capacity', 'Usable Capacity', 'Usable Volume (Whole)']
                # 250508 spec_name 추가
                elif 'Microwave Ovens' in product_category_lv2:
                    spec_name = ['Oven Capacity', 'Capacity']
                # elif 'Vacuum Cleaners' in product_category_lv2 and any(set(['Canister', 'Robot', 'Stick']) & set(product_category_lv3)):
                #     spec_name = ['Dust Capacity']
            elif 'M' in related_expression_units:
                if 'Dishwashers' in product_category_lv2:
                    spec_name = ['Size']
                elif 'Cooking Appliances' in product_category_lv2 and 'Hoods' in product_category_lv3:
                    spec_name = ['Size']
            elif 'W' in related_expression_units and 'Vacuum Cleaners' in product_category_lv2 and any(set(['Canister','Stick']) & set(product_category_lv3)):
                    spec_name = ['Suction Power', 'Max Suction Power (Set with Battery)']
        if 'Television' in product_category_lv1 and 'M' in related_expression_units:
            # 250508 spec_name 추가
            if any(set(['Lifestyle TV', 'TV']) & set(product_category_lv2)):
                spec_name = ['Screen Size', 'Screen Size (cm)']
            if 'Business TV' in product_category_lv2:
                spec_name = ['Diagonal Size (Inch)']
        # GB 추가 4: 미포함 category 1 포함
        if 'Computers' in product_category_lv1 and any(set(['Chromebook', 'Galaxy']) & set(product_category_lv3)):
            if 'KG' in related_expression_units:
                spec_name = ['Weight']
            elif 'MB' in related_expression_units:
                spec_name = ['Storage']
            elif 'M' in related_expression_units:
                spec_name = ['Display']
        if 'Memory and Storage' in product_category_lv1 and 'MB' in related_expression_units:
            spec_name = ['Capacity'] 

    return spec_name, spec_unit


def group_options_with_specs(ner_llist, option_unit_map=None):
    result_groups = []
    
    for sublist in ner_llist:
        if len(sublist) <= 1:
            result_groups.append(sublist)
            continue
        
        option_items = []
        spec_items = []
        other_items = []
        
        for item in sublist:
            field = item.get('field')
            operator = item.get('operator')
            
            if field == 'product_option' and operator == 'in':
                option_items.append(item)
            elif field == 'product_spec':
                spec_items.append(item)
            else:
                other_items.append(item)
        
        # 옵션이나 스펙 항목이 없으면 그대로 추가
        if not option_items or not spec_items:
            result_groups.append(sublist)
            continue
        
        # 각 옵션과 스펙 항목 매칭
        groups = match_options_and_specs(option_items, spec_items, option_unit_map)
        # __log.debug(f'groups: {groups}')
        
        # 나머지 항목 처리
        if other_items:
            for group in groups:
                group.extend(other_items)
        
        result_groups.extend(groups)
    
    return result_groups

# def period_map(category_lv1, category_lv2, category_lv3, country_code):
#     if country_code == 'KR':
#         PERIOD_MAP = {
#             'HHP': '0Y',
#             'PC': {
#                 'NOTE':'',
#                 'AIO':''              ## 1. 추가
#                 },
#             'ELECTRIC WASHER': {
#                 'FCD': '',
#                 'FWM': '',
#                 'OWM': '',
#                 'FWM/FCD': ''
#                 },
#             '냉장고': '',
#             '김치냉장고': '',
#             'AIR CONDITIONER': {
#                 'FAC': '냉방 면적',
#                 'RAC': '냉방 면적',
#                 'WAC': '냉방 면적',
#                 'ACR': '사용 면적',
#                 },
#             'DISH WASHER': '용량',
#             'Flat Panel Displayer': {
#                 'LCD Monitor': '화면사이즈 (cm)',
#                 'LED TV': '화면크기',
#                 'MICROLED SCREEN': '화면크기',
#                 'QLED TV': '화면크기',
#                 'OLED SCREEN': '화면크기',
#             },
#             # '진공청소기': ['최대흡입력', 'W'],
#             'COOKING GOODS': '소비전력',
#             ## 3. 추가
#             'BRAND SOLUTION': {
#                 'PERSONAL CLOUD DRIVE': 'Capacity',
#                 'BRAND SSD': '용량',
#                 'BRAND CARD': 'Capacity'
#             },
#             ## 4. 추가
#             'CONSUMER AUDIO': '크기',
#             # 'HOME AUDIO': '본체 크기 (가로x높이x깊이)',
#             'MERCHANDISING': {
#                 'BIDET': '제품크기',
#                 'HARMAN AUDIO': '크기',
#                 'SAMSUNG BIDET': '제품크기',
#                 # 'SAMSUNG EXTERNAL HDD': '크기(가로x깊이x높이)',
#                 # 'SAMSUNG HOME APPLIANCES OPTION': '크기(가로 × 높이 × 깊이)'
#             },
#             # '정수기':'크기(가로 × 높이 × 깊이)'

#         }
#     elif country_code == 'GB':
#         PERIOD_MAP = {
#             'Mobile': {
#                 'Smartphones': 'Size (Main_Display)',
#                 'Tablets': 'Size (Main_Display)', ## 추가 1. 화면 관련 스펙이 있음
#                 'Watches': 'Size (Main Display)',
#                 # 'Rings': None, # 모든 spec에 단위가 disp_nm2에 있음
#             },
#             'Computers' : {
#                 'Computers': 'Display'
#             },
#             'Home Appliances' : {
#                 'Washers and Dryers': {
#                     'Dryers': 'Drying Capacity (kg)',
#                     'Washer Dryer Combo': 'Washing Capacity (kg)',
#                     'Washing Machines': 'Washing Capacity (kg)'
#                 },
#                 'Refrigerators': 'Gross Total(Litre)',
#                 'Dishwashers': 'Capacity (Place Setting)',
#                 'Microwave Ovens': 'Oven Capacity',
#                 ## 추가 2.
#                 'Cooking Appliances': 'Oven Capacity', ## 다른 모델 코드에 대해서 'Usable Capacity'와 같이 다른 표현 사용하기도 함
#                 'Vacuum Cleaners': 'Dust Capacity',          
#             },
#             'Television': {
#                 'TV': 'Screen Size',
#                 'Lifestyle TV': 'Screen Size',
#                 ## 추가 3.
#                 'Business TV': 'Diagonal Size (Inch)',
#                 'Projectors': 'Screen Size'
#             },
#             'Display': 'Screen Size (Class)', # Class가 단위
#             ## 추가 4.
#             'Memory and Storage': 'Capacity'
#         }

def create_date_sequence_excluding_base(base_date_str, period):
    base_date = pd.to_datetime(base_date_str + '-01')
    
    if period.endswith('Y'):
        months = int(period[:-1]) * 12
    elif period.endswith('M'):
        months = int(period[:-1])
    
    # 기준월 제외하고 역산
    start_date = base_date - pd.DateOffset(months=months)
    end_date = base_date - pd.DateOffset(months=1)
    
    date_range = pd.date_range(start=start_date, end=end_date, freq='MS')
    return [date.strftime('%Y-%m') for date in date_range]

def match_options_and_specs(option_items, spec_items, option_unit_map=None):
    groups = []
    
    processed_specs = set()
    
    def extract_unit(expression):
        match = re.search(r'\d+\s*([^\d\s]+)', str(expression))
        if match:
            return match.group(1)
        return None
    
    spec_units = {}
    for i, spec in enumerate(spec_items):
        unit = extract_unit(spec.get('expression', ''))
        if unit:
            if unit not in spec_units:
                spec_units[unit] = []
            spec_units[unit].append((i, spec))
    
    if option_unit_map is None:
        option_unit_map = {}
    
    option_with_same_units = {}
    for option in option_items:
        option_name = option.get('mapping_code', option.get('expression', ''))
        possible_units = option_unit_map.get(option_name, [])
        for unit in possible_units:
            if unit not in option_with_same_units:
                option_with_same_units[unit] = []
            option_with_same_units[unit].append(option)
    
    for unit, options in option_with_same_units.items():
        if len(options) > 1 and unit in spec_units:
            unit_specs = spec_units[unit]
            
            if len(options) == len(unit_specs):
                for i, option in enumerate(options):
                    idx, spec = unit_specs[i]
                    
                    option_group = [option, spec]
                    groups.append(option_group)
                    processed_specs.add(idx)
                    
                    options[i] = None
    
    for option in option_items:
        if option in [o for options_list in option_with_same_units.values() for o in options_list if o is not None] or option not in [o for options_list in option_with_same_units.values() for o in options_list]:
            option_name = option.get('mapping_code', option.get('expression', ''))
            option_group = [option]
            
            possible_units = option_unit_map.get(option_name, [])
            
            if possible_units:
                for unit in possible_units:
                    matching_specs = []
                    
                    if unit in spec_units:
                        for idx, spec in spec_units[unit]:
                            if idx not in processed_specs:
                                matching_specs.append(spec)
                                processed_specs.add(idx)
                        
                        if matching_specs:
                            option_group.extend(matching_specs)
                            break
            
            if len(option_group) == 1 and spec_items:
                option_name = option_group[0].get('mapping_code', option_group[0].get('expression', ''))
                possible_units = option_unit_map.get(option_name, []) if option_unit_map else []
                
                for i, spec in enumerate(spec_items):
                    if i not in processed_specs:
                        spec_unit = extract_unit(spec.get('expression', ''))
                        # 단위 호환성 체크 추가
                        if not possible_units or spec_unit in possible_units:
                            option_group.append(spec)
                            processed_specs.add(i)
                            break
            
            if len(option_group) > 1:  
                groups.append(option_group)
    
    remaining_specs = [spec_items[i] for i in range(len(spec_items)) if i not in processed_specs]
    if remaining_specs:
        if not groups and option_items:  
            groups.append(option_items + remaining_specs)
        elif groups:  
            remaining_to_add = []
            
            for spec in remaining_specs:
                spec_unit = extract_unit(spec.get('expression', ''))
                spec_operator = spec.get('operator')
                added = False
                
                for group in groups:
                    group_option = next((item for item in group if item.get('field') == 'product_option'), None)
                    
                    if group_option:
                        option_name = group_option.get('mapping_code', group_option.get('expression', ''))
                        possible_units = option_unit_map.get(option_name, [])
                        
                        if spec_unit in possible_units:
                            group.append(spec)
                            added = True
                            break
                
                if not added:
                    remaining_to_add.append(spec)
            
            if remaining_to_add:
                groups.append(remaining_to_add)
    
    return groups


def matching_extended_spec_pairs(full_extended_info, country_code, site_cd):
    def extract_number(spec):
        num, unit = spec.split()

        num = float(num)

        if unit == 'TB':
            return num * 1024
        return num
    # AS/AVAS
    spec_name = None
    # AS/AVAS
    spec_df_list = []
    spec_count_list = []
    unique_spec_llist = []
    for single_model_df in full_extended_info:
        c1 = single_model_df['category_lv1'].unique()
        c2 = single_model_df['category_lv2'].unique()
        c3 = single_model_df['category_lv3'].unique()

        # HC9
        if country_code == 'KR':
            if 'HHP' in c1 and ('NEW RADIO MOBILE (5G SMARTPHONE)' in c2 or 'LTE HHP' in c2):
                spec_name = '스토리지(저장 용량) (GB)'
            elif 'Flat Panel Displayer' in c1:
                if 'LCD Monitor' not in c2:
                    spec_name = '화면크기'
                elif 'LCD Monior' in c2 and len(c2) == 1:
                    spec_name = '화면사이즈 (cm)'
            elif 'ELECTRIC WASHER' in c1:
                if any(set(['FWM', 'OWM', 'FWM/FCD']) & set(c2)):
                    spec_name = '세탁 용량'
                elif 'FCD' in c2:
                    spec_name = '건조 용량'
            else:
                return None
        else:
            if 'Mobile' in c1 and ('Smartphones' in c2 or 'Tablets' in c2):
                spec_name = 'Storage (GB)'
            elif 'Television' in c1:
                if 'Lifestyle TV' in c2:
                    spec_name = 'Screen Size'
                else:
                    return None
            elif 'Display' in c1 and 'Display Monitors' in c2:
                spec_name = 'Screen Size (Class)'
            elif 'Home Appliances' in c1 and 'Washers and Dryers' in c2:
                if 'Washing Machines' in c2 or 'Washer Dryer Combo' in c3:
                    spec_name = 'Washing Capacity (kg)'
                elif 'Dryers' in c3:
                    spec_name = 'Drying Capacity (kg)'
            else:
                return None

        mdl_codes = sum(single_model_df['extended_info'], [])

        mdl_code_placeholders = ", ".join(
                    "'" + _ + "'" for _ in mdl_codes
                )
        with connection.cursor() as curs:
            pair_match_sql = f"""
                            SELECT category_lv1, category_lv2, category_lv3, goods_nm, mdl_code, disp_nm1, disp_nm2, value
                            FROM rubicon_v3_complement_product_spec
                            WHERE mdl_code in ({mdl_code_placeholders})
                            and disp_nm2 = '{str(spec_name)}'
                            and site_cd = '{site_cd}'
                            and country_code = '{country_code}'
                            and on_sale not like 'X'
                            order by goods_nm
                            """
            curs.execute(pair_match_sql)
            result_spec = curs.fetchall()

            if not result_spec:
                return None
            spec_df = pd.DataFrame(result_spec, columns=[c.name for c in curs.description])
            if spec_name == '스토리지(저장 용량) (GB)':
                spec_df['value'] = spec_df['value'].fillna('1 TB')
            spec_df_list.append(spec_df)
            extracted_spec_counts = spec_df['value'].value_counts().to_dict()
            extracted_spec_values = spec_df['value'].unique().tolist()
            spec_count_list.append(extracted_spec_counts)
            unique_spec_llist.append(extracted_spec_values)
    
    common_elements = reduce(np.intersect1d, unique_spec_llist)

    total_counts = {}
    for s in common_elements:
        total_counts[s] = sum(d.get(s, 0) for d in spec_count_list)
    
    if spec_name != '화면사이즈 (cm)':
        max_count_spec_value = max(total_counts.items(), 
                            key=lambda item: (item[1], extract_number(item[0])))[0]
    elif spec_name == '화면사이즈 (cm)':
        max_count_spec_value = max(total_counts, key = total_counts.get)
    filtered_mdl_codes = [df[df['value'] == max_count_spec_value]['mdl_code'].tolist() for df in spec_df_list]
    final_df_list = []
    for e_df, l in zip(full_extended_info, filtered_mdl_codes):
        if e_df.empty:
            return None
        # e_df['extended_info'] = e_df['extended_info'].apply(lambda x: list(set(x).intersection(set(l))))
        e_df['extended_info'] = e_df.apply(
        lambda row: [item for item in row['extended_info'] if item in l] 
                    if '갤럭시 S' in row['mapping_code'] 
                    else [item for item in row['extended_info'] if item in l],
        axis=1
        )
        e_df = e_df[e_df['extended_info'].apply(lambda x: len(x) > 0)]
        final_df_list.append(e_df)
    
    return final_df_list

def get_purchasable(df, country_code, site_cd):
    category_models = {}
    
    for _, row in df.iterrows():
        category_key = (row['category_lv1'], row['category_lv2'], row['category_lv3'])
        
        if category_key not in category_models:
            category_models[category_key] = []
        
        category_models[category_key].extend(row['extended_info'])
    
    optimized_queries = []
    
    for category, models in category_models.items():
        category_lv1, category_lv2, category_lv3 = category
        model_codes = "'" + "', '".join(models) + "'"
        
        if country_code == 'KR':
            query = f"""
            SELECT 
                mdl_code,
                CASE WHEN goods_stat_cd = '30' AND show_yn = 'Y' THEN TRUE ELSE FALSE END AS purchasable
            FROM rubicon_data_product_category 
            WHERE mdl_code IN ({model_codes})
            AND site_cd in ('{site_cd}')
            """
            # __log.debug(f'query: {query}')
        else:
            query = f"""
            SELECT 
                model_code,
                CASE WHEN salesstatus = 'PURCHASABLE' THEN TRUE ELSE FALSE END AS purchasable
            FROM rubicon_data_uk_model_price
            WHERE model_code IN ({model_codes})
            AND site_cd in ('{site_cd}')
            """
        optimized_queries.append({
            'category': category,
            'model_codes': models,
            'query': query
        })
        # __log.debug(f"purchasble query: {query}")
    
    for i, query_info in enumerate(optimized_queries):
        category = query_info['category']
    with connection.cursor() as curs:
        model_purchasable = {}
        for query_info in optimized_queries:
            curs.execute(query_info['query'])
            for mdl_code, is_purchasable in curs.fetchall():
                model_purchasable[mdl_code] = is_purchasable

    
    new_rows = []
    
    for _, row in df.iterrows():
        for model_code in row['extended_info']:
            is_purchasable = model_purchasable.get(model_code, False)
            
            new_row = {
                'mapping_code': row['mapping_code'],
                'id': row['id'],
                'category_lv1': row['category_lv1'],
                'category_lv2': row['category_lv2'],
                'category_lv3': row['category_lv3'],
                'extended_info': [model_code], 
                'purchasable': is_purchasable,
                'expression': row.get('expression', '')
            }
            
            new_rows.append(new_row)
    
    result_df = pd.DataFrame(new_rows)
    if result_df.empty: 
        return result_df
    result_df = result_df.groupby(['mapping_code', 'id', 'category_lv1', 'category_lv2', 'category_lv3', 'purchasable', 'expression']).agg({
        'extended_info': lambda x: sum(x.tolist(), [])
    }).reset_index()

    result_df['old_id'] = result_df['id']
    
    result_df = result_df.sort_values(by=['purchasable', 'id'], ascending=[False, True]).reset_index(drop = True)
    result_df['id'] = result_df.index
    result_df = result_df[result_df['purchasable'] == True]

    return result_df

# exist_nonexist insert 0613
def contains_non_exist(value):
    # HC10
    non_exist_list = [
    '없음', 
    'N/A', 
    '미적용',
    "미지원",
    "미포함",
    "불가능",
    "비대상",
    "아니오",
    "지원안함",
    "해당없음",
    "해당 없음",
    "해당사항없음",
    "없음",
    "연결 불가",
    "No",
    "None",
    "NONE",
    "Not Available",
    "Not supported",
    "X",
    "무",
    ]
        
    if not isinstance(value, str):
        return False
    return any(keyword.lower() in value.lower() for keyword in non_exist_list)

# exist_nonexist insert 0613
def hard_coding_df_retriever(os_df, operator):
    value_list = os_df['value'].to_list()
    
    if operator == 'in':
        os_exist_df = os_df[~os_df['value'].apply(contains_non_exist)]
    else:
        os_exist_df = os_df[os_df['value'].apply(contains_non_exist)]

    exist_nonexist = True

    return os_exist_df, exist_nonexist

# 후순위 랭킹 insert 0620
def extra_categories_rank_lower(df, country_code):
    if country_code == 'KR':
        CATEGORY3_KR_TARGETS = {'Accessory Kit', 'Adapter', 'Band', 'Battery', 'Cable', 'Camera', 'Cartridges', 'Case', 'Charger', 'Cover', 'Film', 'Installation Kit', 'Keyboard', 'Kimchi Container', 'Mouse', 'Panel', 'Remote Controller', 'Shelf', 'Stand', 'Tray','Box','Brush','Connector','Container','Dispenser','Dust Bag','Filter','Foucet','Hanger','Kettle','Memory','Mircrophone','Mop','Paper','Station','Storage','Weight'}
        CATEGORY2_KR_TARGETS = {'HHP OPTION', 'MOBILE-VPS PRODUCT', 'HHP ACC', 'HOME APPLIANCE', 'SMART HOME DEVICES', 'VD-VPS PRODUCT'}
        condition3 = df['category_lv3'].isin(CATEGORY3_KR_TARGETS)
        condition2 = df['category_lv2'].isin(CATEGORY2_KR_TARGETS)
        
        df.loc[condition3 | condition2, 'id'] += 100

    elif country_code == 'GB':
        CATEGORY3_GB_TARGETS = {'BESPOKE panels', 'Accessories'}
        CATEGORY2_GB_TARGETS = {'Computer Accessories', 'Display Accessories', 'Home Appliance Accessories', 'Mobile Accessories', 'Projector Accessories', 'SmartThings', 'TV Accessories', 'TV Audio Accessories'}
        condition3 = df['category_lv3'].isin(CATEGORY3_GB_TARGETS)
        condition2 = df['category_lv2'].isin(CATEGORY2_GB_TARGETS)
        
        df.loc[condition3 | condition2, 'id'] += 100

    return df

def get_model_code_extended(cmp, country_code, site_cd):
    full_table_nm = 'rubicon_data_product_category' if country_code == 'KR' else 'rubicon_data_uk_product_spec_basics'
    c_list = []
    if country_code == 'KR':
        n10_table = """select 
                            product_category_lv1, 
                            product_category_lv2, 
                            product_category_lv3, 
                            mdl_code, 
                            goods_nm, 
                            release_date, 
                            site_cd, 
                            set_tp_cd 
                        from rubicon_data_product_category
                        union all
                        select 
                            product_category_lv1, 
                            product_category_lv2, 
                            product_category_lv3, 
                            mdl_code, 
                            goods_nm, 
                            release_date, 
                            site_cd, 
                            set_tp_cd
                        from rubicon_data_prd_mst_hist"""
    else:
        n10_table = """select 
                            category_lv1, 
                            category_lv2,
                            category_lv3,
                            model_code,
                            display_name,
                            launch_date,
                            site_cd
                        from rubicon_data_uk_product_spec_basics 
                        union all
                        select 
                            category_lv1, 
                            category_lv2,
                            category_lv3,
                            model_code,
                            display_name,
                            launch_date,
                            site_cd
                        from rubicon_data_uk_product_spec_basics_hist"""
    category_lv1 = cmp.get('category_lv1', "")
    category_lv2 = cmp.get('category_lv2', "")
    category_lv3 = cmp.get('category_lv3', "")
    mapping_code = cmp.get('mapping_code', "")

    category_lv1_placeholder = ", ".join(
                            "'" + _ + "'" for _ in cmp.get("category_lv1", "")
                        )
    category_lv2_placeholder = ", ".join(
                    "'" + _ + "'" for _ in cmp.get("category_lv2", "")
                )
    category_lv3_placeholder = ", ".join(
                    "'" + _ + "'" for _ in cmp.get("category_lv3", "")
                )
    mdl_placeholder = ", ".join(
                    "'" + _ + "'" for _ in list(set(cmp.get("mapping_code", "")))
                )
    
    with connection.cursor() as curs:
        query = f"""
                SELECT
                    {'product_category_lv1' if country_code == 'KR' else 'category_lv1'}, 
                    {'product_category_lv2' if country_code == 'KR' else 'category_lv2'}, 
                    {'product_category_lv3' if country_code == 'KR' else 'category_lv3'}, 
                    {'mdl_code' if country_code == 'KR' else 'model_code'}, 
                    {'goods_nm' if country_code == 'KR' else 'display_name'}, 
                    {'release_date' if country_code == 'KR' else 'launch_date'} as release_date
                FROM ({n10_table})
                --FROM {full_table_nm}
                WHERE site_cd = '{site_cd}'
                AND {'mdl_code' if country_code == 'KR' else 'model_code'} in ({mdl_placeholder})
                """
        
        curs.execute(query)
        result_c = curs.fetchall()
        for row in result_c:
            category_lv1, category_lv2, category_lv3, model_code, goods_nm, release_date = row
            c_list.append({
                    "mapping_code": goods_nm,
                    "category_lv1": category_lv1,
                    "category_lv2": category_lv2,
                    "category_lv3": category_lv3,
                    "edge": "recommend",
                    "meta": '',
                    'extended_info': [model_code],
                    "id": 0,
                    "expression": model_code
                })
        return c_list

def extract_watch_category(goods_nm):
   if pd.isna(goods_nm):
       return None
      
   patterns = [
       (r'Watch(\d+) Classic', lambda m: f'Watch{m.group(1)} Classic'),
       (r'Watch(\d+) Pro', lambda m: f'Watch{m.group(1)} Pro'),
       (r'Watch Ultra', lambda m: 'Watch Ultra'),
       (r'Watch FE', lambda m: 'Watch FE'),
       (r'Watch(\d+)', lambda m: f'Watch{m.group(1)}')
   ]
   
   for pattern, formatter in patterns:
       match = re.search(pattern, goods_nm)
       if match:
           return formatter(match)
   
   return None  

def extract_mm_value(value):
    if pd.isna(value):
        return None
    
    match = re.search(r'\((\d+(?:\.\d+)?)mm\)', value)
    if match:
        mm_number = match.group(1)
        return f'{mm_number} mm'
    else:
        return None