from typing import Dict, Any, List, Set

class RoleBasedAccessControl:
    """
    Part 10: Role-Based Access Control (RBAC) System.
    Enforces strict role permissions and project-level isolation.
    """

    ROLES = {
        "ORGANIZATION_ADMIN",
        "PROJECT_MANAGER",
        "GIS_ANALYST",
        "SURVEY_OFFICER",
        "FIELD_VERIFIER",
        "VIEWER"
    }

    ROLE_PERMISSIONS: Dict[str, Set[str]] = {
        "ORGANIZATION_ADMIN": {
            "org:manage", "user:manage", "project:create", "project:delete",
            "project:edit", "scene:upload", "ai:run", "review:decide",
            "report:generate", "export:download", "api_key:manage"
        },
        "PROJECT_MANAGER": {
            "project:edit", "scene:upload", "ai:run", "review:decide",
            "report:generate", "export:download"
        },
        "GIS_ANALYST": {
            "scene:upload", "ai:run", "report:generate", "export:download"
        },
        "SURVEY_OFFICER": {
            "review:decide", "report:generate", "export:download"
        },
        "FIELD_VERIFIER": {
            "field_task:update", "export:download"
        },
        "VIEWER": {
            "project:view", "report:view", "export:download"
        }
    }

    @classmethod
    def can_perform(cls, user_role: str, permission: str) -> bool:
        """Checks if a user role has the required permission."""
        perms = cls.ROLE_PERMISSIONS.get(user_role.upper(), set())
        return permission in perms

    @classmethod
    def enforce_tenant_isolation(
        cls,
        user_org_id: str,
        resource_org_id: str
    ) -> bool:
        """
        Validates that a user can only access resources belonging to their organization.
        Raises PermissionError on cross-tenant violation.
        """
        if user_org_id != resource_org_id:
            raise PermissionError(
                f"Cross-tenant access violation: User Org '{user_org_id}' cannot access Resource Org '{resource_org_id}'."
            )
        return True
