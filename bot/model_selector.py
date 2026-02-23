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
    코드에 모델명을 명시하지 않습니다.
    API가 반환하는 모델 리스트 중 '음성(whisper)'과 '비전(vision)' 모델만 제외하고,
    사용 가능한 첫 번째 텍스트 모델을 즉시 반환합니다.
    """
    try:
        # 1. Groq 서버에 현재 사용 가능한 모델 목록 요청
        models = client.models.list()
        
        # 2. 텍스트 모델만 남기기 (오디오/이미지 전용 모델 제외)
        text_models = [
            m.id for m in models.data 
            if 'whisper' not in m.id 
            and 'vision' not in m.id 
            and 'llava' not in m.id
        ]
        
        if not text_models:
            raise Exception("Groq API에서 텍스트 모델을 찾을 수 없습니다.")

        # 3. 디버깅용: 어떤 모델들이 있는지 콘솔에 출력 (선택 과정 투명화)
        print(f"📋 API Loaded Models: {text_models}")

        # 4. 리스트의 첫 번째 모델을 무조건 선택 (가장 최신이거나 추천 모델일 확률 높음)
        selected_model = text_models[0]
        
        return selected_model

    except Exception as e:
        print(f"⚠️ Model Selection Error: {e}")
        # API 호출 실패 시 에러를 발생시켜 봇이 멈추거나 재시도하게 함 (임의 지정 X)
        raise e
