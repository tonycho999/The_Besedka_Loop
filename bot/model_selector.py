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
    2. 중단 예정인 특정 모델(Llama 4 Maverick 17B) 제외
    3. 남은 것 중 첫 번째 텍스트 모델 반환
    """
    try:
        # 1. Groq 서버에 현재 사용 가능한 모델 목록 요청
        models = client.models.list()
        
        # [설정] 제외할 모델의 정확한 ID 리스트 (정확히 일치하는 것만 제외)
        BANNED_MODELS = [
            "meta-llama/llama-4-maverick-17b-128e-instruct"  # 2026-03-09 중단 예정
        ]

        # 2. 텍스트 모델만 남기기
        text_models = [
            m.id for m in models.data 
            if 'whisper' not in m.id 
            and 'vision' not in m.id 
            and 'llava' not in m.id
            and m.id not in BANNED_MODELS  # [수정] 특정 모델명만 정확히 제외
        ]
        
        if not text_models:
            raise Exception("Groq API에서 텍스트 모델을 찾을 수 없습니다.")

        # 3. 디버깅용: 필터링 후 남은 모델들 출력
        print(f"📋 API Loaded Models (Filtered): {text_models}")

        # 4. 리스트의 첫 번째 모델 선택 (가장 최신일 확률 높음)
        selected_model = text_models
        
        return selected_model

    except Exception as e:
        print(f"⚠️ Model Selection Error: {e}")
        raise e
