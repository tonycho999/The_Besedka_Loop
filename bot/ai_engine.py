import json
import re
import time

def extract_content(completion):
    """
    [안전 파싱 함수]
    AI 응답이 객체, 딕셔너리, 리스트 등 어떤 형태로 오든 내용만 문자열로 추출
    """
    try:
        # 1. 표준 객체 접근
        if hasattr(completion, 'choices'):
            choices = completion.choices
            if isinstance(choices, list) and len(choices) > 0:
                first_choice = choices
                
                # choices이 객체인 경우
                if hasattr(first_choice, 'message'):
                    return str(first_choice.message.content)
                
                # choices이 딕셔너리인 경우
                if isinstance(first_choice, dict):
                    message = first_choice.get('message', {})
                    if isinstance(message, dict):
                        return str(message.get('content', ''))
                    return str(message)

                # choices이 리스트인 경우
                if isinstance(first_choice, list):
                    if len(first_choice) > 0:
                        return str(first_choice)
                    return ""

        # 2. 딕셔너리 접근
        if isinstance(completion, dict):
            choices = completion.get('choices', [])
            if choices:
                return str(choices.get('message', {}).get('content', ''))

    except Exception as e:
        print(f"⚠️ 파싱 중 에러 발생: {e}")
    
    return ""

def generate_post(client, model_id, mode, actor, target_post=None, category=None, topic=None, affinity_score=70, ad_data=None):
    
    # 모델명 정리
    if isinstance(model_id, list): model_id = model_id
    model_id = str(model_id).strip()
    
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

    # 2. 프롬프트 구성
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

    # 3. AI 호출 (3회 재시도)
    full_text = ""
    success = False
    
    for attempt in range(3):
        try:
            completion = client.chat.completions.create(
                messages=[{"role": "system", "content": base_prompt}, {"role": "user", "content": task_prompt}],
                model=model_id, 
                temperature=0.9
            )
            
            content = extract_content(completion)
            
            if content:
                full_text = content
                success = True
                break
            else:
                print(f"⚠️ 빈 응답 수신 ({attempt+1}/3)")
                time.sleep(1)

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
        # [핵심 수정 구간] 제목이 없으면 내용에서 추출 (에러 방지 로직 적용)
        if not result["title"] or "Update from" in result["title"]:
            if result["content"]:
                try:
                    # 1. 내용을 문자열로 확실히 변환
                    content_str = str(result["content"])
                    # 2. 마침표로 문장 분리
                    sentences = content_str.split('.')
                    # 3. 첫 번째 문장 선택 (리스트가 비어있지 않은지 확인)
                    if sentences:
                        first_sentence = sentences.strip()
                        # 4. 단어로 분리해서 6단어만 추출
                        words = first_sentence.split()
                        short_title = " ".join(words[:6])
                        result["title"] = short_title + "..."
                    else:
                        result["title"] = topic
                except Exception as e:
                    print(f"⚠️ 제목 생성 중 오류 (기본값 사용): {e}")
                    result["title"] = topic
            else:
                result["title"] = topic

    if not result["content"]: result["content"] = full_text

    return result
