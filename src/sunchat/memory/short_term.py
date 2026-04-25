import json
import os
from dataclasses import asdict
from typing import List

from sunchat.models.message import Message


class ShortTermMemory:
    """
    按窗口保留最近若干轮 user/assistant，可选文件持久化（由配置决定路径与模式）。

    Args:
        session_id: 会话唯一标识，用于落盘文件名。
        data_storage_path: 存放 ``{session_id}.json`` 的根目录。
        chat_window_size: 保留的「轮数」；内部按条数记为 ``窗口×2``（user+assistant 各一条为一轮的一半）。
        session_storage_model: ``"file"`` 时读写磁盘；``"short"`` 时仅进程内。

    说明:
        不在这里拼 LLM 消息；只维护对话列表。不变量由调用方在 ``add`` 后保证最后一条
        角色与业务一致（如用户发言后为 ``user``）。
    """

    def __init__(
        self,
        session_id: str,
        *,
        data_storage_path: str,
        chat_window_size: int,
        session_storage_model: str,
    ) -> None:
        self._session_id = session_id
        self._data_storage_path = data_storage_path
        self._window = chat_window_size
        self._storage_model = session_storage_model
        self._messages: List[Message] = []
        self._load()

    @property
    def session_id(self) -> str:
        return self._session_id

    def add(self, message: Message) -> None:
        self._messages.append(message)
        max_messages = self._window * 2
        if len(self._messages) > max_messages:
            self._messages = self._messages[-max_messages:]
        self._save()

    def get(self) -> List[Message]:
        return self._messages

    def _file_path(self) -> str:
        return os.path.join(self._data_storage_path, f"{self._session_id}.json")

    def _save(self) -> None:
        if self._storage_model != "file":
            return
        os.makedirs(self._data_storage_path, exist_ok=True)
        with open(self._file_path(), "w", encoding="utf-8") as f:
            json.dump([asdict(m) for m in self._messages], f, ensure_ascii=False)

    def _load(self) -> None:
        if self._storage_model != "file":
            return
        try:
            with open(self._file_path(), "r", encoding="utf-8") as f:
                data = json.load(f)
                self._messages = [Message(**m) for m in data]
        except OSError:
            pass
