import pytest
from unittest.mock import AsyncMock, MagicMock
from bot.handlers.admin import admin_stats, give_spreads
from bot.config import ADMIN_ID

# Тест админ-статистики
@pytest.mark.asyncio
async def test_admin_stats_logic():
    message = AsyncMock()
    # Имитируем вызов функции
    await admin_stats(message)
    # Проверяем, что бот отправил ответ (вызвал message.answer)
    assert message.answer.called

# Тест выдачи попыток
@pytest.mark.asyncio
async def test_give_spreads_command():
    message = AsyncMock()
    command = MagicMock()
    command.args = "12345 5" # ID и количество
    
    # Вызываем функцию
    await give_spreads(message, command)
    
    # Проверяем, что пользователю ушел ответ о начислении
    assert "начислено" in message.answer.call_args[0][0].lower()

