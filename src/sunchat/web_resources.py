"""通过 ``sunchat.static`` 资源包读取网页等静态文件。"""
from __future__ import annotations

from functools import lru_cache
from importlib.resources import files


@lru_cache(maxsize=1)
def read_chat_html() -> str:
    return files("sunchat.static").joinpath("chat.html").read_text(encoding="utf-8")
