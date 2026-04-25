# 历史导入路径；新代码请用 ``sunchat.infrastructure.llm``。
from sunchat.infrastructure.llm.httpx_backend import HttpxLlmCompletions, LlmClient

# 旧名称兼容
LLMClient = HttpxLlmCompletions

__all__ = ["HttpxLlmCompletions", "LLMClient", "LlmClient"]
