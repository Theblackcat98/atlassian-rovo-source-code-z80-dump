"""Tests for analytics event mappers."""

import unittest
from unittest.mock import MagicMock

from rovodev.modules.analytics.instrumentation.session import CurrentSession
from rovodev.modules.analytics.mappers.base import DEFAULT_SESSION_ID, SpanEventMapper


class TestMapper(SpanEventMapper):
    """Test mapper implementation."""

    def can_map(self, span_dict, is_start):
        return True

    def map_event(self, span_dict, is_start, span=None):
        return {}


class TestEventMappers(unittest.TestCase):
    def setUp(self):
        self.mapper = TestMapper()
        # Reset current session before each test
        CurrentSession.set_session_id(None)

    def test_extract_session_id(self):
        """Test session ID extraction."""
        # Test with current session set
        CurrentSession.set_session_id("test-session")
        session_id = self.mapper.extract_session_id({})
        self.assertEqual(session_id, "test-session")

        # Test with no current session
        CurrentSession.set_session_id(None)
        session_id = self.mapper.extract_session_id({})
        self.assertEqual(session_id, DEFAULT_SESSION_ID)

    def test_get_common_attributes(self):
        """Test getting common attributes."""
        # Set up current session
        CurrentSession.set_session_id("test-session")

        # Get common attributes
        span_dict = {"attributes": {}}
        attrs = self.mapper.get_common_attributes(span_dict)

        # Verify session ID is included
        self.assertEqual(attrs["sessionId"], "test-session")
        self.assertEqual(attrs["singleInstrumentationID"], "test-session")
