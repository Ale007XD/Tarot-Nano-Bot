"""Temporary /test_payment command — DEV ONLY, remove before prod launch."""
from __future__ import annotations

import json
import logging
from unittest.mock import MagicMock

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from bot.config import LLM_MODEL
from bot.database import delete_pending_execution, get_pending_execution, save_reading
from bot.keyboards import share_kb
from bot.vm_runner import get_trace_hash, run_full_reading

router = Router()


@router.message(Command("test_payment"))
async def test_payment(message: Message) -> None:
    """Simulate successful Stars payment for dev testing."""
    if not message.from_user:
        return

    user_id = message.from_user.id
    await message.answer("🔧 Симуляция оплаты Stars...")

    await delete_pending_execution(user_id)

    try:
        trace = await run_full_reading(
            user_id=user_id,
            free_spreads=1,
            model=LLM_MODEL,
        )
    except Exception as e:
        logging.error(f"[test_payment] run_full_reading failed: {e}")
        await message.answer(f"❌ Ошибка: {e}")
        return

    cards_text = ""
    interpretation = ""
    for step in getattr(trace, "steps", []):
        step_id = getattr(step, "step_id", "") or getattr(step, "id", "")
        out = getattr(step, "output", None)
        if step_id == "draw_spread" and isinstance(out, dict):
            cards_text = str(out.get("cards_text", ""))
        elif step_id == "llm_interpret" and isinstance(out, str):
            interpretation = out

    trace_hash = get_trace_hash(trace)
    trace_id = str(getattr(trace, "trace_id", ""))

    await save_reading(
        user_id=user_id,
        spread="past_present_future",
        cards=cards_text,
        interpretation=interpretation,
        paid=1,
        execution_id=trace_id or None,
        trace_hash=trace_hash,
    )

    msg = f"🔮 **[TEST] Полный расклад**\n\n{cards_text}\n\n{interpretation}"
    if len(msg) > 4000:
        await message.answer(msg[:4000])
        await message.answer(msg[4000:], reply_markup=share_kb())
    else:
        await message.answer(msg, reply_markup=share_kb())
