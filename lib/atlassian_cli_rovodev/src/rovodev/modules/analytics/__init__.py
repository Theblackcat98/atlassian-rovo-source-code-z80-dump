"""Analytics module for RovoDev CLI."""

import os
from typing import Optional

import logfire
from loguru import logger
from opentelemetry.sdk.trace import SpanProcessor
from pydantic_ai import Agent

from ...common.config_model import RovoDevConfig

# Apply OpenTelemetry dependency conflict patch for packaged binaries
from .opentelemetry_patch import apply_opentelemetry_dependency_patch
from .processor import AtlassianAnalyticsSpanProcessor

apply_opentelemetry_dependency_patch()


def initialize_analytics(version: str, config: Optional[RovoDevConfig] = None) -> Optional[SpanProcessor]:
    """Initialize analytics with the given configuration."""
    try:
        # Create the analytics processor
        analytics_processor = AtlassianAnalyticsSpanProcessor(config=config)

        # Configure Logfire in local mode (not sending to logfire.dev)
        def scrub_callback(match: "logfire.ScrubMatch") -> str | None:
            """Custom scrubbing callback that allows session-related attributes."""
            # Allow session-related attributes
            if match.path[0] == "attributes":
                # List of allowed session-related attributes
                allowed_attrs = [
                    "session_id",
                    "current_session_id",
                    "previous_session_id",
                    "session_event_type",
                    "command_name",  # Allow command names even if they contain "session"
                    "sub_command",  # Allow subcommands even if they contain "session"
                    "command_args",  # Allow command args even if they contain "session"
                    "original_content",  # Allow code content even if it contains sensitive words
                ]

                # Check if this is an allowed attribute
                if any(attr in match.path[1] for attr in allowed_attrs):
                    return match.value

            # Let logfire handle other matches
            return None

        logfire.configure(
            service_name="rovodev",
            service_version=version,
            environment="development",
            additional_span_processors=[analytics_processor],
            send_to_logfire=False,  # Local mode only
            console=False,  # Don't print logs to console
            scrubbing=logfire.ScrubbingOptions(callback=scrub_callback),  # Custom scrubbing
        )

        # Enable HTTP client auto-instrumentation (opt-in via environment variable)
        if os.getenv("ROVODEV_ENABLE_HTTP_INSTRUMENTATION", "").lower() == "true":
            try:
                # Auto-instrument all HTTPX calls
                logfire.instrument_httpx()
                logger.debug("HTTPX auto-instrumentation enabled")

                # Auto-instrument all requests calls
                logfire.instrument_requests()
                logger.debug("Requests auto-instrumentation enabled")
            except Exception as e:
                logger.error(f"Error enabling HTTP auto-instrumentation: {e}")
        else:
            logger.debug("HTTP auto-instrumentation disabled (set ROVODEV_ENABLE_HTTP_INSTRUMENTATION=true to enable)")

        # Enable OpenTelemetry instrumentation in Pydantic AI
        try:
            # This one-line magically turns on observability throughout PydanticAI
            Agent.instrument_all()
            logger.debug("Pydantic AI OpenTelemetry instrumentation enabled")
        except Exception as e:
            logger.error(f"Error enabling Pydantic AI OpenTelemetry instrumentation: {e}")

        logger.debug("Analytics initialized successfully")
        return analytics_processor

    except Exception as e:
        # Fail gracefully if analytics initialization fails
        logger.error(f"Failed to initialize analytics: {e}")
        return None
