from paymind.features.builder import (
    build_payment_method_features,
    build_success_features,
    build_arrival_features,
)


SAMPLE = {
    "timestamp_utc": "3/10/20 3:48",
    "transaction_type": "deposit",
    "currency": "aud",
    "amount": 1000,
    "hour": 3,
    "day_of_week": "Tuesday",
    "is_weekend": 0,
    "is_cross_border": 0,
    "payment_code": "mcb",
    "payment_type": "mcb",
    "banking_hours_indicator": 0,
}


def test_payment_method_features():
    result = build_payment_method_features(
        SAMPLE
    )

    assert result["currency"] == "AUD"
    assert result["month"] == 3
    assert result["quarter"] == 1
    assert result["amount_bucket"] == "1000_5000"


def test_success_features():
    result = build_success_features(
        SAMPLE
    )

    assert result["payment_code"] == "mcb"
    assert result["payment_type"] == "mcb"


def test_arrival_features():
    result = build_arrival_features(
        SAMPLE
    )

    assert result[
        "banking_hours_indicator"
    ] == 0