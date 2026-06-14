"""Sprint Tarot-2: wiring tests.

Covers:
- tarot.draw callback: SUCCESS → save_reading, show card
- tarot.draw callback: FSM error → error message, no save
- tarot.full_reading callback: SUCCESS (free) → save_reading, show spread
- tarot.full_reading callback: SUSPENDED → save_pending + invoice
- tarot.full_reading callback: FSM error → error message
- payment.process_pre_checkout_query: valid payload → ok=True
- payment.process_pre_checkout_query: invalid payload → ok=False
- payment.process_successful_payment: SUCCESS → save_reading + show spread
- payment.process_successful_payment: no pending → warning message
- payment.process_successful_payment: resume FAILED → error message
- payment_service.create_reading_invoice: payload structure
"""

from __future__ import annotations

import json
from types import SimpleNamespace
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_trace(status: str, trace_id: str = "tid-001", steps: list[Any] | None = None) -> Any:
    t = MagicMock()
    t.trace_id = trace_id
    status_obj = MagicMock()
    status_obj.__str__ = lambda s: status
    t.status = status_obj
    t.steps = steps or []
    t.model_dump_json = MagicMock(return_value=json.dumps({"trace_id": trace_id, "status": status}))
    return t


def _make_step_with_card(card_name: str, interpretation: str) -> Any:
    step = MagicMock()
    step.output = {"card_name": card_name, "interpretation": interpretation}
    return step


def _make_step_with_spread(spread: str, interpretation: str) -> Any:
    step = MagicMock()
    step.output = {"spread": spread, "interpretation": interpretation}
    return step


def _make_callback(user_id: int = 42, data: str = "draw") -> MagicMock:
    cb = MagicMock()
    cb.from_user = MagicMock(id=user_id)
    cb.message = AsyncMock()
    cb.bot = AsyncMock()
    cb.data = data
    cb.answer = AsyncMock()
    return cb


def _make_message(user_id: int = 42, payload_json: str = "") -> MagicMock:
    msg = MagicMock()
    msg.from_user = MagicMock(id=user_id)
    msg.answer = AsyncMock()
    sp = MagicMock()
    sp.invoice_payload = payload_json
    sp.telegram_payment_charge_id = "charge-xyz"
    msg.successful_payment = sp
    return msg


def _make_pre_checkout(payload_json: str, query_id: str = "q1") -> MagicMock:
    pq = MagicMock()
    pq.invoice_payload = payload_json
    pq.id = query_id
    pq.answer = AsyncMock()
    return pq


# ---------------------------------------------------------------------------
# tarot.draw tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_draw_success_saves_reading() -> None:
    step = _make_step_with_card("The Star", "Надежда и вдохновение")
    trace = _make_trace("SUCCESS", steps=[step])

    with (
        patch("bot.handlers.tarot.run_card_of_day", new=AsyncMock(return_value=trace)),
        patch("bot.handlers.tarot.get_trace_hash", return_value="hash-abc"),
        patch("bot.handlers.tarot.save_reading", new=AsyncMock()) as mock_save,
        patch("bot.handlers.tarot.LLM_MODEL", "test-model"),
        patch("bot.handlers.tarot.TAROT_SALT", "salt"),
    ):
        from bot.handlers.tarot import draw
        cb = _make_callback()
        await draw(cb)

    mock_save.assert_awaited_once()
    call_kwargs = mock_save.call_args.kwargs
    assert call_kwargs["spread"] == "card_of_the_day"
    assert call_kwargs["cards"] == "The Star"
    assert call_kwargs["trace_hash"] == "hash-abc"
    cb.message.answer.assert_awaited_once()
    text = cb.message.answer.call_args.args[0]
    assert "The Star" in text


@pytest.mark.asyncio
async def test_draw_fsm_error_no_save() -> None:
    trace = _make_trace("FAILED")

    with (
        patch("bot.handlers.tarot.run_card_of_day", new=AsyncMock(return_value=trace)),
        patch("bot.handlers.tarot.save_reading", new=AsyncMock()) as mock_save,
        patch("bot.handlers.tarot.LLM_MODEL", "test-model"),
        patch("bot.handlers.tarot.TAROT_SALT", "salt"),
    ):
        from bot.handlers.tarot import draw
        cb = _make_callback()
        await draw(cb)

    mock_save.assert_not_awaited()
    cb.message.answer.assert_awaited_once()
    text = cb.message.answer.call_args.args[0]
    assert "⚠️" in text


