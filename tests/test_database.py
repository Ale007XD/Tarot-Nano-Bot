import asyncio

from bot.database import init_db, add_user, get_user


async def _test():

    await init_db()

    user_id = 999999

    await add_user(user_id, "test_user")

    user = await get_user(user_id)

    assert user is not None


def run():

    asyncio.run(_test())
