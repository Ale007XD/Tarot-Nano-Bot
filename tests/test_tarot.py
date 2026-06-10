"""Tests for tarot handler — deterministic card math and draw callback."""

from __future__ import annotations

import os
from unittest.mock import AsyncMock

import aiosqlite
import pytest

import bot.database
from bot.handlers.tarot import ProviderResponse, calculate_deterministic_card, draw

TEST_TAROT_DB = "test_tarot_runtime.db"

SALT = "NANO_VM_CRYPTO_DETERMINISTIC_SECURE_SALT_2026"


@pytest.fixture(autouse=True)
async def setup_tarot_db() -> object:
    old = bot.database.DB_PATH
    bot.database.DB_PATH = TEST_TAROT_DB

    async with aiosqlite.connect(TEST_TAROT_DB) as db:
        await db.execute(
            "CREATE TABLE IF NOT EXISTS readings ("
            "id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, "
            "spread TEXT, cards TEXT, interpretation TEXT, "
            "paid INTEGER DEFAULT 0, execution_id TEXT, trace_hash TEXT, "
            "created_at INTEGER DEFAULT 0)"
        )
        await db.commit()

    yield

    if os.path.exists(TEST_TAROT_DB):
        os.remove(TEST_TAROT_DB)
    bot.database.DB_PATH = old


def test_deterministic_card_same_input() -> None:
    c1 = calculate_deterministic_card(123456789, "2026-06-09", SALT)
    c2 = calculate_deterministic_card(123456789, "2026-06-09", SALT)
    assert c1 == c2
    assert 0 <= c1 < 78


def test_deterministic_card_different_users() -> None:
    c1 = calculate_deterministic_card(1, "2026-06-09", SALT)
    c2 = calculate_deterministic_card(2, "2026-06-09", SALT)
    assert c1 != c2


def test_deterministic_card_different_dates() -> None:
    c1 = calculate_deterministic_card(42, "2026-06-09", SALT)
    c2 = calculate_deterministic_card(42, "2026-06-10", SALT)
    assert c1 != c2


def test_provider_response_invalid_card_id() -> None:
    with pytest.raises(ValueError):
        ProviderResponse(
            card_id=99,
            card_name="Invalid",
            interpretation="Error",
            execution_date="2026-06-09",
        )


async def test_draw_callback_saves_reading() -> None:
    callback = AsyncMock()
    callback.from_user.id = 999888
    callback.message = AsyncMock()

    await draw(callback)

    async with aiosqlite.connect(TEST_TAROT_DB) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM readings WHERE user_id = 999888"
        ) as cursor:
            row = await cursor.fetchone()

    assert row is not None
    assert row["spread"] == "card_of_the_day"
    assert row["paid"] == 0
    assert len(str(row["cards"])) > 0


async def test_draw_callback_sends_message() -> None:
    callback = AsyncMock()
    callback.from_user.id = 111222
    callback.message = AsyncMock()

    await draw(callback)

    callback.message.answer.assert_called_once()
    text = callback.message.answer.call_args[0][0]
    assert "🔮" in text
    assert "карту дня" in text
