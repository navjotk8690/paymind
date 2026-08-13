# Connectors

PayMind is an open-source connector/library. A connector maps host-system fields into the canonical `EvaluateRequest` schema and then calls the SDK or API inside the user's own environment.

Connectors must not:

- execute payments
- persist raw transaction payloads by default
- expose proprietary training data

## Canonical request schema

```python
from paymind.api.schemas import EvaluateRequest

canonical = EvaluateRequest.model_validate(
    {
        "timestamp_utc": "2026-08-07T05:30:00Z",
        "transaction_type": "deposit",
        "currency": "AUD",
        "amount": 500.0,
        "hour": 5,
        "day_of_week": "Friday",
        "is_weekend": 0,
        "is_cross_border": 0,
    }
)
```

## Example host connector

```python
from paymind.api.schemas import EvaluateRequest


class ExampleHostConnector:
    def transform(self, payload: dict) -> EvaluateRequest:
        return EvaluateRequest.model_validate(
            {
                "timestamp_utc": payload["timestamp_utc"],
                "transaction_type": payload["transaction_type"],
                "currency": payload["currency"],
                "amount": payload["amount"],
                "hour": payload["hour"],
                "day_of_week": payload["day_of_week"],
                "is_weekend": payload.get("is_weekend", 0),
                "is_cross_border": payload.get("is_cross_border", 0),
            }
        )
```

## Built-in helpers

- `paymind.connectors.json_connector.JsonConnector`
- `paymind.connectors.csv_connector.CsvConnector`
- `paymind.connectors.synthetic.sample_evaluate_request`

`CsvConnector` only validates canonical JSON serialized into a `payload_json` column. It is not a public CSV training feature.
