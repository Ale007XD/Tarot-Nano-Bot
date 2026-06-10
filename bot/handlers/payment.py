"""Payment handler — Telegram Stars pre-checkout + successful_payment → FSM resume."""

from __future__ import annotations

import logging

from aiogram import F, Router
from aiogram.types import Message, PreCheckoutQuery
from nano_vm.models import Trace
from pydantic import BaseModel, Field

from bot.config import LLM_MODEL
from bot.database import (
    delete_pending_execution,
    get_pending_execution,
    save_reading,
)
from bot.keyboards import share_kb
from bot.vm_runner import get_trace_hash, resume_full_reading

router = Router(name="payment_router")


class OrderPayload(BaseModel):
    user_id: int
    execution_id: str  # FSM trace_id — no reading_id techdebt
    amount: int = Field(gt=0)


@router.pre_checkout_query()
async def process_pre_checkout_query(pre_checkout_query: PreCheckoutQuery) -> None:
    try:
        OrderPayload.model_validate_json(pre_checkout_query.invoice_payload)
        await pre_checkout_query.answer(ok=True)
    except Exception as e:
        logging.error(f"[Payment] PreCheckoutQuery validation failure: {e}")
        await pre_checkout_query.answer(
            ok=False,
            error_message="Критическая ошибка валидации структуры платежа. Повторите запрос.",
        )


@router.message(F.successful_payment)
async def process_successful_payment(message: Message) -> None:
    successful_payment = message.successful_payment
    if not message.from_user or not successful_payment:
        return

    user_id = message.from_user.id

    try:
        payload = OrderPayload.model_validate_json(successful_payment.invoice_payload)
    except Exception as e:
        logging.error(f"[Payment] Payload parse failure: {e}")
        await message.answer("🚨 Ошибка разбора платежа. Обратитесь в поддержку.")
        return

    pending = await get_pending_execution(user_id)
    if pending is None:
        logging.warning(f"[Payment] No pending execution for user={user_id}")
        await message.answer(
            "⚠️ Оплата получена, но активный расклад не найден. Обратитесь в поддержку."
        )
        return

    execution_id_db, trace_json = pending

    if execution_id_db != payload.execution_id:
        logging.warning(
            f"[Payment] execution_id mismatch: db={execution_id_db} payload={payload.execution_id}"
        )

    try:
        trace = Trace.model_validate_json(trace_json)
        charge_id = successful_payment.telegram_payment_charge_id
        resumed = await resume_full_reading(
            trace=trace,
            charge_id=charge_id,
            model=LLM_MODEL,
        )
    except Exception as e:
        logging.error(f"[Payment] resume_full_reading failed: {e}")
        await message.answer(
            "🚨 Ошибка при продолжении расклада после оплаты. Обратитесь в поддержку."
        )
        return
    finally:
        await delete_pending_execution(user_id)

    status = str(getattr(resumed, "status", "")).upper()
    if not status.endswith("SUCCESS"):
        logging.error(f"[Payment] resume ended with status={status}")
        await message.answer(
            "⚠️ Оплата получена, но расклад не завершился корректно. Обратитесь в поддержку."
        )
        return

    cards_text = ""
    interpretation = ""
    try:
        steps = getattr(resumed, "steps", [])
        for step in steps:
            out = getattr(step, "output", None)
            if isinstance(out, dict) and "spread" in out:
                cards_text = str(out.get("spread", ""))
                interpretation = str(out.get("interpretation", ""))
                break
    except Exception as e:
        logging.error(f"[Payment] trace extraction failed: {e}")

    trace_hash = get_trace_hash(resumed)
    resumed_id = str(getattr(resumed, "trace_id", ""))

    await save_reading(
        user_id=user_id,
        spread="past_present_future",
        cards=cards_text,
        interpretation=interpretation,
        paid=1,
        execution_id=resumed_id or None,
        trace_hash=trace_hash,
    )

    msg = f"🔮 **Оплата подтверждена! Полный расклад**\n\n{cards_text}\n\n{interpretation}"
    if len(msg) > 4000:
        await message.answer(msg[:4000])
        await message.answer(msg[4000:], reply_markup=share_kb())
    else:
        await message.answer(msg, reply_markup=share_kb())
