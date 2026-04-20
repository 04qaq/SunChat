"""包内 prompts 资源（支持 wheel / uvpacker 嵌入 zip）。"""
from __future__ import annotations

from importlib.resources import files


def read_prompt_text(*relative: str) -> str:
    """读取 ``sunchat/prompts/<relative>`` 下 UTF-8 文本。"""
    return files("sunchat").joinpath("prompts", *relative).read_text(encoding="utf-8")
