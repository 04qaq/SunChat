# run.py — 开发时可直接 python run.py（将 src 加入路径）；默认开启热重载
import os
import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parent / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

os.environ.setdefault("UVICORN_RELOAD", "1")

from sunchat import main

if __name__ == "__main__":
    main()
