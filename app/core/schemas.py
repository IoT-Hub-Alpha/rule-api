from __future__ import annotations

from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class ActionConfig(BaseModel):
    type: Literal["notification", "stop_machine", "alert", "webhook", "command"]
    template_id: int | None = None
    machine_id: str | None = None
    url: str | None = None
    method: Literal["GET", "POST", "PUT", "PATCH", "DELETE"] = "POST"
    headers: dict[str, str] | None = None
    payload: dict[str, Any] | None = None
    command: str | None = None
    params: dict[str, Any] | None = None

    @model_validator(mode="after")
    def validate_shape(self) -> "ActionConfig":
        if self.type in {"notification", "alert"} and self.template_id is None:
            raise ValueError(f"{self.type} action must include template_id")
        if self.type == "webhook" and not self.url:
            raise ValueError("webhook action must include url")
        if self.type == "command" and not self.command:
            raise ValueError("command action must include command")
        if self.type == "stop_machine" and not self.machine_id:
            raise ValueError("stop_machine action must include machine_id")
        return self


class Condition(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: Literal["leaf", "and", "or"]
    operator: Literal["gt", "gte", "lt", "lte", "eq", "ne"] | None = None
    threshold: float | None = None
    window_seconds: int | None = Field(default=None, ge=1)
    occurrences: int | None = Field(default=None, ge=1)
    conditions: list["Condition"] | None = None

    @model_validator(mode="after")
    def _validate_shape(self) -> "Condition":
        if self.type == "leaf":
            if self.conditions is not None:
                raise ValueError("leaf node cannot have conditions")
            if self.operator is None or self.threshold is None:
                raise ValueError("leaf node requires operator and threshold")
        else:
            if not self.conditions:
                raise ValueError(f"{self.type} node requires non-empty conditions")
            if self.operator is not None or self.threshold is not None:
                raise ValueError(f"{self.type} node cannot have operator/threshold")

        if (self.occurrences is None) != (self.window_seconds is None):
            raise ValueError("occurrences and window_seconds must be set together")

        return self


class RuleCreate(BaseModel):
    name: str
    description: str | None = None
    device_id: UUID
    condition: Condition
    action_config: list[ActionConfig]
    is_enabled: bool = True

    @field_validator("name")
    @classmethod
    def name_not_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Rule name cannot be blank")
        return v.strip()

    @field_validator("description")
    @classmethod
    def normalize_description(cls, v: str | None) -> str | None:
        if v is None:
            return None
        v = v.strip()
        return v or None


class RuleUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    device_id: UUID | None = None
    condition: Condition | None = None
    action_config: list[ActionConfig] | None = None
    is_enabled: bool | None = None

    @field_validator("name")
    @classmethod
    def name_not_blank(cls, v: str | None) -> str | None:
        if v is None:
            return None
        if not v.strip():
            raise ValueError("Rule name cannot be blank")
        return v.strip()

    @field_validator("description")
    @classmethod
    def normalize_description(cls, v: str | None) -> str | None:
        if v is None:
            return None
        v = v.strip()
        return v or None


class RuleOut(BaseModel):
    id: str
    device_id: str
    name: str
    description: str | None
    condition: dict[str, Any]
    action_config: list[dict[str, Any]]
    is_enabled: bool
    last_triggered_at: datetime | None
    event_cooldown_until: datetime | None
    created_at: datetime
    updated_at: datetime


class Pagination(BaseModel):
    page: int
    page_size: int
    total: int
    total_pages: int
    next_page: int | None
    prev_page: int | None


class RuleResponse(BaseModel):
    data: RuleOut


class RuleListResponse(BaseModel):
    data: list[RuleOut]
    pagination: Pagination


class RuleListSimpleResponse(BaseModel):
    data: list[RuleOut]
