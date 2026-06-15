"""Tarot handler — Card of the Day and Full Reading via FSM vm_runner."""
from __future__ import annotations

import logging

from aiogram import Router
from aiogram.types import CallbackQuery

from bot.config import LLM_MODEL, TAROT_SALT
from bot.database import (
    delete_pending_execution,
    get_user,
    save_pending_execution,
    save_reading,
)
from bot.i18n import lang_from_user, t
from bot.keyboards import paywall_kb, share_kb
from bot.vm_runner import get_trace_hash, run_card_of_day, run_full_reading

import datetime

router = Router()

_SUSPENDED = "SUSPENDED"
_SUCCESS = "SUCCESS"


def _extract_card_of_day(trace: object) -> tuple[str, str] | None:
    try:
        steps = getattr(trace, "steps", [])
        card_name = ""
        interpretation = ""
        for step in steps:
            step_id = getattr(step, "step_id", "") or getattr(step, "id", "")
            out = getattr(step, "output", None)
            if step_id == "draw_card" and isinstance(out, dict):
                card_name = str(out.get("card_name", ""))
            elif step_id == "llm_interpret" and isinstance(out, str):
                interpretation = out
            elif step_id == "llm_interpret" and isinstance(out, dict):
                interpretation = str(out.get("output", out.get("text", "")))
        if card_name:
            return card_name, interpretation
        return None
    except Exception:
        return None


def _extract_full_reading(trace: object) -> tuple[str, str] | None:
    try:
        steps = getattr(trace, "steps", [])
        cards_text = ""
        interpretation = ""
        for step in steps:
            step_id = getattr(step, "step_id", "") or getattr(step, "id", "")
            out = getattr(step, "output", None)
            if step_id == "draw_spread" and isinstance(out, dict):
                cards_text = str(out.get("cards_text", ""))
            elif step_id == "llm_interpret" and isinstance(out, str):
                interpretation = out
            elif step_id == "llm_interpret" and isinstance(out, dict):
                interpretation = str(out.get("output", out.get("text", "")))
        if cards_text or interpretation:
            return cards_text, interpretation
        return None
    except Exception:
        return None


@router.callback_query(lambda c: c.data == "draw")
async def draw(callback: CallbackQuery) -> None:
    if not callback.from_user or not callback.message:
        return

    lang = lang_from_user(callback.from_user)
    user_id = callback.from_user.id
    execution_date = datetime.date.today().isoformat()

    try:
        trace = await run_card_of_day(
            user_id=user_id,
            execution_date=execution_date,
            salt=TAROT_SALT,
            model=LLM_MODEL,
            language=lang,
        )
    except Exception as e:
        logging.error(f"[tarot] run_card_of_day failed: {e}")
        await callback.message.answer(t("err_card_failed", lang))
        await callback.answer()
        return

    status = str(getattr(trace, "status", "")).upper()
    if not status.endswith(_SUCCESS):
        await callback.message.answer(t("err_card_unavailable", lang))
        await callback.answer()
        return

    result = _extract_card_of_day(trace)
    if result is None:
        await callback.message.answer(t("err_card_extract", lang))
        await callback.answer()
        return

    card_name, interpretation = result
    trace_hash = get_trace_hash(trace)
    execution_id = str(getattr(trace, "trace_id", ""))

    await save_reading(
        user_id=user_id,
        spread="card_of_the_day",
        cards=card_name,
        interpretation=interpretation,
        paid=0,
        execution_id=execution_id or None,
        trace_hash=trace_hash,
    )

    text = (
        f"{t('card_of_day_title', lang)}\n\n"
        f"**{card_name}**\n\n"
        f"{interpretation}\n\n"
        f"{t('card_of_day_upsell', lang)}"
    )
    await callback.message.answer(text, reply_markup=paywall_kb(lang))
    await callback.answer()


@router.callback_query(lambda c: c.data == "buy")
async def full_reading(callback: CallbackQuery) -> None:
    if not callback.from_user or not callback.message or not callback.bot:
        return

    lang = lang_from_user(callback.from_user)
    user_id = callback.from_user.id
    user = await get_user(user_id)
    free_spreads = int(user[3]) if user else 0

    try:
        trace = await run_full_reading(
            user_id=user_id,
            free_spreads=free_spreads,
            model=LLM_MODEL,
            language=lang,
        )
    except Exception as e:
        logging.error(f"[tarot] run_full_reading failed: {e}")
        await callback.message.answer(t("err_reading_failed", lang))
        await callback.answer()
        return

    status = str(getattr(trace, "status", "")).upper()

    _payment_required = False
    for _s in getattr(trace, "steps", []):
        _out = getattr(_s, "output", None)
        if isinstance(_out, dict) and _out.get("action") == "REQUIRES_ACTION":
            _payment_required = True
            break

    if _SUSPENDED in status or _payment_required:
        execution_id = str(getattr(trace, "trace_id", ""))
        await save_pending_execution(user_id, execution_id, trace.model_dump_json())
        from bot.services.payment_service import create_reading_invoice
        await create_reading_invoice(callback.bot, user_id, execution_id=execution_id, lang=lang)

    elif status.endswith(_SUCCESS):
        result = _extract_full_reading(trace)
        if result is None:
            await callback.message.answer(t("err_reading_extract", lang))
            await callback.answer()
            return

        cards_text, interpretation = result
        trace_hash = get_trace_hash(trace)
        execution_id = str(getattr(trace, "trace_id", ""))

        await save_reading(
            user_id=user_id,
            spread="past_present_future",
            cards=cards_text,
            interpretation=interpretation,
            paid=0,
            execution_id=execution_id or None,
            trace_hash=trace_hash,
        )

        msg = f"{t('full_reading_title', lang)}\n\n{cards_text}\n\n{interpretation}"
        if len(msg) > 4000:
            await callback.message.answer(msg[:4000])
            await callback.message.answer(msg[4000:], reply_markup=share_kb(lang))
        else:
            await callback.message.answer(msg, reply_markup=share_kb(lang))
    else:
        logging.error(f"[tarot] full_reading unexpected status={status}")
        await callback.message.answer(t("err_reading_unavailable", lang))

    await callback.answer()
