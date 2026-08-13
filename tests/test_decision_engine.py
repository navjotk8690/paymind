from paymind.models.registry import ModelRegistry
from paymind.ranking.decision_engine import DecisionEngine


def test_decision_engine():

    registry = ModelRegistry().load()

    engine = DecisionEngine(
        registry,
        top_k=5,
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

    results = engine.evaluate(
        transaction
    )

    assert len(results) == 5

    assert results[0].rank == 1

    for index in range(
        len(results) - 1
    ):
        assert (
            results[index].final_score
            >=
            results[index + 1].final_score
        )

    for result in results:
        assert result.estimated_fee >= 0
        assert result.effective_fee_rate >= 0

        assert (
            0.0
            <= result.fee_score
            <= 1.0
        )


def test_decision_engine_respects_available_routes():
    registry = ModelRegistry().load()
    engine = DecisionEngine(
        registry,
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
        "available_payment_routes": ["checkout", "worldpay"],
    }

    results = engine.evaluate(transaction)

    assert results
    assert {result.payment_method for result in results} <= {"checkout", "worldpay"}


def test_decision_engine_returns_empty_when_no_routes_selected():
    registry = ModelRegistry().load()
    engine = DecisionEngine(
        registry,
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
        "available_payment_routes": [],
    }

    results = engine.evaluate(transaction)

    assert results == []
