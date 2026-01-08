#!/usr/bin/env python3
"""
Resume Normalization Module - Maps raw resume data to canonical ATS-friendly representations.

This module provides role-specific normalization of resume data to ATS-friendly formats
while preserving raw data and supporting explainability.

PUBLIC API (FROZEN):
====================
The following public API is FROZEN as of version 1.1.0 and guaranteed stable:

Public Functions:
----------------
1. normalize_resume(
       raw_resume_data: Dict[str, Any],
       role_profile: RoleProfile = RoleProfile.DEFAULT,
       normalize_enabled: bool = True,
       skills_as_strings: bool = False,
       debug: bool = False,
       **kwargs
   ) -> Dict[str, Any]
   - CONTRACT FROZEN: Function signature, parameter names/types/defaults, return structure
   - Convenience function that instantiates ResumeNormalizer and calls normalize()
   - Stability: Breaking changes require MAJOR version bump. New parameters may be
     added with defaults (backward compatible).

2. ResumeNormalizer class:
   - __init__(
         role_profile: RoleProfile = RoleProfile.DEFAULT,
         normalize_enabled: bool = True,
         skills_as_strings: bool = False,
         debug: bool = False,
         **kwargs
     )
     - CONTRACT FROZEN: Constructor signature stable
   
   - normalize(raw_resume_data: Dict[str, Any]) -> Dict[str, Any]
     - CONTRACT FROZEN: Method signature and return structure stable

3. RoleProfile enum:
   - CONTRACT FROZEN: Enum values stable. Active profiles: DEFAULT, SOFTWARE_ENGINEER,
     DATA_SCIENTIST. Deprecated profiles maintained for API compatibility.

Input Contract (FROZEN):
------------------------
raw_resume_data: Dict[str, Any] - Must match expected schema:
    Required top-level fields:
    - name: Optional[str]
    - email: Optional[str]
    - phone: Optional[str]
    - education: List[Dict] - Each entry must have: degree, institution, year/start_year/end_year
    - skills: List[str]
    - experience: List[Dict] - Each entry must have: title, company, duration/start_year/end_year
    - projects: List[Dict] - Each entry must have: name, description
    
    Raises ResumeValidationError if schema validation fails.

role_profile: RoleProfile enum - Role profile for normalization rules
    - DEFAULT: General-purpose normalization
    - SOFTWARE_ENGINEER: Software engineering role-specific rules
    - DATA_SCIENTIST: Data science role-specific rules
    - Deprecated profiles accepted but fall back to DEFAULT

normalize_enabled: bool - If False, returns raw data with minimal processing
    - Default: True

skills_as_strings: bool - Controls skills output format
    - True: List[str] (backward compatibility)
    - False: List[Dict] with name, confidence, source (recommended)
    - Default: False

debug: bool - If True, includes explainability metadata in output
    - Default: False

Output Contract (FROZEN):
-------------------------
Returns Dict[str, Any] with structure:
{
    'raw': Dict[str, Any],                    # Original input data (preserved)
    'normalized': Dict[str, Any],             # Normalized data (if normalize_enabled=True)
    'normalization_enabled': bool,            # Whether normalization was applied
    'normalization_version': str,              # Version of normalization rules (e.g., "1.1.0")
    'role_profile': str,                       # Role profile used (enum value)
    'original_profile': Optional[str],         # Present if deprecated profile used
    'profile_deprecated': Optional[bool],      # Present if deprecated profile used
    'explainability': Optional[Dict]           # Present if debug=True
}

normalized structure (when normalize_enabled=True):
{
    'name': str,                               # Title Case normalized
    'email': str,                              # Lowercase normalized
    'phone': str,                              # Standardized format: (XXX) XXX-XXXX
    'education': List[Dict],                   # Sorted by end_year descending, canonicalized
        # Each entry: degree (canonical), degree_raw, institution, start_year, end_year, raw_date
    'skills': List[str] | List[Dict],         # Format depends on skills_as_strings
        # If skills_as_strings=False: [{'name': str, 'confidence': float, 'source': str}, ...]
    'experience': List[Dict],                  # Sorted by end_year descending
        # Each entry: title, company, start_year, end_year, raw_date, description
    'projects': List[Dict]                     # Normalized names and descriptions
        # Each entry: name, description
}

Stability Guarantees (FROZEN):
------------------------------
1. Function Signatures: Stable - parameter names, types, defaults will not change
   without MAJOR version bump. New parameters may be added with defaults.

2. Return Structure: Stable - all current top-level fields guaranteed to exist.
   New fields may be added (backward compatible) but existing fields will not be
   removed or have incompatible type changes without MAJOR version bump.

3. Exception Types: Stable - ResumeValidationError for schema validation failures.
   Exception messages may improve but exception types remain stable.

4. Normalization Rules: Versioned via normalization_version field. Rule changes
   increment version. Same input + same version = same output (deterministic).

5. Role Profiles: Active profiles (DEFAULT, SOFTWARE_ENGINEER, DATA_SCIENTIST)
   are stable. Deprecated profiles maintained for compatibility but may be removed
   in future MAJOR version.

6. Skills Format: Controlled by skills_as_strings parameter. Both formats
   supported. Format stability guaranteed per parameter value.

7. Unexpected Parameters: Passing unexpected **kwargs triggers UserWarning but
   does not break execution. This helps catch API misuse early.

Internal Functions (NOT PUBLIC API):
------------------------------------
The following are internal implementation details and may change:
- validate_resume_schema, ResumeNormalizer._normalize_* methods, all helper
  functions, constants, and internal data structures.

These are not part of the public API contract.
"""

import re
import warnings
from typing import Dict, List, Optional, Any, Set, Tuple
from enum import Enum


# ============================================================================
# Normalization Versioning
# ============================================================================

# Normalization version - increment when normalization rules change
# Version format: MAJOR.MINOR.PATCH
# - MAJOR: Breaking changes to normalization output structure or behavior
# - MINOR: New normalization rules, new role profiles, or significant rule changes
# - PATCH: Bug fixes, minor rule adjustments, or documentation updates
#
# Versioning Strategy:
# ====================
# 1. Increment MAJOR when:
#    - Output structure changes (new required fields, removed fields)
#    - Normalization behavior changes in ways that break compatibility
#    - API changes that affect how normalized data is consumed
#
# 2. Increment MINOR when:
#    - New normalization rules are added
#    - New role profiles are activated
#    - Significant improvements to existing normalization rules
#    - New skill mappings or degree mappings are added
#
# 3. Increment PATCH when:
#    - Bug fixes in normalization logic
#    - Minor adjustments to existing rules
#    - Documentation updates
#    - Code refactoring that doesn't change output
#
# Example version history:
# - 1.0.0: Initial release
# - 1.1.0: Added new role profile
# - 1.1.1: Fixed bug in phone normalization
# - 2.0.0: Changed output structure (breaking change)
NORMALIZATION_VERSION = "1.1.0"


class ResumeValidationError(ValueError):
    """Custom exception for resume validation errors."""
    pass


