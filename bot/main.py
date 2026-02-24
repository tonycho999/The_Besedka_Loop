import os
import random
import datetime
from groq import Groq
from github import Github
from dotenv import load_dotenv
import config

# .env 파일 로드 (로컬 테스트용)
load_dotenv()

def get_groq_client():
    """유효한 API 키 중 하나를 랜덤 선택하여 클라이언트 생성"""
    if not config.VALID_KEYS:
        raise ValueError("❌ 유효한 GROQ_API_KEY가 없습니다. 환경변수를 확인하세요.")
    
    selected_key = random.choice(config.VALID_KEYS)
    return Groq(api_key=selected_key)

def get_dynamic_model(client):
    """
    [중요] 모델명을 하드코딩하지 않습니다.
    API를 통해 사용 가능한 모델 리스트를 조회하고, 그 중 하나를 선택합니다.
    """
    try:
        models = client.models.list()
        # 사용 가능한 모델 ID 추출
        available_models = [m.id for m in models.data if 'whisper' not in m.id] # Whisper(음성) 모델 제외
        
        if not available_models:
            raise Exception("사용 가능한 텍스트 모델을 찾을 수 없습니다.")

        # 리스트 중 첫 번째 혹은 랜덤 선택 (여기서는 안정성을 위해 리스트의 첫 번째 모델 선택)
        # 필요하다면 random.choice(available_models)로 변경 가능
        selected_model = available_models[0]
        
        print(f"✅ 조회된 모델 리스트: {available_models}")
        print(f"🚀 선택된 모델: {selected_model}")
        
        return selected_model
    except Exception as e:
        print(f"⚠️ 모델 조회 중 오류 발생: {e}")
        # 만약 API 조회가 실패할 경우를 대비한 최후의 보루 (이 부분은 실행되지 않기를 기대합니다)
        return "llama3-70b-8192"

def generate_conversation():
    client = get_groq_client()
    model_id = get_dynamic_model(client) # 동적 모델 할당

    # 1. 랜덤 요소 선택
    topic = random.choice(config.DAILY_TOPICS)
    participants = random.sample(config.PERSONAS, 2)
    p1, p2 = participants[0], participants[1]

    print(f"🎨 주제: {topic}")
    print(f"🗣️ 참여자: {p1['name']} ({p1['country']}) vs {p2['name']} ({p2['country']})")

    # 2. 프롬프트 작성
    system_prompt = f"""
    You are a scriptwriter for a developer community log.
    Write a short, casual conversation (about 6-8 lines) between two characters.
    
    Topic: {topic}
    
    Character 1: {p1['name']} ({p1['role']}). Personality: {p1['style']}. Native Language: {p1['lang']}.
    Character 2: {p2['name']} ({p2['role']}). Personality: {p2['style']}. Native Language: {p2['lang']}.
    
    Format:
    - {p1['name']}: [Line]
    - {p2['name']}: [Line]
    ...
    
    Keep it short, engaging, and reflect their personalities. 
    They can mix English with a little bit of their native language greetings or exclamations.
    """

    # 3. Groq API 호출
    completion = client.chat.completions.create(
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Create a conversation about '{topic}'."}
        ],
        model=model_id,
        temperature=0.7,
    )

    content = completion.choices[0].message.content
    return topic, p1, p2, content

def format_markdown(topic, p1, p2, content):
    """결과물을 마크다운 형식으로 변환"""
    date_str = datetime.datetime.now().strftime("%Y-%m-%d")
    
    md_output = f"""# 📅 {date_str} - Daily Chat Log

## 💡 Topic: {topic}
**Participants:**
* **{p1['name']}** ({p1['role']}, {p1['country']})
* **{p2['name']}** ({p2['role']}, {p2['country']})

---

### 💬 Conversation
{content}

---
"""
    # [광고 로직] config.AD_MODE가 True일 때만 광고 추가
    if config.AD_MODE:
        ad = random.choice(config.PROMOTED_SITES)
        ad_block = f"""
> **Sponsored**: [{ad['desc']}]({ad['url']})
"""
        md_output += ad_block

    return md_output, date_str

def push_to_github(file_name, content):
    """GitHub 리포지토리에 파일 업로드"""
    if not config.GITHUB_TOKEN:
        print("⚠️ GITHUB_TOKEN이 없습니다. 로컬에만 출력합니다.")
        print("="*20 + "\n" + content + "\n" + "="*20)
        return

    try:
        g = Github(config.GITHUB_TOKEN)
        repo = g.get_repo(config.REPO_NAME)
        
        # logs 폴더 안에 저장 (없으면 생성됨)
        path = f"logs/{file_name}"
        
        repo.create_file(
            path=path,
            message=f"Add chat log: {file_name}",
            content=content,
            branch="main" 
        )
        print(f"✅ GitHub 업로드 완료: https://github.com/{config.REPO_NAME}/blob/main/{path}")
        
    except Exception as e:
        print(f"❌ GitHub 업로드 실패: {e}")

if __name__ == "__main__":
    try:
        # 1. 대화 생성
        topic, p1, p2, chat_content = generate_conversation()
        
        # 2. 포맷팅
        final_md, date_str = format_markdown(topic, p1, p2, chat_content)
        
        # 3. 파일명 생성 (예: 2024-05-20_debugging_nightmare.md)
        safe_topic = topic.replace(" ", "_")
        file_name = f"{date_str}_{safe_topic}.md"
        
        # 4. GitHub 푸시 (또는 로컬 출력)
        push_to_github(file_name, final_md)
        
    except Exception as e:
        print(f"🔥 치명적인 오류 발생: {e}")
