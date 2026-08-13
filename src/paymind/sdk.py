from __future__ import annotations

from typing import Any

from paymind.api.schemas import (
    EvaluateRequest,
    EvaluateResponse,
    ModelsResponse,
    RecommendationResponse,
)
from paymind.models.registry import ModelRegistry
from paymind.ranking.decision_engine import DecisionEngine
from paymind.runtime.transactions import normalize_transaction_context


class PayMind:
    """
    Embeddable stateless PayMind SDK.

    Loads the registered models once and evaluates
    transactions through the PayMind decision engine.
    """

    def __init__(
        self,
        decision_engine: DecisionEngine | None = None,
        registry: ModelRegistry | None = None,
    ) -> None:
        self._registry = registry

        if decision_engine is not None:
            self._engine = decision_engine
            if self._registry is None:
                self._registry = getattr(decision_engine, "registry", None)
            return

        if registry is None:
            registry = ModelRegistry().load()

        self._registry = registry
        self._engine = DecisionEngine(registry=registry, top_k=5)

    def _build_response(
        self,
        results: list[Any],
    ) -> EvaluateResponse:
        recommendations = [
            RecommendationResponse(
                rank=result.rank,
                payment_method=result.payment_method,
                final_score=result.final_score,
                candidate_probability=result.candidate_probability,
                success_probability=result.success_probability,
                arrival_p50_minutes=result.arrival_p50_minutes,
                arrival_p90_minutes=result.arrival_p90_minutes,
                estimated_fee=result.estimated_fee,
                effective_fee_rate=result.effective_fee_rate,
                fee_score=result.fee_score,
                settlement_score=result.settlement_score,
                candidate_score=result.candidate_score,
                reliability_score=result.reliability_score,
                reasons=result.reasons,
            )
            for result in results
        ]
        return EvaluateResponse(recommendations=recommendations)

    def evaluate(
        self,
        payload: EvaluateRequest | dict,
    ) -> EvaluateResponse:

        request = (
            payload
            if isinstance(payload, EvaluateRequest)
            else EvaluateRequest.model_validate(payload)
        )

        transaction = normalize_transaction_context(
            request.model_dump(exclude_none=True)
        )

        results = self._engine.evaluate(transaction)
        return self._build_response(results)

    def models(self) -> ModelsResponse:
        if self._registry is None:
            raise RuntimeError("Model registry is unavailable.")
        return ModelsResponse.model_validate(self._registry.describe_models())

    def health(self) -> dict[str, Any]:
        if self._registry is None:
            return {"status": "ok", "models": {"loaded": True}}
        return {"status": "ok", "models": self._registry.status()}
