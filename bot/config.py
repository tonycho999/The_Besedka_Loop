import os

# ==========================================
# 1. 광고 및 홍보 설정 (Native Ad System)
# ==========================================
AD_MODE = False  # True로 변경 시, 게시글에 자연스러운 PPL이 포함됩니다.

PROMOTED_SITES = [
    {
        "name": "Matzip Finder", # 서비스 이름
        "url": "https://your-site-A.com", 
        "desc": "finding cheap and delicious local restaurants", # AI가 이해할 설명 (영어 권장)
        "context": "when talking about lunch, dinner, or hungry moments" # 언제 언급할지 힌트
    },
    {
        "name": "DevTool Pro",
        "url": "https://your-site-B.com", 
        "desc": "boosting developer productivity with AI",
        "context": "when complaining about bugs or slow coding"
    }
]

# ==========================================
# 2. GitHub 설정
# ==========================================
REPO_NAME = "tonycho999/The_Besedka_Loop"
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")

# ==========================================
# 3. 페르소나 (10인)
# ==========================================
PERSONAS = [
    {"id": "jinwoo", "name": "Jin-woo", "role": "DevOps", "style": "cynical, loves soju, hates legacy", "lang": "Korean"},
    {"id": "kenji", "name": "Kenji", "role": "Frontend", "style": "polite, nostalgic, detail-obsessed", "lang": "Japanese"},
    {"id": "wei", "name": "Wei", "role": "AI Researcher", "style": "ambitious, tech-focused, dry humor", "lang": "Chinese"},
    {"id": "budi", "name": "Budi", "role": "Backend", "style": "relaxed, coffee addict, peace-maker", "lang": "Indonesian"},
    {"id": "carlos", "name": "Carlos", "role": "Mobile App", "style": "passionate, loud, chaotic", "lang": "Spanish"},
    {"id": "lena", "name": "Lena", "role": "Security", "style": "logical, direct, paranoid", "lang": "German"},
    {"id": "amelie", "name": "Amélie", "role": "UI/UX", "style": "artistic, sensitive, hates bad kerning", "lang": "French"},
    {"id": "hina", "name": "Hina", "role": "Illustrator", "style": "cute, emotional, uses lots of emojis", "lang": "Japanese"},
    {"id": "sarah", "name": "Sarah", "role": "Product Manager", "style": "trendy, hip, social butterfly", "lang": "Korean"},
    {"id": "marco", "name": "Marco", "role": "CTO", "style": "gourmet, perfectionist, slightly arrogant", "lang": "French"},
]

# ==========================================
# 4. 콘텐츠 비율 (Hyper-Realism)
# ==========================================
CONTENT_CATEGORIES = {
    "life": {"ratio": 0.3, "desc": "Netflix, snacks, gym, hobbies (No work talk, casual)"},
    "relation": {"ratio": 0.4, "desc": "Teasing, joking, debating, or venting about colleagues"},
    "work_rant": {"ratio": 0.1, "desc": "Legacy code, server crash, bugs, deadlines (Short & angry)"},
    "info": {"ratio": 0.2, "desc": "New gadgets, tech news, useful tools, keyboard flex"}
}

# ==========================================
# 5. 대화 주제 (Seed Topics)
# ==========================================
TOPICS = [
    "Tabs vs Spaces", "Vim vs VSCode", "Mac vs Windows", "Dark mode vs Light mode", 
    "expensive keyboard delivery", "drinking alone", "camping fail", "new cat tower", 
    "internet down", "blue screen", "forgot semicolon", "deployment fail",
    "Bitcoin crash", "Bitcoin to the moon", "Boss acting like Marco"
]

# ==========================================
# 6. 시스템 상수
# ==========================================
AFFINITY_MIN = 50
AFFINITY_MAX = 90
DEFAULT_AFFINITY = 70
HISTORY_LIMIT = 15
VACATION_CHANCE = 0.01
SICK_CHANCE = 0.02
