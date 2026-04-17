# app/api/ws.py
import uuid
from pathlib import Path

from fastapi import WebSocket

from app.emtion.sentiment import analyze_sentiment
from app.emtion.state import EmotionMapper, EmotionState
from app.llm.client import LLMClient
from app.memory.short_term import ShortTermMemory
from app.models.message import Message

_PROMPT_PATH = Path(__file__).resolve().parent.parent / "prompts" / "system_base.txt"


async def websocket_endpoint(ws: WebSocket) -> None:
    await ws.accept()

    session_id = ws.query_params.get("session_id") or ""
    if not session_id:
        session_id = str(uuid.uuid4())

    memory = ShortTermMemory(session_id)
    emotion = EmotionState()
    llm = LLMClient()

    await ws.send_json({"type": "session", "session_id": session_id})

    while True:
        data = await ws.receive_json()

        if data["type"] == "chat":
            user_text = data["content"]

            s_new = analyze_sentiment(user_text)
            e = emotion.update(s_new)
            emo_style = EmotionMapper.style_for_e(e)

            await ws.send_json({"type": "emotion", "e": e, "session_id": session_id})

            system_prompt = _PROMPT_PATH.read_text(encoding="utf-8")

            memory.add(Message("user", user_text))
            messages = [
                Message("system", system_prompt),
                Message("system", emo_style),
            ] + memory.get()

            reply = ""

            async for token in llm.stream_chat(messages):
                reply += token
                await ws.send_json({"type": "token", "delta": token})

            memory.add(Message("assistant", reply))

            await ws.send_json({"type": "done"})
