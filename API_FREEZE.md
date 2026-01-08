# API Freeze Documentation

## Overview

The public API of `resume_normalizer` module is **FROZEN** as of version 1.1.0. This document defines what constitutes the public API and the policies governing its stability.

## Public API Definition

The following are considered part of the **stable public API**:

### 1. `normalize_resume()` Function

**Signature (FROZEN):**
```python
def normalize_resume(
    raw_resume_data: Dict[str, Any],
    role_profile: RoleProfile = RoleProfile.DEFAULT,
    normalize_enabled: bool = True,
    skills_as_strings: bool = False,
    debug: bool = False,
    **kwargs
) -> Dict[str, Any]
```

**Stable Elements:**
- Parameter names and order
- Parameter types and default values
- Return value structure (backward compatible additions allowed)
- Exception types (`ResumeValidationError`)
- Behavior semantics

### 2. `ResumeNormalizer` Class

**Public Methods (FROZEN):**

#### `__init__()`
```python
def __init__(
    self,
    role_profile: RoleProfile = RoleProfile.DEFAULT,
    normalize_enabled: bool = True,
    skills_as_strings: bool = False,
    debug: bool = False,
    **kwargs
)
```

#### `normalize()`
```python
def normalize(self, raw_resume_data: Dict[str, Any], **kwargs) -> Dict[str, Any]
```

**Stable Elements:**
- Method signatures
- Return value structures
- Public attribute access patterns
- Exception types

### 3. `RoleProfile` Enum

**Stable Elements:**
- Enum values (all values remain accessible)
- Enum value names and string representations

### 4. Exceptions

**Stable Elements:**
- `ResumeValidationError` exception class
- Exception message formats (may be enhanced but not changed)

## API Freeze Policies

### 1. Breaking Changes Policy

**Breaking changes are defined as:**
- Removing a parameter from a function/method signature
- Changing a parameter's type or required status
- Removing a return field
- Changing exception types for the same error condition
- Changing behavior in ways that break existing code

**Breaking changes will:**
- Only occur with a **MAJOR version bump** (e.g., 1.x.x → 2.0.0)
- Be clearly documented in CHANGELOG
- Include migration guides
- Provide deprecation warnings for at least one version cycle

### 2. Backward Compatible Changes

**The following changes are allowed without breaking the API:**

- **Adding new optional parameters** with default values
- **Adding new return fields** (existing fields remain unchanged)
- **Enhancing exception messages** (without changing exception types)
- **Improving internal implementation** (as long as behavior matches)
- **Adding new enum values** (existing values remain)

### 3. Deprecation Policy

**Deprecation process:**
1. Feature is marked as deprecated with clear warnings
2. Deprecated feature remains functional for at least one MAJOR version cycle
3. Migration path is documented
4. Feature is removed only in a MAJOR version bump

### 4. Unexpected Parameter Warnings

**Runtime safeguards:**
- Passing unexpected keyword arguments triggers `UserWarning`
- Warnings help catch typos and API misuse early
- Warnings do not prevent execution (parameters are ignored)
- Warnings include guidance on correct usage

## Usage Examples

### Correct Usage

```python
from resume_normalizer import normalize_resume, RoleProfile

# All parameters are valid
result = normalize_resume(
    raw_data,
    role_profile=RoleProfile.SOFTWARE_ENGINEER,
    normalize_enabled=True,
    skills_as_strings=False,
    debug=False
)
```

### Incorrect Usage (Triggers Warnings)

```python
# Typo in parameter name
result = normalize_resume(raw_data, role_profiles=RoleProfile.DEFAULT)  # Warning!

# Unknown parameter
result = normalize_resume(raw_data, verbose=True)  # Warning!

# Using ResumeNormalizer incorrectly
normalizer = ResumeNormalizer(role_profile=RoleProfile.DEFAULT, verbose=True)  # Warning!
```

## Version Compatibility

### Current Version: 1.1.0

**API Status:** FROZEN

**What's Stable:**
- Function signatures
- Return structures
- Exception types
- Enum values

**What May Change (Backward Compatible):**
- New optional parameters
- New return fields
- Enhanced error messages
- Internal optimizations

## Migration Guide

When upgrading between versions:

1. **PATCH versions (1.1.0 → 1.1.1):**
   - No API changes expected
   - Bug fixes and minor improvements only

2. **MINOR versions (1.1.0 → 1.2.0):**
   - New features may be added
   - New optional parameters may be added
   - New return fields may be added
   - Existing code continues to work

3. **MAJOR versions (1.x.x → 2.0.0):**
   - Breaking changes possible
   - Review CHANGELOG for details
   - Follow migration guide
   - Update code as needed

## Reporting API Issues

If you encounter:
- Unexpected warnings about parameters
- Behavior that seems to violate API stability
- Questions about API compatibility

Please report with:
- Version number
- Code example
- Expected vs actual behavior
- Warning messages (if any)

## Internal API

**Not part of public API (may change without notice):**
- Private methods (prefixed with `_`)
- Internal helper functions
- Implementation details
- Non-documented features

## Best Practices

1. **Use only documented public API**
2. **Handle warnings** - Fix typos and remove deprecated usage
3. **Pin versions** in production for stability
4. **Test upgrades** in development before production
5. **Read CHANGELOG** when upgrading versions

