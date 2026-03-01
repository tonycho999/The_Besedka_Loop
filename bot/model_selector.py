import random
from groq import Groq
import config

def get_client():
    api_key = random.choice(config.VALID_KEYS)
    return Groq(api_key=api_key)

def get_dynamic_model(client):
    """
    [최적화된 선택 로직]
    1. 채팅 불가 모델(Audio, Vision, Guard) 제외
    2. 비표준 응답 모델(Compound) 제외
    3. 약관 동의 필요 모델(Canopylabs) 제외 <--- [NEW]
    4. 중단 예정 모델(Maverick) 제외
    """
    try:
        models = client.models.list()
        
        for m in models.data:
            mid = m.id
            
            # 채팅용이 아니거나 에러를 유발하는 모델군 필터링
            # - whisper: 음성용
            # - vision / llava: 이미지용
            # - guard: 보안용
            # - compound: 비표준 응답(리스트) 이슈
            # - canopylabs: 웹에서 약관 동의(Terms Accept)를 해야만 API 사용 가능
            if ('whisper' in mid or 
                'vision' in mid or 
                'llava' in mid or 
                'guard' in mid or 
                'compound' in mid or 
                'canopylabs' in mid):  # <--- [여기가 핵심 추가입니다]
                continue
            
            # 중단 예정 모델 제외
            if "llama-4-maverick-17b-128e-instruct" in mid:
                continue
            
            # 안전한 모델 발견 시 즉시 반환
            return str(mid)
            
        # 모델이 없으면 가장 안전한 기본값
        print("⚠️ No suitable model found, using default.")
        return "llama-3.1-8b-instant"

    except Exception as e:
        print(f"⚠️ Model Selection Error: {e}")
        return "llama-3.1-8b-instant"
