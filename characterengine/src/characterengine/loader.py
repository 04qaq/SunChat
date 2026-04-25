from __future__ import annotations

from pathlib import Path

import yaml

from characterengine.models import PsychologyProfileModel


def load_psychology_profile_from_text(raw: str) -> PsychologyProfileModel:
    data = yaml.safe_load(raw) or {}
    profile = PsychologyProfileModel.model_validate(data)
    if profile.mbti.strategy == "fixed" and not (
        profile.mbti.type and len(profile.mbti.type.strip()) == 4
    ):
        raise ValueError(
            "mbti.strategy=fixed 时请在 YAML 中填写 mbti.type（四字母，如 INFP）；"
            "infer_once 可不填 type，由会话推断。"
        )
    return profile


def load_psychology_profile_from_path(path: Path | str) -> PsychologyProfileModel:
    p = Path(path)
    try:
        raw = p.read_text(encoding="utf-8")
    except OSError as e:
        raise FileNotFoundError(f"心理画像文件不存在: {p}") from e
    return load_psychology_profile_from_text(raw)
