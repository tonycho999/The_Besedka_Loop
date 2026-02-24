import random
import time
import datetime
from github import Github, Auth
import config
from ai_engine import generate_content

# 🔗 [인연] 베세드카 관계도 (Chemistry)
RELATIONSHIPS = {
    "Jin-woo": {"Amélie": "romance", "Kenji": "colleague", "Marco": "bestie"},
    "Amélie":  {"Jin-woo": "romance", "Marco": "bestie", "Hina": "colleague"},
    "Kenji":   {"Sarah": "rival", "Jin-woo": "colleague", "Wei": "bestie"},
    "Sarah":   {"Kenji": "rival", "Hina": "bestie", "Lena": "colleague"},
    "Carlos":  {"Marco": "bestie", "Budi": "colleague", "Hina": "bestie"},
    "Marco":   {"Carlos": "bestie", "Amélie": "bestie", "Jin-woo": "colleague"},
    "Wei":     {"Budi": "colleague", "Lena": "bestie", "Kenji": "bestie"},
    "Budi":    {"Wei": "colleague", "Carlos": "colleague"},
    "Lena":    {"Hina": "bestie", "Wei": "bestie", "Sarah": "colleague"},
    "Hina":    {"Lena": "bestie", "Sarah": "bestie", "Carlos": "bestie"}
}

def clean_text(text):
    if not text: return ""
    return text.lstrip(" ,.-!").strip()

# [필터] 에러, 숫자 제목, 너무 짧은 글 자동 차단
def is_bad_content(title, body):
    full_text = (title + " " + body).lower()
    
    # 에러 메시지
    if "error" in title.lower() or "exception" in full_text: return True, "Error detected"
    # 시간 제목 차단 (02:00, 11:30 등)
    if ":" in title and any(c.isdigit() for c in title): return True, "Time in title"
    # 숫자만 있는 제목
    if title.replace('.', '').replace(':', '').strip().isdigit(): return True, "Numeric Title"
    # 너무 짧음
    if len(body) < 10: return True, "Too Short"
    
    return False, ""

# [핵심] 최근 글 5개 가져오기 (대화 후보군)
def get_recent_posts_info(repo, limit=5):
    try:
        contents = repo.get_contents("src/pages/blog")
        # 날짜순 정렬 (파일명 기준)
        md_files = sorted([c for c in contents if c.name.endswith('.md')], key=lambda x: x.name)
        
        if not md_files: return []

        # 뒤에서부터 n개 가져오기 (최신순으로 뒤집음)
        recent_files = md_files[-limit:]
        recent_files.reverse() 
        
        posts_data = []
        for file in recent_files:
            content = file.decoded_content.decode("utf-8")
            lines = content.split('\n')
            
            title = next((l.replace('title:', '').replace('"', '').strip() for l in lines if l.startswith("title:")), "No Title")
            author = next((l.replace('author:', '').replace('"', '').strip() for l in lines if l.startswith("author:")), "Unknown")
            
            # 본문 추출
            dash_count = 0
            body_lines = []
            for line in lines:
                if line.strip() == '---':
                    dash_count += 1
                    continue
                if dash_count >= 2:
                    body_lines.append(line)
            
            posts_data.append({
                "title": title,
                "author": author,
                "body": "\n".join(body_lines).strip(),
                "filename": file.name
            })
            
        return posts_data # [최신글, 그전글, 그전전글...] 순서
    except Exception as e:
        print(f"Error reading posts: {e}")
        return []

def main():
    print("--- ⛺ The Besedka Loop Bot Started (Community V2) ---")
    time.sleep(random.randint(0, 18000) / 10.0)

    auth = Auth.Token(config.GITHUB_TOKEN)
    repo = Github(auth=auth).get_repo(config.REPO_NAME)

    # 1. 모드 결정 (답글 40%, 사생활 30%, 개발공감 30%)
    modes = ["reply", "life", "dev_life"]
    weights = [0.4, 0.3, 0.3]
    selected_mode = random.choices(modes, weights=weights, k=1)[0]
    
    # 2. 최근 글 5개 스캔
    recent_posts = get_recent_posts_info(repo, limit=5)
    
    # 글이 없으면 강제로 새 글 쓰기
    if selected_mode == "reply" and not recent_posts:
        selected_mode = "life"

    # 3. 작성자 및 타겟 선정
    target_persona = None
    relation_type = "colleague"
    reply_target_post = None

    if selected_mode == "reply":
        # [중요] 최근 5개 글 중에서 하나를 랜덤으로 선택 (가중치: 최신일수록 높음)
        # 예: [1등(50%), 2등(25%), 3등(15%), 4등(5%), 5등(5%)]
        if len(recent_posts) > 0:
            target_index = random.choices(range(len(recent_posts)), weights=[50, 25, 15, 5, 5][:len(recent_posts)], k=1)[0]
            reply_target_post = recent_posts[target_index]
            origin_author = reply_target_post['author']
            
            # 그 작성자와 관계있는 친구 찾기
            friends = RELATIONSHIPS.get(origin_author, {})
            candidates = [p for p in config.PERSONAS if p['name'] in friends.keys()]
            
            if candidates:
                target_persona = random.choice(candidates)
                relation_type = friends.get(target_persona['name'], "colleague")
            else:
                others = [p for p in config.PERSONAS if p['name'] != origin_author]
                target_persona = random.choice(others)

            print(f"🎯 Connection: {target_persona['name']} replies to {origin_author}'s post ('{reply_target_post['title']}')")
    
    else:
        # 일반 글은 랜덤
        target_persona = random.choice(config.PERSONAS)
        print(f"🎯 New Story: {target_persona['name']} ({selected_mode})")

    # 4. 글 생성
    title, body = generate_content(
        target_persona, 
        mode=selected_mode, 
        context_title=reply_target_post['title'] if reply_target_post else "",
        context_body=reply_target_post['body'] if reply_target_post else "",
        context_author=reply_target_post['author'] if reply_target_post else "",
        relation_type=relation_type
    )

    # [제목 처리] 답글인 경우 Re: Re: 로직 적용
    if selected_mode == "reply" and reply_target_post:
        original_title = reply_target_post['title']
        if original_title.startswith("Re:"):
            # 이미 Re:가 있으면 하나 더 붙임 (Re: Re: ...)
            # 단, 너무 길어지면(Re가 2개 이상) 그냥 유지하거나 정리
            if original_title.count("Re:") >= 2:
                 title = original_title # Re: Re: 유지
            else:
                 title = f"Re: {original_title}"
        else:
            title = f"Re: {original_title}"

    # 5. 검열 및 업로드
    is_bad, reason = is_bad_content(title, body)
    if is_bad:
        print(f"⚠️ SKIPPED: {reason} (Title: {title})")
        return

    date_str = datetime.datetime.now().strftime("%Y-%m-%d")
    
    md_output = f'''---
layout: ../../layouts/BlogPostLayout.astro
title: "{title}"
author: "{target_persona["name"]}"
date: "{date_str}"
image: ""
category: "Daily Log"
location: "{target_persona["country"]}"
---

{body}'''

    file_path = f"src/pages/blog/{date_str}-{target_persona['id']}-{random.randint(1000,9999)}.md"
    repo.create_file(file_path, f"Signal from {target_persona['name']}", md_output, branch="main")
    print(f"✅ Posted: {title}")

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
