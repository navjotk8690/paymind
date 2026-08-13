import importlib
import sys

import gradio as gr


def test_root_app_import_does_not_launch(monkeypatch):
    launched = {"called": False}

    def fake_launch(self, *args, **kwargs):
        launched["called"] = True
        raise AssertionError("launch should not be called during import")

    monkeypatch.setattr(gr.Blocks, "launch", fake_launch, raising=False)
    sys.modules.pop("app", None)
    sys.modules.pop("frontend.app", None)

    module = importlib.import_module("app")

    assert hasattr(module, "app")
    assert launched["called"] is False
