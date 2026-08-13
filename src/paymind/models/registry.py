from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any
import importlib
import json
import os

from catboost import CatBoostClassifier, CatBoostRegressor


DEFAULT_REGISTRY_PATH = Path("models/registry.json")
DEFAULT_HF_CACHE_DIR = Path("runtime/hf-cache")
REFERENCE_MODELS_DISCLAIMER = (
    "Reference models are provided for demonstration and development only. "
    "Retrain PayMind on your own payment environment before real use."
)


class ModelRegistryError(RuntimeError):
    pass


@dataclass(frozen=True)
class ModelInfo:
    key: str
    display_name: str
    version: str
    enabled: bool
    loaded: bool
    source: str
    mode: str
    metadata: dict[str, Any]


class ModelRegistry:
    """
    Load reference or locally retrained PayMind model artifacts.

    The registry supports either local filesystem paths or optional
    Hugging Face Hub artifacts. Training data is never fetched or stored.
    """

    def __init__(
        self,
        registry_path: Path | str = DEFAULT_REGISTRY_PATH,
        hf_cache_dir: Path | str = DEFAULT_HF_CACHE_DIR,
    ) -> None:
        self.registry_path = Path(registry_path)
        self.hf_cache_dir = Path(hf_cache_dir)
        self.config: dict[str, Any] = {}
        self.disclaimer = REFERENCE_MODELS_DISCLAIMER

        self.payment_method_model: CatBoostClassifier | None = None
        self.success_model: CatBoostClassifier | None = None
        self.arrival_p50_model: CatBoostRegressor | None = None
        self.arrival_p90_model: CatBoostRegressor | None = None

        self.metadata: dict[str, dict[str, Any]] = {}
        self.loaded = False

    def _load_json(
        self,
        path: Path,
    ) -> dict[str, Any]:
        if not path.exists():
            raise ModelRegistryError(f"File not found: {path}")

        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise ModelRegistryError(f"Invalid JSON: {path}") from exc

        if not isinstance(payload, dict):
            raise ModelRegistryError(f"Manifest must be an object: {path}")

        return payload

    def _download_huggingface_artifact(
        self,
        spec: dict[str, Any],
    ) -> Path:
        try:
            hub = importlib.import_module("huggingface_hub")
        except ImportError as exc:
            raise ModelRegistryError(
                "huggingface_hub is required for manifest entries with source='huggingface'"
            ) from exc

        repo_id = spec.get("repo_id")
        filename = spec.get("filename")

        if not repo_id or not filename:
            raise ModelRegistryError(
                "Hugging Face artifact entries require both 'repo_id' and 'filename'"
            )

        revision = spec.get("revision")
        cache_dir = spec.get("cache_dir") or os.getenv("PAYMIND_HF_CACHE_DIR")
        cache_root = Path(cache_dir) if cache_dir else self.hf_cache_dir
        cache_root.mkdir(parents=True, exist_ok=True)

        downloaded = hub.hf_hub_download(
            repo_id=repo_id,
            filename=filename,
            revision=revision,
            cache_dir=str(cache_root),
            token=os.getenv("HUGGINGFACE_HUB_TOKEN") or None,
        )
        return Path(downloaded)

    def _resolve_artifact_path(
        self,
        spec: dict[str, Any],
    ) -> Path:
        source = str(spec.get("source", "local")).lower()

        if source == "local":
            local_path = spec.get("local_path")
            if not local_path:
                raise ModelRegistryError("Local artifact entries require 'local_path'")
            path = Path(local_path)
            if not path.exists():
                raise ModelRegistryError(f"Model file not found: {path}")
            return path

        if source == "huggingface":
            return self._download_huggingface_artifact(spec)

        raise ModelRegistryError(f"Unsupported artifact source: {source}")

    def _load_metadata(
        self,
        model_name: str,
        spec: dict[str, Any],
    ) -> None:
        path = self._resolve_artifact_path(spec)
        self.metadata[model_name] = self._load_json(path)

    def _primary_source(
        self,
        config: dict[str, Any],
    ) -> str:
        artifacts = config.get("artifacts", {})
        for artifact_name in ("model", "p50_model", "p90_model", "metadata"):
            artifact = artifacts.get(artifact_name)
            if artifact:
                return str(artifact.get("source", "local")).lower()
        return "local"

    def load(self) -> "ModelRegistry":
        self.config = self._load_json(self.registry_path)
        self.disclaimer = self.config.get(
            "reference_models_disclaimer",
            REFERENCE_MODELS_DISCLAIMER,
        )

        models = self.config.get("models", {})
        if not models:
            raise ModelRegistryError("No models found in registry.")

        self._load_payment_method(models.get("payment_method"))
        self._load_success(models.get("success"))
        self._load_arrival(models.get("arrival"))

        self.loaded = True
        return self

    def _load_payment_method(
        self,
        config: dict[str, Any] | None,
    ) -> None:
        if not config or not config.get("enabled", False):
            return

        artifacts = config.get("artifacts", {})
        model_path = self._resolve_artifact_path(artifacts["model"])
        model = CatBoostClassifier()
        model.load_model(str(model_path))
        self.payment_method_model = model

        metadata_spec = artifacts.get("metadata")
        if metadata_spec:
            self._load_metadata("payment_method", metadata_spec)

    def _load_success(
        self,
        config: dict[str, Any] | None,
    ) -> None:
        if not config or not config.get("enabled", False):
            return

        artifacts = config.get("artifacts", {})
        model_path = self._resolve_artifact_path(artifacts["model"])
        model = CatBoostClassifier()
        model.load_model(str(model_path))
        self.success_model = model

        metadata_spec = artifacts.get("metadata")
        if metadata_spec:
            self._load_metadata("success", metadata_spec)

    def _load_arrival(
        self,
        config: dict[str, Any] | None,
    ) -> None:
        if not config or not config.get("enabled", False):
            return

        artifacts = config.get("artifacts", {})
        p50_path = self._resolve_artifact_path(artifacts["p50_model"])
        p90_path = self._resolve_artifact_path(artifacts["p90_model"])

        p50_model = CatBoostRegressor()
        p90_model = CatBoostRegressor()
        p50_model.load_model(str(p50_path))
        p90_model.load_model(str(p90_path))

        self.arrival_p50_model = p50_model
        self.arrival_p90_model = p90_model

        metadata_spec = artifacts.get("metadata")
        if metadata_spec:
            self._load_metadata("arrival", metadata_spec)

    def ensure_loaded(self) -> None:
        if not self.loaded:
            raise ModelRegistryError("Model registry has not been loaded.")

    def get_payment_method_model(self) -> CatBoostClassifier:
        self.ensure_loaded()
        if self.payment_method_model is None:
            raise ModelRegistryError("Payment method model is unavailable.")
        return self.payment_method_model

    def get_success_model(self) -> CatBoostClassifier:
        self.ensure_loaded()
        if self.success_model is None:
            raise ModelRegistryError("Success model is unavailable.")
        return self.success_model

    def get_arrival_models(self) -> tuple[CatBoostRegressor, CatBoostRegressor]:
        self.ensure_loaded()
        if self.arrival_p50_model is None or self.arrival_p90_model is None:
            raise ModelRegistryError("Arrival models are unavailable.")
        return self.arrival_p50_model, self.arrival_p90_model

    def get_metadata(self, model_name: str) -> dict[str, Any]:
        self.ensure_loaded()
        if model_name not in self.metadata:
            raise ModelRegistryError(f"No metadata for: {model_name}")
        return self.metadata[model_name]

    def get_model_info(self, model_name: str) -> ModelInfo:
        self.ensure_loaded()
        config = self.config.get("models", {}).get(model_name, {})
        enabled = bool(config.get("enabled", False))
        loaded = {
            "payment_method": self.payment_method_model is not None,
            "success": self.success_model is not None,
            "arrival": self.arrival_p50_model is not None and self.arrival_p90_model is not None,
        }.get(model_name, False)
        return ModelInfo(
            key=model_name,
            display_name=config.get("display_name", model_name.replace("_", " ").title()),
            version=str(config.get("version", self.metadata.get(model_name, {}).get("version", "unknown"))),
            enabled=enabled,
            loaded=loaded,
            source=self._primary_source(config),
            mode=str(config.get("mode", "reference")),
            metadata=self.metadata.get(model_name, {}),
        )

    def describe_models(self) -> dict[str, Any]:
        self.ensure_loaded()
        return {
            "registry_version": self.config.get("registry_version", "unknown"),
            "disclaimer": self.disclaimer,
            "models": [
                self.get_model_info("payment_method").__dict__,
                self.get_model_info("success").__dict__,
                self.get_model_info("arrival").__dict__,
            ],
        }

    def status(self) -> dict[str, Any]:
        return {
            "loaded": self.loaded,
            "payment_method": self.payment_method_model is not None,
            "success": self.success_model is not None,
            "arrival_p50": self.arrival_p50_model is not None,
            "arrival_p90": self.arrival_p90_model is not None,
            "registry_version": self.config.get("registry_version", "unknown"),
            "disclaimer": self.disclaimer,
        }
