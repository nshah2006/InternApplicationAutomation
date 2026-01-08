"""
AI text generation database model.
"""

from sqlalchemy import Column, String, Integer, DateTime, JSON, Text, ForeignKey, Boolean, Float
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.database import Base


class AIGeneration(Base):
    """
    AI text generation model.
    
    Stores AI-generated text suggestions, prompts, and approval status.
    """
    __tablename__ = 'ai_generations'
    
    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Foreign keys
    resume_profile_id = Column(Integer, ForeignKey('resume_profiles.id'), nullable=False, index=True)
    form_schema_id = Column(Integer, ForeignKey('form_schemas.id'), nullable=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    
    # Input data
    job_description = Column(Text, nullable=False)
    normalized_resume_data = Column(JSON, nullable=False)
    
    # Field context (which form field this is for)
    field_name = Column(String(255))  # e.g., "cover_letter", "personal_statement"
    field_type = Column(String(50))  # e.g., "textarea", "input"
    
    # AI generation metadata
    model_name = Column(String(100))  # e.g., "gpt-4", "gpt-3.5-turbo"
    prompt_template = Column(Text)  # The prompt template used
    prompt = Column(Text, nullable=False)  # The actual prompt sent to AI
    temperature = Column(Float, default=0.7)
    max_tokens = Column(Integer, default=1000)
    
    # AI response
    generated_text = Column(Text, nullable=False)
    raw_response = Column(JSON)  # Full API response for debugging
    
    # Usage tracking
    tokens_used = Column(Integer)
    cost_estimate = Column(Float)  # Estimated cost in USD
    
    # Approval workflow
    is_approved = Column(Boolean, default=False)
    approved_at = Column(DateTime(timezone=True))
    approved_text = Column(Text)  # Final approved text (may differ from generated)
    
    # User feedback
    user_feedback = Column(Text)
    rating = Column(Integer)  # 1-5 rating
    
    # Notes
    notes = Column(Text)
    
    # Relationships
    resume_profile = relationship('ResumeProfile', backref='ai_generations')
    form_schema = relationship('FormSchema', backref='ai_generations')

