#!/usr/bin/env python3
"""
Example demonstrating skill normalization with confidence metadata.
"""

import json
from resume_normalizer import normalize_resume, RoleProfile


def example_skill_confidence():
    """Examples of skill normalization with confidence."""
    
    print("=" * 60)
    print("SKILL NORMALIZATION WITH CONFIDENCE")
    print("=" * 60)
    
    # Sample raw resume data
    raw_resume_data = {
        'name': 'John Doe',
        'email': 'john@example.com',
        'phone': '(123) 456-7890',
        'education': [],
        'skills': ['python', 'js', 'react', 'aws', 'docker'],
        'experience': [],
        'projects': []
    }
    
    # Example 1: New format with confidence (default)
    print("\n1. Skills as objects with confidence (default):")
    print("-" * 60)
    result = normalize_resume(raw_resume_data, skills_as_strings=False)
    print("Skills format:")
    for skill in result['normalized']['skills']:
        print(f"  - {skill['name']}: confidence={skill['confidence']}, source={skill['source']}")
    
    # Example 2: Backward compatibility - skills as strings
    print("\n2. Skills as strings (backward compatibility):")
    print("-" * 60)
    result = normalize_resume(raw_resume_data, skills_as_strings=True)
    print(f"Skills: {result['normalized']['skills']}")
    
    # Example 3: Skills from explicit section (higher confidence)
    print("\n3. Skills from explicit section (higher confidence):")
    print("-" * 60)
    raw_data_explicit = {
        **raw_resume_data,
        '_skills_metadata': {'from_explicit_section': True}
    }
    result = normalize_resume(raw_data_explicit, skills_as_strings=False)
    for skill in result['normalized']['skills']:
        print(f"  - {skill['name']}: confidence={skill['confidence']}, source={skill['source']}")
    
    # Example 4: Skills inferred from text (lower confidence)
    print("\n4. Skills inferred from text (lower confidence):")
    print("-" * 60)
    raw_data_inferred = {
        **raw_resume_data,
        '_skills_metadata': {'from_explicit_section': False}
    }
    result = normalize_resume(raw_data_inferred, skills_as_strings=False)
    for skill in result['normalized']['skills']:
        print(f"  - {skill['name']}: confidence={skill['confidence']}, source={skill['source']}")
    
    # Example 5: Confidence differences for mapped vs unmapped skills
    print("\n5. Confidence differences:")
    print("-" * 60)
    raw_data_mixed = {
        **raw_resume_data,
        'skills': ['python', 'js', 'some-unknown-skill', 'react'],
        '_skills_metadata': {'from_explicit_section': True}
    }
    result = normalize_resume(raw_data_mixed, skills_as_strings=False)
    print("Skills with confidence scores:")
    for skill in result['normalized']['skills']:
        print(f"  - {skill['name']}: confidence={skill['confidence']:.2f} "
              f"({'exact match' if skill['confidence'] >= 0.95 else 'partial match' if skill['confidence'] >= 0.8 else 'unmapped'})")
    
    # Example 6: Role-specific prioritization with confidence
    print("\n6. Role-specific prioritization (Software Engineer):")
    print("-" * 60)
    result = normalize_resume(
        raw_resume_data,
        role_profile=RoleProfile.SOFTWARE_ENGINEER,
        skills_as_strings=False
    )
    print("Skills sorted by priority and confidence:")
    for skill in result['normalized']['skills']:
        print(f"  - {skill['name']}: confidence={skill['confidence']}")


if __name__ == '__main__':
    example_skill_confidence()

