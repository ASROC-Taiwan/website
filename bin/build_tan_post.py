import sys
from dotenv import load_dotenv
from tanbot import TANBot
from pathlib import Path

load_dotenv()

bot = TANBot(rel_path_to_hugo="sources/content/tan/tan-bot/")
bot.load_gsheet()
has_updated = bot.hugo.generate_posts()

if has_updated:
    print("New posts generated!")
    bot.broadcast(line=True, instagram=False, facebook=False)
    Path(".new_posts").touch()
    sys.exit(0)  # 0 means new posts
else:
    print("No new posts.")
    sys.exit(0)  # still 0 to let github action passed by a green light
