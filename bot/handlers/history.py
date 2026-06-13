from __future__ import annotations

from aiogram import Router, types
from aiogram.filters import Command

from bot.database import get_user_readings
from bot.i18n import lang_from_user, t

router = Router()


@router.message(Command("history"))
async def cmd_history(message: types.Message) -> None:
    if not message.from_user:
        return

    lang = lang_from_user(message.from_user)
    user_id = message.from_user.id
    readings = await get_user_readings(user_id, limit=10)

    if not readings:
        await message.answer(t("history_empty", lang), parse_mode="Markdown")
        return

    text = t("history_title", lang)

    for idx, row in enumerate(readings, 1):
        spread_name = str(row[1])
        cards_drawn = str(row[2])
        interpretation = str(row[3])
        is_paid = bool(row[4])

        status_marker = t("history_paid_marker", lang) if is_paid else t("history_free_marker", lang)
        short_interpretation = (
            interpretation[:120] + "..." if len(interpretation) > 120 else interpretation
        )

        text += f"{idx}. *Spread:* {spread_name} | {status_marker}\n"
        text += f"🃏 *Cards:* `{cards_drawn}`\n"
        text += f"🧠 *Reading:* _{short_interpretation}_\n"
        text += "---" if idx < len(readings) else ""
        text += "\n\n"

    await message.answer(text, parse_mode="Markdown")
