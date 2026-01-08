"""
Preview mode endpoints for live form autofill.
"""

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
import asyncio
from concurrent.futures import ThreadPoolExecutor

from app.db.database import get_db
from app.models.db.resume import ResumeProfile
from app.models.db.form_schema import FormSchema
from ats_field_mapper import map_ats_field, SelectionStrategy
from playwright.sync_api import sync_playwright, Page
from app.core.logging_config import get_logger
from app.dependencies.feature_flags import require_autofill_feature

logger = get_logger(__name__)
router = APIRouter(prefix="/preview", tags=["preview"])


class PreviewAutofillRequest(BaseModel):
    """Request model for preview autofill endpoint."""
    resume_id: int = Field(..., description="Resume profile ID")
    schema_id: int = Field(..., description="Form schema ID")
    url: str = Field(..., description="Form URL to autofill")


class PreviewAutofillResponse(BaseModel):
    """Response model for preview autofill endpoint."""
    success: bool = Field(..., description="Whether autofill was successful")
    message: str = Field(..., description="Status message")
    preview_url: Optional[str] = Field(None, description="URL with preview parameters")


def fill_form_field(page: Page, field_info: Dict[str, Any], value: Any) -> bool:
    """
    Fill a form field using Playwright.
    
    Args:
        page: Playwright page object
        field_info: Field information from schema
        value: Value to fill
        
    Returns:
        True if field was filled successfully, False otherwise
    """
    if not value:
        return False
    
    try:
        # Try multiple selector strategies
        selectors = []
        
        # Priority: id > name > aria-label > label text
        if field_info.get('id_attribute'):
            selectors.append(f"#{field_info['id_attribute']}")
        
        if field_info.get('name_attribute'):
            selectors.append(f"[name='{field_info['name_attribute']}']")
        
        if field_info.get('aria_label'):
            selectors.append(f"[aria-label='{field_info['aria_label']}']")
        
        # Try to find by label text (more complex)
        if field_info.get('label_text'):
            # Try to find label and then the associated input
            try:
                label = page.query_selector(f"text='{field_info['label_text']}'")
                if label:
                    label_for = label.get_attribute('for')
                    if label_for:
                        selectors.append(f"#{label_for}")
            except:
                pass
        
        # Try each selector
        for selector in selectors:
            try:
                element = page.query_selector(selector)
                if element:
                    field_type = field_info.get('field_type', '').lower()
                    input_type = field_info.get('input_type', '').lower()
                    
                    # Handle different field types
                    if field_type == 'select':
                        # For select dropdowns
                        page.select_option(selector, str(value))
                        return True
                    elif field_type == 'textarea':
                        page.fill(selector, str(value))
                        return True
                    elif field_type == 'input':
                        if input_type in ['checkbox', 'radio']:
                            if value:
                                page.check(selector)
                            else:
                                page.uncheck(selector)
                        else:
                            page.fill(selector, str(value))
                        return True
            except Exception as e:
                continue
        
        return False
    except Exception as e:
        return False


def _run_preview_autofill(resume_data: Dict[str, Any], schema_data: Dict[str, Any], url: str) -> Dict[str, Any]:
    """
    Run preview autofill in a synchronous context.
    
    This function runs in a thread pool to avoid blocking the async event loop.
    """
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False)  # Show browser for preview
            context = browser.new_context()
            page = context.new_page()
            
            # Navigate to form URL
            page.goto(url, wait_until='domcontentloaded', timeout=30000)
            
            # Wait for form to load
            page.wait_for_timeout(2000)
            
            filled_count = 0
            failed_fields = []
            fields = schema_data.get('fields', [])
            
            # Fill each field based on mappings
            for field_info in fields:
                # Skip ignored fields
                if field_info.get('mapping_match_type') == 'ignored':
                    continue
                
                # Get field name for mapping
                field_name = (
                    field_info.get('label_text') or
                    field_info.get('placeholder') or
                    field_info.get('aria_label') or
                    field_info.get('name_attribute') or
                    field_info.get('id_attribute') or
                    ''
                )
                
                if not field_name:
                    continue
                
                # Map field to resume data
                mapping_result = map_ats_field(
                    ats_field_name=field_name,
                    resume_data=resume_data,
                    selection_strategy=SelectionStrategy.MOST_RECENT,
                    fuzzy_threshold=0.7,
                    explain=False
                )
                
                if mapping_result and mapping_result.get('value'):
                    value = mapping_result['value']
                    
                    # Fill the field
                    if fill_form_field(page, field_info, value):
                        filled_count += 1
                    else:
                        # Track failed field fills
                        failed_fields.append({
                            'field_name': field_name,
                            'field_type': field_info.get('field_type'),
                            'has_value': True
                        })
                else:
                    # Track fields without mappings
                    failed_fields.append({
                        'field_name': field_name,
                        'field_type': field_info.get('field_type'),
                        'has_value': False,
                        'match_type': mapping_result.get('match_type', 'none') if mapping_result else 'none'
                    })
            
            # Keep browser open for preview (user will close it)
            # Browser will stay open until user closes it
            
            return {
                'success': True,
                'filled_count': filled_count,
                'failed_fields': failed_fields,
                'message': f"Preview mode activated. Filled {filled_count} fields. Form will revert on reload."
            }
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'failed_fields': failed_fields if 'failed_fields' in locals() else []
        }


