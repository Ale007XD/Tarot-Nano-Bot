"""Tests for bot/database.py — async, uses in-memory SQLite via tmp path."""

from __future__ import annotations

import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import bot.config as config_module


@pytest.fixture(autouse=True)
def tmp_db(tmp_path: object, monkeypatch: pytest.MonkeyPatch) -> None:
    """Redirect DB_PATH to a temp file for each test."""
    db_file = str(tmp_path) + "/test_tarot.db"  # type: ignore[operator]
    monkeypatch.setattr(config_module, "DB_PATH", db_file)
    # Also patch the DB_PATH that database.py imported at module load
    import bot.database as db_mod

    monkeypatch.setattr(db_mod, "DB_PATH", db_file)


@pytest.mark.asyncio
async def test_init_db_creates_tables() -> None:
    import aiosqlite

    import bot.database as db_mod
    from bot.database import init_db

    await init_db()
    async with aiosqlite.connect(db_mod.DB_PATH) as db:
        cursor = await db.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = {row[0] for row in await cursor.fetchall()}
    assert "users" in tables
    assert "readings" in tables
    assert "referrals" in tables
    assert "pending_executions" in tables


@pytest.mark.asyncio
async def test_add_and_get_user() -> None:
    from bot.database import add_user, get_user, init_db

    await init_db()
    await add_user(123, "alice")
    row = await get_user(123)
    assert row is not None
    assert row[0] == 123


@pytest.mark.asyncio
async def test_add_user_idempotent() -> None:
    from bot.database import add_user, get_user, init_db

    await init_db()
    await add_user(42, "bob")
    await add_user(42, "bob")  # second call must not raise
    row = await get_user(42)
    assert row is not None


@pytest.mark.asyncio
async def test_get_user_none_for_unknown() -> None:
    from bot.database import get_user, init_db

    await init_db()
    assert await get_user(999999) is None


@pytest.mark.asyncio
async def test_decrement_free_spreads() -> None:
    from bot.database import add_user, decrement_free_spreads, get_user, init_db

    await init_db()
    await add_user(10, "carol")
    await decrement_free_spreads(10)
    row = await get_user(10)
    assert row is not None
    assert row[3] == 0  # free_spreads


@pytest.mark.asyncio
async def test_decrement_free_spreads_no_underflow() -> None:
    from bot.database import add_user, decrement_free_spreads, get_user, init_db

    await init_db()
    await add_user(11, "dave")
    await decrement_free_spreads(11)  # 1 → 0
    await decrement_free_spreads(11)  # 0 → stays 0
    row = await get_user(11)
    assert row is not None
    assert row[3] == 0


@pytest.mark.asyncio
async def test_add_referral_increments_spreads() -> None:
    from bot.database import add_referral, add_user, get_user, init_db

    await init_db()
    await add_user(20, "eve")
    await add_user(21, "frank")
    await add_referral(referrer_id=20, invited_id=21)
    row = await get_user(20)
    assert row is not None
    assert row[3] == 2  # 1 default + 1 referral


@pytest.mark.asyncio
async def test_save_and_get_reading() -> None:
    from bot.database import add_user, get_user_readings, init_db, save_reading

    await init_db()
    await add_user(30, "grace")
    await save_reading(
        user_id=30,
        spread="card_of_the_day",
        cards="The Fool",
        interpretation="You stand at a threshold.",
        paid=0,
        execution_id="exec-abc",
        trace_hash="hash-xyz",
    )
    rows = await get_user_readings(30)
    assert len(rows) == 1
    assert rows[0][1] == "card_of_the_day"
    assert rows[0][2] == "The Fool"
    assert rows[0][5] == "exec-abc"
    assert rows[0][6] == "hash-xyz"


@pytest.mark.asyncio
async def test_get_user_readings_empty() -> None:
    from bot.database import get_user_readings, init_db

    await init_db()
    assert await get_user_readings(99999) == []


@pytest.mark.asyncio
async def test_save_and_get_pending_execution() -> None:
    from bot.database import (
        get_pending_execution,
        init_db,
        save_pending_execution,
    )

    await init_db()
    await save_pending_execution(50, "exec-001", '{"trace": "data"}')
    result = await get_pending_execution(50)
    assert result is not None
    exec_id, trace_json = result
    assert exec_id == "exec-001"
    assert "trace" in trace_json


@pytest.mark.asyncio
async def test_pending_execution_upsert() -> None:
    from bot.database import (
        get_pending_execution,
        init_db,
        save_pending_execution,
    )

    await init_db()
    await save_pending_execution(51, "exec-001", '{"v": 1}')
    await save_pending_execution(51, "exec-002", '{"v": 2}')  # upsert
    result = await get_pending_execution(51)
    assert result is not None
    assert result[0] == "exec-002"


@pytest.mark.asyncio
async def test_delete_pending_execution() -> None:
    from bot.database import (
        delete_pending_execution,
        get_pending_execution,
        init_db,
        save_pending_execution,
    )

    await init_db()
    await save_pending_execution(52, "exec-001", "{}")
    await delete_pending_execution(52)
    assert await get_pending_execution(52) is None


@pytest.mark.asyncio
async def test_get_pending_execution_none_for_unknown() -> None:
    from bot.database import get_pending_execution, init_db

    await init_db()
    assert await get_pending_execution(999) is None
