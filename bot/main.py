import os
import random
import datetime
from github import Github
from groq import Groq

# --- 1. 설정 (Configuration) ---
REPO_NAME = "tonycho999/The_Besedka_Loop"  # 본인의 저장소 이름으로 변경하세요!
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")

# 10인의 페르소나 데이터 (성격, 말투, 국적)
PERSONAS = [
    {"id": "jinwoo", "name": "Jin-woo", "country": "Korea", "role": "DevOps", "style": "cynical but warm, loves soju, uses '...'", "lang": "Korean"},
    {"id": "kenji", "name": "Kenji", "country": "Japan", "role": "Frontend", "style": "polite, nostalgic, detail-oriented", "lang": "Japanese"},
    {"id": "wei", "name": "Wei", "country": "China", "role": "AI Dev", "style": "ambitious, tech-focused, energetic", "lang": "Chinese"},
    {"id": "budi", "name": "Budi", "country": "Indonesia", "role": "Backend", "style": "relaxed, loves coffee, optimistic", "lang": "Indonesian"},
    {"id": "carlos", "name": "Carlos", "country": "Spain", "role": "Mobile App", "style": "passionate, loud, football fan", "lang": "Spanish"},
    {"id": "lena", "name": "Lena", "country": "Germany", "role": "Web Dev", "style": "logical, direct, environmentalist", "lang": "German"},
    {"id": "amelie", "name": "Amélie", "country": "France", "role": "UI/UX", "style": "artistic, poetic, hates ugly UI", "lang": "French"},
    {"id": "hina", "name": "Hina", "country": "Japan", "role": "Illustrator", "style": "cute, uses emojis, emotional", "lang": "Japanese"},
    {"id": "sarah", "name": "Sarah", "country": "Korea", "role": "Graphic Des", "style": "trendy, hip, loves photography", "lang": "Korean"},
    {"id": "marco", "name": "Marco", "country": "France", "role": "Publisher", "style": "gourmet, proud, perfectionist", "lang": "French"},
]

TOPICS = [
    "debugging nightmare at 3 AM", "unexpected rain and coffee", "new framework released", 
    "missing the old office team", "client made a ridiculous request", "found a delicious local restaurant",
    "laptop battery died during meeting", "learned a new coding trick", "late night inspiration"
]

def generate_content(persona):
    client = Groq(api_key=GROQ_API_KEY)
    topic = random.choice(TOPICS)
    
    # 프롬프트: "너는 [이름]이다. [언어]로 [주제]에 대해 짧은 블로그 글을 써라."
    prompt = f"""
    You are {persona['name']}, a {persona['role']} living in {persona['country']}.
    Your personality is {persona['style']}.
    
    Write a short blog post (about 150 words) about: "{topic}".
    
    [Rules]
    1. Write PRIMARILY in {persona['lang']} (your native language).
    2. Mix in 1-2 sentences of English so global friends understand.
    3. Be natural, casual, and human-like.
    4. Start with a catchy title in English.
    5. Do NOT include any introductory text like "Here is the post". Just the title and body.
    6. Format: First line is Title, then a blank line, then the Body.
    """

    completion = client.chat.completions.create(
        messages=[{"role": "user", "content": prompt}],
        model="llama3-70b-8192",
    )
    
    content = completion.choices[0].message.content.strip()
    lines = content.split('\n')
    title = lines[0].replace("#", "").replace("*", "").strip()
    body = "\n".join(lines[1:]).strip()
    
    return title, body, topic

def create_fake_comments(current_author):
    # 본인이 아닌 다른 멤버 2명을 랜덤으로 뽑아 댓글 생성
    others = [p for p in PERSONAS if p['id'] != current_author['id']]
    commenters = random.sample(others, 2)
    
    html = '<div class="comment-box"><h3>💬 Alumni Comments</h3>'
    
    for c in commenters:
        # 간단한 랜덤 리액션 (API 호출 아끼기 위해 하드코딩 + 랜덤 조합)
        reactions = [
            "Haha, totally agree!", "Miss you guys.", "Come visit me soon!", 
            "Sounds tough...", "Wow, looks great.", "Cheers! 🍻", 
            "Keep pushing!", "Same here in my city."
        ]
        msg = random.choice(reactions)
        
        html += f"""
        <div class="comment">
            <img src="https://api.dicebear.com/7.x/avataaars/svg?seed={c['id']}" class="avatar">
            <div class="bubble">
                <strong>{c['name']} ({c['country']})</strong>
                <p>{msg}</p>
            </div>
        </div>
        """
    html += '</div>'
    return html

def main():
    # 1. 랜덤 페르소나 선택
    persona = random.choice(PERSONAS)
    print(f"Selected Persona: {persona['name']}")

    # 2. 글 생성 (LLM)
    title, body, topic = generate_content(persona)
    
    # 3. 이미지 생성 (Pollinations.ai 사용 - 무료/무제한)
    # 주제와 국가 분위기에 맞는 이미지 프롬프트 생성
    image_prompt = f"{topic}, {persona['country']} vibe, cinematic lighting, photography, 4k"
    image_url = f"https://image.pollinations.ai/prompt/{image_prompt.replace(' ', '%20')}?width=800&height=400&nologo=true"

    # 4. 마크다운 파일 내용 조립
    date_str = datetime.datetime.now().strftime("%Y-%m-%d")
    comments_html = create_fake_comments(persona)
    
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

{comments_html}
"""

    # 5. GitHub에 파일 업로드 (Push)
    g = Github(GITHUB_TOKEN)
    repo = g.get_repo(REPO_NAME)
    
    file_name = f"src/pages/blog/{date_str}-{persona['id']}-{random.randint(100,999)}.md"
    
    try:
        repo.create_file(file_name, f"New post by {persona['name']}", md_content, branch="main")
        print(f"Successfully created post: {file_name}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
