"""
User database model.
"""

from sqlalchemy import Column, String, Integer, DateTime, Boolean, Enum as SQLEnum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.database import Base
import enum


class OAuthProvider(str, enum.Enum):
    """OAuth provider types."""
    GOOGLE = "google"
    GITHUB = "github"


class User(Base):
    """
    User model.
    
    Stores user account information and OAuth provider details.
    """
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_login = Column(DateTime(timezone=True))
    
    # User identification
    email = Column(String(255), unique=True, nullable=False, index=True)
    username = Column(String(100), unique=True, nullable=True, index=True)
    full_name = Column(String(255))
    
    # OAuth provider information
    oauth_provider = Column(SQLEnum(OAuthProvider), nullable=False)
    oauth_provider_id = Column(String(255), nullable=False)  # Provider's user ID
    oauth_email = Column(String(255))  # Email from OAuth provider
    
    # Profile picture
    avatar_url = Column(String(512))
    
    # Account status
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    
    # Relationships
    resume_profiles = relationship('ResumeProfile', backref='user', cascade='all, delete-orphan')
    form_schemas = relationship('FormSchema', backref='user', cascade='all, delete-orphan')
    approved_mappings = relationship('ApprovedMapping', backref='user', cascade='all, delete-orphan')
    ai_generations = relationship('AIGeneration', backref='user', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f"<User(id={self.id}, email={self.email}, provider={self.oauth_provider})>"

