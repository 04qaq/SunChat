# sunchat/application/ws_session.py
"""单 WebSocket 连接上的聊天编排：与 FastAPI/Starlette 解耦的用例层实现。"""

from __future__ import annotations

import json
import logging
import uuid
from dataclasses import dataclass

import httpx
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
from characterengine.models import PsychologyProfileModel

from sunchat.api.ws_protocol import WS_PROTOCOL_NAME, WS_PROTOCOL_VERSION
from sunchat.config import Settings
from sunchat.domain.errors import UserFacingError
from sunchat.emotion.strategies import LlmMoodStrategy, StaticMoodStrategy
from sunchat.infrastructure.llm import HttpxLlmCompletions
from sunchat.infrastructure.mood_trace import JsonlMoodTraceWriter
from sunchat.memory.short_term import ShortTermMemory
from sunchat.models.message import Message
from sunchat.ports.mood import MoodStrategy
from sunchat.ports.trace import MoodTracePort
from sunchat.prompt_resources import read_prompt_text
from sunchat.psychology.loader import load_psychology_profile

_logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class _EngineBundle:
    """每连接内复用的心理档案、引擎配置与已组装的 JSON/系统提示。"""

    profile: PsychologyProfileModel
    config: CharacterEngineConfig
    character_context_json: str
    psych_system: str
    mbti_type: str
    mbti_source: str


def _engine_config(s: Settings) -> CharacterEngineConfig:
    return CharacterEngineConfig(
        mbti_infer_timeout_s=s.MBTI_INFER_TIMEOUT_S,
        mbti_foundations_infer_max_chars=s.MBTI_FOUNDATIONS_INFER_MAX_CHARS,
        mbti_main_foundations_max_chars=s.MBTI_MAIN_FOUNDATIONS_MAX_CHARS,
        mbti_persona_max_chars=s.MBTI_PERSONA_MAX_CHARS,
        mbti_judge_persona_excerpt_chars=s.MBTI_JUDGE_PERSONA_EXCERPT_CHARS,
    )


def _mood_strategy(s: Settings, llm: HttpxLlmCompletions) -> MoodStrategy:
    if s.MOOD_USE_LLM_JUDGE:
        return LlmMoodStrategy(
            llm=llm,
            max_dialogue_messages=s.MOOD_JUDGE_MAX_MESSAGES,
            judge_temperature=0.15,
            judge_timeout_s=s.MOOD_JUDGE_TIMEOUT_S,
        )
    return StaticMoodStrategy()


def _trace(s: Settings) -> MoodTracePort:
    return JsonlMoodTraceWriter(
        enabled=s.MOOD_TRACE_ENABLED,
        base_dir=s.MOOD_TRACE_DIR,
    )


def _llm(httpx_client: httpx.AsyncClient, s: Settings) -> HttpxLlmCompletions:
    return HttpxLlmCompletions(
        httpx_client,
        base_url=s.LLM_BASE_URL,
        api_key=s.LLM_API_KEY,
        model=s.LLM_MODEL,
    )


async def _init_engine(llm: HttpxLlmCompletions, s: Settings) -> _EngineBundle:
    eng = _engine_config(s)
    profile = load_psychology_profile()
    if profile.mbti.strategy == "infer_once":
        mbti_type, cognitive_hint = await infer_mbti_once(
            llm, profile, config=eng
        )
        mbti_source = "inferred"
    else:
        mbti_type = (profile.mbti.type or "INFP").strip().upper()
        cognitive_hint = (profile.mbti.notes or "").strip()
        mbti_source = "fixed"

    character_context_json = judge_character_context_json(
        profile, mbti_type, cognitive_hint, config=eng
    )
    psych_system = build_psychology_system_message(
        profile, mbti_type, cognitive_hint, config=eng
    )
    return _EngineBundle(
        profile=profile,
        config=eng,
        character_context_json=character_context_json,
        psych_system=psych_system,
        mbti_type=mbti_type,
        mbti_source=mbti_source,
    )


