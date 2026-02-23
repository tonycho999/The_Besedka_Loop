import os
import random
import time
import datetime
from github import Github, Auth
from groq import Groq

# --- 설정 ---
REPO_NAME = "tonycho999/The_Besedka_Loop"  # 본인 저장소 이름
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")

# [핵심] 4개의 키 중 유효한 것만 리스트에 담기
API_KEYS = [
    os.environ.get("GROQ_API_KEY_1"),
    os.environ.get("GROQ_API_KEY_2"),
    os.environ.get("GROQ_API_KEY_3"),
    os.environ.get("GROQ_API_KEY_4")
]
VALID_KEYS = [k for k in API_KEYS if k is not None]

if not VALID_KEYS:
    print("Error: No Groq API keys found!")
    exit(1)

# 페르소나 데이터
PERSONAS = [
    {"id": "jinwoo", "name": "Jin-woo", "country": "Korea", "role": "DevOps", "style": "cynical but warm, loves soju", "lang": "Korean"},
    {"id": "kenji", "name": "Kenji", "country": "Japan", "role": "Frontend", "style": "polite, nostalgic", "lang": "Japanese"},
    {"id": "wei", "name": "Wei", "country": "China", "role": "AI Dev", "style": "ambitious, tech-focused", "lang": "Chinese"},
    {"id": "budi", "name": "Budi", "country": "Indonesia", "role": "Backend", "style": "relaxed, loves coffee", "lang": "Indonesian"},
    {"id": "carlos", "name": "Carlos", "country": "Spain", "role": "Mobile App", "style": "passionate, loud", "lang": "Spanish"},
    {"id": "lena", "name": "Lena", "country": "Germany", "role": "Web Dev", "style": "logical, direct", "lang": "German"},
    {"id": "amelie", "name": "Amélie", "country": "France", "role": "UI/UX", "style": "artistic, poetic", "lang": "French"},
    {"id": "hina", "name": "Hina", "country": "Japan", "role": "Illustrator", "style": "cute, emotional", "lang": "Japanese"},
    {"id": "sarah", "name": "Sarah", "country": "Korea", "role": "Graphic Des", "style": "trendy, hip", "lang": "Korean"},
    {"id": "marco", "name": "Marco", "country": "France", "role": "Publisher", "style": "gourmet, perfectionist", "lang": "French"},
]

TOPICS = [
    "debugging nightmare", "unexpected rain", "new framework released", 
    "missing the team", "client request", "delicious local food",
    "laptop died", "coding trick", "late night inspiration", "server crash"
]

def get_groq_client():
    """4개의 키 중 하나를 랜덤으로 뽑아 클라이언트 생성"""
    selected_key = random.choice(VALID_KEYS)
    print(f"Using API Key ending in ...{selected_key[-4:]}")
    return Groq(api_key=selected_key)

def get_best_available_model(client):
    """
    [핵심 기능]
    Groq API에 '지금 사용 가능한 모델 목록'을 요청한 뒤,
    텍스트 생성에 가장 적합한 모델을 자동으로 선택합니다.
    특정 모델명을 하드코딩하지 않으므로 단종 이슈에서 안전합니다.
    """
    try:
        models = client.models.list()
        # 사용 가능한 모델 ID 목록 추출
        available_models = [m.id for m in models.data]
        
        # 음성 인식 모델(whisper) 등 텍스트 생성이 아닌 모델 제외
        text_models = [m for m in available_models if 'whisper' not in m and 'vision' not in m]
        
        if not text_models:
            print("No text models found via API.")
            return None

        # 우선순위 로직: 성능 좋은(70b) -> 최신(llama-3) 순으로 검색
        # 1순위: '70b'가 포함된 모델 (고성능)
        for m in text_models:
            if '70b' in m:
                print(f"Auto-selected High Performance Model: {m}")
                return m
        
        # 2순위: 'llama-3'가 포함된 모델 (최신)
        for m in text_models:
            if 'llama-3' in m:
                print(f"Auto-selected Llama-3 Model: {m}")
                return m

        # 3순위: 아무거나 첫 번째 텍스트 모델
        selected = text_models[0]
        print(f"Auto-selected Fallback Model: {selected}")
        return selected

    except Exception as e:
        print(f"Failed to fetch model list: {e}")
        # API 호출 실패 시 비상용 하드코딩 (이 경우는 어쩔 수 없음)
        return "llama-3.3-70b-versatile"

