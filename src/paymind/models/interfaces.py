from __future__ import annotations
from dataclasses import dataclass
from typing import Protocol, Sequence

@dataclass(frozen=True)
class ArrivalPrediction:
    p50_minutes: float
    p90_minutes: float

class PaymentTypeModel(Protocol):
    @property
    def version(self) -> str: ...
    def predict_probabilities(self, features: dict[str, object]) -> dict[str, float]: ...

class SuccessModel(Protocol):
    @property
    def version(self) -> str: ...
    def predict_probabilities(self, candidates: Sequence[dict[str, object]]) -> list[float]: ...

class ArrivalModel(Protocol):
    @property
    def version(self) -> str: ...
    def predict(self, candidates: Sequence[dict[str, object]]) -> list[ArrivalPrediction]: ...
