# bot/database.py
import aiosqlite
from bot.config import DB_PATH


async def init_db():

    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
        CREATE TABLE IF NOT EXISTS users(
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            referrer_id INTEGER,
            free_spreads INTEGER DEFAULT 1
        )
        """)

        await db.execute("""
        CREATE TABLE IF NOT EXISTS readings(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            spread TEXT,
            cards TEXT,
            interpretation TEXT,
            paid INTEGER
        )
        """)

        await db.execute("""
        CREATE TABLE IF NOT EXISTS referrals(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            referrer_id INTEGER,
            invited_id INTEGER
        )
        """)

        await db.commit()


async def add_user(user_id, username, referrer_id=None):

    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT OR IGNORE INTO users(user_id, username, referrer_id) VALUES(?,?,?)",
            (user_id, username, referrer_id),
        )

        await db.commit()


async def add_referral(referrer_id, invited_id):

    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO referrals(referrer_id, invited_id) VALUES(?,?)",
            (referrer_id, invited_id),
        )

        await db.execute(
            "UPDATE users SET free_spreads = free_spreads + 1 WHERE user_id=?",
            (referrer_id,),
        )

        await db.commit()


async def get_user(user_id):

    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("SELECT * FROM users WHERE user_id=?", (user_id,))

        return await cursor.fetchone()


# ====================== НОВЫЕ ФУНКЦИИ ДЛЯ МОНЕТИЗАЦИИ ======================


async def decrement_free_spreads(user_id: int):
    """Тратим одно бесплатное гадание (от рефералов)"""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE users SET free_spreads = free_spreads - 1 "
            "WHERE user_id=? AND free_spreads > 0",
            (user_id,),
        )
        await db.commit()


async def save_reading(
    user_id: int, spread: str, cards: str, interpretation: str, paid: int
):
    """Сохраняем каждое гадание в историю"""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO readings(user_id, spread, cards, interpretation, paid) "
            "VALUES(?,?,?,?,?)",
            (user_id, spread, cards, interpretation, paid),
        )
        await db.commit()


# ====================== SPRINT-0: HISTORY LAYER ======================


async def get_user_readings(user_id: int, limit: int = 10) -> list[tuple]:
    """Получение истории состояний раскладов пользователя для Reflection Engine"""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT id, user_id, spread, cards, interpretation, paid FROM readings "
            "WHERE user_id = ? ORDER BY id DESC LIMIT ?",
            (user_id, limit),
        )
        return await cursor.fetchall()
