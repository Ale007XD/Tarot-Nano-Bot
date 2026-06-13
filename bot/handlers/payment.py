"""Payment handler — Telegram Stars pre-checkout + successful_payment → FSM run."""
from __future__ import annotations

import logging

from aiogram import F, Router
from aiogram.types import Message, PreCheckoutQuery
from pydantic import BaseModel, Field

from bot.config import LLM_MODEL
from bot.database import delete_pending_execution, get_pending_execution, save_reading
from bot.i18n import lang_from_user, t
from bot.keyboards import share_kb
from bot.vm_runner import get_trace_hash, run_full_reading

router = Router(name="payment_router")


class OrderPayload(BaseModel):
    user_id: int
    execution_id: str
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
            error_message="Payment validation error. Please try again.",
        )


@router.message(F.successful_payment)
async def process_successful_payment(message: Message) -> None:
    successful_payment = message.successful_payment
    if not message.from_user or not successful_payment:
        return

    lang = lang_from_user(message.from_user)
    user_id = message.from_user.id

    try:
        payload = OrderPayload.model_validate_json(successful_payment.invoice_payload)
    except Exception as e:
        logging.error(f"[Payment] Payload parse failure: {e}")
        await message.answer(t("err_payment_parse", lang))
        return

    await delete_pending_execution(user_id)

    try:
        resumed = await run_full_reading(
            user_id=user_id,
            free_spreads=1,
            model=LLM_MODEL,
            language=lang,
        )
    except Exception as e:
        logging.error(f"[Payment] run_full_reading after payment failed: {e}")
        await message.answer(t("err_payment_resume", lang))
        return

    status = str(getattr(resumed, "status", "")).upper()
    if not status.endswith("SUCCESS"):
        logging.error(f"[Payment] run ended with status={status}")
        await message.answer(t("err_payment_incomplete", lang))
        return

    cards_text = ""
    interpretation = ""
    try:
        steps = getattr(resumed, "steps", [])
        for step in steps:
            step_id = getattr(step, "step_id", "") or getattr(step, "id", "")
            out = getattr(step, "output", None)
            if step_id == "draw_spread" and isinstance(out, dict):
                cards_text = str(out.get("cards_text", ""))
            elif step_id == "llm_interpret" and isinstance(out, str):
                interpretation = out
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

    msg = f"{t('full_reading_paid_title', lang)}\n\n{cards_text}\n\n{interpretation}"
    if len(msg) > 4000:
        await message.answer(msg[:4000])
        await message.answer(msg[4000:], reply_markup=share_kb(lang))
    else:
        await message.answer(msg, reply_markup=share_kb(lang))
