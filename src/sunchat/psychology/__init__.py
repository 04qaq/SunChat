"""SunChat 集成：心理引擎逻辑来自独立包 `characterengine`；此处仅再导出并保留应用内加载器。"""

from characterengine import (
    CharacterEngineConfig,
    append_character_state_to_user_content,
    big_five_to_behavior_cues,
    build_character_state_context_xml,
    build_psychology_system_message,
    infer_mbti_once,
    judge_character_context_json,
    load_psychology_profile_from_text,
    neuroticism_score,
    PsychologyProfileModel,
)
from sunchat.psychology.loader import load_psychology_profile

__all__ = [
    "CharacterEngineConfig",
    "PsychologyProfileModel",
    "append_character_state_to_user_content",
    "big_five_to_behavior_cues",
    "build_character_state_context_xml",
    "build_psychology_system_message",
    "infer_mbti_once",
    "judge_character_context_json",
    "load_psychology_profile",
    "load_psychology_profile_from_text",
    "neuroticism_score",
]
