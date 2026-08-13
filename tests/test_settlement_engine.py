from paymind.models.registry import (
    ModelRegistry,
)
from paymind.models.candidate_generator import (
    CandidateGenerator,
)
from paymind.models.reliability_engine import (
    ReliabilityEngine,
)
from paymind.models.settlement_engine import (
    SettlementEngine,
)


def test_settlement_engine():

    registry = ModelRegistry().load()

    generator = CandidateGenerator(
        registry,
        top_k=3,
    )

    reliability = ReliabilityEngine(
        registry
    )

    settlement = SettlementEngine(
        registry
    )

    transaction = {
        "timestamp_utc":
            "2026-08-07 05:30:00",

        "transaction_type":
            "deposit",

        "currency":
            "AUD",

        "amount":
            500,

        "hour":
            5,

        "day_of_week":
            "Friday",

        "is_weekend":
            0,

        "is_cross_border":
            0,
    }

    candidates = generator.generate(
        transaction
    )

    reliability_results = (
        reliability.evaluate(
            transaction,
            candidates,
        )
    )

    settlement_results = (
        settlement.evaluate(
            transaction,
            reliability_results,
        )
    )

    assert len(
        settlement_results
    ) == 3

    for result in settlement_results:
        assert (
            result.arrival_p50_minutes
            >= 0
        )

        assert (
            result.arrival_p90_minutes
            >= result.arrival_p50_minutes
        )