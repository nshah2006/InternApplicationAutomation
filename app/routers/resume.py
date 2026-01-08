"""
Resume upload and processing endpoints.
"""

from fastapi import APIRouter, HTTPException, UploadFile, File, Depends
from sqlalchemy.orm import Session
from typing import Optional
import os
import tempfile

from app.models.schemas import UploadResumeRequest, UploadResumeResponse
from app.db.database import get_db
from app.models.db.resume import ResumeProfile
from resume_parser import parse_resume

router = APIRouter(prefix="/upload-resume", tags=["resume"])


@router.post("", response_model=UploadResumeResponse)
async def upload_resume(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Upload and parse a resume file.
    
    Args:
        file: Resume file (PDF or DOCX)
        db: Database session
        
    Returns:
        UploadResumeResponse with parsed resume data
    """
    # Validate file type
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")
    
    file_ext = os.path.splitext(file.filename)[1].lower()
    if file_ext not in ['.pdf', '.docx']:
        raise HTTPException(
            status_code=400,
            detail="Invalid file type. Only PDF and DOCX files are supported."
        )
    
    # Save file temporarily
    file_content = await file.read()
    file_size = len(file_content)
    
    with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as tmp_file:
        tmp_file.write(file_content)
        tmp_file_path = tmp_file.name
    
    try:
        # Parse resume
        parsed_data = parse_resume(tmp_file_path)
        
        # Extract metadata
        name = parsed_data.get('name')
        email = parsed_data.get('email')
        phone = parsed_data.get('phone')
        
        # Determine file type
        file_type = 'pdf' if file_ext == '.pdf' else 'docx'
        
        # Create database record
        resume_profile = ResumeProfile(
            original_filename=file.filename,
            file_type=file_type,
            file_size=file_size,
            parsed_data=parsed_data,
            name=name,
            email=email,
            phone=phone
        )
        
        db.add(resume_profile)
        db.commit()
        db.refresh(resume_profile)
        
        return UploadResumeResponse(
            success=True,
            message="Resume uploaded and parsed successfully",
            data={
                "resume_id": resume_profile.id,
                "parsed_data": parsed_data,
                "created_at": resume_profile.created_at.isoformat() if resume_profile.created_at else None
            }
        )
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to parse resume: {str(e)}"
        )
    finally:
        # Clean up temporary file
        if os.path.exists(tmp_file_path):
            os.unlink(tmp_file_path)

