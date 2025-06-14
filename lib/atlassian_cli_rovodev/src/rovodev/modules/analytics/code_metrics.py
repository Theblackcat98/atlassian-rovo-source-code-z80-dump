"""Utilities for calculating code modification metrics."""

from difflib import unified_diff
from typing import Dict


def calculate_code_changes(original_content: str, new_content: str) -> Dict[str, int]:
    """
    Calculate metrics about code changes between two contents.

    Args:
        original_content: Original file content
        new_content: New file content

    Returns:
        Dictionary with metrics:
        - lines_added: Number of lines added
        - lines_removed: Number of lines removed
    """
    metrics = {"lines_added": 0, "lines_removed": 0}

    # Handle empty content cases
    if original_content == new_content:
        return metrics

    # Generate diff
    diff = list(unified_diff(original_content.splitlines(keepends=True), new_content.splitlines(keepends=True)))

    # Count changes
    for line in diff:
        # Skip diff headers
        if line.startswith(("---", "+++", "@@")):
            continue

        # Count actual changes
        if line.startswith("+"):
            metrics["lines_added"] += 1
        elif line.startswith("-"):
            metrics["lines_removed"] += 1

    return metrics
