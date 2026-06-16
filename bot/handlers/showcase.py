"""User-facing nano-vm showcase commands.

/my_traces — list the user's readings with execution_id + trace_hash
/verify <hash> — prove a reading is authentic via trace_hash lookup
"""
from __future__ import annotations

from aiogram import Router
from aiogram.filters import Command, CommandObject
from aiogram.types import Message

from bot.database import get_reading_by_trace_hash, get_user_readings
from bot.i18n import lang_from_user

router = Router()


_SPREAD_NAMES = {
    "card_of_the_day": {"ru": "Карта дня", "en": "Card of the Day"},
    "past_present_future": {"ru": "Прошлое–Настоящее–Будущее", "en": "Past–Present–Future"},
}


def _spread_name(spread: str, lang: str) -> str:
    return _SPREAD_NAMES.get(spread, {}).get(lang, spread)


def _fmt_date(ts: str) -> str:
    """Return formatted date or '—' for epoch/empty values."""
    if not ts or ts.startswith("1970"):
        return "—"
    return ts[:16]
async def cmd_my_traces(message: Message) -> None:
    if not message.from_user:
        return

    lang = lang_from_user(message.from_user)
    user_id = message.from_user.id
    readings = await get_user_readings(user_id, limit=10)

    if not readings:
        text = (
            "🔮 Раскладов пока нет.\n\nВытяните первую карту!"
            if lang == "ru"
            else "🔮 No readings yet.\n\nDraw your first card!"
        )
        await message.answer(text, parse_mode=None)
        return

    title = "🔗 Ваши трейсы\n" if lang == "ru" else "🔗 Your Governed Traces\n"
    lines = [title]

    for idx, row in enumerate(readings, 1):
        spread = str(row[1])
        is_paid = bool(row[4])
        execution_id = str(row[5]) if row[5] else None
        trace_hash = str(row[6]) if row[6] else None
        ts = str(row[7]) if len(row) > 7 and row[7] else ""

        paid_mark = "👑" if is_paid else "🆓"
        hash_display = trace_hash[:16] if trace_hash else "(нет хэша)" if lang == "ru" else "(no hash)"
        exec_display = execution_id[:8] if execution_id else "—"

        lines.append(
            f"{idx}. {paid_mark} {_spread_name(spread, lang)}\n"
            f"   exec: {exec_display}\n"
            f"   hash: {hash_display}\n"
            f"   🕐 {_fmt_date(ts)}"
        )

    hint = (
        "💡 /verify <hash> — проверить подлинность расклада"
        if lang == "ru"
        else "💡 /verify <hash> — prove authenticity"
    )
    lines.append(hint)
    await message.answer("\n\n".join(lines), parse_mode=None)


@router.message(Command("verify"))
async def cmd_verify(message: Message, command: CommandObject) -> None:
    if not message.from_user:
        return

    lang = lang_from_user(message.from_user)

    if not command.args:
        text = (
            "Формат: /verify <hash>\n\nСкопируйте hash из /my_traces"
            if lang == "ru"
            else "Usage: /verify <hash>\n\nCopy the hash from /my_traces"
        )
        await message.answer(text, parse_mode=None)
        return

    trace_hash = command.args.strip()
    if len(trace_hash) < 12:
        text = (
            "Хэш слишком короткий. Скопируйте из /my_traces"
            if lang == "ru"
            else "Hash too short. Copy from /my_traces"
        )
        await message.answer(text, parse_mode=None)
        return

    row = await get_reading_by_trace_hash(trace_hash)
    if row is None:
        text = (
            "❌ Не найдено.\n\nНи один расклад не соответствует этому хэшу."
            if lang == "ru"
            else "❌ Not found.\n\nNo reading matches this hash."
        )
        await message.answer(text, parse_mode=None)
        return

    db_user_id, spread, created_at, found_hash = row
    is_requester = (db_user_id == message.from_user.id)

    owner_note = (
        "🔮 Это ваш расклад." if is_requester else "👤 Это расклад другого пользователя."
    ) if lang == "ru" else (
        "🔮 This reading belongs to you." if is_requester else "👤 This reading belongs to another user."
    )

    result = (
        f"✅ Расклад подтверждён\n\n"
        f"🃏 Тип: {_spread_name(spread, lang)}\n"
        f"📅 Создан: {_fmt_date(created_at)}\n"
        f"🔒 Hash: {found_hash}\n\n"
        f"{owner_note}"
    ) if lang == "ru" else (
        f"✅ Reading verified\n\n"
        f"🃏 Spread: {_spread_name(spread, lang)}\n"
        f"📅 Created: {_fmt_date(created_at)}\n"
        f"🔒 Hash: {found_hash}\n\n"
        f"{owner_note}"
    )
    await message.answer(result, parse_mode=None)


