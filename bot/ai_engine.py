import json
import re

def generate_post(client, model_id, mode, actor, target_post=None, category=None, topic=None, affinity_score=70):
    """
    AI를 사용하여 게시글 또는 답글을 생성하는 핵심 함수
    mode: 'new' (새 글) / 'reply' (답글)
    """

    # 1. 페르소나 기본 설정
    base_prompt = f"""
    You are {actor['name']} ({actor['role']}, {actor['country']}).
    Personality: {actor['style']}.
    Native Language: {actor['lang']}.
    
    [Rules]
    1. Write a short, casual developer community post.
    2. Mix English with a few native words naturally (Greetings, exclamations).
    3. NO weather talk. NO time in title (e.g., [10:00]).
    4. Keep it realistic and human-like.
    """

    # 2. 모드별 프롬프트 분기
    if mode == "new":
        task_prompt = f"""
        [Task: Create a New Post]
        Category: {category['desc']}
        Topic Seed: {topic}
        
        Format:
        Title: [Short & Catchy Title]
        Content: [1-4 lines of body text]
        """
    
    elif mode == "reply":
        # 호감도에 따른 말투 가이드
        vibe = "Professional"
        if affinity_score >= 85: vibe = "Super friendly, joking, bro-like"
        elif affinity_score <= 55: vibe = "Cold, sarcastic, short"
        
        task_prompt = f"""
        [Task: Reply to a Post]
        You are replying to '{target_post['author']}'.
        Original Title: "{target_post['title']}"
        Original Content: "{target_post['content']}"
        
        Current Affinity: {affinity_score}/100 ({vibe})
        
        Format:
        Title: Re: {target_post['title']}
        Content: [1-5 lines reply. React based on affinity.]
        
        [IMPORTANT]
        At the end, output JSON for affinity change (-3 to +3).
        Example: ```json {{ "change": 2 }} ```
        """

    # 3. API 호출
    try:
        completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": base_prompt},
                {"role": "user", "content": task_prompt}
            ],
            model=model_id,
            temperature=0.8, # 창의성 확보
        )
        full_text = completion.choices[0].message.content
    except Exception as e:
        return {"title": "Error", "content": "AI Server Error...", "affinity_change": 0}

    # 4. 결과 파싱 (Title, Content, JSON)
    result = {"title": "", "content": "", "affinity_change": 0}
    
    # 답글일 경우 JSON(호감도 변화) 추출
    if mode == "reply":
        json_match = re.search(r"```json\s*({.*?})\s*```", full_text, re.DOTALL)
        if json_match:
            try:
                data = json.loads(json_match.group(1))
                result["affinity_change"] = data.get("change", 0)
                full_text = full_text.replace(json_match.group(0), "") # 본문에서 JSON 제거
            except: pass

    # 제목/내용 분리
    lines = full_text.strip().split('\n')
    content_buffer = []
    
    for line in lines:
        if line.lower().startswith("title:"):
            result["title"] = line.split(":", 1)[1].strip()
        elif line.lower().startswith("content:"):
            pass # "Content:" 라인은 건너뜀
        else:
            if line.strip():
                content_buffer.append(line)
    
    result["content"] = "\n".join(content_buffer).strip()
    
    # 파싱 실패 시 기본값 처리
    if not result["title"]: 
        if mode == "reply": result["title"] = f"Re: {target_post['title']}"
        else: result["title"] = f"Update from {actor['name']}"
        
    if not result["content"]: result["content"] = full_text

    return result
