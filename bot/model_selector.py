import random
from groq import Groq
import config

def get_client():
    api_key = random.choice(config.VALID_KEYS)
    return Groq(api_key=api_key)

def get_dynamic_model(client):
    """
    [Claude Code 솔루션]
    리스트를 생성하지 않고, 조건에 맞는 모델을 발견하는 즉시 반환(Early Return)합니다.
    이 방식은 리스트가 섞여 들어갈 가능성을 0%로 만듭니다.
    """
    try:
        models = client.models.list()
        
        # 제외할 키워드들
        BANNED_KEYWORDS = ['whisper', 'vision', 'llava', 'guard', 'maverick']

        # 모델 리스트를 순회하면서 조건 검사
        for m in models.data:
            mid = m.id
            
            # 1. 금지 키워드가 하나라도 있으면 패스
            if any(banned in mid for banned in BANNED_KEYWORDS):
                continue
            
            # 2. 조건에 맞으면 변수에 담거나 할 것 없이, 그 자리에서 즉시 리턴!
            # (이러면 리스트가 생성될 틈이 없습니다)
            print(f"✅ Selected Model: {mid}")
            return str(mid)
            
        # 반복문을 다 돌았는데도 없으면 기본값
        print("⚠️ No matching model found, using default.")
        return "llama-3.1-8b-instant"

    except Exception as e:
        print(f"⚠️ Model Selection Error: {e}")
        return "llama-3.1-8b-instant"
