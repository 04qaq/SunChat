# app/llm/client.py
import json
from typing import List, AsyncGenerator

import httpx

from app.config import settings
from app.models.message import Message


class LLMClient:

    async def stream_chat(
        self,
        messages: List[Message],
    ) -> AsyncGenerator[str, None]:
        base = settings.LLM_BASE_URL.rstrip("/")
        url = f"{base}/chat/completions"

        payload = {
            "model": settings.LLM_MODEL,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "stream": True,
        }

        headers = {
            "Authorization": f"Bearer {settings.LLM_API_KEY}",
            "Content-Type": "application/json",
        }

        async with httpx.AsyncClient(timeout=None) as client:
            async with client.stream("POST", url, json=payload, headers=headers) as r:
                r.raise_for_status()
                async for line in r.aiter_lines():
                    if not line or not line.startswith("data:"):
                        continue

                    if line.strip() == "data: [DONE]":
                        break

                    try:
                        raw = line[5:].strip()
                        data = json.loads(raw)
                        delta = data["choices"][0]["delta"].get("content") or ""
                        if delta:
                            yield delta
                    except (json.JSONDecodeError, KeyError, IndexError):
                        continue