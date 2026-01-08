"""
Pydantic schemas for API request/response models.
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class UploadResumeRequest(BaseModel):
    """Request model for resume upload endpoint."""
    # TODO: Add file upload handling
    pass


class UploadResumeResponse(BaseModel):
    """Response model for resume upload endpoint."""
    success: bool = Field(..., description="Whether upload was successful")
    message: str = Field(..., description="Status message")
    data: Optional[Dict[str, Any]] = Field(None, description="Response data with resume_id and parsed_data")


class ExtractFormSchemaRequest(BaseModel):
    """Request model for form schema extraction endpoint."""
    url: str = Field(..., description="URL to extract form schema from")
    headless: bool = Field(True, description="Run browser in headless mode")
    timeout: int = Field(30000, description="Timeout in milliseconds")


class ExtractFormSchemaResponse(BaseModel):
    """Response model for form schema extraction endpoint."""
    success: bool = Field(..., description="Whether extraction was successful")
    message: str = Field(..., description="Status message")
    schema_data: Optional[Dict[str, Any]] = Field(None, description="Response data with schema_id and schema")


class MappingReviewResponse(BaseModel):
    """Response model for mapping review endpoint."""
    success: bool = Field(..., description="Whether request was successful")
    message: str = Field(..., description="Status message")
    mappings: Optional[List[Dict[str, Any]]] = Field(None, description="Field mappings for review")
    resume_data: Optional[Dict[str, Any]] = Field(None, description="Resume data for context")
    form_schema: Optional[Dict[str, Any]] = Field(None, description="Form schema for context")


class GenerateTextRequest(BaseModel):
    """Request model for AI text generation endpoint."""
    resume_id: int = Field(..., description="Resume profile ID")
    job_description: str = Field(..., description="Job description text")
    field_type: str = Field(..., description="Type of text field (e.g., 'cover_letter', 'personal_statement')")
    max_length: Optional[int] = Field(500, description="Maximum length of generated text")


class GenerateTextResponse(BaseModel):
    """Response model for AI text generation endpoint."""
    success: bool = Field(..., description="Whether generation was successful")
    message: str = Field(..., description="Status message")
    generation_id: Optional[int] = Field(None, description="ID of the stored generation")
    suggested_text: Optional[str] = Field(None, description="AI-generated text suggestion")
    is_approved: bool = Field(False, description="Whether the suggestion is approved")


class ApproveGenerationRequest(BaseModel):
    """Request model for approving AI generation."""
    generation_id: int = Field(..., description="AI generation ID to approve")
    approved_text: Optional[str] = Field(None, description="Final approved text (may differ from suggestion)")


class ApproveGenerationResponse(BaseModel):
    """Response model for approving AI generation."""
    success: bool = Field(..., description="Whether approval was successful")
    message: str = Field(..., description="Status message")

