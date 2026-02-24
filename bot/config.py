import os

# ==========================================
# 1. API 키 설정
# ==========================================
_raw_keys = [os.environ.get(f"GROQ_API_KEY_{i}") for i in range(1, 5)]
VALID_KEYS = [k for k in _raw_keys if k]

# ==========================================
# 2. 광고 설정
# ==========================================
AD_MODE = False
PROMOTED_SITES = [
    {"name": "Matzip Finder", "url": "https://site-a.com", "desc": "cheap local food", "context": "hungry"},
    {"name": "DevTool Pro", "url": "https://site-b.com", "desc": "AI coding tool", "context": "debugging"}
]

# ==========================================
# 3. GitHub 설정
# ==========================================
REPO_NAME = "tonycho999/The_Besedka_Loop"
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")

# ==========================================
# 4. 페르소나 (10인)
# ==========================================
PERSONAS = [
    {"id": "jinwoo", "name": "Jin-woo", "country": "Korea", "role": "DevOps", "style": "cynical, loves soju, hates legacy", "lang": "Korean"},
    {"id": "kenji", "name": "Kenji", "country": "Japan", "role": "Frontend", "style": "polite, nostalgic, detail-obsessed", "lang": "Japanese"},
    {"id": "wei", "name": "Wei", "country": "China", "role": "AI Researcher", "style": "ambitious, tech-focused, dry humor", "lang": "Chinese"},
    {"id": "budi", "name": "Budi", "country": "Indonesia", "role": "Backend", "style": "relaxed, coffee addict, peace-maker", "lang": "Indonesian"},
    {"id": "carlos", "name": "Carlos", "country": "Spain", "role": "Mobile App", "style": "passionate, loud, chaotic", "lang": "Spanish"},
    {"id": "lena", "name": "Lena", "country": "Germany", "role": "Security", "style": "logical, direct, paranoid", "lang": "German"},
    {"id": "amelie", "name": "Amélie", "country": "France", "role": "UI/UX", "style": "artistic, sensitive, hates bad kerning", "lang": "French"},
    {"id": "hina", "name": "Hina", "country": "Japan", "role": "Illustrator", "style": "cute, emotional, uses lots of emojis", "lang": "Japanese"},
    {"id": "sarah", "name": "Sarah", "country": "Korea", "role": "Product Manager", "style": "trendy, hip, social butterfly", "lang": "Korean"},
    {"id": "marco", "name": "Marco", "country": "France", "role": "CTO", "style": "gourmet, perfectionist, slightly arrogant", "lang": "French"},
]

# ==========================================
# 5. 콘텐츠 비율 (잡담 비중 증가)
# ==========================================
CONTENT_CATEGORIES = {
    "chit_chat": {"ratio": 0.4, "desc": "Pure nonsense, lunch menu, coffee, tired, weather, gaming"},
    "life": {"ratio": 0.2, "desc": "Netflix, snacks, gym, hobbies"},
    "relation": {"ratio": 0.3, "desc": "Teasing colleagues, office jokes"},
    "tech_rant": {"ratio": 0.1, "desc": "Code bugs, server crash, stupid legacy code"}
}

# ==========================================
# 6. 대화 주제 (리얼함 추가)
# ==========================================
TOPICS = [
    # Tech
    "Tabs vs Spaces", "Vim vs VSCode", "Dark mode supremacy", "Mechanical Keyboard sound", 
    "Forgot semicolon", "Production DB deleted", "Git merge conflict", "StackOverflow copy-paste",
    
    # Life & Rant
    "Coffee spilled on keyboard", "My back hurts", "Need more caffeine", "Zoom meeting is boring",
    "Lunch was terrible", "Anyone wanna play LoL?", "Steam Sale is dangerous", "I want to go home",
    "Why is it Monday again?", "Code works but I don't know why"
]

# ==========================================
# 7. 시스템 상수
# ==========================================
AFFINITY_MIN = 50
AFFINITY_MAX = 90
DEFAULT_AFFINITY = 70
HISTORY_LIMIT = 15
VACATION_CHANCE = 0.01
SICK_CHANCE = 0.02
