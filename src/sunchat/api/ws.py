# app/api/ws.py
import logging
import uuid

from fastapi import WebSocket
from starlette.websockets import WebSocketDisconnect

from sunchat.config import settings
from sunchat.emtion.judge import compute_mood_signal
from sunchat.emtion.state import build_mood_prompt_injection
from sunchat.emtion.trace import append_chat_round_trace
from sunchat.llm.client import LLMClient
from sunchat.memory.short_term import ShortTermMemory
from sunchat.models.message import Message
from sunchat.psychology.assemble import (
    build_psychology_system_message,
    judge_character_context_json,
)
from sunchat.prompt_resources import read_prompt_text
from sunchat.psychology.loader import load_psychology_profile
from sunchat.psychology.mbti_infer import infer_mbti_once

_logger = logging.getLogger(__name__)


async def websocket_endpoint(ws: WebSocket) -> None:
    await ws.accept()

    session_id = ws.query_params.get("session_id") or ""
    if not session_id:
        session_id = str(uuid.uuid4())

    memory = ShortTermMemory(session_id)
    llm = LLMClient()
    chat_round = 0

    profile = load_psychology_profile()
    if profile.mbti.strategy == "infer_once":
        mbti_type, cognitive_hint = await infer_mbti_once(llm, profile)
        mbti_source = "inferred"
    else:
        mbti_type = (profile.mbti.type or "INFP").strip().upper()
        cognitive_hint = (profile.mbti.notes or "").strip()
        mbti_source = "fixed"

    character_context_json = judge_character_context_json(
        profile, mbti_type, cognitive_hint
    )
    psych_system = build_psychology_system_message(
        profile, mbti_type, cognitive_hint
    )

    await ws.send_json(
        {
            "type": "session",
            "session_id": session_id,
            "psychology": {
                "mbti": mbti_type,
                "mbti_source": mbti_source,
                "mission_primary": profile.drives.mission.primary,
                "drives_schema_version": profile.drives.schema_version,
            },
        }
    )

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
                    mood = await compute_mood_signal(
                        llm,
                        memory.get(),
                        user_text,
                        character_context_json=character_context_json,
                    )
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

                system_prompt = read_prompt_text("system_base.txt")

                memory.add(Message("user", user_text))
                messages = [
                    Message("system", system_prompt),
                    Message("system", psych_system),
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
                    mbti_type=mbti_type,
                    mbti_source=mbti_source,
                    mission_primary=profile.drives.mission.primary,
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
