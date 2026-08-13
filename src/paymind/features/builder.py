from __future__ import annotations

import math
from typing import Any

from paymind.runtime.transactions import normalize_transaction_context, parse_timestamp

PAYMENT_METHOD_FEATURES = [
    "transaction_type",
    "currency",
    "amount",
    "log_amount",
    "amount_bucket",
    "hour",
    "day_of_week",
    "month",
    "quarter",
    "is_weekend",
    "is_cross_border",
]


SUCCESS_FEATURES = [
    "transaction_type",
    "currency",
    "amount",
    "log_amount",
    "amount_bucket",
    "hour",
    "day_of_week",
    "month",
    "quarter",
    "is_weekend",
    "is_cross_border",
    "payment_code",
    "payment_type",
]


ARRIVAL_FEATURES = [
    "transaction_type",
    "currency",
    "amount",
    "log_amount",
    "amount_bucket",
    "hour",
    "day_of_week",
    "month",
    "quarter",
    "is_weekend",
    "is_cross_border",
    "payment_code",
    "payment_type",
    "banking_hours_indicator",
]


CATEGORICAL_FEATURES = {
    "payment_method": [
        "transaction_type",
        "currency",
        "amount_bucket",
        "day_of_week",
    ],

    "success": [
        "transaction_type",
        "currency",
        "amount_bucket",
        "day_of_week",
        "payment_code",
        "payment_type",
    ],

    "arrival": [
        "transaction_type",
        "currency",
        "amount_bucket",
        "day_of_week",
        "payment_code",
        "payment_type",
    ],
}
def amount_bucket(amount: float) -> str:
    if amount < 100:
        return "0_100"

    if amount < 500:
        return "100_500"

    if amount < 1_000:
        return "500_1000"

    if amount < 5_000:
        return "1000_5000"

    if amount < 10_000:
        return "5000_10000"

    if amount < 50_000:
        return "10000_50000"

    return "50000_plus"


def normalize_currency(value: Any) -> str:
    if value is None:
        return "UNKNOWN"

    text = str(value).strip().upper()

    if not text:
        return "UNKNOWN"

    return text


def normalize_category(value: Any) -> str:
    if value is None:
        return "unknown"

    text = str(value).strip().lower()

    if not text:
        return "unknown"

    return text


def common_features(row: dict[str, Any]) -> dict[str, Any]:
    normalized = normalize_transaction_context(row)
    timestamp = parse_timestamp(normalized["timestamp_utc"])
    amount = float(normalized["amount"])

    return {
        "transaction_type":
            normalize_category(
                normalized.get("transaction_type")
            ),

        "currency":
            normalize_currency(
                normalized.get("currency")
            ),

        "amount":
            amount,

        "log_amount":
            math.log1p(amount),

        "amount_bucket":
            amount_bucket(amount),

        "hour":
            int(normalized["hour"]),

        "day_of_week":
            str(normalized["day_of_week"]),

        "month":
            timestamp.month,

        "quarter":
            ((timestamp.month - 1) // 3) + 1,

        "is_weekend":
            int(normalized["is_weekend"]),

        "is_cross_border":
            int(normalized["is_cross_border"]),
    }


def build_payment_method_features(
    row: dict[str, Any],
) -> dict[str, Any]:

    features = common_features(row)

    return {
        name: features[name]
        for name in PAYMENT_METHOD_FEATURES
    }


def build_success_features(
    row: dict[str, Any],
) -> dict[str, Any]:

    features = common_features(row)

    features.update(
        {
            "payment_code":
                normalize_category(
                    row.get("payment_code")
                ),

            "payment_type":
                normalize_category(
                    row.get("payment_type")
                ),
        }
    )

    return {
        name: features[name]
        for name in SUCCESS_FEATURES
    }


def build_arrival_features(
    row: dict[str, Any],
) -> dict[str, Any]:

    features = common_features(row)

    features.update(
        {
            "payment_code":
                normalize_category(
                    row.get("payment_code")
                ),

            "payment_type":
                normalize_category(
                    row.get("payment_type")
                ),

            "banking_hours_indicator":
                int(
                    row.get(
                        "banking_hours_indicator",
                        0,
                    )
                ),
        }
    )

    return {
        name: features[name]
        for name in ARRIVAL_FEATURES
    }


def get_feature_names(
    model_name: str,
) -> list[str]:

    if model_name == "payment_method":
        return PAYMENT_METHOD_FEATURES

    if model_name == "success":
        return SUCCESS_FEATURES

    if model_name == "arrival":
        return ARRIVAL_FEATURES

    raise ValueError(
        f"Unknown model: {model_name}"
    )


def get_categorical_features(
    model_name: str,
) -> list[str]:

    if model_name not in CATEGORICAL_FEATURES:
        raise ValueError(
            f"Unknown model: {model_name}"
        )

    return CATEGORICAL_FEATURES[
        model_name
    ]
