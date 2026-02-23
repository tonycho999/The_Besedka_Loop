import random
import time
import datetime
from github import Github, Auth
import config
from ai_engine import generate_content

# ... (clean_text, is_bad_content 함수는 기존과 동일하게 유지) ...
def clean_text(text):
    if not text: return ""
    return text.lstrip(" ,.-!").strip()

def is_bad_content(title, body):
    full_text = (title + " " + body).lower()
    error_keywords = ["system error", "ai needs sleep", "error:", "exception"]
    if any(k in full_text for k in error_keywords): return True, "Error Message"
    # 숫자 제목 차단
    if title.replace('.', '').isdigit(): return True, "Numeric Title"
    if len(title) < 5: return True, "Bad Title"
    return False, ""

# [수정] 최신 글 찾기 (날짜 보존의 핵심)
def get_latest_post(repo):
    try:
        contents = repo.get_contents("src/pages/blog")
        md_files = [c for c in contents if c.name.endswith('.md')]
        if not md_files: return None

        # 파일명(YYYY-MM-DD-...) 기준으로 정렬해서 진짜 최신 글 찾기
        md_files.sort(key=lambda x: x.name) 
        return md_files[-1] 

    except Exception as e:
        return None

def update_relay_comments(repo):
    try:
        last_file = get_latest_post(repo)
        if not last_file: return

        # [중요] 파일 내용을 읽어옴 (이 안에 'date: 2026-02-23'이 들어있음)
        content = last_file.decoded_content.decode("utf-8")
        
        # 댓글 생성 로직
        author = next((line.split('"')[1] for line in content.split('\n') if "author:" in line), "Someone")
        title = next((line.replace('title:', '').replace('"', '').strip() for line in content.split('\n') if line.startswith("title:")), "Post")

        new_comments = ""
        count = 0
        for p in random.sample([p for p in config.PERSONAS if p['name'] != author], 2):
            msg, _ = generate_content(p, "comment", title)
            msg = clean_text(msg).replace('"', "")
            is_bad, _ = is_bad_content("", msg)
            if not is_bad:
                new_comments += f'''\n<div class="comment"><img src="https://api.dicebear.com/7.x/avataaars/svg?seed={p["id"]}" class="avatar"><div class="bubble"><strong>{p["name"]}</strong><p>{msg}</p></div></div>'''
                count += 1
        
        if count > 0:
            # [핵심] 기존 content(날짜 포함)는 절대 건드리지 않고 뒤에만 붙임
            if '<div class="comment-box">' in content:
                updated_content = content.replace('</div>', new_comments + '</div>')
            else:
                updated_content = content + '\n\n<div class="comment-box"><h3>💬 Alumni Comments</h3>' + new_comments + '</div>'
            
            # 파일 업데이트 (Git 히스토리는 바뀌지만, 글 내용은 안전함)
            repo.update_file(last_file.path, f"New comments", updated_content, last_file.sha, branch="main")
            print(f"✅ Comments added to {last_file.name}")

    except Exception as e: 
        print(f"Relay error: {e}")

# ... (main 함수 등 나머지는 기존 최신 버전 유지) ...
def main():
    print("--- ⛺ The Besedka Loop Bot Started (Work-Life Balance Mode) ---")
    time.sleep(random.randint(0, 18000) / 10.0)

    auth = Auth.Token(config.GITHUB_TOKEN)
    repo = Github(auth=auth).get_repo(config.REPO_NAME)

    update_relay_comments(repo)

    persona = random.choice(config.PERSONAS)
    full_text, topic_raw = generate_content(persona, "post")
    
    lines = [clean_text(line) for line in full_text.split('\n') if clean_text(line)]
    if len(lines) > 1:
        title = lines[0].replace('"', "'")
        body = "\n\n".join(lines[1:])
    else:
        title = clean_text(topic_raw) if topic_raw else "Daily Log"
        body = clean_text(full_text)

    is_bad, reason = is_bad_content(title, body)
    if is_bad:
        print(f"⚠️ SKIPPED: {reason}")
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

    # 청소기 (50개 유지)
    try:
        contents = repo.get_contents("src/pages/blog")
        md_files = sorted([c for c in contents if c.name.endswith('.md')], key=lambda x: x.name)
        if len(md_files) > 50:
            for file in md_files[:len(md_files)-50]:
                repo.delete_file(file.path, "Cleanup", file.sha, branch="main")
    except: pass

if __name__ == "__main__":
    main()
