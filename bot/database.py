# bot/database.py
from __future__ import annotations

import aiosqlite

__all__ = [
    "DB_PATH",
    "init_db",
    "add_user",
    "get_user",
    "decrement_free_spreads",
    "add_referral",
    "save_reading",
    "get_user_readings",
    "get_top_users",
    "get_recent_traces",
    "get_reading_by_trace_hash",
    "save_pending_execution",
    "get_pending_execution",
    "delete_pending_execution",
]

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

        # Migration: add columns introduced in sprint_tarot_1 to pre-existing DBs
        existing: list[tuple[object, ...]] = list(
            await (await db.execute("PRAGMA table_info(readings)")).fetchall()
        )
        col_names = {row[1] for row in existing}  # type: ignore[index]
        if "execution_id" not in col_names:
            await db.execute("ALTER TABLE readings ADD COLUMN execution_id TEXT")
        if "trace_hash" not in col_names:
            await db.execute("ALTER TABLE readings ADD COLUMN trace_hash TEXT")

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
            "UPDATE users SET free_spreads = free_spreads - 1 WHERE user_id=? AND free_spreads > 0",
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
        await db.execute("DELETE FROM pending_executions WHERE user_id=?", (user_id,))
        await db.commit()


async def get_top_users(limit: int = 10) -> list[tuple[int, str | None, int, int]]:
    """Return top users by reading count: (user_id, username, total_readings, paid_readings)."""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            """
            SELECT u.user_id, u.username,
                   COUNT(r.id) as total,
                   SUM(CASE WHEN r.paid=1 THEN 1 ELSE 0 END) as paid
            FROM users u
            LEFT JOIN readings r ON u.user_id = r.user_id
            GROUP BY u.user_id
            ORDER BY total DESC
            LIMIT ?
            """,
            (limit,),
        )
        rows = await cursor.fetchall()
        return [
            (int(row[0]), str(row[1]) if row[1] else None, int(row[2] or 0), int(row[3] or 0))
            for row in rows
        ]


async def get_recent_traces(limit: int = 20) -> list[tuple[int, str, str, str | None]]:
    """Return recent readings with trace info: (user_id, spread, created_at, trace_hash)."""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            """
            SELECT user_id, spread,
                   datetime(created_at, 'unixepoch') as ts,
                   trace_hash
            FROM readings
            ORDER BY created_at DESC
            LIMIT ?
            """,
            (limit,),
        )
        rows = await cursor.fetchall()
        return [
            (int(row[0]), str(row[1]), str(row[2]), str(row[3]) if row[3] else None)
            for row in rows
        ]


async def get_reading_by_trace_hash(trace_hash: str) -> tuple[int, str, str, str] | None:
    """Lookup a reading by its trace_hash for user verification.

    Returns (user_id, spread, created_at, trace_hash) or None.
    """
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            """
            SELECT user_id, spread,
                   datetime(created_at, 'unixepoch') as ts,
                   trace_hash
            FROM readings
            WHERE trace_hash = ?
            LIMIT 1
            """,
            (trace_hash,),
        )
        row = await cursor.fetchone()
        if row is None:
            return None
        return (int(row[0]), str(row[1]), str(row[2]), str(row[3]))
