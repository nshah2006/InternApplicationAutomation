"""
Authentication service for OAuth and JWT handling.
"""

import os
import jwt
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from app.models.db.user import User, OAuthProvider

# JWT configuration
SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'your-secret-key-change-in-production')
ALGORITHM = 'HS256'
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 days


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token.
    
    Args:
        data: Data to encode in token (typically {'sub': user_id})
        expires_delta: Optional custom expiration time
        
    Returns:
        Encoded JWT token string
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({'exp': expire, 'iat': datetime.utcnow()})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Verify and decode a JWT token.
    
    Args:
        token: JWT token string
        
    Returns:
        Decoded token payload or None if invalid
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.JWTError:
        return None


def get_or_create_user_from_oauth(
    db: Session,
    provider: OAuthProvider,
    provider_id: str,
    email: str,
    full_name: Optional[str] = None,
    avatar_url: Optional[str] = None,
    username: Optional[str] = None
) -> User:
    """
    Get or create a user from OAuth provider data.
    
    Args:
        db: Database session
        provider: OAuth provider (google or github)
        provider_id: Provider's user ID
        email: User's email address
        full_name: User's full name
        avatar_url: User's avatar URL
        username: User's username
        
    Returns:
        User object
    """
    # Try to find existing user by provider + provider_id
    user = db.query(User).filter(
        User.oauth_provider == provider,
        User.oauth_provider_id == provider_id
    ).first()
    
    if user:
        # Update last login and any changed info
        user.last_login = datetime.utcnow()
        if email and user.email != email:
            user.email = email
        if full_name:
            user.full_name = full_name
        if avatar_url:
            user.avatar_url = avatar_url
        if username:
            user.username = username
        db.commit()
        return user
    
    # Try to find by email (in case user switches providers)
    user = db.query(User).filter(User.email == email).first()
    if user:
        # Update provider info
        user.oauth_provider = provider
        user.oauth_provider_id = provider_id
        user.oauth_email = email
        if full_name:
            user.full_name = full_name
        if avatar_url:
            user.avatar_url = avatar_url
        if username:
            user.username = username
        user.last_login = datetime.utcnow()
        db.commit()
        return user
    
    # Create new user
    user = User(
        email=email,
        oauth_provider=provider,
        oauth_provider_id=provider_id,
        oauth_email=email,
        full_name=full_name or email.split('@')[0],
        avatar_url=avatar_url,
        username=username or email.split('@')[0],
        is_active=True,
        is_verified=True,  # OAuth users are pre-verified
        last_login=datetime.utcnow()
    )
    
    db.add(user)
    db.commit()
    db.refresh(user)
    
    return user


def get_user_by_id(db: Session, user_id: int) -> Optional[User]:
    """
    Get user by ID.
    
    Args:
        db: Database session
        user_id: User ID
        
    Returns:
        User object or None
    """
    return db.query(User).filter(User.id == user_id).first()

