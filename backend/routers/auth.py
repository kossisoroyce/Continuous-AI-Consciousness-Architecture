"""
Authentication & Authorization API Router
Endpoints for RBAC, user management, and authentication
"""
from fastapi import APIRouter, HTTPException, Header, Depends
from pydantic import BaseModel
from typing import Optional, List, Set
from datetime import datetime

router = APIRouter()

# Import auth systems
from auth.rbac import rbac_manager, Permission, PREDEFINED_ROLES

# ============== Authentication ==============

class LoginRequest(BaseModel):
    username: str
    password: str

class CreateUserRequest(BaseModel):
    username: str
    display_name: str
    password: str
    roles: List[str] = ["role_operator"]
    clearance_level: str = "UNCLASSIFIED"

class AssignRoleRequest(BaseModel):
    user_id: str
    role_id: str

@router.post("/auth/login")
async def login(request: LoginRequest):
    """Authenticate user and get session token"""
    user = rbac_manager.authenticate(request.username, request.password)
    
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # Generate API key for session
    api_key = rbac_manager.generate_api_key(user.id)
    
    permissions = rbac_manager.get_user_permissions(user.id)
    
    return {
        "user_id": user.id,
        "username": user.username,
        "display_name": user.display_name,
        "roles": list(user.roles),
        "clearance_level": user.clearance_level,
        "permissions": [p.value for p in permissions],
        "api_key": api_key,
        "message": "Login successful"
    }

@router.post("/auth/logout")
async def logout(authorization: Optional[str] = Header(None)):
    """Logout and invalidate session"""
    # In a full implementation, we'd invalidate the API key
    return {"message": "Logout successful"}

@router.get("/auth/verify")
async def verify_token(authorization: Optional[str] = Header(None)):
    """Verify API key and get user info"""
    if not authorization:
        raise HTTPException(status_code=401, detail="No authorization header")
    
    # Extract token
    token = authorization.replace("Bearer ", "").replace("Token ", "")
    
    user = rbac_manager.authenticate_api_key(token)
    
    if not user:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    
    permissions = rbac_manager.get_user_permissions(user.id)
    
    return {
        "valid": True,
        "user_id": user.id,
        "username": user.username,
        "roles": list(user.roles),
        "permissions": [p.value for p in permissions]
    }

# ============== User Management ==============

@router.post("/auth/users")
async def create_user(request: CreateUserRequest):
    """Create a new user"""
    # Check if username exists
    for user in rbac_manager.users.values():
        if user.username == request.username:
            raise HTTPException(status_code=400, detail="Username already exists")
    
    user = rbac_manager.create_user(
        username=request.username,
        display_name=request.display_name,
        password=request.password,
        roles=set(request.roles),
        clearance_level=request.clearance_level
    )
    
    return {
        "user_id": user.id,
        "username": user.username,
        "display_name": user.display_name,
        "roles": list(user.roles),
        "clearance_level": user.clearance_level
    }

@router.get("/auth/users")
async def list_users():
    """List all users"""
    users = []
    for user in rbac_manager.users.values():
        users.append({
            "user_id": user.id,
            "username": user.username,
            "display_name": user.display_name,
            "roles": list(user.roles),
            "clearance_level": user.clearance_level,
            "is_active": user.is_active,
            "last_login": user.last_login.isoformat() if user.last_login else None
        })
    return {"users": users}

@router.get("/auth/users/{user_id}")
async def get_user(user_id: str):
    """Get user details"""
    if user_id not in rbac_manager.users:
        raise HTTPException(status_code=404, detail="User not found")
    
    user = rbac_manager.users[user_id]
    permissions = rbac_manager.get_user_permissions(user_id)
    
    return {
        "user_id": user.id,
        "username": user.username,
        "display_name": user.display_name,
        "email": user.email,
        "roles": list(user.roles),
        "clearance_level": user.clearance_level,
        "is_active": user.is_active,
        "mfa_enabled": user.mfa_enabled,
        "created_at": user.created_at.isoformat(),
        "last_login": user.last_login.isoformat() if user.last_login else None,
        "permissions": [p.value for p in permissions]
    }

