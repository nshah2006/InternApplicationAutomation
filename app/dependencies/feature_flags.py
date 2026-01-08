"""
Dependencies for feature flag checks.
"""

from fastapi import HTTPException, status, Depends
from sqlalchemy.orm import Session
from typing import Optional

from app.db.database import get_db
from app.models.db.user import User
from app.services.feature_flag_service import FeatureFlagService
from app.dependencies import get_current_user


def check_feature_flag(
    feature_name: str,
    user: Optional[User] = None
):
    """
    Dependency factory to check if a feature is enabled.
    
    Args:
        feature_name: Name of the feature flag
        user: Optional user (if None, will try to get from request)
        
    Returns:
        Dependency function
    """
    async def _check_feature(
        current_user: Optional[User] = Depends(get_current_user),
        db: Session = Depends(get_db)
    ):
        """Check feature flag for current user."""
        service = FeatureFlagService(db)
        
        # Use provided user or current user
        check_user = user or current_user
        
        if not service.is_feature_enabled(feature_name, check_user):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Feature '{feature_name}' is not enabled"
            )
        
        return True
    
    return _check_feature


def require_autofill_feature():
    """Dependency to require autofill feature to be enabled."""
    return check_feature_flag(FeatureFlagService.AUTOFILL)


def require_ai_feature():
    """Dependency to require AI generation feature to be enabled."""
    return check_feature_flag(FeatureFlagService.AI_GENERATION)


def require_role(role_name: str):
    """
    Dependency factory to require a specific role.
    
    Args:
        role_name: Name of the required role
        
    Returns:
        Dependency function
    """
    async def _require_role(
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
    ):
        """Check if user has required role."""
        from app.services.feature_flag_service import FeatureFlagService
        
        service = FeatureFlagService(db)
        user_roles = service._get_user_roles(current_user)
        
        if role_name not in user_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{role_name}' required"
            )
        
        return current_user
    
    return _require_role


def require_admin():
    """Dependency to require admin role."""
    return require_role("admin")


def require_moderator_or_admin():
    """
    Dependency to require moderator or admin role.
    
    Returns:
        Dependency function
    """
    async def _require_moderator_or_admin(
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
    ):
        """Check if user has moderator or admin role."""
        from app.services.feature_flag_service import FeatureFlagService
        
        service = FeatureFlagService(db)
        user_roles = service._get_user_roles(current_user)
        
        if "admin" not in user_roles and "moderator" not in user_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Moderator or admin role required"
            )
        
        return current_user
    
    return _require_moderator_or_admin

