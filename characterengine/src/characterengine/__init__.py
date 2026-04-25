"""Character psychology engine: OCEAN, MBTI resources, drives, judge JSON, context XML."""

from characterengine.assemble import (
    append_character_state_to_user_content,
    build_character_state_context_xml,
    build_psychology_system_message,
    judge_character_context_json,
)
from characterengine.config import CharacterEngineConfig
from characterengine.cues import big_five_to_behavior_cues, neuroticism_score
from characterengine.infer import infer_mbti_once
from characterengine.loader import (
    load_psychology_profile_from_path,
    load_psychology_profile_from_text,
)
from characterengine.message import Message
from characterengine.models import (
    DriveMissionModel,
    DrivesModel,
    MBTIModel,
    OceanModel,
    PsychologyProfileModel,
    RoleModel,
)
from characterengine.mbti_resources import (
    format_persona_for_judge,
    format_persona_for_main,
    load_foundations_excerpt,
    optional_foundations_block_for_main,
)

__all__ = [
    "CharacterEngineConfig",
    "DriveMissionModel",
    "DrivesModel",
    "MBTIModel",
    "Message",
    "OceanModel",
    "PsychologyProfileModel",
    "RoleModel",
    "append_character_state_to_user_content",
    "big_five_to_behavior_cues",
    "build_character_state_context_xml",
    "build_psychology_system_message",
    "format_persona_for_judge",
    "format_persona_for_main",
    "infer_mbti_once",
    "judge_character_context_json",
    "load_foundations_excerpt",
    "load_psychology_profile_from_path",
    "load_psychology_profile_from_text",
    "neuroticism_score",
    "optional_foundations_block_for_main",
]

__version__ = "0.1.0"
