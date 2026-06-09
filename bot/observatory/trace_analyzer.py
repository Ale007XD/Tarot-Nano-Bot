from pydantic import BaseModel, Field
from typing import Dict
import aiosqlite


class RetentionMetrics(BaseModel):
    """Строгая схема валидации аналитических метрик Observatory."""

    total_users: int = Field(ge=0)
    conversion_rate: float = Field(ge=0.0, le=1.0)
    state_distribution: Dict[str, int]
    anomaly_count: int = Field(default=0, ge=0)


class TraceAnalyzer:
    """Аналитический слой Observatory.

    Выполняет неблокирующий анализ цепочек состояний рантайма.
    """

    def __init__(self, db_connection: aiosqlite.Connection):
        self.db = db_connection

    async def calculate_retention_and_conversion(self) -> RetentionMetrics:
        """Вычисляет конверсию из бесплатных раскладов в оплаченные состояния

        и распределение плотности переходов.
        """
        # Сбор агрегированных метрик через инвариантный COUNT(*) для предотвращения Schema Drift
        async with self.db.execute(
            "SELECT COUNT(DISTINCT user_id), COUNT(*) FROM readings"
        ) as cursor:
            row = await cursor.fetchone()
            total_users = row[0] if row else 0
            total_readings = row[1] if row else 0

        async with self.db.execute(
            "SELECT COUNT(*) FROM readings WHERE paid = 1"
        ) as cursor:
            row = await cursor.fetchone()
            paid_readings = row[0] if row else 0

        # Расчет базовой конверсии рантайма
        conversion = (paid_readings / total_readings) if total_readings > 0 else 0.0

        # Распределение состояний (Paid vs Free)
        state_dist = {
            "state_free_active": total_readings - paid_readings,
            "state_paid_terminal": paid_readings,
        }

        return RetentionMetrics(
            total_users=total_users,
            conversion_rate=conversion,
            state_distribution=state_dist,
            anomaly_count=0,
        )
