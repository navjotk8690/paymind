from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pandas as pd

from paymind.features.builder import (
    build_arrival_features,
)
from paymind.models.reliability_engine import (
    ReliabilityResult,
)
from paymind.models.registry import (
    ModelRegistry,
)


@dataclass(frozen=True)
class SettlementResult:
    payment_method: str
    candidate_probability: float
    success_probability: float
    arrival_p50_minutes: float
    arrival_p90_minutes: float
    rank: int


class SettlementEngine:
    def __init__(
        self,
        registry: ModelRegistry,
    ) -> None:
        self.registry = registry

    def evaluate_candidate(
        self,
        transaction: dict[str, Any],
        result: ReliabilityResult,
    ) -> SettlementResult:

        p50_model, p90_model = (
            self.registry
            .get_arrival_models()
        )

        row = dict(transaction)

        row["payment_code"] = (
            result.payment_method
        )

        row["payment_type"] = (
            result.payment_method
        )

        # Temporary default until a connector
        # supplies a more precise value.
        if "banking_hours_indicator" not in row:
            hour = int(row.get("hour", 0))
            is_weekend = int(
                row.get(
                    "is_weekend",
                    0,
                )
            )

            row[
                "banking_hours_indicator"
            ] = int(
                9 <= hour <= 16
                and is_weekend == 0
            )

        features = build_arrival_features(
            row
        )

        X = pd.DataFrame(
            [features]
        )

        p50 = float(
            p50_model.predict(X)[0]
        )

        p90 = float(
            p90_model.predict(X)[0]
        )

        # Arrival cannot be negative.
        p50 = max(
            0.0,
            p50,
        )

        p90 = max(
            0.0,
            p90,
        )

        # Protect against quantile crossing.
        if p90 < p50:
            p90 = p50

        return SettlementResult(
            payment_method=(
                result.payment_method
            ),
            candidate_probability=(
                result.candidate_probability
            ),
            success_probability=(
                result.success_probability
            ),
            arrival_p50_minutes=p50,
            arrival_p90_minutes=p90,
            rank=result.rank,
        )

    def evaluate(
        self,
        transaction: dict[str, Any],
        reliability_results: list[
            ReliabilityResult
        ],
    ) -> list[SettlementResult]:

        return [
            self.evaluate_candidate(
                transaction,
                result,
            )
            for result
            in reliability_results
        ]