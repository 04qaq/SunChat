# SunChat

基于 **FastAPI + WebSocket** 的流式对话服务：支持 DeepSeek（OpenAI 兼容）接口、短期对话记忆与简单情绪状态，浏览器打开首页即可聊天。

## 功能概览

- **流式回复**：SSE 解析后通过 WebSocket 逐段推送，前端实时展示。
- **短期记忆**：按配置窗口保留最近若干轮 `user` / `assistant` 消息（可选文件持久化）。
- **情绪状态**：根据情感分数更新内部情绪值 \(E_t\)，并注入系统提示影响语气；前端可展示情绪数值。

## 环境要求

- Python **3.12+**
- 推荐使用 [**uv**](https://github.com/astral-sh/uv) 管理依赖

## 快速开始

### 1. 克隆仓库

```bash
git clone https://github.com/04qaq/SunChat.git
cd SunChat
```

### 2. 配置 API Key

```bash
cp .env.example .env
```

编辑 `.env`，将 `LLM_API_KEY` 设为你在 [DeepSeek 开放平台](https://platform.deepseek.com/) 申请的密钥（勿将 `.env` 提交到 Git）。

### 3. 安装依赖并启动

```bash
uv sync
uv run python run.py
```

默认监听 **http://127.0.0.1:8000**。

### 4. 使用浏览器聊天

在浏览器打开：**http://127.0.0.1:8000/**

健康检查：**http://127.0.0.1:8000/health**

## WebSocket 协议（摘要）

连接：`ws://127.0.0.1:8000/ws`（可选查询参数 `session_id` 复用会话）。

- 客户端发送：`{"type": "chat", "content": "用户消息"}`
- 服务端推送：`session`（会话 id）、`emotion`（情绪）、`token`（增量文本）、`done`（本轮结束）

## 项目结构（节选）

```text
run.py                 # 启动入口（将 src 加入 Python 路径）
src/app/
  main.py              # FastAPI 路由与静态聊天页
  api/ws.py            # WebSocket 会话、记忆与情绪
  llm/client.py        # DeepSeek 流式调用
  memory/short_term.py # 短期记忆
  emtion/              # 情感与情绪映射
  static/chat.html     # 极简聊天前端
```

## 许可证

MIT（若需更换请自行修改本文件。）
