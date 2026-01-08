#!/usr/bin/env python3
"""
Example demonstrating strict schema validation in resume_normalizer.
"""

from resume_normalizer import normalize_resume, ResumeValidationError, RoleProfile


def test_validation_examples():
    """Examples of validation errors."""
    
    print("=" * 60)
    print("RESUME VALIDATION EXAMPLES")
    print("=" * 60)
    
    # Example 1: Valid data
    print("\n1. Valid resume data:")
    print("-" * 60)
    valid_data = {
        'name': 'John Doe',
        'email': 'john@example.com',
        'phone': '(123) 456-7890',
        'education': [
            {'degree': 'BS Computer Science', 'institution': 'University', 'year': '2020'}
        ],
        'skills': ['Python', 'Java'],
        'experience': [
            {'title': 'Software Engineer', 'company': 'Tech Corp', 'duration': '2020-2023'}
        ],
        'projects': [
            {'name': 'Project 1', 'description': 'A project'}
        ]
    }
    try:
        result = normalize_resume(valid_data)
        print("✓ Validation passed")
    except ResumeValidationError as e:
        print(f"✗ Validation failed: {e}")
    
    # Example 2: Missing required field
    print("\n2. Missing required field (skills):")
    print("-" * 60)
    invalid_data = {
        'name': 'John Doe',
        'email': 'john@example.com',
        'phone': '(123) 456-7890',
        'education': [],
        # Missing 'skills'
        'experience': [],
        'projects': []
    }
    try:
        result = normalize_resume(invalid_data)
        print("✗ Validation should have failed")
    except ResumeValidationError as e:
        print(f"✓ Validation correctly failed:\n{e}")
    
    # Example 3: Wrong type for skills (not a list)
    print("\n3. Wrong type for skills (string instead of list):")
    print("-" * 60)
    invalid_data = {
        'name': 'John Doe',
        'email': 'john@example.com',
        'phone': '(123) 456-7890',
        'education': [],
        'skills': 'Python, Java',  # Should be a list
        'experience': [],
        'projects': []
    }
    try:
        result = normalize_resume(invalid_data)
        print("✗ Validation should have failed")
    except ResumeValidationError as e:
        print(f"✓ Validation correctly failed:\n{e}")
    
    # Example 4: Wrong type in skills list
    print("\n4. Wrong type in skills list (number instead of string):")
    print("-" * 60)
    invalid_data = {
        'name': 'John Doe',
        'email': 'john@example.com',
        'phone': '(123) 456-7890',
        'education': [],
        'skills': ['Python', 123],  # Number instead of string
        'experience': [],
        'projects': []
    }
    try:
        result = normalize_resume(invalid_data)
        print("✗ Validation should have failed")
    except ResumeValidationError as e:
        print(f"✓ Validation correctly failed:\n{e}")
    
    # Example 5: Wrong type for education item
    print("\n5. Wrong type for education item (string instead of dict):")
    print("-" * 60)
    invalid_data = {
        'name': 'John Doe',
        'email': 'john@example.com',
        'phone': '(123) 456-7890',
        'education': ['BS Computer Science'],  # Should be list of dicts
        'skills': [],
        'experience': [],
        'projects': []
    }
    try:
        result = normalize_resume(invalid_data)
        print("✗ Validation should have failed")
    except ResumeValidationError as e:
        print(f"✓ Validation correctly failed:\n{e}")
    
    # Example 6: Wrong type in education item field
    print("\n6. Wrong type in education item field (number instead of string):")
    print("-" * 60)
    invalid_data = {
        'name': 'John Doe',
        'email': 'john@example.com',
        'phone': '(123) 456-7890',
        'education': [
            {'degree': 'BS Computer Science', 'institution': 'University', 'year': 2020}  # int instead of str
        ],
        'skills': [],
        'experience': [],
        'projects': []
    }
    try:
        result = normalize_resume(invalid_data)
        print("✗ Validation should have failed")
    except ResumeValidationError as e:
        print(f"✓ Validation correctly failed:\n{e}")
    
    # Example 7: Not a dictionary
    print("\n7. Input is not a dictionary:")
    print("-" * 60)
    try:
        result = normalize_resume("not a dict")  # type: ignore
        print("✗ Validation should have failed")
    except ResumeValidationError as e:
        print(f"✓ Validation correctly failed:\n{e}")


if __name__ == '__main__':
    test_validation_examples()

