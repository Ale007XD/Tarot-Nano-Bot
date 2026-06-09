"""Изолированное тестирование административного контура и логики начислений."""

import os
from unittest.mock import AsyncMock, MagicMock

import aiosqlite
import pytest
import pytest_asyncio

import bot.database
import bot.handlers.admin
from bot.handlers.admin import admin_stats, give_spreads

TEST_DB_PATH = "test_admin_runtime.db"


@pytest_asyncio.fixture(autouse=True)
async def setup_test_environment():
    """Фикстура изоляции: принудительно переопределяет пути во всех пространствах имен."""
    # Сохраняем исходные состояния
    old_db_path = bot.database.DB_PATH
    old_admin_path = bot.handlers.admin.DB_PATH

    # Перелинковка путей для предотвращения деградации из-за локального импорта
    bot.database.DB_PATH = TEST_DB_PATH
    bot.handlers.admin.DB_PATH = TEST_DB_PATH

    # Инициализация детерминированной структуры таблиц MVP
    async with aiosqlite.connect(TEST_DB_PATH) as db:
        await db.execute(
            "CREATE TABLE IF NOT EXISTS users ("
            "user_id INTEGER PRIMARY KEY, "
            "free_spreads INTEGER DEFAULT 0)"
        )
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

    # Гарантированная зачистка дисковых артефактов
    if os.path.exists(TEST_DB_PATH):
        os.remove(TEST_DB_PATH)

    # Восстановление контекста рантайма
    bot.database.DB_PATH = old_db_path
    bot.handlers.admin.DB_PATH = old_admin_path


@pytest.mark.asyncio
async def test_admin_stats_logic():
    """Тест парсинга метрик и формирования структуры отчета обсерватории."""
    message = AsyncMock()

    # Наполнение тестового фикстурного пространства
    async with aiosqlite.connect(TEST_DB_PATH) as db:
        await db.execute("INSERT INTO users (user_id, free_spreads) VALUES (777, 0)")
        await db.execute(
            "INSERT INTO readings (user_id, spread, cards, interpretation, paid) "
            "VALUES (777, 'one_card', 'The Magician', 'Execution Valid', 1)"
        )
        await db.commit()

    await admin_stats(message)

    # Верификация вызова интерфейса отправки медиа-отчета QuickChart
    message.answer_photo.assert_called_once()
    caption = message.answer_photo.call_args[1]["caption"]
    assert "Юзеров всего: `1`" in caption
    assert "Оплат всего: `1`" in caption


@pytest.mark.asyncio
async def test_give_spreads_command():
    """Тест детерминированного инкремента баланса переходов сессии пользователя."""
    message = AsyncMock()
    command = MagicMock()
    command.args = "777 5"  # Симуляция ввода: инкрементировать на 5 для ID 777

    async with aiosqlite.connect(TEST_DB_PATH) as db:
        await db.execute("INSERT INTO users (user_id, free_spreads) VALUES (777, 2)")
        await db.commit()

    await give_spreads(message, command)

    # Валидация мутации состояния в СУБД
    async with aiosqlite.connect(TEST_DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT free_spreads FROM users WHERE user_id = 777") as cursor:
            row = await cursor.fetchone()

    assert row is not None
    assert row["free_spreads"] == 7  # 2 исходных + 5 начисленных
    message.answer.assert_called_once_with("✅ Юзеру `777` выдано 5 попыток.")
