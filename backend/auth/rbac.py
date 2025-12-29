"""
Role-Based Access Control (RBAC) System
Implements hierarchical roles and fine-grained permissions
"""
from enum import Enum
from typing import Set, Dict, List, Optional
from pydantic import BaseModel, Field
from datetime import datetime, timezone
import uuid
import hashlib
import secrets

class Permission(str, Enum):
    """Fine-grained permissions for HMT platform"""
    # Brain Management
    BRAIN_CREATE = "brain.create"
    BRAIN_READ = "brain.read"
    BRAIN_UPDATE = "brain.update"
    BRAIN_DELETE = "brain.delete"
    BRAIN_EXPORT = "brain.export"
    
    # Session Management
    SESSION_CREATE = "session.create"
    SESSION_READ = "session.read"
    SESSION_END = "session.end"
    
    # AI Interaction
    AI_INTERACT = "ai.interact"
    AI_OVERRIDE = "ai.override"
    AI_CONFIGURE = "ai.configure"
    
    # Detection/Vision
    DETECTION_VIEW = "detection.view"
    DETECTION_CONFIGURE = "detection.configure"
    DETECTION_EXPORT = "detection.export"
    
    # Trust & Calibration
    TRUST_VIEW = "trust.view"
    TRUST_MODIFY = "trust.modify"
    TRUST_RESET = "trust.reset"
    
    # Audit
    AUDIT_VIEW = "audit.view"
    AUDIT_EXPORT = "audit.export"
    AUDIT_ADMIN = "audit.admin"
    
    # Mission
    MISSION_START = "mission.start"
    MISSION_END = "mission.end"
    MISSION_REVIEW = "mission.review"
    MISSION_REPLAY = "mission.replay"
    
    # Administration
    ADMIN_USERS = "admin.users"
    ADMIN_ROLES = "admin.roles"
    ADMIN_SYSTEM = "admin.system"
    ADMIN_SECURITY = "admin.security"
    
    # Data Classification
    DATA_UNCLASSIFIED = "data.unclassified"
    DATA_CUI = "data.cui"
    DATA_SECRET = "data.secret"
    DATA_TOP_SECRET = "data.top_secret"

class Role(BaseModel):
    """Role definition with permissions"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: str
    permissions: Set[Permission]
    parent_role: Optional[str] = None  # For role hierarchy
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    class Config:
        use_enum_values = True

# Predefined roles
PREDEFINED_ROLES = {
    "operator": Role(
        id="role_operator",
        name="Operator",
        description="Standard operator with basic HMT interaction capabilities",
        permissions={
            Permission.BRAIN_READ,
            Permission.SESSION_CREATE,
            Permission.SESSION_READ,
            Permission.SESSION_END,
            Permission.AI_INTERACT,
            Permission.DETECTION_VIEW,
            Permission.TRUST_VIEW,
            Permission.MISSION_START,
            Permission.MISSION_END,
            Permission.DATA_UNCLASSIFIED,
        }
    ),
    "senior_operator": Role(
        id="role_senior_operator",
        name="Senior Operator",
        description="Experienced operator with override capabilities",
        permissions={
            Permission.BRAIN_READ,
            Permission.BRAIN_UPDATE,
            Permission.SESSION_CREATE,
            Permission.SESSION_READ,
            Permission.SESSION_END,
            Permission.AI_INTERACT,
            Permission.AI_OVERRIDE,
            Permission.DETECTION_VIEW,
            Permission.DETECTION_CONFIGURE,
            Permission.TRUST_VIEW,
            Permission.TRUST_MODIFY,
            Permission.MISSION_START,
            Permission.MISSION_END,
            Permission.MISSION_REVIEW,
            Permission.AUDIT_VIEW,
            Permission.DATA_UNCLASSIFIED,
            Permission.DATA_CUI,
        },
        parent_role="role_operator"
    ),
    "mission_commander": Role(
        id="role_mission_commander",
        name="Mission Commander",
        description="Full mission control and review capabilities",
        permissions={
            Permission.BRAIN_CREATE,
            Permission.BRAIN_READ,
            Permission.BRAIN_UPDATE,
            Permission.BRAIN_EXPORT,
            Permission.SESSION_CREATE,
            Permission.SESSION_READ,
            Permission.SESSION_END,
            Permission.AI_INTERACT,
            Permission.AI_OVERRIDE,
            Permission.AI_CONFIGURE,
            Permission.DETECTION_VIEW,
            Permission.DETECTION_CONFIGURE,
            Permission.DETECTION_EXPORT,
            Permission.TRUST_VIEW,
            Permission.TRUST_MODIFY,
            Permission.TRUST_RESET,
            Permission.MISSION_START,
            Permission.MISSION_END,
            Permission.MISSION_REVIEW,
            Permission.MISSION_REPLAY,
            Permission.AUDIT_VIEW,
            Permission.AUDIT_EXPORT,
            Permission.DATA_UNCLASSIFIED,
            Permission.DATA_CUI,
            Permission.DATA_SECRET,
        },
        parent_role="role_senior_operator"
    ),
    "administrator": Role(
        id="role_administrator",
        name="System Administrator",
        description="Full system administration capabilities",
        permissions=set(Permission),  # All permissions
        parent_role="role_mission_commander"
    ),
    "auditor": Role(
        id="role_auditor",
        name="Auditor",
        description="Read-only access for compliance review",
        permissions={
            Permission.BRAIN_READ,
            Permission.SESSION_READ,
            Permission.DETECTION_VIEW,
            Permission.TRUST_VIEW,
            Permission.AUDIT_VIEW,
            Permission.AUDIT_EXPORT,
            Permission.MISSION_REVIEW,
            Permission.MISSION_REPLAY,
            Permission.DATA_UNCLASSIFIED,
            Permission.DATA_CUI,
        }
    ),
}

class User(BaseModel):
    """User account with role assignments"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    username: str
    display_name: str
    email: Optional[str] = None
    roles: Set[str] = Field(default_factory=set)  # Role IDs
    password_hash: Optional[str] = None
    api_key_hash: Optional[str] = None
    
    # Security
    clearance_level: str = "UNCLASSIFIED"
    mfa_enabled: bool = False
    
    # Metadata
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_login: Optional[datetime] = None
    is_active: bool = True
    
    class Config:
        use_enum_values = True

