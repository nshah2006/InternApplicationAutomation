"""
Admin endpoints for managing feature flags and roles.
"""

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

from app.db.database import get_db
from app.models.db.user import User
from app.models.db.feature_flag import FeatureFlag, FeatureFlagStatus
from app.models.db.role import Role, UserRoleAssignment
from app.services.feature_flag_service import FeatureFlagService
from app.dependencies.feature_flags import require_admin
from app.core.logging_config import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/admin", tags=["admin"])


class FeatureFlagRequest(BaseModel):
    """Request model for creating/updating feature flag."""
    name: str = Field(..., description="Feature flag name")
    display_name: str = Field(..., description="Display name")
    status: str = Field(..., description="Status: enabled, disabled, or rollout")
    description: Optional[str] = Field(None, description="Description")
    rollout_percentage: int = Field(0, ge=0, le=100, description="Rollout percentage (0-100)")
    role_overrides: Optional[Dict[str, str]] = Field(None, description="Role-based overrides")
    config: Optional[Dict[str, Any]] = Field(None, description="Additional configuration")


class FeatureFlagResponse(BaseModel):
    """Response model for feature flag."""
    id: int
    name: str
    display_name: str
    status: str
    description: Optional[str]
    rollout_percentage: int
    role_overrides: Dict[str, str]
    config: Dict[str, Any]
    created_at: str
    updated_at: Optional[str]


class AssignRoleRequest(BaseModel):
    """Request model for assigning role to user."""
    user_id: int = Field(..., description="User ID")
    role_name: str = Field(..., description="Role name")
    expires_at: Optional[str] = Field(None, description="Expiration date (ISO format)")


@router.post("/feature-flags", response_model=FeatureFlagResponse)
async def create_or_update_feature_flag(
    request: FeatureFlagRequest,
    current_user: User = Depends(require_admin()),
    db: Session = Depends(get_db)
):
    """
    Create or update a feature flag.
    
    Args:
        request: FeatureFlagRequest with feature flag details
        current_user: Current admin user
        db: Database session
        
    Returns:
        FeatureFlagResponse with feature flag details
    """
    # Validate status
    if request.status not in [s.value for s in FeatureFlagStatus]:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid status. Must be one of: {[s.value for s in FeatureFlagStatus]}"
        )
    
    service = FeatureFlagService(db)
    
    try:
        feature_flag = service.create_or_update_feature_flag(
            name=request.name,
            display_name=request.display_name,
            status=request.status,
            description=request.description,
            rollout_percentage=request.rollout_percentage,
            role_overrides=request.role_overrides,
            config=request.config,
            updated_by=current_user.id
        )
        
        logger.info(
            "Feature flag updated",
            extra={
                'event_type': 'feature_flag_updated',
                'feature_flag': feature_flag.name,
                'status': feature_flag.status,
                'updated_by': current_user.id
            }
        )
        
        return FeatureFlagResponse(
            id=feature_flag.id,
            name=feature_flag.name,
            display_name=feature_flag.display_name,
            status=feature_flag.status,
            description=feature_flag.description,
            rollout_percentage=feature_flag.rollout_percentage,
            role_overrides=feature_flag.role_overrides or {},
            config=feature_flag.config or {},
            created_at=feature_flag.created_at.isoformat() if feature_flag.created_at else "",
            updated_at=feature_flag.updated_at.isoformat() if feature_flag.updated_at else None
        )
    except Exception as e:
        logger.error(
            "Failed to update feature flag",
            extra={
                'event_type': 'feature_flag_update_failed',
                'feature_flag': request.name,
                'error': str(e)
            },
            exc_info=True
        )
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update feature flag: {str(e)}"
        )


@router.get("/feature-flags", response_model=List[FeatureFlagResponse])
async def get_all_feature_flags(
    current_user: User = Depends(require_admin()),
    db: Session = Depends(get_db)
):
    """
    Get all feature flags.
    
    Args:
        current_user: Current admin user
        db: Database session
        
    Returns:
        List of feature flags
    """
    service = FeatureFlagService(db)
    feature_flags = service.get_all_feature_flags()
    
    return [
        FeatureFlagResponse(
            id=ff.id,
            name=ff.name,
            display_name=ff.display_name,
            status=ff.status,
            description=ff.description,
            rollout_percentage=ff.rollout_percentage,
            role_overrides=ff.role_overrides or {},
            config=ff.config or {},
            created_at=ff.created_at.isoformat() if ff.created_at else "",
            updated_at=ff.updated_at.isoformat() if ff.updated_at else None
        )
        for ff in feature_flags
    ]


