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
            (user_id, username, referrer_id)
        )

        await db.commit()


async def add_referral(referrer_id, invited_id):

    async with aiosqlite.connect(DB_PATH) as db:

        await db.execute(
            "INSERT INTO referrals(referrer_id, invited_id) VALUES(?,?)",
            (referrer_id, invited_id)
        )

        await db.execute(
            "UPDATE users SET free_spreads = free_spreads + 1 WHERE user_id=?",
            (referrer_id,)
        )

        await db.commit()


async def get_user(user_id):

    async with aiosqlite.connect(DB_PATH) as db:

        cursor = await db.execute(
            "SELECT * FROM users WHERE user_id=?",
            (user_id,)
        )

        return await cursor.fetchone()
