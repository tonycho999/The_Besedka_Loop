import random
import time
import datetime
from github import Github, Auth
import config
from ai_engine import generate_content

def update_relay_comments(repo):
    try:
        contents = repo.get_contents("src/pages/blog")
        md_files = sorted([c for c in contents if c.name.endswith('.md')], key=lambda x: x.name)
        if not md_files: return
        
        last_file = md_files[-1]
        content = last_file.decoded_content.decode("utf-8")
        if "comment-box" in content: return

        author = next((line.split('"')[1] for line in content.split('\n') if "author:" in line), "Someone")
        title = next((line.replace('title:', '').replace('"', '').strip() for line in content.split('\n') if line.startswith("title:")), "Post")

        comment_section = '\n\n<div class="comment-box"><h3>💬 Alumni Comments</h3>'
        for p in random.sample([p for p in config.PERSONAS if p['name'] != author], 2):
            msg, _ = generate_content(p, "comment", title)
            # [수정됨] f-string 충돌 방지를 위해 삼중 따옴표(''' ''') 사용
            comment_section += f'''\n<div class="comment"><img src="https://api.dicebear.com/7.x/avataaars/svg?seed={p["id"]}" class="avatar"><div class="bubble"><strong>{p["name"]}</strong><p>{msg.replace('"', "")}</p></div></div>'''
        
        repo.update_file(last_file.path, f"Relay comments", content + comment_section + '</div>', last_file.sha, branch="main")
    except Exception as e: print(f"Relay error: {e}")

def main():
    print("--- ⛺ The Besedka Loop Bot Started ---")
    time.sleep(random.randint(0, 18000) / 10.0)

    auth = Auth.Token(config.GITHUB_TOKEN)
    repo = Github(auth=auth).get_repo(config.REPO_NAME)

    update_relay_comments(repo)

    persona = random.choice(config.PERSONAS)
    full_text, topic = generate_content(persona, "post")
    
    lines = full_text.split('\n')
    title = lines[0].strip().replace('"', "'")
    body = "\n".join(lines[1:]).strip()

    image_url = f"https://image.pollinations.ai/prompt/{topic.replace(' ', '%20')},{persona['country']}?width=800&height=400&nologo=true"
    date_str = datetime.datetime.now().strftime("%Y-%m-%d")
    
    md_output = f'---\nlayout: ../../layouts/BlogPostLayout.astro\ntitle: "{title}"\nauthor: "{persona["name"]}"\ndate: "{date_str}"\nimage: "{image_url}"\ncategory: "Daily Log"\nlocation: "{persona["country"]}"\n---\n\n{body}'

    file_path = f"src/pages/blog/{date_str}-{persona['id']}-{random.randint(1000,9999)}.md"
    repo.create_file(file_path, f"Signal from {persona['name']}", md_output, branch="main")
    print(f"Post Success: {file_path}")

if __name__ == "__main__":
    main()
