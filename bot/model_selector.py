import random
from groq import Groq
import config

def get_client():
    api_key = random.choice(config.VALID_KEYS)
    return Groq(api_key=api_key)

def get_dynamic_model(client):
    """
    [완전 동적 방식]
    반드시 '문자열(String)' 하나만 반환합니다. 절대 리스트를 반환하지 않습니다.
    """
    try:
        models = client.models.list()
        
        BANNED_MODELS = [
            "meta-llama/llama-4-maverick-17b-128e-instruct"
        ]

        text_models = [
            m.id for m in models.data 
            if 'whisper' not in m.id 
            and 'vision' not in m.id 
            and 'llava' not in m.id
            and 'guard' not in m.id
            and m.id not in BANNED_MODELS
        ]
        
        if not text_models:
            # 만약 API가 비어있으면 안전한 기본값 강제 리턴
            return "llama-3.1-8b-instant"

        # [절대 규칙] 리스트의 0번째 요소(문자열)만 반환
        return text_models

    except Exception as e:
        print(f"⚠️ Model Selection Error: {e}")
        # 에러 발생 시에도 안전한 기본값 리턴 (멈춤 방지)
        return "llama-3.1-8b-instant"
