# Form Schema Extractor

A Playwright-based tool for extracting form schemas from web pages and automatically mapping fields to canonical resume schema using the ATS field mapper.

## Overview

The `form_schema_extractor` module provides a read-only form extraction tool that:
- Extracts all form fields from web pages using Playwright
- Captures multiple field name sources (labels, placeholders, aria-labels, etc.)
- Normalizes and maps fields to canonical schema using `ats_field_mapper`
- Outputs a complete form schema with suggested mappings
- **Does NOT autofill or submit forms** - purely read-only extraction

## Installation

1. Install Playwright:
```bash
pip install playwright>=1.40.0
playwright install chromium
```

2. The module requires `ats_field_mapper` which should already be in your project.

## Features

- **Multi-source Field Extraction**: Extracts field names from:
  - Label text (highest priority)
  - Placeholder text
  - aria-label attribute
  - name attribute
  - id attribute

- **Automatic Mapping**: Uses `ats_field_mapper` to suggest canonical field mappings
- **Blacklist Support**: Automatically ignores blacklisted fields (e.g., "Internal Use Only")
- **Form Detection**: Identifies all forms and standalone fields
- **Field Properties**: Captures required, disabled, readonly, hidden status
- **JSON Output**: Exports complete schema as JSON

## Usage

### Command Line

```bash
python form_schema_extractor.py <url> [output_file.json]
```

Example:
```bash
python form_schema_extractor.py https://example.com/job-application form_schema.json
```

### Programmatic Usage

```python
from form_schema_extractor import FormSchemaExtractor

# Using context manager (recommended)
with FormSchemaExtractor(headless=True) as extractor:
    # Extract schema
    schema = extractor.extract_form_schema("https://example.com/application")
    
    # Print summary
    extractor.print_schema_summary(schema)
    
    # Save to JSON
    extractor.extract_to_json("https://example.com/application", "schema.json")
```

### Convenience Function

```python
from form_schema_extractor import extract_form_schema

# Extract and save in one call
schema_dict = extract_form_schema(
    "https://example.com/application",
    headless=True,
    output_file="schema.json"
)
```

## Output Format

The extracted schema includes:

```json
{
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
      "aria_label": null,
      "name_attribute": "email",
      "id_attribute": "email",
      "required": true,
      "disabled": false,
      "readonly": false,
      "hidden": false,
      "suggested_canonical_field": "email",
      "mapping_confidence": 1.0,
      "mapping_match_type": "exact",
      "normalized_field_name": "email address",
      "field_index": 0,
      "form_index": 0
    }
  ],
  "total_fields": 10,
  "mapped_fields": 8,
  "ignored_fields": 1,
  "unmapped_fields": 1
}
```

## Field Mapping

Fields are mapped using the following priority:

1. **Label Text** - Text from associated `<label>` element
2. **Placeholder Text** - `placeholder` attribute
3. **aria-label** - `aria-label` attribute
4. **name Attribute** - `name` attribute
5. **id Attribute** - `id` attribute

The first non-empty value is used for mapping. The field name is then normalized and matched against the canonical schema using `ats_field_mapper`.

### Mapping Results

- **exact**: Exact match to canonical field
- **fuzzy**: Fuzzy match with confidence score
- **ignored**: Field matches blacklist pattern
- **none**: No match found

## Example Output

```
================================================================================
FORM SCHEMA EXTRACTION SUMMARY
================================================================================

URL: https://example.com/application
Title: Job Application Form
Schema Version: 1.0.0

Forms Found: 1
Total Fields: 10
  - Mapped: 8
  - Ignored: 1
  - Unmapped: 1

Forms:
  [0] application-form (id: application-form, method: post)

Fields:
  ✓ [form[0]] Email Address              -> email                          (exact, 100.0%)
  ✓ [form[0]] Phone Number               -> phone_number                   (exact, 100.0%)
  ~ [form[0]] Job Titl                   -> experience.title              (fuzzy, 94.1%)
  ✗ [form[0]] Internal Use Only          -> N/A                            (ignored)
  ? [form[0]] Custom Field               -> N/A                            (none)
```

## Limitations

- **Read-only**: Does not interact with forms (no filling, clicking, submitting)
- **Static Forms**: Works best with static HTML forms (may miss dynamically loaded forms)
- **JavaScript**: Requires JavaScript-enabled browser (Playwright handles this)
- **Authentication**: Does not handle authentication (you may need to login manually first)

## Use Cases

1. **Form Analysis**: Understand form structure before automation
2. **Mapping Discovery**: Discover which fields map to resume data
3. **Schema Documentation**: Generate documentation of form schemas
4. **Pre-automation Planning**: Plan form filling strategies

## Integration with ATS Field Mapper

The extractor uses `ats_field_mapper` for:
- Field name normalization
- Canonical field mapping
- Blacklist checking
- Confidence scoring

All mapping features from `ats_field_mapper` are available, including:
- Sensitivity-weighted confidence scoring
- Fuzzy matching
- Selection strategies (for list fields)
- Explainability (can be added to extraction)

## Troubleshooting

### Playwright Not Found
```bash
pip install playwright
playwright install chromium
```

### No Fields Found
- Check if the page loads correctly
- Verify forms are present in HTML (not dynamically loaded)
- Try increasing timeout: `FormSchemaExtractor(timeout=60000)`

### Fields Not Mapping
- Check if field names match known patterns
- Review blacklist patterns
- Use explainability to see why fields aren't matching

## Security Notes

- The extractor is read-only and does not submit data
- It only extracts visible form structure
- No sensitive data is stored or transmitted
- Use responsibly and in accordance with website terms of service

