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

# [설정]
POST_DIR = "src/pages/blog" 
STATUS_FILE = "status.json"
HISTORY_FILE = "history.json"
POST_PROBABILITY = 0.58

# 1. GitHub 함수
def get_github_repo():
    if not config.GITHUB_TOKEN: return None
    auth = Auth.Token(config.GITHUB_TOKEN)
    g = Github(auth=auth)
    return g.get_repo(config.REPO_NAME)

def load_data_from_github(repo, filename, default_data):
    if not repo: return default_data
    try:
        contents = repo.get_contents(filename)
        json_str = contents.decoded_content.decode("utf-8")
        return json.loads(json_str)
    except: return default_data

def save_data_to_github(repo, filename, data, message):
    if not repo: return
    try:
        json_str = json.dumps(data, indent=2, ensure_ascii=False)
        try:
            contents = repo.get_contents(filename)
            repo.update_file(contents.path, message, json_str, contents.sha, branch="main")
            print(f"💾 {filename} 업데이트")
        except:
            repo.create_file(filename, message, json_str, branch="main")
            print(f"💾 {filename} 생성")
    except Exception as e: print(f"❌ {filename} 저장 실패: {e}")

# 2. 초기 데이터
def get_initial_status():
    data = {}
    for p in config.PERSONAS:
        data[p['id']] = {
            "state": "normal", 
            "return_date": None,
            "relationships": {t['id']: config.DEFAULT_AFFINITY for t in config.PERSONAS if t['id'] != p['id']}
        }
    return data

