from __future__ import annotations

from pathlib import Path
from typing import Sequence


class CatBoostSuccessModel:
    def __init__(self, model_path: str | Path, version: str) -> None:
        try:
            from catboost import CatBoostClassifier
        except ImportError as exc:  # pragma: no cover
            raise RuntimeError("Install navcore-paymind with runtime model dependencies") from exc

        self._model = CatBoostClassifier()
        self._model.load_model(str(model_path))
        self._version = version

    @property
    def version(self) -> str:
        return self._version

    def predict_probabilities(self, candidates: Sequence[dict[str, object]]) -> list[float]:
        if not candidates:
            return []
        return [float(value) for value in self._model.predict_proba(list(candidates))[:, 1]]
