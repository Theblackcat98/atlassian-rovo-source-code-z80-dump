"""Tests for dynamic_config module."""

from unittest.mock import Mock, patch

import pytest

from rovodev.common.dynamic_config import DynamicConfigData, DynamicConfiguration


def test_dynamic_config_data():
    """Test DynamicConfigData dataclass."""
    config = DynamicConfigData(is_internal=True, model_id=["test-model", "test-model-2"], banned=False)
    assert config.is_internal is True
    assert config.model_id == ["test-model", "test-model-2"]


@pytest.fixture
def mock_requests():
    """Mock requests.post."""
    with patch("requests.post") as mock_post:
        yield mock_post


def test_is_internal_detection():
    """Test internal user detection based on email domain."""
    with patch("requests.post") as mock_post:
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"value": {"model_id": ["test-model", "test-model-2"], "banned": False}}
        mock_post.return_value = mock_response

        # Test internal user
        internal_config = DynamicConfiguration("test@atlassian.com")
        assert internal_config.config().is_internal is True

        # Test external user
        external_config = DynamicConfiguration("test@example.com")
        assert external_config.config().is_internal is False


def test_model_id_from_config():
    """Test model ID is correctly retrieved from config response."""
    with patch("requests.post") as mock_post:
        # Mock response with custom model ID
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"value": {"model_id": ["custom-model-v1"], "banned": True}}
        mock_post.return_value = mock_response

        config = DynamicConfiguration("test@example.com")
        assert config.config().model_id == ["custom-model-v1"]
