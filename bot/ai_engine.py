import model_selector
import random

def generate_content(persona, mode="life", context_title="", context_body="", context_author="", current_affinity=50, affinity_label="Colleague"):
    try:
        client = model_selector.get_client()
        model_id = model_selector.get_dynamic_model(client)
        print(f"🤖 Selected Model: {model_id}")

        prompt = ""
        sentiment_delta = 0 # 기본 변화량 0

        # --- [모드 1] 답글 (호감도 시스템 적용) ---
        if mode == "reply":
            # 점수에 따른 연기 지침
            behavior_guide = ""
            if current_affinity >= 80:
                behavior_guide = "You LOVE this person. Be very affectionate, supportive, or playful."
            elif current_affinity >= 60:
                behavior_guide = "You are close friends. Casual, joking, warm."
            elif current_affinity >= 40:
                behavior_guide = "Professional colleague. Polite but not too deep."
            elif current_affinity >= 20:
                behavior_guide = "Awkward relationship. Short answers, slightly cold or sarcastic."
            else:
                behavior_guide = "You DISLIKE this person. Be cold, critical, or ignore their point."

            prompt = f"""
            You are {persona['name']} from {persona['country']}.
            You are replying to {context_author}.
            
            [RELATIONSHIP STATUS]
            - Affinity Score: {current_affinity}/100 ({affinity_label})
            - BEHAVIOR GUIDE: {behavior_guide}
            
            [CONTEXT]
            Title: {context_title}
            Content: "{context_body}"
            
            [TASK]
            1. Write a reply based on the relationship score.
            2. Decide how this interaction changes the affinity score (Range: -5 to +5).
               - Good conversation/Support: +1 to +5
               - Argument/Insult/Coldness: -1 to -5
               - Neutral: 0
            
            [FORMAT]
            - First line: Title
            - Second line: [DELTA: number] (e.g., [DELTA: +3] or [DELTA: -2])
            - Third line onwards: Content
            """
            print(f"   🗣️ Mode: Reply (Score: {current_affinity} - {affinity_label})")

        # --- [모드 2, 3] 일반 글 (변화 없음) ---
        else:
            prompt = f"""
            You are {persona['name']}.
            Write a short blog post about {mode} (Life/Dev).
            Tone: Casual. Length: 3-5 sentences.
            [FORMAT]
            - First line: Title
            - Second line: [DELTA: 0]
            - Third line onwards: Content
            """

        # API 호출
        chat_completion = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model=model_id,
            temperature=0.8,
        )

        full_text = chat_completion.choices[0].message.content.strip()
        lines = full_text.split('\n')
        
        title = "Daily Log"
        body = ""
        
        # 파싱 로직 ([DELTA: +3] 추출)
        if lines:
            title = lines[0].strip().replace('"', '').replace("Title: ", "")
            
            # 델타 값 찾기
            for line in lines:
                if "[DELTA:" in line:
                    try:
                        delta_str = line.split("[DELTA:")[1].split("]")[0].strip()
                        sentiment_delta = int(delta_str)
                    except:
                        sentiment_delta = 0 if mode != "reply" else random.randint(-1, 2)
                    break
            
            # 본문 추출 (DELTA 라인과 빈 줄 제거)
            body_lines = [l for l in lines[1:] if "[DELTA:" not in l and l.strip() != ""]
            body = "\n".join(body_lines).strip()
            
            if mode == "reply":
                return "REPLY_PLACEHOLDER", body, sentiment_delta
            
            return title, body, 0

    except Exception as e:
        print(f"❌ AI Logic Error: {e}")
        return "Error", "System Error", 0
