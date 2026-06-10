# bot/config.py
from __future__ import annotations

import os
import sys

from dotenv import load_dotenv

load_dotenv()

# Telegram
TELEGRAM_TOKEN: str = os.getenv("TELEGRAM_TOKEN", "")
ADMIN_ID: int = int(os.getenv("ADMIN_ID", "0"))

# LLM — LiteLLM model string (OpenRouter or any LiteLLM-compatible provider)
# Example: "openrouter/mistralai/mistral-7b-instruct"
LLM_MODEL: str = os.getenv("LLM_MODEL", "openrouter/mistralai/mistral-7b-instruct")

# Tarot determinism salt — change to rotate card assignments across all users
TAROT_SALT: str = os.getenv("TAROT_SALT", "TAROT_GOVERNANCE_SALT_2026")

# DB
DB_PATH: str = os.getenv("DB_PATH", "tarot.db")

# Validation — skip when running under pytest
if not TELEGRAM_TOKEN and "pytest" not in sys.modules:
    raise ValueError("TELEGRAM_TOKEN not found in .env")

# Legacy LLM config (used by bot/services/llm_service.py)
OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
OPENROUTER_API_KEY: str = os.getenv("OPENROUTER_API_KEY", "")
USE_OPENROUTER: bool = os.getenv("USE_OPENROUTER", "true").lower() == "true"
