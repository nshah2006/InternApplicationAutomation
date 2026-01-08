# Canonical Schema Versioning Strategy

## Overview

The ATS field mapper uses semantic versioning to track changes to the canonical field namespace, mapping rules, selection strategies, and output structure. Each mapping output includes a `canonical_schema_version` field indicating which version of the schema was used.

## Version Format

Versions follow the semantic versioning format: `MAJOR.MINOR.PATCH`

- **MAJOR**: Breaking changes to canonical field names, output structure, or behavior
- **MINOR**: New canonical fields added, new selection strategies, mapping rule changes
- **PATCH**: Bug fixes, minor adjustments, documentation updates

## Current Version

The current canonical schema version is defined in `ats_field_mapper.py`:

```python
CANONICAL_SCHEMA_VERSION = "1.0.0"
```

## When to Increment Versions

### MAJOR Version (Breaking Changes)

Increment MAJOR version when:

1. **Canonical Field Changes**
   - Canonical field names are removed or renamed
   - Field namespace structure changes (e.g., `education.degree` → `education.degree_name`)
   - Breaking changes to `CanonicalField` enum values

2. **Output Structure Changes**
   - New required fields added to mapping output
   - Existing fields removed from mapping output
   - Field names in output dictionary changed
   - Field types changed in ways that break compatibility

3. **Behavior Changes**
   - Selection strategy behavior changes that produce different results
   - Mapping logic changes that break backward compatibility
   - Confidence calculation formula changes

4. **API Changes**
   - Changes to function signatures that break existing code
   - Changes to exception types or error handling

**Example**: Renaming `CanonicalField.EMAIL` to `CanonicalField.EMAIL_ADDRESS` would be a MAJOR change.

### MINOR Version (New Features)

Increment MINOR version when:

1. **New Canonical Fields**
   - New fields added to `CanonicalField` enum
   - New field categories added (e.g., certifications, languages)

2. **New Selection Strategies**
   - New `SelectionStrategy` enum values added
   - New selection logic implemented

3. **Mapping Rule Changes**
   - New ATS field name variations added to `ATS_FIELD_MAPPINGS`
   - Fuzzy matching algorithm improvements
   - New normalization rules

4. **New Features**
   - New explainability features
   - New confidence calculation options
   - New utility functions

**Example**: Adding `CanonicalField.CERTIFICATIONS` or `SelectionStrategy.FIRST` would be a MINOR change.

### PATCH Version (Bug Fixes)

Increment PATCH version when:

1. **Bug Fixes**
   - Fixes to field matching logic
   - Fixes to selection strategy implementation
   - Fixes to normalization rules

2. **Minor Adjustments**
   - Sensitivity weight adjustments
   - Threshold tuning
   - Performance improvements

3. **Documentation**
   - Documentation updates
   - Code comments improvements
   - Example updates

**Example**: Fixing a bug where a specific field name wasn't matching correctly would be a PATCH change.

## Version History

### 1.0.0 (Initial Release)

- Initial canonical field namespace (35 fields)
- Basic field mapping (exact and fuzzy matching)
- Field name normalization
- Selection strategies: `most_recent`, `longest`, `highest_degree`
- Sensitivity-weighted confidence scoring
- Explainability support

## Upgrade Strategy

### Checking Schema Version

All mapping outputs include a `canonical_schema_version` field:

```python
result = map_ats_field('email', resume_data)
version = result['canonical_schema_version']  # e.g., "1.0.0"
```

### Version Compatibility

1. **Same MAJOR Version**: Fully compatible
   - Same canonical field names
   - Same output structure
   - Same behavior

2. **Different MAJOR Version**: Breaking changes
   - May have different canonical field names
   - May have different output structure
   - Requires code updates

3. **Different MINOR/PATCH Version**: Backward compatible
   - New fields may be added
   - Behavior improvements
   - Generally safe to upgrade

### Migration Guide

#### From 1.0.0 to 1.1.0 (Example MINOR upgrade)

If new fields are added:

```python
# Old code (1.0.0)
result = map_ats_field('email', resume_data)
email = result['value']

# New code (1.1.0) - still works, but can use new fields
result = map_ats_field('email', resume_data)
email = result['value']  # Still works
# Can also use new fields if available
```

#### From 1.0.0 to 2.0.0 (Example MAJOR upgrade)

If field names change:

```python
# Old code (1.0.0)
result = map_ats_field('email', resume_data)
email = result['value']

# New code (2.0.0) - requires updates
result = map_ats_field('email_address', resume_data)  # Field name changed
email = result['value']
```

### Best Practices

1. **Always Check Version**: Verify the schema version before processing results
   ```python
   result = map_ats_field('email', resume_data)
   if result['canonical_schema_version'].startswith('1.'):
       # Handle version 1.x
   elif result['canonical_schema_version'].startswith('2.'):
       # Handle version 2.x
   ```

2. **Version Pinning**: Pin to a specific MAJOR version in production
   ```python
   # Pin to version 1.x
   assert result['canonical_schema_version'].startswith('1.')
   ```

3. **Gradual Migration**: When upgrading MAJOR versions:
   - Test thoroughly with your data
   - Update field name references
   - Update selection strategy usage if changed
   - Verify output structure matches expectations

4. **Monitor Changes**: Review CHANGELOG or version history when upgrading

## Version Comparison

To compare versions programmatically:

```python
from packaging import version

current_version = result['canonical_schema_version']
if version.parse(current_version) >= version.parse('2.0.0'):
    # Use new API
else:
    # Use old API
```

## Testing

When making version changes:

1. **Update Tests**: Ensure all tests pass with new version
2. **Backward Compatibility**: Test that old code still works (for MINOR/PATCH)
3. **Migration Tests**: Create tests for migration scenarios (for MAJOR)
4. **Documentation**: Update this document with version history

## Questions?

For questions about versioning or upgrade strategies, refer to:
- `ats_field_mapper.py` for current version constant
- This document for version history and upgrade guides
- Code comments for version-specific behavior

