import os
import json
import random
import datetime
from dotenv import load_dotenv
from github import Github

# 로컬 모듈 임포트
import config
from ai_engine import generate_post

# [사용자 요청] model_selector는 제외했으므로, 
# 같은 폴더에 model_selector.py가 있다고 가정하고 임포트
try:
    from model_selector import get_groq_client, get_dynamic_model
except ImportError:
    print("⚠️ model_selector.py를 찾을 수 없습니다.")
    exit()

load_dotenv()

# 파일 경로 정의
STATUS_FILE = "status.json"
HISTORY_FILE = "history.json"

# ==========================================
# 1. 데이터 관리 함수 (Load/Save)
# ==========================================
def load_json(filename, default):
    if not os.path.exists(filename): return default
    with open(filename, 'r', encoding='utf-8') as f: return json.load(f)

def save_json(filename, data):
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def get_initial_status():
    """초기 상태 생성 (최초 실행 시)"""
    data = {}
    for p in config.PERSONAS:
        data[p['id']] = {
            "state": "normal", # normal, vacation, sick
            "return_date": None,
            # 다른 멤버들과의 관계 초기화
            "relationships": {t['id']: config.DEFAULT_AFFINITY for t in config.PERSONAS if t['id'] != p['id']}
        }
    return data

def push_to_github(filename, content):
    """GitHub 업로드 함수"""
    if not config.GITHUB_TOKEN:
        print("⚠️ GitHub Token 없음 - 로컬 출력으로 대체")
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
    # 1. API 클라이언트 및 모델 준비
    client = get_groq_client()
    model_id = get_dynamic_model(client)
    
    # 2. 데이터 로드
    status_db = load_json(STATUS_FILE, get_initial_status())
    history_db = load_json(HISTORY_FILE, []) # 최근 게시글 리스트
    today = datetime.datetime.now().strftime("%Y-%m-%d")

    print(f"📅 Date: {today} | Model: {model_id}")

    # 3. 멤버 상태 체크 (복귀자 확인)
    returner = None
    active_members = []
    
    for pid, data in status_db.items():
        # 복귀 날짜 체크
        if data['return_date'] == today:
            print(f"✨ {pid}님이 복귀했습니다!")
            data['state'] = "normal"
            data['return_date'] = None
            returner = pid
        
        # 활동 가능한 멤버(정상 상태)만 추림
        if data['state'] == "normal":
            active_members.append(pid)

    if not active_members:
        print("😱 모든 멤버가 휴가/병가 중입니다! (활동 불가)")
        return

    # 4. 행동 결정 (New Post vs Reply)
    mode = "new"
    actor_id = None
    target_post = None
    topic = None
    category = None
    
    # [Case A] 복귀자가 있으면 무조건 복귀 신고식
    if returner:
        mode = "new"
        actor_id = returner
        category = {"desc": "Returning from vacation/sick leave. Feeling fresh or tired."}
        topic = "I'm back"
    
    # [Case B] 일반 상황: 40% 확률로 답글 작성 (단, 역사가 있어야 함)
    else:
        if history_db and random.random() < 0.4:
            mode = "reply"
            # 최근 10개 글 중 하나 선택 (떡밥 물기)
            target_post = random.choice(history_db[-10:])
            
            # 원글 작성자가 아닌 사람 중에서 선택
            candidates = [m for m in active_members if m != target_post['author_id']]
            if candidates:
                actor_id = random.choice(candidates)
            else:
                mode = "new" # 후보가 없으면 새 글로 전환
        
        # [Case C] 새 글 작성 (60% 또는 답글 실패 시)
        if mode == "new":
            actor_id = random.choice(active_members)
            # 카테고리 가중치 뽑기
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

    # 5. 페르소나 객체 가져오기
    actor = next(p for p in config.PERSONAS if p['id'] == actor_id)
    
    print(f"🚀 Mode: {mode.upper()} | Actor: {actor['name']}")
    
    # 호감도 조회 (답글인 경우)
    affinity_score = 70
    if mode == "reply":
        target_id = target_post['author_id']
        affinity_score = status_db[actor_id]['relationships'].get(target_id, 70)
        print(f"   Target: {target_post['author']} (Current Affinity: {affinity_score})")

    # ----------------------------------------------
    # 6. AI 생성 요청 (AI Engine)
    # ----------------------------------------------
    result = generate_post(
        client, model_id, mode, actor, 
        target_post=target_post, 
        category=category,
        topic=topic,
        affinity_score=affinity_score
    )

    # 7. 결과 출력
    print(f"\nTitle: {result['title']}")
    print("-" * 30)
    print(result['content'])
    print("-" * 30)

    # 8. 후처리 및 데이터 업데이트
    
    # A. 호감도 업데이트 (답글인 경우)
    if mode == "reply" and result['affinity_change'] != 0:
        target_id = target_post['author_id']
        change = result['affinity_change']
        
        # 양방향 업데이트 (서로에 대한 인상 변화)
        curr_a = status_db[actor_id]['relationships'].get(target_id, 70)
        curr_b = status_db[target_id]['relationships'].get(actor_id, 70)
        
        # Clamp (Min~Max 제한)
        new_a = max(config.AFFINITY_MIN, min(curr_a + change, config.AFFINITY_MAX))
        new_b = max(config.AFFINITY_MIN, min(curr_b + change, config.AFFINITY_MAX))
        
        status_db[actor_id]['relationships'][target_id] = new_a
        status_db[target_id]['relationships'][actor_id] = new_b
        print(f"📊 Affinity Updated: {change} point(s) applied.")

    # B. 랜덤 이벤트 (휴가/병가) - 글 쓴 사람에게만 발생
    dice = random.random()
    if dice < config.VACATION_CHANCE:
        days = random.randint(3, 7)
        ret_date = datetime.datetime.now() + datetime.timedelta(days=days)
        status_db[actor_id]['state'] = "vacation"
        status_db[actor_id]['return_date'] = ret_date.strftime("%Y-%m-%d")
        print(f"✈️ {actor['name']} is going on VACATION for {days} days!")
        
    elif dice < config.VACATION_CHANCE + config.SICK_CHANCE:
        days = random.randint(1, 2)
        ret_date = datetime.datetime.now() + datetime.timedelta(days=days)
        status_db[actor_id]['state'] = "sick"
        status_db[actor_id]['return_date'] = ret_date.strftime("%Y-%m-%d")
        print(f"🤒 {actor['name']} is SICK for {days} days.")

    # C. 역사 기록 (History)
    new_log = {
        "id": datetime.datetime.now().timestamp(),
        "date": today,
        "author": actor['name'],
        "author_id": actor['id'],
        "title": result['title'],
        "content": result['content']
    }
    history_db.insert(0, new_log) # 최신 글을 맨 앞에 추가
    if len(history_db) > config.HISTORY_LIMIT:
        history_db.pop() # 오래된 글 삭제

    # D. 파일 저장
    save_json(STATUS_FILE, status_db)
    save_json(HISTORY_FILE, history_db)
    
    # E. GitHub 업로드
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
