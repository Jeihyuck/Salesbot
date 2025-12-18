import sys

sys.path.append("/www/alpha/")

from pydantic import BaseModel

from apps.rubicon_v3.__function.__prompts import session_title_prompt
from apps.rubicon_v3.__function import __llm_call, __utils


class SessionTitle(BaseModel):
    session_title: str


def session_title_generation(
    main_query,
    files,
    language,
    model_name="gpt-4.1-mini",
):
    """
    세션 제목을 생성하는 함수
    """
    prompt = session_title_prompt.PROMPT

    # 시스템 프롬프트로 메시지 초기화
    messages = [{"role": "system", "content": [{"type": "text", "text": prompt}]}]

    # 성공적으로 처리된 모든 이미지를 수집
    processed_images = []
    for file in files:
        try:
            image_dict = __utils.process_image_file(file)
            processed_images.append(image_dict)
        except Exception as e:
            print(f"Error processing image {file.name}: {str(e)}")
            continue

    # 이미지와 텍스트를 포함한 사용자 메시지 생성
    user_content = []

    # 이미지가 있는 경우 먼저 추가
    if processed_images:
        user_content.extend(processed_images)

    # 텍스트 콘텐츠 추가
    user_prompt = f"""User Query: {main_query}
Language: {language}"""
    user_content.append({"type": "text", "text": user_prompt})

    # 완성된 사용자 메시지 추가
    messages.append({"role": "user", "content": user_content})

    response = __llm_call.open_ai_call_structured(
        model_name, messages, SessionTitle, 0.01, 0.1, 42
    )

    return response
