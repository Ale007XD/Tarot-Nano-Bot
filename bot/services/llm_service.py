import httpx
from bot.config import OPENAI_API_KEY, OPENROUTER_API_KEY, USE_OPENROUTER


async def generate_reading(cards):

    prompt = f"""
You are a mystical tarot reader.

Interpret this spread in a personal tone.

Cards:
{cards}

Explain past, present and future.
"""

    if USE_OPENROUTER:

        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}"
        }

        json = {
            "model": "mistralai/mistral-7b-instruct:free",
            "messages": [{"role": "user", "content": prompt}]
        }

        async with httpx.AsyncClient() as client:

            r = await client.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers=headers,
                json=json
            )

            data = r.json()

            return data["choices"][0]["message"]["content"]

    else:

        headers = {
            "Authorization": f"Bearer {OPENAI_API_KEY}"
        }

        json = {
            "model": "gpt-4o-mini",
            "messages": [{"role": "user", "content": prompt}]
        }

        async with httpx.AsyncClient() as client:

            r = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers=headers,
                json=json
            )

            data = r.json()

            return data["choices"][0]["message"]["content"]
