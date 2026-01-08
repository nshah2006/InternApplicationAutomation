"""
Form schema database model.
"""

from sqlalchemy import Column, String, Integer, DateTime, JSON, Text, ForeignKey
from sqlalchemy.sql import func
from app.db.database import Base


class FormSchema(Base):
    """
    Form schema model.
    
    Stores extracted form schemas from ATS platforms.
    """
    __tablename__ = 'form_schemas'
    
    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Source information
    url = Column(String(2048), nullable=False, index=True)
    title = Column(String(500))
    platform = Column(String(50))  # greenhouse, lever, workday, etc.
    
    # Schema data (stored as JSON)
    schema_data = Column(JSON, nullable=False)
    
    # Statistics
    total_fields = Column(Integer, default=0)
    mapped_fields = Column(Integer, default=0)
    ignored_fields = Column(Integer, default=0)
    unmapped_fields = Column(Integer, default=0)
    
    # Schema version
    schema_version = Column(String(20))  # Canonical schema version
    
    # Notes/description
    notes = Column(Text)
    
    # Foreign key to user
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)