async def run_websocket_chat(
    ws: WebSocket,
    *,
    httpx_client: httpx.AsyncClient,
    settings: Settings,
) -> None:
    """
    接受 WebSocket，完成：会话建连、心理元数据、按轮处理 ``chat`` 并流式回复。

    Args:
        ws: Starlette WebSocket 实例（已在外层或此处 ``accept``）。
        httpx_client: 应用 lifespan 注入的 **共享** ``httpx.AsyncClient``。
        settings: 当前进程配置（便于测试注入子类或 mock）。

    说明:
        异常路径对用户仅返回短文案；详细堆栈与关联 ``error_id`` 写入日志。客户端
        在 ``error`` 后仍会收到 ``done``，以统一结束单轮状态机。
    """
    await ws.accept()

    s = settings
    raw_session = (ws.query_params.get("session_id") or "").strip()
    session_id = raw_session if raw_session else str(uuid.uuid4())

    llm = _llm(httpx_client, s)
    mood = _mood_strategy(s, llm)
    trace = _trace(s)
    try:
        bundle = await _init_engine(llm, s)
    except Exception as exc:
        _logger.exception("心理引擎初始化失败: %s", exc)
        try:
            err_id = uuid.uuid4().hex[:8]
            await ws.send_json(
                {
                    "type": "error",
                    "message": f"服务初始化失败（{err_id}），请检查配置与依赖。",
                }
            )
        except Exception:
            return
        return

    profile = bundle.profile
    mbti_type = bundle.mbti_type
    mbti_source = bundle.mbti_source
    character_context_json = bundle.character_context_json
    psych_system = bundle.psych_system

    memory = ShortTermMemory(
        session_id,
        data_storage_path=s.DATA_STORAGE_PATH,
        chat_window_size=s.CHAT_WINDOW_SIZE,
        session_storage_model=s.SESSION_STORAGE_MODEL,
    )
    chat_round = 0

    await ws.send_json(
        {
            "type": "session",
            "session_id": session_id,
            "protocol": {
                "name": WS_PROTOCOL_NAME,
                "version": WS_PROTOCOL_VERSION,
            },
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
            except (json.JSONDecodeError, TypeError, ValueError) as exc:
                _logger.warning("receive_json 失败: %s", exc, exc_info=True)
                if not await _safe_send(
                    ws,
                    {
                        "type": "error",
                        "message": "无法解析消息（需合法 JSON 对象）",
                    },
                ):
                    return
                continue
            except Exception as exc:
                _logger.warning("receive_json 未预期错误: %s", exc, exc_info=True)
                if not await _safe_send(
                    ws,
                    {
                        "type": "error",
                        "message": "无法解析消息（需 JSON）",
                    },
                ):
                    return
                continue

            if data.get("type") != "chat":
                await _safe_send(
                    ws,
                    {
                        "type": "error",
                        "message": "未知消息类型，请使用 type: chat",
                    },
                )
                continue

            if "content" not in data:
                await _safe_send(
                    ws, {"type": "error", "message": "缺少 content 字段"}
                )
                continue

            user_text = data.get("content")
            if not isinstance(user_text, str):
                user_text = str(user_text)
            chat_round += 1

            try:
                mood_result = await mood.compute(
                    memory.get(),
                    user_text,
                    character_context_json=character_context_json,
                )
                if s.MOOD_USE_LLM_JUDGE:
                    mood_pct = mood_result.mood_pct
                    mood_label = (
                        mood_result.label.strip() if mood_result.label else None
                    )
                    judge_used_llm = mood_result.used_llm
                    valence = mood_result.valence
                    confidence = mood_result.confidence
                else:
                    mood_pct = 50
                    mood_label = None
                    judge_used_llm = False
                    valence = 0.0
                    confidence = 0.0

                state_xml = build_character_state_context_xml(
                    profile=profile,
                    mood_pct=mood_pct,
                    mood_label=mood_label if s.MOOD_USE_LLM_JUDGE else None,
                    valence=valence,
                    confidence=confidence,
                    mood_judge_enabled=s.MOOD_USE_LLM_JUDGE,
                )

                emo_payload: dict = {
                    "type": "emotion",
                    "mood_pct": mood_pct,
                    "session_id": session_id,
                }
                if mood_label is not None:
                    emo_payload["label"] = mood_label
                if not await _safe_send(ws, emo_payload):
                    return

                system_prompt = read_prompt_text("system_base.txt")

                memory.add(Message("user", user_text))
                hist = memory.get()

                if hist and hist[-1].role == "user":
                    last_augmented = append_character_state_to_user_content(
                        hist[-1].content,
                        profile=profile,
                        mood_pct=mood_pct,
                        mood_label=mood_label
                        if s.MOOD_USE_LLM_JUDGE
                        else None,
                        valence=valence,
                        confidence=confidence,
                        mood_judge_enabled=s.MOOD_USE_LLM_JUDGE,
                    )
                    hist_for_llm = hist[:-1] + [Message("user", last_augmented)]
                else:
                    _logger.error(
                        "短记忆不变量异常：add(user) 后末条非 user session=%s",
                        session_id,
                    )
                    hist_for_llm = hist

                messages = [
                    Message("system", system_prompt),
                    Message("system", psych_system),
                ] + hist_for_llm

                reply = ""
                async for token in llm.stream_chat(messages):
                    reply += token
                    if not await _safe_send(
                        ws, {"type": "token", "delta": token}
                    ):
                        return

                memory.add(Message("assistant", reply))

                trace.append_round(
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
                if not await _safe_send(ws, {"type": "done"}):
                    return

            except WebSocketDisconnect:
                return
            except UserFacingError as ufe:
                if not await _round_error(
                    ws, session_id, ufe.public_message
                ):
                    return
            except httpx.HTTPError as exc:
                _logger.error(
                    "LLM/HTTP 错误 session=%s: %s", session_id, exc, exc_info=True
                )
                if not await _round_error(
                    ws, session_id, "上游服务暂时不可用，请稍后再试。"
                ):
                    return
            except Exception as exc:
                err_id = uuid.uuid4().hex[:8]
                _logger.exception(
                    "chat 轮次失败 session=%s error_id=%s", session_id, err_id
                )
                if not await _round_error(
                    ws,
                    session_id,
                    f"处理消息时出错（{err_id}）。可凭编号在日志中定位。",
                ):
                    return
    except WebSocketDisconnect:
        return


async def _safe_send(ws: WebSocket, payload: dict) -> bool:
    """尝试发送 JSON；对端已断开时返回 False。"""
    try:
        await ws.send_json(payload)
        return True
    except (WebSocketDisconnect, RuntimeError) as e:
        _logger.debug("send 失败（连接已关闭？）: %s", e)
        return False
    except Exception as exc:
        _logger.warning("send_json 失败: %s", exc, exc_info=True)
        return False


async def _round_error(
    ws: WebSocket, _session_id: str, public_message: str
) -> bool:
    if not await _safe_send(
        ws, {"type": "error", "message": public_message}
    ):
        return False
    return await _safe_send(ws, {"type": "done"})
