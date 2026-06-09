# bot/handlers/history.py
from aiogram import Router, types
from aiogram.filters import Command
from bot.database import get_user_readings

router = Router()

@router.message(Command("history"))
async def cmd_history(message: types.Message):
    user_id = message.from_user.id
    readings = await get_user_readings(user_id, limit=10)
    
    if not readings:
        await message.answer(
            "🔮 *Ваша история состояний пуста.*\n\n"
            "Сделайте первый расклад через команду /tarot, чтобы запустить Reflection Engine!",
            parse_mode="Markdown"
        )
        return
        
    text = "📜 *Reflection Engine | Таймлайн Истории Состояний:*\n\n"
    
    for idx, row in enumerate(readings, 1):
        # Структура кортежа: id (0), user_id (1), spread (2), cards (3), interpretation (4), paid (5)
        spread_name = row[2]
        cards_drawn = row[3]
        interpretation = row[4]
        is_paid = row[5]
        
        status_marker = "👑 [Paid State]" if is_paid else "🆓 [Free State]"
        # Обрезаем длинный вывод интерпретации для краткости отображения в листинге
        short_interpretation = interpretation[:120] + "..." if len(interpretation) > 120 else interpretation
        
        text += f"{idx}. *Расклад:* {spread_name} | {status_marker}\n"
        text += f"🃏 *Карты:* `{cards_drawn}`\n"
        text += f"🧠 *Рефлексия:* _{short_interpretation}_\n"
        text += "---" if idx < len(readings) else ""
        text += "\n\n"
        
    await message.answer(text, parse_mode="Markdown")
  
