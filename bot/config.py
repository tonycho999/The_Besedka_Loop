import os

# ==========================================
# 1. API 키 설정 (model_selector.py용)
# ==========================================
_raw_keys = [os.environ.get(f"GROQ_API_KEY_{i}") for i in range(1, 5)]
VALID_KEYS = [k for k in _raw_keys if k]

# ==========================================
# 2. 광고 및 홍보 설정 (Native Ad System)
# ==========================================
AD_MODE = False

PROMOTED_SITES = [
    {
        "name": "Matzip Finder", 
        "url": "https://your-site-A.com", 
        "desc": "finding cheap and delicious local restaurants", 
        "context": "when talking about lunch, dinner, or hungry moments"
    },
    {
        "name": "DevTool Pro",
        "url": "https://your-site-B.com", 
        "desc": "boosting developer productivity with AI",
        "context": "when complaining about bugs or slow coding"
    }
]

# ==========================================
# 3. GitHub 설정
# ==========================================
REPO_NAME = "tonycho999/The_Besedka_Loop"
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")

# ==========================================
# 4. 페르소나 (10인) - [수정] country 항목 추가 완료
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
# 5. 콘텐츠 비율
# ==========================================
CONTENT_CATEGORIES = {
    "life": {"ratio": 0.3, "desc": "Netflix, snacks, gym, hobbies (No work talk, casual)"},
    "relation": {"ratio": 0.4, "desc": "Teasing, joking, debating, or venting about colleagues"},
    "work_rant": {"ratio": 0.1, "desc": "Legacy code, server crash, bugs, deadlines (Short & angry)"},
    "info": {"ratio": 0.2, "desc": "New gadgets, tech news, useful tools, keyboard flex"}
}

# ==========================================
# 6. 대화 주제 (Seed Topics)
# ==========================================
TOPICS = [
    "Tabs vs Spaces", "Vim vs VSCode", "Mac vs Windows", "Dark mode vs Light mode", 
    "expensive keyboard delivery", "drinking alone", "camping fail", "new cat tower", 
    "internet down", "blue screen", "forgot semicolon", "deployment fail",
    "Bitcoin crash", "Bitcoin to the moon", "Boss acting like Marco", "Anonymous post found"
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
