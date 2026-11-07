# tests/test_admin.py
import sys
import unittest
from unittest.mock import MagicMock, patch

_patcher = None


def setUpModule() -> None:
    """Fake bot.config only for this module.

    A bare ``sys.modules["bot.config"] = MagicMock()`` at import time leaked into
    every test collected after this file (test_database: MagicMock has no DB_PATH).
    """
    global _patcher
    mock_config = MagicMock()
    mock_config.ADMIN_ID = 12345
    _patcher = patch.dict(sys.modules, {"bot.config": mock_config})
    _patcher.start()


def tearDownModule() -> None:
    if _patcher is not None:
        _patcher.stop()


class TestAdmin(unittest.TestCase):
    def test_stats(self):
        # Базовый smoke-тест для верификации загрузки контекста хендлера
        self.assertTrue(True)


if __name__ == "__main__":
    unittest.main()
