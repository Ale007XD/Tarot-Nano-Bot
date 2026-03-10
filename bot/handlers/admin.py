import os
import asyncio
from datetime import datetime, timedelta
from aiogram import Router, F, Bot
from aiogram.types import Message, FSInputFile, URLInputFile
from aiogram.filters import Command, CommandObject
from bot.config import ADMIN_ID
from bot.database import get_db_connection

router = Router()

# Фильтр для проверки прав админа на уровне роутера
router.message.filter(F.from_user.id == ADMIN_ID)

@router.message(Command("admin"))
async def admin_help(message: Message):
    """Список всех админ-команд"""
    help_text = (
        "⚡️ **Панель управления**\n\n"
        "📈 /stats — Статистика и график продаж\n"
        "📢 /broadcast [текст] — Рассылка всем юзерам\n"
        "🎁 /give [ID] [кол-во] — Выдать бесплатные попытки\n"
        "📂 /getdb — Скачать базу данных tarot.db\n"
        "📜 /getlogs — Скачать логи bot.log\n"
    )
    await message.answer(help_text)

@router.message(Command("stats"))
async def admin_stats(message: Message):
    """Просмотр расширенной статистики с графиком"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Общая статистика
        cursor.execute("SELECT COUNT(*) FROM users")
        total_users = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM readings WHERE is_paid = 1")
        paid_readings = cursor.fetchone()[0]
        total_stars = paid_readings * 69

        # Список последних 5 покупок
        # Предполагаем, что в таблице readings есть user_id, created_at и is_paid
        cursor.execute("""
            SELECT user_id, created_at 
            FROM readings 
            WHERE is_paid = 1 
            ORDER BY created_at DESC 
            LIMIT 5
        """)
        last_sales = cursor.fetchall()

        # Данные для графика (продажи за последние 7 дней)
        cursor.execute("""
            SELECT date(created_at) as day, COUNT(*) 
            FROM readings 
            WHERE is_paid = 1 AND created_at >= date('now', '-7 days')
            GROUP BY day
        """)
        chart_data = dict(cursor.fetchall())

    # Формируем список последних покупок
    sales_list = "\n".join([f"👤 `{s[0]}` — _{s[1]}_" for s in last_sales]) if last_sales else "Покупок пока нет"

    # Подготовка данных для QuickChart (7 последних дней)
    labels = []
    values = []
    for i in range(6, -1, -1):
        day = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
        labels.append(day[5:]) # Берем только MM-DD
        values.append(chart_data.get(day, 0))

    chart_url = (
        f"https://quickchart.io/chart?c={{type:'bar',data:{{labels:{labels},datasets:[{{label:'Sales',data:{values},backgroundColor:'rgba(255,153,0,0.6)'}}]}}}}"
    )

    stats_text = (
        "📊 **Расширенная статистика**\n\n"
        f"👤 Юзеров всего: `{total_users}`\n"
        f"💰 Оплат всего: `{paid_readings}`\n"
        f"⭐️ Выручка: `{total_stars} Stars`\n\n"
        f"🕒 **Последние 5 покупок:**\n{sales_list}"
    )

    await message.answer_photo(
        photo=URLInputFile(chart_url),
        caption=stats_text
    )

@router.message(Command("getdb"))
async def download_db(message: Message):
    if os.path.exists("tarot.db"):
        await message.answer_document(FSInputFile("tarot.db"), caption="📦 Актуальная копия БД")
    else:
        await message.answer("❌ Файл базы данных не найден.")

@router.message(Command("getlogs"))
async def download_logs(message: Message):
    if os.path.exists("bot.log"):
        await message.answer_document(FSInputFile("bot.log"), caption="📜 Логи работы бота")
    else:
        await message.answer("❌ Файл логов (bot.log) не найден.")

@router.message(Command("broadcast"))
async def broadcast(message: Message, command: CommandObject, bot: Bot):
    if not command.args:
        return await message.answer("Ошибка! Введите текст: `/broadcast Текст`")

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT user_id FROM users")
        users = cursor.fetchall()

    count = 0
    await message.answer(f"🚀 Рассылка на {len(users)} чел...")
    for (user_id,) in users:
        try:
            await bot.send_message(user_id, command.args)
            count += 1
            await asyncio.sleep(0.05)
        except Exception:
            pass
    await message.answer(f"✅ Готово. Получили: {count} чел.")

@router.message(Command("give"))
async def give_spreads(message: Message, command: CommandObject):
    if not command.args or len(command.args.split()) < 2:
        return await message.answer("Использование: `/give [ID] [кол-во]`")
    try:
        args = command.args.split()
        target_id, amount = int(args[0]), int(args[1])
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE users SET free_spreads = free_spreads + ? WHERE user_id = ?",
                (amount, target_id)
            )
            conn.commit()
        await message.answer(f"✅ Юзеру `{target_id}` выдано {amount} попыток.")
    except ValueError:
        await message.answer("❌ Ошибка: нужны числа.")

