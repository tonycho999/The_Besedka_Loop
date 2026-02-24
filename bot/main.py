import random
import time
import datetime
from github import Github, Auth
import config
from ai_engine import generate_content

# [설정] 베세드카 입주민 관계도 (Chemistry Map)
# 이 짝꿍들은 우선적으로 서로의 글에 반응합니다.
RELATIONSHIPS = {
    "Jin-woo": {"Amélie": "romance", "Kenji": "colleague"},
    "Amélie":  {"Jin-woo": "romance", "Marco": "bestie"},
    "Kenji":   {"Sarah": "rival", "Jin-woo": "colleague"},
    "Sarah":   {"Kenji": "rival", "Hina": "bestie"},
    "Carlos":  {"Marco": "bestie", "Budi": "colleague"},
    "Marco":   {"Carlos": "bestie", "Amélie": "bestie"},
    "Wei":     {"Budi": "colleague", "Lena": "bestie"},
    "Budi":    {"Wei": "colleague", "Carlos": "colleague"},
    "Lena":    {"Hina": "bestie", "Wei": "bestie"},
    "Hina":    {"Lena": "bestie", "Sarah": "bestie"}
}

def clean_text(text):
    if not text: return ""
    return text.lstrip(" ,.-!").strip()

def is_bad_content(title, body):
    full_text = (title + " " + body).lower()
    if "error" in title.lower(): return True, "Error Title"
    if title.replace('.', '').replace(':', '').strip().isdigit(): return True, "Numeric Title"
    if len(body) < 10: return True, "Too Short"
    return False, ""

# 최신 글 정보 가져오기 (제목, 내용, 작성자)
def get_latest_post_info(repo):
    try:
        contents = repo.get_contents("src/pages/blog")
        # 날짜순 정렬 (파일명 기준)
        md_files = sorted([c for c in contents if c.name.endswith('.md')], key=lambda x: x.name)
        
        if not md_files: return None

        last_file = md_files[-1]
        content = last_file.decoded_content.decode("utf-8")
        
        # Frontmatter 파싱
        lines = content.split('\n')
        title = next((l.replace('title:', '').replace('"', '').strip() for l in lines if l.startswith("title:")), "No Title")
        author = next((l.replace('author:', '').replace('"', '').strip() for l in lines if l.startswith("author:")), "Unknown")
        
        # 본문 추출 (--- 두 번째 이후)
        dash_count = 0
        body_lines = []
        for line in lines:
            if line.strip() == '---':
                dash_count += 1
                continue
            if dash_count >= 2:
                body_lines.append(line)
        
        body = "\n".join(body_lines).strip()
        return {"title": title, "author": author, "body": body}

    except Exception as e:
        print(f"Error reading last post: {e}")
        return None

def main():
    print("--- ⛺ The Besedka Loop Bot Started (Relation & Reply Mode) ---")
    time.sleep(random.randint(0, 18000) / 10.0)

    auth = Auth.Token(config.GITHUB_TOKEN)
    repo = Github(auth=auth).get_repo(config.REPO_NAME)

    # 1. 모드 결정 (확률 가중치)
    # Life(30), Reply(40), Work(10), Info(20)
    modes = ["life", "reply", "work", "info"]
    weights = [0.3, 0.4, 0.1, 0.2]
    selected_mode = random.choices(modes, weights=weights, k=1)[0]
    
    # 2. 컨텍스트 준비
    latest_post = get_latest_post_info(repo)
    
    # 예외 처리: 글이 하나도 없으면 답글 불가 -> 강제 Life 모드
    if selected_mode == "reply" and not latest_post:
        selected_mode = "life"

    # 3. 작성자(Persona) 선정
    target_persona = None
    relation_type = "colleague" # 기본 관계

    if selected_mode == "reply":
        # 답글 모드: 원작자와 관계있는 사람 찾기
        origin_author = latest_post['author']
        
        # 관계도에 있는 친구들 후보군
        friends = RELATIONSHIPS.get(origin_author, {})
        candidates = [p for p in config.PERSONAS if p['name'] in friends.keys()]
        
        if candidates and random.random() < 0.8: # 80% 확률로 지인이 답글
            target_persona = random.choice(candidates)
            relation_type = friends.get(target_persona['name'], "colleague")
        else:
            # 관계없는 사람도 가끔 등판 (랜덤)
            others = [p for p in config.PERSONAS if p['name'] != origin_author]
            target_persona = random.choice(others)
            
        print(f"🎯 Action: {target_persona['name']} replies to {origin_author}")
        
    else:
        # 일반 모드: 그냥 랜덤 선택 (연속 작성 방지 로직 추가 가능)
        target_persona = random.choice(config.PERSONAS)
        print(f"🎯 Action: {target_persona['name']} posts new {selected_mode} log")

    # 4. 글 생성
    title, body = generate_content(
        target_persona, 
        mode=selected_mode, 
        context_title=latest_post['title'] if latest_post else "",
        context_body=latest_post['body'] if latest_post else "",
        context_author=latest_post['author'] if latest_post else "",
        relation_type=relation_type
    )

    # 5. 검열 및 업로드
    is_bad, reason = is_bad_content(title, body)
    if is_bad:
        print(f"⚠️ SKIPPED: {reason}")
        return

    date_str = datetime.datetime.now().strftime("%Y-%m-%d")
    
    # Frontmatter 조립
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
    print(f"✅ Post Success: {file_path} (Mode: {selected_mode})")

    # 6. 청소기 (50개 유지)
    try:
        contents = repo.get_contents("src/pages/blog")
        md_files = sorted([c for c in contents if c.name.endswith('.md')], key=lambda x: x.name)
        if len(md_files) > 50:
            for file in md_files[:len(md_files)-50]:
                repo.delete_file(file.path, "Cleanup", file.sha, branch="main")
    except: pass

if __name__ == "__main__":
    main()
