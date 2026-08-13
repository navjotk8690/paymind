from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any
import json


DEFAULT_FEE_CONFIG_PATH = Path(
    "config/fee_config.json"
)


@dataclass(frozen=True)
class FeeEvaluation:
    payment_method: str

    percentage_fee: float
    fixed_fee: float
    fx_fee: float

    total_fee: float

    fee_percentage_of_amount: float


class FeeService:
    """
    Runtime fee evaluation service.

    By default, fees are loaded from:
        config/fee_config.json

    A fee config dict can still be passed directly,
    which is useful for tests or custom deployments.
    """

    def __init__(
        self,
        fee_config: dict[
            str,
            dict[str, float],
        ] | None = None,
        config_path: str | Path = DEFAULT_FEE_CONFIG_PATH,
    ) -> None:

        if fee_config is not None:
            self.fee_config = fee_config
            return

        path = Path(config_path)

        if not path.exists():
            raise FileNotFoundError(
                f"Fee config not found: {path}"
            )

        try:
            self.fee_config = json.loads(
                path.read_text(
                    encoding="utf-8"
                )
            )

        except json.JSONDecodeError as exc:
            raise ValueError(
                f"Invalid fee config JSON: {path}"
            ) from exc

    def evaluate(
        self,
        transaction: dict[str, Any],
        payment_method: str,
    ) -> FeeEvaluation:

        amount = float(
            transaction["amount"]
        )

        if amount < 0:
            raise ValueError(
                "Transaction amount cannot be negative."
            )

        method = (
            str(payment_method)
            .strip()
            .lower()
        )

        config = self.fee_config.get(
            method,
            {},
        )

        percentage = float(
            config.get(
                "percentage",
                0.0,
            )
        )

        fixed = float(
            config.get(
                "fixed",
                0.0,
            )
        )

        fx_percentage = float(
            config.get(
                "fx_percentage",
                0.0,
            )
        )

        percentage_fee = (
            amount
            * percentage
            / 100.0
        )

        fx_fee = (
            amount
            * fx_percentage
            / 100.0
        )

        total_fee = (
            percentage_fee
            + fixed
            + fx_fee
        )

        if amount > 0:
            effective_percentage = (
                total_fee
                / amount
            )
        else:
            effective_percentage = 0.0

        return FeeEvaluation(
            payment_method=method,

            percentage_fee=
                percentage_fee,

            fixed_fee=
                fixed,

            fx_fee=
                fx_fee,

            total_fee=
                total_fee,

            fee_percentage_of_amount=
                effective_percentage,
        )