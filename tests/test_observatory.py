import pytest
import pytest_asyncio
import aiosqlite
from bot.observatory.trace_analyzer import TraceAnalyzer


@pytest_asyncio.fixture(scope="function")
async def telemetry_db():
    async with aiosqlite.connect(":memory:") as db:
        await db.execute(
            "CREATE TABLE readings (id TEXT, user_id INTEGER, paid INTEGER)"
        )
        # Генерируем тестовую трассу: 3 бесплатных перехода, 1 оплаченный
        test_data = [
            ("r1", 101, 0),
            ("r2", 101, 1),
            ("r3", 102, 0),
            ("r4", 103, 0),
        ]
        await db.executemany(
            "INSERT INTO readings (id, user_id, paid) VALUES (?, ?, ?)", test_data
        )
        await db.commit()
        yield db


@pytest.mark.asyncio
async def test_observatory_metrics_delivery(telemetry_db):
    analyzer = TraceAnalyzer(telemetry_db)
    metrics = await analyzer.calculate_retention_and_conversion()

    assert metrics.total_users == 3
    assert metrics.conversion_rate == 0.25  # 1 paid из 4-х
    assert metrics.state_distribution["state_paid_terminal"] == 1
    assert metrics.state_distribution["state_free_active"] == 3
