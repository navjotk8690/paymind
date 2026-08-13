from pathlib import Path
import json

from paymind.models import registry as registry_module
from paymind.models.registry import ModelRegistry


def test_registry_loads_models():
    registry = ModelRegistry().load()
    status = registry.status()

    assert status["loaded"] is True
    assert status["payment_method"] is True
    assert status["success"] is True
    assert status["arrival_p50"] is True
    assert status["arrival_p90"] is True

    summary = registry.describe_models()
    assert summary["models"]
    assert "disclaimer" in summary


def test_registry_metadata():
    registry = ModelRegistry().load()

    assert registry.get_metadata("payment_method")
    assert registry.get_metadata("success")
    assert registry.get_metadata("arrival")


def test_local_manifest_loading(tmp_path):
    manifest_path = tmp_path / "registry.json"
    manifest = {
        "registry_version": "test-local",
        "reference_models_disclaimer": "demo",
        "models": {
            "payment_method": {
                "enabled": True,
                "display_name": "Payment Method",
                "version": "1.0.0",
                "mode": "reference",
                "artifacts": {
                    "model": {
                        "source": "local",
                        "local_path": str(Path("models/payment_method/payment_method_v1.cbm").resolve()),
                    },
                    "metadata": {
                        "source": "local",
                        "local_path": str(Path("models/payment_method/metadata.json").resolve()),
                    },
                },
            },
            "success": {
                "enabled": True,
                "display_name": "Success",
                "version": "1.0.0",
                "mode": "reference",
                "artifacts": {
                    "model": {
                        "source": "local",
                        "local_path": str(Path("models/success/success_v1.cbm").resolve()),
                    },
                    "metadata": {
                        "source": "local",
                        "local_path": str(Path("models/success/metadata.json").resolve()),
                    },
                },
            },
            "arrival": {
                "enabled": True,
                "display_name": "Arrival",
                "version": "1.0.0",
                "mode": "reference",
                "artifacts": {
                    "p50_model": {
                        "source": "local",
                        "local_path": str(Path("models/arrival/arrival_p50_v1.cbm").resolve()),
                    },
                    "p90_model": {
                        "source": "local",
                        "local_path": str(Path("models/arrival/arrival_p90_v1.cbm").resolve()),
                    },
                    "metadata": {
                        "source": "local",
                        "local_path": str(Path("models/arrival/metadata.json").resolve()),
                    },
                },
            },
        },
    }
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    registry = ModelRegistry(registry_path=manifest_path).load()
    assert registry.status()["loaded"] is True
    assert registry.get_model_info("payment_method").source == "local"


def test_huggingface_manifest_loading_uses_downloads(tmp_path, monkeypatch):
    downloads: list[tuple[str, str, str | None]] = []
    files = {
        "payment_method.cbm": tmp_path / "payment_method.cbm",
        "payment_method.json": tmp_path / "payment_method.json",
        "success.cbm": tmp_path / "success.cbm",
        "success.json": tmp_path / "success.json",
        "arrival_p50.cbm": tmp_path / "arrival_p50.cbm",
        "arrival_p90.cbm": tmp_path / "arrival_p90.cbm",
        "arrival.json": tmp_path / "arrival.json",
    }

    for name, path in files.items():
        if name.endswith(".json"):
            path.write_text(json.dumps({"name": name, "metrics": {}}), encoding="utf-8")
        else:
            path.write_text("stub", encoding="utf-8")

    class FakeHub:
        @staticmethod
        def hf_hub_download(repo_id, filename, revision=None, cache_dir=None, token=None):
            downloads.append((repo_id, filename, revision))
            return str(files[filename])

    class DummyClassifier:
        def load_model(self, path):
            self.path = path

    class DummyRegressor:
        def load_model(self, path):
            self.path = path

    monkeypatch.setattr(registry_module.importlib, "import_module", lambda name: FakeHub)
    monkeypatch.setattr(registry_module, "CatBoostClassifier", DummyClassifier)
    monkeypatch.setattr(registry_module, "CatBoostRegressor", DummyRegressor)

    manifest_path = tmp_path / "registry_hf.json"
    manifest = {
        "registry_version": "test-hf",
        "models": {
            "payment_method": {
                "enabled": True,
                "display_name": "Payment Method",
                "version": "1.0.0",
                "mode": "reference",
                "artifacts": {
                    "model": {"source": "huggingface", "repo_id": "org/demo", "filename": "payment_method.cbm"},
                    "metadata": {"source": "huggingface", "repo_id": "org/demo", "filename": "payment_method.json"},
                },
            },
            "success": {
                "enabled": True,
                "display_name": "Success",
                "version": "1.0.0",
                "mode": "reference",
                "artifacts": {
                    "model": {"source": "huggingface", "repo_id": "org/demo", "filename": "success.cbm"},
                    "metadata": {"source": "huggingface", "repo_id": "org/demo", "filename": "success.json"},
                },
            },
            "arrival": {
                "enabled": True,
                "display_name": "Arrival",
                "version": "1.0.0",
                "mode": "reference",
                "artifacts": {
                    "p50_model": {"source": "huggingface", "repo_id": "org/demo", "filename": "arrival_p50.cbm"},
                    "p90_model": {"source": "huggingface", "repo_id": "org/demo", "filename": "arrival_p90.cbm"},
                    "metadata": {"source": "huggingface", "repo_id": "org/demo", "filename": "arrival.json"},
                },
            },
        },
    }
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    registry = ModelRegistry(registry_path=manifest_path, hf_cache_dir=tmp_path / "hf-cache").load()
    assert registry.status()["loaded"] is True
    assert registry.get_model_info("success").source == "huggingface"
    assert len(downloads) == 7
