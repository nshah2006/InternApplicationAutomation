# Normalization Versioning Strategy

## Overview

The resume normalization module uses semantic versioning to track changes to normalization rules. Each normalized output includes a `normalization_version` field indicating which version of the normalization rules were applied.

## Version Format

Versions follow the semantic versioning format: `MAJOR.MINOR.PATCH`

- **MAJOR**: Breaking changes to normalization output structure or behavior
- **MINOR**: New normalization rules, new role profiles, or significant rule changes
- **PATCH**: Bug fixes, minor rule adjustments, or documentation updates

## Current Version

The current normalization version is defined in `resume_normalizer.py`:

```python
NORMALIZATION_VERSION = "1.0.0"
```

## When to Increment Versions

### MAJOR Version (Breaking Changes)

Increment MAJOR version when:

1. **Output Structure Changes**
   - New required fields added to normalized output
   - Existing fields removed from normalized output
   - Field names changed
   - Field types changed in ways that break compatibility

2. **Behavior Changes**
   - Normalization logic changes that produce different results for the same input
   - Changes that break backward compatibility

3. **API Changes**
   - Changes to function signatures
   - Changes to exception types or error handling

**Example**: Changing `normalized` output structure from flat to nested format.

### MINOR Version (New Features)

Increment MINOR version when:

1. **New Normalization Rules**
   - New skill mappings added
   - New degree mappings added
   - New normalization patterns for names, emails, phones, etc.

2. **New Role Profiles**
   - New role profiles activated (not deprecated)
   - New skill prioritization rules for existing profiles

3. **Significant Rule Improvements**
   - Major improvements to existing normalization rules
   - New normalization strategies that enhance output quality

**Example**: Adding support for international phone number formats.

### PATCH Version (Bug Fixes)

Increment PATCH version when:

1. **Bug Fixes**
   - Fixes to normalization logic that produce incorrect results
   - Fixes to edge cases

2. **Minor Adjustments**
   - Small improvements to existing rules
   - Performance optimizations that don't change output

3. **Documentation**
   - Documentation updates
   - Code comments improvements

**Example**: Fixing a bug where certain phone number formats weren't normalized correctly.

## Version in Output

Every normalized output includes the `normalization_version` field:

```python
{
    'raw': {...},
    'normalized': {...},
    'normalization_version': '1.0.0',
    'normalization_enabled': True,
    'role_profile': 'software_engineer'
}
```

This allows consumers to:
- Track which version of normalization rules were applied
- Handle different versions appropriately
- Debug issues related to specific normalization versions
- Plan migrations when breaking changes occur

## Version History

### 1.0.0 (Initial Release)
- Initial normalization implementation
- Support for SOFTWARE_ENGINEER, DATA_SCIENTIST, and DEFAULT profiles
- Basic ATS-friendly formatting for all fields
- Skill prioritization for active role profiles

## Migration Guide

When upgrading to a new MAJOR version:

1. **Review Changelog**: Check what breaking changes were introduced
2. **Update Code**: Modify code that consumes normalized output to handle new structure
3. **Test Thoroughly**: Verify that your code works with the new version
4. **Update Version Checks**: If you check `normalization_version`, update your logic

## Best Practices

1. **Always Check Version**: When consuming normalized output, consider checking the version
2. **Document Dependencies**: Document which normalization version your code expects
3. **Test with Multiple Versions**: If possible, test with different normalization versions
4. **Report Issues**: Include normalization version when reporting bugs or issues

## Example Usage

```python
from resume_normalizer import normalize_resume, NORMALIZATION_VERSION

result = normalize_resume(raw_data)

# Check version
if result['normalization_version'] != NORMALIZATION_VERSION:
    print(f"Warning: Output version {result['normalization_version']} "
          f"differs from current version {NORMALIZATION_VERSION}")

# Use normalized data
normalized = result['normalized']
```

## Questions or Issues

If you have questions about versioning or need to report a version-related issue, please include:
- The normalization version you're using
- The normalization version in the output (if different)
- Description of the issue or question

