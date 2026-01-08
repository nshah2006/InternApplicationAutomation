#!/usr/bin/env python3
"""
Example demonstrating form schema extraction using Playwright.
"""

from form_schema_extractor import FormSchemaExtractor, extract_form_schema
import json


def example_form_extraction():
    """Examples of form schema extraction."""
    
    print("=" * 80)
    print("FORM SCHEMA EXTRACTION EXAMPLES")
    print("=" * 80)
    
    # Example 1: Extract from a test URL (you can replace with actual job application form)
    print("\n1. Extracting Form Schema from URL:")
    print("-" * 80)
    
    # Note: Replace with an actual URL that has forms
    # For demonstration, we'll show the structure
    test_url = "https://example.com"  # Replace with actual form URL
    
    print(f"URL: {test_url}")
    print("\nNote: This is a demonstration. Replace with an actual form URL.")
    print("The extractor will:")
    print("  - Navigate to the URL")
    print("  - Extract all form fields")
    print("  - Extract labels, placeholders, aria-labels")
    print("  - Map fields to canonical schema")
    print("  - Output complete schema with mappings")
    
    # Example 2: Using the extractor programmatically
    print("\n2. Using FormSchemaExtractor Programmatically:")
    print("-" * 80)
    
    example_code = '''
    from form_schema_extractor import FormSchemaExtractor
    
    with FormSchemaExtractor(headless=True) as extractor:
        # Extract schema
        schema = extractor.extract_form_schema("https://example.com/application")
        
        # Print summary
        extractor.print_schema_summary(schema)
        
        # Save to JSON
        extractor.extract_to_json("https://example.com/application", "schema.json")
    '''
    
    print(example_code)
    
    # Example 3: Field mapping examples
    print("\n3. Field Mapping Examples:")
    print("-" * 80)
    print("The extractor maps fields using multiple sources:")
    print("  1. Label text (highest priority)")
    print("  2. Placeholder text")
    print("  3. aria-label attribute")
    print("  4. name attribute")
    print("  5. id attribute")
    print("\nExample mappings:")
    print("  'Email Address' -> email (exact match)")
    print("  'Phone Number' -> phone_number (exact match)")
    print("  'Full Name' -> full_name (exact match)")
    print("  'Internal Use Only' -> ignored (blacklisted)")
    print("  'Job Titl' -> experience.title (fuzzy match)")
    
    # Example 4: Schema structure
    print("\n4. Schema Structure:")
    print("-" * 80)
    example_schema = {
        "url": "https://example.com/application",
        "title": "Job Application Form",
        "schema_version": "1.0.0",
        "forms": [
            {
                "index": 0,
                "id": "application-form",
                "name": "application-form",
                "action": "/submit",
                "method": "post"
            }
        ],
        "fields": [
            {
                "selector": "#email",
                "field_type": "input",
                "input_type": "email",
                "label_text": "Email Address",
                "placeholder_text": "Enter your email",
                "aria_label": None,
                "name_attribute": "email",
                "id_attribute": "email",
                "required": True,
                "disabled": False,
                "readonly": False,
                "hidden": False,
                "suggested_canonical_field": "email",
                "mapping_confidence": 1.0,
                "mapping_match_type": "exact",
                "normalized_field_name": "email address",
                "field_index": 0,
                "form_index": 0
            }
        ],
        "total_fields": 1,
        "mapped_fields": 1,
        "ignored_fields": 0,
        "unmapped_fields": 0
    }
    
    print(json.dumps(example_schema, indent=2))
    
    # Example 5: Command-line usage
    print("\n5. Command-Line Usage:")
    print("-" * 80)
    print("python form_schema_extractor.py <url> [output_file.json]")
    print("\nExample:")
    print("  python form_schema_extractor.py https://example.com/application schema.json")
    print("\nThis will:")
    print("  - Extract form schema from the URL")
    print("  - Print a summary to console")
    print("  - Save full schema to schema.json")


if __name__ == '__main__':
    example_form_extraction()

