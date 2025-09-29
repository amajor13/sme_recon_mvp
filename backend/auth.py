"""
Auth0 JWT authentication for FastAPI backend
"""
import os
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
import requests

# Auth0 configuration
AUTH0_DOMAIN = os.getenv("AUTH0_DOMAIN", "your-auth0-domain.auth0.com")
AUTH0_AUDIENCE = os.getenv("AUTH0_AUDIENCE", "your-auth0-audience")
AUTH0_ALGORITHM = "RS256"

# HTTP Bearer token scheme
security = HTTPBearer()

class Auth0JWTBearer:
    """Auth0 JWT Bearer token validator"""
    
    def __init__(self):
        self.jwks_url = f"https://{AUTH0_DOMAIN}/.well-known/jwks.json"
        self.jwks_cache = None
    
    def get_jwks(self):
        """Get JSON Web Key Set from Auth0"""
        if not self.jwks_cache:
            try:
                response = requests.get(self.jwks_url)
                response.raise_for_status()
                self.jwks_cache = response.json()
            except requests.RequestException as e:
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail=f"Unable to fetch JWKS: {str(e)}"
                )
        return self.jwks_cache
    
    def get_signing_key(self, kid: str):
        """Get the signing key for a given key ID"""
        jwks = self.get_jwks()
        
        for key in jwks.get("keys", []):
            if key.get("kid") == kid:
                return key
        
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unable to find appropriate signing key"
        )
    
    def verify_token(self, token: str) -> dict:
        """Verify and decode the JWT token"""
        try:
            # Decode header to get key ID
            unverified_header = jwt.get_unverified_header(token)
            kid = unverified_header.get("kid")
            
            if not kid:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token header missing key ID"
                )
            
            # Get the signing key
            signing_key = self.get_signing_key(kid)
            
            # Construct the public key
            from jose.utils import base64url_decode
            import json
            
            key_data = {
                "kty": signing_key["kty"],
                "use": signing_key.get("use"),
                "n": signing_key["n"],
                "e": signing_key["e"]
            }
            
            # Verify and decode the token
            payload = jwt.decode(
                token,
                key_data,
                algorithms=[AUTH0_ALGORITHM],
                audience=AUTH0_AUDIENCE,
                issuer=f"https://{AUTH0_DOMAIN}/"
            )
            
            return payload
            
        except JWTError as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid token: {str(e)}"
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Token validation failed: {str(e)}"
            )

# Create Auth0 validator instance
auth0_validator = Auth0JWTBearer()

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    """
    Dependency to get the current authenticated user from JWT token
    """
    token = credentials.credentials
    
    # Verify the token and get user info
    user_info = auth0_validator.verify_token(token)
    
    return {
        "user_id": user_info.get("sub"),
        "email": user_info.get("email"),
        "name": user_info.get("name"),
        "email_verified": user_info.get("email_verified", False),
        "permissions": user_info.get("permissions", []),
        "scope": user_info.get("scope", "").split()
    }

async def get_optional_user(credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False))) -> Optional[dict]:
    """
    Optional dependency to get user info if token is provided
    """
    if not credentials:
        return None
    
    try:
        return await get_current_user(credentials)
    except HTTPException:
        return None