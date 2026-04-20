# sunchat/main.py
from fastapi import FastAPI, WebSocket
from fastapi.responses import HTMLResponse

from sunchat.api.ws import websocket_endpoint
from sunchat.web_resources import read_chat_html

app = FastAPI()


@app.get("/")
def chat_page():
    return HTMLResponse(read_chat_html())


@app.websocket("/ws")
async def ws(ws: WebSocket):
    await websocket_endpoint(ws)


@app.get("/health")
def health():
    return {"status": "ok"}