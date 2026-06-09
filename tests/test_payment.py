import pytest
import pytest_asyncio
import aiosqlite
from datetime import datetime
from unittest.mock import patch, AsyncMock
from aiogram.types import PreCheckoutQuery, User, SuccessfulPayment, Message, Chat
from bot.handlers.payment import (
    process_pre_checkout_query,
    process_successful_payment,
    OrderPayload,
)


@pytest_asyncio.fixture(scope="function")
async def mock_db():
    """
    Изолированная embedded СУБД для проверки транзакционных переходов.
    Обеспечивает чистую фикстуру для каждого тест-кейса.
    """
    async with aiosqlite.connect(":memory:") as db:
        await db.execute(
            """
            CREATE TABLE readings (
                id TEXT PRIMARY KEY,
                user_id INTEGER,
                paid INTEGER DEFAULT 0
            )
            """
        )
        # Инициализация исходного состояния S (paid = 0)
        await db.execute(
            "INSERT INTO readings (id, user_id, paid) VALUES (?, ?, ?)",
            ("reading_test_001", 12345, 0),
        )
        await db.commit()
        yield db


@pytest.mark.asyncio
async def test_pre_checkout_query_validation_success():
    """Проверка успешной валидации схемы инвойса и отправки ok=True."""
    payload = OrderPayload(user_id=12345, reading_id="reading_test_001", amount=50)

    query = PreCheckoutQuery(
        id="query_id_123",
        from_user=User(id=12345, is_bot=False, first_name="Tester"),
        currency="XTR",
        total_amount=50,
        invoice_payload=payload.model_dump_json(),
    )

    # Патчинг метода на уровне класса для обхода Pydantic frozen_instance guardrail
    with patch.object(
        PreCheckoutQuery, "answer", new_callable=AsyncMock
    ) as mock_answer:
        await process_pre_checkout_query(query)
        mock_answer.assert_called_once_with(ok=True)


@pytest.mark.asyncio
async def test_successful_payment_state_transition(mock_db):
    """
    Проверка инварианта перехода:
    delta(S, E_payment) -> S', где S'.paid = 1
    """
    payload = OrderPayload(user_id=12345, reading_id="reading_test_001", amount=50)

    succ_payment = SuccessfulPayment(
        currency="XTR",
        total_amount=50,
        invoice_payload=payload.model_dump_json(),
        shipping_option_id=None,
        order_info=None,
        telegram_payment_charge_id="xtr_charge_id",
        provider_payment_charge_id="prov_charge_id",
    )

    message = Message(
        message_id=999,
        date=datetime.now(),
        chat=Chat(id=12345, type="private"),
        from_user=User(id=12345, is_bot=False, first_name="Tester"),
        successful_payment=succ_payment,
    )

    # Патчинг метода отправки сообщений на уровне класса
    with patch.object(Message, "answer", new_callable=AsyncMock) as mock_answer:
        # Выполнение перехода delta(S, E)
        await process_successful_payment(message, mock_db)

        # Проверка отправки нотификации
        mock_answer.assert_called_once()
        assert "успешно верифицирована" in mock_answer.call_args[0][0]

    # Верификация мутации состояния в СУБД (S -> S')
    async with mock_db.execute(
        "SELECT paid FROM readings WHERE id = ?", ("reading_test_001",)
    ) as cursor:
        row = await cursor.fetchone()
        assert row is not None
        assert row[0] == 1, (
            "Математический инвариант нарушен: состояние paid не перешло в 1"
        )
