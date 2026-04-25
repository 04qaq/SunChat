# sunchat/main.py
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI, WebSocket
from fastapi.responses import HTMLResponse

from sunchat.api.ws import websocket_endpoint
from sunchat.web_resources import read_chat_html


@asynccontextmanager
async def _app_lifespan(app: FastAPI):
    # read=None：流式补全不限制单 chunk 间等待；connect/pool 仍设上限避免半开连接占满
    t = httpx.Timeout(connect=30.0, read=None, write=120.0, pool=10.0)
    limits = httpx.Limits(
        max_keepalive_connections=20, max_connections=100
    )
    async with httpx.AsyncClient(timeout=t, limits=limits) as client:
        app.state.llm_http_client = client
        yield


app = FastAPI(lifespan=_app_lifespan)


@app.get("/")
def chat_page():
    return HTMLResponse(read_chat_html())


@app.websocket("/ws")
async def ws(ws: WebSocket):
    await websocket_endpoint(ws)


@app.get("/health")
def health():
    return {"status": "ok"}
