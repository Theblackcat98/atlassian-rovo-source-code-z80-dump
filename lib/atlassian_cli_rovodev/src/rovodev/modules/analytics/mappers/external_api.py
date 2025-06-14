"""HTTP API event mapper for analytics using HTTP auto-instrumentation."""

from typing import Any, Dict, Optional
from urllib.parse import urlparse

from .base import SpanEventMapper


class ExternalAPIEventMapper(SpanEventMapper):
    """Maps HTTP client spans from auto-instrumentation to HTTP API analytics events."""

    def can_map(self, span_dict: Dict[str, Any], is_start: bool) -> bool:
        """Check if this span represents an HTTP call."""
        attributes = span_dict.get("attributes", {})

        # Must be an HTTP client span
        return "http.method" in attributes and "http.url" in attributes

    def _get_service_name(self, url: str) -> str:
        """Extract service name from URL."""
        try:
            parsed = urlparse(url)
            domain = parsed.netloc.lower()

            # Special handling for known services
            if "api.statsig.com" in domain:
                return "statsig"
            elif "api.atlassian.com" in domain:
                if "/rovodev/" in parsed.path:
                    return "rovodev_api"
                else:
                    return "atlassian_api"
            elif "localhost" in domain or "127.0.0.1" in domain:
                return "localhost"
            else:
                return domain or "unknown"
        except Exception:
            return "unknown"

    def map_event(
        self, span_dict: Dict[str, Any], is_start: bool, span: Optional[Any] = None
    ) -> Optional[Dict[str, Any]]:
        """Map HTTP span to HTTP API analytics event."""
        attributes = span_dict.get("attributes", {})

        # Extract HTTP details
        url = attributes.get("http.url", "unknown")
        method = attributes.get("http.method", "unknown")
        service_name = self._get_service_name(url)

        # Common attributes for all HTTP API events
        event_attributes = self.get_common_attributes(span_dict)
        event_attributes.update(
            {
                "service_name": service_name,
                "endpoint": url,
                "request_method": method.upper(),
                "timestamp": self.format_timestamp(self.get_span_timestamp(span_dict, is_start)),
            }
        )

        if is_start:
            # Started event - add request details if available
            if "http.request.body.size" in attributes:
                event_attributes["request_size_bytes"] = attributes["http.request.body.size"]
            action = "started"
        else:
            # Completed/Error event
            status = span_dict.get("status", {})
            is_error = status.get("status_code") == "ERROR"

            # Add completion metrics
            event_attributes.update(
                {
                    "duration_ms": self.calculate_duration_ms(span_dict["start_time"], span_dict["end_time"]),
                    "success": not is_error,
                }
            )

            # Add HTTP response details
            if "http.response.status_code" in attributes:
                event_attributes["status_code"] = attributes["http.response.status_code"]
            if "http.response.body.size" in attributes:
                event_attributes["response_size_bytes"] = attributes["http.response.body.size"]

            if is_error:
                # Add error details
                event_attributes.update(
                    {
                        "error_type": attributes.get("error.type", "unknown"),
                        "error_message": status.get("description", ""),
                    }
                )
                action = "error"
            else:
                action = "completed"

        return {
            "source": f"rovodev http_api {action}",
            "action": action,
            "action_subject": "http_api_call",
            "attributes": event_attributes,
        }
