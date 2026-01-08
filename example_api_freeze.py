#!/usr/bin/env python3
"""
Example demonstrating API freeze safeguards and warnings.
"""

import warnings
from resume_normalizer import normalize_resume, ResumeNormalizer, RoleProfile


def example_api_freeze_warnings():
    """Examples of API freeze warnings."""
    
    print("=" * 60)
    print("API FREEZE SAFEGUARDS DEMONSTRATION")
    print("=" * 60)
    
    raw_resume_data = {
        'name': 'John Doe',
        'email': 'john@example.com',
        'phone': '(123) 456-7890',
        'education': [],
        'skills': ['Python'],
        'experience': [],
        'projects': []
    }
    
    # Example 1: Correct usage (no warnings)
    print("\n1. Correct usage (no warnings):")
    print("-" * 60)
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        result = normalize_resume(
            raw_resume_data,
            role_profile=RoleProfile.SOFTWARE_ENGINEER,
            normalize_enabled=True,
            skills_as_strings=False,
            debug=False
        )
        if w:
            print(f"Warnings issued: {len(w)}")
            for warning in w:
                print(f"  - {warning.message}")
        else:
            print("✓ No warnings - correct API usage")
    
    # Example 2: Unexpected parameter in normalize_resume
    print("\n2. Unexpected parameter in normalize_resume() (triggers warning):")
    print("-" * 60)
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        result = normalize_resume(
            raw_resume_data,
            role_profile=RoleProfile.DEFAULT,
            verbose=True  # Unexpected parameter
        )
        if w:
            print(f"✓ Warning issued as expected:")
            for warning in w:
                print(f"  {warning.category.__name__}: {warning.message}")
        else:
            print("✗ No warning issued (unexpected)")
    
    # Example 3: Typo in parameter name
    print("\n3. Typo in parameter name (triggers warning):")
    print("-" * 60)
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        result = normalize_resume(
            raw_resume_data,
            role_profiles=RoleProfile.DEFAULT  # Typo: should be role_profile
        )
        if w:
            print(f"✓ Warning issued as expected:")
            for warning in w:
                print(f"  {warning.category.__name__}: {warning.message}")
        else:
            print("✗ No warning issued (unexpected)")
    
    # Example 4: Unexpected parameter in ResumeNormalizer
    print("\n4. Unexpected parameter in ResumeNormalizer.__init__() (triggers warning):")
    print("-" * 60)
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        normalizer = ResumeNormalizer(
            role_profile=RoleProfile.DEFAULT,
            verbose=True  # Unexpected parameter
        )
        if w:
            print(f"✓ Warning issued as expected:")
            for warning in w:
                print(f"  {warning.category.__name__}: {warning.message}")
        else:
            print("✗ No warning issued (unexpected)")
    
    # Example 5: Unexpected parameter in normalize() method
    print("\n5. Unexpected parameter in normalize() method (triggers warning):")
    print("-" * 60)
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        normalizer = ResumeNormalizer()
        result = normalizer.normalize(raw_resume_data, verbose=True)  # Unexpected parameter
        if w:
            print(f"✓ Warning issued as expected:")
            for warning in w:
                print(f"  {warning.category.__name__}: {warning.message}")
        else:
            print("✗ No warning issued (unexpected)")
    
    # Example 6: Multiple unexpected parameters
    print("\n6. Multiple unexpected parameters (triggers multiple warnings):")
    print("-" * 60)
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        result = normalize_resume(
            raw_resume_data,
            verbose=True,
            output_format='json',  # Multiple unexpected parameters
            include_metadata=True
        )
        if w:
            print(f"✓ {len(w)} warning(s) issued as expected:")
            for warning in w:
                print(f"  {warning.category.__name__}: {warning.message}")
        else:
            print("✗ No warnings issued (unexpected)")


if __name__ == '__main__':
    example_api_freeze_warnings()

