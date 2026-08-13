from __future__ import annotations
from dataclasses import dataclass

from paymind.api.schemas import EvaluateRequest, EvaluateResponse
from paymind.models.registry import ModelRegistry
from paymind.sdk import PayMind


@dataclass
class EvaluationService:
    sdk: PayMind

    @classmethod
    def from_registry(
        cls,
        registry: ModelRegistry | None = None,
        *,
        top_k: int = 5,
    ) -> "EvaluationService":
        loaded_registry = registry or ModelRegistry().load()
        return cls(PayMind(registry=loaded_registry))

    def evaluate(
        self,
        payload: EvaluateRequest | dict[str, object],
    ) -> EvaluateResponse:
        return self.sdk.evaluate(payload)
