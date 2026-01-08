#!/usr/bin/env python3
"""
Example usage of the resume normalization module.
"""

import json
from resume_normalizer import normalize_resume, RoleProfile, ResumeNormalizer


def example_usage():
    """Example demonstrating resume normalization."""
    
    # Sample raw resume data (as would come from resume_parser)
    raw_resume_data = {
        'name': 'john doe',
        'email': 'John.Doe@Example.COM',
        'phone': '123-456-7890',
        'education': [
            {
                'degree': 'BS in Computer Science',
                'institution': 'State Univ',
                'year': '2020',
                'start_year': '2016',
                'end_year': '2020',
                'raw_date': '2016 - 2020'
            }
        ],
        'skills': ['python', 'js', 'react', 'node', 'aws', 'docker'],
        'experience': [
            {
                'title': 'software engineer',
                'company': 'tech corp inc',
                'duration': '2020 - Present',
                'start_year': '2020',
                'end_year': None,
                'raw_date': '2020 - Present'
            }
        ],
        'projects': [
            {
                'name': 'web app',
                'description': 'A web application built with react and node.js'
            }
        ]
    }
    
    print("=" * 60)
    print("RESUME NORMALIZATION EXAMPLE")
    print("=" * 60)
    
    # Example 1: Normalize with default profile
    print("\n1. Normalization with DEFAULT profile:")
    print("-" * 60)
    result_default = normalize_resume(raw_resume_data, normalize_enabled=True)
    print(json.dumps(result_default['normalized'], indent=2))
    
    # Example 2: Normalize with Software Engineer profile
    print("\n2. Normalization with SOFTWARE_ENGINEER profile:")
    print("-" * 60)
    result_se = normalize_resume(
        raw_resume_data,
        role_profile=RoleProfile.SOFTWARE_ENGINEER,
        normalize_enabled=True
    )
    print(json.dumps(result_se['normalized'], indent=2))
    
    # Example 3: Normalization disabled (returns raw data)
    print("\n3. Normalization DISABLED:")
    print("-" * 60)
    result_disabled = normalize_resume(raw_resume_data, normalize_enabled=False)
    print(f"Normalization enabled: {result_disabled['normalization_enabled']}")
    print(f"Raw data preserved: {result_disabled['raw'] == raw_resume_data}")
    
    # Example 4: Using ResumeNormalizer class directly
    print("\n4. Using ResumeNormalizer class directly:")
    print("-" * 60)
    normalizer = ResumeNormalizer(
        role_profile=RoleProfile.DATA_SCIENTIST,
        normalize_enabled=True
    )
    result_ds = normalizer.normalize(raw_resume_data)
    print(f"Role profile: {result_ds['role_profile']}")
    print(f"Skills (prioritized for Data Scientist):")
    for skill in result_ds['normalized']['skills']:
        print(f"  - {skill}")
    
    # Example 5: Accessing both raw and normalized data
    print("\n5. Accessing both raw and normalized data:")
    print("-" * 60)
    result = normalize_resume(raw_resume_data)
    print(f"Raw name: {result['raw']['name']}")
    print(f"Normalized name: {result['normalized']['name']}")
    print(f"Raw email: {result['raw']['email']}")
    print(f"Normalized email: {result['normalized']['email']}")
    print(f"Raw phone: {result['raw']['phone']}")
    print(f"Normalized phone: {result['normalized']['phone']}")


if __name__ == '__main__':
    example_usage()

