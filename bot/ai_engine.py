import random
from groq import Groq
import config

def get_client():
    api_key = random.choice(config.VALID_KEYS)
    return Groq(api_key=api_key)

def get_dynamic_model(client):
    """
    [최적화된 선택 로직]
    표준 채팅 응답을 주지 않는 모델(Audio, Vision, Guard, Compound 등)을 철저히 배제합니다.
    """
    try:
        models = client.models.list()
        
        for m in models.data:
            mid = m.id
            
            # 채팅용이 아닌 모델 거르기
            # whisper(음성), vision/llava(시각), guard(보안)
            # compound(비표준 응답 발생 모델) <- 이번 에러의 주범!
            if 'whisper' in mid or 'vision' in mid or 'llava' in mid or 'guard' in mid or 'compound' in mid:
                continue
            
            # 중단 예정 모델 제외
            if "llama-4-maverick-17b-128e-instruct" in mid:
                continue
            
            # 검증된 모델 발견 시 즉시 반환
            return str(mid)
            
        # 모델이 없으면 가장 안전한 기본값
        print("⚠️ No suitable model found, using default.")
        return "llama-3.1-8b-instant"

    except Exception as e:
        print(f"⚠️ Model Selection Error: {e}")
        return "llama-3.1-8b-instant"
