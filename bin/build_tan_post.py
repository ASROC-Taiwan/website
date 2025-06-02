from dotenv import load_dotenv
from tanbot import TANBot

load_dotenv()

bot = TANBot(rel_path_to_hugo="sources/content/tan/tan-bot/")
bot.load_gsheet()
has_updated = bot.hugo.generate_posts()
