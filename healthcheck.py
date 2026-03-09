import asyncio
import os
import sys

sys.path.append(os.path.dirname(__file__))

import httpx

from bot.config import TELEGRAM_TOKEN, OPENAI_API_KEY, OPENROUTER_API_KEY, USE_OPENROUTER
from bot.database import init_db
from bot.services.tarot_engine import build_deck
from bot.services.llm_service import generate_reading


# ------------------------
# ENV CHECK
# ------------------------

def check_env():

    print("Checking ENV...")

    assert TELEGRAM_TOKEN, "TELEGRAM_TOKEN missing"

    if USE_OPENROUTER:

        assert OPENROUTER_API_KEY, "OPENROUTER_API_KEY missing"

    else:

        assert OPENAI_API_KEY, "OPENAI_API_KEY missing"

    print("ENV OK")


# ------------------------
# TELEGRAM API
# ------------------------

async def check_telegram():

    print("Checking Telegram API...")

    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getMe"

    async with httpx.AsyncClient() as client:

        r = await client.get(url)

        data = r.json()

        assert data["ok"], "Telegram token invalid"

        bot_name = data["result"]["username"]

        print(f"Telegram OK (@{bot_name})")


# ------------------------
# DATABASE
# ------------------------

async def check_database():

    print("Checking database...")

    await init_db()

    print("Database OK")


# ------------------------
# TAROT ENGINE
# ------------------------

def check_tarot():

    print("Checking tarot deck...")

    deck = build_deck()

    assert len(deck) == 78, "Tarot deck corrupted"

    print("Tarot deck OK")


# ------------------------
# LLM API
# ------------------------

async def check_llm():

    print("Checking LLM provider...")

    cards = """
Past: The Fool
Present: The Tower
Future: The Star
"""

    result = await generate_reading(cards)

    assert isinstance(result, str)

    assert len(result) > 30

    print("LLM OK")


# ------------------------
# MAIN
# ------------------------

async def main():

    print("\n🔮 TAROT BOT HEALTHCHECK\n")

    check_env()

    await check_telegram()

    await check_database()

    check_tarot()

    # # await check_llm()

    print("\n✅ ALL SYSTEMS OPERATIONAL\n")


if __name__ == "__main__":

    try:

        asyncio.run(main())

    except Exception as e:

        print("\n❌ HEALTHCHECK FAILED\n")

        print(e)

        sys.exit(1)
