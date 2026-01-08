#!/usr/bin/env python3
"""
Example demonstrating ATS field mapping to resume schema paths.
"""

from ats_field_mapper import (
    map_ats_field,
    map_multiple_fields,
    CanonicalField,
    SelectionStrategy,
    get_canonical_fields,
    get_ats_field_variations,
    fuzzy_match_field,
    FIELD_SENSITIVITY_WEIGHTS
)
from resume_normalizer import normalize_resume


def example_ats_mapping():
    """Examples of ATS field mapping."""
    
    print("=" * 60)
    print("ATS FIELD MAPPING EXAMPLES")
    print("=" * 60)
    
    # Sample normalized resume data
    resume_data = {
        'name': 'John Doe',
        'email': 'john.doe@example.com',
        'phone': '(123) 456-7890',
        'education': [
            {
                'degree': 'Bachelor of Science in Computer Science',
                'institution': 'State University',
                'start_year': '2016',
                'end_year': '2020',
                'raw_date': '2016 - 2020'
            }
        ],
        'skills': ['Python', 'Java', 'JavaScript'],
        'experience': [
            {
                'title': 'Software Engineer',
                'company': 'Tech Corp',
                'start_year': '2020',
                'end_year': None,
                'raw_date': '2020 - Present'
            }
        ],
        'projects': [
            {
                'name': 'Web Application',
                'description': 'A full-stack web application'
            }
        ]
    }
    
    # Example 1: Exact match
    print("\n1. Exact field name matching:")
    print("-" * 60)
    result = map_ats_field('email', resume_data)
    if result:
        print(f"ATS Field: '{result['ats_field_name']}'")
        print(f"Canonical Field: {result['canonical_field']}")
        print(f"Schema Path: {result['schema_path']}")
        print(f"Value: {result['value']}")
        print(f"Match Type: {result['match_type']}")
        print(f"Confidence: {result['confidence']}")
    
    # Example 2: Fuzzy matching
    print("\n2. Fuzzy field name matching:")
    print("-" * 60)
    test_fields = [
        'E-Mail Address',  # Variation with special chars
        'Phone Number',    # Exact match
        'First Name',      # Exact match
        'Job Titl',        # Typo - fuzzy match
        'Compani Name',    # Typo - fuzzy match
    ]
    
    for field in test_fields:
        result = map_ats_field(field, resume_data)
        if result:
            print(f"  '{field}' -> {result['canonical_field']} "
                  f"({result['match_type']}, confidence: {result['confidence']:.2f})")
        else:
            print(f"  '{field}' -> No match found")
    
    # Example 3: Mapping multiple fields
    print("\n3. Mapping multiple ATS fields:")
    print("-" * 60)
    ats_fields = [
        'Full Name',
        'Email Address',
        'Phone',
        'Highest Degree',
        'University',
        'Graduation Year',
        'Current Job Title',
        'Company',
        'Skills'
    ]
    
    mappings = map_multiple_fields(ats_fields, resume_data)
    for ats_field, mapping in mappings.items():
        print(f"  {ats_field:20} -> {mapping['canonical_field']:25} "
              f"= {str(mapping['value'])[:30]}")
    
    # Example 4: Education field mapping with selection strategies
    print("\n4. Education field mapping (with selection strategies):")
    print("-" * 60)
    edu_fields = [
        'Degree',
        'School Name',
        'Education Start Date',
        'Graduation Date'
    ]
    
    # Use most_recent strategy (default)
    for field in edu_fields:
        result = map_ats_field(field, resume_data, SelectionStrategy.MOST_RECENT)
        if result:
            print(f"  {field:25} -> {result['schema_path']:30} = {result['value']}")
            print(f"    (strategy: {result['selection_strategy']}, index: {result['selected_index']})")
    
    # Example 5: Experience field mapping with different strategies
    print("\n5. Experience field mapping (comparing strategies):")
    print("-" * 60)
    exp_field = 'Job Title'
    
    strategies = [
        ('MOST_RECENT', SelectionStrategy.MOST_RECENT),
        ('LONGEST', SelectionStrategy.LONGEST)
    ]
    
    for strategy_name, strategy in strategies:
        result = map_ats_field(exp_field, resume_data, strategy)
        if result:
            print(f"  {strategy_name:15}: {result['value']:30} (index: {result['selected_index']})")
    
    # Example 5b: Education with highest_degree strategy
    print("\n5b. Education degree selection (highest_degree strategy):")
    print("-" * 60)
    result = map_ats_field('Degree', resume_data, SelectionStrategy.HIGHEST_DEGREE)
    if result:
        print(f"  Selected: {result['value']} (index: {result['selected_index']})")
        print(f"  Strategy: {result['selection_strategy']}")
    
    # Example 6: Canonical field namespace
    print("\n6. Canonical field namespace:")
    print("-" * 60)
    print(f"Total canonical fields: {len(get_canonical_fields())}")
    print("\nSample canonical fields:")
    for field in list(CanonicalField)[:10]:
        print(f"  - {field.value}")
    
    # Example 7: Field variations
    print("\n7. ATS field variations for 'email':")
    print("-" * 60)
    variations = get_ats_field_variations(CanonicalField.EMAIL)
    for variation in variations[:5]:
        print(f"  - '{variation}'")
    print(f"  ... and {len(variations) - 5} more")
    
    # Example 8: Confidence scoring with sensitivity weights
    print("\n8. Confidence scoring with sensitivity weights:")
    print("-" * 60)
    print("Sensitive fields require higher raw scores for acceptance.")
    print("\nTesting various field matches:")
    
    test_cases = [
        ('email', 'CRITICAL (weight=0.5)'),
        ('E-Mail Addres', 'CRITICAL - typo'),
        ('phone', 'CRITICAL (weight=0.5)'),
        ('Phone Numbr', 'CRITICAL - typo'),
        ('first name', 'HIGH (weight=0.7)'),
        ('First Nam', 'HIGH - typo'),
        ('skills', 'STANDARD (weight=1.0)'),
        ('Skils', 'STANDARD - typo'),
    ]
    
    for field_name, description in test_cases:
        result = map_ats_field(field_name, resume_data, fuzzy_threshold=0.7)
        if result:
            print(f"\n  Field: '{field_name}' ({description})")
            print(f"    Match Type: {result['match_type']}")
            print(f"    Raw Score: {result.get('raw_score', 'N/A'):.3f}")
            print(f"    Sensitivity Weight: {result.get('sensitivity_weight', 'N/A'):.2f}")
            print(f"    Weighted Confidence: {result['confidence']:.3f}")
            print(f"    Status: ACCEPTED (confidence >= threshold)")
        else:
            print(f"\n  Field: '{field_name}' ({description})")
            print(f"    Status: REJECTED (confidence below threshold)")
    
    # Example 9: Deterministic mapping (same input = same output)
    print("\n9. Deterministic mapping verification:")
    print("-" * 60)
    test_field = 'E-Mail Address'
    result1 = map_ats_field(test_field, resume_data)
    result2 = map_ats_field(test_field, resume_data)
    print(f"Field: '{test_field}'")
    print(f"First call:  {result1['canonical_field']} (confidence: {result1['confidence']:.2f})")
    print(f"Second call: {result2['canonical_field']} (confidence: {result2['confidence']:.2f})")
    print(f"Deterministic: {result1['canonical_field'] == result2['canonical_field']}")
    
    # Example 10: Sensitivity weights overview
    print("\n10. Field sensitivity weights:")
    print("-" * 60)
    print("CRITICAL (0.5): Email, Phone")
    print("HIGH (0.7): Name fields, Work Authorization")
    print("MEDIUM (0.85): Education/Experience dates, GPA")
    print("STANDARD (1.0): Skills, Descriptions, URLs")
    print(f"\nTotal fields with weights: {len(FIELD_SENSITIVITY_WEIGHTS)}")


if __name__ == '__main__':
    example_ats_mapping()

