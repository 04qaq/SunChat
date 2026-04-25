# Character Engine

可单独发布的 **角色心理层**：Big Five（OCEAN）结构化画像、MBTI 行为规格（`foundations.md` + `personas.yaml`）、目标（drives）、评判用 `CHARACTER_JSON`、以及末条用户消息可挂载的 `character_state` XML。

与具体聊天框架解耦：只需提供 YAML 画像文本、可选的 LLM 客户端（用于 `infer_once` MBTI），即可拼装 system 补充段与动态上下文。

## 安装

```bash
pip install characterengine
```

或从本仓库根目录以可编辑模式安装：

```bash
pip install -e ./characterengine
```

## 依赖

- Python 3.12+
- `pydantic`, `pyyaml`

## 快速用法

```python
from pathlib import Path
from characterengine import (
    CharacterEngineConfig,
    build_psychology_system_message,
    judge_character_context_json,
    load_psychology_profile_from_path,
)

profile = load_psychology_profile_from_path(Path("psychology_profile.yaml"))
cfg = CharacterEngineConfig()
text = build_psychology_system_message(
    profile, "ENFP", "", config=cfg
)
judge_blob = judge_character_context_json(profile, "ENFP", "", config=cfg)
```

资源默认从包内 `characterengine.resources` 读取；可参考同目录下的 `psychology_profile.example.yaml` 编写画像。

## 许可证

MIT
