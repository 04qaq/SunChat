from __future__ import annotations

from characterengine.loader import load_psychology_profile_from_text
from characterengine.models import PsychologyProfileModel
from sunchat.prompt_resources import read_prompt_text


def load_psychology_profile() -> PsychologyProfileModel:
    try:
        raw = read_prompt_text("psychology_profile.yaml")
    except OSError as e:
        raise FileNotFoundError(
            "心理引擎配置不存在: sunchat/prompts/psychology_profile.yaml"
        ) from e
    return load_psychology_profile_from_text(raw)
