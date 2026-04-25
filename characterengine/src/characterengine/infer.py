"""会话启动时根据 OCEAN + 角色摘要 + foundations 节选推断 MBTI（infer_once）。"""
from __future__ import annotations

import json
import logging
import re
from typing import Protocol, Tuple, runtime_checkable

from characterengine.config import CharacterEngineConfig
from characterengine.message import Message
from characterengine.mbti_resources import load_foundations_excerpt
from characterengine.models import PsychologyProfileModel

_logger = logging.getLogger(__name__)

_VALID_MBTI = frozenset(
    [
        "INTJ",
        "INTP",
        "ENTJ",
        "ENTP",
        "INFJ",
        "INFP",
        "ENFJ",
        "ENFP",
        "ISTJ",
        "ISFJ",
        "ESTJ",
        "ESFJ",
        "ISTP",
        "ISFP",
        "ESTP",
        "ESFP",
    ]
)

_INFER_SYSTEM = """你是 Character Engine 的 MBTI 分型模块，仅用于角色扮演一致性。
你必须结合：用户提供的 Big Five(OCEAN)、角色摘要、以及下一条 system 中的《认知框架节选》。
从 16 型中选**最贴切**的一型；不得输出分析过程。
只输出一个 JSON 对象，字段严格为：
{"type": "四字母大写如 INFP", "cognitive_hint": "一句中文：该类型典型的信息加工与对外反应习惯（拒绝网络刻板段子）"}
type 必须是 16 型之一。"""


@runtime_checkable
class SupportsChatComplete(Protocol):
    async def complete_chat(
        self,
        messages: list[Message],
        *,
        temperature: float = 0.2,
        timeout_s: float = 60.0,
    ) -> str: ...


def _parse_infer(raw: str) -> Tuple[str, str]:
    m = re.search(r"\{[\s\S]*\}", raw)
    if not m:
        raise ValueError("no json")
    data = json.loads(m.group())
    t = str(data["type"]).strip().upper()
    if t not in _VALID_MBTI:
        raise ValueError(f"invalid mbti type: {t}")
    hint = str(data.get("cognitive_hint", "") or "").strip()
    return t, hint


async def infer_mbti_once(
    llm: SupportsChatComplete,
    profile: PsychologyProfileModel,
    *,
    config: CharacterEngineConfig | None = None,
) -> Tuple[str, str]:
    """返回 (mbti_type, cognitive_hint)。失败时回退 ISFJ + 空提示。"""
    cfg = config or CharacterEngineConfig()
    ocean = profile.ocean.model_dump()
    user_obj = {
        "role_summary": profile.role.role_summary,
        "ocean": ocean,
        "behavior_hints": profile.behavior_hints[:8],
    }
    foundations = load_foundations_excerpt(cfg.mbti_foundations_infer_max_chars)
    messages = [
        Message("system", _INFER_SYSTEM),
        Message(
            "system",
            "## 认知框架节选（用于分型，与心情评判共用同一套定义）\n\n" + foundations,
        ),
        Message("user", json.dumps(user_obj, ensure_ascii=False)),
    ]
    try:
        raw = await llm.complete_chat(
            messages,
            temperature=0.1,
            timeout_s=cfg.mbti_infer_timeout_s,
        )
        t, hint = _parse_infer(raw)
        return t, hint
    except Exception as exc:
        _logger.warning("mbti infer failed: %s", exc)
        return "ISFJ", ""
