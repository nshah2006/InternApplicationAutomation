#!/usr/bin/env python3
"""
Example demonstrating explainability metadata in normalization output.
"""

import json
from resume_normalizer import normalize_resume, RoleProfile


def example_explainability():
    """Examples of explainability metadata."""
    
    print("=" * 60)
    print("NORMALIZATION EXPLAINABILITY")
    print("=" * 60)
    
    # Sample raw resume data
    raw_resume_data = {
        'name': 'john doe',
        'email': 'John.Doe@Example.COM',
        'phone': '123-456-7890',
        'education': [
            {
                'degree': 'BS in Computer Science',
                'institution': 'State Univ',
                'start_year': '2016',
                'end_year': '2020',
                'raw_date': '2016 - 2020'
            }
        ],
        'skills': ['python', 'js', 'react'],
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
                'description': 'A web application'
            }
        ]
    }
    
    # Example 1: Normalization without explainability (default)
    print("\n1. Normalization WITHOUT explainability (default, debug=False):")
    print("-" * 60)
    result = normalize_resume(raw_resume_data, debug=False)
    print(f"Keys in result: {list(result.keys())}")
    print(f"'explainability' key present: {'explainability' in result}")
    
    # Example 2: Normalization with explainability (debug=True)
    print("\n2. Normalization WITH explainability (debug=True):")
    print("-" * 60)
    result = normalize_resume(raw_resume_data, debug=True)
    print(f"Keys in result: {list(result.keys())}")
    print(f"'explainability' key present: {'explainability' in result}")
    
    # Example 3: Name explainability
    print("\n3. Name normalization explainability:")
    print("-" * 60)
    if 'explainability' in result:
        name_expl = result['explainability']['name']
        print(json.dumps(name_expl, indent=2))
    
    # Example 4: Email explainability
    print("\n4. Email normalization explainability:")
    print("-" * 60)
    if 'explainability' in result:
        email_expl = result['explainability']['email']
        print(json.dumps(email_expl, indent=2))
    
    # Example 5: Skills explainability
    print("\n5. Skills normalization explainability:")
    print("-" * 60)
    if 'explainability' in result:
        skills_expl = result['explainability']['skills']
        print(f"Source: {skills_expl['source']}")
        print(f"Transformation: {skills_expl['transformation']}")
        print(f"Rules applied: {skills_expl['rules_applied']}")
        print(f"Format: {skills_expl['format']}")
        print("\nIndividual skill transformations:")
        for skill_expl in skills_expl['skills']:
            print(f"  - '{skill_expl['value']}' -> '{skill_expl['transformed_value']}' "
                  f"(canonicalized: {skill_expl['canonicalized']}, "
                  f"confidence: {skill_expl.get('confidence', 'N/A')})")
    
    # Example 6: Education explainability
    print("\n6. Education normalization explainability:")
    print("-" * 60)
    if 'explainability' in result:
        edu_expl = result['explainability']['education']
        print(f"Transformation: {edu_expl['transformation']}")
        print(f"Rules applied: {edu_expl['rules_applied']}")
        print(f"Sorted: {edu_expl['sorted']}")
        print("\nEntry-level transformations:")
        for entry_expl in edu_expl['entries']:
            print(f"\n  Entry {entry_expl['index']}:")
            print(f"    Degree: '{entry_expl['degree']['value']}' -> "
                  f"'{entry_expl['degree']['transformed_value']}' "
                  f"(canonicalized: {entry_expl['degree']['canonicalized']})")
            print(f"    Institution: '{entry_expl['institution']['value']}' -> "
                  f"'{entry_expl['institution']['transformed_value']}'")
            print(f"    Years validated: start={entry_expl['years']['start_year']['validated']}, "
                  f"end={entry_expl['years']['end_year']['validated']}")
    
    # Example 7: Full explainability structure
    print("\n7. Full explainability structure (keys only):")
    print("-" * 60)
    if 'explainability' in result:
        print("Top-level explainability keys:")
        for key in result['explainability'].keys():
            print(f"  - {key}")


if __name__ == '__main__':
    example_explainability()

