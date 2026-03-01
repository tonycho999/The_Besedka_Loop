import random
from groq import Groq
import config

def get_client():
    api_key = random.choice(config.VALID_KEYS)
    return Groq(api_key=api_key)

def get_dynamic_model(client):
    """
    [수정됨] 리스트 반환 원천 봉쇄.
    무조건 문자열(String) 하나만 반환합니다.
    """
    try:
        models = client.models.list()
        
        # 제외할 모델
        BANNED_MODELS = [
            "meta-llama/llama-4-maverick-17b-128e-instruct"
        ]

        # 텍스트 모델 필터링
        text_models = [
            m.id for m in models.data 
            if 'whisper' not in m.id 
            and 'vision' not in m.id 
            and 'llava' not in m.id
            and 'guard' not in m.id
            and m.id not in BANNED_MODELS
        ]
        
        # 모델이 없으면 기본값
        if not text_models:
            return "llama-3.1-8b-instant"

        # [핵심] 절대 리스트를 리턴하지 않음. 0번째 요소(문자열)만 리턴.
        selected_model = text_models
        return str(selected_model)

    except Exception as e:
        print(f"⚠️ Model Selection Error: {e}")
        return "llama-3.1-8b-instant"
