from paymind.models.registry import (
    ModelRegistry,
)
from paymind.models.candidate_generator import (
    CandidateGenerator,
)


def test_candidate_generator():

    registry = (
        ModelRegistry()
        .load()
    )

    generator = CandidateGenerator(
        registry=registry,
        top_k=3,
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

    assert len(candidates) == 3

    assert (
        candidates[0].probability
        >= candidates[1].probability
    )

    assert (
        candidates[1].probability
        >= candidates[2].probability
    )

    assert candidates[0].rank == 1
    assert candidates[1].rank == 2
    assert candidates[2].rank == 3


def test_candidate_generator_filters_unavailable_routes():
    registry = ModelRegistry().load()
    generator = CandidateGenerator(
        registry=registry,
        top_k=5,
    )

    transaction = {
        "timestamp_utc": "2026-08-07 05:30:00",
        "transaction_type": "deposit",
        "currency": "AUD",
        "amount": 500,
        "country": "AU",
        "ip_country": "AU",
        "app_type": "web_checkout",
        "available_payment_routes": ["worldpay"],
    }

    candidates = generator.generate(transaction)

    assert len(candidates) == 1
    assert candidates[0].payment_method == "worldpay"
