import asyncio
import os
import sys

import httpx

# Добавляем корень проекта в путь поиска модулей
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from bot.config import (
    DB_PATH,
    OPENAI_API_KEY,
    OPENROUTER_API_KEY,
    TELEGRAM_TOKEN,
    USE_OPENROUTER,
)
from bot.database import init_db
from bot.services.llm_service import generate_reading
from bot.services.tarot_engine import build_deck


def check_env():
    print("--- Проверка конфигурации ---")
    assert TELEGRAM_TOKEN, "TELEGRAM_TOKEN отсутствует"
    if USE_OPENROUTER:
        assert OPENROUTER_API_KEY, "OPENROUTER_API_KEY отсутствует"
    else:
        assert OPENAI_API_KEY, "OPENAI_API_KEY отсутствует"
    print("ENV: OK")


async def check_telegram():
    print("--- Проверка связи с Telegram ---")
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getMe"
    async with httpx.AsyncClient(timeout=10.0) as client:
        r = await client.get(url)
        data = r.json()
        assert data.get("ok"), f"Ошибка API Telegram: {data.get('description')}"
        print(f"Telegram: OK (@{data['result']['username']})")


async def check_database():
    print("--- Проверка базы данных ---")
    await init_db()
    assert os.path.exists(DB_PATH), f"Файл БД {DB_PATH} не найден"
    print("Database: OK")


def check_tarot():
    print("--- Проверка колоды ---")
    deck = build_deck()
    assert len(deck) == 78, f"Ошибка: в колоде {len(deck)} карт, ожидалось 78"
    print("Tarot deck: OK")


async def check_llm():
    print("--- Проверка LLM ---")
    cards = "Past: The Fool, Present: The Tower, Future: The Star"
    result = await generate_reading(cards)
    assert isinstance(result, str) and len(result) > 10, "LLM вернула пустой или некорректный ответ"
    print("LLM: OK")


async def main():
    print("\n🔮 TAROT BOT HEALTHCHECK STARTING\n")
    check_env()
    await check_telegram()
    await check_database()
    check_tarot()
    await check_llm()
    print("\n✅ ВСЕ СИСТЕМЫ В НОРМЕ\n")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        print(f"\n❌ HEALTHCHECK FAILED: {e}")
        sys.exit(1)