class RoleProfile(str, Enum):
    """
    Available role profiles for normalization.
    
    TODO: Profile Limitation Rationale
    ===================================
    Currently, only SOFTWARE_ENGINEER, DATA_SCIENTIST, and DEFAULT profiles are actively
    maintained with role-specific skill prioritization. Other profiles are kept in the enum
    for API compatibility but are deprecated and will fall back to DEFAULT behavior.
    
    Reasons for limitation:
    1. Maintenance overhead: Each profile requires curated skill priorities and testing
    2. Focus on high-impact profiles: Software Engineer and Data Scientist cover majority of use cases
    3. Resource constraints: Limiting active profiles allows better quality and faster iteration
    4. Future extensibility: Deprecated profiles can be reactivated when needed
    
    To reactivate a profile: Add skill priorities to ROLE_SKILL_PRIORITIES dictionary.
    """
    # Active profiles - fully supported with role-specific prioritization
    SOFTWARE_ENGINEER = "software_engineer"
    DATA_SCIENTIST = "data_scientist"
    DEFAULT = "default"
    
    # Deprecated profiles - kept for API compatibility, fall back to DEFAULT behavior
    # TODO: These profiles are deprecated. They will use DEFAULT normalization.
    # To reactivate: Add skill priorities to ROLE_SKILL_PRIORITIES and update this comment.
    PRODUCT_MANAGER = "product_manager"  # Deprecated - use DEFAULT
    DEVOPS_ENGINEER = "devops_engineer"  # Deprecated - use DEFAULT
    FRONTEND_DEVELOPER = "frontend_developer"  # Deprecated - use DEFAULT
    BACKEND_DEVELOPER = "backend_developer"  # Deprecated - use DEFAULT
    FULL_STACK_DEVELOPER = "full_stack_developer"  # Deprecated - use DEFAULT
    MACHINE_LEARNING_ENGINEER = "machine_learning_engineer"  # Deprecated - use DEFAULT


# ATS-friendly skill mappings (maps variations to canonical forms)
ATS_SKILL_MAPPINGS = {
    # Programming Languages
    'js': 'JavaScript', 'javascript': 'JavaScript', 'js/ts': 'JavaScript/TypeScript',
    'ts': 'TypeScript', 'typescript': 'TypeScript',
    'c++': 'C++', 'cpp': 'C++', 'c plus plus': 'C++',
    'c#': 'C#', 'csharp': 'C#', 'c sharp': 'C#',
    'python': 'Python', 'py': 'Python',
    'java': 'Java',
    'go': 'Go', 'golang': 'Go',
    'rust': 'Rust',
    'ruby': 'Ruby',
    'php': 'PHP',
    'swift': 'Swift',
    'kotlin': 'Kotlin',
    'scala': 'Scala',
    'r': 'R',
    
    # Frameworks & Libraries
    'react': 'React', 'react.js': 'React', 'reactjs': 'React',
    'angular': 'Angular', 'angular.js': 'Angular', 'angularjs': 'Angular',
    'vue': 'Vue.js', 'vue.js': 'Vue.js', 'vuejs': 'Vue.js',
    'node': 'Node.js', 'node.js': 'Node.js', 'nodejs': 'Node.js',
    'express': 'Express.js', 'express.js': 'Express.js',
    'django': 'Django',
    'flask': 'Flask',
    'spring': 'Spring', 'spring boot': 'Spring Boot',
    
    # Databases
    'sql': 'SQL',
    'mysql': 'MySQL',
    'postgresql': 'PostgreSQL', 'postgres': 'PostgreSQL',
    'mongodb': 'MongoDB', 'mongo': 'MongoDB',
    'redis': 'Redis',
    
    # Cloud & DevOps
    'aws': 'AWS', 'amazon web services': 'AWS',
    'azure': 'Azure',
    'gcp': 'GCP', 'google cloud': 'GCP',
    'docker': 'Docker',
    'kubernetes': 'Kubernetes', 'k8s': 'Kubernetes',
    'git': 'Git',
    'github': 'GitHub',
    'gitlab': 'GitLab',
    
    # Data Science & ML
    'ml': 'Machine Learning', 'machine learning': 'Machine Learning',
    'dl': 'Deep Learning', 'deep learning': 'Deep Learning',
    'ds': 'Data Science', 'data science': 'Data Science',
    'nlp': 'NLP', 'natural language processing': 'NLP',
    'tensorflow': 'TensorFlow', 'tf': 'TensorFlow',
    'pytorch': 'PyTorch',
    'pandas': 'Pandas',
    'numpy': 'NumPy',
}

# Fixed taxonomy for degree canonicalization
# Maps variations to canonical degree names
DEGREE_TAXONOMY = {
    # Bachelor's Degrees
    'bachelor of science': 'Bachelor of Science',
    'bachelor of arts': 'Bachelor of Arts',
    'bachelor of engineering': 'Bachelor of Engineering',
    'bachelor of technology': 'Bachelor of Technology',
    'bachelor of business administration': 'Bachelor of Business Administration',
    'bachelor of computer science': 'Bachelor of Computer Science',
    'bachelor of information technology': 'Bachelor of Information Technology',
    'bachelor of applied science': 'Bachelor of Applied Science',
    'bachelor of fine arts': 'Bachelor of Fine Arts',
    'bachelor of architecture': 'Bachelor of Architecture',
    'bachelor of education': 'Bachelor of Education',
    'bachelor of nursing': 'Bachelor of Nursing',
    'bachelor of commerce': 'Bachelor of Commerce',
    'bachelor of economics': 'Bachelor of Economics',
    'bachelor of mathematics': 'Bachelor of Mathematics',
    'bachelor of physics': 'Bachelor of Physics',
    'bachelor of chemistry': 'Bachelor of Chemistry',
    'bachelor of biology': 'Bachelor of Biology',
    'bachelor of psychology': 'Bachelor of Psychology',
    'bachelor of sociology': 'Bachelor of Sociology',
    'bachelor of political science': 'Bachelor of Political Science',
    'bachelor of history': 'Bachelor of History',
    'bachelor of english': 'Bachelor of English',
    'bachelor of philosophy': 'Bachelor of Philosophy',
    'bachelor of law': 'Bachelor of Law',
    'bachelor of medicine': 'Bachelor of Medicine',
    'bachelor of surgery': 'Bachelor of Surgery',
    
    # Master's Degrees
    'master of science': 'Master of Science',
    'master of arts': 'Master of Arts',
    'master of engineering': 'Master of Engineering',
    'master of technology': 'Master of Technology',
    'master of business administration': 'Master of Business Administration',
    'master of computer science': 'Master of Computer Science',
    'master of information technology': 'Master of Information Technology',
    'master of applied science': 'Master of Applied Science',
    'master of fine arts': 'Master of Fine Arts',
    'master of architecture': 'Master of Architecture',
    'master of education': 'Master of Education',
    'master of public administration': 'Master of Public Administration',
    'master of public health': 'Master of Public Health',
    'master of social work': 'Master of Social Work',
    'master of law': 'Master of Law',
    'master of philosophy': 'Master of Philosophy',
    'master of data science': 'Master of Data Science',
    'master of information systems': 'Master of Information Systems',
    
    # Doctoral Degrees
    'doctor of philosophy': 'PhD',
    'phd': 'PhD',
    'doctor of medicine': 'Doctor of Medicine',
    'doctor of law': 'Doctor of Law',
    'doctor of education': 'Doctor of Education',
    'doctor of business administration': 'Doctor of Business Administration',
    'doctor of engineering': 'Doctor of Engineering',
    
    # Associate Degrees
    'associate of science': 'Associate of Science',
    'associate of arts': 'Associate of Arts',
    'associate of applied science': 'Associate of Applied Science',
    
    # Professional Certificates
    'certificate': 'Certificate',
    'diploma': 'Diploma',
    'professional certificate': 'Professional Certificate',
}

