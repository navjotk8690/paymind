from __future__ import annotations

import json
import logging
from dataclasses import dataclass


LOGGER = logging.getLogger("paymind")


@dataclass(frozen=True)
class SafeEvent:
    event: str
    request_id_hash: str
    latency_ms: float
    status: str
    model_versions: dict[str, str]


def configure_logging() -> None:
    if LOGGER.handlers:
        return
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(message)s"))
    LOGGER.addHandler(handler)
    LOGGER.setLevel(logging.INFO)


def log_safe_event(event: SafeEvent) -> None:
    LOGGER.info(json.dumps(event.__dict__, sort_keys=True))
