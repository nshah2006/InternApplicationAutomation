"""
Authentication routes for OAuth (Google + GitHub).
"""

from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from typing import Dict, Any
import httpx

from app.db.database import get_db
from app.models.db.user import User, OAuthProvider
from app.services.auth_service import create_access_token, get_current_user
from app.dependencies import get_current_user_optional

router = APIRouter(prefix="/auth", tags=["authentication"])


@router.get("/login/{provider}")
async def login(provider: str, request: Request):
    """
    Initiate OAuth login flow.
    
    Args:
        provider: OAuth provider ('google' or 'github')
        request: FastAPI request object
    
    Returns:
        RedirectResponse to OAuth provider
    """
    if provider not in ['google', 'github']:
        raise HTTPException(status_code=400, detail="Invalid provider")
    
    # Get redirect URL from query params or use default
    redirect_url = request.query_params.get('redirect_url', '/')
    
    # Build OAuth URL based on provider
    if provider == 'google':
        client_id = os.getenv('GOOGLE_CLIENT_ID')
        if not client_id:
            raise HTTPException(status_code=500, detail="Google OAuth not configured")
        
        redirect_uri = f"{os.getenv('BASE_URL', 'http://localhost:8000')}/auth/callback/google"
        scope = "openid email profile"
        oauth_url = (
            f"https://accounts.google.com/o/oauth2/v2/auth?"
            f"client_id={client_id}&"
            f"redirect_uri={redirect_uri}&"
            f"response_type=code&"
            f"scope={scope}&"
            f"access_type=offline&"
            f"prompt=consent"
        )
    else:  # github
        client_id = os.getenv('GITHUB_CLIENT_ID')
        if not client_id:
            raise HTTPException(status_code=500, detail="GitHub OAuth not configured")
        
        redirect_uri = f"{os.getenv('BASE_URL', 'http://localhost:8000')}/auth/callback/github"
        scope = "user:email"
        oauth_url = (
            f"https://github.com/login/oauth/authorize?"
            f"client_id={client_id}&"
            f"redirect_uri={redirect_uri}&"
            f"scope={scope}"
        )
    
    # Store redirect URL in session/cookie (simplified - in production use secure session)
    response = RedirectResponse(url=oauth_url)
    response.set_cookie(key="oauth_redirect", value=redirect_url, httponly=True, samesite="lax")
    return response


