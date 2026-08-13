from __future__ import annotations


PAYMENT_METHOD_COLUMNS = [
    "event_id",
    "timestamp_utc",
    "transaction_type",
    "country",
    "ip_country",
    "jurisdiction",
    "currency",
    "local_currency",
    "amount",
    "app_type",
    "hour",
    "day_of_week",
    "is_weekend",
    "is_cross_border",
    "payment_type",
]


SUCCESS_COLUMNS = [
    "timestamp_utc",
    "transaction_type",
    "currency",
    "amount",
    "hour",
    "day_of_week",
    "is_weekend",
    "is_cross_border",
    "payment_code",
    "payment_type",
    "success",
]


ARRIVAL_COLUMNS = [
    "timestamp_utc",
    "transaction_type",
    "currency",
    "amount",
    "hour",
    "day_of_week",
    "is_weekend",
    "is_cross_border",
    "payment_code",
    "payment_type",
    "banking_hours_indicator",
    "arrival_duration_minutes",
]