def generate_text(persona, prompt_type="post", context=""):
    client = get_groq_client()
    
    # [변경] 모델명을 직접 쓰지 않고 함수를 통해 받아옴
    current_model = get_best_available_model(client)
    
    if prompt_type == "post":
        topic = random.choice(TOPICS)
        sys_prompt = f"""
        You are {persona['name']}, a {persona['role']} in {persona['country']}.
        Write a short blog post (100-150 words) about: "{topic}".
        Style: {persona['style']}.
        Language: Mixed {persona['lang']} (70%) and English (30%).
        Format: First line is Title, then blank line, then Body.
        NO introductory text.
        """
        return client.chat.completions.create(messages=[{"role": "user", "content": sys_prompt}], model=current_model).choices[0].message.content.strip(), topic

    elif prompt_type == "comment":
        sys_prompt = f"""
        You are {persona['name']}. Your friend wrote a post about: "{context}".
        Write a short, natural comment (1 sentence).
        Style: {persona['style']}.
        Language: English or {persona['lang']}.
        """
        return client.chat.completions.create(messages=[{"role": "user", "content": sys_prompt}], model=current_model).choices[0].message.content.strip(), ""

def update_last_post_with_comments(repo):
    """가장 최근 글(아직 댓글 없는)을 찾아 댓글 달기"""
    try:
        contents = repo.get_contents("src/pages/blog")
        md_files = [c for c in contents if c.name.endswith('.md')]
        
        if not md_files:
            return

        # 최신순 정렬
        last_file = sorted(md_files, key=lambda x: x.name)[-1]
        
        file_content = last_file.decoded_content.decode("utf-8")
        
        # 이미 댓글 있으면 패스
        if "class=\"comment-box\"" in file_content:
            print(f"Skipping comments: {last_file.name} already has them.")
            return

        # 작성자 확인
        current_author_line = [line for line in file_content.split('\n') if "author:" in line]
        current_author_name = "Unknown"
        if current_author_line:
            current_author_name = current_author_line[0].split('"')[1]

        # 댓글 멤버 선정
        candidates = [p for p in PERSONAS if p['name'] != current_author_name]
        commenters = random.sample(candidates, 2)
        
        comments_html = '\n\n<div class="comment-box"><h3>💬 Alumni Comments</h3>'
        
        # 주제 파악
        post_title = "Daily Life"
        for line in file_content.split('\n'):
            if line.startswith("title:"):
                post_title = line.replace('title:', '').replace('"', '').strip()
                break

        for c in commenters:
            msg, _ = generate_text(c, "comment", post_title)
            comments_html += f"""
<div class="comment">
  <img src="https://api.dicebear.com/7.x/avataaars/svg?seed={c['id']}" class="avatar">
  <div class="bubble">
    <strong>{c['name']} ({c['country']})</strong>
    <p>{msg.replace('"', '')}</p>
  </div>
</div>
"""
        comments_html += '</div>'
        
        new_content = file_content + comments_html
        repo.update_file(last_file.path, f"Add comments to {last_file.name}", new_content, last_file.sha, branch="main")
        print(f"Updated comments for: {last_file.name}")
        
    except Exception as e:
        print(f"Comment update failed: {e}")

def main():
    print("--- Bot Started ---")

    # [테스트용] 확률 체크 해제 상태 (배포 시 필요하면 주석 해제하세요)
    # if random.random() > 0.58:
    #     print("Skipping execution (Random probability check).")
    #     return

    # 2. [대기] 0.1초 단위 정밀 랜덤 대기 (0~30분)
    delay_units = random.randint(0, 18000)
    delay_seconds = delay_units / 10.0
    
    print(f"Sleeping for {delay_seconds} seconds...")
    time.sleep(delay_seconds)

    # 3. GitHub 연결
    auth = Auth.Token(GITHUB_TOKEN)
    g = Github(auth=auth)
    repo = g.get_repo(REPO_NAME)

    # 4. 이전 글 댓글 달기
    update_last_post_with_comments(repo)

    # 5. 새 글 작성
    persona = random.choice(PERSONAS)
    print(f"Selected Persona for new post: {persona['name']}")
    
    title, body, topic = generate_text(persona, "post")
    
    image_prompt = f"{topic}, {persona['country']} vibe, cinematic lighting, 4k"
    image_url = f"https://image.pollinations.ai/prompt/{image_prompt.replace(' ', '%20')}?width=800&height=400&nologo=true"
    
    date_str = datetime.datetime.now().strftime("%Y-%m-%d")
    
    md_content = f"""---
layout: ../../layouts/BlogPostLayout.astro
title: "{title.replace('"', "'")}"
author: "{persona['name']}"
date: "{date_str}"
image: "{image_url}"
category: "Daily Log"
location: "{persona['country']}"
---

{body}
"""

    file_name = f"src/pages/blog/{date_str}-{persona['id']}-{random.randint(1000,9999)}.md"
    try:
        repo.create_file(file_name, f"New post by {persona['name']}", md_content, branch="main")
        print(f"Successfully created post: {file_name}")
    except Exception as e:
        print(f"Error creating post: {e}")

if __name__ == "__main__":
    main()
