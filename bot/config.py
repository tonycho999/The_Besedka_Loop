import os

# 광고 및 홍보 설정
AD_MODE = False  # 광고 활성화 여부
PROMOTED_SITES = [
    {
        "url": "https://your-site-A.com", 
        "desc": "가성비 최고의 맛집 검색 서비스"
    },
    {
        "url": "https://your-site-B.com", 
        "desc": "개발자 생산성을 높여주는 유용한 도구"
    }
]

# GitHub 설정
REPO_NAME = "tonycho999/The_Besedka_Loop"
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")

# Groq API 키 로테이션
API_KEYS = [os.environ.get(f"GROQ_API_KEY_{i}") for i in range(1, 5)]
VALID_KEYS = [k for k in API_KEYS if k]

# 페르소나 데이터
PERSONAS = [
    {"id": "jinwoo", "name": "Jin-woo", "country": "Korea", "role": "DevOps", "style": "cynical but warm, loves soju", "lang": "Korean"},
    {"id": "kenji", "name": "Kenji", "country": "Japan", "role": "Frontend", "style": "polite, nostalgic", "lang": "Japanese"},
    {"id": "wei", "name": "Wei", "country": "China", "role": "AI Dev", "style": "ambitious, tech-focused", "lang": "Chinese"},
    {"id": "budi", "name": "Budi", "country": "Indonesia", "role": "Backend", "style": "relaxed, loves coffee", "lang": "Indonesian"},
    {"id": "carlos", "name": "Carlos", "country": "Spain", "role": "Mobile App", "style": "passionate, loud", "lang": "Spanish"},
    {"id": "lena", "name": "Lena", "country": "Germany", "role": "Web Dev", "style": "logical, direct", "lang": "German"},
    {"id": "amelie", "name": "Amélie", "country": "France", "role": "UI/UX", "style": "artistic, poetic", "lang": "French"},
    {"id": "hina", "name": "Hina", "country": "Japan", "role": "Illustrator", "style": "cute, emotional", "lang": "Japanese"},
    {"id": "sarah", "name": "Sarah", "country": "Korea", "role": "Graphic Des", "style": "trendy, hip", "lang": "Korean"},
    {"id": "marco", "name": "Marco", "country": "France", "role": "Publisher", "style": "gourmet, perfectionist", "lang": "French"},
]

DAILY_TOPICS = ["debugging nightmare", "unexpected rain", "new framework", "team missing", "local food", "laptop died", "late night inspiration"]
