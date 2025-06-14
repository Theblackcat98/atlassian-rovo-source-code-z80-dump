"""Test configuration for UI components."""

from datetime import datetime, timedelta

import pytest


@pytest.fixture
def sample_messages():
    """Create sample message data for testing."""
    return [
        {"kind": "request", "parts": [{"content": "User message 1", "part_kind": "user-prompt"}]},
        {"kind": "response", "parts": [{"content": "Assistant response 1", "part_kind": "text"}]},
    ]


@pytest.fixture
def sample_session(sample_messages):
    """Create sample session data for testing."""
    now = datetime.now()
    return {
        "session_id": "test-session",
        "title": "Test Session",
        "created": now.strftime("%Y-%m-%d %H:%M:%S"),
        "last_saved": now.strftime("%Y-%m-%d %H:%M:%S"),
        "num_messages": len(sample_messages),
        "total_tokens": 1000,
        "context_limit": 2000,
        "message_history": sample_messages,
    }
