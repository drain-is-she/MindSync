"""Shared integration contract v1. Coordinate changes with both developers."""
from datetime import datetime
from enum import Enum
from typing import Literal, Protocol
from pydantic import BaseModel, ConfigDict, Field, AwareDatetime, field_validator

class Contract(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)

class Mode(str, Enum):
    TEXT_ONLY = "text_only"
    CURRENT_VITALS = "current_vitals"
    FULL_CONTEXT = "full_context"

class VitalReading(Contract):
    profile_id: str = Field(min_length=1, max_length=100)
    measured_at: AwareDatetime
    heart_rate_bpm: float | None = Field(default=None, ge=20, le=250)
    spo2_percent: float | None = Field(default=None, ge=50, le=100)
    respiratory_rate_per_min: float | None = Field(default=None, ge=3, le=80)
    activity_level: float | None = Field(default=None, ge=0, le=1)
    simulated: bool = True

class HistorySummary(Contract):
    profile_id: str
    window_days: int = 7
    sample_count: int
    mean_heart_rate_bpm: float | None = None
    earlier_sleep_avg_hours: float | None = None
    recent_sleep_avg_hours: float | None = None
    missing_fraction: float = 0.0
    data_stale: bool = False
    simulated: bool = True

class ChatRequest(Contract):
    session_id: str = Field(min_length=1, max_length=100)
    profile_id: str = Field(min_length=1, max_length=100)
    message: str = Field(min_length=1, max_length=10000)
    mode: Mode
    consent_to_use_vitals: bool = False

    @field_validator("message", "session_id", "profile_id")
    @classmethod
    def nonblank(cls, value):
        if not value.strip():
            raise ValueError("Must not be blank")
        return value

class SourceRef(Contract):
    source_id: str
    chunk_id: str
    publisher: str
    title: str
    url: str
    section: str | None = None

class ToolEvent(Contract):
    name: str
    status: Literal["ok", "error", "blocked"]
    summary: str

class AgentOutput(Contract):
    reply: str
    sources: list[SourceRef] = Field(default_factory=list)
    tool_trace: list[ToolEvent] = Field(default_factory=list)
    simulated_data_used: bool = False

class ChatResponse(AgentOutput):
    mode: Mode
    safety_route: Literal["ordinary_support", "urgent_support"]
    latency_ms: int

class ContextProvider(Protocol):
    def get_current_vitals(self, profile_id: str) -> VitalReading | None: ...
    def get_history_summary(self, profile_id: str, days: int = 7) -> HistorySummary: ...
