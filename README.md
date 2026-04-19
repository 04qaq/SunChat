# SunChat

基于 **FastAPI + WebSocket** 的流式对话服务：支持 DeepSeek（OpenAI 兼容）接口、短期对话记忆与简单情绪状态，浏览器打开首页即可聊天。

## 功能概览

- **流式回复**：SSE 解析后通过 WebSocket 逐段推送，前端实时展示。
- **短期记忆**：按配置窗口保留最近若干轮 `user` / `assistant` 消息（可选文件持久化）。
- **心理引擎**：`prompts/psychology_profile.yaml` 配置 **性格（OCEAN）**、**行为逻辑（MBTI `fixed` / `infer_once`）**、**目标与需要（drives）**；行为细则由自研 [`prompts/mbti_engine/`](src/app/prompts/mbti_engine/)（`foundations.md` + `personas.yaml`）注入主对话与心情评判（评判侧为节选 JSON）；连接时推送 `psychology` 元数据。
- **心情指数**：每轮由评判模型结合上述 CHARACTER 上下文与对话输出 valence，映射为 **0～100** 的 `mood_pct`，经 `mood_injection.txt` 注入主模型（无跨轮 EMA 累积）。

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

默认监听 **0.0.0.0:8000**（本机访问 **http://127.0.0.1:8000/**；可用环境变量 `HOST`、`PORT` 覆盖）。

### 4. 使用浏览器聊天

在浏览器打开：**http://127.0.0.1:8000/**

健康检查：**http://127.0.0.1:8000/health**

## WebSocket 协议（摘要）

连接：`ws://127.0.0.1:8000/ws`（可选查询参数 `session_id` 复用会话）。

- 客户端发送：`{"type": "chat", "content": "用户消息"}`
- 服务端推送：`session`（会话 id）、`emotion`（`mood_pct`、`label` 等）、`token`（增量文本）、`done`（本轮结束）、`error`（可选）

## 项目结构（节选）

```text
run.py                 # 启动入口（将 src 加入 Python 路径）
src/app/
  main.py              # FastAPI 路由与静态聊天页
  api/ws.py            # WebSocket 会话、记忆与情绪
  llm/client.py        # DeepSeek 流式调用
  memory/short_term.py # 短期记忆
  emtion/              # 心情评判与注入
  prompts/             # system_base、psychology_profile、judge、mood_injection、mbti_engine/
  mbti_engine/         # 自研 MBTI foundations + personas 加载
  psychology/          # 心理引擎加载与组装（可选保留 character_traits.json 作评判回退）
  static/chat.html     # 极简聊天前端
```

## 文档与配置说明

- **本仓库不包含** `doc/`（需求、开发说明、架构笔记等仅在本地维护，不随 Git 分发）。
- **密钥**：仅使用项目根目录 `.env`（从 `.env.example` 复制）；**切勿**提交 `.env` 或任何真实 API Key。
- 代码入口与行为说明可直接阅读：`src/app/api/ws.py`（对话编排）、`src/app/config.py`（环境变量）、`src/app/prompts/`（人设与提示词）。

## 许可证

MIT
