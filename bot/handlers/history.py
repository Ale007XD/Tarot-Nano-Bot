from __future__ import annotations

from aiogram import Router, types
from aiogram.filters import Command

from bot.database import get_user_readings
from bot.i18n import lang_from_user, t

router = Router()

_SPREAD_NAMES: dict[str, dict[str, str]] = {
    "card_of_the_day": {"ru": "Карта дня", "en": "Card of the Day"},
    "past_present_future": {"ru": "Прошлое–Настоящее–Будущее", "en": "Past–Present–Future"},
}


def _spread_name(spread: str, lang: str) -> str:
    return _SPREAD_NAMES.get(spread, {}).get(lang, spread)


@router.message(Command("history"))
async def cmd_history(message: types.Message) -> None:
    if not message.from_user:
        return

    lang = lang_from_user(message.from_user)
    user_id = message.from_user.id
    readings = await get_user_readings(user_id, limit=10)

    if not readings:
        await message.answer(t("history_empty", lang), parse_mode=None)
        return

    title = "📜 История раскладов\n\n" if lang == "ru" else "📜 Reading History\n\n"
    parts = [title]

    for idx, row in enumerate(readings, 1):
        spread = str(row[1])
        cards_drawn = str(row[2])
        interpretation = str(row[3])
        is_paid = bool(row[4])
        trace_hash = str(row[6]) if len(row) > 6 and row[6] else None

        status = t("history_paid_marker", lang) if is_paid else t("history_free_marker", lang)
        short = interpretation[:120] + "..." if len(interpretation) > 120 else interpretation
        hash_line = f"   hash: {trace_hash[:16]}" if trace_hash else ""

        entry = f"{idx}. {_spread_name(spread, lang)} | {status}\n   {cards_drawn}\n   {short}\n"
        if hash_line:
            entry += hash_line + "\n"

        parts.append(entry)

    await message.answer("\n".join(parts), parse_mode=None)
