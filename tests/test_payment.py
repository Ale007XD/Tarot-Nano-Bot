"""Tests for payment handlers."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest
from aiogram.types import PreCheckoutQuery, User

from bot.handlers.payment import OrderPayload, process_pre_checkout_query


def test_order_payload_valid() -> None:
    p = OrderPayload(user_id=1, reading_id="r1", amount=69)
    assert p.user_id == 1
    assert p.amount == 69


def test_order_payload_invalid_amount() -> None:
    with pytest.raises(ValueError):
        OrderPayload(user_id=1, reading_id="r1", amount=0)


async def test_pre_checkout_query_valid_payload() -> None:
    payload = OrderPayload(user_id=12345, reading_id="r1", amount=69)
    query = PreCheckoutQuery(
        id="qid",
        from_user=User(id=12345, is_bot=False, first_name="T"),
        currency="XTR",
        total_amount=69,
        invoice_payload=payload.model_dump_json(),
    )
    with patch.object(PreCheckoutQuery, "answer", new_callable=AsyncMock) as mock_ans:
        await process_pre_checkout_query(query)
        mock_ans.assert_called_once_with(ok=True)


async def test_pre_checkout_query_invalid_payload() -> None:
    query = PreCheckoutQuery(
        id="qid",
        from_user=User(id=1, is_bot=False, first_name="T"),
        currency="XTR",
        total_amount=69,
        invoice_payload="not-json",
    )
    with patch.object(PreCheckoutQuery, "answer", new_callable=AsyncMock) as mock_ans:
        await process_pre_checkout_query(query)
        call_kwargs = mock_ans.call_args[1]
        assert call_kwargs["ok"] is False