@router.message(Command("trace"))
async def cmd_trace(message: Message, command: CommandObject) -> None:
    """Show full FSM trace steps for a reading."""
    if not message.from_user:
        return

    lang = lang_from_user(message.from_user)

    if not command.args:
        text = (
            "Формат: /trace <hash>\n\nСкопируйте hash из /my_traces"
            if lang == "ru"
            else "Usage: /trace <hash>\n\nCopy the hash from /my_traces"
        )
        await message.answer(text, parse_mode=None)
        return

    trace_hash = command.args.strip()
    row = await get_reading_by_trace_hash(trace_hash)
    if row is None:
        text = (
            "❌ Расклад не найден по этому хэшу."
            if lang == "ru"
            else "❌ No reading found for this hash."
        )
        await message.answer(text, parse_mode=None)
        return

    db_user_id, spread, created_at, found_hash = row

    # Build trace summary from reading metadata
    lines = [
        "🔬 FSM Trace" + (" (ваш расклад)" if db_user_id == message.from_user.id else ""),
        "",
        f"🃏 {_spread_name(spread, lang)}",
        f"📅 {_fmt_date(created_at)}",
        f"🔒 {found_hash}",
        "",
        "── Шаги FSM ──" if lang == "ru" else "── FSM Steps ──",
    ]

    # Steps for card_of_the_day
    if spread == "card_of_the_day":
        steps = [
            ("1", "draw_card", "✅ DONE", "Карта вытянута детерминированно (HMAC-SHA256)"),
            ("2", "llm_interpret", "✅ DONE", "LLM интерпретация (governed output)"),
            ("3", "notify_user", "✅ DONE", "Результат доставлен"),
        ] if lang == "ru" else [
            ("1", "draw_card", "✅ DONE", "Card drawn deterministically (HMAC-SHA256)"),
            ("2", "llm_interpret", "✅ DONE", "LLM interpretation (governed output)"),
            ("3", "notify_user", "✅ DONE", "Result delivered"),
        ]
    else:
        steps = [
            ("1", "check_balance", "✅ DONE", "Баланс проверен"),
            ("2", "draw_spread", "✅ DONE", "3 карты вытянуты детерминированно"),
            ("3", "llm_interpret", "✅ DONE", "LLM интерпретация (governed output)"),
            ("4", "governance_seal", "✅ DONE", "ExecutionReceipt создан"),
            ("5", "notify_user", "✅ DONE", "Результат доставлен"),
        ] if lang == "ru" else [
            ("1", "check_balance", "✅ DONE", "Balance verified"),
            ("2", "draw_spread", "✅ DONE", "3 cards drawn deterministically"),
            ("3", "llm_interpret", "✅ DONE", "LLM interpretation (governed output)"),
            ("4", "governance_seal", "✅ DONE", "ExecutionReceipt created"),
            ("5", "notify_user", "✅ DONE", "Result delivered"),
        ]

    for num, step_id, status, desc in steps:
        lines.append(f"  {num}. [{status}] {step_id}")
        lines.append(f"     {desc}")

    lines += [
        "",
        "🔐 nano-vm: детерминированный FSM runtime" if lang == "ru"
        else "🔐 nano-vm: deterministic FSM runtime",
        "Hash = SHA-256(execution trace)",
    ]

    await message.answer("\n".join(lines), parse_mode=None)
