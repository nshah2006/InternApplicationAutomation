# ATS Field Mapper

Maps ATS (Applicant Tracking System) form field names to resume schema paths with fuzzy matching support.

## Overview

The `ats_field_mapper` module provides a deterministic mapping system that translates various ATS field name formats into canonical field names and resume schema paths. This enables automatic form filling by mapping form fields to resume data.

## Features

- **Canonical Field Namespace**: Standardized field names for consistent mapping
- **Fuzzy Matching**: Handles typos, variations, and different naming conventions
- **Deterministic Output**: Same input always produces same output
- **Schema Path Mapping**: Maps to actual resume data structure paths
- **Multiple Field Support**: Batch mapping of multiple fields

## Canonical Field Namespace

The module defines a canonical set of field names covering:

- **Personal Information**: name, email, phone, address, URLs
- **Education**: degree, institution, dates, major, GPA
- **Experience**: title, company, dates, description, current status
- **Skills**: technical skills and competencies
- **Projects**: project names and descriptions
- **Other**: resume file, cover letter, availability, salary, work authorization

## Usage

### Basic Field Mapping

```python
from ats_field_mapper import map_ats_field
from resume_parser import parse_resume

# Parse resume
resume_data = parse_resume("resume.pdf")

# Map ATS field to resume data
result = map_ats_field("Email Address", resume_data)

if result:
    print(f"Canonical Field: {result['canonical_field']}")
    print(f"Schema Path: {result['schema_path']}")
    print(f"Value: {result['value']}")
    print(f"Match Type: {result['match_type']}")  # 'exact' or 'fuzzy'
    print(f"Confidence: {result['confidence']}")
```

### Mapping Multiple Fields

```python
from ats_field_mapper import map_multiple_fields

ats_fields = [
    "Full Name",
    "Email",
    "Phone Number",
    "Highest Degree",
    "Current Job Title"
]

mappings = map_multiple_fields(ats_fields, resume_data)

for field_name, mapping in mappings.items():
    print(f"{field_name}: {mapping['value']}")
```

### Fuzzy Matching

```python
from ats_field_mapper import fuzzy_match_field, CanonicalField

# Handles typos and variations
result = fuzzy_match_field("E-Mail Addres", threshold=0.7)
# Returns CanonicalField.EMAIL

result = fuzzy_match_field("Phone Numbr", threshold=0.7)
# Returns CanonicalField.PHONE
```

### Education/Experience with Index

```python
# Map education fields (index 0 = first education entry)
result = map_ats_field("Degree", resume_data, index=0)
# Returns mapping to education[0].degree

# Map experience fields (index 1 = second experience entry)
result = map_ats_field("Job Title", resume_data, index=1)
# Returns mapping to experience[1].title
```

## Mapping Result Structure

```python
{
    'canonical_field': 'email',           # Canonical field name
    'schema_path': 'email',               # Path in resume data
    'value': 'john@example.com',          # Actual value
    'match_type': 'exact',                # 'exact' or 'fuzzy'
    'confidence': 1.0,                     # 0.0-1.0
    'ats_field_name': 'Email Address',    # Original ATS field name
    'normalized_field_name': 'email address'  # Normalized version
}
```

## Field Name Normalization

Field names are normalized by:
1. Converting to lowercase
2. Removing common prefixes/suffixes ("Required:", "Optional:", etc.)
3. Removing special characters
4. Normalizing whitespace

Examples:
- "Email Address (Required)" → "email address"
- "Phone #" → "phone"
- "First Name:" → "first name"

## Fuzzy Matching

Fuzzy matching uses sequence similarity (difflib.SequenceMatcher) with configurable threshold (default: 0.7).

- **Exact Match**: Confidence = 1.0
- **Fuzzy Match**: Confidence = similarity score (0.7-1.0)
- **No Match**: Returns None if below threshold

## Schema Path Mapping

Canonical fields map to resume schema paths:

- `email` → `resume_data['email']`
- `education.degree` → `resume_data['education'][index]['degree']`
- `experience.title` → `resume_data['experience'][index]['title']`
- `skills` → `resume_data['skills']`

## Supported ATS Field Variations

The module recognizes 100+ common ATS field name variations, including:

- **Name**: "First Name", "Last Name", "Full Name", "Name", "Given Name", etc.
- **Email**: "Email", "E-Mail", "Email Address", "Contact Email", etc.
- **Phone**: "Phone", "Phone Number", "Telephone", "Mobile", "Cell Phone", etc.
- **Education**: "Degree", "Highest Degree", "School", "University", "Graduation Date", etc.
- **Experience**: "Job Title", "Position", "Company", "Employer", "Start Date", etc.

## Deterministic Behavior

The mapping is deterministic:
- Same input always produces same output
- Normalization ensures consistent matching
- Fuzzy matching uses fixed threshold for consistency

## Examples

See `example_ats_mapping.py` for complete usage examples.

## Future Enhancements

- Browser automation integration for form filling
- Custom field mapping rules
- Field validation and type checking
- Multi-language support

