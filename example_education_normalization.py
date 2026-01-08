#!/usr/bin/env python3
"""
Example demonstrating hardened education normalization.
"""

import json
from resume_normalizer import normalize_resume, RoleProfile


def example_education_normalization():
    """Examples of education normalization with canonicalization and validation."""
    
    print("=" * 60)
    print("EDUCATION NORMALIZATION WITH CANONICALIZATION")
    print("=" * 60)
    
    # Sample raw resume data with various degree formats
    raw_resume_data = {
        'name': 'John Doe',
        'email': 'john@example.com',
        'phone': '(123) 456-7890',
        'education': [
            {
                'degree': 'BS in Computer Science',
                'institution': 'State Univ',
                'start_year': '2016',
                'end_year': '2020',
                'raw_date': '2016 - 2020'
            },
            {
                'degree': 'Master of Science',
                'institution': 'Tech University',
                'start_year': '2020',
                'end_year': '2022',
                'raw_date': '2020 - 2022'
            },
            {
                'degree': 'B.A.',
                'institution': 'Community College',
                'start_year': '2014',
                'end_year': '2016',
                'raw_date': '2014 - 2016'
            }
        ],
        'skills': [],
        'experience': [],
        'projects': []
    }
    
    # Example 1: Canonicalization and raw preservation
    print("\n1. Degree canonicalization with raw preservation:")
    print("-" * 60)
    result = normalize_resume(raw_resume_data)
    for edu in result['normalized']['education']:
        print(f"  Raw: {edu.get('degree_raw')}")
        print(f"  Canonical: {edu.get('degree')}")
        print(f"  Institution: {edu.get('institution')}")
        print(f"  Years: {edu.get('start_year')} - {edu.get('end_year')}")
        print()
    
    # Example 2: Year validation
    print("\n2. Year validation (invalid years filtered out):")
    print("-" * 60)
    raw_data_invalid_years = {
        **raw_resume_data,
        'education': [
            {
                'degree': 'BS',
                'institution': 'University',
                'start_year': '2016',
                'end_year': '2020',  # Valid
            },
            {
                'degree': 'MS',
                'institution': 'University',
                'start_year': '20',  # Invalid - too short
                'end_year': '2022',  # Valid
            },
            {
                'degree': 'PhD',
                'institution': 'University',
                'start_year': '2020',
                'end_year': '1850',  # Invalid - out of range
            },
            {
                'degree': 'BA',
                'institution': 'University',
                'start_year': '2014',
                'end_year': '2200',  # Invalid - out of range
            }
        ]
    }
    result = normalize_resume(raw_data_invalid_years)
    for edu in result['normalized']['education']:
        print(f"  Degree: {edu.get('degree')}")
        print(f"  Start Year: {edu.get('start_year')} (validated)")
        print(f"  End Year: {edu.get('end_year')} (validated)")
        print()
    
    # Example 3: Sorting by end_year descending
    print("\n3. Sorting by end_year descending (most recent first):")
    print("-" * 60)
    raw_data_mixed_order = {
        **raw_resume_data,
        'education': [
            {
                'degree': 'BS',
                'institution': 'University A',
                'start_year': '2010',
                'end_year': '2014',
            },
            {
                'degree': 'MS',
                'institution': 'University B',
                'start_year': '2018',
                'end_year': '2020',
            },
            {
                'degree': 'PhD',
                'institution': 'University C',
                'start_year': '2020',
                'end_year': '2024',
            }
        ]
    }
    result = normalize_resume(raw_data_mixed_order)
    print("Education entries sorted by end_year (descending):")
    for i, edu in enumerate(result['normalized']['education'], 1):
        print(f"  {i}. {edu.get('degree')} - {edu.get('end_year')} ({edu.get('institution')})")
    
    # Example 4: Various degree format canonicalization
    print("\n4. Degree format canonicalization examples:")
    print("-" * 60)
    test_degrees = [
        'BS',
        'B.S.',
        'Bachelor of Science',
        'BS in Computer Science',
        'M.S.',
        'Master of Science',
        'MBA',
        'M.B.A.',
        'PhD',
        'Ph.D.',
        'Doctor of Philosophy',
        'BA',
        'B.A.',
        'Bachelor of Arts'
    ]
    
    from resume_normalizer import ResumeNormalizer
    normalizer = ResumeNormalizer()
    
    for test_degree in test_degrees:
        result = normalizer._normalize_degree(test_degree)
        if result:
            print(f"  '{test_degree}' -> '{result['canonical']}' (raw: '{result['raw']}')")


if __name__ == '__main__':
    example_education_normalization()

