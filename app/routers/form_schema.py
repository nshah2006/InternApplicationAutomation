"""
Form schema extraction endpoints.
"""

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session

from app.models.schemas import ExtractFormSchemaRequest, ExtractFormSchemaResponse
from app.db.database import get_db
from app.models.db.form_schema import FormSchema
from form_schema_extractor import extract_form_schema as extract_schema

router = APIRouter(prefix="/extract-form-schema", tags=["form-schema"])


@router.post("", response_model=ExtractFormSchemaResponse)
async def extract_form_schema(
    request: ExtractFormSchemaRequest,
    db: Session = Depends(get_db)
):
    """
    Extract form schema from a URL.
    
    Args:
        request: ExtractFormSchemaRequest with URL and options
        db: Database session
        
    Returns:
        ExtractFormSchemaResponse with extracted form schema
    """
    try:
        # Extract form schema
        schema_data = extract_schema(
            url=request.url,
            headless=request.headless,
            timeout=request.timeout
        )
        
        # Calculate statistics
        fields = schema_data.get('fields', [])
        total_fields = len(fields)
        
        mapped_fields = sum(1 for f in fields if f.get('suggested_canonical_field'))
        ignored_fields = sum(1 for f in fields if f.get('mapping_match_type') == 'ignored')
        unmapped_fields = total_fields - mapped_fields - ignored_fields
        
        # Create database record
        form_schema = FormSchema(
            url=request.url,
            title=schema_data.get('title'),
            platform=schema_data.get('platform'),
            schema_data=schema_data,
            total_fields=total_fields,
            mapped_fields=mapped_fields,
            ignored_fields=ignored_fields,
            unmapped_fields=unmapped_fields,
            schema_version=schema_data.get('canonical_schema_version')
        )
        
        db.add(form_schema)
        db.commit()
        db.refresh(form_schema)
        
        return ExtractFormSchemaResponse(
            success=True,
            message="Form schema extracted successfully",
            schema_data={
                "schema_id": form_schema.id,
                "schema": schema_data,
                "created_at": form_schema.created_at.isoformat() if form_schema.created_at else None
            }
        )
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to extract form schema: {str(e)}"
        )

