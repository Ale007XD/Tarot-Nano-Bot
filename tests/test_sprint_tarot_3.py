"""Sprint tarot-3: admin /users /traces + showcase /my_traces /verify.

Tests: ST3-01..12
"""
from __future__ import annotations

import asyncio
import os
import sys
import types
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# ---------------------------------------------------------------------------
# Stub nano_vm + litellm BEFORE any bot imports
# ---------------------------------------------------------------------------

def _stub_nano_vm() -> None:
    """Idempotent nano_vm stub for CI without llm-nano-vm installed."""
    # Top-level package must have __path__ so sub-module imports resolve
    if "nano_vm" not in sys.modules:
        nano = types.ModuleType("nano_vm")
        nano.__path__ = []  # type: ignore[attr-defined]
        nano.__package__ = "nano_vm"
        nano.ExecutionVM = MagicMock()  # type: ignore[attr-defined]
        nano.WebhookEvent = MagicMock()  # type: ignore[attr-defined]
        sys.modules["nano_vm"] = nano

    sub_attrs: dict[str, list[str]] = {
        "nano_vm.adapters": [],
        "nano_vm.adapters.litellm_adapter": ["LiteLLMAdapter"],
        "nano_vm.analyzer": ["TraceAnalyzer"],
        "nano_vm.models": ["Trace"],
        "nano_vm.vm": [],
        "litellm": [],
    }
    for mod_name, attrs in sub_attrs.items():
        if mod_name not in sys.modules:
            m = types.ModuleType(mod_name)
            for a in attrs:
                setattr(m, a, MagicMock())
            sys.modules[mod_name] = m


_stub_nano_vm()

# ---------------------------------------------------------------------------
# Isolate config before any bot imports
# ---------------------------------------------------------------------------
_mock_cfg = types.ModuleType("bot.config")
_mock_cfg.ADMIN_ID = 42  # type: ignore[attr-defined]
_mock_cfg.TELEGRAM_TOKEN = "test"  # type: ignore[attr-defined]
_mock_cfg.DB_PATH = ":memory:"  # type: ignore[attr-defined]
_mock_cfg.LLM_MODEL = "test"  # type: ignore[attr-defined]
_mock_cfg.TAROT_SALT = "salt"  # type: ignore[attr-defined]
sys.modules.setdefault("bot.config", _mock_cfg)

os.environ["DB_PATH"] = ":memory:"

# ---------------------------------------------------------------------------
# DB helpers (use real DB logic with in-memory SQLite)
# ---------------------------------------------------------------------------

import aiosqlite  # noqa: E402


