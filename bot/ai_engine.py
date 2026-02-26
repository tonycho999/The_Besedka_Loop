import json
import re
import time  # [추가] 재시도 대기용

def generate_post(client, model_id, mode, actor, target_post=None, category=None, topic=None, affinity_score=70, ad_data=None):
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
    """

    ad_instruction = ""
    if ad_data:
        ad_instruction = f"""
        [PPL] Mention "{ad_data['name']}" naturally. Context: {ad_data['context']}
        """

    # 2. 모드별 프롬프트
    if mode == "new":
        task_prompt = f"""
        [Task: New Post]
        Category: {category['desc']}
        Topic: {topic}
        {ad_instruction}
        
        Format:
        Title: [Title]
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
            completion = client.chat.completions.create(
                messages=[{"role": "system", "content": base_prompt}, {"role": "user", "content": task_prompt}],
                model=model_id, temperature=0.9
            )
            full_text = completion.choices[0].message.content
            success = True
            break  # 성공하면 탈출
        except Exception as e:
            print(f"⚠️ AI 호출 실패 ({attempt+1}/3): {e}")
            time.sleep(2)  # 2초 휴식 후 재시도

    # 3번 다 실패했을 경우
    if not success:
        print("❌ 최종 실패: AI 응답을 받아오지 못했습니다.")
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
            result["title"] = line.split(":", 1)[1].strip()
        elif line.lower().startswith("content:"): pass 
        else:
            if line.strip(): content_buffer.append(line)
    
    result["content"] = "\n".join(content_buffer).strip()
    
    if mode == "reply": result["title"] = f"Re: {target_post['title']}"
    if not result["title"] and mode == "new": result["title"] = f"Update from {actor['name']}"
    if not result["content"]: result["content"] = full_text

    return result