@pytest.mark.asyncio
async def test_draw_exception_handled() -> None:
    with (
        patch("bot.handlers.tarot.run_card_of_day", new=AsyncMock(side_effect=RuntimeError("boom"))),
        patch("bot.handlers.tarot.save_reading", new=AsyncMock()) as mock_save,
        patch("bot.handlers.tarot.LLM_MODEL", "test-model"),
        patch("bot.handlers.tarot.TAROT_SALT", "salt"),
    ):
        from bot.handlers.tarot import draw
        cb = _make_callback()
        await draw(cb)

    mock_save.assert_not_awaited()
    cb.answer.assert_awaited_once()


# ---------------------------------------------------------------------------
# tarot.full_reading tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_full_reading_success_free() -> None:
    step = _make_step_with_spread("Past: The Fool\nPresent: The Star\nFuture: The Sun", "Великий путь")
    trace = _make_trace("SUCCESS", steps=[step])

    with (
        patch("bot.handlers.tarot.get_user", new=AsyncMock(return_value=(42, "user", None, 2))),
        patch("bot.handlers.tarot.run_full_reading", new=AsyncMock(return_value=trace)),
        patch("bot.handlers.tarot.get_trace_hash", return_value="hash-xyz"),
        patch("bot.handlers.tarot.save_reading", new=AsyncMock()) as mock_save,
        patch("bot.handlers.tarot.LLM_MODEL", "test-model"),
    ):
        from bot.handlers.tarot import full_reading
        cb = _make_callback(data="full_reading")
        await full_reading(cb)

    mock_save.assert_awaited_once()
    kwargs = mock_save.call_args.kwargs
    assert kwargs["spread"] == "past_present_future"
    assert kwargs["paid"] == 0


@pytest.mark.asyncio
async def test_full_reading_suspended_saves_pending_and_invoice() -> None:
    trace = _make_trace("SUSPENDED", trace_id="tid-suspend")

    with (
        patch("bot.handlers.tarot.get_user", new=AsyncMock(return_value=(42, "user", None, 0))),
        patch("bot.handlers.tarot.run_full_reading", new=AsyncMock(return_value=trace)),
        patch("bot.handlers.tarot.save_pending_execution", new=AsyncMock()) as mock_pending,
        patch("bot.handlers.tarot.save_reading", new=AsyncMock()) as mock_save,
        patch("bot.handlers.tarot.LLM_MODEL", "test-model"),
        patch("bot.services.payment_service.create_reading_invoice", new=AsyncMock()),
    ):
        from bot.handlers.tarot import full_reading
        cb = _make_callback(data="full_reading")
        await full_reading(cb)

    mock_pending.assert_awaited_once_with(42, "tid-suspend", trace.model_dump_json())
    mock_save.assert_not_awaited()
    cb.message.answer.assert_not_awaited()  # invoice, not direct answer


@pytest.mark.asyncio
async def test_full_reading_fsm_error() -> None:
    trace = _make_trace("FAILED")

    with (
        patch("bot.handlers.tarot.get_user", new=AsyncMock(return_value=(42, "user", None, 0))),
        patch("bot.handlers.tarot.run_full_reading", new=AsyncMock(return_value=trace)),
        patch("bot.handlers.tarot.save_reading", new=AsyncMock()) as mock_save,
        patch("bot.handlers.tarot.LLM_MODEL", "test-model"),
    ):
        from bot.handlers.tarot import full_reading
        cb = _make_callback(data="full_reading")
        await full_reading(cb)

    mock_save.assert_not_awaited()
    text = cb.message.answer.call_args.args[0]
    assert "⚠️" in text


# ---------------------------------------------------------------------------
# payment.process_pre_checkout_query tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_pre_checkout_valid() -> None:
    payload = json.dumps({"user_id": 42, "execution_id": "tid-001", "amount": 69})
    pq = _make_pre_checkout(payload)

    from bot.handlers.payment import process_pre_checkout_query
    await process_pre_checkout_query(pq)

    pq.answer.assert_awaited_once_with(ok=True)


