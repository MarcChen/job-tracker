import pytest
from unittest.mock import patch, MagicMock
from src.sms_alert import SMSAPI, MissingParameter, TooManySMS, ServiceNotEnabled, ServerError  # Adjust import as needed


@pytest.fixture
def sms_api():
    return SMSAPI(user="fake_user", password="fake_password")


@patch("sms_api.requests.get")
def test_send_sms_success(mock_get, sms_api):
    # Mock a successful SMS send
    mock_get.return_value = MagicMock(status_code=200)

    sms_api.send_sms("Test message")
    mock_get.assert_called_once()


@patch("sms_api.requests.get")
def test_send_sms_error_handling(mock_get, sms_api):
    # Test each error scenario
    error_scenarios = [
        (400, MissingParameter),
        (402, TooManySMS),
        (403, ServiceNotEnabled),
        (500, ServerError)
    ]

    for status_code, expected_exception in error_scenarios:
        mock_get.return_value = MagicMock(status_code=status_code)
        with pytest.raises(expected_exception):
            sms_api.send_sms("Test message")
