from __future__ import annotations

from pathlib import Path


class CatBoostPaymentTypeModel:
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

    def predict_probabilities(self, features: dict[str, object]) -> dict[str, float]:
        ordered = [features]
        probabilities = self._model.predict_proba(ordered)[0]
        labels = [str(label) for label in self._model.classes_]
        return {label: float(probability) for label, probability in zip(labels, probabilities)}
