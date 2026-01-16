import requests
from config import DEEPSEEK_API_KEY, MODEL_NAME, MAX_TOKENS, TEMPERATURE

API_URL = "https://api.deepseek.com/chat/completions"

def ask_deepseek(messages):
    response = requests.post(
        API_URL,
        headers={
            "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
            "Content-Type": "application/json"
        },
        json={
            "model": MODEL_NAME,
            "messages": messages,
            "max_tokens": MAX_TOKENS,
            "temperature": TEMPERATURE
        },
        timeout=30
    )

    response.raise_for_status()
    return response.json()["choices"][0]["message"]["content"]