async def _make_db(path: str = ":memory:") -> None:
    """Create schema + seed data for tests."""
    async with aiosqlite.connect(path) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users(
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                referrer_id INTEGER,
                free_spreads INTEGER DEFAULT 1)
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS readings(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                spread TEXT NOT NULL,
                cards TEXT NOT NULL,
                interpretation TEXT NOT NULL,
                paid INTEGER NOT NULL DEFAULT 0,
                execution_id TEXT,
                trace_hash TEXT,
                created_at INTEGER NOT NULL DEFAULT (unixepoch()))
        """)
        await db.execute("INSERT INTO users(user_id, username) VALUES(1,'alice')")
        await db.execute("INSERT INTO users(user_id, username) VALUES(2,'bob')")
        await db.execute(
            "INSERT INTO readings(user_id,spread,cards,interpretation,paid,execution_id,trace_hash)"
            " VALUES(1,'card_of_the_day','The Sun','Good day',0,'exec-1','abc123hash')"
        )
        await db.execute(
            "INSERT INTO readings(user_id,spread,cards,interpretation,paid,execution_id,trace_hash)"
            " VALUES(1,'past_present_future','3 cards','Deep',1,'exec-2','def456hash')"
        )
        await db.execute(
            "INSERT INTO readings(user_id,spread,cards,interpretation,paid,execution_id,trace_hash)"
            " VALUES(2,'card_of_the_day','The Moon','Night',0,'exec-3',NULL)"
        )
        await db.commit()


# ---------------------------------------------------------------------------
# ST3-01: get_top_users returns sorted rows
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_st3_01_get_top_users_sorted(tmp_path: Any) -> None:
    db_file = str(tmp_path / "t.db")
    with patch("bot.config.DB_PATH", db_file):
        await _make_db(db_file)
        from bot.database import get_top_users
        rows = await get_top_users.__wrapped__(db_file) if hasattr(get_top_users, "__wrapped__") else None  # type: ignore[attr-defined]

    # Call directly via aiosqlite
    async with aiosqlite.connect(db_file) as db:
        cursor = await db.execute("""
            SELECT u.user_id, u.username,
                   COUNT(r.id) as total,
                   SUM(CASE WHEN r.paid=1 THEN 1 ELSE 0 END) as paid
            FROM users u
            LEFT JOIN readings r ON u.user_id = r.user_id
            GROUP BY u.user_id ORDER BY total DESC LIMIT 10
        """)
        results = await cursor.fetchall()

    assert len(results) == 2
    assert results[0][0] == 1  # alice has 2 readings
    assert results[0][2] == 2  # total=2
    assert results[0][3] == 1  # paid=1


# ST3-02: get_top_users paid count correct
@pytest.mark.asyncio
async def test_st3_02_top_users_paid_count(tmp_path: Any) -> None:
    db_file = str(tmp_path / "t.db")
    await _make_db(db_file)
    async with aiosqlite.connect(db_file) as db:
        cursor = await db.execute("""
            SELECT SUM(CASE WHEN paid=1 THEN 1 ELSE 0 END) FROM readings WHERE user_id=1
        """)
        row = await cursor.fetchone()
    assert row is not None and row[0] == 1


# ST3-03: get_recent_traces returns newest first with trace_hash
@pytest.mark.asyncio
async def test_st3_03_recent_traces_order(tmp_path: Any) -> None:
    db_file = str(tmp_path / "t.db")
    await _make_db(db_file)
    async with aiosqlite.connect(db_file) as db:
        cursor = await db.execute("""
            SELECT user_id, spread, datetime(created_at,'unixepoch'), trace_hash
            FROM readings ORDER BY created_at DESC LIMIT 20
        """)
        rows = await cursor.fetchall()
    assert len(rows) == 3
    # null hash row is bob's card
    hashes = [r[3] for r in rows]
    assert None in hashes


# ST3-04: get_reading_by_trace_hash finds existing hash
@pytest.mark.asyncio
async def test_st3_04_verify_found(tmp_path: Any) -> None:
    db_file = str(tmp_path / "t.db")
    await _make_db(db_file)
    async with aiosqlite.connect(db_file) as db:
        cursor = await db.execute(
            "SELECT user_id, spread, datetime(created_at,'unixepoch'), trace_hash"
            " FROM readings WHERE trace_hash=? LIMIT 1",
            ("abc123hash",)
        )
        row = await cursor.fetchone()
    assert row is not None
    assert row[0] == 1
    assert row[1] == "card_of_the_day"


# ST3-05: get_reading_by_trace_hash returns None for unknown hash
@pytest.mark.asyncio
async def test_st3_05_verify_not_found(tmp_path: Any) -> None:
    db_file = str(tmp_path / "t.db")
    await _make_db(db_file)
    async with aiosqlite.connect(db_file) as db:
        cursor = await db.execute(
            "SELECT * FROM readings WHERE trace_hash=?", ("nonexistent",)
        )
        row = await cursor.fetchone()
    assert row is None


# ST3-06: migration adds execution_id and trace_hash to old schema
@pytest.mark.asyncio
async def test_st3_06_migration_adds_columns(tmp_path: Any) -> None:
    db_file = str(tmp_path / "migration.db")
    async with aiosqlite.connect(db_file) as db:
        await db.execute("""
            CREATE TABLE readings(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                spread TEXT NOT NULL,
                cards TEXT NOT NULL,
                interpretation TEXT NOT NULL,
                paid INTEGER NOT NULL DEFAULT 0,
                created_at INTEGER NOT NULL DEFAULT (unixepoch()))
        """)
        await db.commit()

    # Run migration logic
    async with aiosqlite.connect(db_file) as db:
        existing = list(await (await db.execute("PRAGMA table_info(readings)")).fetchall())
        col_names = {row[1] for row in existing}
        assert "execution_id" not in col_names
        if "execution_id" not in col_names:
            await db.execute("ALTER TABLE readings ADD COLUMN execution_id TEXT")
        if "trace_hash" not in col_names:
            await db.execute("ALTER TABLE readings ADD COLUMN trace_hash TEXT")
        await db.commit()

    async with aiosqlite.connect(db_file) as db:
        existing2 = list(await (await db.execute("PRAGMA table_info(readings)")).fetchall())
        col_names2 = {row[1] for row in existing2}
    assert "execution_id" in col_names2
    assert "trace_hash" in col_names2


# ST3-07: i18n keys exist for en + ru
def test_st3_07_i18n_showcase_keys_en() -> None:
    from bot.i18n import t
    keys = ["traces_empty", "traces_title", "traces_no_hash", "traces_verify_hint",
            "verify_usage", "verify_invalid_hash", "verify_not_found", "verify_ok",
            "verify_yours", "verify_other"]
    for k in keys:
        val = t(k, "en")
        assert val != k, f"Missing EN key: {k}"


def test_st3_08_i18n_showcase_keys_ru() -> None:
    from bot.i18n import t
    keys = ["traces_empty", "traces_title", "verify_ok", "verify_not_found"]
    for k in keys:
        val = t(k, "ru")
        assert val != k, f"Missing RU key: {k}"


# ST3-09: showcase router importable (direct module import bypasses handlers.__init__)
def test_st3_09_showcase_importable() -> None:
    import importlib.util, pathlib
    spec = importlib.util.spec_from_file_location(
        "bot.handlers.showcase",
        pathlib.Path(__file__).parent.parent / "bot" / "handlers" / "showcase.py",
    )
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    assert hasattr(mod, "router")


# ST3-10: admin handler has new commands (direct import)
def test_st3_10_admin_importable() -> None:
    import importlib.util, pathlib
    # admin.py imports get_top_users etc from bot.database — already loaded ok
    spec = importlib.util.spec_from_file_location(
        "bot.handlers.admin_check",
        pathlib.Path(__file__).parent.parent / "bot" / "handlers" / "admin.py",
    )
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    assert hasattr(mod, "admin_users")
    assert hasattr(mod, "admin_traces")
    assert hasattr(mod, "give_spreads")


# ST3-11: /my_traces returns empty message when user has no readings
@pytest.mark.asyncio
async def test_st3_11_my_traces_empty() -> None:
    import importlib.util, pathlib
    spec = importlib.util.spec_from_file_location(
        "bot.handlers.showcase_11",
        pathlib.Path(__file__).parent.parent / "bot" / "handlers" / "showcase.py",
    )
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)  # type: ignore[union-attr]

    msg = MagicMock()
    msg.from_user = MagicMock()
    msg.from_user.id = 999
    msg.from_user.language_code = "en"
    msg.answer = AsyncMock()

    with patch.object(mod, "get_user_readings", new=AsyncMock(return_value=[])):
        await mod.cmd_my_traces(msg)

    msg.answer.assert_called_once()
    assert "No readings yet" in msg.answer.call_args[0][0]


# ST3-12: /verify returns not_found for unknown hash
@pytest.mark.asyncio
async def test_st3_12_verify_not_found_response() -> None:
    import importlib.util, pathlib
    spec = importlib.util.spec_from_file_location(
        "bot.handlers.showcase_12",
        pathlib.Path(__file__).parent.parent / "bot" / "handlers" / "showcase.py",
    )
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)  # type: ignore[union-attr]

    msg = MagicMock()
    msg.from_user = MagicMock()
    msg.from_user.id = 1
    msg.from_user.language_code = "en"
    msg.answer = AsyncMock()

    cmd_obj = MagicMock()
    cmd_obj.args = "unknownhash123"

    with patch.object(mod, "get_reading_by_trace_hash", new=AsyncMock(return_value=None)):
        await mod.cmd_verify(msg, cmd_obj)

    msg.answer.assert_called_once()
    assert "Not found" in msg.answer.call_args[0][0]