@router.get("/feature-flags/{feature_name}", response_model=FeatureFlagResponse)
async def get_feature_flag(
    feature_name: str,
    current_user: User = Depends(require_admin()),
    db: Session = Depends(get_db)
):
    """
    Get a specific feature flag.
    
    Args:
        feature_name: Feature flag name
        current_user: Current admin user
        db: Database session
        
    Returns:
        FeatureFlagResponse with feature flag details
    """
    feature_flag = db.query(FeatureFlag).filter(
        FeatureFlag.name == feature_name,
        FeatureFlag.is_active == True
    ).first()
    
    if not feature_flag:
        raise HTTPException(status_code=404, detail=f"Feature flag '{feature_name}' not found")
    
    return FeatureFlagResponse(
        id=feature_flag.id,
        name=feature_flag.name,
        display_name=feature_flag.display_name,
        status=feature_flag.status,
        description=feature_flag.description,
        rollout_percentage=feature_flag.rollout_percentage,
        role_overrides=feature_flag.role_overrides or {},
        config=feature_flag.config or {},
        created_at=feature_flag.created_at.isoformat() if feature_flag.created_at else "",
        updated_at=feature_flag.updated_at.isoformat() if feature_flag.updated_at else None
    )


@router.post("/roles/assign")
async def assign_role(
    request: AssignRoleRequest,
    current_user: User = Depends(require_admin()),
    db: Session = Depends(get_db)
):
    """
    Assign a role to a user.
    
    Args:
        request: AssignRoleRequest with user_id and role_name
        current_user: Current admin user
        db: Database session
        
    Returns:
        Success message
    """
    # Get user
    user = db.query(User).filter(User.id == request.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail=f"User {request.user_id} not found")
    
    # Get role
    role = db.query(Role).filter(Role.name == request.role_name).first()
    if not role:
        raise HTTPException(status_code=404, detail=f"Role '{request.role_name}' not found")
    
    # Check if assignment already exists
    existing = db.query(UserRoleAssignment).filter(
        UserRoleAssignment.user_id == request.user_id,
        UserRoleAssignment.role_id == role.id,
        UserRoleAssignment.is_active == True
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=400,
            detail=f"User already has role '{request.role_name}'"
        )
    
    # Create assignment
    from datetime import datetime
    expires_at = None
    if request.expires_at:
        try:
            expires_at = datetime.fromisoformat(request.expires_at.replace('Z', '+00:00'))
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid expiration date format")
    
    assignment = UserRoleAssignment(
        user_id=request.user_id,
        role_id=role.id,
        assigned_by=current_user.id,
        expires_at=expires_at
    )
    
    db.add(assignment)
    db.commit()
    
    logger.info(
        "Role assigned",
        extra={
            'event_type': 'role_assigned',
            'user_id': request.user_id,
            'role_name': request.role_name,
            'assigned_by': current_user.id
        }
    )
    
    return {
        "success": True,
        "message": f"Role '{request.role_name}' assigned to user {request.user_id}"
    }


@router.delete("/roles/assign/{user_id}/{role_name}")
async def remove_role(
    user_id: int,
    role_name: str,
    current_user: User = Depends(require_admin()),
    db: Session = Depends(get_db)
):
    """
    Remove a role from a user.
    
    Args:
        user_id: User ID
        role_name: Role name
        current_user: Current admin user
        db: Database session
        
    Returns:
        Success message
    """
    # Get role
    role = db.query(Role).filter(Role.name == role_name).first()
    if not role:
        raise HTTPException(status_code=404, detail=f"Role '{role_name}' not found")
    
    # Get assignment
    assignment = db.query(UserRoleAssignment).filter(
        UserRoleAssignment.user_id == user_id,
        UserRoleAssignment.role_id == role.id,
        UserRoleAssignment.is_active == True
    ).first()
    
    if not assignment:
        raise HTTPException(
            status_code=404,
            detail=f"User {user_id} does not have role '{role_name}'"
        )
    
    # Deactivate assignment
    assignment.is_active = False
    db.commit()
    
    logger.info(
        "Role removed",
        extra={
            'event_type': 'role_removed',
            'user_id': user_id,
            'role_name': role_name,
            'removed_by': current_user.id
        }
    )
    
    return {
        "success": True,
        "message": f"Role '{role_name}' removed from user {user_id}"
    }

