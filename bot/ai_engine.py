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
            # [랜덤 결정] 오늘은 긴 글을 쓸까? (30% 확률)
            is_long_post = random.random() < 0.3
            
            if is_long_post:
                # [긴 글 모드]
                length_instruction = """
                - LENGTH: Long and detailed (10-15 sentences).
                - CONTENT: Tell a specific story about a coding problem, a tech philosophy, or a workspace incident.
                - TONE: Thoughtful, storytelling, immersive.
                """
                topic_instruction = "TOPICS: Refactoring legacy code, Learning Rust/Go, Burnout & Recovery, Open Source contribution, Team conflict resolution."
                print("   📝 Mode: Long Essay")
            else:
                # [짧은 글 모드]
                length_instruction = """
                - LENGTH: Very short and quick (3-4 sentences).
                - CONTENT: Just a quick status update or a fleeting thought.
                - TONE: Casual, murmuring, minimalist.
                """
                topic_instruction = "TOPICS: Coding bugs, Coffee, Late night work, Server crash, Simple Git issues."
                print("   📝 Mode: Short Log")

            prompt = f"""
            You are {persona['name']}, a developer from {persona['country']}.
            Write a blog post diary (Daily Log).
            
            [STRICT RULES]
            1. NEVER mention weather (No rain, sun, wind, snow).
            2. {topic_instruction}
            3. {length_instruction}
            4. FORMAT: 
               - First line: Creative Title (No quotes)
               - Second line onwards: Content.
            5. Do NOT start with symbols like ',' or '.'.
            """
        
        elif type == "comment":
            prompt = f"""
            You are {persona['name']}, a developer.
            Write a 1-sentence comment on the post: "{context}".
            Casual tone, no weather talk. React like a colleague.
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
            topic = lines[0] if lines else "Dev Log"
            return full_text, topic
            
        return full_text, ""

    except Exception as e:
        print(f"❌ AI Logic Error: {e}")
        return "System Error", "Error"
