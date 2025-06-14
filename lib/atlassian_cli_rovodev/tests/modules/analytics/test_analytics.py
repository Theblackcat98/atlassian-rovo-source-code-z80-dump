"""Tests for the analytics module."""

import unittest
from unittest.mock import patch

from rovodev.modules.analytics import initialize_analytics
from rovodev.modules.analytics.atlassian_client import AtlassianAnalyticsClient
from rovodev.modules.analytics.processor import AtlassianAnalyticsSpanProcessor


class TestAnalytics(unittest.TestCase):
    """Tests for the analytics module."""

    @patch("logfire.configure")
    @patch("rovodev.modules.analytics.user_info.nemo", create=True)
    def test_initialize_analytics(self, mock_nemo, mock_configure):
        """Test that analytics initialization works."""
        # Set up mock nemo attributes
        mock_nemo.AUTH_METHOD = "slauth"
        mock_nemo.USER_EMAIL = None
        mock_nemo.CLOUD_ID = "a436116f-02ce-4520-8fbb-7301462a1674"  # Default AI Gateway cloud ID

        processor = initialize_analytics("0.1.0")

        # Check that the processor was created
        assert isinstance(processor, AtlassianAnalyticsSpanProcessor)
        assert isinstance(processor.analytics_client, AtlassianAnalyticsClient)

        # Check that logfire was configured
        mock_configure.assert_called_once()
