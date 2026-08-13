from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Any


@dataclass(frozen=True)
class FeeResult:
    percentage_fee_amount: float
    fixed_fee_amount: float
    fx_markup_amount: float
    estimated_fee: float
    effective_fee_rate: float


def calculate_fee(
    transaction: Mapping[str, Any],
    option: Mapping[str, Any],
) -> FeeResult:
    amount = float(transaction["amount"])
    percentage_fee = float(option.get("fee_percentage", 0.0))
    fixed_fee = float(option.get("fee_fixed", 0.0))
    fx_markup_percentage = float(option.get("fx_markup_percentage", 0.0))
    minimum_fee = float(option.get("minimum_fee", 0.0))
    maximum_fee = option.get("maximum_fee")

    percentage_fee_amount = amount * percentage_fee / 100.0
    fixed_fee_amount = fixed_fee
    fx_markup_amount = amount * fx_markup_percentage / 100.0
    raw_fee = percentage_fee_amount + fixed_fee_amount + fx_markup_amount

    estimated_fee = max(raw_fee, minimum_fee)
    if maximum_fee is not None:
        estimated_fee = min(estimated_fee, float(maximum_fee))

    estimated_fee = round(estimated_fee, 8)
    effective_fee_rate = estimated_fee / amount

    return FeeResult(
        percentage_fee_amount=round(percentage_fee_amount, 8),
        fixed_fee_amount=round(fixed_fee_amount, 8),
        fx_markup_amount=round(fx_markup_amount, 8),
        estimated_fee=estimated_fee,
        effective_fee_rate=round(effective_fee_rate, 10),
    )
