import sqlite3
import unittest

class TestDatabase(unittest.TestCase):
    def test_db_structure(self):
        # Используем оперативную память для теста, никаких файлов
        conn = sqlite3.connect(':memory:')
        cursor = conn.cursor()
        
        # Создаем таблицу как в реальном проекте
        cursor.execute("CREATE TABLE users (user_id INTEGER, free_spreads INTEGER)")
        cursor.execute("INSERT INTO users VALUES (123, 1)")
        
        cursor.execute("SELECT free_spreads FROM users WHERE user_id=123")
        result = cursor.fetchone()[0]
        
        self.assertEqual(result, 1)
        conn.close()

if __name__ == '__main__':
    unittest.main()

