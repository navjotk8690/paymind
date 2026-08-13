from paymind.api.schemas import EvaluateRequest


class ExampleHostConnector:
    """Example only: map your host fields to the canonical PayMind contract."""

    def transform(self, payload: dict) -> EvaluateRequest:
        canonical = {
            "timestamp_utc": payload["timestamp_utc"],
            "transaction_type": payload["type"],
            "currency": payload["currency"],
            "amount": payload["amount"],
            "hour": payload["hour"],
            "day_of_week": payload["day_of_week"],
            "is_weekend": payload.get("is_weekend", 0),
            "is_cross_border": payload.get("is_cross_border", 0),
        }
        return EvaluateRequest.model_validate(canonical)
