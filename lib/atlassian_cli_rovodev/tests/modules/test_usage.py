from unittest.mock import MagicMock, patch

import pytest

import nemo
from rovodev.modules.usage import handle_usage_command


@pytest.fixture(autouse=True)
def set_auth_method():
    """Fixture to set the authentication method before each test."""
    original_auth_method = nemo.AUTH_METHOD
    nemo.AUTH_METHOD = "api_token"
    yield
    nemo.AUTH_METHOD = original_auth_method


def test_usage_not_api_token():
    nemo.AUTH_METHOD = "slauth"
    result = handle_usage_command()
    assert "/usage is only available when using API_TOKEN authentication." in result


def test_usage_success(capsys):
    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None
    mock_response.json.return_value = {
        "balance": {
            "dailyTotal": 10000000,
            "dailyRemaining": 9999974,
            "dailyUsed": 26,
        }
    }
    with patch("rovodev.modules.usage.get_ai_gateway_headers", return_value={"Authorization": "test"}):
        with patch("rovodev.modules.usage.httpx.get", return_value=mock_response):
            handle_usage_command()
            out = capsys.readouterr().out
            assert "Total Allowed:      10,000,000" in out
            assert "Remaining Balance:  9,999,974" in out
            assert "Used Today:         26" in out


def test_usage_reset_message_when_retry_after_seconds_with_no_remaining(capsys):
    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None
    mock_response.json.return_value = {
        "balance": {
            "dailyTotal": 10000000,
            "dailyRemaining": 0,
            "dailyUsed": 10000000,
        },
        "retryAfterSeconds": 3661,
    }
    with patch("rovodev.modules.usage.get_ai_gateway_headers", return_value={"Authorization": "test"}):
        with patch("rovodev.modules.usage.httpx.get", return_value=mock_response):
            handle_usage_command()
            out = capsys.readouterr().out
            assert "Total Allowed:      10,000,000" in out
            assert "Remaining Balance:  0" in out
            assert "Used Today:         10,000,000" in out
            assert "Your daily token allowance resets in 1 hour, 1 minute and 1 second." in out
