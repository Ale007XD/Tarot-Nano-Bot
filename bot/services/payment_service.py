from __future__ import annotations

import json

from aiogram import Bot
from aiogram.types import LabeledPrice

from bot.i18n import t

_READING_AMOUNT = 69


async def create_reading_invoice(
    bot: Bot,
    user_id: int,
    execution_id: str,
    lang: str = "en",
) -> None:
    payload = json.dumps(
        {"user_id": user_id, "execution_id": execution_id, "amount": _READING_AMOUNT}
    )
    prices = [LabeledPrice(label=t("btn_buy", lang), amount=_READING_AMOUNT)]
    await bot.send_invoice(
        chat_id=user_id,
        title="🔮 Destiny Oracle — Full Reading",
        description="Past • Present • Future + personal interpretation",
        payload=payload,
        provider_token="",
        currency="XTR",
        prices=prices,
        start_parameter="tarot-reading",
    )
