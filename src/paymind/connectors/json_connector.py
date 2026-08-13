from __future__ import annotations

from paymind.api.schemas import EvaluateRequest


class JsonConnector:
    """Validates a canonical JSON payload without persisting or mutating it."""

    def transform(self, payload: dict[str, object]) -> EvaluateRequest:
        return EvaluateRequest.model_validate(payload)
