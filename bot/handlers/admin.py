"""Административный контур управления и аналитики MVP."""

import asyncio
from datetime import datetime, timedelta
import os

import aiosqlite
from aiogram import Bot, F, Router
from aiogram.filters import Command, CommandObject
from aiogram.types import FSInputFile, Message, URLInputFile

from bot.config import ADMIN_ID
from bot.database import DB_PATH
from bot.observatory.trace_analyzer import TraceAnalyzer

router = Router()

# Фильтр для проверки прав админа на уровне роутера
router.message.filter(F.from_user.id == ADMIN_ID)


@router.message(Command("admin"))
async def admin_help(message: Message) -> None:
    """Список всех админ-команд."""
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
    """Просмотр расширенной статистики рантайма MVP с интеграцией Observatory."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row

        # Общая статистика пользователей
        async with db.execute("SELECT COUNT(*) as total_users FROM users") as cursor:
            row_users = await cursor.fetchone()
        total_users = row_users["total_users"] if row_users else 0

        # Общая статистика оплаченных раскладов (исправление Schema Drift: paid)
        async with db.execute(
            "SELECT COUNT(*) as paid_readings FROM readings WHERE paid = 1"
        ) as cursor:
            row_paid = await cursor.fetchone()
        paid_readings = row_paid["paid_readings"] if row_paid else 0
        total_stars = paid_readings * 69

        # Подключение аналитического слоя Observatory для неблокирующего расчета метрик
        analyzer = TraceAnalyzer(db)
        metrics = await analyzer.calculate_retention_and_conversion()

    # Генерация безопасной структуры меток времени
    labels = []
    values = []
    for i in range(6, -1, -1):
        day = (datetime.now() - timedelta(days=i)).strftime("%m-%d")
        labels.append(day)
        values.append(0)  # Заглушка до развертывания логики повременных сессий

    chart_url = (
        f"https://quickchart.io/chart?c={{type:'bar',data:{{labels:{labels},"
        f"datasets:[{{label:'Sales',data:{values},backgroundColor:'rgba(255,153,0,0.6)'}}]}}}}"
    )

    stats_text = (
        "📊 **Расширенная статистика рантайма**\n\n"
        f"👤 Юзеров всего: `{total_users}`\n"
        f"💰 Оплат всего: `{paid_readings}`\n"
        f"⭐️ Выручка: `{total_stars} Stars`\n"
        f"📈 Конверсия (CR): `{metrics.conversion_rate * 100:.2f}%`\n"
        f"🔄 Активные сессии (Free): `{metrics.state_distribution.get('state_free_active', 0)}`\n"
        f"🔒 Завершенные сессии (Paid): `{metrics.state_distribution.get('state_paid_terminal', 0)}`\n"
    )

    try:
        await message.answer_photo(
            photo=URLInputFile(chart_url), caption=stats_text, parse_mode="Markdown"
        )
    except Exception:
        await message.answer(stats_text, parse_mode="Markdown")


@router.message(Command("getdb"))
async def download_db(message: Message) -> None:
    """Скачивание актуальной копии базы данных СУБД."""
    if os.path.exists(DB_PATH):
        await message.answer_document(
            FSInputFile(DB_PATH), caption="📦 Актуальная копия БД"
        )
    else:
        await message.answer("❌ Файл базы данных не найден.")


@router.message(Command("getlogs"))
async def download_logs(message: Message) -> None:
    """Скачивание логов работы бота."""
    if os.path.exists("bot.log"):
        await message.answer_document(
            FSInputFile("bot.log"), caption="📜 Логи работы бота"
        )
    else:
        await message.answer("❌ Файл логов (bot.log) не найден.")


@router.message(Command("broadcast"))
async def broadcast(message: Message, command: CommandObject, bot: Bot) -> None:
    """Широковещательная неблокирующая рассылка по цепочкам сессий."""
    if not command.args:
        await message.answer("Ошибка! Введите текст: `/broadcast Текст`")
        return

    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT user_id FROM users") as cursor:
            rows = await cursor.fetchall()

    count = 0
    await message.answer(f"🚀 Рассылка на {len(rows)} чел...")
    for row in rows:
        user_id = row["user_id"]
        try:
            await bot.send_message(user_id, command.args)
            count += 1
            await asyncio.sleep(0.05)
        except Exception:
            pass
    await message.answer(f"✅ Готово. Получили: {count} чел.")


@router.message(Command("give"))
async def give_spreads(message: Message, command: CommandObject) -> None:
    """Выдача попыток инкремента переходов пользователя."""
    if not command.args or len(command.args.split()) < 2:
        await message.answer("Использование: `/give [ID] [кол-во]`")
        return
    try:
        args = command.args.split()
        target_id, amount = int(args[0]), int(args[1])
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute(
                "UPDATE users SET free_spreads = free_spreads + ? WHERE user_id = ?",
                (amount, target_id),
            )
            await db.commit()
        await message.answer(f"✅ Юзеру `{target_id}` выдано {amount} попыток.")
    except ValueError:
        await message.answer("❌ Ошибка: нужны числа.")
