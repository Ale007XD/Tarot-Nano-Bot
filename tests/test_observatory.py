"""Tests for TraceAnalyzer metrics."""

from __future__ import annotations

import aiosqlite
import pytest

from bot.observatory.trace_analyzer import TraceAnalyzer


@pytest.fixture
async def telemetry_db() -> object:
    async with aiosqlite.connect(":memory:") as db:
        await db.execute(
            "CREATE TABLE readings (id TEXT, user_id INTEGER, paid INTEGER)"
        )
        await db.executemany(
            "INSERT INTO readings VALUES (?, ?, ?)",
            [("r1", 101, 0), ("r2", 101, 1), ("r3", 102, 0), ("r4", 103, 0)],
        )
        await db.commit()
        yield db


async def test_observatory_total_users(telemetry_db: object) -> None:
    metrics = await TraceAnalyzer(telemetry_db).calculate_retention_and_conversion()
    assert metrics.total_users == 3


async def test_observatory_conversion_rate(telemetry_db: object) -> None:
    metrics = await TraceAnalyzer(telemetry_db).calculate_retention_and_conversion()
    assert metrics.conversion_rate == 0.25


async def test_observatory_state_distribution(telemetry_db: object) -> None:
    metrics = await TraceAnalyzer(telemetry_db).calculate_retention_and_conversion()
    assert metrics.state_distribution["state_paid_terminal"] == 1
    assert metrics.state_distribution["state_free_active"] == 3
