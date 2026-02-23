import os
import random
import time
import datetime
import base64
from github import Github
from groq import Groq

# --- 설정 ---
REPO_NAME = "tonycho999/The_Besedka_Loop"  # 본인 저장소 이름 확인!
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")

# 페르소나 데이터 (기존과 동일)
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

def generate_text(persona, prompt_type="post", context=""):
    client = Groq(api_key=GROQ_API_KEY)
    
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
        return client.chat.completions.create(messages=[{"role": "user", "content": sys_prompt}], model="llama3-70b-8192").choices[0].message.content.strip(), topic

    elif prompt_type == "comment":
        sys_prompt = f"""
        You are {persona['name']}. Your friend wrote a post about: "{context}".
        Write a short, natural comment (1 sentence).
        Style: {persona['style']}.
        Language: English or {persona['lang']}.
        """
        return client.chat.completions.create(messages=[{"role": "user", "content": sys_prompt}], model="llama3-70b-8192").choices[0].message.content.strip(), ""

def update_last_post_with_comments(repo):
    """가장 최근 글을 찾아 댓글을 달아주는 함수"""
    try:
        # 1. 블로그 폴더의 파일 목록 가져오기
        contents = repo.get_contents("src/pages/blog")
        md_files = [c for c in contents if c.name.endswith('.md')]
        
        if not md_files:
            return

        # 2. 이름순 정렬 (YYYY-MM-DD 포맷이라 이름순=최신순)
        last_file = sorted(md_files, key=lambda x: x.name)[-1]
        
        # 3. 파일 내용 읽기
        file_content = last_file.decoded_content.decode("utf-8")
        
        # 이미 댓글이 있으면 패스
        if "class=\"comment-box\"" in file_content:
            print(f"Skipping comments: {last_file.name} already has them.")
            return

        # 4. 작성자 찾기 (본인이 본인 글에 댓글 달면 안 되니까)
        current_author_line = [line for line in file_content.split('\n') if "author:" in line]
        current_author_name = "Unknown"
        if current_author_line:
            current_author_name = current_author_line[0].split('"')[1]

        # 5. 댓글 작성자 2명 선정 (작성자 제외)
        candidates = [p for p in PERSONAS if p['name'] != current_author_name]
        commenters = random.sample(candidates, 2)
        
        # 6. 댓글 생성 및 HTML 조립
        comments_html = '\n\n<div class="comment-box"><h3>💬 Alumni Comments</h3>'
        
        # 포스트 주제 추측 (제목 라인)
        post_title = file_content.split('\n')[2].replace('title:', '').strip()

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
        
        # 7. 파일 업데이트 (기존 내용 + 댓글)
        new_content = file_content + comments_html
        repo.update_file(last_file.path, f"Add comments to {last_file.name}", new_content, last_file.sha, branch="main")
        print(f"Updated comments for: {last_file.name}")
        
    except Exception as e:
        print(f"Comment update failed: {e}")

def main():
    print("--- Bot Started ---")

    # 1. [확률] 하루 14회 목표 (58% 실행)
    if random.random() > 0.58:
        print("Skipping execution (Random probability check).")
        return

    # 2. [대기] 0~30분 사이 100ms 단위 랜덤 대기
    # 30분 = 1800초 = 18000 * 100ms
    delay_units = random.randint(0, 18000)
    delay_seconds = delay_units / 10.0  # 예: 1234.5초
    
    print(f"Sleeping for {delay_seconds} seconds...")
    time.sleep(delay_seconds)

    # 3. GitHub 연결
    g = Github(GITHUB_TOKEN)
    repo = g.get_repo(REPO_NAME)

    # 4. [선행 작업] 이전 글에 댓글 달기
    update_last_post_with_comments(repo)

    # 5. [메인 작업] 새 글 작성 (댓글 없이)
    persona = random.choice(PERSONAS)
    print(f"Selected Persona for new post: {persona['name']}")
    
    title, body, topic = generate_text(persona, "post")
    
    # 이미지 생성 URL
    image_prompt = f"{topic}, {persona['country']} vibe, cinematic lighting, 4k"
    image_url = f"https://image.pollinations.ai/prompt/{image_prompt.replace(' ', '%20')}?width=800&height=400&nologo=true"
    
    date_str = datetime.datetime.now().strftime("%Y-%m-%d")
    
    # 마크다운 조립 (댓글 섹션 없음!)
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

    # 6. 파일 업로드
    file_name = f"src/pages/blog/{date_str}-{persona['id']}-{random.randint(1000,9999)}.md"
    try:
        repo.create_file(file_name, f"New post by {persona['name']}", md_content, branch="main")
        print(f"Successfully created post: {file_name}")
    except Exception as e:
        print(f"Error creating post: {e}")

if __name__ == "__main__":
    main()
