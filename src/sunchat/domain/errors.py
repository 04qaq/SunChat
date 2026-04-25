"""可映射到 WebSocket 用户可见 `error` 消息的领域异常。"""


class UserFacingError(Exception):
    """
    表示「可对用户展示的失败」。

    Attributes:
        public_message: 推送给前端的 `message` 文本（应简短、无内部路径与堆栈）。

    说明:
        与裸 ``Exception`` 相比，本类显式表达「可安全外显」；未捕获的其它异常
        仍经统一 errhandler 记日志并外显泛化提示。
    """

    __slots__ = ("public_message",)

    def __init__(self, public_message: str) -> None:
        self.public_message = public_message
        super().__init__(public_message)
