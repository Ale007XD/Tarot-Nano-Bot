"""Изолированное тестирование криптографического детерминизма Tarot/Reflection Engine."""

import os
from unittest.mock import AsyncMock

import aiosqlite
import pytest
import pytest_asyncio

import bot.database
from bot.handlers.tarot import ProviderResponse, calculate_deterministic_card, draw

TEST_TAROT_DB = "test_tarot_runtime.db"


@pytest_asyncio.fixture(autouse=True)
async def setup_tarot_test_environment():
    """Фикстура изоляции: подменяет путь к БД в контуре database и создает схему."""
    old_db_path = bot.database.DB_PATH
    bot.database.DB_PATH = TEST_TAROT_DB

    # Инициализация чистой WAL-схемы для записи истории переходов
    async with aiosqlite.connect(TEST_TAROT_DB) as db:
        await db.execute(
            "CREATE TABLE IF NOT EXISTS readings ("
            "reading_id INTEGER PRIMARY KEY AUTOINCREMENT, "
            "user_id INTEGER, "
            "spread TEXT, "
            "cards TEXT, "
            "interpretation TEXT, "
            "paid INTEGER DEFAULT 0)"
        )
        await db.commit()

    yield

    # Гарантированная зачистка дисковых артефактов СУБД
    if os.path.exists(TEST_TAROT_DB):
        os.remove(TEST_TAROT_DB)

    bot.database.DB_PATH = old_db_path


def test_deterministic_card_math():
    """Проверка математического инварианта: одинаковый ввод дает идентичный ID карты."""
    user_id = 123456789
    current_date = "2026-06-09"
    salt = "NANO_VM_CRYPTO_DETERMINISTIC_SECURE_SALT_2026"

    # Первый прогон вычислений
    card_id_1 = calculate_deterministic_card(user_id, current_date, salt)
    # Второй прогон вычислений
    card_id_2 = calculate_deterministic_card(user_id, current_date, salt)

    # Верификация детерминизма
    assert card_id_1 == card_id_2
    assert 0 <= card_id_1 < 78


def test_provider_response_validation():
    """Проверка strict-валидации схемы типов Pydantic v2."""
    with pytest.raises(ValueError):
        # Передаем card_id вне допустимого диапазона [0, 77]
        ProviderResponse(
            card_id=99,
            card_name="Invalid Card",
            interpretation="Error State",
            execution_date="2026-06-09",
        )


@pytest.mark.asyncio
async def test_draw_callback_handler_execution():
    """Тест выполнения хендлера draw, генерации контракта и персистентности в WAL."""
    callback_query = AsyncMock()
    callback_query.from_user.id = 999888
    callback_query.message = AsyncMock()

    # Симуляция триггера инварианта «draw»
    await draw(callback_query)

    # 1. Проверка записи снапшота в изолированную базу данных
    async with aiosqlite.connect(TEST_TAROT_DB) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM readings WHERE user_id = 999888") as cursor:
            row = await cursor.fetchone()

    assert row is not None
    assert row["spread"] == "card_of_the_day"
    assert row["paid"] == 0
    assert len(row["cards"]) > 0

    # 2. Проверка отправки UI-слоя пользователю
    callback_query.message.answer.assert_called_once()
    called_text = callback_query.message.answer.call_args[0][0]
    assert "🔮 **Вы вытянули карту дня**:" in called_text
