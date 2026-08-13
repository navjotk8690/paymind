from __future__ import annotations

import os

import uvicorn
from fastapi import FastAPI

from paymind.api.schemas import (
    EvaluateRequest,
    EvaluateResponse,
    HealthResponse,
    ModelsResponse,
)
from paymind.sdk import PayMind


app = FastAPI(
    title="NavCore PayMind",
    version="0.2.0",
)


paymind = PayMind()


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse.model_validate(paymind.health())


@app.get("/models", response_model=ModelsResponse)
def models() -> ModelsResponse:
    return paymind.models()


@app.post(
    "/evaluate",
    response_model=EvaluateResponse,
)
def evaluate(
    request: EvaluateRequest,
) -> EvaluateResponse:
    return paymind.evaluate(request)


def run() -> None:
    uvicorn.run(
        "paymind.api.app:app",
        host=os.getenv("PAYMIND_HOST", "127.0.0.1"),
        port=int(os.getenv("PAYMIND_PORT", "8080")),
        reload=False,
    )


if __name__ == "__main__":
    run()
