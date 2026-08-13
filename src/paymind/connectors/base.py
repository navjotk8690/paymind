from __future__ import annotations

from typing import Protocol

from paymind.api.schemas import EvaluateRequest


class Connector(Protocol):
    def transform(self, payload: dict[str, object]) -> EvaluateRequest: ...
