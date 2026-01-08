"""
Resume profile database model.
"""

from sqlalchemy import Column, String, Integer, DateTime, JSON, Text, ForeignKey
from sqlalchemy.sql import func
from app.db.database import Base


class ResumeProfile(Base):
    """
    Resume profile model.
    
    Stores parsed resume data and metadata.
    """
    __tablename__ = 'resume_profiles'
    
    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # File metadata
    original_filename = Column(String(255), nullable=False)
    file_type = Column(String(10), nullable=False)  # pdf, docx
    file_size = Column(Integer)  # Size in bytes
    
    # Parsed resume data (stored as JSON)
    parsed_data = Column(JSON, nullable=False)
    
    # Normalized data (optional, can be computed on demand)
    normalized_data = Column(JSON)
    
    # Metadata
    name = Column(String(255))  # Extracted name
    email = Column(String(255))  # Extracted email
    phone = Column(String(50))  # Extracted phone
    
    # Notes/description
    notes = Column(Text)
    
    # Foreign key to user
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)

