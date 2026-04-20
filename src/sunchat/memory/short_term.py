import json
import os
from dataclasses import asdict
from typing import List

from sunchat.config import settings
from sunchat.models.message import Message


class ShortTermMemory:
    def __init__(self, session_id: str):
        self.session_id_ = session_id
        self.messages_: List[Message] = []
        self._load()

    def add(self, message: Message) -> None:
        self.messages_.append(message)
        if len(self.messages_) > settings.CHAT_WINDOW_SIZE * 2:
            self.messages_ = self.messages_[-settings.CHAT_WINDOW_SIZE * 2 :]
        self._save()

    def get(self) -> List[Message]:
        return self.messages_

    def _file_path(self) -> str:
        return os.path.join(settings.DATA_STORAGE_PATH, f"{self.session_id_}.json")

    def _save(self) -> None:
        if settings.SESSION_STORAGE_MODEL != "file":
            return
        os.makedirs(settings.DATA_STORAGE_PATH, exist_ok=True)
        with open(self._file_path(), "w", encoding="utf-8") as f:
            json.dump([asdict(m) for m in self.messages_], f, ensure_ascii=False)

    def _load(self) -> None:
        if settings.SESSION_STORAGE_MODEL != "file":
            return
        try:
            with open(self._file_path(), "r", encoding="utf-8") as f:
                data = json.load(f)
                self.messages_ = [Message(**m) for m in data]
        except OSError:
            pass
