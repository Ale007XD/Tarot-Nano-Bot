"""Tests for tarot handler — deterministic card math and draw callback."""

from __future__ import annotations

import os
from unittest.mock import AsyncMock, MagicMock, patch

import aiosqlite
import pytest

import bot.database
from bot.tools.tarot_tools import FULL_DECK, draw_deterministic_card

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


# ---------------------------------------------------------------------------
# draw_deterministic_card unit tests (replaces ProviderResponse / calculate_*)
# ---------------------------------------------------------------------------

def test_deterministic_card_same_input() -> None:
    r1 = draw_deterministic_card(123456789, "2026-06-09", SALT)
    r2 = draw_deterministic_card(123456789, "2026-06-09", SALT)
    assert r1["card_index"] == r2["card_index"]
    assert 0 <= int(r1["card_index"]) < 78


def test_deterministic_card_different_users() -> None:
    r1 = draw_deterministic_card(1, "2026-06-09", SALT)
    r2 = draw_deterministic_card(2, "2026-06-09", SALT)
    assert r1["card_index"] != r2["card_index"]


def test_deterministic_card_different_dates() -> None:
    r1 = draw_deterministic_card(42, "2026-06-09", SALT)
    r2 = draw_deterministic_card(42, "2026-06-10", SALT)
    assert r1["card_index"] != r2["card_index"]


def test_deterministic_card_name_in_deck() -> None:
    result = draw_deterministic_card(42, "2026-06-09", SALT)
    assert result["card_name"] in FULL_DECK


def test_deterministic_card_invalid_id_out_of_range() -> None:
    # card_index must always be 0..77 — SHA-256 % 78 guarantee
    for uid in range(100):
        r = draw_deterministic_card(uid, "2026-06-09", SALT)
        assert 0 <= int(r["card_index"]) < 78


# ---------------------------------------------------------------------------
# draw callback tests (via mock vm_runner)
# ---------------------------------------------------------------------------

def _make_successful_trace(card_name: str = "The Star") -> MagicMock:
    step = MagicMock()
    step.output = {"card_name": card_name, "interpretation": "Надежда и свет"}
    trace = MagicMock()
    status = MagicMock()
    status.__str__ = lambda s: "SUCCESS"
    trace.status = status
    trace.trace_id = "tid-draw-001"
    trace.steps = [step]
    trace.model_dump_json = MagicMock(return_value='{"trace_id":"tid-draw-001"}')
    return trace


async def test_draw_callback_saves_reading() -> None:
    trace = _make_successful_trace("The Star")

    with (
        patch("bot.handlers.tarot.run_card_of_day", new=AsyncMock(return_value=trace)),
        patch("bot.handlers.tarot.get_trace_hash", return_value="hash-test"),
        patch("bot.handlers.tarot.LLM_MODEL", "test-model"),
        patch("bot.handlers.tarot.TAROT_SALT", SALT),
    ):
        from bot.handlers.tarot import draw

        callback = AsyncMock()
        callback.from_user = MagicMock(id=999888)
        callback.message = AsyncMock()
        callback.answer = AsyncMock()
        await draw(callback)

    async with aiosqlite.connect(TEST_TAROT_DB) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM readings WHERE user_id = 999888") as cursor:
            row = await cursor.fetchone()

    assert row is not None
    assert row["spread"] == "card_of_the_day"
    assert row["paid"] == 0
    assert len(str(row["cards"])) > 0


async def test_draw_callback_sends_message() -> None:
    trace = _make_successful_trace("The Moon")

    with (
        patch("bot.handlers.tarot.run_card_of_day", new=AsyncMock(return_value=trace)),
        patch("bot.handlers.tarot.get_trace_hash", return_value=None),
        patch("bot.handlers.tarot.LLM_MODEL", "test-model"),
        patch("bot.handlers.tarot.TAROT_SALT", SALT),
    ):
        from bot.handlers.tarot import draw

        callback = AsyncMock()
        callback.from_user = MagicMock(id=111222)
        callback.message = AsyncMock()
        callback.answer = AsyncMock()
        await draw(callback)

    callback.message.answer.assert_called_once()
    text = callback.message.answer.call_args[0][0]
    assert "🔮" in text
    assert "карту дня" in text
    
