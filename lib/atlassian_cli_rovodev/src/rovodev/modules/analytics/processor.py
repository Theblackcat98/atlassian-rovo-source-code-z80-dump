"""Atlassian Analytics span processor for OpenTelemetry."""

import os
from pathlib import Path
from typing import Any, Dict, Optional

from loguru import logger
from opentelemetry.context import Context
from opentelemetry.sdk.trace import ReadableSpan, SpanProcessor
from opentelemetry.trace import Span

from ...common.config_model import RovoDevConfig
from .atlassian_client import AtlassianAnalyticsClient
from .mappers import EventMapperRegistry, LLMEventMapper
from .mappers.agent_run import AgentRunEventMapper
from .mappers.command import CommandEventMapper
from .mappers.crash import CrashEventMapper
from .mappers.external_api import ExternalAPIEventMapper
from .mappers.mcp import MCPEventMapper
from .mappers.permission import PermissionEventMapper
from .mappers.session import SessionEventMapper
from .mappers.tool import ToolEventMapper


class AtlassianAnalyticsSpanProcessor(SpanProcessor):
    """
    An OpenTelemetry SpanProcessor that converts spans to Atlassian Analytics events
    and sends them via the Atlassian Analytics client.
    """

    def __init__(self, config: Optional[RovoDevConfig] = None):
        """Initialize the analytics processor."""
        # Initialize the client (now uses simplified service-first user info)
        logger.debug("Initializing Atlassian Analytics client")
        self.analytics_client = AtlassianAnalyticsClient(
            environment=os.environ.get("ACRA_ANALYTICS_ENV", "prod"),
            product="rovodev",
            subproduct="rovodev",
        )

        # Initialize the mapper registry
        self.mapper_registry = EventMapperRegistry()

        # Store config
        self.config = config

        # Register mappers
        self._register_mappers()

    def _register_mappers(self):
        """Register all event mappers."""
        # Register the LLM event mapper
        self.mapper_registry.register_mapper(LLMEventMapper())

        # Register the Tool event mapper
        self.mapper_registry.register_mapper(ToolEventMapper())

        # Register the Session event mapper
        self.mapper_registry.register_mapper(SessionEventMapper())

        # Register the Command event mapper
        self.mapper_registry.register_mapper(CommandEventMapper())

        # Register the MCP event mapper
        self.mapper_registry.register_mapper(MCPEventMapper())

        # Register the Permission event mapper
        self.mapper_registry.register_mapper(PermissionEventMapper())

        # Register the Crash event mapper
        self.mapper_registry.register_mapper(CrashEventMapper())

        # Register the Code Modification mapper
        from .mappers.code_modification import CodeModificationMapper

        self.mapper_registry.register_mapper(CodeModificationMapper())

        # Register the Agent Run event mapper
        collect_prompts = False
        if self.config:
            collect_prompts = self.config.logging.enable_prompt_collection
        self.mapper_registry.register_mapper(AgentRunEventMapper(collect_prompts=collect_prompts))

        # Register the HTTP API event mapper
        self.mapper_registry.register_mapper(ExternalAPIEventMapper())

    def on_start(self, span: Span, parent_context: Optional[Context] = None):
        """Process span when it starts."""
        # Convert span to dictionary
        span_dict = self._span_to_dict(span)

        # Find all mappers for the span
        mappers = self.mapper_registry.get_mappers_for_span(span_dict, is_start=True)

        for mapper in mappers:
            # Map the span to an event
            event = mapper.map_event(span_dict, is_start=True, span=span)
            if event:
                # Send the event to Atlassian Analytics
                try:
                    self.analytics_client.send_event(event)
                    logger.debug(f"Sent analytics event from {mapper.__class__.__name__} successfully")
                except Exception as e:
                    logger.error(
                        f"Error sending start event from {mapper.__class__.__name__} to Atlassian Analytics: {e}"
                    )

    def on_end(self, span: ReadableSpan):
        """Process span when it ends."""
        # Convert span to dictionary
        span_dict = self._span_to_dict(span)

        # Find all mappers for the span
        mappers = self.mapper_registry.get_mappers_for_span(span_dict, is_start=False)

        for mapper in mappers:
            # Map the span to an event
            event = mapper.map_event(span_dict, is_start=False, span=span)
            if event:
                # Send the event to Atlassian Analytics
                try:
                    self.analytics_client.send_event(event)
                    logger.debug(f"Sent analytics event from {mapper.__class__.__name__} successfully")
                except Exception as e:
                    logger.error(
                        f"Error sending end event from {mapper.__class__.__name__} to Atlassian Analytics: {e}"
                    )

    def _span_to_dict(self, span) -> Dict[str, Any]:
        """Convert a span to a dictionary with all relevant information."""
        # For ReadableSpan (on_end), we can directly access attributes
        if isinstance(span, ReadableSpan):
            return {
                "name": span.name,
                "kind": str(span.kind),
                "status": {
                    "status_code": span.status.status_code.name,
                    "description": span.status.description,
                },
                "attributes": dict(span.attributes),
                "events": [
                    {"name": event.name, "timestamp": event.timestamp, "attributes": dict(event.attributes)}
                    for event in span.events
                ],
                "start_time": span.start_time,
                "end_time": span.end_time,
            }
        # For Span (on_start), we need to use the span's methods
        else:
            return {
                "name": span.name,
                "kind": str(span.kind),
                "status": "started",  # Custom status for start events
                "attributes": dict(span.attributes),
            }

    def force_flush(self, timeout_millis=30000):
        """Force flush any pending events."""
        pass

    def shutdown(self):
        """Shutdown the processor."""
        pass
