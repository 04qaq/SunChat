# sunchat/api/ws.py
"""WebSocket 运输层：仅做依赖解析并委托用例层，不包含业务分支。"""

import logging

import httpx
from fastapi import WebSocket

from sunchat.application.ws_session import run_websocket_chat
from sunchat.config import settings

_logger = logging.getLogger(__name__)


async def websocket_endpoint(ws: WebSocket) -> None:
    """
    处理 ``/ws``：从 ``app.state`` 取得共享 ``httpx.AsyncClient`` 并进入聊天编排。

    Raises:
        RuntimeError: 当应用未通过 lifespan 注册 ``llm_http_client`` 时（启动配置错误）。

    说明:
        与协议相关的常量见 :mod:`sunchat.api.ws_protocol`；具体消息形状由
        :func:`sunchat.application.ws_session.run_websocket_chat` 维护。
    """
    client: httpx.AsyncClient | None = getattr(
        ws.app.state, "llm_http_client", None
    )
    if client is None:
        _logger.critical("app.state 缺少 llm_http_client，请检查 lifespan 配置")
        raise RuntimeError(
            "llm_http_client 未注册：请在创建 FastAPI 时绑定共享 httpx.AsyncClient 的 lifespan"
        )
    await run_websocket_chat(ws, httpx_client=client, settings=settings)
