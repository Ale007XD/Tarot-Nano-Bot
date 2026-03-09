import os
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

USE_OPENROUTER = os.getenv("USE_OPENROUTER", "true").lower() == "true"

DB_PATH = "tarot.db"
