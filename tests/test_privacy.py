from paymind.settings import load_settings


def test_default_privacy_is_stateless():
    settings = load_settings()
    assert settings.privacy.persist_requests is False
    assert settings.privacy.persist_responses is False
    assert settings.privacy.log_request_payloads is False
    assert settings.privacy.log_response_payloads is False
