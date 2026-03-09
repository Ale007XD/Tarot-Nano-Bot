import asyncio

from bot.services.llm_service import generate_reading


async def _test():

    cards = """
Past: The Fool
Present: The Tower
Future: The Star
"""

    result = await generate_reading(cards)

    assert isinstance(result, str)

    assert len(result) > 20


def run():

    asyncio.run(_test())
