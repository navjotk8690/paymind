import json
from pathlib import Path

from paymind import PayMind


def test_sdk_evaluates_example():
    payload = json.loads(Path("examples/request.json").read_text())
    result = PayMind().evaluate(payload)

    assert result.recommendations
    assert result.recommendations[0].rank == 1
    assert result.recommendations[0].arrival_p90_minutes >= result.recommendations[0].arrival_p50_minutes
