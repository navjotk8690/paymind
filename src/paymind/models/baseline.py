from __future__ import annotations
import math
from collections.abc import Sequence
from paymind.models.interfaces import ArrivalPrediction

class BaselinePaymentTypeModel:
    def __init__(self, version: str = "baseline-method-v1") -> None: self._version = version
    @property
    def version(self) -> str: return self._version
    def predict_probabilities(self, features: dict[str, object]) -> dict[str, float]:
        country, currency = str(features["country"]), str(features["currency"])
        amount, tx_type = float(features["amount"]), str(features["transaction_type"])
        scores = {"card":1.0,"local_bank":1.0,"bank_transfer":1.0,"wallet":0.8,"wire":0.5,"instant_payment":0.8}
        local = {"ID":"IDR","MY":"MYR","TH":"THB","AU":"AUD","GB":"GBP","SG":"SGD"}.get(country)
        if local == currency:
            scores["local_bank"] += 2.2; scores["instant_payment"] += 1.4
        else:
            scores["card"] += 1.2; scores["wire"] += 0.7
        if amount <= 1000: scores["wallet"] += 0.8; scores["card"] += 0.5
        elif amount >= 25000: scores["wire"] += 2.0; scores["bank_transfer"] += 1.0
        if tx_type == "withdrawal": scores["wire"] += 1.0; scores["bank_transfer"] += 1.2; scores["card"] *= 0.35
        exps={k:math.exp(v) for k,v in scores.items()}; total=sum(exps.values())
        return {k:v/total for k,v in exps.items()}

class BaselineSuccessModel:
    def __init__(self, version: str = "baseline-success-v1") -> None: self._version = version
    @property
    def version(self) -> str: return self._version
    def predict_probabilities(self, candidates: Sequence[dict[str, object]]) -> list[float]:
        out=[]
        for c in candidates:
            base=0.86
            if c.get("success_rate_7d") is not None: base=0.65*float(c["success_rate_7d"])+0.35*base
            if c.get("success_rate_30d") is not None: base=0.65*base+0.35*float(c["success_rate_30d"])
            ratio=min(float(c.get("amount",0))/max(float(c.get("maximum_amount",1)),1),1.5)
            base -= max(ratio-0.75,0)*0.12 + min(float(c.get("effective_fee_rate",0)),0.2)*0.15
            base -= min(max(int(c.get("position",1))-1,0),10)*0.005
            out.append(round(min(max(base,0.02),0.995),8))
        return out

class BaselineArrivalModel:
    def __init__(self, version: str = "baseline-arrival-v1") -> None: self._version = version
    @property
    def version(self) -> str: return self._version
    def predict(self, candidates: Sequence[dict[str, object]]) -> list[ArrivalPrediction]:
        result=[]
        defaults={"instant_payment":5,"wallet":20,"card":30,"local_bank":180,"bank_transfer":720,"wire":2880}
        for c in candidates:
            configured=c.get("configured_arrival_minutes")
            hist7=c.get("average_arrival_minutes_7d")
            hist30=c.get("average_arrival_minutes_30d")
            p90hist=c.get("p90_arrival_minutes_30d")
            base=float(configured) if configured is not None else float(defaults.get(str(c.get("payment_type")),240))
            if hist30 is not None: base=0.55*base+0.45*float(hist30)
            if hist7 is not None: base=0.45*base+0.55*float(hist7)
            if int(c.get("is_cross_border",0)): base*=1.35
            if str(c.get("day_of_week")) in {"Saturday","Sunday"}: base*=1.25
            p50=max(base,1.0)
            p90=max(float(p90hist),p50) if p90hist is not None else p50*1.8
            result.append(ArrivalPrediction(round(p50,2),round(p90,2)))
        return result
