"""Big Five（OCEAN）→ 短行为指令。"""
from __future__ import annotations

from characterengine.models import OceanModel


def neuroticism_score(ocean: OceanModel) -> float:
    """神经质 ≈ 1 − 情绪稳定性（emotional_stability）。"""
    return max(0.0, min(1.0, 1.0 - ocean.emotional_stability))


def big_five_to_behavior_cues(ocean: OceanModel) -> str:
    n = neuroticism_score(ocean)
    cues: list[str] = []
    if ocean.extraversion < 0.35:
        cues.append("社交场合偏内敛；非必要不长篇独白。")
    if ocean.agreeableness > 0.65:
        cues.append("默认合作、少抬杠；拒绝时语气委婉。")
    if n > 0.6:
        cues.append("压力下反应：语速略快、多确认、易多想；不人身攻击。")
    if ocean.conscientiousness > 0.65:
        cues.append("回答较有条理，会主动收尾与确认下一步。")
    if ocean.openness > 0.65:
        cues.append("愿意接新话题与隐喻；避免僵化套话。")
    if ocean.extraversion >= 0.65:
        cues.append("互动偏外放时可主动延展话题，但仍尊重角色摘要中的关系边界。")
    if ocean.agreeableness < 0.35:
        cues.append("合作意愿偏低时可直接表态，避免为迎合而虚假附和。")
    if n < 0.35 and ocean.emotional_stability > 0.65:
        cues.append("情绪基底较稳：除非对话明确出现严重刺激，否则不宜动辄极端化反应。")
    if not cues:
        cues.append("气质维度接近中等：结合角色摘要与场景自然演绎，避免脸谱化。")
    return " ".join(cues)
