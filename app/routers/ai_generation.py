"""
AI text generation endpoints.
"""

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field

from app.db.database import get_db
from app.models.db.resume import ResumeProfile
from app.models.db.form_schema import FormSchema
from app.models.db.ai_generation import AIGeneration
from app.services.ai_service import generate_text, build_prompt
from resume_normalizer import normalize_resume, RoleProfile
from app.dependencies.feature_flags import require_ai_feature

router = APIRouter(prefix="/ai-generation", tags=["ai-generation"])


class GenerateTextRequest(BaseModel):
    """Request model for AI text generation."""
    resume_id: int = Field(..., description="Resume profile ID")
    schema_id: Optional[int] = Field(None, description="Form schema ID (optional)")
    job_description: str = Field(..., description="Job description text")
    field_name: str = Field("cover_letter", description="Field name (e.g., 'cover_letter', 'personal_statement')")
    field_type: str = Field("textarea", description="Field type (e.g., 'textarea', 'input')")
    model: Optional[str] = Field(None, description="AI model to use (defaults to configured model)")
    temperature: Optional[float] = Field(None, description="Temperature for generation (0.0-2.0)")
    max_tokens: Optional[int] = Field(None, description="Maximum tokens")


class GenerateTextResponse(BaseModel):
    """Response model for AI text generation."""
    success: bool = Field(..., description="Whether generation was successful")
    message: str = Field(..., description="Status message")
    generation_id: Optional[int] = Field(None, description="AI generation record ID")
    generated_text: Optional[str] = Field(None, description="Generated text")
    prompt: Optional[str] = Field(None, description="Prompt used")
    tokens_used: Optional[int] = Field(None, description="Tokens used")
    cost_estimate: Optional[float] = Field(None, description="Estimated cost")


class ApproveGenerationRequest(BaseModel):
    """Request model for approving AI generation."""
    generation_id: int = Field(..., description="AI generation ID")
    approved_text: Optional[str] = Field(None, description="Final approved text (may differ from generated)")
    user_feedback: Optional[str] = Field(None, description="User feedback")
    rating: Optional[int] = Field(None, description="Rating (1-5)")


class ApproveGenerationResponse(BaseModel):
    """Response model for approving AI generation."""
    success: bool = Field(..., description="Whether approval was successful")
    message: str = Field(..., description="Status message")


@router.post("/generate", response_model=GenerateTextResponse)
async def generate_ai_text(
    request: GenerateTextRequest,
    db: Session = Depends(get_db),
    _: bool = Depends(require_ai_feature())
):
    """
    Generate text using AI.
    
    Args:
        request: GenerateTextRequest with resume_id, job_description, and field info
        db: Database session
        
    Returns:
        GenerateTextResponse with generated text
    """
    # Load resume profile
    resume_profile = db.query(ResumeProfile).filter(
        ResumeProfile.id == request.resume_id
    ).first()
    
    if not resume_profile:
        raise HTTPException(status_code=404, detail=f"Resume profile {request.resume_id} not found")
    
    # Load form schema if provided
    form_schema = None
    if request.schema_id:
        form_schema = db.query(FormSchema).filter(
            FormSchema.id == request.schema_id
        ).first()
        if not form_schema:
            raise HTTPException(status_code=404, detail=f"Form schema {request.schema_id} not found")
    
    # Get normalized resume data
    parsed_data = resume_profile.parsed_data
    normalized_data = resume_profile.normalized_data
    
    # If normalized data doesn't exist, normalize it
    if not normalized_data:
        try:
            normalized_result = normalize_resume(
                raw_resume_data=parsed_data,
                role_profile=RoleProfile.DEFAULT,
                normalize=True
            )
            normalized_data = normalized_result.get('normalized', {})
            # Optionally save normalized data back to profile
            resume_profile.normalized_data = normalized_data
            db.commit()
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to normalize resume: {str(e)}"
            )
    
    # Generate text using AI
    try:
        result = generate_text(
            job_description=request.job_description,
            normalized_resume=normalized_data,
            field_name=request.field_name,
            model=request.model,
            temperature=request.temperature,
            max_tokens=request.max_tokens
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"AI generation failed: {str(e)}"
        )
    
    # Store generation in database
    ai_generation = AIGeneration(
        resume_profile_id=request.resume_id,
        form_schema_id=request.schema_id,
        job_description=request.job_description,
        normalized_resume_data=normalized_data,
        field_name=request.field_name,
        field_type=request.field_type,
        model_name=result['model_name'],
        prompt_template=build_prompt.__doc__ or "",
        prompt=result['prompt'],
        generated_text=result['generated_text'],
        raw_response=result['raw_response'],
        tokens_used=result['tokens_used'],
        cost_estimate=result['cost_estimate'],
        temperature=request.temperature or 0.7,
        max_tokens=request.max_tokens or 1000
    )
    
    db.add(ai_generation)
    db.commit()
    db.refresh(ai_generation)
    
    return GenerateTextResponse(
        success=True,
        message="Text generated successfully",
        generation_id=ai_generation.id,
        generated_text=result['generated_text'],
        prompt=result['prompt'],
        tokens_used=result['tokens_used'],
        cost_estimate=result['cost_estimate']
    )


@router.post("/approve", response_model=ApproveGenerationResponse)
async def approve_generation(
    request: ApproveGenerationRequest,
    db: Session = Depends(get_db)
):
    """
    Approve an AI-generated text.
    
    Args:
        request: ApproveGenerationRequest with generation_id and optional approved_text
        db: Database session
        
    Returns:
        ApproveGenerationResponse with success status
    """
    # Load AI generation
    ai_generation = db.query(AIGeneration).filter(
        AIGeneration.id == request.generation_id
    ).first()
    
    if not ai_generation:
        raise HTTPException(status_code=404, detail=f"AI generation {request.generation_id} not found")
    
    # Update approval status
    from datetime import timezone
    ai_generation.is_approved = True
    ai_generation.approved_at = datetime.now(timezone.utc)
    ai_generation.approved_text = request.approved_text or ai_generation.generated_text
    ai_generation.user_feedback = request.user_feedback
    ai_generation.rating = request.rating
    
    db.commit()
    
    return ApproveGenerationResponse(
        success=True,
        message="Generation approved successfully"
    )


@router.get("/history/{resume_id}")
async def get_generation_history(
    resume_id: int,
    db: Session = Depends(get_db),
    limit: int = 20
):
    """
    Get AI generation history for a resume.
    
    Args:
        resume_id: Resume profile ID
        db: Database session
        limit: Maximum number of records to return
        
    Returns:
        List of AI generation records
    """
    generations = db.query(AIGeneration).filter(
        AIGeneration.resume_profile_id == resume_id
    ).order_by(AIGeneration.created_at.desc()).limit(limit).all()
    
    return {
        "success": True,
        "generations": [
            {
                "id": gen.id,
                "field_name": gen.field_name,
                "field_type": gen.field_type,
                "generated_text": gen.generated_text,
                "approved_text": gen.approved_text,
                "is_approved": gen.is_approved,
                "created_at": gen.created_at.isoformat() if gen.created_at else None,
                "approved_at": gen.approved_at.isoformat() if gen.approved_at else None,
                "tokens_used": gen.tokens_used,
                "cost_estimate": gen.cost_estimate,
                "rating": gen.rating
            }
            for gen in generations
        ]
    }

