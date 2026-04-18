# run.py
import os
import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parent / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

import uvicorn

if __name__ == "__main__":
    # 0.0.0.0：本机可用 localhost / 127.0.0.1，同网其它设备可用局域网 IP 访问
    host = os.environ.get("HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", "8000"))
    uvicorn.run("app.main:app", host=host, port=port, reload=True)
