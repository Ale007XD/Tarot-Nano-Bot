# bot/services/llm_service.py
import httpx
import json
from bot.config import OPENAI_API_KEY, OPENROUTER_API_KEY, USE_OPENROUTER


async def generate_reading(cards: str) -> str:
    prompt = f"""
You are a mystical tarot reader.

Interpret this spread in a personal tone, warmly and mysteriously.

Cards:
{cards}

Explain past, present and future in 2-3 beautiful paragraphs.
"""

    try:
        if USE_OPENROUTER:
            if not OPENROUTER_API_KEY:
                raise ValueError("OPENROUTER_API_KEY is missing in .env")

            headers = {"Authorization": f"Bearer {OPENROUTER_API_KEY}"}
            json_data = {
                "model": "mistralai/mistral-7b-instruct:free",
                "messages": [{"role": "user", "content": prompt}]
            }
            url = "https://openrouter.ai/api/v1/chat/completions"
        else:
            if not OPENAI_API_KEY:
                raise ValueError("OPENAI_API_KEY is missing in .env")
            headers = {"Authorization": f"Bearer {OPENAI_API_KEY}"}
            json_data = {
                "model": "gpt-4o-mini",
                "messages": [{"role": "user", "content": prompt}]
            }
            url = "https://api.openai.com/v1/chat/completions"

        async with httpx.AsyncClient(timeout=20.0) as client:
            r = await client.post(url, headers=headers, json=json_data)
            data = r.json()

            if r.status_code != 200 or "choices" not in data:
                error_msg = data.get("error", {}).get("message", str(data))
                print(f"❌ LLM ERROR {r.status_code}: {error_msg}")
                print(f"Full response: {json.dumps(data, ensure_ascii=False, indent=2)}")
                return "🔮 Оракул сейчас в медитации... Попробуйте чуть позже или проверьте API-ключ в .env"

            return data["choices"][0]["message"]["content"]

    except Exception as e:
        print(f"🚨 LLM Exception: {type(e).__name__}: {e}")
        return "🔮 Судьба шепчет... (временная техническая пауза, попробуйте через минуту)"
