"""领域级异常与（可选）不变量；与具体传输、存储、模型供应商无关。"""

from sunchat.domain.errors import UserFacingError

__all__ = ["UserFacingError"]
