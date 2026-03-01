import random
from groq import Groq
import config

def get_client():
    """
    config.VALID_KEYS에서 랜덤 키를 가져와 클라이언트 생성
    """
    api_key = random.choice(config.VALID_KEYS)
    return Groq(api_key=api_key)

def get_dynamic_model(client):
    """
    [완전 동적 방식]
    API가 반환하는 모델 리스트 중:
    1. 오디오(whisper), 비전(vision, llava) 모델 제외
    2. 보안용(guard) 및 중단 예정(maverick) 모델 제외
    3. 남은 것 중 '첫 번째 텍스트 모델(문자열)'만 반환
    """
    try:
        # 1. Groq 서버에 현재 사용 가능한 모델 목록 요청
        models = client.models.list()
        
        # [설정] 제외할 모델의 정확한 ID 리스트
        BANNED_MODELS = [
            "meta-llama/llama-4-maverick-17b-128e-instruct"  # 중단 예정
        ]

        # 2. 텍스트 모델만 남기기 (필터링 강화)
        text_models = [
            m.id for m in models.data 
            if 'whisper' not in m.id 
            and 'vision' not in m.id 
            and 'llava' not in m.id
            and 'guard' not in m.id      # [추가] 보안 검사용 모델 제외 (채팅 불가)
            and m.id not in BANNED_MODELS
        ]
        
        if not text_models:
            raise Exception("Groq API에서 텍스트 모델을 찾을 수 없습니다.")

        # [핵심 수정] 리스트 전체가 아니라, 0번째 요소(String) 하나만 선택!
        selected_model = text_models
        
        # 디버깅용 출력 (이제 리스트가 아니라 모델명 하나만 찍힐 것임)
        # print(f"👉 Final Selected Model: {selected_model}")
        
        return selected_model

    except Exception as e:
        print(f"⚠️ Model Selection Error: {e}")
        # 여기서 에러가 나면 봇이 멈추도록 예외를 던짐
        raise e
