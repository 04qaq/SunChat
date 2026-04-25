# SunChat

基于 **FastAPI + WebSocket** 的流式对话服务：支持 DeepSeek（OpenAI 兼容）接口、短期对话记忆与简单情绪状态，浏览器打开首页即可聊天。

## 功能概览

- **流式回复**：SSE 解析后通过 WebSocket 逐段推送，前端实时展示。
- **短期记忆**：按配置窗口保留最近若干轮 `user` / `assistant` 消息（可选文件持久化）。
- **心理引擎**：独立 Python 包 [`characterengine`](characterengine/)（可单独 `pip install -e ./characterengine` 发布）；应用侧在 [`sunchat/prompts/psychology_profile.yaml`](src/sunchat/prompts/psychology_profile.yaml) 配置 **OCEAN**、**MBTI（`fixed` / `infer_once`）**、**drives**。MBTI 资源（`foundations.md`、`personas.yaml`）随 `characterengine` 分发；连接时推送 `psychology` 元数据。
- **心情与目标（动态层）**：每轮由评判模型结合 CHARACTER_JSON（含 Big Five 行为指令、`goals`、MBTI 节选等）输出 valence，映射为 **0～100** 的 `mood_pct`；与配置中的主/次目标、`horizon` 一并写入 **末条 user 消息** 末尾的 `<context><module name="character_state">...</module></context>` XML（无跨轮 EMA）。静态 system 中的心理引擎段含 **Big Five → 短行为指令**（不把原始小数写入主 prompt），并约定与 MBTI 冲突时以五维气质为准。

## 环境要求

- Python **3.12.x**（`pyproject.toml` 中 `requires-python = "==3.12.*"`，与 [uvpacker](https://github.com/touken928/uvpacker) 等打包工具对齐）
- 推荐使用 [**uv**](https://github.com/astral-sh/uv) 管理依赖

## Live2D 桌面客户端（可选）

仓库内 **[`desktop/`](desktop/)** 为 **Electron + electron-vite + Vue 3** 聊天窗（无边框可拖动顶栏，连接与后端相同的 WebSocket）。详见 [`desktop/README.md`](desktop/README.md)。**不要在仓库根目录直接执行 `npm run dev` 作为桌面依赖**；请先 **`cd desktop`** 安装依赖后 `npm run dev`，或在根目录执行 **`npm run dev:desktop`**。

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

开发时可直接使用 **`UVICORN_RELOAD=1 uv run sunchat`** 开启热重载。默认 `uv run sunchat` 不开启热重载。

环境变量由 **python-dotenv** 加载：默认读取当前工作目录下的 **`.env`**，或通过 **`DOTENV_PATH`** 指定任意路径（便于跨平台与分发目录）。

默认监听 **0.0.0.0:8000**（本机访问 **http://127.0.0.1:8000/**；可用环境变量 `HOST`、`PORT` 覆盖）。

### Windows 分发目录（uvpacker）

应用依赖本地包 **`characterengine`**（见仓库根目录 `characterengine/`）。打包或发布到 PyPI 时，请同时将 `characterengine` 作为依赖安装（例如先发布 `characterengine`，再在 `sunchat` 的依赖里写版本约束），或与当前仓库一样使用 **可编辑路径依赖** 一并拷贝源码树。

本项目 `pyproject.toml` 已满足 [uvpacker](https://github.com/touken928/uvpacker) 对目标项目的要求（`[build-system]`、`requires-python ==3.12.*`、`[project.scripts]` 入口 `sunchat`）。在任意装有 uv 的系统上可构建面向 **win_amd64** 的自包含目录：

```bash
uvx uvpacker build . -o path/to/output
```

产出目录内运行 **`sunchat.exe`** 前，请在运行目录放置 **`.env`**，或设置 **`DOTENV_PATH`** 指向你的环境文件。`sunchat/static`（页面）与 `sunchat/prompts`（提示词等）均随发行包通过 `importlib.resources` 加载，无需源码树中的 `src/` 路径。

### 4. 使用浏览器聊天

在浏览器打开：**http://127.0.0.1:8000/**

健康检查：**http://127.0.0.1:8000/health**

## WebSocket 协议（摘要）

连接：`ws://127.0.0.1:8000/ws`（可选查询参数 `session_id` 复用会话）。

- 客户端发送：`{"type": "chat", "content": "用户消息"}`
- 服务端推送：`session`（含 **`protocol.version`**、会话 id、`psychology`）、`emotion`（`mood_pct`、`label` 等）、`token`（增量文本）、`done`（本轮结束）、`error`（可选）

完整说明见 [`docs/WEBSOCKET_PROTOCOL.md`](docs/WEBSOCKET_PROTOCOL.md)。

## 项目结构（节选）

```text
pyproject.toml         # 依赖（含可编辑路径依赖 characterengine）、uv_build、sunchat 入口
characterengine/       # 可单独开源的心理层包（src/characterengine + 自带 MBTI 资源）
src/sunchat/
  __init__.py          # 包入口，导出 main（对应 sunchat = "sunchat:main"）
  __main__.py          # python -m sunchat
  main.py              # FastAPI 路由
  web_resources.py     # 经 importlib.resources 读取 sunchat/static
  prompt_resources.py  # 经 importlib.resources 读取 sunchat/prompts
  config.py            # 设置（python-dotenv + 环境变量）
  api/ws.py            # WebSocket 会话、记忆与情绪
  llm/client.py        # DeepSeek 流式调用
  memory/short_term.py # 短期记忆
  emotion/             # 心情评判与策略（Llm/Static）
  psychology/          # 从 prompts 加载 YAML，再导出 characterengine API
  prompts/             # system_base、judge、psychology_profile.yaml、character_traits.json 等
  static/              # 如 chat.html
```

## 测试

```bash
# Python（需 dev 依赖）
uv sync --extra dev
uv run pytest tests -q

# 桌面端（Vitest）
cd desktop && npm test
```

`tests/conftest.py` 会为 pytest 设置占位 `LLM_API_KEY` 等，**不会调用真实 LLM**。会话文件写入目录为 `tests/_test_session_data/`（已 gitignore）。

## 文档与配置说明
- 代码入口与行为说明可直接阅读：`src/sunchat/api/ws.py`（对话编排）、`src/sunchat/config.py`（环境变量）、`src/sunchat/prompts/`（人设与提示词资源包）。

## 许可证

MIT
