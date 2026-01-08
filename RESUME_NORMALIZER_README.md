# Resume Normalization Module

The `resume_normalizer` module provides ATS-friendly normalization of resume data while preserving the original raw data.

## Features

- **Role-Specific Normalization**: Different normalization profiles for different job roles
- **ATS-Friendly Formatting**: Standardizes formats for better ATS parsing
- **Raw Data Preservation**: Keeps original data alongside normalized data
- **Toggleable Normalization**: Can be enabled or disabled
- **Skill Prioritization**: Role-specific skill ordering based on relevance

## Usage

### Basic Usage

```python
from resume_normalizer import normalize_resume, RoleProfile
from resume_parser import parse_resume

# Parse a resume
raw_data = parse_resume("resume.pdf")

# Normalize with default profile
result = normalize_resume(raw_data)
print(result['normalized'])  # ATS-friendly normalized data
print(result['raw'])        # Original raw data
```

### Role-Specific Normalization

```python
from resume_normalizer import normalize_resume, RoleProfile

# Normalize for Software Engineer role
result = normalize_resume(
    raw_data,
    role_profile=RoleProfile.SOFTWARE_ENGINEER,
    normalize_enabled=True
)

# Normalize for Data Scientist role
result = normalize_resume(
    raw_data,
    role_profile=RoleProfile.DATA_SCIENTIST,
    normalize_enabled=True
)
```

### Disable Normalization

```python
# Return raw data only (no normalization)
result = normalize_resume(raw_data, normalize_enabled=False)
# result['normalized'] == result['raw']
```

### Using the Class Directly

```python
from resume_normalizer import ResumeNormalizer, RoleProfile

normalizer = ResumeNormalizer(
    role_profile=RoleProfile.DEVOPS_ENGINEER,
    normalize_enabled=True
)

result = normalizer.normalize(raw_data)
```

## Available Role Profiles

- `SOFTWARE_ENGINEER`: General software engineering roles
- `DATA_SCIENTIST`: Data science and analytics roles
- `PRODUCT_MANAGER`: Product management roles
- `DEVOPS_ENGINEER`: DevOps and infrastructure roles
- `FRONTEND_DEVELOPER`: Frontend development roles
- `BACKEND_DEVELOPER`: Backend development roles
- `FULL_STACK_DEVELOPER`: Full-stack development roles
- `MACHINE_LEARNING_ENGINEER`: ML engineering roles
- `DEFAULT`: Generic normalization (no role-specific prioritization)

## Normalization Rules

### Name
- Converts to Title Case
- Handles special cases (Mc, O', etc.)

### Email
- Converts to lowercase
- Preserves original format

### Phone
- Normalizes to format: `(XXX) XXX-XXXX`
- Handles US numbers with country code

### Education
- Normalizes degree names to canonical forms
- Standardizes institution names
- Sorts by end year (most recent first)

### Skills
- Maps variations to canonical forms (e.g., "js" → "JavaScript")
- Role-specific prioritization (high/medium priority skills first)
- Deduplicates and sorts

### Experience
- Normalizes job titles to Title Case
- Standardizes company names
- Sorts by end year (most recent first)

### Projects
- Normalizes project names and descriptions
- Preserves original content

## Output Structure

```python
{
    'raw': {
        # Original raw resume data
        'name': 'john doe',
        'email': 'John.Doe@Example.COM',
        ...
    },
    'normalized': {
        # ATS-friendly normalized data
        'name': 'John Doe',
        'email': 'john.doe@example.com',
        ...
    },
    'normalization_enabled': True,
    'role_profile': 'software_engineer'
}
```

## Integration with Resume Parser

```python
from resume_parser import parse_resume
from resume_normalizer import normalize_resume, RoleProfile

# Parse resume
raw_resume = parse_resume("resume.pdf")

# Normalize for specific role
normalized_resume = normalize_resume(
    raw_resume,
    role_profile=RoleProfile.SOFTWARE_ENGINEER
)

# Save both versions
with open('resume_normalized.json', 'w') as f:
    json.dump(normalized_resume, f, indent=2)
```

## Examples

See `example_normalization.py` for complete usage examples.

