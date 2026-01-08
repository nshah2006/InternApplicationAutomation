#!/usr/bin/env python3
"""
Example demonstrating explainability in ATS field mappings.
"""

import json
from ats_field_mapper import (
    map_ats_field,
    map_multiple_fields,
    SelectionStrategy,
    CANONICAL_SCHEMA_VERSION
)


def example_ats_explainability():
    """Examples of explainability in ATS field mapping."""
    
    print("=" * 70)
    print("ATS FIELD MAPPING EXPLAINABILITY")
    print("=" * 70)
    print(f"\nCanonical Schema Version: {CANONICAL_SCHEMA_VERSION}")
    print("=" * 70)
    
    # Sample resume data
    resume_data = {
        'name': 'John Doe',
        'email': 'john.doe@example.com',
        'phone': '(123) 456-7890',
        'education': [
            {
                'degree': 'Bachelor of Science',
                'institution': 'State University',
                'start_year': '2016',
                'end_year': '2020'
            },
            {
                'degree': 'Master of Science',
                'institution': 'Tech University',
                'start_year': '2020',
                'end_year': '2022'
            },
            {
                'degree': 'PhD',
                'institution': 'Research University',
                'start_year': '2022',
                'end_year': None  # Current
            }
        ],
        'experience': [
            {
                'title': 'Junior Developer',
                'company': 'Company A',
                'start_year': '2020',
                'end_year': '2022'
            },
            {
                'title': 'Senior Developer',
                'company': 'Company B',
                'start_year': '2022',
                'end_year': None  # Current
            }
        ],
        'skills': ['Python', 'Java', 'JavaScript']
    }
    
    # Example 1: Exact match with explainability
    print("\n1. Exact Match - Email Field:")
    print("-" * 70)
    result = map_ats_field('email', resume_data, explain=True)
    if result and 'explainability' in result:
        exp = result['explainability']
        print(f"ATS Field: '{result['ats_field_name']}'")
        print(f"Canonical Field: {result['canonical_field']}")
        print(f"Value: {result['value']}")
        print(f"Schema Version: {result['canonical_schema_version']}")
        print(f"\nExplainability:")
        print(f"  Summary: {exp['human_readable_summary']}")
        print(f"  Match Method: {exp['field_matching']['method']}")
        print(f"  Confidence: {result['confidence']:.1%}")
        print(f"  Sensitivity Category: {exp['confidence_calculation']['sensitivity_category']}")
    
    # Example 2: Fuzzy match with normalization steps
    print("\n2. Fuzzy Match - Field Name Normalization:")
    print("-" * 70)
    result = map_ats_field('E-Mail Address (Required)', resume_data, explain=True)
    if result and 'explainability' in result:
        exp = result['explainability']
        print(f"ATS Field: '{result['ats_field_name']}'")
        print(f"Normalized: '{exp['field_name_normalization']['normalized']}'")
        print(f"\nNormalization Steps:")
        for i, step in enumerate(exp['field_name_normalization']['steps'], 1):
            print(f"  {i}. {step['step']}: {step['description']}")
            print(f"     Before: '{step['before']}'")
            print(f"     After:  '{step['after']}'")
        print(f"\nMatching:")
        print(f"  Method: {exp['field_matching']['method']}")
        print(f"  Matched Field: {exp['field_matching']['matched_field']}")
        print(f"  Similarity Score: {exp['field_matching']['similarity_score']:.3f}")
        print(f"  Reasoning: {exp['field_matching']['reasoning']}")
    
    # Example 3: Fuzzy match with alternatives
    print("\n3. Fuzzy Match - Alternatives Considered:")
    print("-" * 70)
    result = map_ats_field('Job Titl', resume_data, explain=True)
    if result and 'explainability' in result:
        exp = result['explainability']
        print(f"ATS Field: '{result['ats_field_name']}'")
        print(f"Canonical Field: {result['canonical_field']}")
        print(f"\nTop Alternatives Considered:")
        for alt in exp['field_matching']['alternatives_considered'][:5]:
            print(f"  - '{alt['field']}' -> {alt['canonical']} "
                  f"(similarity: {alt['similarity']:.3f}, "
                  f"partial: {alt['partial_match']})")
    
    # Example 4: Confidence calculation explainability
    print("\n4. Confidence Calculation - Sensitivity Weighting:")
    print("-" * 70)
    test_fields = [
        ('email', 'CRITICAL'),
        ('E-Mail Addres', 'CRITICAL - typo'),
        ('skills', 'STANDARD')
    ]
    
    for field_name, description in test_fields:
        result = map_ats_field(field_name, resume_data, explain=True, fuzzy_threshold=0.7)
        if result and 'explainability' in result:
            exp = result['explainability']
            calc = exp['confidence_calculation']
            print(f"\nField: '{field_name}' ({description})")
            print(f"  Raw Score: {calc['raw_score']:.3f}")
            print(f"  Sensitivity Weight: {calc['sensitivity_weight']:.2f} ({calc['sensitivity_category']})")
            print(f"  Weighted Confidence: {calc['weighted_confidence']:.3f}")
            print(f"  Threshold: {calc['threshold']}")
            print(f"  Passed: {calc['passed_threshold']}")
            print(f"  Reasoning: {calc['reasoning']}")
    
    # Example 5: Selection strategy explainability
    print("\n5. Selection Strategy Explainability:")
    print("-" * 70)
    strategies = [
        ('MOST_RECENT', SelectionStrategy.MOST_RECENT),
        ('LONGEST', SelectionStrategy.LONGEST),
        ('HIGHEST_DEGREE', SelectionStrategy.HIGHEST_DEGREE)
    ]
    
    for strategy_name, strategy in strategies:
        result = map_ats_field(
            'education.degree',
            resume_data,
            selection_strategy=strategy,
            explain=True
        )
        if result and 'explainability' in result:
            exp = result['explainability']
            sel = exp['selection']
            print(f"\nStrategy: {strategy_name}")
            print(f"  Selected: {result['value']} (index: {sel['selected_index']})")
            print(f"  Reasoning: {sel['reasoning']}")
            print(f"  Total Entries: {sel['total_entries']}")
    
    # Example 6: Experience selection
    print("\n6. Experience Selection (Most Recent):")
    print("-" * 70)
    result = map_ats_field(
        'experience.title',
        resume_data,
        selection_strategy=SelectionStrategy.MOST_RECENT,
        explain=True
    )
    if result and 'explainability' in result:
        exp = result['explainability']
        sel = exp['selection']
        print(f"Selected: {result['value']}")
        print(f"Reasoning: {sel['reasoning']}")
        print(f"Summary: {exp['human_readable_summary']}")
    
    # Example 7: Full explainability JSON output
    print("\n7. Complete Explainability Structure:")
    print("-" * 70)
    result = map_ats_field('Phone Number', resume_data, explain=True)
    if result and 'explainability' in result:
        print(json.dumps(result['explainability'], indent=2, default=str))
    
    # Example 8: Multiple fields with explainability
    print("\n8. Multiple Fields Mapping with Explainability:")
    print("-" * 70)
    fields = ['Full Name', 'Email Address', 'Phone']
    results = map_multiple_fields(fields, resume_data, explain=True)
    
    for field_name, mapping in results.items():
        if 'explainability' in mapping:
            exp = mapping['explainability']
            print(f"\n{field_name}:")
            print(f"  Value: {mapping['value']}")
            print(f"  Summary: {exp['human_readable_summary']}")
            print(f"  Match: {exp['field_matching']['method']}")
            print(f"  Confidence: {mapping['confidence']:.1%}")


if __name__ == '__main__':
    example_ats_explainability()

