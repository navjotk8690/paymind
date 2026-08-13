from __future__ import annotations
from pathlib import Path
import json

def require_columns(frame,required:set[str],name:str):
    missing=required-set(frame.columns)
    if missing: raise ValueError(f"{name} missing columns: {sorted(missing)}")

def save_metadata(path:Path,payload:dict):
    path.parent.mkdir(parents=True,exist_ok=True); path.write_text(json.dumps(payload,indent=2),encoding="utf-8")
