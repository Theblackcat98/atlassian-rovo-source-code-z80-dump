"""Tests for event mapper registry."""

from typing import Any, Dict, Optional

import pytest

from rovodev.modules.analytics.mappers.base import SpanEventMapper
from rovodev.modules.analytics.mappers.registry import EventMapperRegistry


class TestMapper(SpanEventMapper):
    """Test mapper that always maps."""

    def can_map(self, span_dict: Dict[str, Any], is_start: bool) -> bool:
        return True

    def map_event(
        self, span_dict: Dict[str, Any], is_start: bool, span: Optional[Any] = None
    ) -> Optional[Dict[str, Any]]:
        return {"test": "event"}


class ToolMapper(SpanEventMapper):
    """Test mapper that maps tool spans."""

    def can_map(self, span_dict: Dict[str, Any], is_start: bool) -> bool:
        return span_dict.get("type") == "tool"

    def map_event(
        self, span_dict: Dict[str, Any], is_start: bool, span: Optional[Any] = None
    ) -> Optional[Dict[str, Any]]:
        return {"tool": "event"}


class CodeMapper(SpanEventMapper):
    """Test mapper that maps code tool spans."""

    def can_map(self, span_dict: Dict[str, Any], is_start: bool) -> bool:
        return span_dict.get("type") == "tool" and span_dict.get("tool") == "code"

    def map_event(
        self, span_dict: Dict[str, Any], is_start: bool, span: Optional[Any] = None
    ) -> Optional[Dict[str, Any]]:
        return {"code": "event"}


@pytest.fixture
def registry():
    """Create a fresh registry for each test."""
    return EventMapperRegistry()


def test_register_mapper(registry):
    """Test registering a mapper."""
    mapper = TestMapper()
    registry.register_mapper(mapper)
    assert len(registry._mappers) == 1
    assert registry._mappers[0] == mapper


def test_get_no_mappers(registry):
    """Test getting mappers when none match."""
    mappers = registry.get_mappers_for_span({"type": "unknown"}, is_start=True)
    assert len(mappers) == 0


def test_get_single_mapper(registry):
    """Test getting a single matching mapper."""
    mapper = ToolMapper()
    registry.register_mapper(mapper)

    mappers = registry.get_mappers_for_span({"type": "tool"}, is_start=True)
    assert len(mappers) == 1
    assert mappers[0] == mapper


def test_get_multiple_mappers(registry):
    """Test getting multiple matching mappers."""
    tool_mapper = ToolMapper()
    code_mapper = CodeMapper()
    registry.register_mapper(tool_mapper)
    registry.register_mapper(code_mapper)

    # Both mappers should match
    mappers = registry.get_mappers_for_span({"type": "tool", "tool": "code"}, is_start=True)
    assert len(mappers) == 2
    assert tool_mapper in mappers
    assert code_mapper in mappers


def test_mapper_order(registry):
    """Test that mappers are returned in registration order."""
    mapper1 = TestMapper()
    mapper2 = TestMapper()
    registry.register_mapper(mapper1)
    registry.register_mapper(mapper2)

    mappers = registry.get_mappers_for_span({}, is_start=True)
    assert len(mappers) == 2
    assert mappers[0] == mapper1  # First registered
    assert mappers[1] == mapper2  # Second registered
