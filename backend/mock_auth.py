"""
Mock authentication for development
"""
from typing import Optional, Dict
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import os

# HTTP Bearer token scheme
security = HTTPBearer(auto_error=False)

async def get_current_user_mock(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)) -> Optional[Dict]:
    """
    Mock authentication that accepts any token for development
    """
    if not credentials:
        # For development, allow unauthenticated access
        return {
            "user_id": "mock-user-123",
            "email": "demo@example.com",
            "name": "Demo User",
            "email_verified": True,
            "permissions": [],
            "scope": ["read:data", "write:data"]
        }
    
    # Accept mock token
    if credentials.credentials == "mock-jwt-token-for-development":
        return {
            "user_id": "mock-user-123",
            "email": "demo@example.com", 
            "name": "Demo User",
            "email_verified": True,
            "permissions": [],
            "scope": ["read:data", "write:data"]
        }
    
    # For development, accept any other token as well
    return {
        "user_id": "dev-user",
        "email": "dev@example.com",
        "name": "Development User", 
        "email_verified": True,
        "permissions": [],
        "scope": ["read:data", "write:data"]
    }