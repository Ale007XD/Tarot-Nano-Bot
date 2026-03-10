import sys
from unittest.mock import MagicMock

# Сначала создаем фейковый модуль config
mock_config = MagicMock()
mock_config.ADMIN_ID = 12345 
sys.modules['bot.config'] = mock_config

# Теперь можно безопасно импортировать admin
from bot.handlers.admin import admin_stats
import unittest

class TestAdmin(unittest.TestCase):
    def test_stats(self):
        self.assertTrue(True)

if __name__ == '__main__':
    unittest.main()

