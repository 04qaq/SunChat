"""心理引擎数据模型：性格（OCEAN）、行为逻辑（MBTI）、目标与需要（Drives，可扩展）。"""
from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class OceanModel(BaseModel):
    openness: float = Field(ge=0.0, le=1.0)
    conscientiousness: float = Field(ge=0.0, le=1.0)
    extraversion: float = Field(ge=0.0, le=1.0)
    agreeableness: float = Field(ge=0.0, le=1.0)
    emotional_stability: float = Field(ge=0.0, le=1.0)


class RoleModel(BaseModel):
    name: str = ""
    name_reading: str = ""
    role_summary: str = ""


class MBTIModel(BaseModel):
    """行为逻辑层：固定类型或会话启动时推断一次。"""

    model_config = ConfigDict(extra="allow")

    strategy: Literal["fixed", "infer_once"] = "fixed"
    type: str | None = None
    """四字母，如 INFP；strategy=fixed 时必填（或由 infer 覆盖）。"""
    notes: str = ""
    """可选：对该类型在扮演中的补充说明。"""


class DriveMissionModel(BaseModel):
    """主目标；后续可增量子字段，勿删 extra。"""

    model_config = ConfigDict(extra="allow")

    primary: str = ""
    narrative: str = ""


class DrivesModel(BaseModel):
    """
    目标与需要（Drives）：当前可写死文案，预留扩展面。

    - mission：主指令叙事
    - needs：结构化需要列表（如 affiliation / competence），随产品迭代
    - extensions：任意键值，供插件或后续版本读取（如 quests、flags）
    """

    model_config = ConfigDict(extra="allow")

    schema_version: int = Field(1, description="配置模式版本，便于迁移")
    mission: DriveMissionModel = Field(default_factory=DriveMissionModel)
    needs: list[dict[str, Any]] = Field(default_factory=list)
    extensions: dict[str, Any] = Field(default_factory=dict)


class PsychologyProfileModel(BaseModel):
    """单文件心理画像（psychology_profile.yaml）根模型。"""

    model_config = ConfigDict(extra="allow")

    role: RoleModel = Field(default_factory=RoleModel)
    ocean: OceanModel
    ocean_notes: dict[str, str] = Field(default_factory=dict)
    behavior_hints: list[str] = Field(default_factory=list)
    scenario: dict[str, str] = Field(default_factory=dict)
    relationship: dict[str, str] = Field(default_factory=dict)
    mbti: MBTIModel = Field(default_factory=MBTIModel)
    drives: DrivesModel = Field(default_factory=DrivesModel)
