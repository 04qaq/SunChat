from __future__ import annotations

import yaml

from sunchat.prompt_resources import read_prompt_text
from sunchat.psychology.models import PsychologyProfileModel


def load_psychology_profile() -> PsychologyProfileModel:
    try:
        raw = read_prompt_text("psychology_profile.yaml")
    except OSError as e:
        raise FileNotFoundError(
            "心理引擎配置不存在: sunchat_prompts/psychology_profile.yaml"
        ) from e
    data = yaml.safe_load(raw) or {}
    profile = PsychologyProfileModel.model_validate(data)
    if profile.mbti.strategy == "fixed" and not (
        profile.mbti.type and len(profile.mbti.type.strip()) == 4
    ):
        raise ValueError(
            "mbti.strategy=fixed 时请在 YAML 中填写 mbti.type（四字母，如 INFP）；"
            "infer_once 可不填 type，由连接时推断。"
        )
    return profile
