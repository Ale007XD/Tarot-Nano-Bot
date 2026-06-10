from __future__ import annotations

import logging

import aiosqlite
from aiogram import F, Router
from aiogram.types import Message, PreCheckoutQuery
from pydantic import BaseModel, Field

from bot.database import DB_PATH

router = Router(name="payment_router")


class OrderPayload(BaseModel):
    user_id: int
    reading_id: str
    amount: int = Field(gt=0)


@router.pre_checkout_query()
async def process_pre_checkout_query(pre_checkout_query: PreCheckoutQuery) -> None:
    try:
        OrderPayload.model_validate_json(pre_checkout_query.invoice_payload)
        await pre_checkout_query.answer(ok=True)
    except Exception as e:
        logging.error(f"[Payment Engine] PreCheckoutQuery validation failure: {e}")
        await pre_checkout_query.answer(
            ok=False,
            error_message="Критическая ошибка валидации структуры платежа. Повторите запрос.",
        )


@router.message(F.successful_payment)
async def process_successful_payment(message: Message) -> None:
    successful_payment = message.successful_payment
    if not successful_payment:
        return

    try:
        payload = OrderPayload.model_validate_json(successful_payment.invoice_payload)

        async with aiosqlite.connect(DB_PATH) as db:
            async with db.execute(
                "UPDATE readings SET paid = 1 WHERE id = ? AND user_id = ?",
                (payload.reading_id, payload.user_id),
            ) as cursor:
                if cursor.rowcount == 0:
                    logging.warning(
                        f"[Payment Engine] State update anomaly: "
                        f"reading {payload.reading_id} not found."
                    )
                    await message.answer(
                        "⚠️ Транзакция зафиксирована, но целевой расклад не обнаружен в репозитории."
                    )
                    return
            await db.commit()

        await message.answer(
            "🔮 Оплата Telegram Stars успешно верифицирована!\n"
            "Ваш полный расклад Past-Present-Future разблокирован "
            "и сохранен в истории состояний."
        )
    except Exception as e:
        logging.error(f"[Payment Engine] Critical state mutation failure: {e}")
        await message.answer(
            "🚨 Произошел системный сбой при фиксации перехода состояния. Обратитесь в поддержку."
        )
