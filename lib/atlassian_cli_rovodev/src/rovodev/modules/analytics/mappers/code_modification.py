"""Code modification event mapper."""

import json
from pathlib import Path
from typing import Any, Dict, Optional

from loguru import logger

from ..code_metrics import calculate_code_changes
from ..file_type_utils import get_file_type_and_language
from .base import SpanEventMapper


class CodeModificationMapper(SpanEventMapper):
    """Maps code modification tool events to analytics events."""

    def can_map(self, span_dict: Dict[str, Any], is_start: bool) -> bool:
        """Check if this is a code modification tool."""
        attributes = span_dict.get("attributes", {})
        tool_name = attributes.get("gen_ai.tool.name", "")
        return tool_name in ["find_and_replace_code", "create_file", "delete_file"]

    def _calculate_metrics(self, tool_name: str, original_content: str, current_content: str) -> tuple[int, int]:
        """Calculate lines added and removed based on tool type and content."""
        original_lines = len(original_content.splitlines()) if original_content else 0
        current_lines = len(current_content.splitlines()) if current_content else 0

        if tool_name == "create_file":
            return current_lines, 0
        elif tool_name == "delete_file":
            return 0, original_lines
        else:  # find_and_replace_code
            metrics = calculate_code_changes(original_content, current_content)
            return metrics["lines_added"], metrics["lines_removed"]

    def map_event(
        self, span_dict: Dict[str, Any], is_start: bool, span: Optional[Any] = None
    ) -> Optional[Dict[str, Any]]:
        """Map a code modification tool event to analytics event."""
        attributes = span_dict.get("attributes", {})
        tool_name = attributes.get("gen_ai.tool.name", "")

        if is_start:
            try:
                args = json.loads(attributes.get("tool_arguments", "{}"))
                file_path = args.get("file_path")

                if tool_name == "create_file":
                    # For create, store empty string as original
                    if span:
                        span.set_attribute("original_content", "")
                else:  # Both delete and modify need to store current content
                    if file_path and Path(file_path).exists():
                        content = Path(file_path).read_text()
                        if span:
                            span.set_attribute("original_content", content)
            except Exception as e:
                logger.debug(f"Failed to read original content: {e}")
            return None

        # On completion, just count the lines
        try:
            args = json.loads(attributes.get("tool_arguments", "{}"))
            file_path = args.get("file_path")
            if not file_path:
                return None

            # Get original content
            original = attributes.get("original_content")
            if original is None and tool_name != "create_file":
                return None

            original = original or ""
            original_lines = len(original.splitlines()) if original else 0

            # Get current content (empty string for delete)
            current = ""
            if tool_name != "delete_file":
                if not Path(file_path).exists():
                    return None
                current = Path(file_path).read_text()
            current_lines = len(current.splitlines()) if current else 0

            # Get file type and language
            file_type, language = get_file_type_and_language(file_path)

            # Calculate metrics
            lines_added, lines_removed = self._calculate_metrics(tool_name, original, current)

            return {
                "source": "rovodev code completed",
                "action": "completed",
                "action_subject": "code_modification",
                "attributes": {
                    "tool_name": tool_name,
                    "file_type": file_type,
                    "language": language,
                    "lines_added": lines_added,
                    "lines_removed": lines_removed,
                },
            }

        except Exception as e:
            logger.debug(f"Failed to calculate metrics: {e}")
            return None
