import json
import re

def generate_post(client, model_id, mode, actor, target_post=None, category=None, topic=None, affinity_score=70, ad_data=None):
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

    ad_instruction = ""
    if ad_data:
        ad_instruction = f"""
        [PPL Mission] Mention "{ad_data['name']}" ({ad_data['url']}) naturally.
        Context: {ad_data['context']}. Do NOT sound like a bot.
        """

    # 2. 모드별 프롬프트
    if mode == "new":
        task_prompt = f"""
        [Task: Create a New Post]
        Category: {category['desc']}
        Topic: {topic}
        {ad_instruction}
        
        Format:
        Title: [Title]
        Content: [Body]
        """
    
    elif mode == "reply":
        # 호감도에 따른 말투
        vibe = "Friendly" if affinity_score > 80 else "Cold" if affinity_score < 55 else "Normal"
        
        task_prompt = f"""
        [Task: Reply to a Post]
        You are replying to {target_post['author']}.
        Original Post: "{target_post['title']}"
        Original Content: "{target_post['content']}"
        
        Your Affinity: {affinity_score}/100 ({vibe})
        {ad_instruction}
        
        [IMPORTANT Rules for Reply]
        1. Start the content with a blockquote (>) summarizing the part you are replying to.
        2. Do NOT invent a new title. The system will handle the title. Only output the Content.
        
        Format:
        Content: [ > Quote original text here... \n\n Your reply body here...]
        At the very end, output JSON: ```json {{ "change": -2 to +2 }} ```
        """

    # 3. AI 호출
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
    except:
        return {"title": "Error", "content": "Server Error", "affinity_change": 0}

    # 4. 결과 파싱
    result = {"title": "", "content": "", "affinity_change": 0}
    
    # JSON 파싱 (호감도 변화)
    if mode == "reply":
        json_match = re.search(r"```json\s*({.*?})\s*```", full_text, re.DOTALL)
        if json_match:
            try:
                result["affinity_change"] = json.loads(json_match.group(1)).get("change", 0)
                full_text = full_text.replace(json_match.group(0), "") 
            except: pass

    # 텍스트 파싱
    lines = full_text.strip().split('\n')
    content_buffer = []
    
    for line in lines:
        if line.lower().startswith("title:") and mode == "new":
            result["title"] = line.split(":", 1)[1].strip()
        elif line.lower().startswith("content:"):
            pass 
        else:
            if line.strip():
                content_buffer.append(line)
    
    result["content"] = "\n".join(content_buffer).strip()
    
    # [수정됨] 답글일 경우, 제목을 AI가 짓지 않고 코드로 강제함 (Re: Logic)
    if mode == "reply":
        # 이미 Re:가 있으면 그대로 두고, 없으면 붙임 (Re: Re: 지원)
        original_title = target_post['title']
        result["title"] = f"Re: {original_title}"
        
    # 새 글인데 제목이 없으면 기본값
    if not result["title"] and mode == "new": 
        result["title"] = f"Update from {actor['name']}"

    if not result["content"]: result["content"] = full_text

    return result
