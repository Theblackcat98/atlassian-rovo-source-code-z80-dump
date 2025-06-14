"""Tests for HTTP API event mapper using HTTP auto-instrumentation."""

from unittest.mock import Mock

import pytest

from rovodev.modules.analytics.mappers.external_api import ExternalAPIEventMapper


class TestExternalAPIEventMapper:
    """Test the ExternalAPIEventMapper class with HTTP auto-instrumentation."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mapper = ExternalAPIEventMapper()

    def test_can_map_http_span(self):
        """Test that mapper can identify HTTP spans."""
        span_dict = {
            "name": "HTTP GET",
            "attributes": {
                "http.method": "GET",
                "http.url": "https://api.statsig.com/v1/get_config",
            },
        }
        assert self.mapper.can_map(span_dict, True)

    def test_can_map_any_http_span(self):
        """Test that mapper can identify any HTTP call."""
        span_dict = {
            "name": "HTTP GET",
            "attributes": {
                "http.method": "GET",
                "http.url": "https://example.com/api/test",
            },
        }
        assert self.mapper.can_map(span_dict, True)

    def test_cannot_map_non_http_span(self):
        """Test that mapper ignores non-HTTP spans."""
        span_dict = {"name": "llm_call", "attributes": {}}
        assert not self.mapper.can_map(span_dict, False)

    def test_can_map_localhost_http_span(self):
        """Test that mapper can identify localhost HTTP calls."""
        span_dict = {
            "name": "HTTP GET",
            "attributes": {
                "http.method": "GET",
                "http.url": "http://localhost:8080/api/test",
            },
        }
        assert self.mapper.can_map(span_dict, False)

    def test_get_service_name_statsig(self):
        """Test service name extraction for Statsig."""
        service_name = self.mapper._get_service_name("https://api.statsig.com/v1/get_config")
        assert service_name == "statsig"

    def test_get_service_name_rovodev_api(self):
        """Test service name extraction for RovoDev API."""
        service_name = self.mapper._get_service_name("https://api.atlassian.com/rovodev/v2/credits/check")
        assert service_name == "rovodev_api"

    def test_get_service_name_general_atlassian(self):
        """Test service name extraction for general Atlassian API."""
        service_name = self.mapper._get_service_name("https://api.atlassian.com/ex/confluence/v1/pages")
        assert service_name == "atlassian_api"

    def test_get_service_name_localhost(self):
        """Test service name extraction for localhost."""
        service_name = self.mapper._get_service_name("http://localhost:8080/api/test")
        assert service_name == "localhost"

    def test_get_service_name_unknown_domain(self):
        """Test service name extraction for unknown domain."""
        service_name = self.mapper._get_service_name("https://example.com/api/test")
        assert service_name == "example.com"

    def test_map_started_event(self):
        """Test mapping of HTTP started event."""
        span_dict = {
            "name": "HTTP POST",
            "attributes": {
                "http.method": "POST",
                "http.url": "https://api.statsig.com/v1/get_config",
                "http.request.body.size": 150,
            },
            "start_time": 1000000000000000000,
        }

        event = self.mapper.map_event(span_dict, is_start=True)

        assert event is not None
        assert event["action"] == "started"
        assert event["action_subject"] == "http_api_call"
        assert event["source"] == "rovodev http_api started"

        attributes = event["attributes"]
        assert attributes["service_name"] == "statsig"
        assert attributes["endpoint"] == "https://api.statsig.com/v1/get_config"
        assert attributes["request_method"] == "POST"
        assert attributes["request_size_bytes"] == 150

    def test_map_completed_event(self):
        """Test mapping of HTTP completed event."""
        span_dict = {
            "name": "HTTP GET",
            "attributes": {
                "http.method": "GET",
                "http.url": "https://api.atlassian.com/rovodev/v2/credits/check",
                "http.response.status_code": 200,
                "http.response.body.size": 500,
            },
            "start_time": 1000000000000000000,
            "end_time": 1000000001000000000,  # +1000ms
            "status": {"status_code": "OK"},
        }

        event = self.mapper.map_event(span_dict, is_start=False)

        assert event is not None
        assert event["action"] == "completed"
        assert event["action_subject"] == "http_api_call"
        assert event["source"] == "rovodev http_api completed"

        attributes = event["attributes"]
        assert attributes["service_name"] == "rovodev_api"
        assert attributes["status_code"] == 200
        assert attributes["response_size_bytes"] == 500
        assert attributes["success"] is True
        assert attributes["duration_ms"] == 1000

    def test_map_error_event(self):
        """Test mapping of HTTP error event."""
        span_dict = {
            "name": "HTTP POST",
            "attributes": {
                "http.method": "POST",
                "http.url": "https://api.statsig.com/v1/get_config",
                "http.response.status_code": 500,
                "error.type": "HTTPStatusError",
            },
            "start_time": 1000000000000000000,
            "end_time": 1000000002000000000,  # +2000ms
            "status": {"status_code": "ERROR", "description": "Internal Server Error"},
        }

        event = self.mapper.map_event(span_dict, is_start=False)

        assert event is not None
        assert event["action"] == "error"
        assert event["action_subject"] == "http_api_call"
        assert event["source"] == "rovodev http_api error"

        attributes = event["attributes"]
        assert attributes["service_name"] == "statsig"
        assert attributes["status_code"] == 500
        assert attributes["success"] is False
        assert attributes["error_type"] == "HTTPStatusError"
        assert attributes["error_message"] == "Internal Server Error"
        assert attributes["duration_ms"] == 2000

    def test_map_event_with_minimal_attributes(self):
        """Test mapping with minimal HTTP attributes."""
        span_dict = {
            "name": "HTTP GET",
            "attributes": {
                "http.method": "GET",
                "http.url": "https://api.statsig.com/v1/get_config",
            },
            "start_time": 1000000000000000000,
        }

        event = self.mapper.map_event(span_dict, is_start=True)

        assert event is not None
        attributes = event["attributes"]
        assert attributes["service_name"] == "statsig"
        assert attributes["endpoint"] == "https://api.statsig.com/v1/get_config"
        assert attributes["request_method"] == "GET"
        # Should not have request_size_bytes if not provided
        assert "request_size_bytes" not in attributes

    def test_get_service_name_edge_cases(self):
        """Test service name extraction with edge cases."""
        # Invalid URL
        assert self.mapper._get_service_name("not-a-url") == "unknown"

        # Empty URL
        assert self.mapper._get_service_name("") == "unknown"

        # URL without domain
        assert self.mapper._get_service_name("http://") == "unknown"
