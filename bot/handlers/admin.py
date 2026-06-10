"""Административный контур управления и аналитики MVP."""

from __future__ import annotations

import asyncio
from datetime import datetime, timedelta

import aiosqlite
from aiogram import F, Router
from aiogram.filters import Command, CommandObject
from aiogram.types import FSInputFile, Message

from bot.config import ADMIN_ID
from bot.database import DB_PATH
from bot.observatory.trace_analyzer import TraceAnalyzer

router = Router()
router.message.filter(F.from_user.id == ADMIN_ID)


@router.message(Command("admin"))
async def admin_help(message: Message) -> None:
    help_text = (
        "⚡️ **Панель управления**\n\n"
        "📈 /stats — Статистика рантайма\n"
        "📢 /broadcast [текст] — Рассылка всем юзерам\n"
        "🎁 /give [ID] [кол-во] — Выдать бесплатные попытки\n"
        "📂 /getdb — Скачать базу данных\n"
        "📜 /getlogs — Скачать логи bot.log\n"
    )
    await message.answer(help_text, parse_mode="Markdown")


@router.message(Command("stats"))
async def admin_stats(message: Message) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row

        async with db.execute("SELECT COUNT(*) as total_users FROM users") as cursor:
            row_users = await cursor.fetchone()
        total_users = row_users["total_users"] if row_users else 0

        async with db.execute(
            "SELECT COUNT(*) as paid_readings FROM readings WHERE paid = 1"
        ) as cursor:
            row_paid = await cursor.fetchone()
        paid_readings = row_paid["paid_readings"] if row_paid else 0
        total_stars = paid_readings * 69

        analyzer = TraceAnalyzer(db)
        metrics = await analyzer.calculate_retention_and_conversion()

    labels = []
    values: list[int] = []
    for i in range(6, -1, -1):
        day = (datetime.now() - timedelta(days=i)).strftime("%m-%d")
        labels.append(day)
        values.append(0)

    chart_url = (
        f"https://quickchart.io/chart?c={{type:'bar',data:{{labels:{labels},"
        f"datasets:[{{label:'Sales',data:{values},"
        f"backgroundColor:'rgba(255,153,0,0.6)'}}]}}}}"
    )

    free_active = metrics.state_distribution.get("state_free_active", 0)
    paid_terminal = metrics.state_distribution.get("state_paid_terminal", 0)

    stats_text = (
        "📊 **Расширенная статистика рантайма**\n\n"
        f"👤 Юзеров всего: `{total_users}`\n"
        f"💰 Оплат всего: `{paid_readings}`\n"
        f"⭐️ Выручка: `{total_stars} Stars`\n"
        f"📈 Конверсия (CR): `{metrics.conversion_rate * 100:.2f}%`\n"
        f"🔄 Активные сессии (Free): `{free_active}`\n"
        f"🔒 Завершенные сессии (Paid): `{paid_terminal}`\n"
    )

    try:
        await message.answer_photo(
            photo=chart_url,
            caption=stats_text,
            parse_mode="Markdown",
        )
    except Exception:
        await message.answer(stats_text, parse_mode="Markdown")


@router.message(Command("broadcast"))
async def admin_broadcast(message: Message, command: CommandObject) -> None:
    if not command.args:
        await message.answer("❗ Укажите текст: /broadcast <текст>")
        return

    text = command.args
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT user_id FROM users") as cursor:
            rows = await cursor.fetchall()

    if not message.bot:
        return

    rows_list = list(rows)
    sent = 0
    for row in rows_list:
        try:
            await message.bot.send_message(int(row[0]), text)
            sent += 1
            await asyncio.sleep(0.05)
        except Exception:
            pass

    await message.answer(f"✅ Отправлено {sent} / {len(rows_list)} пользователям.")


@router.message(Command("give"))
async def admin_give(message: Message, command: CommandObject) -> None:
    if not command.args:
        await message.answer("❗ Укажите: /give <user_id> <кол-во>")
        return

    parts = command.args.split()
    if len(parts) != 2:
        await message.answer("❗ Формат: /give <user_id> <кол-во>")
        return

    try:
        target_id = int(parts[0])
        amount = int(parts[1])
    except ValueError:
        await message.answer("❗ user_id и кол-во должны быть числами.")
        return

    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE users SET free_spreads = free_spreads + ? WHERE user_id = ?",
            (amount, target_id),
        )
        await db.commit()

    await message.answer(f"✅ Пользователю {target_id} выдано {amount} бесплатных раскладов.")


@router.message(Command("getdb"))
async def admin_getdb(message: Message) -> None:
    try:
        await message.answer_document(FSInputFile(DB_PATH), caption="📂 База данных")
    except Exception as e:
        await message.answer(f"❌ Ошибка: {e}")


@router.message(Command("getlogs"))
async def admin_getlogs(message: Message) -> None:
    try:
        await message.answer_document(FSInputFile("bot.log"), caption="📜 Логи")
    except Exception as e:
        await message.answer(f"❌ Ошибка: {e}")


# Alias for backward compatibility with tests
give_spreads = admin_give
