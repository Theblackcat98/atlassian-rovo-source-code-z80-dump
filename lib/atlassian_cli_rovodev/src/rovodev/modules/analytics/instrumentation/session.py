"""Session instrumentation utilities."""

import logfire
from loguru import logger


class CurrentSession:
    """Simple holder for current session information."""

    _current_session_id: str | None = None

    @classmethod
    def get_session_id(cls) -> str | None:
        return cls._current_session_id

    @classmethod
    def set_session_id(cls, session_id: str | None):
        cls._current_session_id = session_id


def track_session_created(session_id, title=None):
    """Track when a new session is created."""
    logger.debug(f"About to create span for new session: {session_id}")
    CurrentSession.set_session_id(session_id)  # Set as current session

    with logfire.span("session created") as span:
        span.set_attribute("current_session_id", session_id)
        span.set_attribute("session_event_type", "created")
        if title:
            span.set_attribute("session_title", title)


def track_session_switched(from_session_id, to_session_id):
    """Track when the user switches from one session to another."""
    logger.debug(f"About to create span for session switch: {from_session_id} -> {to_session_id}")
    CurrentSession.set_session_id(to_session_id)  # Update current session
    with logfire.span("session switched") as span:
        span.set_attribute("current_session_id", to_session_id)
        span.set_attribute("session_event_type", "switched")
        span.set_attribute("previous_session_id", from_session_id)


def track_session_restored(session_id, title=None, num_messages=None):
    """Track when a session is restored from storage."""
    logger.debug(f"About to create span for restored session: {session_id}")
    CurrentSession.set_session_id(session_id)  # Set as current session

    with logfire.span("session restored") as span:
        span.set_attribute("current_session_id", session_id)
        span.set_attribute("session_event_type", "restored")
        if title:
            span.set_attribute("session_title", title)
        if num_messages is not None:
            span.set_attribute("num_messages", num_messages)


def track_session_forked(parent_session_id, new_session_id, title=None):
    """Track when a session is forked from an existing one."""
    CurrentSession.set_session_id(new_session_id)  # Set new session as current
    with logfire.span("session forked") as span:
        span.set_attribute("current_session_id", new_session_id)
        span.set_attribute("session_event_type", "forked")
        span.set_attribute("parent_session_id", parent_session_id)
        if title:
            span.set_attribute("session_title", title)


def track_session_deleted(session_id, title=None):
    """Track when a session is deleted."""
    logger.debug(f"About to create span for deleted session: {session_id}")
    with logfire.span("session deleted") as span:
        span.set_attribute("deleted_session_id", session_id)
        span.set_attribute("session_event_type", "deleted")
        if title:
            span.set_attribute("session_title", title)
