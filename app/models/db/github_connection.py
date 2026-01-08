"""
GitHub connection database model.
"""

from sqlalchemy import Column, String, Integer, DateTime, Boolean, ForeignKey, Text, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.database import Base


class GitHubConnection(Base):
    """
    GitHub connection model.
    
    Stores GitHub OAuth tokens and connection metadata for users.
    """
    __tablename__ = 'github_connections'
    
    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Foreign key to user
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True, unique=True)
    
    # GitHub OAuth token (encrypted in production)
    access_token = Column(String(512), nullable=False)  # GitHub OAuth access token
    token_type = Column(String(50), default='bearer')
    
    # GitHub user information
    github_username = Column(String(255), nullable=False)
    github_user_id = Column(String(255), nullable=False)  # GitHub's user ID
    github_email = Column(String(255))
    github_avatar_url = Column(String(512))
    
    # Connection status
    is_active = Column(Boolean, default=True)
    last_synced_at = Column(DateTime(timezone=True))
    
    # Scopes granted (read-only: public_repo, read:user)
    scopes = Column(String(255))  # Comma-separated list of scopes
    
    # Relationships
    user = relationship('User', backref='github_connection')
    selected_repos = relationship('GitHubRepo', backref='connection', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f"<GitHubConnection(id={self.id}, user_id={self.user_id}, github_username={self.github_username})>"


class GitHubRepo(Base):
    """
    GitHub repository model.
    
    Stores GitHub repository information and selection status.
    """
    __tablename__ = 'github_repos'
    
    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Foreign key to GitHub connection
    github_connection_id = Column(Integer, ForeignKey('github_connections.id'), nullable=False, index=True)
    
    # Repository identification
    repo_id = Column(Integer, nullable=False, unique=True)  # GitHub's repository ID
    full_name = Column(String(255), nullable=False)  # e.g., "username/repo-name"
    name = Column(String(255), nullable=False)  # Repository name
    
    # Repository metadata
    description = Column(Text)
    url = Column(String(512))  # GitHub URL
    homepage = Column(String(512))  # Project homepage
    language = Column(String(100))  # Primary language
    stars_count = Column(Integer, default=0)
    forks_count = Column(Integer, default=0)
    watchers_count = Column(Integer, default=0)
    
    # README content
    readme_content = Column(Text)  # Full README content
    readme_summary = Column(Text)  # Summarized README (first 500 chars)
    readme_fetched_at = Column(DateTime(timezone=True))
    
    # Selection status
    is_selected = Column(Boolean, default=False)  # User selected this repo as a project
    selected_at = Column(DateTime(timezone=True))
    
    # Additional metadata (stored as JSON)
    metadata = Column(JSON)  # Additional repo metadata (topics, license, etc.)
    
    # Relationships
    connection = relationship('GitHubConnection', backref='repos')
    
    def __repr__(self):
        return f"<GitHubRepo(id={self.id}, full_name={self.full_name}, is_selected={self.is_selected})>"

