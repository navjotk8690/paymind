from paymind.connectors.synthetic import sample_evaluate_request
from paymind.evaluation.service import EvaluationService


def test_service_wraps_decision_engine_response():
    service = EvaluationService.from_registry()
    response = service.evaluate(sample_evaluate_request())

    assert response.recommendations
    assert response.recommendations[0].rank == 1
    assert response.recommendations[0].arrival_p90_minutes >= response.recommendations[0].arrival_p50_minutes
