from __future__ import annotations
from paymind.models.baseline import BaselinePaymentTypeModel,BaselineSuccessModel,BaselineArrivalModel
from paymind.models.catboost_method import CatBoostPaymentTypeModel
from paymind.models.catboost_success import CatBoostSuccessModel
from paymind.models.catboost_arrival import CatBoostArrivalModel
from paymind.models.interfaces import PaymentTypeModel,SuccessModel,ArrivalModel
from paymind.settings import ModelSettings

def build_models(settings:ModelSettings)->tuple[PaymentTypeModel,SuccessModel,ArrivalModel]:
    if settings.provider=="baseline":
        return BaselinePaymentTypeModel(settings.payment_type_model_version),BaselineSuccessModel(settings.success_model_version),BaselineArrivalModel(settings.arrival_model_version)
    if settings.provider=="catboost":
        paths=(settings.payment_type_model_path,settings.success_model_path,settings.arrival_p50_model_path,settings.arrival_p90_model_path)
        if not all(paths): raise ValueError("CatBoost provider requires method, success, arrival P50 and arrival P90 paths")
        return CatBoostPaymentTypeModel(paths[0],settings.payment_type_model_version),CatBoostSuccessModel(paths[1],settings.success_model_version),CatBoostArrivalModel(paths[2],paths[3],settings.arrival_model_version)
    raise ValueError(f"Unsupported model provider: {settings.provider}")
