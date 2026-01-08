"""
Mapping review endpoints.
"""

from fastapi import APIRouter, HTTPException, Query, Depends
from sqlalchemy.orm import Session
from typing import Optional, List, Dict, Any

from app.models.schemas import MappingReviewResponse
from app.db.database import get_db
from app.models.db.resume import ResumeProfile
from app.models.db.form_schema import FormSchema
from app.models.db.mapping import ApprovedMapping
from ats_field_mapper import map_multiple_fields, SelectionStrategy
from app.core.logging_config import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/mapping-review", tags=["mapping"])


@router.get("", response_model=MappingReviewResponse)
async def get_mapping_review(
    resume_id: Optional[int] = Query(None, description="Resume ID to review mappings for"),
    schema_id: Optional[int] = Query(None, description="Form schema ID to review mappings for"),
    db: Session = Depends(get_db)
):
    """
    Get mapping review for resume and form schema.
    
    Args:
        resume_id: Optional resume ID
        schema_id: Optional form schema ID
        db: Database session
        
    Returns:
        MappingReviewResponse with field mappings for review
    """
    # Load resume profile if ID provided
    resume_data = None
    resume_profile = None
    if resume_id:
        resume_profile = db.query(ResumeProfile).filter(ResumeProfile.id == resume_id).first()
        if not resume_profile:
            raise HTTPException(status_code=404, detail=f"Resume profile {resume_id} not found")
        resume_data = resume_profile.parsed_data
    
    # Load form schema if ID provided
    form_schema_obj = None
    schema_data = None
    if schema_id:
        form_schema_obj = db.query(FormSchema).filter(FormSchema.id == schema_id).first()
        if not form_schema_obj:
            raise HTTPException(status_code=404, detail=f"Form schema {schema_id} not found")
        schema_data = form_schema_obj.schema_data
    
    # If both IDs provided, check for existing approved mapping
    approved_mapping = None
    if resume_id and schema_id:
        approved_mapping = db.query(ApprovedMapping).filter(
            ApprovedMapping.resume_profile_id == resume_id,
            ApprovedMapping.form_schema_id == schema_id
        ).first()
    
    # Generate mappings if we have both resume and schema data
    mappings: List[Dict[str, Any]] = []
    if resume_data and schema_data:
        # Extract field names from schema
        fields = schema_data.get('fields', [])
        field_names = [
            f.get('label_text') or f.get('placeholder') or f.get('aria_label') or f.get('name', '')
            for f in fields
            if f.get('label_text') or f.get('placeholder') or f.get('aria_label') or f.get('name')
        ]
        
        # Generate mappings
        if field_names:
            mapping_results = map_multiple_fields(
                ats_field_names=field_names,
                resume_data=resume_data,
                selection_strategy=SelectionStrategy.MOST_RECENT,
                fuzzy_threshold=0.7,
                explain=True
            )
            
            # Convert to list format and track failed mappings
            failed_mappings = []
            for field_name, mapping_result in mapping_results.items():
                # Check if mapping failed (no value found or low confidence)
                match_type = mapping_result.get('match_type', 'none')
                confidence = mapping_result.get('confidence', 0.0)
                value = mapping_result.get('value')
                
                # Log failed mappings
                if match_type == 'none' or (match_type != 'exact' and confidence < 0.5) or not value:
                    failed_mappings.append({
                        'ats_field_name': field_name,
                        'match_type': match_type,
                        'confidence': confidence,
                        'resume_id': resume_id,
                        'schema_id': schema_id
                    })
                
                mappings.append({
                    "ats_field_name": field_name,
                    **mapping_result
                })
            
            # Log failed mappings for monitoring
            if failed_mappings:
                logger.warning(
                    "Failed mappings detected",
                    extra={
                        'event_type': 'mapping_failed',
                        'failed_count': len(failed_mappings),
                        'total_fields': len(field_names),
                        'failed_fields': [
                            {
                                'field': fm['ats_field_name'],
                                'match_type': fm['match_type'],
                                'confidence': fm['confidence']
                            }
                            for fm in failed_mappings
                        ],
                        'resume_id': resume_id,
                        'schema_id': schema_id
                    }
                )
    
    # Use approved mapping if available
    if approved_mapping and approved_mapping.mappings:
        mappings = approved_mapping.mappings
    
    return MappingReviewResponse(
        success=True,
        message="Mapping review retrieved successfully",
        mappings=mappings,
        resume_data=resume_data if resume_data else None,
        form_schema=schema_data if schema_data else None
    )

