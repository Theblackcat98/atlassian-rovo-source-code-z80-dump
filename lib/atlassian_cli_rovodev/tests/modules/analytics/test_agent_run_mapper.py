"""Test agent run event mapper."""

import json

import pytest

from rovodev.modules.analytics.mappers.agent_run import AgentRunEventMapper


@pytest.fixture
def agent_run_mapper():
    return AgentRunEventMapper(collect_prompts=True)


@pytest.fixture
def events_json():
    """Sample events JSON with system and user messages."""
    events = [
        {"content": "[Scrubbed due to 'session']", "role": "system", "event.name": "gen_ai.system.message"},
        {"content": "help me with code", "role": "user", "event.name": "gen_ai.user.message"},
    ]
    return json.dumps(events)


def test_can_map_agent_run(agent_run_mapper):
    """Test that mapper recognizes agent run spans."""
    span_dict = {"name": "agent run"}
    assert agent_run_mapper.can_map(span_dict, is_start=True)

    span_dict = {"name": "something else"}
    assert not agent_run_mapper.can_map(span_dict, is_start=True)


def test_map_start_event(agent_run_mapper, events_json):
    """Test mapping of start events."""
    span_dict = {"name": "agent run", "attributes": {"all_messages_events": events_json}}

    event = agent_run_mapper.map_event(span_dict, is_start=True)
    assert event["action"] == "started"
    assert event["source"] == "rovodev agent started"
    assert event["action_subject"].endswith("agent_run")
    assert event["attributes"]["prompt"] == "help me with code"


def test_map_complete_event(agent_run_mapper, events_json):
    """Test mapping of complete events."""
    span_dict = {
        "name": "agent run",
        "attributes": {"all_messages_events": events_json},
        "start_time": 1_000_000,  # 1ms in nanoseconds
        "end_time": 2_000_000,  # 2ms in nanoseconds
    }

    event = agent_run_mapper.map_event(span_dict, is_start=False)
    assert event["action"] == "completed"
    assert event["source"] == "rovodev agent completed"
    assert event["action_subject"].endswith("agent_run")
    assert event["attributes"]["prompt"] == "help me with code"
    assert event["attributes"]["duration_ms"] == 1  # 1ms duration
    assert event["attributes"]["success"] is True


def test_map_error_event(agent_run_mapper, events_json):
    """Test mapping of error events."""
    span_dict = {
        "name": "agent run",
        "status": {"status_code": "ERROR"},
        "attributes": {
            "error.type": "TestError",
            "error.message": "Test error message",
            "all_messages_events": events_json,
        },
    }

    event = agent_run_mapper.map_event(span_dict, is_start=False)
    assert event["action"] == "error"
    assert event["source"] == "rovodev agent error"
    assert event["action_subject"].endswith("agent_run")
    assert event["attributes"]["prompt"] == "help me with code"
    assert event["attributes"]["error_type"] == "TestError"
    assert event["attributes"]["error_message"] == "Test error message"


def test_invalid_events_json(agent_run_mapper):
    """Test handling of invalid events JSON."""
    span_dict = {"name": "agent run", "attributes": {"all_messages_events": "invalid json"}}

    event = agent_run_mapper.map_event(span_dict, is_start=True)
    assert event["action"] == "started"
    assert "prompt" not in event["attributes"]


def test_scrubbed_messages_only(agent_run_mapper):
    """Test handling when all messages are scrubbed."""
    events = [
        {"content": "[Scrubbed due to 'session']", "role": "system", "event.name": "gen_ai.system.message"},
        {"content": "[Scrubbed due to 'session']", "role": "user", "event.name": "gen_ai.user.message"},
    ]

    span_dict = {"name": "agent run", "attributes": {"all_messages_events": json.dumps(events)}}

    event = agent_run_mapper.map_event(span_dict, is_start=True)
    assert event["action"] == "started"
    assert "prompt" not in event["attributes"]


def test_prompt_collection_disabled():
    """Test that prompts are not collected when disabled."""
    mapper = AgentRunEventMapper(collect_prompts=False)
    events = [{"content": "help me with code", "role": "user", "event.name": "gen_ai.user.message"}]

    span_dict = {"name": "agent run", "attributes": {"all_messages_events": json.dumps(events)}}

    event = mapper.map_event(span_dict, is_start=True)
    assert event["action"] == "started"
    assert "prompt" not in event["attributes"]
