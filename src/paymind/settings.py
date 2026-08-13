from __future__ import annotations
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any
import yaml

@dataclass(frozen=True)
class ServiceSettings:
    name:str="navcore-paymind"; version:str="0.2.0"; max_options_per_request:int=50; max_request_bytes:int=262144; request_timeout_ms:int=1000
@dataclass(frozen=True)
class PrivacySettings:
    persist_requests:bool=False; persist_responses:bool=False; log_request_payloads:bool=False; log_response_payloads:bool=False; telemetry_enabled:bool=False
@dataclass(frozen=True)
class ModelSettings:
    provider:str="baseline"
    payment_type_model_path:str|None=None; success_model_path:str|None=None
    arrival_p50_model_path:str|None=None; arrival_p90_model_path:str|None=None
    payment_type_model_version:str="baseline-method-v1"; success_model_version:str="baseline-success-v1"; arrival_model_version:str="baseline-arrival-v1"
@dataclass(frozen=True)
class RankingSettings:
    payment_type_probability_weight:float=0.25; success_probability_weight:float=0.40; cost_weight:float=0.15; speed_weight:float=0.15; position_weight:float=0.05
    def validate(self)->None:
        total=sum((self.payment_type_probability_weight,self.success_probability_weight,self.cost_weight,self.speed_weight,self.position_weight))
        if abs(total-1)>1e-9: raise ValueError(f"Ranking weights must sum to 1.0; received {total}")
@dataclass(frozen=True)
class Settings:
    service:ServiceSettings; privacy:PrivacySettings; models:ModelSettings; ranking:RankingSettings

def _read_yaml(path:Path)->dict[str,Any]:
    if not path.exists(): return {}
    data=yaml.safe_load(path.read_text()) or {}
    if not isinstance(data,dict): raise ValueError(f"Configuration must be a mapping: {path}")
    return data

def load_settings()->Settings:
    config=_read_yaml(Path(os.getenv("PAYMIND_CONFIG_PATH","config/paymind.yaml")))
    rank=_read_yaml(Path(os.getenv("PAYMIND_RANKING_CONFIG_PATH","config/ranking.yaml")))
    service=ServiceSettings(**config.get("service",{})); privacy=PrivacySettings(**config.get("privacy",{})); models=ModelSettings(**config.get("models",{})); ranking=RankingSettings(**rank.get("ranking",{})); ranking.validate()
    if any((privacy.persist_requests,privacy.persist_responses,privacy.log_request_payloads,privacy.log_response_payloads)):
        raise ValueError("PayMind must remain stateless and payload-safe")
    return Settings(service,privacy,models,ranking)
