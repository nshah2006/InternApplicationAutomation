"""
Approved mapping database model.
"""

from sqlalchemy import Column, String, Integer, DateTime, JSON, ForeignKey, Float, Boolean
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.database import Base


class ApprovedMapping(Base):
    """
    Approved mapping model.
    
    Stores user-approved mappings between form fields and resume data.
    """
    __tablename__ = 'approved_mappings'
    
    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Foreign keys
    resume_profile_id = Column(Integer, ForeignKey('resume_profiles.id'), nullable=False, index=True)
    form_schema_id = Column(Integer, ForeignKey('form_schemas.id'), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    
    # Mapping data (stored as JSON array of field mappings)
    mappings = Column(JSON, nullable=False)
    
    # Mapping metadata
    total_mappings = Column(Integer, default=0)
    exact_matches = Column(Integer, default=0)
    fuzzy_matches = Column(Integer, default=0)
    manual_mappings = Column(Integer, default=0)
    
    # Approval status
    is_approved = Column(Boolean, default=False)
    approved_at = Column(DateTime(timezone=True))
    
    # Notes/description
    notes = Column(Text)
    
    # Relationships
    resume_profile = relationship('ResumeProfile', backref='mappings')
    form_schema = relationship('FormSchema', backref='mappings')

