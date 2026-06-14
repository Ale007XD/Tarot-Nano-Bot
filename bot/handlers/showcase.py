"""User-facing nano-vm showcase commands.

/my_traces — list the user's readings with execution_id + trace_hash
/verify <hash> — prove a reading is authentic via trace_hash lookup
"""

from __future__ import annotations

from aiogram import Router
from aiogram.filters import Command, CommandObject
from aiogram.types import Message

from bot.database import get_reading_by_trace_hash, get_user_readings
from bot.i18n import lang_from_user, t

router = Router()


@router.message(Command("my_traces"))
async def cmd_my_traces(message: Message) -> None:
    if not message.from_user:
        return

    lang = lang_from_user(message.from_user)
    user_id = message.from_user.id
    readings = await get_user_readings(user_id, limit=10)

    if not readings:
        await message.answer(t("traces_empty", lang), parse_mode="Markdown")
        return

    lines = [t("traces_title", lang)]
    for idx, row in enumerate(readings, 1):
        spread = str(row[1])
        is_paid = bool(row[4])
        execution_id = str(row[5]) if row[5] else None
        trace_hash = str(row[6]) if row[6] else None
        ts = str(row[7]) if len(row) > 7 else ""

        paid_mark = "👑" if is_paid else "🆓"
        hash_line = f"`{trace_hash[:16]}…`" if trace_hash else t("traces_no_hash", lang)
        exec_line = f"`{execution_id[:8]}…`" if execution_id else "—"

        lines.append(
            f"{idx}. {paid_mark} *{spread}*\n"
            f"   🆔 exec: {exec_line}\n"
            f"   🔒 hash: {hash_line}\n"
            f"   🕐 {ts[:16]}"
        )

    lines.append(t("traces_verify_hint", lang))
    await message.answer("\n\n".join(lines), parse_mode="Markdown")


@router.message(Command("verify"))
async def cmd_verify(message: Message, command: CommandObject) -> None:
    if not message.from_user:
        return

    lang = lang_from_user(message.from_user)

    if not command.args:
        await message.answer(t("verify_usage", lang), parse_mode="Markdown")
        return

    trace_hash = command.args.strip()
    if len(trace_hash) < 8:
        await message.answer(t("verify_invalid_hash", lang), parse_mode="Markdown")
        return

    row = await get_reading_by_trace_hash(trace_hash)
    if row is None:
        await message.answer(t("verify_not_found", lang), parse_mode="Markdown")
        return

    user_id, spread, created_at, found_hash = row
    is_requester = user_id == message.from_user.id
    owner_note = t("verify_yours", lang) if is_requester else t("verify_other", lang)

    result = (
        f"{t('verify_ok', lang)}\n\n"
        f"🃏 *Spread:* {spread}\n"
        f"📅 *Created:* {created_at[:16]}\n"
        f"🔒 *Hash:* `{found_hash}`\n\n"
        f"{owner_note}"
    )
    await message.answer(result, parse_mode="Markdown")
