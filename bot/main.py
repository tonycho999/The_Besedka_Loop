import os
import json
import random
import datetime
from dotenv import load_dotenv
from github import Github

import config
from ai_engine import generate_post

# [핵심 수정] 함수 이름을 model_selector.py에 있는 그대로(get_client) 가져옵니다.
from model_selector import get_client, get_dynamic_model

load_dotenv()

# 파일 경로 정의
STATUS_FILE = "status.json"
HISTORY_FILE = "history.json"

# ==========================================
# 1. 데이터 관리 함수
# ==========================================
def load_json(filename, default):
    if not os.path.exists(filename): return default
    with open(filename, 'r', encoding='utf-8') as f: return json.load(f)

def save_json(filename, data):
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def get_initial_status():
    data = {}
    for p in config.PERSONAS:
        data[p['id']] = {
            "state": "normal", 
            "return_date": None,
            "relationships": {t['id']: config.DEFAULT_AFFINITY for t in config.PERSONAS if t['id'] != p['id']}
        }
    return data

def push_to_github(filename, content):
    if not config.GITHUB_TOKEN:
        print("⚠️ GitHub Token 없음 - 로컬 출력으로 대체")
        print(f"\n[{filename}]\n{content}\n")
        return
    try:
        g = Github(config.GITHUB_TOKEN)
        repo = g.get_repo(config.REPO_NAME)
        path = f"logs/{filename}"
        repo.create_file(path, f"Add post: {filename}", content, branch="main")
        print(f"✅ GitHub Uploaded: {path}")
    except Exception as e:
        print(f"❌ Upload Failed: {e}")

# ==========================================
# 2. 메인 실행 로직
# ==========================================
def main():
    # 1. API 및 데이터 준비
    # [수정] get_groq_client() -> get_client() 호출
    client = get_client()
    model_id = get_dynamic_model(client)
    
    status_db = load_json(STATUS_FILE, get_initial_status())
    history_db = load_json(HISTORY_FILE, []) 
    today = datetime.datetime.now().strftime("%Y-%m-%d")

    print(f"📅 Date: {today} | Model: {model_id}")

    # 2. 상태 체크 (복귀자 확인)
    returner = None
    active_members = []
    
    for pid, data in status_db.items():
        if data['return_date'] == today:
            print(f"✨ {pid}님이 복귀했습니다!")
            data['state'] = "normal"
            data['return_date'] = None
            returner = pid
        if data['state'] == "normal":
            active_members.append(pid)

    if not active_members:
        print("😱 모든 멤버가 부재중입니다!")
        return

    # 3. 광고 데이터 준비 (AD_MODE)
    selected_ad = None
    if config.AD_MODE:
        selected_ad = random.choice(config.PROMOTED_SITES)
        print(f"💰 AD_MODE Active: Including PPL for '{selected_ad['name']}'")

    # 4. 행동 결정 (New Post vs Reply)
    mode = "new"
    actor_id = None
    target_post = None
    topic = None
    category = None
    
    # [Case A] 복귀 신고식
    if returner:
        mode = "new"
        actor_id = returner
        category = {"desc": "Returning from vacation/sick leave."}
        topic = "I'm back"
    
    # [Case B] 일반 상황
    else:
        # 답글 확률 40% (역사가 있어야 함)
        if history_db and random.random() < 0.4:
            mode = "reply"
            target_post = random.choice(history_db[-10:])
            candidates = [m for m in active_members if m != target_post['author_id']]
            if candidates:
                actor_id = random.choice(candidates)
            else:
                mode = "new" 
        
        # 새 글 (60%)
        if mode == "new":
            actor_id = random.choice(active_members)
            r = random.random()
            cumulative = 0
            selected_cat_key = "life"
            for key, val in config.CONTENT_CATEGORIES.items():
                cumulative += val['ratio']
                if r <= cumulative:
                    selected_cat_key = key
                    break
            category = config.CONTENT_CATEGORIES[selected_cat_key]
            topic = random.choice(config.TOPICS)

    # 5. 페르소나 및 호감도 조회
    actor = next(p for p in config.PERSONAS if p['id'] == actor_id)
    affinity_score = 70
    if mode == "reply":
        target_id = target_post['author_id']
        affinity_score = status_db[actor_id]['relationships'].get(target_id, 70)

    print(f"🚀 Mode: {mode.upper()} | Actor: {actor['name']}")

    # ----------------------------------------------
    # 6. AI 생성 요청
    # ----------------------------------------------
    result = generate_post(
        client, model_id, mode, actor, 
        target_post=target_post, 
        category=category,
        topic=topic,
        affinity_score=affinity_score,
        ad_data=selected_ad
    )

    # 7. 결과 출력
    print(f"\nTitle: {result['title']}")
    print("-" * 30)
    print(result['content'])
    print("-" * 30)

    # 8. 데이터 업데이트
    if mode == "reply" and result['affinity_change'] != 0:
        target_id = target_post['author_id']
        change = result['affinity_change']
        curr_a = status_db[actor_id]['relationships'].get(target_id, 70)
        curr_b = status_db[target_id]['relationships'].get(actor_id, 70)
        new_a = max(config.AFFINITY_MIN, min(curr_a + change, config.AFFINITY_MAX))
        new_b = max(config.AFFINITY_MIN, min(curr_b + change, config.AFFINITY_MAX))
        status_db[actor_id]['relationships'][target_id] = new_a
        status_db[target_id]['relationships'][actor_id] = new_b
        print(f"📊 Affinity Updated: {change} points")

    dice = random.random()
    if dice < config.VACATION_CHANCE:
        days = random.randint(3, 7)
        ret_date = datetime.datetime.now() + datetime.timedelta(days=days)
        status_db[actor_id]['state'] = "vacation"
        status_db[actor_id]['return_date'] = ret_date.strftime("%Y-%m-%d")
        print(f"✈️ {actor['name']} -> Vacation ({days} days)")
    elif dice < config.VACATION_CHANCE + config.SICK_CHANCE:
        days = random.randint(1, 2)
        ret_date = datetime.datetime.now() + datetime.timedelta(days=days)
        status_db[actor_id]['state'] = "sick"
        status_db[actor_id]['return_date'] = ret_date.strftime("%Y-%m-%d")
        print(f"🤒 {actor['name']} -> Sick ({days} days)")

    new_log = {
        "id": datetime.datetime.now().timestamp(),
        "date": today,
        "author": actor['name'],
        "author_id": actor['id'],
        "title": result['title'],
        "content": result['content']
    }
    history_db.insert(0, new_log)
    if len(history_db) > config.HISTORY_LIMIT:
        history_db.pop()

    save_json(STATUS_FILE, status_db)
    save_json(HISTORY_FILE, history_db)
    
    safe_title = result['title'].replace(" ", "_").replace(":", "").replace("/", "_")
    filename = f"{today}_{safe_title}.md"
    
    md_content = f"""# {result['title']}
**Date:** {today}
**Author:** {actor['name']} ({actor['role']})

---
{result['content']}
---
"""
    push_to_github(filename, md_content)

if __name__ == "__main__":
    main()
