from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from paymind.fees.service import (
    FeeEvaluation,
    FeeService,
)
from paymind.models.candidate_generator import (
    CandidateGenerator,
)
from paymind.models.reliability_engine import (
    ReliabilityEngine,
)
from paymind.models.registry import (
    ModelRegistry,
)
from paymind.models.settlement_engine import (
    SettlementEngine,
)


@dataclass(frozen=True)
class RankedRecommendation:
    payment_method: str

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

    final_score: float
    rank: int

    reasons: list[str]


class DecisionEngine:
    def __init__(
        self,
        registry: ModelRegistry,
        top_k: int = 5,
        success_weight: float = 0.50,
        settlement_weight: float = 0.20,
        fee_weight: float = 0.20,
        candidate_weight: float = 0.10,
        fee_service: FeeService | None = None,
    ) -> None:

        self.registry = registry

        self.generator = CandidateGenerator(
            registry,
            top_k=top_k,
        )

        self.reliability = ReliabilityEngine(
            registry
        )

        self.settlement = SettlementEngine(
            registry
        )

        self.fees = (
            fee_service
            if fee_service is not None
            else FeeService()
        )

        self.success_weight = success_weight
        self.settlement_weight = settlement_weight
        self.fee_weight = fee_weight
        self.candidate_weight = candidate_weight

        total = (
            success_weight
            + settlement_weight
            + fee_weight
            + candidate_weight
        )

        if abs(total - 1.0) > 0.0001:
            raise ValueError(
                "Ranking weights must sum to 1.0"
            )

    def _settlement_score(
        self,
        p90_minutes: float,
    ) -> float:
        """
        Convert settlement time into a 0-1 score.

        Current V1 normalization:
        0 minutes  -> 1.0
        60+ min    -> 0.0

        Later this can be replaced with a
        configurable or route-aware function.
        """

        maximum_reference_minutes = 60.0

        normalized = min(
            max(
                p90_minutes
                / maximum_reference_minutes,
                0.0,
            ),
            1.0,
        )

        return 1.0 - normalized

    def _normalize_fee_scores(
        self,
        fees: dict[
            str,
            FeeEvaluation,
        ],
    ) -> dict[str, float]:
        """
        Convert absolute fees to relative scores.

        Cheapest candidate:
            1.0

        Most expensive candidate:
            0.0

        Candidates between those two receive
        proportional scores.
        """

        if not fees:
            return {}

        values = [
            result.total_fee
            for result in fees.values()
        ]

        minimum_fee = min(values)
        maximum_fee = max(values)

        # Every candidate has the same fee.
        if abs(
            maximum_fee - minimum_fee
        ) < 1e-12:
            return {
                method: 1.0
                for method in fees
            }

        scores = {}

        for method, result in fees.items():

            normalized = (
                result.total_fee
                - minimum_fee
            ) / (
                maximum_fee
                - minimum_fee
            )

            scores[method] = (
                1.0 - normalized
            )

        return scores

    def _reasons(
        self,
        success_probability: float,
        settlement_score: float,
        fee_score: float,
        candidate_probability: float,
    ) -> list[str]:

        reasons = []

        if success_probability >= 0.80:
            reasons.append(
                "HIGH_SUCCESS_PROBABILITY"
            )

        if settlement_score >= 0.90:
            reasons.append(
                "FAST_EXPECTED_SETTLEMENT"
            )

        if fee_score >= 0.90:
            reasons.append(
                "LOWEST_OR_COMPETITIVE_FEE"
            )

        if candidate_probability >= 0.30:
            reasons.append(
                "HIGH_CANDIDATE_RELEVANCE"
            )

        if not reasons:
            reasons.append(
                "BEST_AVAILABLE_COMBINED_SCORE"
            )

        return reasons

    def evaluate(
        self,
        transaction: dict[str, Any],
    ) -> list[RankedRecommendation]:

        # ----------------------------------------
        # 1. Generate candidate methods
        # ----------------------------------------

        candidates = self.generator.generate(
            transaction
        )

        # ----------------------------------------
        # 2. Predict reliability
        # ----------------------------------------

        reliability_results = (
            self.reliability.evaluate(
                transaction,
                candidates,
            )
        )

        # ----------------------------------------
        # 3. Predict settlement
        # ----------------------------------------

        settlement_results = (
            self.settlement.evaluate(
                transaction,
                reliability_results,
            )
        )

        # ----------------------------------------
        # 4. Calculate fees
        # ----------------------------------------

        fee_results: dict[
            str,
            FeeEvaluation,
        ] = {}

        for result in settlement_results:

            fee_results[
                result.payment_method
            ] = self.fees.evaluate(
                transaction,
                result.payment_method,
            )

        # ----------------------------------------
        # 5. Normalize fee scores
        # ----------------------------------------

        fee_scores = (
            self._normalize_fee_scores(
                fee_results
            )
        )

        # ----------------------------------------
        # 6. Score every candidate
        # ----------------------------------------

        scored = []

        for result in settlement_results:

            payment_method = (
                result.payment_method
            )

            fee_result = fee_results[
                payment_method
            ]

            fee_score = fee_scores[
                payment_method
            ]

            settlement_score = (
                self._settlement_score(
                    result.arrival_p90_minutes
                )
            )

            reliability_score = (
                result.success_probability
            )

            candidate_score = (
                result.candidate_probability
            )

            final_score = (
                reliability_score
                * self.success_weight

                + settlement_score
                * self.settlement_weight

                + fee_score
                * self.fee_weight

                + candidate_score
                * self.candidate_weight
            )

            scored.append(
                {
                    "payment_method":
                        payment_method,

                    "candidate_probability":
                        result.candidate_probability,

                    "success_probability":
                        result.success_probability,

                    "arrival_p50_minutes":
                        result.arrival_p50_minutes,

                    "arrival_p90_minutes":
                        result.arrival_p90_minutes,

                    "estimated_fee":
                        fee_result.total_fee,

                    "effective_fee_rate":
                        fee_result
                        .fee_percentage_of_amount,

                    "fee_score":
                        fee_score,

                    "settlement_score":
                        settlement_score,

                    "candidate_score":
                        candidate_score,

                    "reliability_score":
                        reliability_score,

                    "final_score":
                        final_score,

                    "reasons":
                        self._reasons(
                            result.success_probability,
                            settlement_score,
                            fee_score,
                            result.candidate_probability,
                        ),
                }
            )

        # ----------------------------------------
        # 7. Rank
        # ----------------------------------------

        scored.sort(
            key=lambda row: (
                row["final_score"]
            ),
            reverse=True,
        )

        recommendations = []

        for rank, row in enumerate(
            scored,
            start=1,
        ):

            recommendations.append(
                RankedRecommendation(
                    payment_method=
                        row["payment_method"],

                    candidate_probability=
                        row[
                            "candidate_probability"
                        ],

                    success_probability=
                        row[
                            "success_probability"
                        ],

                    arrival_p50_minutes=
                        row[
                            "arrival_p50_minutes"
                        ],

                    arrival_p90_minutes=
                        row[
                            "arrival_p90_minutes"
                        ],

                    estimated_fee=
                        row["estimated_fee"],

                    effective_fee_rate=
                        row[
                            "effective_fee_rate"
                        ],

                    fee_score=
                        row["fee_score"],

                    settlement_score=
                        row[
                            "settlement_score"
                        ],

                    candidate_score=
                        row["candidate_score"],

                    reliability_score=
                        row[
                            "reliability_score"
                        ],

                    final_score=
                        row["final_score"],

                    rank=rank,

                    reasons=
                        row["reasons"],
                )
            )

        return recommendations