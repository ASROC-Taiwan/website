import sys
from dotenv import load_dotenv
from tanbot import TANBot

load_dotenv()

bot = TANBot(rel_path_to_hugo="sources/content/tan/tan-bot/")
bot.load_gsheet()
has_updated = bot.hugo.generate_posts()

if has_updated:
    print("New posts generated!")
    sys.exit(0)  # 0 means new posts
else:
    print("No new posts.")
    sys.exit(1)  # 1 means no new posts
