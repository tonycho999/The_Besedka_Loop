import random
import time
import datetime
import urllib.parse
from github import Github, Auth
import config
from ai_engine import generate_content

def clean_text(text):
    if not text: return ""
    return text.lstrip(" ,.-!").strip()

def is_bad_content(text):
    text_lower = text.lower()
    # 에러 메시지나 날씨 이야기가 있으면 '불량'으로 판정
    if "system error" in text_lower or "ai needs sleep" in text_lower or "error" in text_lower:
        return True
    if "rain" in text_lower or "weather" in text_lower:
        return True
    return False

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
            
            if not is_bad_content(msg):
                comment_section += f'''\n<div class="comment"><img src="https://api.dicebear.com/7.x/avataaars/svg?seed={p["id"]}" class="avatar"><div class="bubble"><strong>{p["name"]}</strong><p>{msg}</p></div></div>'''
                count += 1
        
        if count > 0:
            repo.update_file(last_file.path, f"Relay comments", content + comment_section + '</div>', last_file.sha, branch="main")
    except Exception as e: 
        print(f"Relay error: {e}")

def main():
    print("--- ⛺ The Besedka Loop Bot Started ---")
    time.sleep(random.randint(0, 18000) / 10.0)

    auth = Auth.Token(config.GITHUB_TOKEN)
    repo = Github(auth=auth).get_repo(config.REPO_NAME)

    update_relay_comments(repo)

    persona = random.choice(config.PERSONAS)
    full_text, topic_raw = generate_content(persona, "post")
    
    # [중요] 에러 메시지("System Error")가 돌아왔다면 업로드 하지 않고 종료
    if is_bad_content(full_text):
        print(f"⚠️ Content Rejected (Error or Weather detected): {full_text}")
        return 

    # 정상적인 글일 때만 처리
    lines = [clean_text(line) for line in full_text.split('\n') if clean_text(line)]
    
    if len(lines) > 1:
        title = lines[0].replace('"', "'")
        body = "\n\n".join(lines[1:])
    else:
        title = clean_text(topic_raw) if topic_raw else "Dev Log"
        body = clean_text(full_text)

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
