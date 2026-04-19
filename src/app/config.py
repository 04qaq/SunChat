from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# 项目根目录下的 .env（与 run.py 同级），便于 uv run 从根目录启动时加载
_ROOT = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=_ROOT / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    CHAT_WINDOW_SIZE: int = 15

    # 心情：评判 LLM 输出 valence→映射为 0～100 心情指数；主模型结合人设与 mood_injection.txt 演绎（无 EMA）
    MOOD_USE_LLM_JUDGE: bool = True
    MOOD_JUDGE_MAX_MESSAGES: int = 12
    MOOD_JUDGE_TIMEOUT_S: float = 45.0

    # 每轮将情感变化、注入主模型的情绪语境与助手全文写入 MOOD_TRACE_DIR（JSONL）
    MOOD_TRACE_ENABLED: bool = True
    MOOD_TRACE_DIR: str = "data/mood_trace"

    # 勿在代码中写真实密钥；本地复制 .env.example 为 .env 后填写
    LLM_API_KEY: str = Field(
        ...,
        min_length=1,
        description="DeepSeek / OpenAI 兼容接口的 API Key",
    )
    LLM_MODEL: str = "deepseek-chat"
    LLM_BASE_URL: str = "https://api.deepseek.com"

    SEESION_STORAGE_PATH: str = "session_data"
    DATA_STORAGE_PATH: str = "data"

    SESSION_STORAGE_MODEL: str = "short"

    # 心理引擎：性格(OCEAN)+行为逻辑(MBTI)+目标与需要(Drives)，见 prompts/psychology_profile.yaml
    PSYCHOLOGY_PROFILE_PATH: Path = _ROOT / "src" / "app" / "prompts" / "psychology_profile.yaml"
    MBTI_INFER_TIMEOUT_S: float = 40.0

    # 自研 MBTI 行为引擎目录（foundations.md + personas.yaml），非外部 skill 仓库
    MBTI_ENGINE_ROOT: Path = _ROOT / "src" / "app" / "prompts" / "mbti_engine"
    MBTI_FOUNDATIONS_INFER_MAX_CHARS: int = 4500
    MBTI_MAIN_FOUNDATIONS_MAX_CHARS: int = 1200
    MBTI_PERSONA_MAX_CHARS: int = 2800
    MBTI_JUDGE_PERSONA_EXCERPT_CHARS: int = 420


settings = Settings()
