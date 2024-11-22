import os

from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.environ.get("BOT_TOKEN")
DB_NAME = os.environ.get("DB_NAME")
