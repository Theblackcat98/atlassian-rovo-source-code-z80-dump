"""Tests for Atlassian Analytics client."""

from unittest.mock import MagicMock, patch

import pytest
from analytics_client.models import Env, Platform, Tenant, TrackEvent, User

from rovodev.modules.analytics.atlassian_client import AtlassianAnalyticsClient
from rovodev.modules.analytics.models import UserInfo


@pytest.fixture
def mock_user_info():
    """Mock user info."""
    return UserInfo(
        account_id="test",  # Username from email (no hashing)
        cloud_id="test-cloud-id",
        is_internal=True,
        user_type="atlassianAccount",
        org_id="test-org-id",
        auth_type="api_token",
    )


@pytest.fixture
def mock_anonymous_user_info():
    """Mock anonymous user info."""
    return UserInfo(
        account_id="anonymous",
        cloud_id="test-cloud-id",
        is_internal=False,
        user_type="anonymous",
        org_id=None,
        auth_type=None,
    )


def test_client_initialization(mock_user_info):
    """Test client initialization with user info."""
    with (
        patch(
            "rovodev.modules.analytics.atlassian_client.get_user_and_tenant_info",
            return_value=mock_user_info,
        ),
        patch("rovodev.modules.analytics.atlassian_client.Client") as mock_client_class,
    ):
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client

        client = AtlassianAnalyticsClient()
        assert client.user_id == mock_user_info.account_id  # Should be hashed
        assert client.tenant_id == mock_user_info.cloud_id
        assert client.is_internal == mock_user_info.is_internal
        assert client.user_type == User.ATLASSIAN_ACCOUNT  # Always ATLASSIAN_ACCOUNT
        assert client.product == "rovodev"
        assert client.subproduct == "rovodev"
        mock_client_class.assert_called_once()


def test_client_initialization_anonymous(mock_anonymous_user_info):
    """Test client initialization with anonymous user."""
    with (
        patch(
            "rovodev.modules.analytics.atlassian_client.get_user_and_tenant_info",
            return_value=mock_anonymous_user_info,
        ),
        patch("rovodev.modules.analytics.atlassian_client.Client") as mock_client_class,
    ):
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client

        client = AtlassianAnalyticsClient()
        assert client.user_id == mock_anonymous_user_info.account_id
        assert client.tenant_id == mock_anonymous_user_info.cloud_id
        assert client.is_internal == mock_anonymous_user_info.is_internal
        assert client.user_type == User.ATLASSIAN_ACCOUNT  # Always ATLASSIAN_ACCOUNT
        assert client.product == "rovodev"
        assert client.subproduct == "rovodev"
        mock_client_class.assert_called_once()


def test_send_event(mock_user_info):
    """Test sending an event."""
    with (
        patch(
            "rovodev.modules.analytics.atlassian_client.get_user_and_tenant_info",
            return_value=mock_user_info,
        ),
        patch("rovodev.modules.analytics.atlassian_client.Client") as mock_client_class,
    ):
        mock_client = MagicMock()
        mock_client.track.return_value = (True, "")
        mock_client_class.return_value = mock_client

        client = AtlassianAnalyticsClient()
        event_data = {
            "source": "test_source",
            "action": "test_action",
            "action_subject": "test_subject",
            "attributes": {"test_key": "test_value"},
        }
        client.send_event(event_data)

        mock_client.track.assert_called_once()
        track_event = mock_client.track.call_args[0][0]
        assert isinstance(track_event, TrackEvent)
        assert track_event.source == "test_source"
        assert track_event.action == "test_action"
        assert track_event.action_subject == "test_subject"
        assert track_event.user_id == mock_user_info.account_id  # Should be hashed
        assert track_event.user_type == User.ATLASSIAN_ACCOUNT  # Always ATLASSIAN_ACCOUNT
        assert track_event.tenant_id == "test-cloud-id"
        assert track_event.tenant_type == Tenant.CLOUD_ID
        # Check that enhanced attributes were added (orgId is now top-level)
        expected_attributes = {"test_key": "test_value", "authType": "api_token", "isInternal": True}
        assert track_event.attributes == expected_attributes

        # Check that orgId is set as top-level property
        assert track_event.org_id == "test-org-id"

        # Check that platform is set
        assert hasattr(track_event, "platform")
        assert track_event.platform in Platform.values()


class TestPlatformDetection:
    """Tests for platform detection functionality."""

    @patch("platform.system")
    def test_detect_platform_mac(self, mock_system, mock_user_info):
        """Test platform detection for macOS."""
        mock_system.return_value = "Darwin"

        with (
            patch(
                "rovodev.modules.analytics.atlassian_client.get_user_and_tenant_info",
                return_value=mock_user_info,
            ),
            patch("rovodev.modules.analytics.atlassian_client.Client") as mock_client_class,
        ):
            mock_client = MagicMock()
            mock_client_class.return_value = mock_client

            client = AtlassianAnalyticsClient()
            assert client.platform == Platform.MAC

    @patch("platform.system")
    def test_detect_platform_linux(self, mock_system, mock_user_info):
        """Test platform detection for Linux."""
        mock_system.return_value = "Linux"

        with (
            patch(
                "rovodev.modules.analytics.atlassian_client.get_user_and_tenant_info",
                return_value=mock_user_info,
            ),
            patch("rovodev.modules.analytics.atlassian_client.Client") as mock_client_class,
        ):
            mock_client = MagicMock()
            mock_client_class.return_value = mock_client

            client = AtlassianAnalyticsClient()
            assert client.platform == Platform.LINUX

    @patch("platform.system")
    def test_detect_platform_windows(self, mock_system, mock_user_info):
        """Test platform detection for Windows."""
        mock_system.return_value = "Windows"

        with (
            patch(
                "rovodev.modules.analytics.atlassian_client.get_user_and_tenant_info",
                return_value=mock_user_info,
            ),
            patch("rovodev.modules.analytics.atlassian_client.Client") as mock_client_class,
        ):
            mock_client = MagicMock()
            mock_client_class.return_value = mock_client

            client = AtlassianAnalyticsClient()
            assert client.platform == Platform.WINDOWS

    @patch("platform.system")
    def test_detect_platform_unknown(self, mock_system, mock_user_info):
        """Test platform detection for unknown platform."""
        mock_system.return_value = "UnknownOS"

        with (
            patch(
                "rovodev.modules.analytics.atlassian_client.get_user_and_tenant_info",
                return_value=mock_user_info,
            ),
            patch("rovodev.modules.analytics.atlassian_client.Client") as mock_client_class,
        ):
            mock_client = MagicMock()
            mock_client_class.return_value = mock_client

            client = AtlassianAnalyticsClient()
            assert client.platform == Platform.UNKNOWN

    def test_platform_included_in_track_event(self, mock_user_info):
        """Test that platform is included in TrackEvent."""
        with (
            patch(
                "rovodev.modules.analytics.atlassian_client.get_user_and_tenant_info",
                return_value=mock_user_info,
            ),
            patch("rovodev.modules.analytics.atlassian_client.Client") as mock_client_class,
            patch("platform.system", return_value="Darwin"),
        ):
            mock_client = MagicMock()
            mock_client.track.return_value = (True, "")
            mock_client_class.return_value = mock_client

            client = AtlassianAnalyticsClient()
            event_data = {
                "source": "test_source",
                "action": "test_action",
                "action_subject": "test_subject",
                "attributes": {"test_key": "test_value"},
            }
            client.send_event(event_data)

            mock_client.track.assert_called_once()
            track_event = mock_client.track.call_args[0][0]
            assert track_event.platform == Platform.MAC
