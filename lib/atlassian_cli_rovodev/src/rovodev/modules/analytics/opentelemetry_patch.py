"""OpenTelemetry monkey patch for handling dependency conflicts in packaged binaries."""

import typing


def apply_opentelemetry_dependency_patch() -> None:
    """
    Apply monkey patch to fix OpenTelemetry dependency conflicts in packaged binaries.

    This patch addresses issues where OpenTelemetry cannot detect library versions
    in PyInstaller packaged binaries, causing DependencyConflict errors even when
    the libraries are available.
    """
    try:
        import opentelemetry.instrumentation.dependencies
        from opentelemetry.instrumentation.dependencies import DependencyConflict

        # Store the original function
        orig_get_dependency_conflicts = opentelemetry.instrumentation.dependencies.get_dependency_conflicts

        def rovodev_dependency_conflicts(
            deps: typing.Collection[str],
        ) -> DependencyConflict | None:
            """Custom dependency conflict handler for RovoDev CLI packaging."""

            # Get the original conflict
            conflict = orig_get_dependency_conflicts(deps)

            # If there's no conflict, return None
            if not conflict:
                return None

            # If the dependency is not found, try to detect it manually in packaged binaries
            if not conflict.found:
                # Check if this is for httpx or requests
                if any("httpx" in dep for dep in deps):
                    try:
                        import httpx

                        # If we can import httpx, create a fake "no conflict" result
                        return None
                    except ImportError:
                        # httpx really isn't available, keep the original conflict
                        return conflict

                if any("requests" in dep for dep in deps):
                    try:
                        import requests

                        # If we can import requests, create a fake "no conflict" result
                        return None
                    except ImportError:
                        # requests really isn't available, keep the original conflict
                        return conflict

            # For all other cases, return the original conflict
            return conflict

        # Apply the monkey patch
        opentelemetry.instrumentation.dependencies.get_dependency_conflicts = rovodev_dependency_conflicts

    except Exception:
        # If monkey patching fails, continue silently
        pass
