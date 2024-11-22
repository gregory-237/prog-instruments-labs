import os

from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.environ.get("BOT_TOKEN")
DB_NAME = os.environ.get("DB_NAME")
DEFAULT_EXTRA_FIELDS = {'user_id': 0, 'role': 'worker', 'ext_params': ''}
