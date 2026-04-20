# SunChat

基于 **FastAPI + WebSocket** 的流式对话服务：支持 DeepSeek（OpenAI 兼容）接口、短期对话记忆与简单情绪状态，浏览器打开首页即可聊天。

## 功能概览

- **流式回复**：SSE 解析后通过 WebSocket 逐段推送，前端实时展示。
- **短期记忆**：按配置窗口保留最近若干轮 `user` / `assistant` 消息（可选文件持久化）。
- **心理引擎**：独立资源包 [`sunchat_prompts`](src/sunchat_prompts/) 中 `psychology_profile.yaml` 配置 **性格（OCEAN）**、**行为逻辑（MBTI `fixed` / `infer_once`）**、**目标与需要（drives）**；行为细则由 [`sunchat_prompts/mbti_engine/`](src/sunchat_prompts/mbti_engine/)（`foundations.md` + `personas.yaml`）经 `importlib.resources` 注入主对话与心情评判（评判侧为节选 JSON）；连接时推送 `psychology` 元数据。
- **心情指数**：每轮由评判模型结合上述 CHARACTER 上下文与对话输出 valence，映射为 **0～100** 的 `mood_pct`，经 `mood_injection.txt` 注入主模型（无跨轮 EMA 累积）。

## 环境要求

- Python **3.12.x**（`pyproject.toml` 中 `requires-python = "==3.12.*"`，与 [uvpacker](https://github.com/touken928/uvpacker) 等打包工具对齐）
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
uv run sunchat
```

开发与热重载仍可使用 **`uv run python run.py`**（脚本会为当前进程设置 `UVICORN_RELOAD=1`）。仅 `uv run sunchat` 时默认不开启热重载；需要时可设置环境变量 `UVICORN_RELOAD=1`。

环境变量由 **python-dotenv** 加载：默认读取当前工作目录下的 **`.env`**，或通过 **`DOTENV_PATH`** 指定任意路径（便于跨平台与分发目录）。

默认监听 **0.0.0.0:8000**（本机访问 **http://127.0.0.1:8000/**；可用环境变量 `HOST`、`PORT` 覆盖）。

### Windows 分发目录（uvpacker）

本项目 `pyproject.toml` 已满足 [uvpacker](https://github.com/touken928/uvpacker) 对目标项目的要求（`[build-system]`、`requires-python ==3.12.*`、`[project.scripts]` 入口 `sunchat`）。在任意装有 uv 的系统上可构建面向 **win_amd64** 的自包含目录：

```bash
uvx uvpacker build . -o path/to/output
```

产出目录内运行 **`sunchat.exe`** 前，请在运行目录放置 **`.env`**，或设置 **`DOTENV_PATH`** 指向你的环境文件。`sunchat_static`（页面）与 `sunchat_prompts`（提示词等）均随发行包通过 `importlib.resources` 加载，无需源码树中的 `src/` 路径。

### 4. 使用浏览器聊天

在浏览器打开：**http://127.0.0.1:8000/**

健康检查：**http://127.0.0.1:8000/health**

## WebSocket 协议（摘要）

连接：`ws://127.0.0.1:8000/ws`（可选查询参数 `session_id` 复用会话）。

- 客户端发送：`{"type": "chat", "content": "用户消息"}`
- 服务端推送：`session`（会话 id）、`emotion`（`mood_pct`、`label` 等）、`token`（增量文本）、`done`（本轮结束）、`error`（可选）

## 项目结构（节选）

```text
run.py                 # 开发启动（src 路径 + 默认热重载）
pyproject.toml         # 依赖、uv_build 后端、脚本入口 sunchat（uvpacker 兼容）
src/sunchat/
  __init__.py          # 包入口，导出 main（对应 sunchat = "sunchat:main"）
  __main__.py          # python -m sunchat
  main.py              # FastAPI 路由
  web_resources.py     # 经 importlib.resources 读取 sunchat_static
  prompt_resources.py  # 经 importlib.resources 读取 sunchat_prompts
  config.py            # 设置（python-dotenv + 环境变量）
  api/ws.py            # WebSocket 会话、记忆与情绪
  llm/client.py        # DeepSeek 流式调用
  memory/short_term.py # 短期记忆
  emtion/              # 心情评判与注入
  mbti_engine/         # MBTI foundations + personas 加载（Python）
  psychology/          # 心理引擎加载与组装（可选保留 character_traits.json 作评判回退）
src/sunchat_prompts/   # 仅非 Python 资源 + __init__.py（提示词、YAML、JSON 等）
  mbti_engine/         # foundations.md、personas.yaml
src/sunchat_static/    # 仅非 Python 资源 + __init__.py（如 chat.html）
```

## 文档与配置说明
- 代码入口与行为说明可直接阅读：`src/sunchat/api/ws.py`（对话编排）、`src/sunchat/config.py`（环境变量）、`src/sunchat_prompts/`（人设与提示词资源包）。

## 许可证

MIT
