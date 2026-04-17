# app/main.py
from pathlib import Path

from fastapi import FastAPI, WebSocket
from fastapi.responses import FileResponse

from app.api.ws import websocket_endpoint

_STATIC = Path(__file__).resolve().parent / "static"

app = FastAPI()


@app.get("/")
def chat_page():
    return FileResponse(_STATIC / "chat.html")


@app.websocket("/ws")
async def ws(ws: WebSocket):
    await websocket_endpoint(ws)


@app.get("/health")
def health():
    return {"status": "ok"}