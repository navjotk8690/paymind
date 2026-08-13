from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Iterable, Mapping, Sequence


@dataclass(frozen=True)
class CountryContext:
    code: str
    name: str
    local_currency: str
    jurisdiction: str


@dataclass(frozen=True)
class RouteProfile:
    route: str
    supported_transaction_types: frozenset[str]
    supported_countries: frozenset[str] | None = None
    supported_app_types: frozenset[str] | None = None
    cross_border_only: bool = False
    local_currency_only: bool = False


COUNTRY_CONTEXT = {
    "AU": CountryContext("AU", "Australia", "AUD", "AU_DEMO"),
    "US": CountryContext("US", "United States", "USD", "US_DEMO"),
    "GB": CountryContext("GB", "United Kingdom", "GBP", "GB_DEMO"),
    "DE": CountryContext("DE", "Germany", "EUR", "DE_DEMO"),
    "SG": CountryContext("SG", "Singapore", "SGD", "SG_DEMO"),
    "NZ": CountryContext("NZ", "New Zealand", "NZD", "NZ_DEMO"),
    "CA": CountryContext("CA", "Canada", "CAD", "CA_DEMO"),
    "JP": CountryContext("JP", "Japan", "JPY", "JP_DEMO"),
}


COUNTRY_OPTIONS = [
    (profile.name, profile.code)
    for profile in COUNTRY_CONTEXT.values()
]


APP_CHANNEL_OPTIONS = [
    ("Web Checkout", "web_checkout"),
    ("Mobile App", "mobile_app"),
    ("Marketplace", "marketplace"),
    ("Direct API", "direct_api"),
]


DEFAULT_DEMO_ROUTES = [
    "stripe",
    "paypal",
    "adyen",
    "checkout",
    "worldpay",
    "square",
    "wise",
    "revolut_pay",
    "bank_transfer",
]


ROUTE_OPTIONS = [
    ("Stripe", "stripe"),
    ("PayPal", "paypal"),
    ("Adyen", "adyen"),
    ("Checkout", "checkout"),
    ("Worldpay", "worldpay"),
    ("Square", "square"),
    ("Wise", "wise"),
    ("Revolut Pay", "revolut_pay"),
    ("Bank Transfer", "bank_transfer"),
]


ROUTE_PROFILES = {
    "stripe": RouteProfile(
        route="stripe",
        supported_transaction_types=frozenset({"deposit", "withdrawal"}),
        supported_app_types=frozenset({"web_checkout", "mobile_app", "direct_api"}),
    ),
    "paypal": RouteProfile(
        route="paypal",
        supported_transaction_types=frozenset({"deposit", "withdrawal"}),
    ),
    "adyen": RouteProfile(
        route="adyen",
        supported_transaction_types=frozenset({"deposit", "withdrawal"}),
        supported_app_types=frozenset({"web_checkout", "mobile_app", "marketplace", "direct_api"}),
    ),
    "checkout": RouteProfile(
        route="checkout",
        supported_transaction_types=frozenset({"deposit"}),
        supported_countries=frozenset({"AU", "GB", "DE", "SG", "NZ"}),
        supported_app_types=frozenset({"web_checkout", "mobile_app"}),
    ),
    "worldpay": RouteProfile(
        route="worldpay",
        supported_transaction_types=frozenset({"deposit", "withdrawal"}),
        supported_countries=frozenset({"AU", "US", "GB", "DE", "SG", "CA", "NZ"}),
        supported_app_types=frozenset({"web_checkout", "marketplace", "direct_api"}),
    ),
    "square": RouteProfile(
        route="square",
        supported_transaction_types=frozenset({"deposit"}),
        supported_countries=frozenset({"AU", "US", "GB", "CA"}),
        supported_app_types=frozenset({"web_checkout", "mobile_app"}),
    ),
    "wise": RouteProfile(
        route="wise",
        supported_transaction_types=frozenset({"deposit", "withdrawal"}),
        cross_border_only=True,
    ),
    "revolut_pay": RouteProfile(
        route="revolut_pay",
        supported_transaction_types=frozenset({"deposit"}),
        supported_countries=frozenset({"GB", "DE", "SG"}),
        supported_app_types=frozenset({"web_checkout", "mobile_app"}),
    ),
    "bank_transfer": RouteProfile(
        route="bank_transfer",
        supported_transaction_types=frozenset({"deposit", "withdrawal"}),
        supported_countries=frozenset({"AU", "GB", "DE", "SG", "NZ", "CA", "JP"}),
        supported_app_types=frozenset({"web_checkout", "marketplace", "direct_api"}),
        local_currency_only=True,
    ),
}


def parse_timestamp(value: Any) -> datetime:
    if isinstance(value, datetime):
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)

    text = str(value).strip()
    if not text:
        raise ValueError("timestamp_utc cannot be empty")

    formats = [
        "%m/%d/%y %H:%M",
        "%m/%d/%Y %H:%M",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%dT%H:%M:%SZ",
        "%Y-%m-%dT%H:%M:%S%z",
    ]

    for fmt in formats:
        try:
            parsed = datetime.strptime(text, fmt)
            if parsed.tzinfo is None:
                return parsed.replace(tzinfo=timezone.utc)
            return parsed.astimezone(timezone.utc)
        except ValueError:
            continue

    raise ValueError(f"Unsupported timestamp format: {value}")


