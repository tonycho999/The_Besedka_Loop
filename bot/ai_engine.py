import json
import re
import time

def generate_post(client, model_id, mode, actor, target_post=None, category=None, topic=None, affinity_score=70, ad_data=None):
    # ==============================================================================
    # [최후의 안전장치] 형님, 여기가 핵심입니다.
    # 외부에서 리스트를 주든, 이상한 걸 주든 여기서 무조건 '문자열 하나'로 만듭니다.
    # ==============================================================================
    if isinstance(model_id, list):
        print(f"⚠️ [System Fix] 리스트로 들어온 모델명을 자동으로 변환합니다: {model_id} -> {model_id}")
        model_id = model_id  # 리스트의 첫 번째 요소 선택
    
    # 혹시 모를 공백 제거 및 문자열 확실화
    model_id = str(model_id).strip()
    
    # [디버깅] 실제 API로 날아가는 모델명이 무엇인지 눈으로 확인
    print(f"👉 API Request Model: '{model_id}' (Type: {type(model_id).__name__})")
    # ==============================================================================

    # 1. 페르소나 설정
    base_prompt = f"""
    You are {actor['name']} ({actor['role']}, {actor['country']}).
    Personality: {actor['style']}.
    Native Language: {actor['lang']}.
    
    [CRITICAL Rules]
    1. NO formal greetings. Start directly.
    2. Keep it casual, cynical, developer vibe.
    3. Use code blocks (```) for tech.
    4. Use @mentions for reply.
    5. Add "TL;DR" if long.
    6. NEVER use titles like "Update from {actor['name']}". Create a real, catchy title.
    """

    ad_instruction = ""
    if ad_data:
        ad_instruction = f"""
        [PPL] Mention "{ad_data['name']}" naturally. Context: {ad_data['context']}
        """

    # 2. 모드별 프롬프트 구성
    if mode == "new":
        task_prompt = f"""
        [Task: New Post]
        Category: {category['desc']}
        Topic: {topic}
        {ad_instruction}
        
        Format:
        Title: [Creative & Short Title]
        Content: [Body]
        JSON: ```json {{ "tags": ["tag1", "tag2"], "mood": "emoji" }} ```
        """
    elif mode == "reply":
        vibe = "Friendly" if affinity_score > 80 else "Cynical" if affinity_score < 55 else "Normal"
        task_prompt = f"""
        [Task: Reply]
        To: {target_post['author']}
        Original: "{target_post['title']}"
        Affinity: {affinity_score}/100 ({vibe})
        {ad_instruction}
        
        [Rules]
        1. Quote original post with >.
        2. Mention author @{target_post['author']}.
        
        Format:
        Content: [Body]
        JSON: ```json {{ "change": -2 to +2, "tags": ["tag1", "tag2"], "mood": "emoji" }} ```
        """

    # 3. AI 호출 (3회 재시도 로직)
    full_text = ""
    success = False
    
    for attempt in range(3):
        try:
            # 형님, 여기서 model=model_id 부분이 핵심입니다. 위에서 정제한 model_id가 들어갑니다.
            completion = client.chat.completions.create(
                messages=[{"role": "system", "content": base_prompt}, {"role": "user", "content": task_prompt}],
                model=model_id, 
                temperature=0.9
            )
            full_text = completion.choices.message.content
            success = True
            break
        except Exception as e:
            print(f"⚠️ AI 호출 실패 ({attempt+1}/3): {e}")
            time.sleep(2)

    if not success:
        return {"title": "Error", "content": "Server Error", "affinity_change": 0, "tags": [], "mood": "🤖"}

    # 4. 결과 파싱
    result = {"title": "", "content": "", "affinity_change": 0, "tags": ["Daily Log"], "mood": "😐"}
    
    json_match = re.search(r"```json\s*({.*?})\s*```", full_text, re.DOTALL)
    if json_match:
        try:
            data = json.loads(json_match.group(1))
            result["affinity_change"] = data.get("change", 0)
            result["tags"] = data.get("tags", ["Daily Log"])
            result["mood"] = data.get("mood", "😐")
            full_text = full_text.replace(json_match.group(0), "") 
        except: pass

    lines = full_text.strip().split('\n')
    content_buffer = []
    for line in lines:
        if line.lower().startswith("title:") and mode == "new":
            result["title"] = line.split(":", 1).strip()
        elif line.lower().startswith("content:"): pass 
        else:
            if line.strip(): content_buffer.append(line)
    
    result["content"] = "\n".join(content_buffer).strip()
    
    if mode == "reply":
        result["title"] = f"Re: {target_post['title']}"
    else:
        # 제목 누락 시 본문 내용이나 주제로 대체
        if not result["title"] or "Update from" in result["title"]:
            if result["content"]:
                first_sentence = result["content"].split('.')
                words = first_sentence.split()[:6]
                result["title"] = " ".join(words) + "..."
            else:
                result["title"] = topic

    if not result["content"]: result["content"] = full_text

    return result
