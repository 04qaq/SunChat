import os
from pathlib import Path

from dotenv import load_dotenv
from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


def load_application_env() -> None:
    """
    将环境文件载入 os.environ。
    路径由环境变量 DOTENV_PATH 指定（默认 `.env`，相对当前工作目录）；便于跨平台与分发目录部署。
    """
    raw = os.environ.get("DOTENV_PATH", ".env")
    path = Path(raw).expanduser()
    if path.is_file():
        load_dotenv(path, encoding="utf-8")


load_application_env()


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file_encoding="utf-8",
        extra="ignore",
    )

    CHAT_WINDOW_SIZE: int = 15

    MOOD_USE_LLM_JUDGE: bool = True
    MOOD_JUDGE_MAX_MESSAGES: int = 12
    MOOD_JUDGE_TIMEOUT_S: float = 45.0

    MOOD_TRACE_ENABLED: bool = True
    MOOD_TRACE_DIR: str = "data/mood_trace"

    LLM_API_KEY: str = Field(
        ...,
        min_length=1,
        description="DeepSeek / OpenAI 兼容接口的 API Key",
    )
    LLM_MODEL: str = "deepseek-chat"
    LLM_BASE_URL: str = "https://api.deepseek.com"

    SESSION_STORAGE_PATH: str = Field(
        default="session_data",
        validation_alias=AliasChoices("SESSION_STORAGE_PATH", "SEESION_STORAGE_PATH"),
    )
    DATA_STORAGE_PATH: str = "data"

    SESSION_STORAGE_MODEL: str = "short"

    MBTI_INFER_TIMEOUT_S: float = 40.0
    MBTI_FOUNDATIONS_INFER_MAX_CHARS: int = 4500
    MBTI_MAIN_FOUNDATIONS_MAX_CHARS: int = 1200
    MBTI_PERSONA_MAX_CHARS: int = 2800
    MBTI_JUDGE_PERSONA_EXCERPT_CHARS: int = 420


settings = Settings()
