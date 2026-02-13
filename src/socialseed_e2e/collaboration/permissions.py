"""
Access control and permissions management for test collaboration.
"""
import logging
from enum import Enum
from typing import Dict, Set, Optional, List
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class Permission(str, Enum):
    """Permission types for test access."""
    READ = "read"
    WRITE = "write"
    DELETE = "delete"
    REVIEW = "review"
    ADMIN = "admin"


class Role(str, Enum):
    """Predefined roles with permission sets."""
    VIEWER = "viewer"
    CONTRIBUTOR = "contributor"
    MAINTAINER = "maintainer"
    OWNER = "owner"


# Role to permissions mapping
ROLE_PERMISSIONS: Dict[Role, Set[Permission]] = {
    Role.VIEWER: {Permission.READ},
    Role.CONTRIBUTOR: {Permission.READ, Permission.WRITE, Permission.REVIEW},
    Role.MAINTAINER: {Permission.READ, Permission.WRITE, Permission.DELETE, Permission.REVIEW},
    Role.OWNER: {Permission.READ, Permission.WRITE, Permission.DELETE, Permission.REVIEW, Permission.ADMIN},
}


class AccessControl(BaseModel):
    """Access control entry for a resource."""
    user_id: str
    permissions: Set[Permission] = set()
    role: Optional[Role] = None
    
    class Config:
        use_enum_values = True


class PermissionManager:
    """
    Manages permissions and access control for tests.
    """
    
    def __init__(self):
        # resource_id -> user_id -> AccessControl
        self._acl: Dict[str, Dict[str, AccessControl]] = {}
        # resource_id -> owner_id
        self._owners: Dict[str, str] = {}
    
    def set_owner(self, resource_id: str, user_id: str):
        """Set the owner of a resource."""
        self._owners[resource_id] = user_id
        self.grant_role(resource_id, user_id, Role.OWNER)
    
    def get_owner(self, resource_id: str) -> Optional[str]:
        """Get the owner of a resource."""
        return self._owners.get(resource_id)
    
    def grant_permission(self, resource_id: str, user_id: str, permission: Permission):
        """Grant a specific permission to a user for a resource."""
        if resource_id not in self._acl:
            self._acl[resource_id] = {}
        
        if user_id not in self._acl[resource_id]:
            self._acl[resource_id][user_id] = AccessControl(user_id=user_id)
        
        self._acl[resource_id][user_id].permissions.add(permission)
        logger.info(f"Granted {permission} to {user_id} on {resource_id}")
    
    def revoke_permission(self, resource_id: str, user_id: str, permission: Permission):
        """Revoke a specific permission from a user."""
        if resource_id in self._acl and user_id in self._acl[resource_id]:
            self._acl[resource_id][user_id].permissions.discard(permission)
            logger.info(f"Revoked {permission} from {user_id} on {resource_id}")
    
    def grant_role(self, resource_id: str, user_id: str, role: Role):
        """Grant a role (with its associated permissions) to a user."""
        if resource_id not in self._acl:
            self._acl[resource_id] = {}
        
        permissions = ROLE_PERMISSIONS.get(role, set())
        self._acl[resource_id][user_id] = AccessControl(
            user_id=user_id,
            permissions=permissions.copy(),
            role=role
        )
        logger.info(f"Granted role {role} to {user_id} on {resource_id}")
    
    def has_permission(self, resource_id: str, user_id: str, permission: Permission) -> bool:
        """Check if a user has a specific permission on a resource."""
        # Owner always has all permissions
        if self._owners.get(resource_id) == user_id:
            return True
        
        if resource_id not in self._acl or user_id not in self._acl[resource_id]:
            return False
        
        return permission in self._acl[resource_id][user_id].permissions
    
    def get_user_permissions(self, resource_id: str, user_id: str) -> Set[Permission]:
        """Get all permissions a user has on a resource."""
        if self._owners.get(resource_id) == user_id:
            return set(Permission)
        
        if resource_id not in self._acl or user_id not in self._acl[resource_id]:
            return set()
        
        return self._acl[resource_id][user_id].permissions.copy()
    
    def list_users(self, resource_id: str) -> List[Dict[str, any]]:
        """List all users with access to a resource."""
        if resource_id not in self._acl:
            return []
        
        users = []
        for user_id, acl in self._acl[resource_id].items():
            users.append({
                "user_id": user_id,
                "role": acl.role,
                "permissions": list(acl.permissions),
                "is_owner": self._owners.get(resource_id) == user_id
            })
        
        return users
    
    def remove_user(self, resource_id: str, user_id: str) -> bool:
        """Remove all access for a user from a resource."""
        if resource_id in self._acl and user_id in self._acl[resource_id]:
            # Prevent removing owner
            if self._owners.get(resource_id) == user_id:
                logger.warning(f"Cannot remove owner {user_id} from {resource_id}")
                return False
            
            del self._acl[resource_id][user_id]
            logger.info(f"Removed user {user_id} from {resource_id}")
            return True
        
        return False
