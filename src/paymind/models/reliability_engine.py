from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pandas as pd

from paymind.features.builder import (
    build_success_features,
)
from paymind.models.candidate_generator import (
    Candidate,
)
from paymind.models.registry import (
    ModelRegistry,
)


@dataclass(frozen=True)
class ReliabilityResult:
    payment_method: str
    candidate_probability: float
    success_probability: float
    rank: int


class ReliabilityEngine:
    def __init__(
        self,
        registry: ModelRegistry,
    ) -> None:
        self.registry = registry

    def evaluate_candidate(
        self,
        transaction: dict[str, Any],
        candidate: Candidate,
    ) -> ReliabilityResult:

        model = (
            self.registry
            .get_success_model()
        )

        row = dict(transaction)

        row["payment_code"] = (
            candidate.payment_method
        )

        row["payment_type"] = (
            candidate.payment_method
        )

        features = build_success_features(
            row
        )

        X = pd.DataFrame(
            [features]
        )

        probability = float(
            model.predict_proba(X)[0][1]
        )

        return ReliabilityResult(
            payment_method=(
                candidate.payment_method
            ),
            candidate_probability=(
                candidate.probability
            ),
            success_probability=(
                probability
            ),
            rank=candidate.rank,
        )

    def evaluate(
        self,
        transaction: dict[str, Any],
        candidates: list[Candidate],
    ) -> list[ReliabilityResult]:

        return [
            self.evaluate_candidate(
                transaction,
                candidate,
            )
            for candidate in candidates
        ]