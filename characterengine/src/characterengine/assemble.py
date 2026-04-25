"""评判用 JSON、主对话 system 补充段与末条 user 动态 XML。"""
from __future__ import annotations

import json
from xml.sax.saxutils import escape

from characterengine.config import CharacterEngineConfig
from characterengine.cues import big_five_to_behavior_cues, neuroticism_score
from characterengine.mbti_resources import (
    format_persona_for_judge,
    format_persona_for_main,
    optional_foundations_block_for_main,
)
from characterengine.models import PsychologyProfileModel


def judge_character_context_json(
    profile: PsychologyProfileModel,
    mbti_type: str,
    cognitive_hint: str,
    *,
    config: CharacterEngineConfig | None = None,
) -> str:
    cfg = config or CharacterEngineConfig()
    persona_j = format_persona_for_judge(mbti_type, config=cfg)
    payload = {
        "name": profile.role.name,
        "name_reading": profile.role.name_reading,
        "role_summary": profile.role.role_summary,
        "ocean": profile.ocean.model_dump(),
        "neuroticism": round(neuroticism_score(profile.ocean), 4),
        "ocean_notes": profile.ocean_notes,
        "behavior_hints": list(profile.behavior_hints),
        "big_five_behavior_cues": big_five_to_behavior_cues(profile.ocean),
        "scenario": profile.scenario,
        "relationship": profile.relationship,
        "goals": {
            "primary": profile.drives.mission.primary,
            "secondary": profile.drives.mission.secondary,
            "horizon": profile.drives.horizon,
        },
        "behavior_logic": {
            "framework": "MBTI",
            "engine": "characterengine",
            "type": mbti_type.upper(),
            "cognitive_hint": cognitive_hint or profile.mbti.notes,
            "persona_excerpt_for_mood": persona_j,
            "playbook_note": (
                "MBTI 为辅助标签；气质冲突时以 big_five_behavior_cues 与 role_summary 为准。"
                "完整型格见主对话 system 中《MBTI 行为规格》；推断心情须结合 pressure_mood 与 OCEAN。"
            ),
        },
        "drives": profile.drives.model_dump(mode="json"),
    }
    return json.dumps(payload, ensure_ascii=False, indent=2)


def build_psychology_system_message(
    profile: PsychologyProfileModel,
    mbti_type: str,
    cognitive_hint: str,
    *,
    config: CharacterEngineConfig | None = None,
) -> str:
    cfg = config or CharacterEngineConfig()
    d = profile.drives
    cues = big_five_to_behavior_cues(profile.ocean)
    lines: list[str] = [
        "### 【心理引擎 · 气质骨架（Big Five）】",
        f"- {cues}",
        "- **冲突策略**：五维气质骨架为单一真源（SSOT）；**MBTI 为可读标签与表达习惯辅助**，若与气质指令、角色摘要或 system 总则冲突，以气质骨架与总则为准。",
        "",
        "### 【心理引擎 · 行为逻辑（MBTI 辅助）】",
        f"- 信息加工与表达可参照 **MBTI {mbti_type.upper()}** 与本节《行为规格》（与上文气质叠加；禁止仅靠四字母随意发挥）。",
    ]
    hint = (cognitive_hint or profile.mbti.notes or "").strip()
    if hint:
        lines.append(f"- 推断/配置给出的认知提示：**{hint}**")
    lines += ["", format_persona_for_main(mbti_type, config=cfg), ""]
    found_blk = optional_foundations_block_for_main(cfg.mbti_main_foundations_max_chars)
    if found_blk.strip():
        lines += [found_blk, ""]
    sec_line = (d.mission.secondary or "").strip()
    lines += [
        "### 【心理引擎 · 目标与需要】",
        f"- **主目标（goals.primary / mission.primary）**：{d.mission.primary or '（可在 YAML 的 drives.mission.primary 配置）'}",
    ]
    if sec_line:
        lines.append(f"- **次目标（goals.secondary）**：{sec_line}")
    lines.append(f"- **目标时间尺度（goals.horizon）**：{d.horizon or 'scene'}")
    if (d.mission.narrative or "").strip():
        lines.append(f"- **叙事补充（mission.narrative）**：{d.mission.narrative.strip()}")
    if d.needs:
        lines.append(
            "- **需要层（needs，可扩展）**："
            + json.dumps(d.needs, ensure_ascii=False)
        )
    if d.extensions:
        lines.append(
            "- **扩展位（drives.extensions，供后续任务/插件读取）**："
            + json.dumps(d.extensions, ensure_ascii=False)
        )
    lines += [
        "",
        "### 【心理引擎 · 动态状态注入】",
        "- 用户消息末尾可能附有 `<context><module name=\"character_state\">...</module></context>`，内含本轮**心情**与**目标**快照（XML）。",
        "- 心情指数 **0～100**（**50 为中性**）与 `valence`/`arousal` 为结构化锚点；请结合完整人设自行演绎语气与详略，**不要**机械复读数字，不要使用通用客服腔。",
        "",
        "请在本轮回复中让人物的目标与需要自然影响动机与措辞；未配置项勿编造具体事实，可保持留白。",
    ]
    return "\n".join(lines).strip()


def _valence_token(valence: float) -> str:
    if valence < -0.5:
        return "negative"
    if valence < -0.15:
        return "slightly_negative"
    if valence <= 0.15:
        return "neutral"
    if valence < 0.5:
        return "slightly_positive"
    return "positive"


def _arousal_token(valence: float, confidence: float) -> str:
    intensity = abs(valence) * max(0.0, min(1.0, confidence))
    if intensity < 0.15:
        return "low"
    if intensity < 0.45:
        return "medium"
    return "high"


def build_character_state_context_xml(
    *,
    profile: PsychologyProfileModel,
    mood_pct: int,
    mood_label: str | None,
    valence: float,
    confidence: float,
    mood_judge_enabled: bool,
) -> str:
    d = profile.drives
    mood_pct = max(0, min(100, int(mood_pct)))
    if mood_judge_enabled:
        v_tok = _valence_token(valence)
        a_tok = _arousal_token(valence, confidence)
    else:
        v_tok = "neutral"
        a_tok = "low"
    label_text = (mood_label or "").strip() or "—"
    primary = (d.mission.primary or "").strip() or "—"
    secondary = (d.mission.secondary or "").strip()
    horizon = escape((d.horizon or "scene").strip() or "scene")
    sec_block = (
        f"\n      <secondary>{escape(secondary)}</secondary>"
        if secondary
        else ""
    )
    inner = (
        f"""  <character_state>
    <mood mood_pct="{mood_pct}" valence="{v_tok}" arousal="{a_tok}">{escape(label_text)}</mood>
    <goals horizon="{horizon}">
      <primary>{escape(primary)}</primary>{sec_block}
    </goals>
  </character_state>"""
    )
    return (
        "<context>\n"
        '  <module name="character_state">\n'
        f"{inner}\n"
        "  </module>\n"
        "</context>"
    )


def append_character_state_to_user_content(
    user_content: str,
    *,
    profile: PsychologyProfileModel,
    mood_pct: int,
    mood_label: str | None,
    valence: float,
    confidence: float,
    mood_judge_enabled: bool,
) -> str:
    xml = build_character_state_context_xml(
        profile=profile,
        mood_pct=mood_pct,
        mood_label=mood_label,
        valence=valence,
        confidence=confidence,
        mood_judge_enabled=mood_judge_enabled,
    )
    return f"{user_content.rstrip()}\n\n{xml}"
