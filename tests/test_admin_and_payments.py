"""Tests for admin handlers and payment logic."""

from __future__ import annotations

import os
from unittest.mock import AsyncMock, MagicMock

import aiosqlite
import pytest

import bot.database
import bot.handlers.admin
from bot.handlers.admin import admin_stats, give_spreads

TEST_DB_PATH = "test_admin_runtime.db"


@pytest.fixture(autouse=True)
async def setup_test_environment() -> object:
    old_db = bot.database.DB_PATH
    old_admin_db = bot.handlers.admin.DB_PATH

    bot.database.DB_PATH = TEST_DB_PATH
    bot.handlers.admin.DB_PATH = TEST_DB_PATH

    async with aiosqlite.connect(TEST_DB_PATH) as db:
        await db.execute(
            "CREATE TABLE IF NOT EXISTS users "
            "(user_id INTEGER PRIMARY KEY, free_spreads INTEGER DEFAULT 0)"
        )
        await db.execute(
            "CREATE TABLE IF NOT EXISTS readings "
            "(reading_id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, "
            "spread TEXT, cards TEXT, interpretation TEXT, paid INTEGER DEFAULT 0)"
        )
        await db.commit()

    yield

    if os.path.exists(TEST_DB_PATH):
        os.remove(TEST_DB_PATH)

    bot.database.DB_PATH = old_db
    bot.handlers.admin.DB_PATH = old_admin_db


async def test_admin_stats_logic() -> None:
    message = AsyncMock()

    async with aiosqlite.connect(TEST_DB_PATH) as db:
        await db.execute("INSERT INTO users (user_id, free_spreads) VALUES (777, 0)")
        await db.execute(
            "INSERT INTO readings (user_id, spread, cards, interpretation, paid) "
            "VALUES (777, 'one_card', 'The Magician', 'Execution Valid', 1)"
        )
        await db.commit()

    await admin_stats(message)

    message.answer_photo.assert_called_once()
    caption = message.answer_photo.call_args[1]["caption"]
    assert "Юзеров всего: `1`" in caption
    assert "Оплат всего: `1`" in caption


async def test_give_spreads_command() -> None:
    message = AsyncMock()
    command = MagicMock()
    command.args = "777 5"

    async with aiosqlite.connect(TEST_DB_PATH) as db:
        await db.execute("INSERT INTO users (user_id, free_spreads) VALUES (777, 2)")
        await db.commit()

    await give_spreads(message, command)

    async with aiosqlite.connect(TEST_DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT free_spreads FROM users WHERE user_id = 777") as cursor:
            row = await cursor.fetchone()

    assert row is not None
    assert row["free_spreads"] == 7
    message.answer.assert_called_once_with("✅ Юзеру `777` выдано 5 попыток.")
