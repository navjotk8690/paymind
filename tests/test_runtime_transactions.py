from paymind.runtime.transactions import normalize_transaction_context


def test_normalize_transaction_context_derives_cross_border_from_currency():
    transaction = normalize_transaction_context(
        {
            "transaction_type": "deposit",
            "amount": 500,
            "currency": "USD",
            "country": "AU",
            "ip_country": "AU",
            "app_type": "web_checkout",
        }
    )

    assert transaction["local_currency"] == "AUD"
    assert transaction["is_cross_border"] == 1
    assert transaction["jurisdiction"] == "AU_DEMO"
    assert transaction["banking_hours_indicator"] in {0, 1}


def test_normalize_transaction_context_respects_explicit_cross_border_override():
    transaction = normalize_transaction_context(
        {
            "transaction_type": "deposit",
            "amount": 500,
            "currency": "USD",
            "country": "AU",
            "ip_country": "AU",
            "app_type": "web_checkout",
            "is_cross_border": 0,
        }
    )

    assert transaction["is_cross_border"] == 0


def test_normalize_transaction_context_defaults_routes():
    transaction = normalize_transaction_context(
        {
            "transaction_type": "withdrawal",
            "amount": 200,
            "currency": "GBP",
            "country": "GB",
            "ip_country": "GB",
            "app_type": "direct_api",
        }
    )

    assert "available_payment_routes" in transaction
    assert "stripe" in transaction["available_payment_routes"]
