from __future__ import annotations

from datetime import datetime, timezone

from paymind.api.schemas import EvaluateRequest


def sample_evaluate_request() -> EvaluateRequest:
    now = datetime.now(timezone.utc)
    return EvaluateRequest.model_validate(
        {
            "timestamp_utc": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "transaction_type": "deposit",
            "currency": "AUD",
            "amount": 500.0,
            "country": "AU",
            "ip_country": "AU",
            "app_type": "web_checkout",
            "available_payment_routes": ["stripe", "checkout", "worldpay", "paypal", "adyen"],
        }
    )
