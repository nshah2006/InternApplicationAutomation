#!/usr/bin/env python3
"""
Playwright-based Form Schema Extractor.

Extracts form field information from web pages and normalizes field names
using ats_field_mapper. Outputs JSON schema only. Read-only extraction
(does not fill or submit forms).
"""

import json
import sys
from typing import Dict, List, Optional, Any
from playwright.sync_api import sync_playwright, Page
from ats_field_mapper import normalize_field_name, map_ats_field, CanonicalField


def extract_label_text(page: Page, field_element) -> Optional[str]:
    """
    Extract label text for a field using multiple strategies.
    
    Args:
        page: Playwright page object
        field_element: Field element handle
        
    Returns:
        Label text if found, None otherwise
    """
    # Strategy 1: aria-labelledby
    try:
        aria_labelledby = field_element.get_attribute('aria-labelledby')
        if aria_labelledby:
            for label_id in aria_labelledby.split():
                try:
                    label_element = page.query_selector(f'#{label_id}')
                    if label_element:
                        text = label_element.inner_text()
                        if text and text.strip():
                            return text.strip()
                except:
                    continue
    except:
        pass
    
    # Strategy 2: aria-label
    try:
        aria_label = field_element.get_attribute('aria-label')
        if aria_label and aria_label.strip():
            return aria_label.strip()
    except:
        pass
    
    # Strategy 3: Associated label element (for attribute)
    try:
        field_id = field_element.get_attribute('id')
        if field_id:
            label_element = page.query_selector(f'label[for="{field_id}"]')
            if label_element:
                text = label_element.inner_text()
                if text and text.strip():
                    return text.strip()
    except:
        pass
    
    # Strategy 4: Parent label element
    try:
        parent_text = field_element.evaluate('''el => {
            let parent = el.parentElement;
            if (parent && parent.tagName === 'LABEL') {
                return parent.innerText.trim();
            }
            return null;
        }''')
        if parent_text:
            return parent_text
    except:
        pass
    
    # Strategy 5: Preceding label element
    try:
        preceding_text = field_element.evaluate('''el => {
            let sibling = el.previousElementSibling;
            while (sibling) {
                if (sibling.tagName === 'LABEL') {
                    return sibling.innerText.trim();
                }
                sibling = sibling.previousElementSibling;
            }
            return null;
        }''')
        if preceding_text:
            return preceding_text
    except:
        pass
    
    return None


def detect_ats_platform(url: str, page: Page) -> Optional[str]:
    """
    Detect ATS platform based on URL and DOM characteristics.
    
    Args:
        url: Page URL
        page: Playwright page object
        
    Returns:
        Platform name ('greenhouse', 'lever', 'workday') or None if unknown
    """
    url_lower = url.lower()
    
    # Greenhouse detection
    if 'greenhouse.io' in url_lower or 'boards.greenhouse.io' in url_lower:
        return 'greenhouse'
    
    # Check for Greenhouse DOM indicators
    try:
        greenhouse_indicators = [
            page.query_selector('[data-qa="greenhouse"]'),
            page.query_selector('.greenhouse'),
            page.query_selector('#greenhouse'),
            page.query_selector('script[src*="greenhouse"]')
        ]
        if any(indicator for indicator in greenhouse_indicators if indicator):
            return 'greenhouse'
    except:
        pass
    
    # Lever detection
    if 'lever.co' in url_lower or 'jobs.lever.co' in url_lower:
        return 'lever'
    
    # Check for Lever DOM indicators
    try:
        lever_indicators = [
            page.query_selector('[data-qa="lever"]'),
            page.query_selector('.lever'),
            page.query_selector('#lever'),
            page.query_selector('script[src*="lever"]'),
            page.query_selector('[class*="lever-"]')
        ]
        if any(indicator for indicator in lever_indicators if indicator):
            return 'lever'
    except:
        pass
    
    # Workday detection
    if 'workday.com' in url_lower or 'myworkdayjobs.com' in url_lower:
        return 'workday'
    
    # Check for Workday DOM indicators
    try:
        workday_indicators = [
            page.query_selector('[data-automation-id*="workday"]'),
            page.query_selector('[data-automation-id*="Workday"]'),
            page.query_selector('.workday'),
            page.query_selector('#workday'),
            page.query_selector('script[src*="workday"]'),
            page.query_selector('[class*="workday-"]'),
            page.query_selector('[id*="workday"]')
        ]
        if any(indicator for indicator in workday_indicators if indicator):
            return 'workday'
    except:
        pass
    
    return None