# Abbreviation mappings (common abbreviations to full forms)
DEGREE_ABBREVIATIONS = {
    'bs': 'Bachelor of Science',
    'b.s.': 'Bachelor of Science',
    'b.s': 'Bachelor of Science',
    'ba': 'Bachelor of Arts',
    'b.a.': 'Bachelor of Arts',
    'b.a': 'Bachelor of Arts',
    'be': 'Bachelor of Engineering',
    'b.e.': 'Bachelor of Engineering',
    'b.e': 'Bachelor of Engineering',
    'btech': 'Bachelor of Technology',
    'b.tech': 'Bachelor of Technology',
    'b.tech.': 'Bachelor of Technology',
    'bba': 'Bachelor of Business Administration',
    'b.b.a.': 'Bachelor of Business Administration',
    'bcs': 'Bachelor of Computer Science',
    'bscs': 'Bachelor of Computer Science',
    'ms': 'Master of Science',
    'm.s.': 'Master of Science',
    'm.s': 'Master of Science',
    'ma': 'Master of Arts',
    'm.a.': 'Master of Arts',
    'm.a': 'Master of Arts',
    'me': 'Master of Engineering',
    'm.e.': 'Master of Engineering',
    'm.e': 'Master of Engineering',
    'mtech': 'Master of Technology',
    'm.tech': 'Master of Technology',
    'm.tech.': 'Master of Technology',
    'mba': 'Master of Business Administration',
    'm.b.a.': 'Master of Business Administration',
    'm.b.a': 'Master of Business Administration',
    'mcs': 'Master of Computer Science',
    'mscs': 'Master of Computer Science',
    'phd': 'PhD',
    'ph.d.': 'PhD',
    'ph.d': 'PhD',
    'd.phil': 'PhD',
    'dphil': 'PhD',
    'md': 'Doctor of Medicine',
    'm.d.': 'Doctor of Medicine',
    'jd': 'Doctor of Law',
    'j.d.': 'Doctor of Law',
    'edd': 'Doctor of Education',
    'ed.d.': 'Doctor of Education',
    'dba': 'Doctor of Business Administration',
    'd.b.a.': 'Doctor of Business Administration',
    'as': 'Associate of Science',
    'a.s.': 'Associate of Science',
    'aa': 'Associate of Arts',
    'a.a.': 'Associate of Arts',
    'aas': 'Associate of Applied Science',
    'a.a.s.': 'Associate of Applied Science',
}

# Legacy mapping for backward compatibility (deprecated, use DEGREE_TAXONOMY)
ATS_DEGREE_MAPPINGS = {**DEGREE_ABBREVIATIONS, **DEGREE_TAXONOMY}

# Role-specific skill priorities (skills most relevant to each role)
# TODO: Only active profiles have skill priorities defined. Deprecated profiles will
# fall back to DEFAULT behavior (alphabetical sorting without prioritization).
ROLE_SKILL_PRIORITIES = {
    # Active profiles - fully supported
    RoleProfile.SOFTWARE_ENGINEER: {
        'high': ['Python', 'Java', 'JavaScript', 'C++', 'SQL', 'Git', 'REST API', 'Microservices'],
        'medium': ['Docker', 'Kubernetes', 'AWS', 'CI/CD', 'Agile', 'Scrum'],
    },
    RoleProfile.DATA_SCIENTIST: {
        'high': ['Python', 'R', 'SQL', 'Machine Learning', 'Data Science', 'Pandas', 'NumPy', 'TensorFlow', 'PyTorch'],
        'medium': ['Statistics', 'NLP', 'Deep Learning', 'Jupyter', 'Tableau', 'Power BI'],
    },
    
    # Deprecated profiles - commented out but kept for reference
    # TODO: To reactivate a deprecated profile, uncomment its entry below and update the enum docstring
    # RoleProfile.DEVOPS_ENGINEER: {
    #     'high': ['Docker', 'Kubernetes', 'AWS', 'CI/CD', 'Terraform', 'Ansible', 'Linux', 'Git'],
    #     'medium': ['Azure', 'GCP', 'Jenkins', 'GitLab', 'Monitoring', 'Infrastructure'],
    # },
    # RoleProfile.FRONTEND_DEVELOPER: {
    #     'high': ['JavaScript', 'TypeScript', 'React', 'Angular', 'Vue.js', 'HTML', 'CSS', 'Node.js'],
    #     'medium': ['Webpack', 'Vite', 'Bootstrap', 'Tailwind CSS', 'Responsive Design'],
    # },
    # RoleProfile.BACKEND_DEVELOPER: {
    #     'high': ['Python', 'Java', 'Node.js', 'SQL', 'REST API', 'Microservices', 'Django', 'Flask', 'Spring'],
    #     'medium': ['PostgreSQL', 'MongoDB', 'Redis', 'Docker', 'AWS', 'Git'],
    # },
    # RoleProfile.MACHINE_LEARNING_ENGINEER: {
    #     'high': ['Python', 'Machine Learning', 'Deep Learning', 'TensorFlow', 'PyTorch', 'Scikit-learn', 'Pandas', 'NumPy'],
    #     'medium': ['NLP', 'Computer Vision', 'MLOps', 'AWS SageMaker', 'Data Science'],
    # },
    # RoleProfile.PRODUCT_MANAGER: {
    #     'high': ['Product Management', 'Agile', 'Scrum', 'User Research', 'Analytics'],
    #     'medium': ['Jira', 'Confluence', 'Roadmapping', 'Stakeholder Management'],
    # },
    # RoleProfile.FULL_STACK_DEVELOPER: {
    #     'high': ['JavaScript', 'TypeScript', 'React', 'Node.js', 'Python', 'SQL', 'REST API'],
    #     'medium': ['Docker', 'AWS', 'Git', 'CI/CD', 'MongoDB', 'PostgreSQL'],
    # },
}


# Expected resume schema for validation
REQUIRED_RESUME_FIELDS = {
    'name': (str, type(None)),  # Optional[str]
    'email': (str, type(None)),  # Optional[str]
    'phone': (str, type(None)),  # Optional[str]
    'education': list,
    'skills': list,
    'experience': list,
    'projects': list,
}

# Expected structure for list items
# Note: Extra fields are allowed (like degree_raw) but not validated
EDUCATION_ITEM_FIELDS = {'degree', 'degree_raw', 'institution', 'year', 'start_year', 'end_year', 'raw_date'}
EXPERIENCE_ITEM_FIELDS = {'title', 'company', 'duration', 'start_year', 'end_year', 'raw_date'}
PROJECTS_ITEM_FIELDS = {'name', 'description'}


