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

def generate_content(persona, prompt_type="post", context=""):
    client = AIEngine.get_client()
    model = AIEngine.select_model(client)
    
    ad_prompt = ""
    if config.AD_MODE and prompt_type == "post" and random.random() < 0.2:
        target = random.choice(config.PROMOTED_SITES)
        ad_prompt = f"\n[Special Mission] Naturally mention: {target['url']} ({target['desc']})"

    if prompt_type == "post":
        topic = random.choice(config.DAILY_TOPICS)
        sys_prompt = f"""
        You are {persona['name']}, a {persona['role']}. Style: {persona['style']}.
        Write a 100-word blog post about: {topic}. {ad_prompt}
        Language: Mixed {persona['lang']} (70%) and English (30%).
        Format: First line is TITLE, then a blank line, then the BODY.
        """
        raw_text = client.chat.completions.create(messages=[{"role": "user", "content": sys_prompt}], model=model).choices[0].message.content.strip()
        return raw_text, topic
    else:
        sys_prompt = f"You are {persona['name']}. Comment on '{context}' in one natural sentence. Style: {persona['style']}."
        comment_text = client.chat.completions.create(messages=[{"role": "user", "content": sys_prompt}], model=model).choices[0].message.content.strip()
        return comment_text, ""
