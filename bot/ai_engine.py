import json
import re

def generate_post(client, model_id, mode, actor, target_post=None, category=None, topic=None, affinity_score=70, ad_data=None):
    """
    ad_data: 광고 정보가 들어오면 PPL 프롬프트 추가
    """

    # 1. 페르소나 기본 설정
    base_prompt = f"""
    You are {actor['name']} ({actor['role']}, {actor['country']}).
    Personality: {actor['style']}.
    Native Language: {actor['lang']}.
    
    [Rules]
    1. Write a short, casual developer community post.
    2. Mix English with a few native words naturally.
    3. NO weather talk. NO time in title.
    4. Keep it realistic.
    """

    # ==========================================
    # [핵심] 자연스러운 광고 주입 로직
    # ==========================================
    ad_instruction = ""
    if ad_data:
        ad_instruction = f"""
        [HIDDEN MISSION (PPL)]
        Naturally mention the service "{ad_data['name']}" ({ad_data['url']}) in your post.
        Description: {ad_data['desc']}.
        Context Hint: {ad_data['context']}.
        
        CRITICAL: 
        - Do NOT sound like a salesman or a bot. 
        - Mention it casually as a personal experience or a tip for a friend.
        - Example: "I was struggling with X, but found Y, it was cool."
        - The link must be included.
        """

    # 2. 모드별 프롬프트 분기
    if mode == "new":
        task_prompt = f"""
        [Task: Create a New Post]
        Category: {category['desc']}
        Topic Seed: {topic}
        
        {ad_instruction}
        
        Format:
        Title: [Short & Catchy Title]
        Content: [1-4 lines of body text]
        """
    
    elif mode == "reply":
        vibe = "Professional"
        if affinity_score >= 85: vibe = "Super friendly, joking, bro-like"
        elif affinity_score <= 55: vibe = "Cold, sarcastic, short"
        
        task_prompt = f"""
        [Task: Reply to a Post]
        You are replying to '{target_post['author']}'.
        Original Title: "{target_post['title']}"
        Original Content: "{target_post['content']}"
        
        Current Affinity: {affinity_score}/100 ({vibe})
        
        {ad_instruction}
        
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
            temperature=0.8,
        )
        full_text = completion.choices[0].message.content
    except Exception as e:
        return {"title": "Error", "content": "AI Server Error...", "affinity_change": 0}

    # 4. 결과 파싱 (기존 로직 동일)
    result = {"title": "", "content": "", "affinity_change": 0}
    
    if mode == "reply":
        json_match = re.search(r"```json\s*({.*?})\s*```", full_text, re.DOTALL)
        if json_match:
            try:
                data = json.loads(json_match.group(1))
                result["affinity_change"] = data.get("change", 0)
                full_text = full_text.replace(json_match.group(0), "")
            except: pass

    lines = full_text.strip().split('\n')
    content_buffer = []
    
    for line in lines:
        if line.lower().startswith("title:"):
            result["title"] = line.split(":", 1)[1].strip()
        elif line.lower().startswith("content:"):
            pass
        else:
            if line.strip():
                content_buffer.append(line)
    
    result["content"] = "\n".join(content_buffer).strip()
    
    if not result["title"]: 
        if mode == "reply": result["title"] = f"Re: {target_post['title']}"
        else: result["title"] = f"Update from {actor['name']}"
    if not result["content"]: result["content"] = full_text

    return result
