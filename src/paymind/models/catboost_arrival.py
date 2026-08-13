from __future__ import annotations
from pathlib import Path
from typing import Sequence
from paymind.models.interfaces import ArrivalPrediction

class CatBoostArrivalModel:
    """Loads separate P50 and P90 CatBoost regressors."""
    def __init__(self, p50_path: str|Path, p90_path: str|Path, version: str) -> None:
        try:
            from catboost import CatBoostRegressor
        except ImportError as exc:
            raise RuntimeError("Install navcore-paymind with runtime model dependencies") from exc
        self._p50=CatBoostRegressor(); self._p50.load_model(str(p50_path))
        self._p90=CatBoostRegressor(); self._p90.load_model(str(p90_path)); self._version=version
    @property
    def version(self)->str: return self._version
    def predict(self, candidates: Sequence[dict[str,object]]) -> list[ArrivalPrediction]:
        if not candidates: return []
        p50=self._p50.predict(list(candidates)); p90=self._p90.predict(list(candidates))
        return [ArrivalPrediction(max(float(a),0.0), max(float(b),float(a),0.0)) for a,b in zip(p50,p90)]
