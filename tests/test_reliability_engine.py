from paymind.models.registry import (
    ModelRegistry,
)
from paymind.models.candidate_generator import (
    CandidateGenerator,
)
from paymind.models.reliability_engine import (
    ReliabilityEngine,
)


def test_reliability_engine():

    registry = ModelRegistry().load()

    generator = CandidateGenerator(
        registry,
        top_k=3,
    )

    reliability = ReliabilityEngine(
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

    results = reliability.evaluate(
        transaction,
        candidates,
    )

    assert len(results) == 3

    for result in results:
        assert (
            0.0
            <= result.success_probability
            <= 1.0
        )