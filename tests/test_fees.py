from paymind.fees.calculator import calculate_fee


def test_fee_with_minimum_and_cap():
    request = {
        "amount": 1000,
    }
    option = {
        "fee_percentage": 2.9,
        "fee_fixed": 0.3,
        "fx_markup_percentage": 0.5,
        "minimum_fee": 1,
        "maximum_fee": 40,
    }
    result = calculate_fee(request, option)
    assert result.estimated_fee == 34.3
    assert result.effective_fee_rate == 0.0343
