from sunchat.prompt_resources import read_prompt_text


def build_mood_prompt_injection(mood_pct: int, label: str | None) -> str:
    """
    将当前心情指数（0～100）与可选概要交给主模型，由模型结合人设自行演绎，
    不再使用固定三档文案或 EMA 数值状态机。
    """
    mood_pct = max(0, min(100, int(mood_pct)))
    template = read_prompt_text("mood_injection.txt")
    if label and label.strip():
        label_line = f"- 本轮心情概要：{label.strip()}\n"
    else:
        label_line = ""
    return (
        template.replace("{{MOOD_PCT}}", str(mood_pct))
        .replace("{{LABEL_LINE}}", label_line)
        .strip()
    )
