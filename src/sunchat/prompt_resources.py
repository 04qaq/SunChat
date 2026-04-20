"""通过 ``sunchat_prompts`` 资源包读取提示词（wheel / uvpacker 嵌入 zip）。"""
from __future__ import annotations

from importlib.resources import files


def read_prompt_text(*relative: str) -> str:
    """读取 ``sunchat_prompts`` 包内相对路径下的 UTF-8 文本。"""
    return files("sunchat_prompts").joinpath(*relative).read_text(encoding="utf-8")
