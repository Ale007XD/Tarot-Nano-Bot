"""Компонент выполнения детерминированных логических переходов Tarot/Reflection Engine."""

import datetime
import hashlib

from aiogram import Router
from aiogram.types import CallbackQuery
from pydantic import BaseModel, Field

from bot.database import decrement_free_spreads, get_user, save_reading
from bot.keyboards import paywall_kb, share_kb
from bot.services.llm_service import generate_reading
from bot.services.payment_service import create_reading_invoice
from bot.services.tarot_engine import draw_spread

try:
    from bot.config import SALT
except ImportError:
    SALT = "NANO_VM_CRYPTO_DETERMINISTIC_SECURE_SALT_2026"

router = Router()

# Кэш частичных карт сессий
partial_cards = {}

# Детерминированный пул из 78 состояний (Арканов) для маппинга хэш-инварианта
TAROT_POOL: list[str] = [
    "The Fool",
    "The Magician",
    "The High Priestess",
    "The Empress",
    "The Emperor",
    "The Hierophant",
    "The Lovers",
    "The Chariot",
    "Strength",
    "The Hermit",
    "Wheel of Fortune",
    "Justice",
    "The Hanged Man",
    "Death",
    "Temperance",
    "The Devil",
    "The Tower",
    "The Star",
    "The Moon",
    "The Sun",
    "Judgement",
    "The World",
] + [f"Minor Arcana Card #{i}" for i in range(22, 78)]


class ProviderResponse(BaseModel):
    """Контракт строгого вывода движка Core Execution VM."""

    card_id: int = Field(..., ge=0, lt=78)
    card_name: str
    interpretation: str
    execution_date: str


def calculate_deterministic_card(user_id: int, current_date: str, salt: str) -> int:
    """Математически строгое вычисление индекса состояния через SHA256."""
    payload = f"{user_id}:{current_date}:{salt}".encode("utf-8")
    hash_hex = hashlib.sha256(payload).hexdigest()
    return int(hash_hex, 16) % 78


@router.callback_query(lambda c: c.data == "draw")
async def draw(callback: CallbackQuery) -> None:
    """Генерация криптографически детерминированной Карты Дня и логирование перехода."""
    if not callback.from_user or not callback.message:
        return

    user_id = callback.from_user.id
    current_date = datetime.date.today().isoformat()

    # Вычисление инварианта перехода по формуле SHA256
    card_id = calculate_deterministic_card(user_id, current_date, SALT)
    card_name = TAROT_POOL[card_id]
    interpretation = f"Детерминированное состояние {card_name} для сессии {user_id}."

    # Валидация выходных типов данных рантайма через Pydantic v2
    response = ProviderResponse(
        card_id=card_id,
        card_name=card_name,
        interpretation=interpretation,
        execution_date=current_date,
    )

    partial_cards[user_id] = response.card_name

    # Инкапсуляция перехода состояния в слой истории (History Layer) через единый контракт БД
    await save_reading(
        user_id=user_id,
        spread="card_of_the_day",
        cards=response.card_name,
        interpretation=response.interpretation,
        paid=0,
    )

    text = (
        f"🔮 **Вы вытянули карту дня**:\n\n"
        f"**{response.card_name}** (ID: {response.card_id})\n\n"
        f"Это только **часть** послания Вселенной.\n\n"
        f"Чтобы узнать **полную картину** (прошлое • настоящее • будущее + глубокая интерпретация) "
        f"— нажмите кнопку ниже."
    )

    await callback.message.answer(text, reply_markup=paywall_kb())


@router.callback_query(lambda c: c.data == "buy")
async def buy(callback: CallbackQuery) -> None:
    """Главная точка монетизации и проверки баланса попыток переходов."""
    if not callback.from_user:
        return

    user = await get_user(callback.from_user.id)
    free_spreads = user[3] if user else 0  # free_spreads — 4-й столбец в таблице users

    if free_spreads > 0:
        await decrement_free_spreads(callback.from_user.id)
        await process_reading(callback, paid=0)
    else:
        await create_reading_invoice(callback.bot, callback.from_user.id)


async def process_reading(sender, paid: int) -> None:
    """Единая функция генерации и сохранения полного чтения (Past-Present-Future)."""
    if isinstance(sender, CallbackQuery):
        user_id = sender.from_user.id
        answer_func = sender.message.answer if sender.message else sender.answer
    else:
        user_id = sender.from_user.id
        answer_func = sender.answer

    spread_data = draw_spread()
    cards_text = "\n".join([f"{pos}: {card}" for pos, card in spread_data])

    interpretation = await generate_reading(cards_text)

    # Логирование мутации состояния в БД WAL
    await save_reading(
        user_id=user_id,
        spread="Past-Present-Future",
        cards=cards_text,
        interpretation=interpretation,
        paid=paid,
    )

    text = (
        f"🔮 **Ваше полное чтение судьбы**\n\n"
        f"{cards_text}\n\n"
        f"{interpretation}\n\n"
        f"Хотите ещё одно гадание? Приглашайте друзей — получите бесплатно! 👇"
    )

    await answer_func(text, reply_markup=share_kb())
