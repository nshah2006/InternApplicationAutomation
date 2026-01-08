#!/usr/bin/env python3
"""
Example demonstrating negative match rules (blacklist) in ATS field mapping.
"""

from ats_field_mapper import (
    map_ats_field,
    map_multiple_fields,
    is_field_blacklisted,
    FIELD_BLACKLIST_PATTERNS
)


def example_ats_blacklist():
    """Examples of blacklist functionality."""
    
    print("=" * 70)
    print("ATS FIELD MAPPER - NEGATIVE MATCH RULES (BLACKLIST)")
    print("=" * 70)
    
    resume_data = {
        'name': 'John Doe',
        'email': 'john@example.com',
        'phone': '(123) 456-7890'
    }
    
    # Example 1: Blacklist detection
    print("\n1. Blacklist Pattern Detection:")
    print("-" * 70)
    test_fields = [
        'Internal Use Only',
        'HR Use Only',
        'Do Not Fill',
        'Reserved',
        'System Field',
        'Test Field',
        'Comment',
        'email',  # Should not be blacklisted
        'Phone Number'  # Should not be blacklisted
    ]
    
    for field in test_fields:
        is_blacklisted, pattern = is_field_blacklisted(field)
        status = '✓ BLACKLISTED' if is_blacklisted else '✓ OK'
        if is_blacklisted:
            print(f"   {field:30} -> {status:15} (pattern: {pattern})")
        else:
            print(f"   {field:30} -> {status}")
    
    # Example 2: Mapping blacklisted fields
    print("\n2. Mapping Blacklisted Fields:")
    print("-" * 70)
    blacklisted_fields = [
        'Internal Use Only',
        'Do Not Fill',
        'HR Use Only',
        'Reserved',
        'System Field'
    ]
    
    for field in blacklisted_fields:
        result = map_ats_field(field, resume_data)
        if result:
            print(f"\n   Field: '{field}'")
            print(f"   Match Type: {result['match_type']}")
            print(f"   Canonical Field: {result.get('canonical_field', 'None')}")
            print(f"   Value: {result.get('value', 'None')}")
            print(f"   Blacklist Reason: {result.get('blacklist_reason', 'N/A')}")
            print(f"   Schema Version: {result.get('canonical_schema_version', 'N/A')}")
    
    # Example 3: Blacklisted field with explainability
    print("\n3. Blacklisted Field with Explainability:")
    print("-" * 70)
    result = map_ats_field('Internal Use Only', resume_data, explain=True)
    if result and 'explainability' in result:
        exp = result['explainability']
        print(f"   Field: '{result['ats_field_name']}'")
        print(f"   Match Type: {result['match_type']}")
        print(f"   Summary: {exp['human_readable_summary']}")
        print(f"\n   Normalization Steps:")
        for step in exp['field_name_normalization']['steps']:
            print(f"     - {step['step']}: {step['description']}")
        print(f"\n   Matching:")
        print(f"     Method: {exp['field_matching']['method']}")
        print(f"     Reasoning: {exp['field_matching']['reasoning']}")
    
    # Example 4: Mixed fields (blacklisted and normal)
    print("\n4. Mixed Fields Mapping (Blacklisted + Normal):")
    print("-" * 70)
    mixed_fields = [
        'email',
        'Internal Use Only',
        'Phone Number',
        'Do Not Fill',
        'name',
        'HR Use Only'
    ]
    
    results = map_multiple_fields(mixed_fields, resume_data)
    
    print("\n   Results Summary:")
    for field in mixed_fields:
        if field in results:
            result = results[field]
            match_type = result.get('match_type', 'N/A')
            if match_type == 'ignored':
                print(f"     {field:25} -> IGNORED (blacklisted)")
            else:
                value = result.get('value', 'None')
                print(f"     {field:25} -> {match_type:10} = {str(value)[:30]}")
        else:
            print(f"     {field:25} -> NOT FOUND")
    
    # Example 5: Available blacklist patterns
    print("\n5. Available Blacklist Patterns:")
    print("-" * 70)
    print(f"   Total patterns: {len(FIELD_BLACKLIST_PATTERNS)}")
    print("\n   Pattern Categories:")
    
    categories = {
        'Internal/Reserved': [p for p in FIELD_BLACKLIST_PATTERNS if 'internal' in p or 'reserved' in p or 'do not' in p],
        'System Fields': [p for p in FIELD_BLACKLIST_PATTERNS if 'system' in p or 'generated' in p or 'hidden' in p],
        'Placeholder/Test': [p for p in FIELD_BLACKLIST_PATTERNS if 'placeholder' in p or 'test' in p or 'example' in p or 'demo' in p],
        'Disabled/Inactive': [p for p in FIELD_BLACKLIST_PATTERNS if 'disabled' in p or 'inactive' in p or 'deprecated' in p],
        'Comments/Notes': [p for p in FIELD_BLACKLIST_PATTERNS if 'comment' in p or 'note' in p or 'remark' in p]
    }
    
    for category, patterns in categories.items():
        if patterns:
            print(f"\n   {category}:")
            for pattern in patterns[:3]:  # Show first 3
                print(f"     - {pattern}")
            if len(patterns) > 3:
                print(f"     ... and {len(patterns) - 3} more")
    
    # Example 6: Normal fields still work
    print("\n6. Normal Fields (Should Still Work):")
    print("-" * 70)
    normal_fields = ['email', 'phone', 'name', 'Full Name', 'E-Mail Address']
    
    for field in normal_fields:
        result = map_ats_field(field, resume_data)
        if result and result.get('match_type') != 'ignored':
            print(f"   {field:20} -> {result['match_type']:10} = {str(result.get('value', 'None'))[:30]}")
        else:
            print(f"   {field:20} -> FAILED")


if __name__ == '__main__':
    example_ats_blacklist()

