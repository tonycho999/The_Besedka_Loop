import random
import time
import json
import datetime
from github import Github, Auth
from github import GithubException
import config
from ai_engine import generate_content

# [기본 관계 설정] 파일이 없을 때 초기화용
# 50~90 사이로 조정했습니다.
DEFAULT_RELATIONS = {
    "romance": 85, "bestie": 75, "colleague": 55, "rival": 50
}

# 초기 관계도 (시작점)
INITIAL_MAP = {
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

# --- [호감도 시스템 함수] ---

def load_relationships(repo):
    try:
        content = repo.get_contents("bot/relationships.json")
        json_data = content.decoded_content.decode("utf-8")
        return json.loads(json_data), content.sha
    except:
        print("⚠️ relationships.json not found. Creating new one...")
        data = {}
        for p in config.PERSONAS:
            name = p['name']
            data[name] = {}
            for other in config.PERSONAS:
                if name == other['name']: continue
                rel_type = INITIAL_MAP.get(name, {}).get(other['name'], "colleague")
                # 기본값도 50~90 범위 내에서 설정
                data[name][other['name']] = DEFAULT_RELATIONS.get(rel_type, 55)
        return data, None

def save_relationships(repo, data, sha):
    json_str = json.dumps(data, indent=2, ensure_ascii=False)
    if sha:
        repo.update_file("bot/relationships.json", "Update affinity scores", json_str, sha, branch="main")
    else:
        repo.create_file("bot/relationships.json", "Init affinity scores", json_str, branch="main")

def get_affinity_level(score):
    # 점수 구간별 멘트 수정 (50점 미만 삭제)
    if score >= 90: return "Soulmate (Deep Trust)"
    if score >= 75: return "Best Friend (Very Close)"
    if score >= 60: return "Close Colleague (Friendly)"
    return "Colleague (Professional/Neutral)" # 50~59점

# --------------------------

def clean_text(text):
    if not text: return ""
    return text.lstrip(" ,.-!").strip()

def is_bad_content(title, body):
    full_text = (title + " " + body).lower()
    if "error" in title.lower(): return True, "Error Title"
    if title.replace('.', '').replace(':', '').strip().isdigit(): return True, "Numeric Title"
    if len(body) < 10: return True, "Too Short"
    return False, ""

def get_recent_posts_info(repo, limit=5):
    try:
        contents = repo.get_contents("src/pages/blog")
        md_files = sorted([c for c in contents if c.name.endswith('.md')], key=lambda x: x.name)
        if not md_files: return []
        recent_files = md_files[-limit:]
        recent_files.reverse() 
        posts_data = []
        for file in recent_files:
            content = file.decoded_content.decode("utf-8")
            lines = content.split('\n')
            title = next((l.replace('title:', '').replace('"', '').strip() for l in lines if l.startswith("title:")), "No Title")
            author = next((l.replace('author:', '').replace('"', '').strip() for l in lines if l.startswith("author:")), "Unknown")
            # 본문 추출 로직 강화
            body_lines = []
            dash_count = 0
            for line in lines:
                if line.strip() == '---':
                    dash_count += 1
                    continue
                if dash_count >= 2:
                    body_lines.append(line)
            posts_data.append({"title": title, "author": author, "body": "\n".join(body_lines).strip()})
        return posts_data
    except: return []

def main():
    print("--- ⛺ The Besedka Loop Bot Started (Safe Range 50-90) ---")
    time.sleep(random.randint(0, 18000) / 10.0)

    auth = Auth.Token(config.GITHUB_TOKEN)
    repo = Github(auth=auth).get_repo(config.REPO_NAME)

    # 1. 호감도 로드
    affinity_data, sha = load_relationships(repo)

    # 2. 모드 결정 (답글 50%, 사생활 25%, 개발 25%)
    modes = ["reply", "life", "dev_life"]
    weights = [0.5, 0.25, 0.25]
    selected_mode = random.choices(modes, weights=weights, k=1)[0]
    
    recent_posts = get_recent_posts_info(repo, limit=5)
    if selected_mode == "reply" and not recent_posts:
        selected_mode = "life"

    target_persona = None
    relation_desc = "Colleague"
    current_score = 55 # 기본값 (안전빵)
    reply_target_post = None

    # 3. 타겟 선정
    if selected_mode == "reply":
        if len(recent_posts) > 0:
            # 최근 글 중 하나 선택 (가중치: 최신순)
            target_index = random.choices(range(len(recent_posts)), weights=[50, 25, 15, 5, 5][:len(recent_posts)], k=1)[0]
            reply_target_post = recent_posts[target_index]
            origin_author = reply_target_post['author']
            
            # 작성자 선정 (본인 제외)
            others = [p for p in config.PERSONAS if p['name'] != origin_author]
            target_persona = random.choice(others)
            
            # 현재 점수 확인 (없으면 기본 55)
            current_score = affinity_data.get(target_persona['name'], {}).get(origin_author, 55)
            # 안전장치: 혹시 파일에 50 미만이나 90 초과가 저장되어 있어도 읽을 때 보정
            current_score = max(50, min(90, current_score))
            
            relation_desc = get_affinity_level(current_score)
            
            print(f"🎯 Interaction: {target_persona['name']} (Score: {current_score}) -> {origin_author}")

    else:
        target_persona = random.choice(config.PERSONAS)
        print(f"🎯 Solo Post: {target_persona['name']} ({selected_mode})")

    # 4. 글 생성
    title, body, sentiment_delta = generate_content(
        target_persona, 
        mode=selected_mode, 
        context_title=reply_target_post['title'] if reply_target_post else "",
        context_body=reply_target_post['body'] if reply_target_post else "",
        context_author=reply_target_post['author'] if reply_target_post else "",
        current_affinity=current_score,
        affinity_label=relation_desc
    )

    # 5. [핵심] 호감도 업데이트 (50 ~ 90 제한)
    if selected_mode == "reply" and reply_target_post:
        origin_author = reply_target_post['author']
        me = target_persona['name']
        
        # 점수 계산
        raw_new_score = current_score + sentiment_delta
        # [제한 적용] 50 미만 금지, 90 초과 금지
        new_score = max(50, min(90, raw_new_score))
        
        # 저장
        if me not in affinity_data: affinity_data[me] = {}
        affinity_data[me][origin_author] = new_score
        
        print(f"❤️ Affinity Update: {me} -> {origin_author} : {current_score} -> {new_score} (Delta: {sentiment_delta})")
        
        save_relationships(repo, affinity_data, sha)

    # 제목 처리 (Re: Re:)
    if selected_mode == "reply" and reply_target_post:
        original_title = reply_target_post['title']
        if original_title.startswith("Re:"):
            if original_title.count("Re:") >= 2: title = original_title
            else: title = f"Re: {original_title}"
        else: title = f"Re: {original_title}"

    # 업로드
    is_bad, reason = is_bad_content(title, body)
    if is_bad:
        print(f"⚠️ SKIPPED: {reason}")
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
    
    # 청소
    try:
        contents = repo.get_contents("src/pages/blog")
        md_files = sorted([c for c in contents if c.name.endswith('.md')], key=lambda x: x.name)
        if len(md_files) > 50:
            for file in md_files[:len(md_files)-50]:
                repo.delete_file(file.path, "Cleanup", file.sha, branch="main")
    except: pass

if __name__ == "__main__":
    main()
