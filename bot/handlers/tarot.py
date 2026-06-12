"""Tarot handler — Card of the Day via FSM vm_runner."""

from __future__ import annotations

import json
import logging

from aiogram import Router
from aiogram.types import CallbackQuery

from bot.config import LLM_MODEL, TAROT_SALT
from bot.database import (
    delete_pending_execution,
    get_pending_execution,
    get_user,
    save_pending_execution,
    save_reading,
)
from bot.keyboards import paywall_kb, share_kb
from bot.vm_runner import get_trace_hash, run_card_of_day, run_full_reading

import datetime

router = Router()

_SUSPENDED = "SUSPENDED"
_SUCCESS = "SUCCESS"

TAROT_POOL: list[str] = [
    "The Fool", "The Magician", "The High Priestess", "The Empress",
    "The Emperor", "The Hierophant", "The Lovers", "The Chariot",
    "Strength", "The Hermit", "Wheel of Fortune", "Justice",
    "The Hanged Man", "Death", "Temperance", "The Devil",
    "The Tower", "The Star", "The Moon", "The Sun", "Judgement", "The World",
] + [f"Minor Arcana Card #{i}" for i in range(22, 78)]


def _extract_card_of_day(trace: object) -> tuple[str, str] | None:
    """Return (card_name, interpretation) from a successful card_of_day trace."""
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
    """Return (cards_text, interpretation) from a successful full_reading trace."""
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

    user_id = callback.from_user.id
    execution_date = datetime.date.today().isoformat()

    try:
        trace = await run_card_of_day(
            user_id=user_id,
            execution_date=execution_date,
            salt=TAROT_SALT,
            model=LLM_MODEL,
        )
    except Exception as e:
        logging.error(f"[tarot] run_card_of_day failed: {e}")
        await callback.message.answer("⚠️ Ошибка при вытягивании карты. Попробуйте позже.")
        await callback.answer()
        return

    status = str(getattr(trace, "status", "")).upper()
    if not status.endswith(_SUCCESS):
        await callback.message.answer("⚠️ Карта дня недоступна. Попробуйте позже.")
        await callback.answer()
        return

    result = _extract_card_of_day(trace)
    if result is None:
        await callback.message.answer("⚠️ Не удалось извлечь карту из трейса.")
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
        f"🔮 **Вы вытянули карту дня**\n\n"
        f"**{card_name}**\n\n"
        f"{interpretation}\n\n"
        f"Это только **часть** послания Вселенной.\n\n"
        f"Чтобы узнать **полную картину** (прошлое • настоящее • будущее"
        f" + глубокая интерпретация) — нажмите кнопку ниже."
    )
    await callback.message.answer(text, reply_markup=paywall_kb())
    await callback.answer()


@router.callback_query(lambda c: c.data == "buy")
async def full_reading(callback: CallbackQuery) -> None:
    if not callback.from_user or not callback.message or not callback.bot:
        return

    user_id = callback.from_user.id
    user = await get_user(user_id)
    free_spreads = int(user[3]) if user else 0

    try:
        trace = await run_full_reading(
            user_id=user_id,
            free_spreads=free_spreads,
            model=LLM_MODEL,
        )
    except Exception as e:
        logging.error(f"[tarot] run_full_reading failed: {e}")
        await callback.message.answer("⚠️ Ошибка при запуске расклада. Попробуйте позже.")
        await callback.answer()
        return

    status = str(getattr(trace, "status", "")).upper()

    if _SUSPENDED in status:
        # FSM paused at payment gate — persist trace, send invoice
        try:
            trace_json = trace.model_dump_json()
        except Exception:
            trace_json = json.dumps({"trace_id": str(getattr(trace, "trace_id", ""))})

        execution_id = str(getattr(trace, "trace_id", ""))
        await save_pending_execution(user_id, execution_id, trace_json)

        from bot.services.payment_service import create_reading_invoice  # local import avoids cycle
        await create_reading_invoice(callback.bot, user_id, execution_id=execution_id)

    elif status.endswith(_SUCCESS):
        result = _extract_full_reading(trace)
        if result is None:
            await callback.message.answer("⚠️ Не удалось извлечь расклад из трейса.")
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

        msg = f"🔮 **Полный расклад**\n\n{cards_text}\n\n{interpretation}"
        # Split if too long for Telegram 4096 char limit
        if len(msg) > 4000:
            await callback.message.answer(msg[:4000])
            await callback.message.answer(msg[4000:], reply_markup=share_kb())
        else:
            await callback.message.answer(msg, reply_markup=share_kb())
    else:
        logging.error(f"[tarot] full_reading unexpected status={status}")
        await callback.message.answer("⚠️ Расклад недоступен. Попробуйте позже.")

    await callback.answer()
        
