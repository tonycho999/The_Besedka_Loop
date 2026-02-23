import model_selector  # 아까 분리한 모델 선택기

def generate_content(persona, type="post", context=""):
    try:
        # 1. 모델과 클라이언트를 동적으로 가져옴
        client = model_selector.get_client()
        model_id = model_selector.get_dynamic_model(client)
        
        print(f"🤖 Selected Model: {model_id}") # 로그 확인용

        prompt = ""
        
        if type == "post":
            # [규칙] 날씨 금지, 개발자 일상
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

        # [수정됨] 여기가 핵심! Gemini 방식(model.generate...)을 버리고 Groq 방식 사용
        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            model=model_id, # 동적으로 받아온 모델 ID
            temperature=0.7,
        )

        # 응답 데이터 추출 (Groq 구조에 맞춤)
        full_text = chat_completion.choices[0].message.content.strip()

        if type == "post":
            lines = full_text.split('\n')
            topic = lines[0] if lines else "Dev Log"
            return full_text, topic
            
        return full_text, ""

    except Exception as e:
        # 여기가 실행되면 로그에 정확한 이유가 찍힘
        print(f"❌ AI Logic Error: {e}")
        return "System Error", "Error"
