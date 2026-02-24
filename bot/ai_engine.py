import model_selector
import random

def generate_content(persona, mode="life", context_title="", context_body="", context_author="", relation_type="colleague"):
    try:
        # 1. 모델 동적 선택
        client = model_selector.get_client()
        model_id = model_selector.get_dynamic_model(client)
        
        print(f"🤖 Selected Model: {model_id}")

        prompt = ""
        
        # --- [모드 1] 답글 달기 (Reply) ---
        if mode == "reply":
            # 답글 길이 랜덤 (1~5 문장)
            reply_length = random.randint(1, 5)
            
            # 관계에 따른 말투 설정
            tone_instruction = "Casual and friendly."
            if relation_type == "romance":
                tone_instruction = "Caring, subtle affection, warm tone."
            elif relation_type == "rival":
                tone_instruction = "Teasing, bickering, sarcastic but friendly."
            elif relation_type == "bestie":
                tone_instruction = "Playful, slang, very short and fast."
            
            prompt = f"""
            You are {persona['name']} from {persona['country']}.
            You are writing a REPLY post to your colleague {context_author}.
            
            [CONTEXT - The Post you are replying to]
            Title: {context_title}
            Content: "{context_body}"
            
            [YOUR ROLE]
            - Relationship with {context_author}: {relation_type} ({tone_instruction}).
            - TASK: Write a reply post responding to the content above.
            - LENGTH: {reply_length} sentences (Keep it natural).
            - STRICT RULE: Do NOT start with "Hi" or "Hello". Just dive into the conversation.
            - TITLE: Must be "Re: {context_title}" (Do not output title in the body, just content).
            """
            
            print(f"   🗣️ Mode: Reply to {context_author} ({relation_type})")

        # --- [모드 2] 사생활 (Life) ---
        elif mode == "life":
            prompt = f"""
            You are {persona['name']}, living in {persona['country']}.
            Write a blog post about your PRIVATE LIFE.
            
            [TOPICS]
            Gaming, Late night snacks, Netflix/Movies, Weekend plans, Cat/Dog, Traffic jam, Just woke up.
            
            [RULES]
            1. STRICTLY NO CODING talk. Behave like a normal human.
            2. TONE: Casual, emotional, or funny.
            3. LENGTH: 3-5 sentences.
            4. TITLE: Creative title (No specific time like '02:00').
            """
            print("   🍺 Mode: Private Life")

        # --- [모드 3] 업무 고충 (Work Struggle) ---
        elif mode == "work":
            prompt = f"""
            You are {persona['name']}, a developer.
            Write a short rant about CODING STRUGGLES.
            
            [TOPICS]
            Legacy code, Server crash, Endless bugs, Deploy failed, Coffee overdose.
            
            [RULES]
            1. TONE: Frustrated, tired, or desperate.
            2. LENGTH: 2-4 sentences.
            3. TITLE: Short and punchy (e.g., "Why me?", "Spaghetti Code").
            """
            print("   💼 Mode: Work Struggle")

        # --- [모드 4] 정보/잡담 (Info) ---
        elif mode == "info":
            prompt = f"""
            You are {persona['name']}.
            Write a casual post sharing a small thought or info.
            
            [TOPICS]
            New keyboard, cool website found, weather feeling, music recommendation.
            
            [RULES]
            1. TONE: Calm and sharing.
            2. LENGTH: 3-4 sentences.
            3. TITLE: Interesting title.
            """
            print("   ℹ️ Mode: Info/Chat")

        # 공통 포맷팅 규칙
        prompt += """
        
        [FORMAT]
        - First line: Title (If reply, use 'Re: ...')
        - Second line onwards: Content.
        - Do NOT include symbols like quotes or markdown bolding in the Title.
        """

        # 2. Groq API 호출
        chat_completion = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model=model_id,
            temperature=0.7,
        )

        full_text = chat_completion.choices[0].message.content.strip()
        lines = full_text.split('\n')
        
        # 제목/본문 분리
        if lines:
            generated_title = lines[0].strip().replace('"', '').replace("Title: ", "")
            generated_body = "\n".join(lines[1:]).strip()
            
            # 답글 모드일 때 제목 강제 고정 (AI가 딴소리 못하게)
            if mode == "reply":
                clean_context_title = context_title.replace("Re: ", "").replace("RE: ", "")
                generated_title = f"Re: {clean_context_title}"
                
            return generated_title, generated_body
            
        return "Daily Log", full_text

    except Exception as e:
        print(f"❌ AI Logic Error: {e}")
        return "System Error", "Error"
