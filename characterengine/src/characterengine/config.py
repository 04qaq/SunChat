"""Limits and timeouts for MBTI resource embedding (no LLM keys)."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class CharacterEngineConfig:
    """Tune token budget for foundations/persona excerpts and MBTI infer timeout."""

    mbti_infer_timeout_s: float = 40.0
    mbti_foundations_infer_max_chars: int = 4500
    mbti_main_foundations_max_chars: int = 1200
    mbti_persona_max_chars: int = 2800
    mbti_judge_persona_excerpt_chars: int = 420
