from paymind.rules.eligibility import evaluate_eligibility


def request(**overrides):
    values = {
        "transaction_type": "deposit",
        "country": "ID",
        "ip_country": "ID",
        "jurisdiction": "OJK",
        "currency": "IDR",
        "amount": 1_000_000,
        "app_type": "MU",
    }
    values.update(overrides)
    return values


def option(**overrides):
    values = {
        "transaction_type": "deposit",
        "status": "active",
        "under_maintenance": False,
        "vendor_unavailable": False,
        "allowed_currencies": ["IDR"],
        "allowed_countries": ["ID"],
        "allowed_jurisdictions": ["OJK"],
        "allowed_ip_countries": ["ID"],
        "restricted_countries": [],
        "minimum_amount": 100,
        "maximum_amount": 2_000_000,
        "app_type": "MU",
    }
    values.update(overrides)
    return values


def test_eligible_route():
    result = evaluate_eligibility(request(), option())
    assert result.eligible is True


def test_restricted_country_rejected():
    result = evaluate_eligibility(
        request(),
        option(restricted_countries=["ID"]),
    )
    assert result.eligible is False
    assert "RESTRICTED_COUNTRY" in [reason.value for reason in result.reason_codes]


def test_wrong_currency_rejected():
    result = evaluate_eligibility(
        request(currency="USD"),
        option(),
    )
    assert result.eligible is False
