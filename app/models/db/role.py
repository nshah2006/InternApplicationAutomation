"""
Role and permission database models.
"""

from sqlalchemy import Column, String, Integer, DateTime, Boolean, ForeignKey, Table, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.database import Base
import enum


class UserRole(str, enum.Enum):
    """User role types."""
    USER = "user"  # Regular user
    ADMIN = "admin"  # Administrator
    MODERATOR = "moderator"  # Moderator


# Association table for user roles (many-to-many)
user_roles = Table(
    'user_roles',
    Base.metadata,
    Column('user_id', Integer, ForeignKey('users.id'), primary_key=True),
    Column('role_id', Integer, ForeignKey('roles.id'), primary_key=True)
)


class Role(Base):
    """
    Role model.
    
    Defines user roles and their permissions.
    """
    __tablename__ = 'roles'
    
    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Role identification
    name = Column(String(50), unique=True, nullable=False, index=True)  # e.g., "admin", "user"
    display_name = Column(String(100), nullable=False)  # e.g., "Administrator"
    description = Column(Text)
    
    # Permissions (stored as JSON or comma-separated)
    permissions = Column(Text)  # JSON array of permission strings
    
    # Status
    is_active = Column(Boolean, default=True)
    
    # Relationships
    users = relationship('User', secondary=user_roles, backref='roles')
    
    def __repr__(self):
        return f"<Role(id={self.id}, name={self.name})>"


class UserRoleAssignment(Base):
    """
    User role assignment model.
    
    Tracks which users have which roles.
    """
    __tablename__ = 'user_role_assignments'
    
    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Foreign keys
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    role_id = Column(Integer, ForeignKey('roles.id'), nullable=False, index=True)
    
    # Assignment metadata
    assigned_by = Column(Integer, ForeignKey('users.id'), nullable=True)  # Who assigned this role
    expires_at = Column(DateTime(timezone=True), nullable=True)  # Optional expiration
    
    # Status
    is_active = Column(Boolean, default=True)
    
    # Relationships
    user = relationship('User', foreign_keys=[user_id], backref='role_assignments')
    role = relationship('Role', backref='assignments')
    assigner = relationship('User', foreign_keys=[assigned_by])
    
    def __repr__(self):
        return f"<UserRoleAssignment(id={self.id}, user_id={self.user_id}, role_id={self.role_id})>"

