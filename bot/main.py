import os
import json
import random
import datetime
from dotenv import load_dotenv
from github import Github, Auth

import config
from ai_engine import generate_post

from model_selector import get_client, get_dynamic_model

load_dotenv()

# ==========================================
# [설정] 파일 경로 및 저장소 설정
# ==========================================
# [수정됨] pages 안의 blog 폴더로 지정
POST_DIR = "pages/blog" 

STATUS_FILE = "status.json"
HISTORY_FILE = "history.json"

# ==========================================
# 1. GitHub 파일 입출력 함수 (영구 기억)
# ==========================================
def get_github_repo():
    """GitHub 저장소 객체 반환"""
    if not config.GITHUB_TOKEN:
        return None
    auth = Auth.Token(config.GITHUB_TOKEN)
    g = Github(auth=auth)
    return g.get_repo(config.REPO_NAME)

def load_data_from_github(repo, filename, default_data):
    """GitHub에서 JSON 파일을 다운로드하여 로드"""
    if not repo: return default_data
    try:
        contents = repo.get_contents(filename)
        json_str = contents.decoded_content.decode("utf-8")
        return json.loads(json_str)
    except Exception as e:
        print(f"⚠️ GitHub에서 {filename} 로드 실패 (새로 생성합니다): {e}")
        return default_data

def save_data_to_github(repo, filename, data, message):
    """GitHub에 JSON 데이터 업로드 (덮어쓰기)"""
    if not repo: return
    try:
        json_str = json.dumps(data, indent=2, ensure_ascii=False)
        
        try:
            contents = repo.get_contents(filename)
            repo.update_file(
                path=contents.path,
                message=message,
                content=json_str,
                sha=contents.sha,
                branch="main"
            )
            print(f"💾 {filename} 저장 완료 (Update)")
        except:
            repo.create_file(
                path=filename,
                message=message,
                content=json_str,
                branch="main"
            )
            print(f"💾 {filename} 저장 완료 (Create)")
            
    except Exception as e:
        print(f"❌ {filename} 저장 실패: {e}")

# ==========================================
# 2. 초기 데이터 생성기
# ==========================================
def get_initial_status():
    data = {}
    for p in config.PERSONAS:
        data[p['id']] = {
            "state": "normal", 
            "return_date": None,
            "relationships": {t['id']: config.DEFAULT_AFFINITY for t in config.PERSONAS if t['id'] != p['id']}
        }
    return data

# ==========================================
# 3. 메인 실행 로직
# ==========================================
def main():
    repo = get_github_repo()
    if not repo and config.GITHUB_TOKEN:
        print("❌ GitHub 저장소를 찾을 수 없습니다.")
        return

    # 기억 불러오기
    print("📥 기억 데이터를 다운로드 중...")
    status_db = load_data_from_github(repo, STATUS_FILE, get_initial_status())
    history_db = load_data_from_github(repo, HISTORY_FILE, [])
    
    client = get_client()
    model_id = get_dynamic_model(client)
    today = datetime.datetime.now().strftime("%Y-%m-%d")

    print(f"📅 Date: {today} | Model: {model_id}")

    # 상태 체크
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
        save_data_to_github(repo, STATUS_FILE, status_db, f"Update status: All away {today}")
        return

    # 광고 준비
    selected_ad = None
    if config.AD_MODE:
        selected_ad = random.choice(config.PROMOTED_SITES)
        print(f"💰 PPL Active: {selected_ad['name']}")

    # 행동 결정
    mode = "new"
    actor_id = None
    target_post = None
    topic = None
    category = None
    
    if returner:
        mode = "new"
        actor_id = returner
        category = {"desc": "Returning from vacation/sick leave."}
        topic = "I'm back"
    else:
        if history_db and random.random() < 0.4:
            mode = "reply"
            target_post = random.choice(history_db[-10:])
            candidates = [m for m in active_members if m != target_post['author_id']]
            if candidates:
                actor_id = random.choice(candidates)
            else:
                mode = "new"
        
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

    actor = next(p for p in config.PERSONAS if p['id'] == actor_id)
    affinity_score = 70
    if mode == "reply":
        target_id = target_post['author_id']
        affinity_score = status_db[actor_id]['relationships'].get(target_id, 70)

    print(f"🚀 Mode: {mode.upper()} | Actor: {actor['name']}")

    # AI 생성
    result = generate_post(
        client, model_id, mode, actor, 
        target_post=target_post, 
        category=category,
        topic=topic,
        affinity_score=affinity_score,
        ad_data=selected_ad
    )

    print(f"\nTitle: {result['title']}")
    print("-" * 30)
    print(result['content'])
    print("-" * 30)

    # 데이터 업데이트
    if mode == "reply" and result['affinity_change'] != 0:
        target_id = target_post['author_id']
        change = result['affinity_change']
        curr_a = status_db[actor_id]['relationships'].get(target_id, 70)
        curr_b = status_db[target_id]['relationships'].get(actor_id, 70)
        new_a = max(config.AFFINITY_MIN, min(curr_a + change, config.AFFINITY_MAX))
        new_b = max(config.AFFINITY_MIN, min(curr_b + change, config.AFFINITY_MAX))
        status_db[actor_id]['relationships'][target_id] = new_a
        status_db[target_id]['relationships'][actor_id] = new_b
        print(f"📊 호감도 변경: {change}")

    dice = random.random()
    if dice < config.VACATION_CHANCE:
        days = random.randint(3, 7)
        ret_date = datetime.datetime.now() + datetime.timedelta(days=days)
        status_db[actor_id]['state'] = "vacation"
        status_db[actor_id]['return_date'] = ret_date.strftime("%Y-%m-%d")
        print(f"✈️ {actor['name']} -> 휴가 ({days}일)")
    elif dice < config.VACATION_CHANCE + config.SICK_CHANCE:
        days = random.randint(1, 2)
        ret_date = datetime.datetime.now() + datetime.timedelta(days=days)
        status_db[actor_id]['state'] = "sick"
        status_db[actor_id]['return_date'] = ret_date.strftime("%Y-%m-%d")
        print(f"🤒 {actor['name']} -> 병가 ({days}일)")

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

    # 최종 저장
    save_data_to_github(repo, STATUS_FILE, status_db, f"Update Status: {today}")
    save_data_to_github(repo, HISTORY_FILE, history_db, f"Update History: {today}")
    
    if repo:
        try:
            safe_title = result['title'].replace(" ", "_").replace(":", "").replace("/", "_")
            
            # [수정] pages/blog/ 경로로 파일명 생성
            filename = f"{POST_DIR}/{today}_{safe_title}.md"
            
            md_content = f"""---
layout: post
title: "{result['title']}"
date: {today}
author: {actor['name']}
categories: [{actor['role']}]
---

{result['content']}
"""
            repo.create_file(
                path=filename,
                message=f"Add post: {result['title']}",
                content=md_content,
                branch="main"
            )
            print(f"✅ 포스팅 업로드 성공: {filename}")
        except Exception as e:
            print(f"❌ 포스팅 업로드 실패: {e}")

if __name__ == "__main__":
    main()
