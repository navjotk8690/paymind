from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from paymind.rules.reason_codes import ReasonCode


@dataclass(frozen=True)
class EligibilityResult:
    eligible: bool
    reason_codes: tuple[ReasonCode, ...]


def evaluate_eligibility(
    transaction: Mapping[str, Any],
    option: Mapping[str, Any],
) -> EligibilityResult:
    failures: list[ReasonCode] = []

    if str(option.get("status", "active")).lower() != "active":
        failures.append(ReasonCode.ROUTE_INACTIVE)
    if bool(option.get("under_maintenance", False)):
        failures.append(ReasonCode.UNDER_MAINTENANCE)
    if bool(option.get("vendor_unavailable", False)):
        failures.append(ReasonCode.VENDOR_UNAVAILABLE)
    if option.get("transaction_type") != transaction.get("transaction_type"):
        failures.append(ReasonCode.TRANSACTION_TYPE_NOT_SUPPORTED)
    if transaction.get("country") in option.get("restricted_countries", []):
        failures.append(ReasonCode.RESTRICTED_COUNTRY)
    allowed_countries = option.get("allowed_countries", [])
    if allowed_countries and transaction.get("country") not in allowed_countries:
        failures.append(ReasonCode.COUNTRY_NOT_SUPPORTED)
    allowed_jurisdictions = option.get("allowed_jurisdictions", [])
    jurisdiction = str(transaction.get("jurisdiction", "")).upper()
    if allowed_jurisdictions and jurisdiction not in allowed_jurisdictions:
        failures.append(ReasonCode.JURISDICTION_NOT_SUPPORTED)
    allowed_ip_countries = option.get("allowed_ip_countries", [])
    if allowed_ip_countries and transaction.get("ip_country") not in allowed_ip_countries:
        failures.append(ReasonCode.IP_COUNTRY_NOT_ALLOWED)
    allowed_currencies = option.get("allowed_currencies", [])
    if allowed_currencies and transaction.get("currency") not in allowed_currencies:
        failures.append(ReasonCode.CURRENCY_NOT_SUPPORTED)
    amount = float(transaction.get("amount", 0.0))
    if amount < float(option.get("minimum_amount", 0.0)):
        failures.append(ReasonCode.AMOUNT_BELOW_MINIMUM)
    if amount > float(option.get("maximum_amount", float("inf"))):
        failures.append(ReasonCode.AMOUNT_ABOVE_MAXIMUM)
    option_app_type = option.get("app_type")
    request_app_type = transaction.get("app_type")
    if option_app_type not in (None, "") and request_app_type != option_app_type:
        failures.append(ReasonCode.APP_TYPE_NOT_SUPPORTED)

    if failures:
        return EligibilityResult(False, tuple(failures))
    return EligibilityResult(True, (ReasonCode.ELIGIBLE,))
