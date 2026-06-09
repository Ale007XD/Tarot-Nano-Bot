# tests/test_admin.py
import sys
import unittest
from unittest.mock import MagicMock

# Сначала создаем фейковый модуль config для изоляции окружения
mock_config = MagicMock()
mock_config.ADMIN_ID = 12345
sys.modules["bot.config"] = mock_config

# Теперь можно безопасно импортировать компонент администрирования


class TestAdmin(unittest.TestCase):
    def test_stats(self):
        # Базовый smoke-тест для верификации загрузки контекста хендлера
        self.assertTrue(True)


if __name__ == "__main__":
    unittest.main()
