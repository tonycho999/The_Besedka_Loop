import random
import time
import datetime
import urllib.parse
from github import Github, Auth
import config
from ai_engine import generate_content

# [검열 1] 텍스트 청소 (앞뒤 지저분한 기호 제거)
def clean_text(text):
    if not text: return ""
    return text.lstrip(" ,.-!").strip()

# [검열 2] 불량 게시물 판독기 (여기가 핵심!)
def is_bad_content(title, body):
    full_text = (title + " " + body).lower()
    
    # 1. 시스템 에러 메시지 차단
    error_keywords = ["system error", "ai needs sleep", "error:", "exception", "debugging nightmare"]
    if any(k in full_text for k in error_keywords):
        return True, "Error Message Detected"

    # 2. 날씨 관련 키워드 차단
    weather_keywords = ["rain", "snow", "weather", "sunny", "cloudy", "storm", "unexpected rain"]
    if any(k in full_text for k in weather_keywords):
        return True, "Weather Talk Detected"

    # 3. 제목이 너무 짧거나 이상한 경우 (예: "Error")
    if len(title) < 5 or "error" in title.lower():
        return True, "Bad Title"

    # 4. 본문이 너무 짧은 경우
    if len(body) < 20:
        return True, "Content Too Short"

    return False, ""

def update_relay_comments(repo):
    try:
        contents = repo.get_contents("src/pages/blog")
        md_files = sorted([c for c in contents if c.name.endswith('.md')], key=lambda x: x.name)
        if not md_files: return
        
        last_file = md_files[-1]
        content = last_file.decoded_content.decode("utf-8")
        if "comment-box" in content: return

        author = next((line.split('"')[1] for line in content.split('\n') if "author:" in line), "Someone")
        title = next((line.replace('title:', '').replace('"', '').strip() for line in content.split('\n') if line.startswith("title:")), "Post")

        comment_section = '\n\n<div class="comment-box"><h3>💬 Alumni Comments</h3>'
        count = 0
        for p in random.sample([p for p in config.PERSONAS if p['name'] != author], 2):
            msg, _ = generate_content(p, "comment", title)
            msg = clean_text(msg).replace('"', "")
            
            # 댓글도 불량 검사
            is_bad, _ = is_bad_content("", msg)
            if not is_bad:
                comment_section += f'''\n<div class="comment"><img src="https://api.dicebear.com/7.x/avataaars/svg?seed={p["id"]}" class="avatar"><div class="bubble"><strong>{p["name"]}</strong><p>{msg}</p></div></div>'''
                count += 1
        
        if count > 0:
            repo.update_file(last_file.path, f"Relay comments", content + comment_section + '</div>', last_file.sha, branch="main")
    except Exception as e: 
        print(f"Relay error: {e}")

def main():
    print("--- ⛺ The Besedka Loop Bot Started (Strict Mode) ---")
    time.sleep(random.randint(0, 18000) / 10.0)

    auth = Auth.Token(config.GITHUB_TOKEN)
    repo = Github(auth=auth).get_repo(config.REPO_NAME)

    update_relay_comments(repo)

    persona = random.choice(config.PERSONAS)
    full_text, topic_raw = generate_content(persona, "post")
    
    # 1. 텍스트 분리 및 청소
    lines = [clean_text(line) for line in full_text.split('\n') if clean_text(line)]
    
    if len(lines) > 1:
        title = lines[0].replace('"', "'")
        body = "\n\n".join(lines[1:])
    else:
        title = clean_text(topic_raw) if topic_raw else "Dev Log"
        body = clean_text(full_text)

    # [중요] 여기서 최종 검사 수행! 불량이면 업로드 안 함.
    is_bad, reason = is_bad_content(title, body)
    if is_bad:
        print(f"⚠️ SKIPPED UPLOAD: {reason}")
        print(f"   - Title: {title}")
        print(f"   - Body Sample: {body[:30]}...")
        return  # 프로그램 종료 (업로드 안 함)

    date_str = datetime.datetime.now().strftime("%Y-%m-%d")
    
    md_output = f'''---
layout: ../../layouts/BlogPostLayout.astro
title: "{title}"
author: "{persona["name"]}"
date: "{date_str}"
image: ""
category: "Daily Log"
location: "{persona["country"]}"
---

{body}'''

    file_path = f"src/pages/blog/{date_str}-{persona['id']}-{random.randint(1000,9999)}.md"
    repo.create_file(file_path, f"Signal from {persona['name']}", md_output, branch="main")
    print(f"✅ Post Success: {file_path}")

if __name__ == "__main__":
    main()
