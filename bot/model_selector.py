import random
from groq import Groq
import config

def get_client():
    api_key = random.choice(config.VALID_KEYS)
    return Groq(api_key=api_key)

def get_dynamic_model(client):
    """
    [최적화된 선택 로직]
    1. 글쓰기 기능이 없는 모델(오디오, 비디오 등)은 제외합니다. (에러 방지)
    2. 중단 예정인 특정 Maverick 모델 하나만 정확히 제외합니다.
    3. 조건에 맞는 모델을 찾으면 '즉시 문자열로 반환'합니다. (리스트 에러 원천 봉쇄)
    """
    try:
        models = client.models.list()
        
        for m in models.data:
            mid = m.id
            
            # 글을 못 쓰는 모델들은 거릅니다 (얘네가 뽑히면 봇이 죽습니다)
            # - whisper: 듣기 평가용 (글 못 씀)
            # - vision / llava: 그림 보기용 (글 못 씀)
            # - guard: 욕설 필터링용 (글 안 써줌)
            if 'whisper' in mid or 'vision' in mid or 'llava' in mid or 'guard' in mid:
                continue
            
            # 형님이 지적하신 '중단 예정 모델' 딱 하나만 제외 (핀셋 제거)
            if "llama-4-maverick-17b-128e-instruct" in mid:
                continue
            
            # 위 조건을 다 통과한 녀석이 나오면 바로 채택!
            # 여기서 바로 return을 때려버리기 때문에 '리스트'가 섞일 틈이 없습니다.
            # print(f"✅ Selected Model: {mid}")  # 디버깅용
            return str(mid)
            
        # 만약 쓸만한 모델이 하나도 없으면 기본값
        print("⚠️ No suitable model found, using default.")
        return "llama-3.1-8b-instant"

    except Exception as e:
        print(f"⚠️ Model Selection Error: {e}")
        return "llama-3.1-8b-instant"
