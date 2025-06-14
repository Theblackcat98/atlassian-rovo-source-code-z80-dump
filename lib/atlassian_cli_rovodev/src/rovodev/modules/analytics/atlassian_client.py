"""Real implementation of Atlassian Analytics client."""

import os
import platform
from typing import Any, Dict, Optional

from analytics_client.client import Client
from analytics_client.models import Env, Platform, Tenant, TrackEvent, User
from loguru import logger

from .user_info import get_user_and_tenant_info


class AtlassianAnalyticsClient:
    """
    Real implementation of Atlassian Analytics client that sends events to Atlassian Analytics.
    """

    def __init__(
        self,
        environment: str = "dev",
        product: str = "rovodev",
        subproduct: str = "rovodev",
    ):
        """
        Initialize the Atlassian Analytics client.

        Args:
            environment: The environment (local, dev, staging, prod)
            product: The product name
            subproduct: The subproduct name
        """
        # Get user and tenant info (now uses service-first approach)
        user_info = get_user_and_tenant_info(as_dict=False)
        self.user_id = user_info.account_id
        self.tenant_id = user_info.cloud_id
        self.is_internal = user_info.is_internal
        self.org_id = user_info.org_id
        self.auth_type = user_info.auth_type
        # Always use ATLASSIAN_ACCOUNT for user type since that's what the analytics client expects
        self.user_type = User.ATLASSIAN_ACCOUNT

        logger.debug(
            f"Analytics client initialized with user info: "
            f"user_id={self.user_id}, tenant_id={self.tenant_id}, "
            f"org_id={self.org_id}, auth_type={self.auth_type}, "
            f"is_internal={self.is_internal}"
        )

        # Set product info
        self.product = product
        self.subproduct = subproduct

        # Detect platform using Atlassian Analytics Platform enum
        self.platform = self._detect_platform()

        # Map string environment to Env enum
        env_map = {
            "local": Env.LOCAL,
            "dev": Env.DEV,
            "staging": Env.STAGING,
            "prod": Env.PROD,
        }
        env = env_map.get(environment.lower(), Env.DEV)

        self.config = {
            "env": env,
            "product": product,
            "subproduct": subproduct,
            "debug": True,  # Enable debug for the spike
        }

        logger.debug(f"Initializing Atlassian Analytics client with config: {self.config}")
        self.client = Client(self.config)
        logger.debug(f"Atlassian Analytics client initialized successfully with platform: {self.platform}")

    def send_event(self, event_data: Dict[str, Any]) -> None:
        """
        Send an event to Atlassian Analytics.

        Args:
            event_data: Dictionary containing mapped event data
        """
        try:
            # Extract event data
            source = event_data.get("source", "")
            action = event_data.get("action", "")
            action_subject = event_data.get("action_subject", "")
            attributes = event_data.get("attributes", {})

            # Enhance attributes with user context
            enhanced_attributes = self._add_user_context(attributes)

            # Create a TrackEvent
            track_event = TrackEvent(
                # Required fields
                source=source,
                action=action,
                action_subject=action_subject,
                # User and tenant identification
                user_id=self.user_id,
                user_type=self.user_type,  # Always ATLASSIAN_ACCOUNT
                tenant_id=self.tenant_id,
                tenant_type=Tenant.CLOUD_ID,
                org_id=self.org_id,  # Organization ID as top-level property
                # Platform information
                platform=self.platform,
                # Enhanced attributes with user context
                attributes=enhanced_attributes,
            )

            # Send the event
            logger.debug(f"Sending event to Atlassian Analytics: {track_event.get_event_name()}")
            success, msg = self.client.track(track_event)

            if success:
                logger.debug(f"Successfully sent event to Atlassian Analytics")
            else:
                logger.error(f"Failed to send event to Atlassian Analytics: {msg}")
        except Exception as e:
            logger.error(f"Error sending event to Atlassian Analytics: {e}")

    def _add_user_context(self, attributes: Dict[str, Any]) -> Dict[str, Any]:
        """Add enhanced user context to event attributes.

        Args:
            attributes: Original event attributes

        Returns:
            Enhanced attributes with user context
        """
        # Create a copy to avoid modifying the original
        enhanced_attributes = attributes.copy()

        # Add enhanced user context if available
        if self.auth_type is not None:
            enhanced_attributes["authType"] = self.auth_type

        # Add other user context that might be useful
        enhanced_attributes["isInternal"] = self.is_internal

        return enhanced_attributes

    def _detect_platform(self) -> str:
        """
        Detect the current platform using Atlassian Analytics Platform enum.

        Returns:
            str: Platform identifier from analytics_client.models.Platform enum
        """
        # Platform mapping for Atlassian Analytics client
        platform_mapping = {
            "darwin": Platform.MAC,
            "linux": Platform.LINUX,
            "windows": Platform.WINDOWS,
        }

        system = platform.system().lower()
        detected_platform = platform_mapping.get(system, Platform.UNKNOWN)

        logger.debug(f"Detected platform: {system} -> {detected_platform}")
        return detected_platform
