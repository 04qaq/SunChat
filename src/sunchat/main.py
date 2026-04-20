# app/main.py
from functools import lru_cache
from importlib.resources import files

from fastapi import FastAPI, WebSocket
from fastapi.responses import HTMLResponse

from sunchat.api.ws import websocket_endpoint

app = FastAPI()


@lru_cache(maxsize=1)
def _chat_html() -> str:
    return files("sunchat").joinpath("static", "chat.html").read_text(encoding="utf-8")


@app.get("/")
def chat_page():
    return HTMLResponse(_chat_html())


@app.websocket("/ws")
async def ws(ws: WebSocket):
    await websocket_endpoint(ws)


@app.get("/health")
def health():
    return {"status": "ok"}