from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pandas as pd

from paymind.features.builder import (
    build_payment_method_features,
)
from paymind.models.registry import (
    ModelRegistry,
)
from paymind.runtime.transactions import route_is_available_for_transaction


@dataclass(frozen=True)
class Candidate:
    payment_method: str
    probability: float
    rank: int


class CandidateGenerator:
    def __init__(
        self,
        registry: ModelRegistry,
        top_k: int = 5,
    ) -> None:
        self.registry = registry
        self.top_k = top_k

    def generate(
        self,
        transaction: dict[str, Any],
    ) -> list[Candidate]:

        model = (
            self.registry
            .get_payment_method_model()
        )

        features = (
            build_payment_method_features(
                transaction
            )
        )

        X = pd.DataFrame(
            [features]
        )

        probabilities = (
            model.predict_proba(X)[0]
        )

        classes = list(
            model.classes_
        )

        ranked = sorted(
            zip(
                classes,
                probabilities,
            ),
            key=lambda item: item[1],
            reverse=True,
        )

        ranked = [
            item
            for item in ranked
            if route_is_available_for_transaction(str(item[0]), transaction)
        ]

        candidates = []

        for rank, (
            payment_method,
            probability,
        ) in enumerate(
            ranked[:self.top_k],
            start=1,
        ):

            candidates.append(
                Candidate(
                    payment_method=str(
                        payment_method
                    ),
                    probability=float(
                        probability
                    ),
                    rank=rank,
                )
            )

        return candidates
