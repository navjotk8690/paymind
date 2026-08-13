from paymind.models.baseline import BaselineArrivalModel

def test_arrival_returns_ordered_quantiles():
    model=BaselineArrivalModel()
    result=model.predict([{"payment_type":"wire","is_cross_border":1,"day_of_week":"Monday"}])[0]
    assert result.p50_minutes>0
    assert result.p90_minutes>=result.p50_minutes