def normalize_country_code(value: Any, *, default: str = "AU") -> str:
    text = str(value or default).strip().upper()
    return text or default


def normalize_category(value: Any, *, default: str) -> str:
    text = str(value or default).strip().lower()
    return text or default


def normalize_routes(routes: Iterable[str] | None) -> list[str]:
    if routes is None:
        return list(DEFAULT_DEMO_ROUTES)

    normalized: list[str] = []
    seen: set[str] = set()

    for route in routes:
        name = normalize_category(route, default="")
        if not name or name in seen:
            continue
        seen.add(name)
        normalized.append(name)

    return normalized


def _fallback_country_context(country_code: str, currency: str | None = None) -> CountryContext:
    return CountryContext(
        code=country_code,
        name=country_code,
        local_currency=(currency or "USD").upper(),
        jurisdiction=f"{country_code}_DEMO",
    )


def _as_optional_int(value: Any) -> int | None:
    if value is None or value == "":
        return None
    return int(value)


def normalize_transaction_context(
    payload: Mapping[str, Any],
    *,
    now: datetime | None = None,
) -> dict[str, Any]:
    clock = now.astimezone(timezone.utc) if now is not None else datetime.now(timezone.utc)
    raw_timestamp = payload.get("timestamp_utc")
    timestamp = parse_timestamp(raw_timestamp) if raw_timestamp else clock

    transaction_type = normalize_category(payload.get("transaction_type"), default="deposit")
    country = normalize_country_code(payload.get("country"))
    ip_country = normalize_country_code(payload.get("ip_country"), default=country)
    app_type = normalize_category(payload.get("app_type"), default="web_checkout")

    country_context = COUNTRY_CONTEXT.get(country) or _fallback_country_context(
        country,
        str(payload.get("currency") or "USD"),
    )

    currency = str(payload.get("currency") or country_context.local_currency).strip().upper()
    local_currency = str(payload.get("local_currency") or country_context.local_currency).strip().upper()
    jurisdiction = str(payload.get("jurisdiction") or country_context.jurisdiction).strip().upper()
    amount = float(payload.get("amount", 0.0))

    explicit_cross_border = _as_optional_int(payload.get("is_cross_border"))
    derived_cross_border = int(currency != local_currency or ip_country != country)
    is_cross_border = explicit_cross_border if explicit_cross_border is not None else derived_cross_border

    explicit_hour = _as_optional_int(payload.get("hour"))
    explicit_weekend = _as_optional_int(payload.get("is_weekend"))
    hour = explicit_hour if explicit_hour is not None else timestamp.hour
    day_of_week = str(payload.get("day_of_week") or timestamp.strftime("%A"))
    is_weekend = explicit_weekend if explicit_weekend is not None else int(timestamp.weekday() >= 5)

    explicit_banking_hours = _as_optional_int(payload.get("banking_hours_indicator"))
    banking_hours_indicator = (
        explicit_banking_hours
        if explicit_banking_hours is not None
        else int(9 <= hour <= 16 and is_weekend == 0)
    )

    return {
        "timestamp_utc": timestamp.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "transaction_type": transaction_type,
        "currency": currency,
        "amount": amount,
        "hour": hour,
        "day_of_week": day_of_week,
        "is_weekend": is_weekend,
        "is_cross_border": int(is_cross_border),
        "banking_hours_indicator": banking_hours_indicator,
        "country": country,
        "ip_country": ip_country,
        "local_currency": local_currency,
        "jurisdiction": jurisdiction,
        "app_type": app_type,
        "available_payment_routes": normalize_routes(payload.get("available_payment_routes")),
    }


def route_is_available_for_transaction(
    route: str,
    transaction: Mapping[str, Any],
) -> bool:
    route_name = normalize_category(route, default="")
    if not route_name:
        return False

    selected_routes = normalize_routes(transaction.get("available_payment_routes"))
    if route_name not in selected_routes:
        return False

    profile = ROUTE_PROFILES.get(route_name)
    if profile is None:
        return True

    transaction_type = normalize_category(transaction.get("transaction_type"), default="deposit")
    country = normalize_country_code(transaction.get("country"))
    app_type = normalize_category(transaction.get("app_type"), default="web_checkout")
    local_currency = str(transaction.get("local_currency") or "").strip().upper()
    currency = str(transaction.get("currency") or "").strip().upper()
    is_cross_border = int(transaction.get("is_cross_border", 0)) == 1

    if transaction_type not in profile.supported_transaction_types:
        return False
    if profile.supported_countries is not None and country not in profile.supported_countries:
        return False
    if profile.supported_app_types is not None and app_type not in profile.supported_app_types:
        return False
    if profile.cross_border_only and not is_cross_border:
        return False
    if profile.local_currency_only and currency != local_currency:
        return False

    return True


def eligible_routes_for_transaction(
    transaction: Mapping[str, Any],
    candidate_routes: Sequence[str] | None = None,
) -> list[str]:
    normalized_transaction = normalize_transaction_context(transaction)
    selected = candidate_routes or DEFAULT_DEMO_ROUTES
    return [
        route
        for route in normalize_routes(selected)
        if route_is_available_for_transaction(route, normalized_transaction)
    ]
