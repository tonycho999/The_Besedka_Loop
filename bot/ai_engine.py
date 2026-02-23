import model_selector  # 위에서 만든 모듈 사용

def generate_content(persona, type="post", context=""):
    try:
        # 1. 클라이언트와 모델 ID를 동적으로 받아옴
        client = model_selector.get_client()
        model_id = model_selector.get_dynamic_model(client)
        
        print(f"🤖 Connected to Model: {model_id}")

        prompt = ""
        
        # 프롬프트 설정 (이전과 동일)
        if type == "post":
            prompt = f"""
            You are {persona['name']}, a developer from {persona['country']}.
            Write a short blog post diary (Daily Log).
            
            [STRICT RULES]
            1. NEVER mention weather (No rain, sun, wind, snow, temperature).
            2. TOPICS: Coding bugs, Server crash, New framework, Coffee, Late night coding, Git issues.
            3. STYLE: Casual, short sentences, like a developer's murmuring.
            4. FORMAT: 
               - First line: Title (No quotes)
               - Second line onwards: Content (3-4 sentences).
            5. Do NOT start with symbols like ',' or '.'.
            """
        
        elif type == "comment":
            prompt = f"""
            You are {persona['name']}, a developer.
            Write a 1-sentence comment on the post: "{context}".
            Casual tone, no weather talk.
            """

        # 2. 받아온 model_id로 요청 전송
        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            model=model_id, # 여기에 'llama...' 같은 문자열 없음. 변수만 있음.
            temperature=0.7,
        )

        # 3. 결과 반환
        full_text = chat_completion.choices[0].message.content.strip()

        if type == "post":
            lines = full_text.split('\n')
            topic = lines[0] if lines else "Dev Log"
            return full_text, topic
            
        return full_text, ""

    except Exception as e:
        print(f"❌ AI Generation Error: {e}")
        return "System Error: AI needs sleep.", "Error"
