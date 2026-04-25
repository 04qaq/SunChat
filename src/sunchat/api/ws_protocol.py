"""WebSocket 客户端与服务端共用的协议版本（高优先级：便于桌面/网页一致演进）。"""

#  bump 当消息形状不兼容时（客户端须能读旧版或提示升级）
WS_PROTOCOL_NAME = "sunchat-ws"
WS_PROTOCOL_VERSION = "1"
