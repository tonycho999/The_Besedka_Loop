import random
import time
import datetime
import urllib.parse
from github import Github, Auth
import config
from ai_engine import generate_content

# [검열 1] 텍스트 청소
def clean_text(text):
    if not text: return ""
    return text.lstrip(" ,.-!").strip()

# [검열 2] 불량 게시물 판독기 (강화됨)
def is_bad_content(title, body):
    full_text = (title + " " + body).lower()
    
    # 1. 시스템 에러 메시지
    error_keywords = ["system error", "ai needs sleep", "error:", "exception", "debugging nightmare"]
    if any(k in full_text for k in error_keywords): return True, "Error Message"

    # 2. 날씨 언급
    weather_keywords = ["rain", "snow", "weather", "sunny", "cloudy", "storm", "unexpected rain"]
    if any(k in full_text for k in weather_keywords): return True, "Weather Talk"

    # 3. [신규] 숫자만 있는 제목 차단 (예: "0.0117...")
    if title.replace('.', '').isdigit(): return True, "Numeric Title"

    # 4. 제목/본문 길이 미달
    if len(title) < 5 or "error" in title.lower(): return True, "Bad Title"
    if len(body) < 20: return True, "Content Too Short"

    return False, ""

# [핵심 수정] 가장 최신 글 찾기 (이름순 X -> 날짜순 O)
def get_latest_post(repo):
    try:
        contents = repo.get_contents("src/pages/blog")
        md_files = [c for c in contents if c.name.endswith('.md')]
        
        if not md_files: return None

        # 파일명에서 날짜 추출 (형식: YYYY-MM-DD-...)
        # first-signal.md 같은 예외 파일은 날짜가 없으므로 아주 옛날로 취급
        def get_date_from_filename(file):
            parts = file.name.split('-')
            if len(parts) >= 3 and parts[0].isdigit() and parts[1].isdigit():
                return f"{parts[0]}-{parts[1]}-{parts[2]}"
            return "2000-01-01" # 날짜 없는 파일은 맨 뒤로 보냄

        # 날짜 기준으로 정렬 (최신 날짜가 맨 뒤로 가도록)
        md_files.sort(key=get_date_from_filename)
        
        return md_files[-1] # 진짜 최신 파일 반환

    except Exception as e:
        print(f"Error finding latest post: {e}")
        return None

# 댓글 달기 (릴레이)
def update_relay_comments(repo):
    try:
        last_file = get_latest_post(repo)
        if not last_file: return

        print(f"💬 Commenting on: {last_file.name}") # 로그 확인용

        content = last_file.decoded_content.decode("utf-8")
        
        # 이미 댓글 박스가 있으면 중단 (하루에 한 번만 달기 위해)
        # 만약 댓글을 더 달고 싶으면 이 줄을 주석 처리하세요.
        # if "comment-box" in content: return 

        author = next((line.split('"')[1] for line in content.split('\n') if "author:" in line), "Someone")
        title = next((line.replace('title:', '').replace('"', '').strip() for line in content.split('\n') if line.startswith("title:")), "Post")

        # 기존 댓글이 있다면 그 뒤에 이어 붙이기, 없으면 새로 만들기
        if '<div class="comment-box">' in content:
            new_comments = ""
        else:
            new_comments = '\n\n<div class="comment-box"><h3>💬 Alumni Comments</h3>'

        count = 0
        # 랜덤 동료 2명이 댓글 작성
        for p in random.sample([p for p in config.PERSONAS if p['name'] != author], 2):
            msg, _ = generate_content(p, "comment", title)
            msg = clean_text(msg).replace('"', "")
            
            is_bad, _ = is_bad_content("", msg)
            if not is_bad:
                new_comments += f'''\n<div class="comment"><img src="https://api.dicebear.com/7.x/avataaars/svg?seed={p["id"]}" class="avatar"><div class="bubble"><strong>{p["name"]}</strong><p>{msg}</p></div></div>'''
                count += 1
        
        if count > 0:
            if '<div class="comment-box">' in content:
                # 기존 댓글 박스 닫는 태그(</div>) 앞에 새 댓글 삽입
                updated_content = content.replace('</div>', new_comments + '</div>')
            else:
                # 아예 새로 추가
                updated_content = content + new_comments + '</div>'
            
            repo.update_file(last_file.path, f"New comments on {last_file.name}", updated_content, last_file.sha, branch="main")
            print("✅ Comments added successfully.")

    except Exception as e: 
        print(f"Relay error: {e}")

# 오래된 글 삭제 (청소기)
def cleanup_old_posts(repo, keep_limit=50):
    try:
        contents = repo.get_contents("src/pages/blog")
        md_files = sorted([c for c in contents if c.name.endswith('.md')], key=lambda x: x.name)
        
        if len(md_files) > keep_limit:
            delete_count = len(md_files) - keep_limit
            files_to_delete = md_files[:delete_count]
            print(f"🧹 Cleaning up: Deleting {delete_count} old posts...")
            for file in files_to_delete:
                repo.delete_file(file.path, "Auto-cleanup", file.sha, branch="main")
    except Exception as e:
        print(f"Cleanup Error: {e}")

def main():
    print("--- ⛺ The Besedka Loop Bot Started (Smart Sort Mode) ---")
    time.sleep(random.randint(0, 18000) / 10.0)

    auth = Auth.Token(config.GITHUB_TOKEN)
    repo = Github(auth=auth).get_repo(config.REPO_NAME)

    # 1. 댓글 달기 (이제 진짜 최신 글에 달림)
    update_relay_comments(repo)

    # 2. 새 글 쓰기
    persona = random.choice(config.PERSONAS)
    full_text, topic_raw = generate_content(persona, "post")
    
    lines = [clean_text(line) for line in full_text.split('\n') if clean_text(line)]
    if len(lines) > 1:
        title = lines[0].replace('"', "'")
        body = "\n\n".join(lines[1:])
    else:
        title = clean_text(topic_raw) if topic_raw else "Dev Log"
        body = clean_text(full_text)

    # 불량 글 필터링 (숫자 제목 등)
    is_bad, reason = is_bad_content(title, body)
    if is_bad:
        print(f"⚠️ SKIPPED UPLOAD: {reason}")
        print(f"   - Title: {title}")
        return

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
    
    # 3. 청소
    cleanup_old_posts(repo, keep_limit=50)

if __name__ == "__main__":
    main()
