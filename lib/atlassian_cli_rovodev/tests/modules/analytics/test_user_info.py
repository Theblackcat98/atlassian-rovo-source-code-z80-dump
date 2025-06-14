"""Tests for user info module."""

import hashlib
import os
from unittest.mock import patch

import pytest
from loguru import logger

import nemo
from rovodev.modules.analytics.user_info import get_user_and_tenant_info


@pytest.mark.parametrize(
    "auth_method,user_email,cloud_id,env_user,user_aaid,expected",
    [
        # Removed: api_token test cases - now require valid service call or will fail
        # Removed: api_token with external email - now fails fast (no fallback)
        # Removed: api_token with no user data - now raises exception instead of anonymous
        (
            "slauth",
            "user@external.com",  # External email
            None,
            None,
            None,
            {
                "accountId": "user",  # Username part from email (no hashing)
                "cloudId": "a436116f-02ce-4520-8fbb-7301462a1674",
                "isInternal": False,  # External email
                "userType": "atlassianAccount",
                "authType": "slauth",
            },
        ),
        (
            "slauth",
            None,
            "test-cloud-id",
            "test-user",
            None,  # No USER_AAID
            {
                "accountId": "test-user",  # System user ID
                "cloudId": "test-cloud-id",
                "isInternal": True,
                "userType": "atlassianAccount",
                "authType": "slauth",
            },
        ),
        (
            "slauth",
            None,
            None,
            "test-user",
            None,  # No USER_AAID
            {
                "accountId": "test-user",  # System user ID
                "cloudId": "a436116f-02ce-4520-8fbb-7301462a1674",
                "isInternal": True,
                "userType": "atlassianAccount",
                "authType": "slauth",
            },
        ),
        # Removed: slauth with no user data - now raises exception instead of anonymous
        (
            "lanyard",
            None,
            "test-cloud-id",
            "test-user",
            None,  # No USER_AAID
            {
                "accountId": "test-user",  # System user ID
                "cloudId": "test-cloud-id",
                "isInternal": True,
                "userType": "atlassianAccount",
                "authType": "lanyard",
            },
        ),
        # Removed: unknown auth method with no user data - now raises exception instead of anonymous
        # Removed: api_token test cases with USER_AAID - now require valid service call
        # Test case for USER_AAID without email but with slauth (should be internal)
        (
            "slauth",
            None,  # No email
            None,
            None,
            "test-aaid-999",  # USER_AAID value
            {
                "accountId": "test-aaid-999",
                "cloudId": "a436116f-02ce-4520-8fbb-7301462a1674",
                "isInternal": True,  # Internal because of slauth
                "userType": "atlassianAccount",
                "authType": "slauth",
            },
        ),
        # Test case for USER_AAID without email but with lanyard (should be internal)
        (
            "lanyard",
            None,  # No email
            None,
            None,
            "test-aaid-888",  # USER_AAID value
            {
                "accountId": "test-aaid-888",
                "cloudId": "a436116f-02ce-4520-8fbb-7301462a1674",
                "isInternal": True,  # Internal because of lanyard
                "userType": "atlassianAccount",
                "authType": "lanyard",
            },
        ),
    ],
)
def test_get_user_and_tenant_info(auth_method, user_email, cloud_id, env_user, user_aaid, expected):
    """Test get_user_and_tenant_info with different auth methods."""
    logger.info(
        f"Testing with: auth_method={auth_method}, user_email={user_email}, cloud_id={cloud_id}, env_user={env_user}, user_aaid={user_aaid}"
    )
    env_vars = {}
    if env_user:
        env_vars["USER"] = env_user
    if user_aaid:
        env_vars["USER_AAID"] = user_aaid
    with patch.dict(os.environ, env_vars, clear=True):
        # Set up mock nemo attributes
        nemo.AUTH_METHOD = auth_method
        nemo.USER_EMAIL = user_email
        nemo.CLOUD_ID = cloud_id or "a436116f-02ce-4520-8fbb-7301462a1674"
        result = get_user_and_tenant_info()
        logger.info(f"Expected: {expected}")
        logger.info(f"Got: {result}")
        assert result == expected


def test_misconfigured_user_info_raises_exception():
    """Test that misconfigured scenarios raise exceptions instead of returning anonymous users."""
    # Test cases that should raise exceptions (no user identification possible)
    test_cases = [
        # api_token with no email or user data
        {
            "auth_method": "api_token",
            "user_email": None,
            "cloud_id": "test-cloud",
            "user": None,
            "user_aaid": None,
        },
        # api_token with external email (service will likely fail, no fallback)
        {
            "auth_method": "api_token",
            "user_email": "user@external.com",
            "cloud_id": "test-cloud",
            "user": None,
            "user_aaid": None,
        },
        # slauth with no user data
        {
            "auth_method": "slauth",
            "user_email": None,
            "cloud_id": "test-cloud",
            "user": None,
            "user_aaid": None,
        },
        # unknown auth method with no user data
        {
            "auth_method": "unknown",
            "user_email": None,
            "cloud_id": "test-cloud",
            "user": None,
            "user_aaid": None,
        },
    ]

    for case in test_cases:
        with patch.dict(os.environ, {}, clear=True):
            nemo.AUTH_METHOD = case["auth_method"]
            nemo.USER_EMAIL = case["user_email"]
            nemo.CLOUD_ID = case["cloud_id"]

            # Set USER environment variable if specified
            if case["user"]:
                os.environ["USER"] = case["user"]
            if case["user_aaid"]:
                os.environ["USER_AAID"] = case["user_aaid"]

            # Should raise exception for misconfigured scenarios
            # API token auth raises UnauthorizedError, others raise ValueError
            if case["auth_method"] == "api_token":
                with pytest.raises(Exception):  # UnauthorizedError or other service errors
                    get_user_and_tenant_info()
            else:
                with pytest.raises(ValueError, match="No user identification available"):
                    get_user_and_tenant_info()
