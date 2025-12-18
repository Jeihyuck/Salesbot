import re
import json
import datetime
import sys
sys.stdout.reconfigure(encoding="utf-8")

import psycopg2


def merge_sentences(text):
    """여러 문장들을 정리하여 각각 새 줄로 구분"""
    # Replace multiple spaces and newlines with a single space
    cleaned_text = text.replace("\n", " ").replace("  ", " ")
    # Split by full stop (or other sentence delimiters) and rejoin with a newline
    sentences = cleaned_text.split(". ")
    # result = ".\n".join(sentence.strip() for sentence in sentences if sentence.strip())
    result = ".\n".join(sentence.strip().replace("  ", " ").replace(" ----", "----").replace("---- ", "----") for sentence in sentences)
    return result


def hypen_checker(text):
    """하이픈 구분선을 찾아 앞뒤로 줄바꿈 추가"""
    # Match sequences of 4 or more dashes and add newlines around them
    converted_text = re.sub(r'-{4,}', lambda match: f"\n{match.group()}\n", text)
    return converted_text.strip()


filter_target = [
	'javascript:', 
	'[본문 바로가기](#container)', 
	'일주일 그만보기', 
	'구매 고객님께 드리는  ', 
	'지금 신청하세요!  ', 
	'**갤럭시 캠퍼스 회원**이시네요!', 
	'오리지널 콘텐츠, 더 풍성해진 커뮤니티까지!  ', 
	'**새로워진 갤럭시 캠퍼스**', 
	'제품 검색', 
	'제품 검색', 
	'통합 검색', 
	'#### 최근 검색어', 
	'#### 추천 제품', 
	'고객님의 최근 본 제품과 연관된 제품을 추천해 드려요!', 
	'#### 맞춤 이벤트', 
	'고객님의 최근 본 제품과 연관된 이벤트를 추천해 드려요!', 
	'#### 인기 검색어', 
	'#### 상품 바로가기',
    '수 있습니다.',
    '### 상품평',
    '#### 스토어 상담 예약 서비스',
    '대상 모델 :',
    '[삼성계정을'
]

def image_description_filter(str):
    """이미지 관련 설명문구 필터링"""
    condition = False
    if '해당' in str:
        condition = True
    if '연출' in str:
        condition = True

    if condition:
        if '이미지' in str:
            return ''
    else:
        return str

def filter_text(str):
    """지정된 필터 단어(filter_target)가 포함된 텍스트 제거"""
    if str != None:
        for filter in filter_target:
            if filter in str:
                return ''
        return str
    else:
        return ''
    
def text_cleaner(text):
    """텍스트 정제: 문장 병합, 구분선 처리, 중복/이미지 설명 제거"""
    rearranged_text = merge_sentences(text)
    rearranged_text = hypen_checker(rearranged_text)
    new_document_list = []
    for line in rearranged_text.splitlines():
        if '-----' in line:
            new_document_list.append(line)
        else:
            if line not in new_document_list:
                checked_line = filter_text(image_description_filter(line))
                if checked_line != None:
                    new_document_list.append(checked_line)

    new_document_list = [line for i, line in enumerate(new_document_list) if i == 0 or line != new_document_list[i - 1]]
    new_document = '\n'.join(new_document_list)

    return new_document
