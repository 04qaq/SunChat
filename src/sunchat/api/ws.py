# app/api/ws.py
import logging
import uuid

from fastapi import WebSocket
from starlette.websockets import WebSocketDisconnect

from characterengine import (
    CharacterEngineConfig,
    append_character_state_to_user_content,
    build_character_state_context_xml,
    build_psychology_system_message,
    infer_mbti_once,
    judge_character_context_json,
)

from sunchat.config import settings
from sunchat.emtion.judge import compute_mood_signal
from sunchat.emtion.trace import append_chat_round_trace
from sunchat.llm.client import LLMClient
from sunchat.memory.short_term import ShortTermMemory
from sunchat.models.message import Message
from sunchat.prompt_resources import read_prompt_text
from sunchat.psychology.loader import load_psychology_profile

_logger = logging.getLogger(__name__)

_ENGINE_CFG = CharacterEngineConfig(
    mbti_infer_timeout_s=settings.MBTI_INFER_TIMEOUT_S,
    mbti_foundations_infer_max_chars=settings.MBTI_FOUNDATIONS_INFER_MAX_CHARS,
    mbti_main_foundations_max_chars=settings.MBTI_MAIN_FOUNDATIONS_MAX_CHARS,
    mbti_persona_max_chars=settings.MBTI_PERSONA_MAX_CHARS,
    mbti_judge_persona_excerpt_chars=settings.MBTI_JUDGE_PERSONA_EXCERPT_CHARS,
)


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
        mbti_type, cognitive_hint = await infer_mbti_once(
            llm, profile, config=_ENGINE_CFG
        )
        mbti_source = "inferred"
    else:
        mbti_type = (profile.mbti.type or "INFP").strip().upper()
        cognitive_hint = (profile.mbti.notes or "").strip()
        mbti_source = "fixed"

    character_context_json = judge_character_context_json(
        profile, mbti_type, cognitive_hint, config=_ENGINE_CFG
    )
    psych_system = build_psychology_system_message(
        profile, mbti_type, cognitive_hint, config=_ENGINE_CFG
    )

    await ws.send_json(
        {
            "type": "session",
            "session_id": session_id,
            "psychology": {
                "mbti": mbti_type,
                "mbti_source": mbti_source,
                "mission_primary": profile.drives.mission.primary,
                "mission_secondary": profile.drives.mission.secondary,
                "goals_horizon": profile.drives.horizon,
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

                state_xml = build_character_state_context_xml(
                    profile=profile,
                    mood_pct=mood_pct,
                    mood_label=mood_label if settings.MOOD_USE_LLM_JUDGE else None,
                    valence=valence,
                    confidence=confidence,
                    mood_judge_enabled=settings.MOOD_USE_LLM_JUDGE,
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
                hist = memory.get()
                if hist and hist[-1].role == "user":
                    last_augmented = append_character_state_to_user_content(
                        hist[-1].content,
                        profile=profile,
                        mood_pct=mood_pct,
                        mood_label=mood_label if settings.MOOD_USE_LLM_JUDGE else None,
                        valence=valence,
                        confidence=confidence,
                        mood_judge_enabled=settings.MOOD_USE_LLM_JUDGE,
                    )
                    hist_for_llm = hist[:-1] + [Message("user", last_augmented)]
                else:
                    hist_for_llm = hist

                messages = [
                    Message("system", system_prompt),
                    Message("system", psych_system),
                ] + hist_for_llm

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
                    emotional_context=state_xml,
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
