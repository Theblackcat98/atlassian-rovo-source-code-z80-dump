"""User and tenant identification utilities for analytics."""

import os
from typing import Any, Dict

from loguru import logger

import nemo

from ..usage import get_usage
from .models import UserInfo, UserType


def _determine_internal_status(auth_type: str, user_email: str = None) -> bool:
    """Determine if user is internal based on email domain first, then auth type.

    Rules:
    1. If email is available, email domain determines status:
       - @atlassian.com = internal
       - other domains = external (regardless of auth type)
    2. If no email, fall back to auth type:
       - ASAP, slauth, lanyard = internal
       - others = external
    """
    # Check email domain first (takes precedence)
    email = user_email or nemo.USER_EMAIL
    if email:
        return email.endswith("@atlassian.com")

    # If no email available, fall back to auth type
    if auth_type in ["ASAP", "slauth", "lanyard", "pipelines"]:
        return True

    return False


def _get_simple_fallback_user_info() -> UserInfo:
    """Simple fallback for slauth/lanyard only."""

    # Try USER_AAID first (most reliable)
    aaid = os.environ.get("USER_AAID")
    if aaid:
        logger.debug("Using USER_AAID for fallback")
        return UserInfo(
            account_id=aaid,
            cloud_id=nemo.CLOUD_ID or "unknown",
            org_id=None,
            auth_type=nemo.AUTH_METHOD,
            is_internal=_determine_internal_status(nemo.AUTH_METHOD, nemo.USER_EMAIL),
            user_type="atlassianAccount",
        )

    # Try username from email (no hashing!)
    if nemo.USER_EMAIL:
        username = nemo.USER_EMAIL.split("@")[0]  # "user@atlassian.com" → "user"
        logger.debug(f"Using username from email: {username}")
        return UserInfo(
            account_id=username,
            cloud_id=nemo.CLOUD_ID or "unknown",
            org_id=None,
            auth_type=nemo.AUTH_METHOD,
            is_internal=_determine_internal_status(nemo.AUTH_METHOD, nemo.USER_EMAIL),
            user_type="atlassianAccount",
        )

    # Try system username
    user = os.environ.get("USER") or os.environ.get("USERNAME") or os.environ.get("LOGNAME")
    if user:
        logger.debug(f"Using system username: {user}")
        return UserInfo(
            account_id=user,
            cloud_id=nemo.CLOUD_ID or "unknown",
            org_id=None,
            auth_type=nemo.AUTH_METHOD,
            is_internal=_determine_internal_status(nemo.AUTH_METHOD, nemo.USER_EMAIL),
            user_type="atlassianAccount",
        )

    # Fail fast - no user identification possible
    raise ValueError(
        f"No user identification available for auth method '{nemo.AUTH_METHOD}'. "
        f"Please check your authentication configuration."
    )


def get_user_and_tenant_info(as_dict: bool = True) -> UserInfo | dict[str, str | bool | UserType]:
    """Get user information with simplified logic.

    Strategy:
    - API token: Service call only (no fallback)
    - slauth/lanyard: Try service, then simple fallback
    - Fail fast if no user identification possible
    """

    if nemo.AUTH_METHOD == "api_token":
        # API token MUST use service call - no fallback
        # If this fails, it indicates a real problem that should be fixed
        logger.debug("API token auth - using service call only")
        usage_data = get_usage()  # Let it raise exception if it fails
        result = _extract_user_info_from_service(usage_data)

    else:
        # For slauth/lanyard: try service first, then fallback
        try:
            logger.debug(f"{nemo.AUTH_METHOD} auth - trying service call first")
            usage_data = get_usage()
            result = _extract_user_info_from_service(usage_data)
        except Exception as e:
            logger.debug(f"Service call failed for {nemo.AUTH_METHOD}, using fallback: {e}")
            result = _get_simple_fallback_user_info()

    return result.to_dict() if as_dict else result


def _extract_user_info_from_service(usage_data: Dict[str, Any]) -> UserInfo:
    """Extract user info from service response."""
    user_credit_limits = usage_data.get("userCreditLimits", {})
    user_data = user_credit_limits.get("user", {})

    if not user_data.get("atlassianAccountId"):
        raise ValueError("Service response missing user account ID")

    logger.debug("Using service call for user identification")
    return UserInfo(
        account_id=user_data.get("atlassianAccountId"),
        cloud_id=user_data.get("cloudId") or nemo.CLOUD_ID or "unknown",
        org_id=user_data.get("atlassianOrgId"),
        auth_type=user_data.get("authType"),
        is_internal=_determine_internal_status(user_data.get("authType"), nemo.USER_EMAIL),
        user_type="atlassianAccount",
    )