def validate_resume_schema(raw_resume_data: Dict[str, Any]) -> None:
    """
    Strictly validate the structure of raw resume data.
    
    Args:
        raw_resume_data: Raw resume data dictionary to validate
        
    Raises:
        ResumeValidationError: If validation fails with descriptive error message
    """
    if not isinstance(raw_resume_data, dict):
        raise ResumeValidationError(
            f"Expected resume data to be a dictionary, got {type(raw_resume_data).__name__}"
        )
    
    errors = []
    
    # Check all required fields exist
    for field_name in REQUIRED_RESUME_FIELDS:
        if field_name not in raw_resume_data:
            errors.append(f"Missing required field: '{field_name}'")
            continue
        
        value = raw_resume_data[field_name]
        expected_type = REQUIRED_RESUME_FIELDS[field_name]
        
        # Validate type (no coercion)
        if isinstance(expected_type, tuple):
            # Optional types (str or None)
            if value is not None and not isinstance(value, str):
                errors.append(
                    f"Field '{field_name}': expected str or None, got {type(value).__name__}"
                )
        elif not isinstance(value, expected_type):
            errors.append(
                f"Field '{field_name}': expected {expected_type.__name__}, got {type(value).__name__}"
            )
        
        # Validate list contents
        if field_name == 'skills' and isinstance(value, list):
            for i, skill in enumerate(value):
                # Skills can be strings (old format) or dicts with name/confidence (new format)
                if isinstance(skill, str):
                    # Old format - valid
                    pass
                elif isinstance(skill, dict):
                    # New format - validate structure
                    if 'name' not in skill:
                        errors.append(
                            f"Field 'skills[{i}]': missing required 'name' field"
                        )
                    elif not isinstance(skill.get('name'), str):
                        errors.append(
                            f"Field 'skills[{i}].name': expected str, got {type(skill.get('name')).__name__}"
                        )
                    if 'confidence' in skill and not isinstance(skill['confidence'], (int, float)):
                        errors.append(
                            f"Field 'skills[{i}].confidence': expected number, got {type(skill['confidence']).__name__}"
                        )
                else:
                    errors.append(
                        f"Field 'skills[{i}]': expected str or dict, got {type(skill).__name__}"
                    )
        
        elif field_name == 'education' and isinstance(value, list):
            for i, edu_item in enumerate(value):
                if not isinstance(edu_item, dict):
                    errors.append(
                        f"Field 'education[{i}]': expected dict, got {type(edu_item).__name__}"
                    )
                else:
                    # Check for unexpected fields (warn but don't fail)
                    for key in edu_item:
                        if key not in EDUCATION_ITEM_FIELDS:
                            # Allow extra fields but could log warning
                            pass
                    # Validate field types in education item
                    for field in EDUCATION_ITEM_FIELDS:
                        if field in edu_item:
                            field_value = edu_item[field]
                            if field_value is not None and not isinstance(field_value, str):
                                errors.append(
                                    f"Field 'education[{i}].{field}': expected str or None, "
                                    f"got {type(field_value).__name__}"
                                )
        
        elif field_name == 'experience' and isinstance(value, list):
            for i, exp_item in enumerate(value):
                if not isinstance(exp_item, dict):
                    errors.append(
                        f"Field 'experience[{i}]': expected dict, got {type(exp_item).__name__}"
                    )
                else:
                    # Validate field types in experience item
                    for field in EXPERIENCE_ITEM_FIELDS:
                        if field in exp_item:
                            field_value = exp_item[field]
                            if field_value is not None and not isinstance(field_value, str):
                                errors.append(
                                    f"Field 'experience[{i}].{field}': expected str or None, "
                                    f"got {type(field_value).__name__}"
                                )
        
        elif field_name == 'projects' and isinstance(value, list):
            for i, proj_item in enumerate(value):
                if not isinstance(proj_item, dict):
                    errors.append(
                        f"Field 'projects[{i}]': expected dict, got {type(proj_item).__name__}"
                    )
                else:
                    # Validate field types in project item
                    for field in PROJECTS_ITEM_FIELDS:
                        if field in proj_item:
                            field_value = proj_item[field]
                            if field_value is not None and not isinstance(field_value, str):
                                errors.append(
                                    f"Field 'projects[{i}].{field}': expected str or None, "
                                    f"got {type(field_value).__name__}"
                                )
    
    # Check for unexpected top-level fields
    unexpected_fields = set(raw_resume_data.keys()) - set(REQUIRED_RESUME_FIELDS.keys())
    if unexpected_fields:
        # Don't fail on unexpected fields, but could log warning
        pass
    
    if errors:
        error_message = "Resume schema validation failed:\n" + "\n".join(f"  - {error}" for error in errors)
        raise ResumeValidationError(error_message)


