import sys
from dotenv import load_dotenv
from tanbot import TANBot
from pathlib import Path

load_dotenv()

bot = TANBot(rel_path_to_image="images")
bot.load_gsheet()
has_updated = bot.instagram.generate_posts(publish=True)

if has_updated:
    print("New image posts generated!")
    Path(".new_img_posts").touch()
    sys.exit(0)  # 0 means new posts
else:
    print("No new image posts.")
    sys.exit(0)  # still 0 to let github action passed by a green light
