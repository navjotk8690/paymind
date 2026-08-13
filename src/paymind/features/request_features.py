from __future__ import annotations

from typing import Any, Mapping


LOCAL_CURRENCY_BY_COUNTRY = {
    "AU": "AUD",
    "GB": "GBP",
    "ID": "IDR",
    "MY": "MYR",
    "SG": "SGD",
    "TH": "THB",
    "NZ": "NZD",
    "CA": "CAD",
    "ZA": "ZAR",
    "AE": "AED",
}


def build_request_features(request: Mapping[str, Any]) -> dict[str, object]:
    country = str(request.get("country", ""))
    currency = str(request.get("currency", ""))
    destination = str(request.get("destination_country") or country)
    settlement = str(request.get("settlement_currency") or currency)
    local_currency = LOCAL_CURRENCY_BY_COUNTRY.get(country)
    is_cross_border = int(
        destination != country or (local_currency is not None and currency != local_currency)
    )

    return {
        "transaction_type": request.get("transaction_type", "deposit"),
        "country": country,
        "destination_country": destination,
        "ip_country": request.get("ip_country", country),
        "jurisdiction": request.get("jurisdiction", ""),
        "currency": currency,
        "settlement_currency": settlement,
        "amount": float(request.get("amount", 0.0)),
        "app_type": request.get("app_type", ""),
        "hour": int(request.get("hour", 0)),
        "day_of_week": request.get("day_of_week", ""),
        "is_weekend": int(request.get("is_weekend", 0)),
        "is_cross_border": int(request.get("is_cross_border", is_cross_border)),
    }