# 3. 메인 로직
def main():
    repo = get_github_repo()
    if not repo and config.GITHUB_TOKEN:
        print("❌ GitHub 연결 실패")
        return

    status_db = load_data_from_github(repo, STATUS_FILE, get_initial_status())
    history_db = load_data_from_github(repo, HISTORY_FILE, [])
    
    client = get_client()
    
    # ===============================================================
    # [긴급 수정] 모델 선택 안전장치 추가
    # model_selector가 리스트(['a', 'b'])를 반환하더라도
    # 여기서 강제로 첫 번째 요소('a')만 꺼내서 문자열로 만듭니다.
    # ===============================================================
    raw_model = get_dynamic_model(client)
    
    if isinstance(raw_model, list):
        model_id = raw_model  # 리스트면 첫 번째 것 선택
    else:
        model_id = raw_model     # 문자열이면 그대로 사용
        
    now = datetime.datetime.now()
    today_date = now.strftime("%Y-%m-%d")
    full_timestamp = now.strftime("%Y-%m-%d %H:%M:%S")

    # [디버깅] 이제 대괄호 [] 없이 모델명 하나만 깔끔하게 찍혀야 정상입니다.
    print(f"📅 Now: {full_timestamp} | Model: {model_id}")

    # 상태 체크
    returner = None
    active_members = []
    for pid, data in status_db.items():
        if data['return_date'] == today_date:
            data['state'] = "normal"
            data['return_date'] = None
            returner = pid
        if data['state'] == "normal": active_members.append(pid)

    if not active_members:
        print("😱 전원 부재중")
        save_data_to_github(repo, STATUS_FILE, status_db, f"Update status: All away {today_date}")
        return

    # 확률 체크
    if not returner:
        dice = random.random()
        if dice > POST_PROBABILITY:
            print(f"💤 휴식 (Dice: {dice:.2f})")
            return

    # 행동 결정
    mode = "new"
    actor_id = None
    target_post = None
    topic = None
    category = None
    
    if returner:
        mode = "new"
        actor_id = returner
        category = {"desc": "Returning."}
        topic = "I'm back"
    else:
        if history_db and random.random() < 0.4:
            mode = "reply"
            target_post = random.choice(history_db[-10:])
            candidates = [m for m in active_members if m != target_post['author_id']]
            if candidates: actor_id = random.choice(candidates)
            else: mode = "new"
        
        if mode == "new":
            actor_id = random.choice(active_members)
            r = random.random()
            cumulative = 0
            for key, val in config.CONTENT_CATEGORIES.items():
                cumulative += val['ratio']
                if r <= cumulative:
                    category = val
                    break
            topic = random.choice(config.TOPICS)

    actor = next(p for p in config.PERSONAS if p['id'] == actor_id)
    affinity_score = 70
    if mode == "reply":
        target_id = target_post['author_id']
        affinity_score = status_db[actor_id]['relationships'].get(target_id, 70)

    print(f"🚀 Mode: {mode.upper()} | Actor: {actor['name']}")

    # AI 생성 (model_id는 이제 무조건 문자열입니다)
    result = generate_post(
        client, model_id, mode, actor, 
        target_post=target_post, 
        category=category,
        topic=topic,
        affinity_score=affinity_score,
        ad_data=random.choice(config.PROMOTED_SITES) if config.AD_MODE else None
    )

    if result['title'] == "Error" or "Error" in result['title']:
        print("❌ AI 생성 실패로 인해 이번 턴은 건너뜁니다.")
        return

    final_title = f"{result['mood']} {result['title']}"
    print(f"📝 Title: {final_title}")

    # 데이터 업데이트 (호감도)
    if mode == "reply" and result['affinity_change'] != 0:
        target_id = target_post['author_id']
        change = result['affinity_change']
        curr_a = status_db[actor_id]['relationships'].get(target_id, 70)
        curr_b = status_db[target_id]['relationships'].get(actor_id, 70)
        new_a = max(config.AFFINITY_MIN, min(curr_a + change, config.AFFINITY_MAX))
        new_b = max(config.AFFINITY_MIN, min(curr_b + change, config.AFFINITY_MAX))
        status_db[actor_id]['relationships'][target_id] = new_a
        status_db[target_id]['relationships'][actor_id] = new_b

    # 휴가/병가
    dice = random.random()
    if dice < config.VACATION_CHANCE:
        days = random.randint(3, 7)
        ret_date = datetime.datetime.now() + datetime.timedelta(days=days)
        status_db[actor_id]['state'] = "vacation"
        status_db[actor_id]['return_date'] = ret_date.strftime("%Y-%m-%d")
        print(f"✈️ 휴가: {actor['name']}")
    elif dice < config.VACATION_CHANCE + config.SICK_CHANCE:
        days = random.randint(1, 2)
        ret_date = datetime.datetime.now() + datetime.timedelta(days=days)
        status_db[actor_id]['state'] = "sick"
        status_db[actor_id]['return_date'] = ret_date.strftime("%Y-%m-%d")
        print(f"🤒 병가: {actor['name']}")

    new_log = {
        "id": datetime.datetime.now().timestamp(),
        "date": full_timestamp, 
        "author": actor['name'],
        "author_id": actor['id'],
        "title": result['title'],
        "content": result['content']
    }
    history_db.insert(0, new_log)
    if len(history_db) > config.HISTORY_LIMIT: history_db.pop()

    save_data_to_github(repo, STATUS_FILE, status_db, f"Update Status: {today_date}")
    save_data_to_github(repo, HISTORY_FILE, history_db, f"Update History: {today_date}")
    
    if repo:
        try:
            safe_name = actor['name'].lower().replace(" ", "")
            random_id = random.randint(1000, 9999)
            filename = f"{POST_DIR}/{today_date}-{safe_name}-{random_id}.md"
            
            md_content = f"""---
layout: ../../layouts/BlogPostLayout.astro
title: "{final_title}"
author: {actor['name']}
date: "{full_timestamp}"
category: Daily Log
tags: {json.dumps(result['tags'], ensure_ascii=False)}
location: {actor['country']}
---

{result['content']}
"""
            repo.create_file(filename, f"Add post: {final_title}", md_content, branch="main")
            print(f"✅ 업로드 성공: {filename}")
        except Exception as e:
            print(f"❌ 업로드 실패: {e}")

if __name__ == "__main__":
    main()
