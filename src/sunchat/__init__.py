"""SunChat: FastAPI WebSocket chat service."""

__version__ = "0.1.0"


def main() -> None:
    import os

    import uvicorn

    host = os.environ.get("HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", "8000"))
    reload = os.environ.get("UVICORN_RELOAD", "").lower() in ("1", "true", "yes")
    uvicorn.run("sunchat.main:app", host=host, port=port, reload=reload)
