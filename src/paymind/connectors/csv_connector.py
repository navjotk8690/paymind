from __future__ import annotations

import json
from pathlib import Path

from paymind.api.schemas import EvaluateRequest


class CsvConnector:
    """Reads one-row canonical CSV exports. List/dict cells must contain JSON."""

    def transform_file(self, path: str | Path) -> list[EvaluateRequest]:
        try:
            import pandas as pd
        except ImportError as exc:
            raise RuntimeError("Install navcore-paymind with pandas support for CSV connectors") from exc

        frame = pd.read_csv(path)
        output = []
        for record in frame.to_dict(orient="records"):
            raw = record.get("payload_json")
            if not isinstance(raw, str):
                raise ValueError("CSV requires a payload_json column")
            output.append(EvaluateRequest.model_validate(json.loads(raw)))
        return output
