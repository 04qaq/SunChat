from app.config import settings


class EmotionState:
    def __init__(self) -> None:
        self.e: float = 0.0

    def update(self, s_new: float) -> float:
        gamma = settings.EMOTTION_GAMMA
        self.e = self.e * gamma + s_new * (1.0 - gamma)
        return self.e


class EmotionMapper:
    @staticmethod
    def style_for_e(e: float) -> str:
        if e > 0.5:
            return "【情绪语境】你当前心情偏愉快；回答时语气可以轻快、乐于助人。"
        if e < -0.5:
            return "【情绪语境】你当前心情偏冷淡；回答可以简短、略带距离感。"
        return "【情绪语境】你当前心情平和；保持自然、专业的语气。"
