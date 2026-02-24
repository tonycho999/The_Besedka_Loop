import model_selector
import random

def generate_content(persona, mode="life", context_title="", context_body="", context_author="", relation_type="colleague"):
    try:
        # 1. 모델 동적 선택
        client = model_selector.get_client()
        model_id = model_selector.get_dynamic_model(client)
        print(f"🤖 Selected Model: {model_id}")

        prompt = ""
        
        # --- [모드 1] 티키타카 답글 (Reply) - 40% ---
        if mode == "reply":
            # 답글 길이 랜덤 (짧게 툭 던지거나, 길게 챙겨주거나)
            reply_length = random.randint(1, 4)
            
            # 관계별 말투 설정 (친분 과시)
            tone_map = {
                "romance": "Warm, caring, subtly flirty. (e.g., 'Did you eat?', 'Don't overwork')",
                "rival": "Teasing, bickering, technical debate. (e.g., 'That's not a bug, it's a feature')",
                "bestie": "Playful, slang, jokes, gaming talk. (e.g., 'LOL', 'Let's play tonight')",
                "colleague": "Friendly support, empathy. (e.g., 'I feel you', 'Great job')"
            }
            tone = tone_map.get(relation_type, "Friendly")

            prompt = f"""
            You are {persona['name']} ({persona['role']}) from {persona['country']}.
            You are writing a REPLY to your friend {context_author}.
            
            [CONTEXT - The Post you are replying to]
            Title: {context_title}
            Content: "{context_body}"
            
            [YOUR ROLE]
            - Relationship: {relation_type}
            - Tone: {tone}
            - TASK: Write a natural reply. Connect with them.
            - LENGTH: {reply_length} sentences.
            - RULE: Do NOT start with formal greetings like "Hi". Just talk.
            """
            print(f"   🗣️ Mode: Reply to {context_author} ({relation_type})")

        # --- [모드 2] 개발자 공감 (Dev Life) - 30% ---
        # 야근/고충보다는 '업계 공감' 위주
        elif mode == "dev_life":
            prompt = f"""
            You are {persona['name']}, a developer.
            Write a short post about 'Developer Lifestyle & Empathy'.
            
            [TOPICS]
            - Mechanical Keyboards (Switch types, Keycaps)
            - Desk Setup (Standing desk, Monitor arm)
            - Health (Back pain, Eyesight, Vitamins)
            - Tech Trends (New framework fatigue, AI tools)
            - Small Joys (Dark mode, Clean code, Noise-canceling headphones)
            
            [RULES]
            1. TONE: Geeky, passionate, or relatable.
            2. NO complaints about overtime. Focus on the LIFESTYLE.
            3. LENGTH: 3-5 sentences.
            4. TITLE: Creative & Abstract (NO timestamps like '02:00').
            """
            print("   ⌨️ Mode: Dev Life (Empathy)")

        # --- [모드 3] 사생활 (Private Life) - 30% ---
        elif mode == "life":
            prompt = f"""
            You are {persona['name']}, living in {persona['country']}.
            Write a blog post about your PRIVATE LIFE (No coding).
            
            [TOPICS]
            - Food (Late night snacks, Coffee, Local dish)
            - Hobbies (Gaming, Netflix, Gym, Cat/Dog)
            - Mood (Relaxed, Excited for weekend, Sentimental)
            
            [RULES]
            1. STRICTLY NO CODING. Show your human side.
            2. TONE: Casual, emotional, or funny.
            3. LENGTH: 3-4 sentences.
            4. TITLE: Creative & Abstract (NO timestamps like '02:00').
            """
            print("   🍺 Mode: Private Life")

        # 공통 포맷
        prompt += """
        [FORMAT]
        - First line: Title
        - Second line onwards: Content.
        - Do NOT use quotes in Title.
        - NEVER mention weather (Rain, Sun, Snow).
        """

        # 2. 결과 생성
        chat_completion = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model=model_id,
            temperature=0.75, # 창의성을 위해 약간 높임
        )

        full_text = chat_completion.choices[0].message.content.strip()
        lines = full_text.split('\n')
        
        if lines:
            generated_title = lines[0].strip().replace('"', '').replace("Title: ", "")
            generated_body = "\n".join(lines[1:]).strip()
            
            # 답글 모드일 때 제목 처리 (Re: Re: 로직은 main.py에서 처리하지만 안전장치로)
            if mode == "reply":
                clean_context = context_title.replace("Re: ", "").replace("RE: ", "")
                # AI가 제목을 맘대로 지으면 무시하고 Re: 붙이기 위해 제목은 비워둠 (main.py에서 결정)
                return "REPLY_TITLE_PLACEHOLDER", generated_body
            
            return generated_title, generated_body
            
        return "Daily Log", full_text

    except Exception as e:
        print(f"❌ AI Logic Error: {e}")
        return "Error", "System Error"