@pytest.mark.asyncio
async def test_pre_checkout_invalid() -> None:
    pq = _make_pre_checkout("not-json{{{")

    from bot.handlers.payment import process_pre_checkout_query
    await process_pre_checkout_query(pq)

    call_kwargs = pq.answer.call_args.kwargs
    assert call_kwargs["ok"] is False


# ---------------------------------------------------------------------------
# payment.process_successful_payment tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_successful_payment_resumes_and_saves() -> None:
    payload = json.dumps({"user_id": 42, "execution_id": "tid-001", "amount": 69})
    msg = _make_message(42, payload)

    step = _make_step_with_spread("Past: X\nPresent: Y\nFuture: Z", "Великое будущее")
    resumed = _make_trace("SUCCESS", trace_id="tid-002", steps=[step])

    trace_json = json.dumps({"trace_id": "tid-001", "status": "SUSPENDED"})

    with (
        patch("bot.handlers.payment.get_pending_execution", new=AsyncMock(return_value=("tid-001", trace_json))),
        patch("bot.handlers.payment.delete_pending_execution", new=AsyncMock()) as mock_delete,
        patch("bot.handlers.payment.save_reading", new=AsyncMock()) as mock_save,
        patch("bot.handlers.payment.get_trace_hash", return_value="hash-resumed"),
        patch("bot.handlers.payment.Trace.model_validate_json", return_value=MagicMock()),
        patch("bot.handlers.payment.resume_full_reading", new=AsyncMock(return_value=resumed)),
        patch("bot.handlers.payment.LLM_MODEL", "test-model"),
    ):
        from bot.handlers.payment import process_successful_payment
        await process_successful_payment(msg)

    mock_delete.assert_awaited_once_with(42)
    mock_save.assert_awaited_once()
    kwargs = mock_save.call_args.kwargs
    assert kwargs["paid"] == 1
    assert kwargs["trace_hash"] == "hash-resumed"
    msg.answer.assert_awaited()


@pytest.mark.asyncio
async def test_successful_payment_no_pending() -> None:
    payload = json.dumps({"user_id": 42, "execution_id": "tid-001", "amount": 69})
    msg = _make_message(42, payload)

    with (
        patch("bot.handlers.payment.get_pending_execution", new=AsyncMock(return_value=None)),
        patch("bot.handlers.payment.save_reading", new=AsyncMock()) as mock_save,
    ):
        from bot.handlers.payment import process_successful_payment
        await process_successful_payment(msg)

    mock_save.assert_not_awaited()
    text = msg.answer.call_args.args[0]
    assert "⚠️" in text


@pytest.mark.asyncio
async def test_successful_payment_resume_failed() -> None:
    payload = json.dumps({"user_id": 42, "execution_id": "tid-001", "amount": 69})
    msg = _make_message(42, payload)

    trace_json = json.dumps({"trace_id": "tid-001", "status": "SUSPENDED"})
    resumed = _make_trace("FAILED", trace_id="tid-002")

    with (
        patch("bot.handlers.payment.get_pending_execution", new=AsyncMock(return_value=("tid-001", trace_json))),
        patch("bot.handlers.payment.delete_pending_execution", new=AsyncMock()),
        patch("bot.handlers.payment.save_reading", new=AsyncMock()) as mock_save,
        patch("bot.handlers.payment.Trace.model_validate_json", return_value=MagicMock()),
        patch("bot.handlers.payment.resume_full_reading", new=AsyncMock(return_value=resumed)),
        patch("bot.handlers.payment.LLM_MODEL", "test-model"),
    ):
        from bot.handlers.payment import process_successful_payment
        await process_successful_payment(msg)

    mock_save.assert_not_awaited()
    text = msg.answer.call_args.args[0]
    assert "⚠️" in text


# ---------------------------------------------------------------------------
# payment_service tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_create_reading_invoice_payload_structure() -> None:
    bot = AsyncMock()
    bot.send_invoice = AsyncMock()

    from bot.services.payment_service import create_reading_invoice
    await create_reading_invoice(bot, user_id=42, execution_id="tid-exec")

    bot.send_invoice.assert_awaited_once()
    kwargs = bot.send_invoice.call_args.kwargs
    assert kwargs["currency"] == "XTR"
    assert kwargs["chat_id"] == 42

    payload = json.loads(kwargs["payload"])
    assert payload["user_id"] == 42
    assert payload["execution_id"] == "tid-exec"
    assert payload["amount"] > 0
