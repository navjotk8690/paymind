from fastapi.testclient import TestClient

from paymind.api.app import app
from paymind.connectors.synthetic import sample_evaluate_request


client = TestClient(app)


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_models():
    response = client.get("/models")
    assert response.status_code == 200
    body = response.json()
    assert body["models"]
    assert "disclaimer" in body


def test_evaluate():
    payload = sample_evaluate_request().model_dump(mode="json")
    response = client.post("/evaluate", json=payload)
    assert response.status_code == 200
    body = response.json()
    assert body["recommendations"]
    assert body["recommendations"][0]["rank"] == 1