class ResumeNormalizer:
    """
    Normalizes resume data to ATS-friendly formats while preserving raw data.
    
    API FREEZE NOTICE:
    ==================
    This class's public API is FROZEN as of version 1.1.0. The following are considered stable:
    - __init__() parameter signature
    - normalize() method signature and return structure
    - Public attribute access patterns
    
    Breaking changes will only occur with MAJOR version bumps. New parameters may be added
    with default values to maintain backward compatibility.
    
    Unexpected keyword arguments will trigger warnings to help catch API misuse.
    """
    
    # Frozen API: These are the only valid __init__ parameters
    _VALID_INIT_PARAMS = {'role_profile', 'normalize_enabled', 'skills_as_strings', 'debug'}
    
    def __init__(
        self,
        role_profile: RoleProfile = RoleProfile.DEFAULT,
        normalize_enabled: bool = True,
        skills_as_strings: bool = False,
        debug: bool = False,
        **kwargs
    ):
        """
        Initialize the normalizer.
        
        API FROZEN: This method signature is stable. New parameters may be added with defaults.
        
        Args:
            role_profile: Role profile to use for normalization.
                         Only SOFTWARE_ENGINEER, DATA_SCIENTIST, and DEFAULT are actively supported.
                         Deprecated profiles will fall back to DEFAULT behavior.
            normalize_enabled: Whether to perform normalization (False returns raw data only)
            skills_as_strings: If True, return skills as list of strings (backward compatibility).
                              If False, return skills as list of objects with name and confidence.
            debug: If True, include explainability metadata in output showing how each field
                   was normalized and what rules were applied.
            **kwargs: Additional keyword arguments. Unexpected arguments will trigger warnings.
        
        Warns:
            UserWarning: If unexpected keyword arguments are provided.
        """
        # API freeze safeguard: Warn on unexpected parameters
        if kwargs:
            unexpected = set(kwargs.keys())
            for param in unexpected:
                warnings.warn(
                    f"Unexpected parameter '{param}' passed to ResumeNormalizer.__init__(). "
                    f"Valid parameters are: {', '.join(sorted(self._VALID_INIT_PARAMS))}. "
                    f"This parameter will be ignored. API is frozen - check documentation for correct usage.",
                    UserWarning,
                    stacklevel=2
                )
        # TODO: Handle deprecated profiles - fall back to DEFAULT if profile is not active
        active_profiles = {RoleProfile.SOFTWARE_ENGINEER, RoleProfile.DATA_SCIENTIST, RoleProfile.DEFAULT}
        if role_profile not in active_profiles:
            # Deprecated profile - use DEFAULT but preserve original for API compatibility
            self.role_profile = RoleProfile.DEFAULT
            self._original_profile = role_profile  # Keep for reference
        else:
            self.role_profile = role_profile
            self._original_profile = None
        
        self.normalize_enabled = normalize_enabled
        self.skills_as_strings = skills_as_strings
        self.debug = debug
        self._explainability = {}  # Track normalization transformations
    
    def normalize(self, raw_resume_data: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """
        Normalize resume data to ATS-friendly format.
        
        API FROZEN: This method signature is stable. Return structure is stable.
        
        Args:
            raw_resume_data: Raw resume data dictionary. Can include optional metadata:
                            - '_skills_metadata': Dict with 'from_explicit_section' (bool) to indicate
                              if skills came from explicit Skills section (default: True)
            **kwargs: Additional keyword arguments. Currently no additional parameters accepted.
                     Unexpected arguments will trigger warnings.
        
        Returns:
            Dictionary with 'raw', 'normalized', 'normalization_version', and other metadata.
            The normalization_version field indicates which version of normalization rules
            were applied to produce the normalized output.
            
            Return structure is stable and backward compatible. New fields may be added
            but existing fields will not be removed without a MAJOR version bump.
            
            Skills format in normalized output:
            - If skills_as_strings=True: List[str] for backward compatibility
            - If skills_as_strings=False: List[Dict] with 'name', 'confidence', and 'source' keys
              - 'name': Normalized skill name (str)
              - 'confidence': Confidence score 0.0-1.0 (float)
              - 'source': 'explicit_section' or 'inferred' (str)
            
        Raises:
            ResumeValidationError: If input data does not match expected schema
        
        Warns:
            UserWarning: If unexpected keyword arguments are provided.
        """
        # API freeze safeguard: Warn on unexpected parameters
        if kwargs:
            warnings.warn(
                f"Unexpected keyword arguments passed to ResumeNormalizer.normalize(): {list(kwargs.keys())}. "
                f"This method currently accepts no additional keyword arguments. "
                f"API is frozen - check documentation for correct usage.",
                UserWarning,
                stacklevel=2
            )
        # Strict schema validation - fail fast with descriptive errors
        validate_resume_schema(raw_resume_data)
        
        if not self.normalize_enabled:
            return {
                'raw': raw_resume_data,
                'normalized': raw_resume_data,
                'normalization_enabled': False,
                'normalization_version': NORMALIZATION_VERSION
            }
        
        normalized = {}
        self._explainability = {}  # Reset explainability tracking
        
        # Detect if skills came from explicit section (check for metadata or default to True)
        # The parser prioritizes explicit sections, so if skills exist, assume explicit unless
        # metadata indicates otherwise
        skills_from_explicit_section = raw_resume_data.get('_skills_metadata', {}).get(
            'from_explicit_section', True
        )
        
        # Normalize each field with explainability tracking
        normalized['name'], self._explainability['name'] = self._normalize_name_with_explanation(
            raw_resume_data.get('name')
        )
        normalized['email'], self._explainability['email'] = self._normalize_email_with_explanation(
            raw_resume_data.get('email')
        )
        normalized['phone'], self._explainability['phone'] = self._normalize_phone_with_explanation(
            raw_resume_data.get('phone')
        )
        normalized['education'], self._explainability['education'] = self._normalize_education_with_explanation(
            raw_resume_data.get('education', [])
        )
        normalized['skills'], self._explainability['skills'] = self._normalize_skills_with_explanation(
            raw_resume_data.get('skills', []),
            skills_from_explicit_section=skills_from_explicit_section
        )
        normalized['experience'], self._explainability['experience'] = self._normalize_experience_with_explanation(
            raw_resume_data.get('experience', [])
        )
        normalized['projects'], self._explainability['projects'] = self._normalize_projects_with_explanation(
            raw_resume_data.get('projects', [])
        )
        
        result = {
            'raw': raw_resume_data,
            'normalized': normalized,
            'normalization_enabled': True,
            'normalization_version': NORMALIZATION_VERSION,
            'role_profile': self.role_profile.value
        }
        
        # Add deprecation warning if original profile was deprecated
        if self._original_profile:
            result['original_profile'] = self._original_profile.value
            result['profile_deprecated'] = True
        
        # Add explainability metadata if debug is enabled
        if self.debug:
            result['explainability'] = self._explainability
        
        return result
    
    # ============================================================================
    # Explainability Wrapper Methods
    # ============================================================================
    
    def _normalize_name_with_explanation(self, name: Optional[str]) -> Tuple[Optional[str], Dict[str, Any]]:
        """Normalize name with explainability tracking."""
        if not name:
            explanation = {
                'source': 'raw',
                'value': None,
                'transformation': 'none',
                'rule_applied': 'null_value'
            }
            return None, explanation
        
        original = name
        normalized = self._normalize_name(name)
        
        explanation = {
            'source': 'raw',
            'value': original,
            'transformed_value': normalized,
            'transformation': 'title_case_with_special_handling',
            'rules_applied': [
                'strip_whitespace',
                'split_by_hyphens_and_spaces',
                'capitalize_parts',
                'handle_special_prefixes_mc_o'
            ],
            'changed': original != normalized
        }
        
        return normalized, explanation
    
    def _normalize_email_with_explanation(self, email: Optional[str]) -> Tuple[Optional[str], Dict[str, Any]]:
        """Normalize email with explainability tracking."""
        if not email:
            explanation = {
                'source': 'raw',
                'value': None,
                'transformation': 'none',
                'rule_applied': 'null_value'
            }
            return None, explanation
        
        original = email
        normalized = self._normalize_email(email)
        
        explanation = {
            'source': 'raw',
            'value': original,
            'transformed_value': normalized,
            'transformation': 'lowercase',
            'rules_applied': ['strip_whitespace', 'to_lowercase'],
            'changed': original != normalized
        }
        
        return normalized, explanation
    
    def _normalize_phone_with_explanation(self, phone: Optional[str]) -> Tuple[Optional[str], Dict[str, Any]]:
        """Normalize phone with explainability tracking."""
        if not phone:
            explanation = {
                'source': 'raw',
                'value': None,
                'transformation': 'none',
                'rule_applied': 'null_value'
            }
            return None, explanation
        
        original = phone
        normalized = self._normalize_phone(phone)
        
        explanation = {
            'source': 'raw',
            'value': original,
            'transformed_value': normalized,
            'transformation': 'standard_format',
            'rules_applied': ['extract_digits', 'format_to_standard'],
            'format_applied': 'us_format' if len(re.sub(r'[^\d]', '', normalized)) == 10 else 'international_format',
            'changed': original != normalized
        }
        
        return normalized, explanation
    
    def _normalize_education_with_explanation(
        self, education: List[Dict[str, Any]]
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """Normalize education with explainability tracking."""
        if not education:
            explanation = {
                'source': 'raw',
                'value': [],
                'transformation': 'none',
                'rule_applied': 'empty_list'
            }
            return [], explanation
        
        original = education
        normalized = self._normalize_education(education)
        
        # Track transformations for each entry
        entry_explanations = []
        for i, (orig_entry, norm_entry) in enumerate(zip(original, normalized)):
            entry_explanation = {
                'index': i,
                'degree': {
                    'source': 'raw',
                    'value': orig_entry.get('degree'),
                    'transformed_value': norm_entry.get('degree'),
                    'canonicalized': norm_entry.get('degree') != orig_entry.get('degree'),
                    'raw_preserved': norm_entry.get('degree_raw')
                },
                'institution': {
                    'source': 'raw',
                    'value': orig_entry.get('institution'),
                    'transformed_value': norm_entry.get('institution'),
                    'changed': norm_entry.get('institution') != orig_entry.get('institution')
                },
                'years': {
                    'start_year': {
                        'source': 'raw',
                        'value': orig_entry.get('start_year'),
                        'transformed_value': norm_entry.get('start_year'),
                        'validated': norm_entry.get('start_year') is not None
                    },
                    'end_year': {
                        'source': 'raw',
                        'value': orig_entry.get('end_year'),
                        'transformed_value': norm_entry.get('end_year'),
                        'validated': norm_entry.get('end_year') is not None
                    }
                }
            }
            entry_explanations.append(entry_explanation)
        
        explanation = {
            'source': 'raw',
            'value': original,
            'transformed_value': normalized,
            'transformation': 'canonicalize_degrees_validate_years_sort',
            'rules_applied': [
                'canonicalize_degree_names',
                'preserve_raw_degree',
                'validate_year_format',
                'sort_by_end_year_desc'
            ],
            'entries': entry_explanations,
            'sorted': True,
            'sort_key': 'end_year_desc'
        }
        
        return normalized, explanation
    
    def _normalize_skills_with_explanation(
        self, skills: List[str], skills_from_explicit_section: bool = True
    ) -> Tuple[List[Any], Dict[str, Any]]:
        """Normalize skills with explainability tracking."""
        if not skills:
            explanation = {
                'source': 'raw',
                'value': [],
                'transformation': 'none',
                'rule_applied': 'empty_list'
            }
            return [], explanation
        
        original = skills
        normalized = self._normalize_skills(skills, skills_from_explicit_section)
        
        # Track transformations for each skill
        skill_explanations = []
        for i, (orig_skill, norm_skill) in enumerate(zip(original, normalized)):
            if self.skills_as_strings:
                skill_explanation = {
                    'index': i,
                    'source': 'raw',
                    'value': orig_skill,
                    'transformed_value': norm_skill,
                    'canonicalized': norm_skill.lower() != orig_skill.lower()
                }
            else:
                skill_explanation = {
                    'index': i,
                    'source': 'raw',
                    'value': orig_skill,
                    'transformed_value': norm_skill['name'],
                    'canonicalized': norm_skill['name'].lower() != orig_skill.lower(),
                    'confidence': norm_skill.get('confidence'),
                    'confidence_source': norm_skill.get('source')
                }
            skill_explanations.append(skill_explanation)
        
        explanation = {
            'source': 'explicit_section' if skills_from_explicit_section else 'inferred',
            'value': original,
            'transformed_value': normalized,
            'transformation': 'canonicalize_and_prioritize',
            'rules_applied': [
                'map_to_canonical_forms',
                'deduplicate',
                'role_specific_prioritization' if self.role_profile != RoleProfile.DEFAULT else 'alphabetical_sort'
            ],
            'skills': skill_explanations,
            'format': 'objects_with_confidence' if not self.skills_as_strings else 'strings',
            'role_profile': self.role_profile.value
        }
        
        return normalized, explanation
    
    def _normalize_experience_with_explanation(
        self, experience: List[Dict[str, Any]]
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """Normalize experience with explainability tracking."""
        if not experience:
            explanation = {
                'source': 'raw',
                'value': [],
                'transformation': 'none',
                'rule_applied': 'empty_list'
            }
            return [], explanation
        
        original = experience
        normalized = self._normalize_experience(experience)
        
        # Track transformations for each entry
        entry_explanations = []
        for i, (orig_entry, norm_entry) in enumerate(zip(original, normalized)):
            entry_explanation = {
                'index': i,
                'title': {
                    'source': 'raw',
                    'value': orig_entry.get('title'),
                    'transformed_value': norm_entry.get('title'),
                    'changed': norm_entry.get('title') != orig_entry.get('title')
                },
                'company': {
                    'source': 'raw',
                    'value': orig_entry.get('company'),
                    'transformed_value': norm_entry.get('company'),
                    'changed': norm_entry.get('company') != orig_entry.get('company')
                },
                'years': {
                    'start_year': {
                        'source': 'raw',
                        'value': orig_entry.get('start_year'),
                        'transformed_value': norm_entry.get('start_year'),
                        'validated': norm_entry.get('start_year') is not None
                    },
                    'end_year': {
                        'source': 'raw',
                        'value': orig_entry.get('end_year'),
                        'transformed_value': norm_entry.get('end_year'),
                        'validated': norm_entry.get('end_year') is not None
                    }
                }
            }
            entry_explanations.append(entry_explanation)
        
        explanation = {
            'source': 'raw',
            'value': original,
            'transformed_value': normalized,
            'transformation': 'normalize_titles_companies_sort',
            'rules_applied': [
                'normalize_job_titles',
                'normalize_company_names',
                'sort_by_end_year_desc'
            ],
            'entries': entry_explanations,
            'sorted': True,
            'sort_key': 'end_year_desc'
        }
        
        return normalized, explanation
    
    def _normalize_projects_with_explanation(
        self, projects: List[Dict[str, Any]]
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """Normalize projects with explainability tracking."""
        if not projects:
            explanation = {
                'source': 'raw',
                'value': [],
                'transformation': 'none',
                'rule_applied': 'empty_list'
            }
            return [], explanation
        
        original = projects
        normalized = self._normalize_projects(projects)
        
        explanation = {
            'source': 'raw',
            'value': original,
            'transformed_value': normalized,
            'transformation': 'title_case_names_trim_descriptions',
            'rules_applied': ['title_case_names', 'trim_descriptions'],
            'entries_count': len(normalized)
        }
        
        return normalized, explanation
    
    # ============================================================================
    # Core Normalization Methods
    # ============================================================================
    
    def _normalize_name(self, name: Optional[str]) -> Optional[str]:
        """Normalize name to ATS-friendly format (Title Case)."""
        if not name:
            return None
        
        # Convert to title case, handling special cases
        normalized = name.strip()
        # Handle names with hyphens, apostrophes, etc.
        parts = re.split(r'[\s-]+', normalized)
        normalized_parts = []
        for part in parts:
            if part:
                # Handle prefixes like "Mc", "O'", etc.
                if part.lower().startswith("mc") and len(part) > 2:
                    normalized_parts.append(part[0:2].capitalize() + part[2:].capitalize())
                elif part.lower().startswith("o'") and len(part) > 2:
                    normalized_parts.append(part[0:2].capitalize() + part[2:].capitalize())
                else:
                    normalized_parts.append(part.capitalize())
        
        return ' '.join(normalized_parts)
    
    def _normalize_email(self, email: Optional[str]) -> Optional[str]:
        """Normalize email to lowercase."""
        if not email:
            return None
        return email.strip().lower()
    
    def _normalize_phone(self, phone: Optional[str]) -> Optional[str]:
        """Normalize phone to standard format: (XXX) XXX-XXXX."""
        if not phone:
            return None
        
        # Extract digits only
        digits = re.sub(r'[^\d]', '', phone)
        
        # Format based on length
        if len(digits) == 10:
            return f"({digits[0:3]}) {digits[3:6]}-{digits[6:]}"
        elif len(digits) == 11 and digits[0] == '1':
            # US number with country code
            return f"+1 ({digits[1:4]}) {digits[4:7]}-{digits[7:]}"
        else:
            # Return original if format is unclear
            return phone.strip()
    
    def _normalize_education(self, education: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Normalize education entries to ATS-friendly format.
        Canonicalizes degree names, validates years, and sorts by end_year descending.
        """
        normalized_edu = []
        
        for entry in education:
            raw_degree = entry.get('degree')
            degree_result = self._normalize_degree(raw_degree)
            
            # Validate and normalize years
            start_year = self._validate_year(entry.get('start_year'))
            end_year = self._validate_year(entry.get('end_year'))
            
            normalized_entry = {
                'degree': degree_result['canonical'] if degree_result else None,
                'degree_raw': raw_degree,  # Preserve raw degree string
                'institution': self._normalize_institution(entry.get('institution')),
                'start_year': start_year,
                'end_year': end_year,
                'raw_date': entry.get('raw_date'),
                'year': entry.get('year'),  # Keep for backward compatibility
            }
            normalized_edu.append(normalized_entry)
        
        # Sort strictly by end_year descending (most recent first)
        # Entries with None or invalid end_year go to the end (sorted as 0)
        normalized_edu.sort(
            key=lambda x: (
                int(x['end_year']) if x['end_year'] and x['end_year'].isdigit() else 0,
            ),
            reverse=True
        )
        
        return normalized_edu
    
    def _validate_year(self, year: Optional[str]) -> Optional[str]:
        """
        Validate graduation year format.
        
        Args:
            year: Year string to validate
            
        Returns:
            Validated year string (4-digit, 1900-2100) or None if invalid
        """
        if not year:
            return None
        
        # Convert to string if needed
        year_str = str(year).strip()
        
        # Check if it's a 4-digit number
        if not year_str.isdigit() or len(year_str) != 4:
            return None
        
        # Validate reasonable range (1900-2100)
        year_int = int(year_str)
        if 1900 <= year_int <= 2100:
            return year_str
        
        return None
    
    def _normalize_degree(self, degree: Optional[str]) -> Optional[Dict[str, str]]:
        """
        Normalize degree to canonical form using fixed taxonomy.
        
        Args:
            degree: Raw degree string
            
        Returns:
            Dictionary with 'canonical' (canonical form) and 'raw' (original) keys,
            or None if degree is None/empty
        """
        if not degree:
            return None
        
        raw_degree = degree.strip()
        degree_lower = raw_degree.lower()
        
        # First, try exact match in taxonomy
        if degree_lower in DEGREE_TAXONOMY:
            canonical = DEGREE_TAXONOMY[degree_lower]
            return {'canonical': canonical, 'raw': raw_degree}
        
        # Try abbreviation mappings
        if degree_lower in DEGREE_ABBREVIATIONS:
            canonical = DEGREE_ABBREVIATIONS[degree_lower]
            return {'canonical': canonical, 'raw': raw_degree}
        
        # Try partial matches in taxonomy (check if taxonomy key is contained in degree)
        for taxonomy_key, canonical in DEGREE_TAXONOMY.items():
            if taxonomy_key in degree_lower:
                # Extract major if present (e.g., "BS in Computer Science")
                major_match = re.search(r'in\s+(\w+(?:\s+\w+)*)', degree_lower)
                if major_match:
                    major = major_match.group(1).title()
                    return {'canonical': f"{canonical} in {major}", 'raw': raw_degree}
                return {'canonical': canonical, 'raw': raw_degree}
        
        # Try abbreviation partial matches
        for abbrev, canonical in DEGREE_ABBREVIATIONS.items():
            # Match abbreviations as whole words or with punctuation
            abbrev_pattern = r'\b' + re.escape(abbrev.replace('.', r'\.?')) + r'\b'
            if re.search(abbrev_pattern, degree_lower):
                # Extract major if present
                major_match = re.search(r'in\s+(\w+(?:\s+\w+)*)', degree_lower)
                if major_match:
                    major = major_match.group(1).title()
                    return {'canonical': f"{canonical} in {major}", 'raw': raw_degree}
                return {'canonical': canonical, 'raw': raw_degree}
        
        # If no mapping found, return title case as canonical (but preserve raw)
        return {'canonical': raw_degree.title(), 'raw': raw_degree}
    
    def _normalize_institution(self, institution: Optional[str]) -> Optional[str]:
        """Normalize institution name to ATS-friendly format."""
        if not institution:
            return None
        
        # Remove common suffixes/prefixes and normalize
        normalized = institution.strip()
        
        # Handle common abbreviations
        abbrev_map = {
            'univ': 'University',
            'univ.': 'University',
            'u.': 'University',
            'u ': 'University ',
            'col': 'College',
            'col.': 'College',
            'inst': 'Institute',
            'inst.': 'Institute',
        }
        
        for abbrev, full in abbrev_map.items():
            normalized = re.sub(rf'\b{re.escape(abbrev)}\b', full, normalized, flags=re.IGNORECASE)
        
        return normalized.title()
    
    def _normalize_skills(
        self,
        skills: List[str],
        skills_from_explicit_section: bool = True
    ) -> List[Any]:
        """
        Normalize skills to ATS-friendly format with role-specific prioritization.
        
        Args:
            skills: List of skill strings to normalize
            skills_from_explicit_section: True if skills came from explicit Skills section,
                                         False if inferred from global text scan
        
        Returns:
            If skills_as_strings is True: List[str] (backward compatibility)
            If skills_as_strings is False: List[Dict] with 'name' and 'confidence' keys
        """
        if not skills:
            return []
        
        # Confidence levels based on source
        # Explicit section skills have higher confidence (0.9)
        # Inferred skills have lower confidence (0.6)
        base_confidence = 0.9 if skills_from_explicit_section else 0.6
        
        normalized_skills = []
        seen = set()
        
        # First pass: normalize and map to canonical forms
        for skill in skills:
            skill_lower = skill.lower().strip()
            confidence = base_confidence
            
            # Check ATS mappings
            if skill_lower in ATS_SKILL_MAPPINGS:
                canonical = ATS_SKILL_MAPPINGS[skill_lower]
                # Exact match in canonical mappings increases confidence
                confidence = min(1.0, confidence + 0.05)
            else:
                # Try partial match
                canonical = None
                for key, value in ATS_SKILL_MAPPINGS.items():
                    if key in skill_lower or skill_lower in key:
                        canonical = value
                        # Partial match slightly reduces confidence
                        confidence = max(0.5, confidence - 0.1)
                        break
                
                if not canonical:
                    # Use original with title case
                    canonical = skill.strip().title()
                    # Unmapped skill reduces confidence
                    confidence = max(0.3, confidence - 0.2)
            
            # Deduplicate
            if canonical.lower() not in seen:
                seen.add(canonical.lower())
                
                if self.skills_as_strings:
                    # Backward compatibility: return as string
                    normalized_skills.append(canonical)
                else:
                    # New format: return as object with name and confidence
                    normalized_skills.append({
                        'name': canonical,
                        'confidence': round(confidence, 2),
                        'source': 'explicit_section' if skills_from_explicit_section else 'inferred'
                    })
        
        # Second pass: Apply role-specific prioritization if profile is not DEFAULT
        if self.role_profile != RoleProfile.DEFAULT and self.role_profile in ROLE_SKILL_PRIORITIES:
            priorities = ROLE_SKILL_PRIORITIES[self.role_profile]
            high_priority = [s.lower() for s in priorities.get('high', [])]
            medium_priority = [s.lower() for s in priorities.get('medium', [])]
            
            # Sort: high priority first, then medium, then others
            if self.skills_as_strings:
                normalized_skills.sort(key=lambda s: (
                    0 if s.lower() in high_priority else (1 if s.lower() in medium_priority else 2),
                    s.lower()
                ))
            else:
                # Sort by priority, then by confidence (descending), then alphabetically
                normalized_skills.sort(key=lambda s: (
                    0 if s['name'].lower() in high_priority else (1 if s['name'].lower() in medium_priority else 2),
                    -s['confidence'],  # Negative for descending
                    s['name'].lower()
                ))
        
        return normalized_skills
    
    def _normalize_experience(self, experience: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Normalize experience entries to ATS-friendly format."""
        normalized_exp = []
        
        for entry in experience:
            normalized_entry = {
                'title': self._normalize_job_title(entry.get('title')),
                'company': self._normalize_company(entry.get('company')),
                'start_year': entry.get('start_year'),
                'end_year': entry.get('end_year'),
                'raw_date': entry.get('raw_date'),
                'duration': entry.get('duration'),  # Keep for backward compatibility
            }
            normalized_exp.append(normalized_entry)
        
        # Sort by end_year (most recent first), then by start_year
        normalized_exp.sort(
            key=lambda x: (
                int(x['end_year']) if x['end_year'] and x['end_year'].isdigit() else 9999,
                int(x['start_year']) if x['start_year'] and x['start_year'].isdigit() else 0
            ),
            reverse=True
        )
        
        return normalized_exp
    
    def _normalize_job_title(self, title: Optional[str]) -> Optional[str]:
        """Normalize job title to ATS-friendly format."""
        if not title:
            return None
        
        # Remove common prefixes/suffixes and normalize
        normalized = title.strip()
        
        # Handle common title patterns
        # Capitalize properly (Title Case)
        normalized = normalized.title()
        
        # Fix common abbreviations
        abbrev_map = {
            'Sr.': 'Senior',
            'Jr.': 'Junior',
            'Eng.': 'Engineer',
            'Mgr.': 'Manager',
            'Dev.': 'Developer',
            'Dir.': 'Director',
        }
        
        for abbrev, full in abbrev_map.items():
            normalized = re.sub(rf'\b{re.escape(abbrev)}\b', full, normalized)
        
        return normalized
    
    def _normalize_company(self, company: Optional[str]) -> Optional[str]:
        """Normalize company name to ATS-friendly format."""
        if not company:
            return None
        
        normalized = company.strip()
        
        # Handle common suffixes
        suffix_map = {
            'inc': 'Inc.',
            'inc.': 'Inc.',
            'llc': 'LLC',
            'corp': 'Corp.',
            'corp.': 'Corp.',
            'ltd': 'Ltd.',
            'ltd.': 'Ltd.',
        }
        
        # Check if ends with suffix
        for suffix, canonical in suffix_map.items():
            if normalized.lower().endswith(f' {suffix}') or normalized.lower().endswith(f' {suffix}.'):
                normalized = normalized.rsplit(' ', 1)[0] + ' ' + canonical
                break
        
        return normalized.title()
    
    def _normalize_projects(self, projects: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Normalize project entries to ATS-friendly format."""
        normalized_projects = []
        
        for project in projects:
            normalized_project = {
                'name': project.get('name', '').strip().title() if project.get('name') else None,
                'description': project.get('description', '').strip() if project.get('description') else None,
            }
            normalized_projects.append(normalized_project)
        
        return normalized_projects


# Frozen API: These are the only valid normalize_resume parameters
_VALID_NORMALIZE_RESUME_PARAMS = {
    'raw_resume_data', 'role_profile', 'normalize_enabled', 'skills_as_strings', 'debug'
}


def normalize_resume(
    raw_resume_data: Dict[str, Any],
    role_profile: RoleProfile = RoleProfile.DEFAULT,
    normalize_enabled: bool = True,
    skills_as_strings: bool = False,
    debug: bool = False,
    **kwargs
) -> Dict[str, Any]:
    """
    Convenience function to normalize resume data.
    
    API FREEZE NOTICE:
    ==================
    This function's signature is FROZEN as of version 1.1.0. The following are stable:
    - Function signature (parameter names, types, defaults)
    - Return value structure (backward compatible additions only)
    - Exception types and error messages
    
    Breaking changes will only occur with MAJOR version bumps. New parameters may be added
    with default values to maintain backward compatibility.
    
    Unexpected keyword arguments will trigger warnings to help catch API misuse.
    
    Args:
        raw_resume_data: Raw resume data dictionary. Must match expected schema:
                        - name: Optional[str]
                        - email: Optional[str]
                        - phone: Optional[str]
                        - education: List[Dict] (with degree, institution, year, etc.)
                        - skills: List[str]
                        - experience: List[Dict] (with title, company, duration, etc.)
                        - projects: List[Dict] (with name, description)
        role_profile: Role profile to use for normalization.
                      Only SOFTWARE_ENGINEER, DATA_SCIENTIST, and DEFAULT are actively supported.
                      Deprecated profiles will fall back to DEFAULT behavior but are still accepted
                      for API compatibility.
        normalize_enabled: Whether to perform normalization
        skills_as_strings: If True, return skills as list of strings (backward compatibility).
                           If False, return skills as list of objects with name and confidence.
        debug: If True, include 'explainability' key in output with detailed transformation metadata.
               Defaults to False to keep output clean for production use.
        **kwargs: Additional keyword arguments. Unexpected arguments will trigger warnings.
        
    Returns:
        Dictionary with 'raw', 'normalized', 'normalization_version', and other metadata.
        The normalization_version field indicates which version of normalization rules
        were applied. If a deprecated profile was used, the result will include
        'original_profile' and 'profile_deprecated' fields.
        
        Return structure is stable and backward compatible. New fields may be added
        but existing fields will not be removed without a MAJOR version bump.
        
        If debug=True, includes 'explainability' key with:
        - Source tracking for each field
        - Transformation rules applied
        - Before/after values
        - Field-specific metadata (e.g., confidence scores, validation results)
        
        Skills format:
        - If skills_as_strings=True: ['Python', 'Java', ...]
        - If skills_as_strings=False: [{'name': 'Python', 'confidence': 0.9, 'source': 'explicit_section'}, ...]
        
    Raises:
        ResumeValidationError: If input data does not match expected schema (missing fields,
                               wrong types, or invalid list item structures)
    
    Warns:
        UserWarning: If unexpected keyword arguments are provided.
    """
    # API freeze safeguard: Warn on unexpected parameters
    if kwargs:
        unexpected = set(kwargs.keys())
        for param in unexpected:
            warnings.warn(
                f"Unexpected parameter '{param}' passed to normalize_resume(). "
                f"Valid parameters are: {', '.join(sorted(_VALID_NORMALIZE_RESUME_PARAMS - {'raw_resume_data'}))}. "
                f"This parameter will be ignored. API is frozen - check documentation for correct usage.",
                UserWarning,
                stacklevel=2
            )
    
    normalizer = ResumeNormalizer(
        role_profile=role_profile,
        normalize_enabled=normalize_enabled,
        skills_as_strings=skills_as_strings,
        debug=debug
    )
    return normalizer.normalize(raw_resume_data)

