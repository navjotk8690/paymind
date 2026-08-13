from __future__ import annotations

from typing import Any
from typing import Literal

from pydantic import BaseModel, Field


class EvaluateRequest(BaseModel):
    timestamp_utc: str | None = None
    transaction_type: Literal["deposit", "withdrawal"] = "deposit"
    currency: str
    amount: float = Field(gt=0)
    country: str | None = None
    ip_country: str | None = None
    app_type: str | None = None
    jurisdiction: str | None = None
    local_currency: str | None = None
    available_payment_routes: list[str] | None = None
    hour: int | None = None
    day_of_week: str | None = None
    is_weekend: int | None = None
    is_cross_border: int | None = None
    banking_hours_indicator: int | None = None


class RecommendationResponse(BaseModel):
    rank: int
    payment_method: str

    final_score: float

    candidate_probability: float
    success_probability: float

    arrival_p50_minutes: float
    arrival_p90_minutes: float

    estimated_fee: float
    effective_fee_rate: float

    fee_score: float
    settlement_score: float
    candidate_score: float
    reliability_score: float

    reasons: list[str]


class EvaluateResponse(BaseModel):
    recommendations: list[RecommendationResponse]


class ModelSummaryResponse(BaseModel):
    key: str
    display_name: str
    version: str
    enabled: bool
    loaded: bool
    source: str
    mode: str
    metadata: dict[str, Any]


class ModelsResponse(BaseModel):
    registry_version: str
    disclaimer: str
    models: list[ModelSummaryResponse]


class HealthResponse(BaseModel):
    status: str
    models: dict[str, Any]
