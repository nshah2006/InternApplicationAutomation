"""
Feature flag database models.
"""

from sqlalchemy import Column, String, Integer, DateTime, Boolean, ForeignKey, Text, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.database import Base
import enum


class FeatureFlagStatus(str, enum.Enum):
    """Feature flag status."""
    ENABLED = "enabled"
    DISABLED = "disabled"
    ROLLOUT = "rollout"  # Gradual rollout (percentage-based)


class FeatureFlag(Base):
    """
    Feature flag model.
    
    Controls feature availability globally or per role.
    """
    __tablename__ = 'feature_flags'
    
    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Feature identification
    name = Column(String(100), unique=True, nullable=False, index=True)  # e.g., "autofill", "ai_generation"
    display_name = Column(String(200), nullable=False)  # e.g., "Autofill Feature"
    description = Column(Text)
    
    # Feature flag status
    status = Column(String(20), nullable=False, default=FeatureFlagStatus.DISABLED.value)
    
    # Rollout configuration (for ROLLOUT status)
    rollout_percentage = Column(Integer, default=0)  # 0-100
    
    # Role-based overrides (JSON: {"role_name": "enabled"|"disabled"})
    role_overrides = Column(JSON, default={})
    
    # Additional configuration (JSON)
    config = Column(JSON, default={})
    
    # Metadata
    created_by = Column(Integer, ForeignKey('users.id'), nullable=True)
    updated_by = Column(Integer, ForeignKey('users.id'), nullable=True)
    
    # Status
    is_active = Column(Boolean, default=True)
    
    # Relationships
    creator = relationship('User', foreign_keys=[created_by])
    updater = relationship('User', foreign_keys=[updated_by])
    
    def __repr__(self):
        return f"<FeatureFlag(id={self.id}, name={self.name}, status={self.status})>"


class FeatureFlagHistory(Base):
    """
    Feature flag change history.
    
    Tracks changes to feature flags for audit purposes.
    """
    __tablename__ = 'feature_flag_history'
    
    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Foreign key
    feature_flag_id = Column(Integer, ForeignKey('feature_flags.id'), nullable=False, index=True)
    
    # Change details
    changed_by = Column(Integer, ForeignKey('users.id'), nullable=True)
    old_status = Column(String(20))
    new_status = Column(String(20))
    old_rollout_percentage = Column(Integer)
    new_rollout_percentage = Column(Integer)
    old_role_overrides = Column(JSON)
    new_role_overrides = Column(JSON)
    change_reason = Column(Text)
    
    # Relationships
    feature_flag = relationship('FeatureFlag', backref='history')
    changer = relationship('User', foreign_keys=[changed_by])
    
    def __repr__(self):
        return f"<FeatureFlagHistory(id={self.id}, feature_flag_id={self.feature_flag_id}, new_status={self.new_status})>"

