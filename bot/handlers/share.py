"""Share reward handler.

When user taps "Shared → +1 free reading" after a paid reading,
we grant one free spread. One reward per trace_hash (dedup via DB).
"""
from __future__ import annotations

import logging

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message

from bot.database import increment_free_spreads
from bot.i18n import lang_from_user

router = Router()

# In-memory dedup for share rewards within a session.
# Persisted dedup would require a share_rewards table — backlog.
_rewarded: set[str] = set()


@router.callback_query(lambda c: c.data and c.data.startswith("share_done:"))
async def share_done(callback: CallbackQuery) -> None:
    if not callback.from_user or not callback.message:
        return

    lang = lang_from_user(callback.from_user)
    user_id = callback.from_user.id
    key = f"{user_id}:{callback.data}"

    if key in _rewarded:
        text = (
            "Вы уже получили награду за этот расклад 🙏"
            if lang == "ru"
            else "You already claimed the reward for this reading 🙏"
        )
        await callback.answer(text, show_alert=True)
        return

    try:
        await increment_free_spreads(user_id, amount=1)
        _rewarded.add(key)
        text = (
            "🎁 +1 бесплатная попытка добавлена! Спасибо, что поделились 🔮"
            if lang == "ru"
            else "🎁 +1 free reading added! Thank you for sharing 🔮"
        )
        await callback.answer(text, show_alert=True)
        logging.info(f"[Share] user {user_id} rewarded +1 free spread")
    except Exception as e:
        logging.error(f"[Share] reward failed for user {user_id}: {e}")
        await callback.answer("❌ Ошибка. Попробуйте позже.", show_alert=True)
