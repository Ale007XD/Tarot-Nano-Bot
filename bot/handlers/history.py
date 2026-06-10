from __future__ import annotations

from aiogram import Router, types
from aiogram.filters import Command

from bot.database import get_user_readings

router = Router()


@router.message(Command("history"))
async def cmd_history(message: types.Message) -> None:
    if not message.from_user:
        return
    user_id = message.from_user.id
    readings = await get_user_readings(user_id, limit=10)

    if not readings:
        await message.answer(
            "🔮 *Ваша история состояний пуста.*\n\n"
            "Сделайте первый расклад через команду /tarot, "
            "чтобы запустить Reflection Engine!",
            parse_mode="Markdown",
        )
        return

    text = "📜 *Reflection Engine | Таймлайн Истории Состояний:*\n\n"

    for idx, row in enumerate(readings, 1):
        # (0)id (1)spread (2)cards (3)interpretation (4)paid (5)execution_id (6)trace_hash
        spread_name = str(row[1])
        cards_drawn = str(row[2])
        interpretation = str(row[3])
        is_paid = bool(row[4])

        status_marker = "👑 [Paid State]" if is_paid else "🆓 [Free State]"
        short_interpretation = (
            interpretation[:120] + "..." if len(interpretation) > 120 else interpretation
        )

        text += f"{idx}. *Расклад:* {spread_name} | {status_marker}\n"
        text += f"🃏 *Карты:* `{cards_drawn}`\n"
        text += f"🧠 *Рефлексия:* _{short_interpretation}_\n"
        text += "---" if idx < len(readings) else ""
        text += "\n\n"

    await message.answer(text, parse_mode="Markdown")
