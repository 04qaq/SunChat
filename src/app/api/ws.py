# app/api/ws.py
import logging
import uuid
from pathlib import Path

from fastapi import WebSocket
from starlette.websockets import WebSocketDisconnect

from app.config import settings
from app.emtion.judge import compute_mood_signal
from app.emtion.state import build_mood_prompt_injection
from app.emtion.trace import append_chat_round_trace
from app.llm.client import LLMClient
from app.memory.short_term import ShortTermMemory
from app.models.message import Message

_logger = logging.getLogger(__name__)

_PROMPT_PATH = Path(__file__).resolve().parent.parent / "prompts" / "system_base.txt"


async def websocket_endpoint(ws: WebSocket) -> None:
    await ws.accept()

    session_id = ws.query_params.get("session_id") or ""
    if not session_id:
        session_id = str(uuid.uuid4())

    memory = ShortTermMemory(session_id)
    llm = LLMClient()
    chat_round = 0

    await ws.send_json({"type": "session", "session_id": session_id})

    try:
        while True:
            try:
                data = await ws.receive_json()
            except WebSocketDisconnect:
                return
            except Exception as exc:
                _logger.warning("receive_json failed: %s", exc)
                try:
                    await ws.send_json(
                        {
                            "type": "error",
                            "message": f"无法解析消息（需 JSON）：{exc!s}",
                        }
                    )
                except Exception:
                    return
                continue

            if data.get("type") != "chat":
                await ws.send_json(
                    {"type": "error", "message": "未知消息类型，请使用 type: chat"}
                )
                continue

            if "content" not in data:
                await ws.send_json({"type": "error", "message": "缺少 content 字段"})
                continue

            user_text = data["content"]
            chat_round += 1

            try:
                if settings.MOOD_USE_LLM_JUDGE:
                    mood = await compute_mood_signal(llm, memory.get(), user_text)
                    mood_pct = mood.mood_pct
                    mood_label = mood.label.strip() if mood.label else None
                    judge_used_llm = mood.used_llm
                    valence = mood.valence
                    confidence = mood.confidence
                else:
                    mood_pct = 50
                    mood_label = None
                    judge_used_llm = False
                    valence = 0.0
                    confidence = 0.0

                emo_style = build_mood_prompt_injection(
                    mood_pct,
                    mood_label if settings.MOOD_USE_LLM_JUDGE else None,
                )

                emo_payload: dict = {
                    "type": "emotion",
                    "mood_pct": mood_pct,
                    "session_id": session_id,
                }
                if mood_label is not None:
                    emo_payload["label"] = mood_label
                await ws.send_json(emo_payload)

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

                append_chat_round_trace(
                    session_id=session_id,
                    round_index=chat_round,
                    mood_pct=mood_pct,
                    valence=valence,
                    confidence=confidence,
                    emotional_context=emo_style,
                    user_text=user_text,
                    assistant_reply=reply,
                    mood_label=mood_label,
                    judge_used_llm=judge_used_llm,
                )

                await ws.send_json({"type": "done"})
            except WebSocketDisconnect:
                return
            except Exception as exc:
                _logger.exception("chat round failed session=%s", session_id)
                try:
                    await ws.send_json(
                        {
                            "type": "error",
                            "message": f"处理消息时出错：{exc!s}",
                        }
                    )
                except Exception:
                    return
    except WebSocketDisconnect:
        return
