import model_selector
import random

def generate_content(persona, type="post", context=""):
    try:
        # 1. 모델 동적 선택
        client = model_selector.get_client()
        model_id = model_selector.get_dynamic_model(client)
        
        print(f"🤖 Selected Model: {model_id}")

        prompt = ""
        
        if type == "post":
            # [랜덤] 30% 확률로 '사생활(Life)' 모드 발동
            mode = "life" if random.random() < 0.3 else "dev"
            
            if mode == "life":
                # [사생활 모드] 코딩 이야기 금지!
                topic_instruction = """
                - TOPICS: Gaming (Steam, Console), Late night snacks (Ramen, Pizza), Gym/Workout, 
                          Netflix/Movies, Cat/Dog, Traffic jam, Just tired, Weekend plans.
                - STRICT RULE: Do NOT talk about coding, bugs, or servers. Just behave like a human.
                - TONE: Casual, short, funny, or emotional.
                """
                print("   🍺 Mode: Private Life (No Coding)")
                
            else:
                # [개발 모드] 기존 유지
                topic_instruction = """
                - TOPICS: Coding bugs, Server crash, New framework, Coffee, Late night coding, Git issues.
                - TONE: Professional but tired, geeky.
                """
                print("   💻 Mode: Dev Log")

            prompt = f"""
            You are {persona['name']}, living in {persona['country']}.
            Write a short blog post diary (Daily Log).
            
            [RULES]
            1. NEVER mention weather (No rain, sun, snow).
            2. {topic_instruction}
            3. FORMAT: 
               - First line: Creative Title (No quotes)
               - Second line onwards: Content (3-4 sentences).
            4. Do NOT start with symbols like ',' or '.'.
            """
        
        elif type == "comment":
            # 댓글도 상황에 따라 사적인 반응 허용
            prompt = f"""
            You are {persona['name']}.
            Write a 1-sentence comment on the post: "{context}".
            Tone: Casual, friendly, like a real friend.
            """

        # 2. Groq API 호출
        chat_completion = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model=model_id,
            temperature=0.7,
        )

        full_text = chat_completion.choices[0].message.content.strip()

        if type == "post":
            lines = full_text.split('\n')
            topic = lines[0] if lines else "Daily Log"
            return full_text, topic
            
        return full_text, ""

    except Exception as e:
        print(f"❌ AI Logic Error: {e}")
        return "System Error", "Error"
