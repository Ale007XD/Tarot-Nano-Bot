# bot/database.py
from __future__ import annotations

import json

import aiosqlite

from bot.config import DB_PATH


# ---------------------------------------------------------------------------
# Schema init
# ---------------------------------------------------------------------------

async def init_db() -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("PRAGMA journal_mode=WAL")

        await db.execute("""
            CREATE TABLE IF NOT EXISTS users(
                user_id     INTEGER PRIMARY KEY,
                username    TEXT,
                referrer_id INTEGER,
                free_spreads INTEGER DEFAULT 1
            )
        """)

        await db.execute("""
            CREATE TABLE IF NOT EXISTS readings(
                id             INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id        INTEGER NOT NULL,
                spread         TEXT NOT NULL,
                cards          TEXT NOT NULL,
                interpretation TEXT NOT NULL,
                paid           INTEGER NOT NULL DEFAULT 0,
                execution_id   TEXT,
                trace_hash     TEXT,
                created_at     INTEGER NOT NULL DEFAULT (unixepoch())
            )
        """)

        await db.execute("""
            CREATE TABLE IF NOT EXISTS referrals(
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                referrer_id INTEGER NOT NULL,
                invited_id  INTEGER NOT NULL
            )
        """)

        # Transient: holds serialised Trace for suspended full_reading executions.
        # Deleted after resume (success or failure).
        await db.execute("""
            CREATE TABLE IF NOT EXISTS pending_executions(
                user_id     INTEGER PRIMARY KEY,
                execution_id TEXT NOT NULL,
                trace_json  TEXT NOT NULL,
                created_at  INTEGER NOT NULL DEFAULT (unixepoch())
            )
        """)

        await db.commit()


# ---------------------------------------------------------------------------
# Users
# ---------------------------------------------------------------------------

async def add_user(
    user_id: int,
    username: str | None,
    referrer_id: int | None = None,
) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT OR IGNORE INTO users(user_id, username, referrer_id) VALUES(?,?,?)",
            (user_id, username, referrer_id),
        )
        await db.commit()


async def get_user(user_id: int) -> tuple[int, str | None, int | None, int] | None:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
        row = await cursor.fetchone()
        if row is None:
            return None
        return row  # type: ignore[return-value]


async def decrement_free_spreads(user_id: int) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE users SET free_spreads = free_spreads - 1 "
            "WHERE user_id=? AND free_spreads > 0",
            (user_id,),
        )
        await db.commit()


# ---------------------------------------------------------------------------
# Referrals
# ---------------------------------------------------------------------------

async def add_referral(referrer_id: int, invited_id: int) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO referrals(referrer_id, invited_id) VALUES(?,?)",
            (referrer_id, invited_id),
        )
        await db.execute(
            "UPDATE users SET free_spreads = free_spreads + 1 WHERE user_id=?",
            (referrer_id,),
        )
        await db.commit()


# ---------------------------------------------------------------------------
# Readings
# ---------------------------------------------------------------------------

async def save_reading(
    user_id: int,
    spread: str,
    cards: str,
    interpretation: str,
    paid: int,
    execution_id: str | None = None,
    trace_hash: str | None = None,
) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO readings"
            "(user_id, spread, cards, interpretation, paid, execution_id, trace_hash)"
            " VALUES(?,?,?,?,?,?,?)",
            (user_id, spread, cards, interpretation, paid, execution_id, trace_hash),
        )
        await db.commit()


async def get_user_readings(user_id: int, limit: int = 10) -> list[tuple[object, ...]]:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT id, spread, cards, interpretation, paid, execution_id, trace_hash,"
            " created_at FROM readings"
            " WHERE user_id=? ORDER BY id DESC LIMIT ?",
            (user_id, limit),
        )
        rows = await cursor.fetchall()
        return [tuple(row) for row in rows]


# ---------------------------------------------------------------------------
# Pending executions (suspend / resume bridge)
# ---------------------------------------------------------------------------

async def save_pending_execution(
    user_id: int,
    execution_id: str,
    trace_json: str,
) -> None:
    """Upsert — one pending execution per user at a time."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO pending_executions(user_id, execution_id, trace_json)"
            " VALUES(?,?,?)"
            " ON CONFLICT(user_id) DO UPDATE SET"
            "   execution_id=excluded.execution_id,"
            "   trace_json=excluded.trace_json,"
            "   created_at=unixepoch()",
            (user_id, execution_id, trace_json),
        )
        await db.commit()


async def get_pending_execution(
    user_id: int,
) -> tuple[str, str] | None:
    """Return (execution_id, trace_json) or None."""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT execution_id, trace_json FROM pending_executions WHERE user_id=?",
            (user_id,),
        )
        row = await cursor.fetchone()
        if row is None:
            return None
        return str(row[0]), str(row[1])


async def delete_pending_execution(user_id: int) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "DELETE FROM pending_executions WHERE user_id=?", (user_id,)
        )
        await db.commit()