@router.get("/auth/users/{user_id}/permissions")
async def get_user_permissions(user_id: str):
    """Get all permissions for a user"""
    if user_id not in rbac_manager.users:
        raise HTTPException(status_code=404, detail="User not found")
    
    permissions = rbac_manager.get_user_permissions(user_id)
    
    return {
        "user_id": user_id,
        "permissions": [p.value for p in permissions]
    }

# ============== Role Management ==============

@router.get("/auth/roles")
async def list_roles():
    """List all available roles"""
    roles = []
    for role in rbac_manager.roles.values():
        roles.append({
            "role_id": role.id,
            "name": role.name,
            "description": role.description,
            "permissions_count": len(role.permissions),
            "parent_role": role.parent_role
        })
    return {"roles": roles}

@router.get("/auth/roles/{role_id}")
async def get_role(role_id: str):
    """Get role details"""
    if role_id not in rbac_manager.roles:
        raise HTTPException(status_code=404, detail="Role not found")
    
    role = rbac_manager.roles[role_id]
    
    return {
        "role_id": role.id,
        "name": role.name,
        "description": role.description,
        "permissions": [p.value if hasattr(p, 'value') else p for p in role.permissions],
        "parent_role": role.parent_role,
        "created_at": role.created_at.isoformat()
    }

@router.post("/auth/roles/assign")
async def assign_role(request: AssignRoleRequest):
    """Assign a role to a user"""
    success = rbac_manager.assign_role(request.user_id, request.role_id)
    
    if not success:
        raise HTTPException(status_code=400, detail="Failed to assign role")
    
    return {
        "message": "Role assigned successfully",
        "user_id": request.user_id,
        "role_id": request.role_id
    }

@router.post("/auth/roles/revoke")
async def revoke_role(request: AssignRoleRequest):
    """Revoke a role from a user"""
    success = rbac_manager.revoke_role(request.user_id, request.role_id)
    
    if not success:
        raise HTTPException(status_code=400, detail="Failed to revoke role")
    
    return {
        "message": "Role revoked successfully",
        "user_id": request.user_id,
        "role_id": request.role_id
    }

# ============== Permission Checks ==============

class CheckPermissionRequest(BaseModel):
    user_id: str
    permission: str

class CheckClearanceRequest(BaseModel):
    user_id: str
    required_level: str

@router.post("/auth/check-permission")
async def check_permission(request: CheckPermissionRequest):
    """Check if user has a specific permission"""
    try:
        permission = Permission(request.permission)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid permission: {request.permission}")
    
    has_permission = rbac_manager.check_permission(request.user_id, permission)
    
    return {
        "user_id": request.user_id,
        "permission": request.permission,
        "granted": has_permission
    }

@router.post("/auth/check-clearance")
async def check_clearance(request: CheckClearanceRequest):
    """Check if user has required clearance level"""
    has_clearance = rbac_manager.check_clearance(
        request.user_id, 
        request.required_level
    )
    
    return {
        "user_id": request.user_id,
        "required_level": request.required_level,
        "granted": has_clearance
    }

@router.get("/auth/permissions")
async def list_permissions():
    """List all available permissions"""
    return {
        "permissions": [
            {"value": p.value, "name": p.name}
            for p in Permission
        ]
    }

@router.get("/auth/clearance-levels")
async def list_clearance_levels():
    """List all clearance levels in order"""
    return {
        "levels": [
            {"value": "UNCLASSIFIED", "order": 0},
            {"value": "CUI", "order": 1, "description": "Controlled Unclassified Information"},
            {"value": "SECRET", "order": 2},
            {"value": "TOP_SECRET", "order": 3}
        ]
    }
