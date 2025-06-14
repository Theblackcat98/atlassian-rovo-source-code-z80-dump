"""Analytics data models."""

from dataclasses import dataclass
from typing import Literal

UserType = Literal["atlassianAccount"]


@dataclass
class UserInfo:
    """User and tenant information for analytics."""

    account_id: str
    cloud_id: str
    is_internal: bool
    user_type: UserType
    org_id: str | None = None  # Organization ID from /credits/check
    auth_type: str | None = None  # Authentication type from /credits/check

    def to_dict(self) -> dict[str, str | bool | UserType]:
        """Convert to dictionary format for backward compatibility."""
        result = {
            "accountId": self.account_id,
            "cloudId": self.cloud_id,
            "isInternal": self.is_internal,
            "userType": self.user_type,
        }

        # Add optional fields if they exist
        if self.org_id is not None:
            result["orgId"] = self.org_id
        if self.auth_type is not None:
            result["authType"] = self.auth_type

        return result
