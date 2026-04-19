from __future__ import annotations

from pathlib import Path

import yaml

from app.config import settings
from app.psychology.models import PsychologyProfileModel


def load_psychology_profile() -> PsychologyProfileModel:
    path = settings.PSYCHOLOGY_PROFILE_PATH
    if not path.is_file():
        raise FileNotFoundError(f"心理引擎配置不存在: {path}")
    raw = path.read_text(encoding="utf-8")
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