def extract_form_schema(url: str, headless: bool = True, timeout: int = 30000) -> Dict[str, Any]:
    """
    Extract form schema from a URL.
    
    Args:
        url: URL to extract forms from
        headless: Run browser in headless mode
        timeout: Page load timeout in milliseconds
        
    Returns:
        Dictionary with form schema information including detected platform
    """
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)
        context = browser.new_context()
        page = context.new_page()
        
        try:
            page.goto(url, wait_until='domcontentloaded', timeout=timeout)
            
            # Get page title
            title = page.title()
            
            # Detect ATS platform
            platform = detect_ats_platform(url, page)
            
            # Find all form fields: input, textarea, select
            all_fields = []
            
            # Find fields in forms
            forms = page.query_selector_all('form')
            for form_idx, form in enumerate(forms):
                fields = form.query_selector_all('input, textarea, select')
                for field_element in fields:
                    field_info = extract_field_info(page, field_element, form_idx)
                    if field_info:
                        all_fields.append(field_info)
            
            # Find standalone fields (outside forms)
            standalone_fields = page.query_selector_all(
                'input:not(form input), textarea:not(form textarea), select:not(form select)'
            )
            for field_element in standalone_fields:
                field_info = extract_field_info(page, field_element, None)
                if field_info:
                    all_fields.append(field_info)
            
            browser.close()
            
            # Build result
            result = {
                'url': url,
                'title': title,
                'platform': platform,
                'fields': all_fields,
                'total_fields': len(all_fields)
            }
            
            return result
            
        except Exception as e:
            browser.close()
            raise


def extract_field_info(page: Page, field_element, form_index: Optional[int]) -> Optional[Dict[str, Any]]:
    """
    Extract information about a single form field.
    
    Args:
        page: Playwright page object
        field_element: Field element handle
        form_index: Index of form this field belongs to (None for standalone)
        
    Returns:
        Dictionary with field information, or None if field should be skipped
    """
    try:
        # Basic field properties
        tag_name = field_element.evaluate('el => el.tagName').lower()
        field_type = tag_name
        input_type = field_element.get_attribute('type') if tag_name == 'input' else None
        
        # Skip hidden fields
        is_hidden = field_element.evaluate('''el => {
            const style = window.getComputedStyle(el);
            return style.display === "none" || style.visibility === "hidden" || el.hidden;
        }''')
        
        if is_hidden:
            return None
        
        # Extract labels/names from multiple sources
        label_text = extract_label_text(page, field_element)
        placeholder_text = field_element.get_attribute('placeholder')
        aria_label = field_element.get_attribute('aria-label')
        name_attribute = field_element.get_attribute('name')
        id_attribute = field_element.get_attribute('id')
        
        # Field properties
        required = field_element.evaluate('el => el.required || el.hasAttribute("required")')
        
        # Determine best field name for mapping (priority: label > placeholder > aria-label > name > id)
        field_name_candidates = [
            label_text,
            placeholder_text,
            aria_label,
            name_attribute,
            id_attribute
        ]
        
        # Use the first non-empty candidate
        best_field_name = next((name for name in field_name_candidates if name and name.strip()), None)
        
        # Normalize field name
        normalized_field_name = None
        suggested_canonical_field = None
        mapping_confidence = None
        mapping_match_type = None
        
        if best_field_name:
            normalized_field_name, _ = normalize_field_name(best_field_name, track_steps=False)
            
            # Try to map using ats_field_mapper (with dummy resume data for field identification)
            dummy_resume = {
                'name': None,
                'email': None,
                'phone': None,
                'education': [],
                'experience': [],
                'skills': [],
                'projects': []
            }
            
            mapping_result = map_ats_field(best_field_name, dummy_resume, explain=False)
            if mapping_result:
                suggested_canonical_field = mapping_result.get('canonical_field')
                mapping_confidence = mapping_result.get('confidence', 0.0)
                mapping_match_type = mapping_result.get('match_type')
        
        # Build field info
        field_info = {
            'field_type': field_type,
            'input_type': input_type,
            'label_text': label_text,
            'placeholder': placeholder_text,
            'aria_label': aria_label,
            'name': name_attribute,
            'id': id_attribute,
            'required': required,
            'form_index': form_index,
            'field_name': best_field_name,
            'normalized_field_name': normalized_field_name,
            'suggested_canonical_field': suggested_canonical_field,
            'mapping_confidence': mapping_confidence,
            'mapping_match_type': mapping_match_type
        }
        
        return field_info
        
    except Exception:
        # Skip fields that can't be processed
        return None


def main():
    """Command-line entry point."""
    if len(sys.argv) < 2:
        print("Usage: python form_schema_extractor.py <url> [--headless=false]", file=sys.stderr)
        sys.exit(1)
    
    url = sys.argv[1]
    headless = '--headless=false' not in sys.argv
    
    try:
        schema = extract_form_schema(url, headless=headless)
        print(json.dumps(schema, indent=2, ensure_ascii=False))
    except Exception as e:
        print(json.dumps({'error': str(e)}, indent=2), file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