@router.post("/autofill", response_model=PreviewAutofillResponse)
async def preview_autofill(
    request: PreviewAutofillRequest,
    db: Session = Depends(get_db),
    _: bool = Depends(require_autofill_feature())
):
    """
    Autofill a form in preview mode.
    
    This endpoint uses Playwright to fill form fields based on resume data
    and mappings. The form is filled but not submitted, and will revert
    on page reload.
    
    Args:
        request: PreviewAutofillRequest with resume_id, schema_id, and url
        db: Database session
        
    Returns:
        PreviewAutofillResponse with success status
    """
    # Load resume profile
    resume_profile = db.query(ResumeProfile).filter(
        ResumeProfile.id == request.resume_id
    ).first()
    
    if not resume_profile:
        raise HTTPException(status_code=404, detail=f"Resume profile {request.resume_id} not found")
    
    # Load form schema
    form_schema = db.query(FormSchema).filter(
        FormSchema.id == request.schema_id
    ).first()
    
    if not form_schema:
        raise HTTPException(status_code=404, detail=f"Form schema {request.schema_id} not found")
    
    resume_data = resume_profile.parsed_data
    schema_data = form_schema.schema_data
    fields = schema_data.get('fields', [])
    
    if not fields:
        raise HTTPException(status_code=400, detail="No fields found in form schema")
    
    # Run Playwright in a thread pool to avoid blocking
    loop = asyncio.get_event_loop()
    executor = ThreadPoolExecutor(max_workers=1)
    
    try:
        result = await loop.run_in_executor(
            executor,
            _run_preview_autofill,
            resume_data,
            schema_data,
            request.url
        )
        
        if not result.get('success'):
            # Log autofill abort
            logger.error(
                "Autofill aborted",
                extra={
                    'event_type': 'autofill_abort',
                    'resume_id': request.resume_id,
                    'schema_id': request.schema_id,
                    'url': request.url,
                    'error': result.get('error'),
                    'failed_fields': result.get('failed_fields', [])
                }
            )
            raise HTTPException(
                status_code=500,
                detail=result.get('error', 'Failed to autofill form')
            )
        
        # Log successful autofill with failed fields info
        failed_fields = result.get('failed_fields', [])
        if failed_fields:
            logger.warning(
                "Autofill completed with failed fields",
                extra={
                    'event_type': 'autofill_partial',
                    'resume_id': request.resume_id,
                    'schema_id': request.schema_id,
                    'filled_count': result.get('filled_count', 0),
                    'failed_count': len(failed_fields),
                    'failed_fields': [
                        {
                            'field_name': ff.get('field_name'),
                            'field_type': ff.get('field_type'),
                            'has_value': ff.get('has_value'),
                            'match_type': ff.get('match_type')
                        }
                        for ff in failed_fields
                    ]
                }
            )
        
        return PreviewAutofillResponse(
            success=True,
            message=result['message'],
            preview_url=request.url
        )
        
    except HTTPException:
        raise
    except Exception as e:
        # Log unexpected autofill abort
        logger.error(
            "Autofill aborted unexpectedly",
            extra={
                'event_type': 'autofill_abort',
                'resume_id': request.resume_id,
                'schema_id': request.schema_id,
                'url': request.url,
                'error_type': type(e).__name__,
                'error_message': str(e)
            },
            exc_info=True
        )
        raise HTTPException(
            status_code=500,
            detail=f"Failed to autofill form: {str(e)}"
        )

