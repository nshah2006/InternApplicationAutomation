"""
Feature flag service for checking feature availability.
"""

from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
from app.models.db.feature_flag import FeatureFlag, FeatureFlagStatus
from app.models.db.role import Role, UserRoleAssignment
from app.models.db.user import User
import json


class FeatureFlagService:
    """
    Service for managing and checking feature flags.
    """
    
    # Feature flag names
    AUTOFILL = "autofill"
    AI_GENERATION = "ai_generation"
    
    def __init__(self, db: Session):
        """
        Initialize feature flag service.
        
        Args:
            db: Database session
        """
        self.db = db
    
    def is_feature_enabled(
        self,
        feature_name: str,
        user: Optional[User] = None
    ) -> bool:
        """
        Check if a feature is enabled for a user.
        
        Args:
            feature_name: Name of the feature flag
            user: Optional user to check role-based permissions
            
        Returns:
            True if feature is enabled, False otherwise
        """
        # Get feature flag
        feature_flag = self.db.query(FeatureFlag).filter(
            FeatureFlag.name == feature_name,
            FeatureFlag.is_active == True
        ).first()
        
        if not feature_flag:
            # Feature flag doesn't exist, default to disabled
            return False
        
        # Check role-based overrides first
        if user:
            user_roles = self._get_user_roles(user)
            for role_name in user_roles:
                if role_name in feature_flag.role_overrides:
                    override_status = feature_flag.role_overrides[role_name]
                    if override_status == FeatureFlagStatus.ENABLED.value:
                        return True
                    elif override_status == FeatureFlagStatus.DISABLED.value:
                        return False
        
        # Check global status
        if feature_flag.status == FeatureFlagStatus.DISABLED.value:
            return False
        elif feature_flag.status == FeatureFlagStatus.ENABLED.value:
            return True
        elif feature_flag.status == FeatureFlagStatus.ROLLOUT.value:
            # Check rollout percentage
            if user:
                # Use user ID for consistent rollout assignment
                user_hash = hash(f"{feature_name}:{user.id}") % 100
                return user_hash < feature_flag.rollout_percentage
            else:
                # No user, default to disabled for rollout
                return False
        
        return False
    
    def get_feature_config(self, feature_name: str) -> Dict[str, Any]:
        """
        Get feature configuration.
        
        Args:
            feature_name: Name of the feature flag
            
        Returns:
            Feature configuration dictionary
        """
        feature_flag = self.db.query(FeatureFlag).filter(
            FeatureFlag.name == feature_name,
            FeatureFlag.is_active == True
        ).first()
        
        if not feature_flag:
            return {}
        
        return feature_flag.config or {}
    
    def _get_user_roles(self, user: User) -> List[str]:
        """
        Get list of role names for a user.
        
        Args:
            user: User object
            
        Returns:
            List of role names
        """
        # Get active role assignments
        assignments = self.db.query(UserRoleAssignment).filter(
            UserRoleAssignment.user_id == user.id,
            UserRoleAssignment.is_active == True
        ).all()
        
        roles = []
        for assignment in assignments:
            role = self.db.query(Role).filter(Role.id == assignment.role_id).first()
            if role and role.is_active:
                roles.append(role.name)
        
        # If no roles assigned, default to "user"
        if not roles:
            roles = ["user"]
        
        return roles
    
    def create_or_update_feature_flag(
        self,
        name: str,
        display_name: str,
        status: str,
        description: Optional[str] = None,
        rollout_percentage: int = 0,
        role_overrides: Optional[Dict[str, str]] = None,
        config: Optional[Dict[str, Any]] = None,
        updated_by: Optional[int] = None
    ) -> FeatureFlag:
        """
        Create or update a feature flag.
        
        Args:
            name: Feature flag name
            display_name: Display name
            status: Status (enabled, disabled, rollout)
            description: Optional description
            rollout_percentage: Rollout percentage (0-100)
            role_overrides: Role-based overrides
            config: Additional configuration
            updated_by: User ID who made the change
            
        Returns:
            Feature flag object
        """
        feature_flag = self.db.query(FeatureFlag).filter(
            FeatureFlag.name == name
        ).first()
        
        if feature_flag:
            # Update existing
            old_status = feature_flag.status
            old_rollout = feature_flag.rollout_percentage
            old_overrides = feature_flag.role_overrides.copy() if feature_flag.role_overrides else {}
            
            feature_flag.display_name = display_name
            feature_flag.status = status
            feature_flag.description = description
            feature_flag.rollout_percentage = rollout_percentage
            feature_flag.role_overrides = role_overrides or {}
            feature_flag.config = config or {}
            feature_flag.updated_by = updated_by
            
            # Create history entry
            from app.models.db.feature_flag import FeatureFlagHistory
            history = FeatureFlagHistory(
                feature_flag_id=feature_flag.id,
                changed_by=updated_by,
                old_status=old_status,
                new_status=status,
                old_rollout_percentage=old_rollout,
                new_rollout_percentage=rollout_percentage,
                old_role_overrides=old_overrides,
                new_role_overrides=role_overrides or {}
            )
            self.db.add(history)
        else:
            # Create new
            feature_flag = FeatureFlag(
                name=name,
                display_name=display_name,
                status=status,
                description=description,
                rollout_percentage=rollout_percentage,
                role_overrides=role_overrides or {},
                config=config or {},
                created_by=updated_by,
                updated_by=updated_by
            )
            self.db.add(feature_flag)
        
        self.db.commit()
        self.db.refresh(feature_flag)
        
        return feature_flag
    
    def get_all_feature_flags(self) -> List[FeatureFlag]:
        """
        Get all feature flags.
        
        Returns:
            List of feature flags
        """
        return self.db.query(FeatureFlag).filter(
            FeatureFlag.is_active == True
        ).all()

