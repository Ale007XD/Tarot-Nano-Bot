# tests/test_database.py
import os
import unittest
import bot.database

# Переопределяем путь к БД до инициализации тестов, чтобы избежать затирания продакшена
TEST_DB_PATH = "test_tarot.db"
bot.database.DB_PATH = TEST_DB_PATH

from bot.database import init_db, save_reading, get_user_readings


class TestDatabaseAsync(unittest.IsolatedAsyncioTestCase):

    async def asyncSetUp(self):
        """Инициализация изолированной тестовой схемы перед каждым тестом"""
        # На всякий случай зачищаем старый файл, если он остался после сбоя
        if os.path.exists(TEST_DB_PATH):
            os.remove(TEST_DB_PATH)
        await init_db()

    async def asyncTearDown(self):
        """Гарантированное уничтожение временного хранилища"""
        if os.path.exists(TEST_DB_PATH):
            os.remove(TEST_DB_PATH)

    async def test_history_layer_contract(self):
        """Тестирование сохранения состояний и получения хронологического таймлайна"""
        user_id = 77777
        
        # 1. Записываем первое (историческое) состояние (Free)
        await save_reading(
            user_id=user_id,
            spread="Колода Дня",
            cards="Шут",
            interpretation="Начало нового цикла рантайма.",
            paid=0
        )
        
        # 2. Записываем второе (более свежее) состояние (Paid)
        await save_reading(
            user_id=user_id,
            spread="Крест Расклад",
            cards="Башня, Смерть",
            interpretation="Глубокая реструктуризация кода ядра.",
            paid=1
        )

        # 3. Извлекаем историю с лимитом
        history = await get_user_readings(user_id=user_id, limit=10)
        
        # Проверяем размерность возвращаемого массива состояний
        self.assertEqual(len(history), 2)
        
        # Проверяем детерминизм сортировки (ORDER BY id DESC) — последнее состояние идет первым
        latest_reading = history[0]
        # Структура: (id, user_id, spread, cards, interpretation, paid)
        self.assertEqual(latest_reading[2], "Крест Расклад")
        self.assertEqual(latest_reading[3], "Башня, Смерть")
        self.assertEqual(latest_reading[5], 1)  # paid = True

        first_reading = history[1]
        self.assertEqual(first_reading[2], "Колода Дня")
        self.assertEqual(first_reading[5], 0)  # paid = False


if __name__ == '__main__':
    unittest.main()
    
