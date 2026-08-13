from __future__ import annotations

from typing import Any, Mapping

from paymind.fees.calculator import FeeResult
from paymind.features.request_features import build_request_features


def build_candidate_features(
    request: Mapping[str, Any],
    option: Mapping[str, Any],
    fee: FeeResult,
) -> dict[str, object]:
    return {
        **build_request_features(request),
        "payment_code": option.get("payment_code", ""),
        "payment_type": option.get("payment_type", ""),
        "position": int(option.get("position", 0)),
        "fee_percentage": float(option.get("fee_percentage", 0.0)),
        "fee_fixed": float(option.get("fee_fixed", 0.0)),
        "fx_markup_percentage": float(option.get("fx_markup_percentage", 0.0)),
        "minimum_amount": float(option.get("minimum_amount", 0.0)),
        "maximum_amount": float(option.get("maximum_amount", 0.0)),
        "estimated_fee": fee.estimated_fee,
        "effective_fee_rate": fee.effective_fee_rate,
        "success_rate_7d": float(option.get("success_rate_7d", 0.0)),
        "success_rate_30d": float(option.get("success_rate_30d", 0.0)),
        "failure_rate_7d": float(option.get("failure_rate_7d", 0.0)),
        "average_fee_30d": float(option.get("average_fee_30d", 0.0)),
        "average_arrival_minutes_7d": float(option.get("average_arrival_minutes_7d", 0.0)),
        "average_arrival_minutes_30d": float(option.get("average_arrival_minutes_30d", 0.0)),
        "p90_arrival_minutes_30d": float(option.get("p90_arrival_minutes_30d", 0.0)),
        "configured_arrival_minutes": float(option.get("configured_arrival_minutes", 0.0)),
    }