@router.get("/callback/{provider}")
async def callback(
    provider: str,
    code: str = None,
    error: str = None,
    db: Session = Depends(get_db)
):
    """
    Handle OAuth callback.
    
    Args:
        provider: OAuth provider ('google' or 'github')
        code: Authorization code from OAuth provider
        error: Error message if OAuth failed
        db: Database session
    
    Returns:
        RedirectResponse to frontend with JWT token
    """
    if error:
        raise HTTPException(status_code=400, detail=f"OAuth error: {error}")
    
    if not code:
        raise HTTPException(status_code=400, detail="Missing authorization code")
    
    try:
        # Exchange code for user info
        if provider == 'google':
            user_info = await _handle_google_callback(code)
        else:  # github
            user_info = await _handle_github_callback(code)
        
        # Get or create user
        user = await _get_or_create_user(
            db=db,
            provider=provider,
            user_info=user_info
        )
        
        # Generate JWT token
        token = create_access_token(data={"sub": str(user.id), "email": user.email})
        
        # Redirect to frontend with token
        frontend_url = os.getenv('FRONTEND_URL', 'http://localhost:3000')
        return RedirectResponse(
            url=f"{frontend_url}/auth/callback?token={token}&provider={provider}"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Authentication failed: {str(e)}")


async def _handle_google_callback(code: str) -> Dict[str, Any]:
    """Handle Google OAuth callback."""
    import os
    
    client_id = os.getenv('GOOGLE_CLIENT_ID')
    client_secret = os.getenv('GOOGLE_CLIENT_SECRET')
    redirect_uri = f"{os.getenv('BASE_URL', 'http://localhost:8000')}/auth/callback/google"
    
    # Exchange code for tokens
    async with httpx.AsyncClient() as client:
        token_response = await client.post(
            "https://oauth2.googleapis.com/token",
            data={
                "client_id": client_id,
                "client_secret": client_secret,
                "code": code,
                "grant_type": "authorization_code",
                "redirect_uri": redirect_uri
            }
        )
        token_response.raise_for_status()
        tokens = token_response.json()
        access_token = tokens["access_token"]
        
        # Get user info
        user_response = await client.get(
            "https://www.googleapis.com/oauth2/v2/userinfo",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        user_response.raise_for_status()
        return user_response.json()


async def _handle_github_callback(code: str) -> Dict[str, Any]:
    """Handle GitHub OAuth callback."""
    import os
    
    client_id = os.getenv('GITHUB_CLIENT_ID')
    client_secret = os.getenv('GITHUB_CLIENT_SECRET')
    redirect_uri = f"{os.getenv('BASE_URL', 'http://localhost:8000')}/auth/callback/github"
    
    # Exchange code for access token
    async with httpx.AsyncClient() as client:
        token_response = await client.post(
            "https://github.com/login/oauth/access_token",
            data={
                "client_id": client_id,
                "client_secret": client_secret,
                "code": code,
                "redirect_uri": redirect_uri
            },
            headers={"Accept": "application/json"}
        )
        token_response.raise_for_status()
        tokens = token_response.json()
        access_token = tokens["access_token"]
        
        # Get user info
        user_response = await client.get(
            "https://api.github.com/user",
            headers={"Authorization": f"token {access_token}"}
        )
        user_response.raise_for_status()
        user_data = user_response.json()
        
        # Get user email (GitHub requires separate API call)
        email_response = await client.get(
            "https://api.github.com/user/emails",
            headers={"Authorization": f"token {access_token}"}
        )
        emails = email_response.json() if email_response.status_code == 200 else []
        primary_email = next((e["email"] for e in emails if e.get("primary")), user_data.get("email", ""))
        
        return {
            "id": str(user_data["id"]),
            "email": primary_email,
            "name": user_data.get("name") or user_data.get("login", ""),
            "avatar_url": user_data.get("avatar_url", ""),
            "login": user_data.get("login", "")
        }


async def _get_or_create_user(
    db: Session,
    provider: str,
    user_info: Dict[str, Any]
) -> User:
    """Get or create user from OAuth info."""
    import os
    from datetime import datetime
    
    oauth_provider = OAuthProvider.GOOGLE if provider == 'google' else OAuthProvider.GITHUB
    provider_id = user_info.get("id") or user_info.get("sub", "")
    email = user_info.get("email", "")
    name = user_info.get("name") or user_info.get("full_name", "") or user_info.get("login", "")
    
    # Find existing user
    user = db.query(User).filter(
        User.oauth_provider == oauth_provider,
        User.oauth_provider_id == provider_id
    ).first()
    
    if user:
        # Update last login
        user.last_login = datetime.utcnow()
        db.commit()
        db.refresh(user)
        return user
    
    # Create new user
    user = User(
        email=email,
        full_name=name,
        oauth_provider=oauth_provider,
        oauth_provider_id=provider_id,
        oauth_email=email,
        avatar_url=user_info.get("avatar_url", ""),
        username=user_info.get("login") if provider == 'github' else None,
        is_active=True,
        is_verified=True  # OAuth providers verify emails
    )
    
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.get("/me")
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    """
    Get current user information.
    
    Returns:
        User information
    """
    return {
        "id": current_user.id,
        "email": current_user.email,
        "username": current_user.username,
        "full_name": current_user.full_name,
        "avatar_url": current_user.avatar_url,
        "oauth_provider": current_user.oauth_provider.value,
        "is_active": current_user.is_active
    }


@router.post("/logout")
async def logout():
    """
    Logout endpoint (client-side token removal).
    
    Returns:
        Success message
    """
    return {"message": "Logged out successfully"}