class RBACManager:
    """
    Role-Based Access Control Manager
    Handles user authentication and authorization
    """
    def __init__(self):
        self.roles: Dict[str, Role] = {**PREDEFINED_ROLES}
        self.users: Dict[str, User] = {}
        self._api_keys: Dict[str, str] = {}  # api_key_hash -> user_id
        
        # Create default admin user
        self._create_default_admin()
    
    def _create_default_admin(self):
        """Create default administrator account"""
        admin = User(
            id="user_admin",
            username="admin",
            display_name="System Administrator",
            roles={"role_administrator"},
            clearance_level="TOP_SECRET"
        )
        # Default password: "admin" (should be changed immediately)
        admin.password_hash = self._hash_password("admin")
        self.users[admin.id] = admin
    
    def _hash_password(self, password: str) -> str:
        """Hash password with salt"""
        salt = secrets.token_hex(16)
        hashed = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
        return f"{salt}:{hashed.hex()}"
    
    def _verify_password(self, password: str, password_hash: str) -> bool:
        """Verify password against hash"""
        try:
            salt, stored_hash = password_hash.split(':')
            computed = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
            return computed.hex() == stored_hash
        except:
            return False
    
    def create_user(
        self,
        username: str,
        display_name: str,
        password: str,
        roles: Set[str] = None,
        clearance_level: str = "UNCLASSIFIED"
    ) -> User:
        """Create a new user"""
        user = User(
            username=username,
            display_name=display_name,
            roles=roles or {"role_operator"},
            clearance_level=clearance_level,
            password_hash=self._hash_password(password)
        )
        self.users[user.id] = user
        return user
    
    def authenticate(self, username: str, password: str) -> Optional[User]:
        """Authenticate user with username/password"""
        for user in self.users.values():
            if user.username == username and user.is_active:
                if self._verify_password(password, user.password_hash):
                    user.last_login = datetime.now(timezone.utc)
                    return user
        return None
    
    def generate_api_key(self, user_id: str) -> Optional[str]:
        """Generate API key for user"""
        if user_id not in self.users:
            return None
        
        api_key = f"hmt_{secrets.token_urlsafe(32)}"
        api_key_hash = hashlib.sha256(api_key.encode()).hexdigest()
        
        self.users[user_id].api_key_hash = api_key_hash
        self._api_keys[api_key_hash] = user_id
        
        return api_key
    
    def authenticate_api_key(self, api_key: str) -> Optional[User]:
        """Authenticate user with API key"""
        api_key_hash = hashlib.sha256(api_key.encode()).hexdigest()
        user_id = self._api_keys.get(api_key_hash)
        
        if user_id and user_id in self.users:
            user = self.users[user_id]
            if user.is_active:
                return user
        return None
    
    def get_user_permissions(self, user_id: str) -> Set[Permission]:
        """Get all permissions for a user (including inherited)"""
        if user_id not in self.users:
            return set()
        
        user = self.users[user_id]
        permissions = set()
        
        for role_id in user.roles:
            if role_id in self.roles:
                permissions.update(self._get_role_permissions(role_id))
        
        return permissions
    
    def _get_role_permissions(self, role_id: str) -> Set[Permission]:
        """Get permissions for a role including inherited"""
        if role_id not in self.roles:
            return set()
        
        role = self.roles[role_id]
        permissions = set(role.permissions)
        
        # Add inherited permissions from parent role
        if role.parent_role and role.parent_role in self.roles:
            permissions.update(self._get_role_permissions(role.parent_role))
        
        return permissions
    
    def check_permission(self, user_id: str, permission: Permission) -> bool:
        """Check if user has a specific permission"""
        permissions = self.get_user_permissions(user_id)
        return permission in permissions
    
    def check_clearance(self, user_id: str, required_level: str) -> bool:
        """Check if user has required clearance level"""
        if user_id not in self.users:
            return False
        
        clearance_order = ["UNCLASSIFIED", "CUI", "SECRET", "TOP_SECRET"]
        user_level = self.users[user_id].clearance_level
        
        try:
            user_idx = clearance_order.index(user_level)
            required_idx = clearance_order.index(required_level)
            return user_idx >= required_idx
        except ValueError:
            return False
    
    def assign_role(self, user_id: str, role_id: str) -> bool:
        """Assign a role to a user"""
        if user_id not in self.users or role_id not in self.roles:
            return False
        
        self.users[user_id].roles.add(role_id)
        return True
    
    def revoke_role(self, user_id: str, role_id: str) -> bool:
        """Revoke a role from a user"""
        if user_id not in self.users:
            return False
        
        self.users[user_id].roles.discard(role_id)
        return True
    
    def create_role(
        self,
        name: str,
        description: str,
        permissions: Set[Permission],
        parent_role: str = None
    ) -> Role:
        """Create a custom role"""
        role = Role(
            name=name,
            description=description,
            permissions=permissions,
            parent_role=parent_role
        )
        self.roles[role.id] = role
        return role

# Global singleton instance
rbac_manager = RBACManager()
