import random
from groq import Groq
import config

class AIEngine:
    @staticmethod
    def get_client():
        return Groq(api_key=random.choice(config.VALID_KEYS))

    @staticmethod
    def select_model(client):
        try:
            models = client.models.list()
            text_models = [m.id for m in models.data if 'whisper' not in m.id and 'vision' not in m.id]
            for m in text_models:
                if '70b' in m: return m
            return text_models[0] if text_models else "llama-3.3-70b-versatile"
        except:
            return "llama-3.3-70b-versatile"

def generate_content(persona, type="post", context=""):
    try:
        if type == "post":
            # [수정] 날씨 금지(Forbidden) 및 개발 관련 주제만 선정
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
            
            response = model.generate_content(prompt)
            full_text = response.text.strip()
            
            # 제목 분리
            lines = full_text.split('\n')
            topic = lines[0] if lines else "Dev Log"
            
            return full_text, topic

        elif type == "comment":
            prompt = f"""
            You are {persona['name']}, a developer.
            Write a 1-sentence comment on the post: "{context}".
            Casual tone, no weather talk.
            """
            response = model.generate_content(prompt)
            return response.text.strip(), ""

    except Exception as e:
        print(f"AI Error: {e}")
        return "System Error: AI needs sleep.", "Error"
