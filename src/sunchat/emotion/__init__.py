"""情绪分析、心情评判与策略（原 ``emtion`` 包，已正名为 ``emotion``）。"""

from sunchat.emotion.judge import (
    MoodJudgeResult,
    compute_mood_signal,
    load_judge_system_prompt,
)
from sunchat.emotion.strategies import LlmMoodStrategy, StaticMoodStrategy

__all__ = [
    "LlmMoodStrategy",
    "MoodJudgeResult",
    "StaticMoodStrategy",
    "compute_mood_signal",
    "load_judge_system_prompt",
]
