#!/usr/bin/env python3
"""
ATS Field Mapper - Maps ATS form field names to resume schema paths.

This module provides deterministic mapping of ATS form field names to canonical
resume schema fields with fuzzy matching, confidence scoring, and selection strategies.

PUBLIC API (FROZEN):
====================
The following public API is FROZEN and guaranteed stable:

Public Functions:
----------------
1. map_ats_field(
       ats_field_name: str,
       resume_data: Dict[str, Any],
       selection_strategy: SelectionStrategy = SelectionStrategy.MOST_RECENT,
       fuzzy_threshold: float = 0.7,
       explain: bool = False
   ) -> Optional[Dict[str, Any]]
   - CONTRACT FROZEN: Function signature, parameter names/types/defaults, return structure
   - Maps single ATS field name to resume data value
   - Stability: Breaking changes require MAJOR version bump

2. map_multiple_fields(
       ats_field_names: List[str],
       resume_data: Dict[str, Any],
       selection_strategy: SelectionStrategy = SelectionStrategy.MOST_RECENT,
       fuzzy_threshold: float = 0.7,
       explain: bool = False
   ) -> Dict[str, Dict[str, Any]]
   - CONTRACT FROZEN: Function signature and return structure stable
   - Batch mapping of multiple field names
   - Returns dict mapping field names to mapping results

3. normalize_field_name(
       field_name: str,
       track_steps: bool = False
   ) -> Tuple[str, Optional[List[Dict[str, str]]]]
   - CONTRACT FROZEN: Function signature stable
   - Normalizes field names for matching
   - Returns normalized name and optional normalization steps

4. is_field_blacklisted(field_name: str) -> Tuple[bool, Optional[str]]
   - CONTRACT FROZEN: Function signature stable
   - Checks if field matches blacklist patterns
   - Returns (is_blacklisted, matched_pattern)

5. get_canonical_fields() -> List[str]
   - CONTRACT FROZEN: Function signature and return type stable
   - Returns list of all canonical field names

6. get_ats_field_variations(canonical_field: CanonicalField) -> List[str]
   - CONTRACT FROZEN: Function signature stable
   - Returns all ATS field name variations for a canonical field

Public Enums (FROZEN):
---------------------
1. CanonicalField: Enum of canonical field names
   - CONTRACT FROZEN: Enum values stable. New fields may be added (MINOR version)
     but existing values will not be removed or renamed without MAJOR version bump.

2. SelectionStrategy: Enum of selection strategies
   - CONTRACT FROZEN: Enum values stable. Values: MOST_RECENT, LONGEST, HIGHEST_DEGREE
   - New strategies may be added (MINOR version) but existing values stable.

Input Contracts (FROZEN):
-------------------------
map_ats_field / map_multiple_fields:
- ats_field_name: str - Field name from ATS form (any string)
- resume_data: Dict[str, Any] - Resume data dictionary matching resume_parser output schema
  Must have: name, email, phone, education, skills, experience, projects
- selection_strategy: SelectionStrategy - Strategy for list field selection
  Default: MOST_RECENT
- fuzzy_threshold: float - Similarity threshold (0.0-1.0) for fuzzy matching
  Default: 0.7. Sensitive fields require higher effective thresholds.
- explain: bool - Include explainability metadata in result
  Default: False

normalize_field_name:
- field_name: str - Raw field name to normalize
- track_steps: bool - Return normalization steps for explainability
  Default: False

is_field_blacklisted:
- field_name: str - Field name to check against blacklist

Output Contracts (FROZEN):
--------------------------
map_ats_field returns Optional[Dict[str, Any]]:
If match found or ignored:
{
    'canonical_field': str,                    # Canonical field name (e.g., "email")
    'schema_path': str,                        # Resume data path (e.g., "email" or "education[0].degree")
    'value': Any,                              # Value from resume_data (may be None)
    'match_type': str,                         # 'exact' | 'fuzzy' | 'ignored' | None
    'confidence': float,                       # Weighted confidence (0.0-1.0)
    'raw_score': float,                        # Unweighted similarity score (0.0-1.0)
    'sensitivity_weight': float,               # Applied sensitivity weight
    'selection_strategy': str,                 # Strategy used (if applicable)
    'selected_index': Optional[int],           # Selected entry index (if applicable)
    'ats_field_name': str,                     # Original field name
    'normalized_field_name': str,              # Normalized field name
    'canonical_schema_version': str,           # Schema version (e.g., "1.0.0")
    'blacklist_reason': Optional[str],         # Present if match_type='ignored'
    'explainability': Optional[Dict]           # Present if explain=True
}
If no match: None

map_multiple_fields returns Dict[str, Dict[str, Any]]:
- Keys: ATS field names from input list
- Values: Mapping results (same structure as map_ats_field return)
- Only includes successfully mapped fields (None results excluded)

normalize_field_name returns:
- If track_steps=False: (normalized: str, None)
- If track_steps=True: (normalized: str, steps: List[Dict])

is_field_blacklisted returns:
- (is_blacklisted: bool, matched_pattern: Optional[str])

Stability Guarantees (FROZEN):
------------------------------
1. Function Signatures: Stable - parameter names, types, defaults will not change
   without MAJOR version bump. New parameters may be added with defaults.

2. Return Structures: Stable - all current fields guaranteed to exist. New fields
   may be added (backward compatible) but existing fields will not be removed or
   have incompatible type changes without MAJOR version bump.

3. Canonical Fields: Enum values stable. New fields may be added (MINOR version)
   but existing values will not be removed or renamed without MAJOR version bump.

4. Selection Strategies: Enum values stable. New strategies may be added (MINOR)
   but existing strategies will not be removed or changed without MAJOR version.

5. Mapping Behavior: Deterministic - same input always produces same output.
   Mapping rules may improve (MINOR/PATCH) but will not break existing mappings.

6. Confidence Scoring: Formula stable (raw_score * sensitivity_weight). Sensitivity
   weights may be adjusted (PATCH) but formula structure remains stable.

7. Blacklist Patterns: FIELD_BLACKLIST_PATTERNS may be extended (PATCH) but existing
   patterns will not be removed without MAJOR version bump.

8. Schema Versioning: CANONICAL_SCHEMA_VERSION tracks changes. Version included
   in all outputs. Version changes follow semantic versioning.

Internal Functions (NOT PUBLIC API):
------------------------------------
The following are internal implementation details and may change:
- fuzzy_match_field, map_field_to_schema_path, _extract_first_name, _extract_last_name,
  _parse_year, _get_degree_level, _select_education_entry, _select_experience_entry,
  _select_project_entry, _build_selection_reasoning, _build_human_readable_summary,
  ATS_FIELD_MAPPINGS, FIELD_SENSITIVITY_WEIGHTS, FIELD_BLACKLIST_PATTERNS

These are not part of the public API contract.
"""

import re
from typing import Dict, List, Optional, Tuple, Any, Callable
from enum import Enum
from difflib import SequenceMatcher


# Canonical Schema Version
# This version tracks changes to the canonical field namespace, mapping rules,
# selection strategies, and output structure. Follows semantic versioning:
# - MAJOR: Breaking changes (field names removed, output structure changed)
# - MINOR: New fields added, new selection strategies, mapping rule changes
# - PATCH: Bug fixes, minor adjustments, documentation updates
CANONICAL_SCHEMA_VERSION = "1.0.0"


class SelectionStrategy(str, Enum):
    """
    Selection strategies for choosing entries from list fields.
    
    - most_recent: Select entry with most recent end date (or current if applicable)
    - longest: Select entry with longest duration (for experience/education) or 
               longest description (for projects)
    - highest_degree: Select education entry with highest degree level
                      (PhD > Master > Bachelor > Associate > Other)
    """
    MOST_RECENT = "most_recent"
    LONGEST = "longest"
    HIGHEST_DEGREE = "highest_degree"


class CanonicalField(str, Enum):
    """
    Canonical field namespace for resume data.
    These are the standard field names used internally.
    """
    # Personal Information
    FIRST_NAME = "first_name"
    LAST_NAME = "last_name"
    FULL_NAME = "full_name"
    EMAIL = "email"
    PHONE = "phone"
    PHONE_NUMBER = "phone_number"
    ADDRESS = "address"
    CITY = "city"
    STATE = "state"
    ZIP_CODE = "zip_code"
    COUNTRY = "country"
    LINKEDIN_URL = "linkedin_url"
    GITHUB_URL = "github_url"
    PORTFOLIO_URL = "portfolio_url"
    WEBSITE = "website"
    
    # Education
    EDUCATION_DEGREE = "education.degree"
    EDUCATION_INSTITUTION = "education.institution"
    EDUCATION_START_DATE = "education.start_date"
    EDUCATION_END_DATE = "education.end_date"
    EDUCATION_MAJOR = "education.major"
    EDUCATION_GPA = "education.gpa"
    
    # Experience
    EXPERIENCE_TITLE = "experience.title"
    EXPERIENCE_COMPANY = "experience.company"
    EXPERIENCE_START_DATE = "experience.start_date"
    EXPERIENCE_END_DATE = "experience.end_date"
    EXPERIENCE_DESCRIPTION = "experience.description"
    EXPERIENCE_CURRENT = "experience.current"
    
    # Skills
    SKILLS = "skills"
    
    # Projects
    PROJECT_NAME = "project.name"
    PROJECT_DESCRIPTION = "project.description"
    
    # Other
    RESUME_FILE = "resume_file"
    COVER_LETTER = "cover_letter"
    AVAILABILITY = "availability"
    SALARY_EXPECTATION = "salary_expectation"
    WORK_AUTHORIZATION = "work_authorization"


# Field sensitivity weights for confidence scoring
# Rationale:
# - CRITICAL fields (weight 0.5): Email, phone - These are contact identifiers that
#   must be accurate. Wrong values lead to failed communication. Require very high
#   confidence (0.9+) for fuzzy matches to prevent misrouting applications.
#
# - HIGH fields (weight 0.7): Name fields, work authorization - Identity and legal
#   status fields. Errors can cause application rejection or legal issues. Require
#   high confidence (0.85+) for fuzzy matches.
#
# - MEDIUM fields (weight 0.85): Education, experience dates, GPA - Important for
#   qualification matching but errors are recoverable. Require moderate confidence
#   (0.75+) for fuzzy matches.
#
# - STANDARD fields (weight 1.0): Skills, descriptions, URLs - Less critical fields
#   where partial matches are acceptable. Use base confidence threshold.
#
# The sensitivity weight is multiplied by the fuzzy match score to produce the final
# confidence. Lower weights mean higher effective threshold requirements.
FIELD_SENSITIVITY_WEIGHTS: Dict[CanonicalField, float] = {
    # CRITICAL - Contact identifiers (weight 0.5)
    CanonicalField.EMAIL: 0.5,
    CanonicalField.PHONE: 0.5,
    CanonicalField.PHONE_NUMBER: 0.5,
    
    # HIGH - Identity and legal fields (weight 0.7)
    CanonicalField.FIRST_NAME: 0.7,
    CanonicalField.LAST_NAME: 0.7,
    CanonicalField.FULL_NAME: 0.7,
    CanonicalField.WORK_AUTHORIZATION: 0.7,
    
    # MEDIUM - Important qualification fields (weight 0.85)
    CanonicalField.EDUCATION_DEGREE: 0.85,
    CanonicalField.EDUCATION_INSTITUTION: 0.85,
    CanonicalField.EDUCATION_START_DATE: 0.85,
    CanonicalField.EDUCATION_END_DATE: 0.85,
    CanonicalField.EDUCATION_GPA: 0.85,
    CanonicalField.EXPERIENCE_START_DATE: 0.85,
    CanonicalField.EXPERIENCE_END_DATE: 0.85,
    CanonicalField.EXPERIENCE_CURRENT: 0.85,
    
    # STANDARD - Less critical fields (weight 1.0)
    CanonicalField.ADDRESS: 1.0,
    CanonicalField.CITY: 1.0,
    CanonicalField.STATE: 1.0,
    CanonicalField.ZIP_CODE: 1.0,
    CanonicalField.COUNTRY: 1.0,
    CanonicalField.LINKEDIN_URL: 1.0,
    CanonicalField.GITHUB_URL: 1.0,
    CanonicalField.PORTFOLIO_URL: 1.0,
    CanonicalField.WEBSITE: 1.0,
    CanonicalField.EDUCATION_MAJOR: 1.0,
    CanonicalField.EXPERIENCE_TITLE: 1.0,
    CanonicalField.EXPERIENCE_COMPANY: 1.0,
    CanonicalField.EXPERIENCE_DESCRIPTION: 1.0,
    CanonicalField.SKILLS: 1.0,
    CanonicalField.PROJECT_NAME: 1.0,
    CanonicalField.PROJECT_DESCRIPTION: 1.0,
    CanonicalField.RESUME_FILE: 1.0,
    CanonicalField.COVER_LETTER: 1.0,
    CanonicalField.AVAILABILITY: 1.0,
    CanonicalField.SALARY_EXPECTATION: 1.0,
}


# ATS field name variations mapped to canonical fields
ATS_FIELD_MAPPINGS = {
    # Name variations
    'first name': CanonicalField.FIRST_NAME,
    'firstname': CanonicalField.FIRST_NAME,
    'fname': CanonicalField.FIRST_NAME,
    'given name': CanonicalField.FIRST_NAME,
    'forename': CanonicalField.FIRST_NAME,
    
    'last name': CanonicalField.LAST_NAME,
    'lastname': CanonicalField.LAST_NAME,
    'lname': CanonicalField.LAST_NAME,
    'surname': CanonicalField.LAST_NAME,
    'family name': CanonicalField.LAST_NAME,
    
    'full name': CanonicalField.FULL_NAME,
    'fullname': CanonicalField.FULL_NAME,
    'name': CanonicalField.FULL_NAME,
    'applicant name': CanonicalField.FULL_NAME,
    'candidate name': CanonicalField.FULL_NAME,
    
    # Contact information
    'email': CanonicalField.EMAIL,
    'email address': CanonicalField.EMAIL,
    'e-mail': CanonicalField.EMAIL,
    'e-mail address': CanonicalField.EMAIL,
    'email id': CanonicalField.EMAIL,
    'contact email': CanonicalField.EMAIL,
    
    'phone': CanonicalField.PHONE,
    'phone number': CanonicalField.PHONE_NUMBER,
    'telephone': CanonicalField.PHONE,
    'telephone number': CanonicalField.PHONE_NUMBER,
    'mobile': CanonicalField.PHONE,
    'mobile number': CanonicalField.PHONE_NUMBER,
    'cell phone': CanonicalField.PHONE,
    'cell': CanonicalField.PHONE,
    'contact number': CanonicalField.PHONE,
    'phone #': CanonicalField.PHONE,
    
    'address': CanonicalField.ADDRESS,
    'street address': CanonicalField.ADDRESS,
    'street': CanonicalField.ADDRESS,
    'address line 1': CanonicalField.ADDRESS,
    'address line1': CanonicalField.ADDRESS,
    
    'city': CanonicalField.CITY,
    
    'state': CanonicalField.STATE,
    'state/province': CanonicalField.STATE,
    'province': CanonicalField.STATE,
    
    'zip': CanonicalField.ZIP_CODE,
    'zip code': CanonicalField.ZIP_CODE,
    'postal code': CanonicalField.ZIP_CODE,
    'postcode': CanonicalField.ZIP_CODE,
    'zip/postal code': CanonicalField.ZIP_CODE,
    
    'country': CanonicalField.COUNTRY,
    
    # URLs
    'linkedin': CanonicalField.LINKEDIN_URL,
    'linkedin profile': CanonicalField.LINKEDIN_URL,
    'linkedin url': CanonicalField.LINKEDIN_URL,
    'linkedin.com': CanonicalField.LINKEDIN_URL,
    
    'github': CanonicalField.GITHUB_URL,
    'github profile': CanonicalField.GITHUB_URL,
    'github url': CanonicalField.GITHUB_URL,
    'github.com': CanonicalField.GITHUB_URL,
    
    'portfolio': CanonicalField.PORTFOLIO_URL,
    'portfolio url': CanonicalField.PORTFOLIO_URL,
    'portfolio website': CanonicalField.PORTFOLIO_URL,
    'personal website': CanonicalField.PORTFOLIO_URL,
    
    'website': CanonicalField.WEBSITE,
    'personal site': CanonicalField.WEBSITE,
    'homepage': CanonicalField.WEBSITE,
    
    # Education
    'degree': CanonicalField.EDUCATION_DEGREE,
    'education degree': CanonicalField.EDUCATION_DEGREE,
    'highest degree': CanonicalField.EDUCATION_DEGREE,
    'degree earned': CanonicalField.EDUCATION_DEGREE,
    'qualification': CanonicalField.EDUCATION_DEGREE,
    
    'school': CanonicalField.EDUCATION_INSTITUTION,
    'university': CanonicalField.EDUCATION_INSTITUTION,
    'college': CanonicalField.EDUCATION_INSTITUTION,
    'institution': CanonicalField.EDUCATION_INSTITUTION,
    'educational institution': CanonicalField.EDUCATION_INSTITUTION,
    'school name': CanonicalField.EDUCATION_INSTITUTION,
    'university name': CanonicalField.EDUCATION_INSTITUTION,
    'college name': CanonicalField.EDUCATION_INSTITUTION,
    
    'education start': CanonicalField.EDUCATION_START_DATE,
    'education start date': CanonicalField.EDUCATION_START_DATE,
    'school start date': CanonicalField.EDUCATION_START_DATE,
    'enrollment date': CanonicalField.EDUCATION_START_DATE,
    
    'education end': CanonicalField.EDUCATION_END_DATE,
    'education end date': CanonicalField.EDUCATION_END_DATE,
    'graduation date': CanonicalField.EDUCATION_END_DATE,
    'graduation year': CanonicalField.EDUCATION_END_DATE,
    'degree date': CanonicalField.EDUCATION_END_DATE,
    'completion date': CanonicalField.EDUCATION_END_DATE,
    
    'major': CanonicalField.EDUCATION_MAJOR,
    'field of study': CanonicalField.EDUCATION_MAJOR,
    'area of study': CanonicalField.EDUCATION_MAJOR,
    'concentration': CanonicalField.EDUCATION_MAJOR,
    'specialization': CanonicalField.EDUCATION_MAJOR,
    
    'gpa': CanonicalField.EDUCATION_GPA,
    'grade point average': CanonicalField.EDUCATION_GPA,
    'cgpa': CanonicalField.EDUCATION_GPA,
    
    # Experience
    'job title': CanonicalField.EXPERIENCE_TITLE,
    'position': CanonicalField.EXPERIENCE_TITLE,
    'title': CanonicalField.EXPERIENCE_TITLE,
    'role': CanonicalField.EXPERIENCE_TITLE,
    'position title': CanonicalField.EXPERIENCE_TITLE,
    'job role': CanonicalField.EXPERIENCE_TITLE,
    
    'company': CanonicalField.EXPERIENCE_COMPANY,
    'employer': CanonicalField.EXPERIENCE_COMPANY,
    'organization': CanonicalField.EXPERIENCE_COMPANY,
    'company name': CanonicalField.EXPERIENCE_COMPANY,
    'employer name': CanonicalField.EXPERIENCE_COMPANY,
    'organization name': CanonicalField.EXPERIENCE_COMPANY,
    
    'employment start': CanonicalField.EXPERIENCE_START_DATE,
    'employment start date': CanonicalField.EXPERIENCE_START_DATE,
    'start date': CanonicalField.EXPERIENCE_START_DATE,
    'job start date': CanonicalField.EXPERIENCE_START_DATE,
    'work start date': CanonicalField.EXPERIENCE_START_DATE,
    'date started': CanonicalField.EXPERIENCE_START_DATE,
    
    'employment end': CanonicalField.EXPERIENCE_END_DATE,
    'employment end date': CanonicalField.EXPERIENCE_END_DATE,
    'end date': CanonicalField.EXPERIENCE_END_DATE,
    'job end date': CanonicalField.EXPERIENCE_END_DATE,
    'work end date': CanonicalField.EXPERIENCE_END_DATE,
    'date ended': CanonicalField.EXPERIENCE_END_DATE,
    'to date': CanonicalField.EXPERIENCE_END_DATE,
    
    'job description': CanonicalField.EXPERIENCE_DESCRIPTION,
    'work description': CanonicalField.EXPERIENCE_DESCRIPTION,
    'responsibilities': CanonicalField.EXPERIENCE_DESCRIPTION,
    'duties': CanonicalField.EXPERIENCE_DESCRIPTION,
    'role description': CanonicalField.EXPERIENCE_DESCRIPTION,
    
    'current position': CanonicalField.EXPERIENCE_CURRENT,
    'current job': CanonicalField.EXPERIENCE_CURRENT,
    'currently employed': CanonicalField.EXPERIENCE_CURRENT,
    'still working': CanonicalField.EXPERIENCE_CURRENT,
    'present': CanonicalField.EXPERIENCE_CURRENT,
    
    # Skills
    'skills': CanonicalField.SKILLS,
    'technical skills': CanonicalField.SKILLS,
    'competencies': CanonicalField.SKILLS,
    'expertise': CanonicalField.SKILLS,
    'proficiencies': CanonicalField.SKILLS,
    'technologies': CanonicalField.SKILLS,
    'tools': CanonicalField.SKILLS,
    'programming languages': CanonicalField.SKILLS,
    
    # Projects
    'project name': CanonicalField.PROJECT_NAME,
    'project title': CanonicalField.PROJECT_NAME,
    
    'project description': CanonicalField.PROJECT_DESCRIPTION,
    'project details': CanonicalField.PROJECT_DESCRIPTION,
    
    # Other
    'resume': CanonicalField.RESUME_FILE,
    'resume file': CanonicalField.RESUME_FILE,
    'cv': CanonicalField.RESUME_FILE,
    'cv file': CanonicalField.RESUME_FILE,
    'upload resume': CanonicalField.RESUME_FILE,
    'attach resume': CanonicalField.RESUME_FILE,
    
    'cover letter': CanonicalField.COVER_LETTER,
    'cover letter file': CanonicalField.COVER_LETTER,
    'upload cover letter': CanonicalField.COVER_LETTER,
    
    'availability': CanonicalField.AVAILABILITY,
    'available': CanonicalField.AVAILABILITY,
    'start date': CanonicalField.AVAILABILITY,
    'when can you start': CanonicalField.AVAILABILITY,
    
    'salary': CanonicalField.SALARY_EXPECTATION,
    'salary expectation': CanonicalField.SALARY_EXPECTATION,
    'expected salary': CanonicalField.SALARY_EXPECTATION,
    'desired salary': CanonicalField.SALARY_EXPECTATION,
    'compensation': CanonicalField.SALARY_EXPECTATION,
    
    'work authorization': CanonicalField.WORK_AUTHORIZATION,
    'authorized to work': CanonicalField.WORK_AUTHORIZATION,
    'work permit': CanonicalField.WORK_AUTHORIZATION,
    'visa status': CanonicalField.WORK_AUTHORIZATION,
    'legal right to work': CanonicalField.WORK_AUTHORIZATION,
}


# Blacklist patterns for fields that should be ignored
# These are fields that should not be mapped (e.g., internal use, reserved, etc.)
# Patterns are matched case-insensitively against normalized field names
FIELD_BLACKLIST_PATTERNS = [
    # Internal/Reserved fields
    r'\binternal\s+use\b',
    r'\breserved\b',
    r'\bdo\s+not\s+fill\b',
    r'\bdo\s+not\s+complete\b',
    r'\bnot\s+for\s+applicant\b',
    r'\bfor\s+internal\s+use\s+only\b',
    r'\bhr\s+use\s+only\b',
    r'\brecruiter\s+use\s+only\b',
    r'\badmin\s+use\s+only\b',
    r'\badministrative\s+use\s+only\b',
    
    # Hidden/System fields
    r'\bhidden\b',
    r'\bsystem\s+field\b',
    r'\bauto\s+generated\b',
    r'\bgenerated\s+by\s+system\b',
    
    # Placeholder/Example fields
    r'\bplaceholder\b',
    r'\bexample\b',
    r'\bsample\b',
    r'\btest\s+field\b',
    r'\bdemo\b',
    
    # Disabled/Inactive fields
    r'\bdisabled\b',
    r'\binactive\b',
    r'\bnot\s+in\s+use\b',
    r'\bdeprecated\b',
    
    # Comments/Notes (non-data fields)
    r'^\s*comment\s*$',
    r'^\s*note\s*$',
    r'^\s*notes\s*$',
    r'^\s*remarks\s*$',
]


def is_field_blacklisted(field_name: str) -> Tuple[bool, Optional[str]]:
    """
    Check if a field name matches blacklist patterns and should be ignored.
    
    Args:
        field_name: Field name to check (will be normalized before checking)
        
    Returns:
        Tuple of (is_blacklisted, matched_pattern)
        - is_blacklisted: True if field should be ignored
        - matched_pattern: The pattern that matched (if any), None otherwise
    """
    # Normalize the field name for pattern matching
    normalized, _ = normalize_field_name(field_name, track_steps=False)
    
    # Check against each blacklist pattern
    for pattern in FIELD_BLACKLIST_PATTERNS:
        if re.search(pattern, normalized, re.IGNORECASE):
            return True, pattern
    
    return False, None


def normalize_field_name(
    field_name: str,
    track_steps: bool = False
) -> Tuple[str, Optional[List[Dict[str, str]]]]:
    """
    Normalize ATS field name for matching.
    
    Args:
        field_name: Raw field name from ATS form
        track_steps: If True, return normalization steps for explainability
        
    Returns:
        If track_steps=False: Normalized field name string
        If track_steps=True: Tuple of (normalized_name, steps_list)
    """
    steps = [] if track_steps else None
    original = field_name
    
    # Step 1: Convert to lowercase
    normalized = field_name.lower().strip()
    if track_steps and normalized != original:
        steps.append({
            'step': 'lowercase',
            'description': 'Converted to lowercase',
            'before': original,
            'after': normalized
        })
    
    # Step 2: Remove common prefixes
    before_prefix = normalized
    normalized = re.sub(r'^(required|optional|please enter|enter)\s*:?\s*', '', normalized)
    if track_steps and normalized != before_prefix:
        steps.append({
            'step': 'remove_prefix',
            'description': 'Removed common prefixes (required:, optional:, etc.)',
            'before': before_prefix,
            'after': normalized
        })
    
    # Step 3: Remove common suffixes
    before_suffix = normalized
    normalized = re.sub(r'\s*:?\s*(required|optional|\(required\)|\(optional\))$', '', normalized)
    if track_steps and normalized != before_suffix:
        steps.append({
            'step': 'remove_suffix',
            'description': 'Removed common suffixes ((required), (optional), etc.)',
            'before': before_suffix,
            'after': normalized
        })
    
    # Step 4: Remove special characters except spaces and hyphens
    before_special = normalized
    normalized = re.sub(r'[^\w\s-]', '', normalized)
    if track_steps and normalized != before_special:
        steps.append({
            'step': 'remove_special_chars',
            'description': 'Removed special characters (kept spaces and hyphens)',
            'before': before_special,
            'after': normalized
        })
    
    # Step 5: Normalize whitespace
    before_whitespace = normalized
    normalized = re.sub(r'\s+', ' ', normalized).strip()
    if track_steps and normalized != before_whitespace:
        steps.append({
            'step': 'normalize_whitespace',
            'description': 'Normalized whitespace (collapsed multiple spaces)',
            'before': before_whitespace,
            'after': normalized
        })
    
    if track_steps:
        return normalized, steps
    return normalized, None


def fuzzy_match_field(
    field_name: str,
    threshold: float = 0.7,
    explain: bool = False
) -> Tuple[Optional[CanonicalField], float, Optional[Dict[str, Any]]]:
    """
    Fuzzy match an ATS field name to a canonical field.
    
    Args:
        field_name: ATS field name to match
        threshold: Similarity threshold (0.0-1.0) for fuzzy matching
        explain: If True, return explainability metadata
        
    Returns:
        Tuple of (CanonicalField, raw_score, explanation) if match found above threshold,
        (None, 0.0, explanation) otherwise. The raw_score is the unweighted similarity score.
        If explain=False, explanation is None.
    """
    norm_result = normalize_field_name(field_name, track_steps=explain)
    if explain:
        normalized, norm_steps = norm_result
        explanation = {
            'normalization': {
                'original': field_name,
                'normalized': normalized,
                'steps': norm_steps or []
            },
            'matching': {
                'method': None,
                'matched_field': None,
                'similarity_score': None,
                'alternatives_considered': [],
                'threshold': threshold
            }
        }
    else:
        normalized, _ = norm_result
        explanation = None
    
    # First try exact match
    if normalized in ATS_FIELD_MAPPINGS:
        canonical_field = ATS_FIELD_MAPPINGS[normalized]
        if explain:
            explanation['matching'] = {
                'method': 'exact',
                'matched_field': normalized,
                'similarity_score': 1.0,
                'alternatives_considered': [],
                'threshold': threshold,
                'reasoning': f'Exact match found in mapping dictionary for "{normalized}"'
            }
        return canonical_field, 1.0, explanation
    
    # Try fuzzy matching
    best_match = None
    best_score = 0.0
    best_matched_field = None
    alternatives = []
    
    for ats_field, canonical_field in ATS_FIELD_MAPPINGS.items():
        # Calculate similarity
        score = SequenceMatcher(None, normalized, ats_field).ratio()
        
        # Also check if normalized field contains or is contained in ats_field
        partial_match = False
        if normalized in ats_field or ats_field in normalized:
            score = max(score, 0.85)  # Boost partial matches
            partial_match = True
        
        if explain:
            alternatives.append({
                'field': ats_field,
                'canonical': canonical_field.value,
                'similarity': score,
                'partial_match': partial_match
            })
        
        if score > best_score:
            best_score = score
            best_match = canonical_field
            best_matched_field = ats_field
    
    # Sort alternatives by score for explainability
    if explain:
        alternatives.sort(key=lambda x: x['similarity'], reverse=True)
        explanation['matching'] = {
            'method': 'fuzzy' if best_score >= threshold else 'none',
            'matched_field': best_matched_field,
            'similarity_score': best_score,
            'alternatives_considered': alternatives[:5],  # Top 5 alternatives
            'threshold': threshold,
            'reasoning': (
                f'Fuzzy match found: "{normalized}" matched "{best_matched_field}" '
                f'with similarity {best_score:.3f}'
                if best_score >= threshold else
                f'No match found: best similarity {best_score:.3f} below threshold {threshold}'
            )
        }
    
    # Return match if above threshold
    if best_score >= threshold:
        return best_match, best_score, explanation
    
    return None, 0.0, explanation


def _extract_first_name(full_name: Optional[str]) -> Optional[str]:
    """Extract first name from full name."""
    if not full_name:
        return None
    parts = full_name.strip().split()
    return parts[0] if parts else None


def _extract_last_name(full_name: Optional[str]) -> Optional[str]:
    """Extract last name from full name."""
    if not full_name:
        return None
    parts = full_name.strip().split()
    if len(parts) >= 2:
        return ' '.join(parts[1:])  # Handle multi-word last names
    return None


def _parse_year(year_str: Optional[str]) -> Optional[int]:
    """Parse year string to integer, returning None if invalid."""
    if not year_str:
        return None
    try:
        year = int(year_str)
        if 1900 <= year <= 2100:
            return year
    except (ValueError, TypeError):
        pass
    return None


def _get_degree_level(degree: Optional[str]) -> int:
    """
    Get numeric level for degree (higher = more advanced).
    Returns: PhD=4, Master=3, Bachelor=2, Associate=1, Other=0
    """
    if not degree:
        return 0
    degree_lower = degree.lower()
    if any(term in degree_lower for term in ['phd', 'ph.d', 'doctorate', 'd.phil']):
        return 4
    elif any(term in degree_lower for term in ['master', 'm.s', 'm.a', 'mba', 'm.tech']):
        return 3
    elif any(term in degree_lower for term in ['bachelor', 'b.s', 'b.a', 'b.tech', 'b.e']):
        return 2
    elif any(term in degree_lower for term in ['associate', 'diploma']):
        return 1
    return 0


def _select_education_entry(
    education_list: List[Dict[str, Any]],
    strategy: SelectionStrategy
) -> Optional[Tuple[int, Dict[str, Any]]]:
    """
    Select an education entry based on strategy.
    
    Args:
        education_list: List of education entries
        strategy: Selection strategy to use
        
    Returns:
        Tuple of (index, entry) if found, (None, None) if list is empty
    """
    if not education_list:
        return None, None
    
    if strategy == SelectionStrategy.MOST_RECENT:
        # Select by highest end_year (None/current treated as most recent)
        best_idx = 0
        best_year = None
        for idx, entry in enumerate(education_list):
            end_year = _parse_year(entry.get('end_year'))
            if end_year is None:
                # Current/ongoing education is most recent
                return idx, entry
            if best_year is None or end_year > best_year:
                best_year = end_year
                best_idx = idx
        return best_idx, education_list[best_idx]
    
    elif strategy == SelectionStrategy.LONGEST:
        # Select by longest duration (end_year - start_year)
        best_idx = 0
        best_duration = -1
        ongoing_idx = None
        
        # First pass: find longest completed duration
        for idx, entry in enumerate(education_list):
            start_year = _parse_year(entry.get('start_year'))
            end_year = _parse_year(entry.get('end_year'))
            if start_year and end_year:
                duration = end_year - start_year
                if duration > best_duration:
                    best_duration = duration
                    best_idx = idx
            elif start_year and end_year is None:
                # Track ongoing education but don't return immediately
                ongoing_idx = idx
        
        # If we found a completed education with duration, use it
        if best_duration >= 0:
            return best_idx, education_list[best_idx]
        
        # If no completed education found, prefer ongoing if available
        if ongoing_idx is not None:
            return ongoing_idx, education_list[ongoing_idx]
        
        # Fallback to first entry if no valid dates
        return 0, education_list[0]
    
    elif strategy == SelectionStrategy.HIGHEST_DEGREE:
        # Select by highest degree level
        best_idx = 0
        best_level = -1
        for idx, entry in enumerate(education_list):
            degree = entry.get('degree') or entry.get('degree_raw')
            level = _get_degree_level(degree)
            if level > best_level:
                best_level = level
                best_idx = idx
        return best_idx, education_list[best_idx]
    
    # Default: first entry
    return 0, education_list[0]


def _select_experience_entry(
    experience_list: List[Dict[str, Any]],
    strategy: SelectionStrategy
) -> Optional[Tuple[int, Dict[str, Any]]]:
    """
    Select an experience entry based on strategy.
    
    Args:
        experience_list: List of experience entries
        strategy: Selection strategy to use
        
    Returns:
        Tuple of (index, entry) if found, (None, None) if list is empty
    """
    if not experience_list:
        return None, None
    
    if strategy == SelectionStrategy.MOST_RECENT:
        # Select by highest end_year (None/current treated as most recent)
        best_idx = 0
        best_year = None
        for idx, entry in enumerate(experience_list):
            end_year = _parse_year(entry.get('end_year'))
            if end_year is None:
                # Current position is most recent
                return idx, entry
            if best_year is None or end_year > best_year:
                best_year = end_year
                best_idx = idx
        return best_idx, experience_list[best_idx]
    
    elif strategy == SelectionStrategy.LONGEST:
        # Select by longest duration (end_year - start_year)
        best_idx = 0
        best_duration = -1
        current_idx = None
        
        # First pass: find longest completed duration
        for idx, entry in enumerate(experience_list):
            start_year = _parse_year(entry.get('start_year'))
            end_year = _parse_year(entry.get('end_year'))
            if start_year and end_year:
                duration = end_year - start_year
                if duration > best_duration:
                    best_duration = duration
                    best_idx = idx
            elif start_year and end_year is None:
                # Track current position but don't return immediately
                current_idx = idx
        
        # If we found a completed position with duration, use it
        if best_duration >= 0:
            return best_idx, experience_list[best_idx]
        
        # If no completed position found, prefer current if available
        if current_idx is not None:
            return current_idx, experience_list[current_idx]
        
        # Fallback to first entry if no valid dates
        return 0, experience_list[0]
    
    # HIGHEST_DEGREE doesn't apply to experience, fallback to most_recent
    return _select_experience_entry(experience_list, SelectionStrategy.MOST_RECENT)


def _select_project_entry(
    projects_list: List[Dict[str, Any]],
    strategy: SelectionStrategy
) -> Optional[Tuple[int, Dict[str, Any]]]:
    """
    Select a project entry based on strategy.
    
    Args:
        projects_list: List of project entries
        strategy: Selection strategy to use
        
    Returns:
        Tuple of (index, entry) if found, (None, None) if list is empty
    """
    if not projects_list:
        return None, None
    
    if strategy == SelectionStrategy.LONGEST:
        # Select by longest description
        best_idx = 0
        best_length = -1
        for idx, entry in enumerate(projects_list):
            description = entry.get('description', '')
            length = len(description) if description else 0
            if length > best_length:
                best_length = length
                best_idx = idx
        return best_idx, projects_list[best_idx]
    
    # MOST_RECENT and HIGHEST_DEGREE don't apply to projects, default to first
    return 0, projects_list[0]


def map_field_to_schema_path(
    canonical_field: CanonicalField,
    resume_data: Dict[str, Any],
    selection_strategy: SelectionStrategy = SelectionStrategy.MOST_RECENT
) -> Tuple[Optional[str], Optional[Any]]:
    """
    Map a canonical field to its value in resume data schema.
    
    Uses selection strategies to choose entries from list fields instead of
    hard-coded indices. Fails safely if no suitable entry exists.
    
    Args:
        canonical_field: Canonical field to map
        resume_data: Resume data dictionary (from resume_parser or resume_normalizer)
        selection_strategy: Strategy for selecting entries from list fields
                          (most_recent, longest, highest_degree)
        
    Returns:
        Tuple of (schema_path, value) where schema_path is dot-notation path
        and value is the actual value from resume data.
        Returns (None, None) if no suitable entry found or field doesn't exist.
    """
    field_str = canonical_field.value
    
    # Handle top-level fields
    if '.' not in field_str:
        if field_str == 'full_name':
            return 'name', resume_data.get('name')
        elif field_str == 'first_name':
            # Extract from full name if available
            full_name = resume_data.get('name')
            return 'name (first)', _extract_first_name(full_name)
        elif field_str == 'last_name':
            # Extract from full name if available
            full_name = resume_data.get('name')
            return 'name (last)', _extract_last_name(full_name)
        elif field_str == 'phone_number':
            return 'phone', resume_data.get('phone')
        elif field_str == 'skills':
            return 'skills', resume_data.get('skills', [])
        else:
            # Direct mapping
            return field_str, resume_data.get(field_str)
    
    # Handle nested fields (education.*, experience.*, project.*)
    parts = field_str.split('.')
    category = parts[0]
    field = parts[1]
    
    if category == 'education':
        education_list = resume_data.get('education', [])
        idx, entry = _select_education_entry(education_list, selection_strategy)
        if entry is None:
            return None, None
        
        # Map field names
        if field == 'degree':
            return f'education[{idx}].degree', entry.get('degree')
        elif field == 'institution':
            return f'education[{idx}].institution', entry.get('institution')
        elif field == 'start_date':
            return f'education[{idx}].start_year', entry.get('start_year')
        elif field == 'end_date':
            return f'education[{idx}].end_year', entry.get('end_year')
        elif field == 'major':
            # Try to extract from degree if present
            degree = entry.get('degree') or entry.get('degree_raw', '')
            if ' in ' in degree:
                major = degree.split(' in ', 1)[1]
                return f'education[{idx}].major', major
            return f'education[{idx}].major', None
        elif field == 'gpa':
            return f'education[{idx}].gpa', entry.get('gpa')
    
    elif category == 'experience':
        experience_list = resume_data.get('experience', [])
        idx, entry = _select_experience_entry(experience_list, selection_strategy)
        if entry is None:
            return None, None
        
        if field == 'title':
            return f'experience[{idx}].title', entry.get('title')
        elif field == 'company':
            return f'experience[{idx}].company', entry.get('company')
        elif field == 'start_date':
            return f'experience[{idx}].start_year', entry.get('start_year')
        elif field == 'end_date':
            return f'experience[{idx}].end_year', entry.get('end_year')
        elif field == 'description':
            return f'experience[{idx}].description', entry.get('description')
        elif field == 'current':
            end_year = entry.get('end_year')
            return f'experience[{idx}].current', end_year is None
    
    elif category == 'project':
        projects_list = resume_data.get('projects', [])
        idx, entry = _select_project_entry(projects_list, selection_strategy)
        if entry is None:
            return None, None
        
        if field == 'name':
            return f'projects[{idx}].name', entry.get('name')
        elif field == 'description':
            return f'projects[{idx}].description', entry.get('description')
    
    return None, None


def _build_selection_reasoning(
    category: str,
    list_data: List[Dict[str, Any]],
    selected_index: Optional[int],
    strategy: SelectionStrategy
) -> str:
    """
    Build human-readable reasoning for entry selection.
    
    Args:
        category: Category name (education, experience, project)
        list_data: List of entries
        selected_index: Index of selected entry
        strategy: Selection strategy used
        
    Returns:
        Human-readable explanation string
    """
    if not list_data or selected_index is None:
        return f'No entries available in {category} list'
    
    if len(list_data) == 1:
        return f'Only one entry available, selected automatically'
    
    entry = list_data[selected_index]
    
    if strategy == SelectionStrategy.MOST_RECENT:
        if category == 'education':
            end_year = entry.get('end_year')
            if end_year is None:
                return f'Selected entry {selected_index} (ongoing/current education)'
            return f'Selected entry {selected_index} with most recent end year ({end_year})'
        elif category == 'experience':
            end_year = entry.get('end_year')
            if end_year is None:
                return f'Selected entry {selected_index} (current position)'
            return f'Selected entry {selected_index} with most recent end year ({end_year})'
        else:
            return f'Selected entry {selected_index} (most_recent strategy)'
    
    elif strategy == SelectionStrategy.LONGEST:
        if category in ['education', 'experience']:
            start_year = _parse_year(entry.get('start_year'))
            end_year = _parse_year(entry.get('end_year'))
            if start_year and end_year:
                duration = end_year - start_year
                return f'Selected entry {selected_index} with longest duration ({duration} years)'
            elif end_year is None:
                return f'Selected entry {selected_index} (ongoing, treated as longest)'
        elif category == 'project':
            desc = entry.get('description', '')
            return f'Selected entry {selected_index} with longest description ({len(desc)} characters)'
        return f'Selected entry {selected_index} (longest strategy)'
    
    elif strategy == SelectionStrategy.HIGHEST_DEGREE:
        degree = entry.get('degree') or entry.get('degree_raw', '')
        level = _get_degree_level(degree)
        level_name = ['Other', 'Associate', 'Bachelor', 'Master', 'PhD'][level] if level < 5 else 'Other'
        return f'Selected entry {selected_index} with highest degree level ({level_name})'
    
    return f'Selected entry {selected_index} using {strategy.value} strategy'


def _build_human_readable_summary(
    ats_field_name: str,
    canonical_field: str,
    match_type: str,
    confidence: float,
    selected_index: Optional[int],
    selection_strategy: Optional[str]
) -> str:
    """
    Build a human-readable summary of the mapping process.
    
    Args:
        ats_field_name: Original ATS field name
        canonical_field: Canonical field name
        match_type: Match type (exact/fuzzy)
        confidence: Weighted confidence score
        selected_index: Selected entry index (if applicable)
        selection_strategy: Selection strategy used (if applicable)
        
    Returns:
        Human-readable summary string
    """
    parts = []
    
    # Field matching
    if match_type == 'exact':
        parts.append(f'Field "{ats_field_name}" exactly matched canonical field "{canonical_field}"')
    else:
        parts.append(f'Field "{ats_field_name}" fuzzy matched to canonical field "{canonical_field}" with confidence {confidence:.1%}')
    
    # Selection (if applicable)
    if selected_index is not None and selection_strategy:
        parts.append(f'Selected entry {selected_index} from list using {selection_strategy} strategy')
    
    return '. '.join(parts) + '.'


def map_ats_field(
    ats_field_name: str,
    resume_data: Dict[str, Any],
    selection_strategy: SelectionStrategy = SelectionStrategy.MOST_RECENT,
    fuzzy_threshold: float = 0.7,
    explain: bool = False
) -> Optional[Dict[str, Any]]:
    """
    Map an ATS field name to resume data value with deterministic result.
    
    Confidence scoring applies field sensitivity weights:
    - CRITICAL fields (email, phone): Require very high confidence (0.9+)
      due to contact identifier importance. Wrong values cause communication failures.
    - HIGH fields (name, work auth): Require high confidence (0.85+)
      due to identity/legal importance. Errors can cause application rejection.
    - MEDIUM fields (dates, GPA): Require moderate confidence (0.75+)
      due to qualification matching importance. Errors are recoverable.
    - STANDARD fields (skills, descriptions): Use base threshold
      as partial matches are acceptable.
    
    Selection strategies for list fields:
    - most_recent: Select entry with most recent end date (or current)
    - longest: Select entry with longest duration/description
    - highest_degree: Select education entry with highest degree level
    
    Negative Match Rules (Blacklist):
    Fields matching blacklist patterns (e.g., "Internal Use Only", "Do Not Fill",
    "Reserved", "HR Use Only") are automatically ignored and return match_type='ignored'
    with a blacklist_reason explaining why the field was excluded.
    
    Args:
        ats_field_name: Field name from ATS form
        resume_data: Resume data dictionary
        selection_strategy: Strategy for selecting entries from list fields
                           (default: most_recent)
        fuzzy_threshold: Similarity threshold for fuzzy matching (base threshold,
                         sensitive fields require higher effective threshold)
        explain: If True, include detailed explainability metadata in result
        
    Returns:
        Dictionary with mapping information:
        {
            'canonical_field': str,
            'schema_path': str,
            'value': Any,
            'match_type': 'exact' | 'fuzzy' | 'ignored' | None,
            'confidence': float,  # Weighted confidence (0.0-1.0)
            'raw_score': float,    # Unweighted similarity score (0.0-1.0)
            'sensitivity_weight': float,  # Applied sensitivity weight
            'selection_strategy': str,    # Strategy used for selection
            'selected_index': Optional[int],  # Index of selected entry (if applicable)
            'ats_field_name': str,
            'normalized_field_name': str,
            'canonical_schema_version': str,  # Schema version (e.g., "1.0.0")
            'blacklist_reason': Optional[str],  # Present if match_type='ignored'
            'explainability': Optional[Dict]  # Present if explain=True
        }
        or None if no match found or no suitable entry exists
        
        Note: Fields matching blacklist patterns return match_type='ignored' instead of None.
        
        When explain=True, the 'explainability' key contains:
        {
            'field_name_normalization': {
                'original': str,
                'normalized': str,
                'steps': List[Dict]  # Normalization steps applied
            },
            'field_matching': {
                'method': 'exact' | 'fuzzy' | 'ignored' | 'none',
                'matched_field': str,
                'similarity_score': float,
                'alternatives_considered': List[Dict],
                'threshold': float,
                'reasoning': str
            },
            'confidence_calculation': {
                'raw_score': float,
                'sensitivity_weight': float,
                'sensitivity_category': str,
                'weighted_confidence': float,
                'threshold': float,
                'passed_threshold': bool,
                'reasoning': str
            },
            'selection': Optional[Dict] {  # Only for list fields
                'category': str,
                'strategy': str,
                'total_entries': int,
                'selected_index': int,
                'reasoning': str
            },
            'human_readable_summary': str
        }
    """
    # Check blacklist first - skip matching for excluded fields
    is_blacklisted, matched_pattern = is_field_blacklisted(ats_field_name)
    if is_blacklisted:
        # Return explicit 'ignored' mapping result
        result = {
            'canonical_field': None,
            'schema_path': None,
            'value': None,
            'match_type': 'ignored',
            'confidence': 0.0,
            'raw_score': 0.0,
            'sensitivity_weight': None,
            'selection_strategy': None,
            'selected_index': None,
            'ats_field_name': ats_field_name,
            'normalized_field_name': None,
            'canonical_schema_version': CANONICAL_SCHEMA_VERSION,
            'blacklist_reason': f'Field matches blacklist pattern: {matched_pattern}'
        }
        
        if explain:
            normalized, norm_steps = normalize_field_name(ats_field_name, track_steps=True)
            result['normalized_field_name'] = normalized
            result['explainability'] = {
                'field_name_normalization': {
                    'original': ats_field_name,
                    'normalized': normalized,
                    'steps': norm_steps or []
                },
                'field_matching': {
                    'method': 'ignored',
                    'matched_field': None,
                    'similarity_score': None,
                    'alternatives_considered': [],
                    'threshold': fuzzy_threshold,
                    'reasoning': f'Field was ignored due to blacklist pattern match: {matched_pattern}'
                },
                'confidence_calculation': None,
                'selection': None,
                'human_readable_summary': f'Field "{ats_field_name}" was ignored (matches blacklist pattern: {matched_pattern})'
            }
        
        return result
    
    # Normalize and try to match with explainability
    match_result = fuzzy_match_field(ats_field_name, fuzzy_threshold, explain=explain)
    canonical_field, raw_score, match_explanation = match_result
    
    if canonical_field is None:
        if explain:
            # Return explanation even for failed matches
            return {
                'canonical_field': None,
                'schema_path': None,
                'value': None,
                'match_type': None,
                'confidence': 0.0,
                'raw_score': raw_score,
                'sensitivity_weight': None,
                'selection_strategy': None,
                'selected_index': None,
                'ats_field_name': ats_field_name,
                'normalized_field_name': match_explanation['normalization']['normalized'] if match_explanation else None,
                'canonical_schema_version': CANONICAL_SCHEMA_VERSION,
                'explainability': match_explanation
            }
        return None
    
    match_type = 'exact' if raw_score == 1.0 else 'fuzzy'
    
    # Get sensitivity weight for this field
    # Default to 1.0 (standard) if field not in weights dict
    sensitivity_weight = FIELD_SENSITIVITY_WEIGHTS.get(canonical_field, 1.0)
    
    # Calculate weighted confidence: multiply raw score by sensitivity weight
    # Rationale: Lower weights penalize fuzzy matches, requiring higher raw scores
    # for sensitive fields to achieve acceptable confidence.
    #
    # Examples:
    # - Email (weight=0.5): raw_score=0.9 → confidence=0.45 (rejected if threshold=0.7)
    #                      raw_score=0.95 → confidence=0.475 (still rejected)
    #                      raw_score=1.0 → confidence=0.5 (rejected)
    #   This ensures only very high-quality matches (or exact matches) are accepted.
    #
    # - Skills (weight=1.0): raw_score=0.7 → confidence=0.7 (accepted if threshold=0.7)
    #   Standard fields accept matches at base threshold.
    #
    # Note: For exact matches (raw_score=1.0), confidence remains 1.0 regardless of weight
    if match_type == 'exact':
        confidence = 1.0
    else:
        confidence = raw_score * sensitivity_weight
    
    # Apply effective threshold check: sensitive fields need higher raw scores
    # For exact matches, we always accept (confidence=1.0)
    # For fuzzy matches, we check if weighted confidence meets threshold.
    # Due to sensitivity weighting, sensitive fields effectively require:
    # - CRITICAL (weight=0.5): raw_score >= threshold/0.5 = threshold*2 (e.g., 0.7*2=1.4, capped at 1.0)
    #   In practice, this means only very high raw scores (0.9+) pass.
    # - HIGH (weight=0.7): raw_score >= threshold/0.7 ≈ threshold*1.43
    # - MEDIUM (weight=0.85): raw_score >= threshold/0.85 ≈ threshold*1.18
    # - STANDARD (weight=1.0): raw_score >= threshold
    if match_type == 'fuzzy' and confidence < fuzzy_threshold:
        # Return explainability even for failed matches if explain=True
        if explain:
            explainability = {
                'field_name_normalization': match_explanation['normalization'] if match_explanation else None,
                'field_matching': match_explanation['matching'] if match_explanation else None,
                'confidence_calculation': {
                    'raw_score': raw_score,
                    'sensitivity_weight': sensitivity_weight,
                    'sensitivity_category': (
                        'CRITICAL' if sensitivity_weight == 0.5 else
                        'HIGH' if sensitivity_weight == 0.7 else
                        'MEDIUM' if sensitivity_weight == 0.85 else
                        'STANDARD'
                    ),
                    'weighted_confidence': confidence,
                    'threshold': fuzzy_threshold,
                    'passed_threshold': False,
                    'reasoning': (
                        f'Confidence {confidence:.3f} calculated as raw_score ({raw_score:.3f}) '
                        f'× sensitivity_weight ({sensitivity_weight:.2f}). '
                        f'Failed threshold check ({fuzzy_threshold}).'
                    )
                },
                'selection': None,
                'human_readable_summary': (
                    f'Field "{ats_field_name}" matched to "{canonical_field.value}" but '
                    f'confidence {confidence:.1%} below threshold {fuzzy_threshold:.1%}'
                )
            }
            return {
                'canonical_field': canonical_field.value,
                'schema_path': None,
                'value': None,
                'match_type': 'fuzzy',
                'confidence': confidence,
                'raw_score': raw_score,
                'sensitivity_weight': sensitivity_weight,
                'selection_strategy': None,
                'selected_index': None,
                'ats_field_name': ats_field_name,
                'normalized_field_name': match_explanation['normalization']['normalized'] if match_explanation else None,
                'canonical_schema_version': CANONICAL_SCHEMA_VERSION,
                'explainability': explainability
            }
        return None
    
    # Map to schema path and get value using selection strategy
    schema_path, value = map_field_to_schema_path(
        canonical_field, resume_data, selection_strategy
    )
    
    # Fail safely if no suitable entry exists
    if schema_path is None or value is None:
        # Check if this is a list field that might have no entries
        field_str = canonical_field.value
        if '.' in field_str:
            category = field_str.split('.')[0]
            if category in ['education', 'experience', 'project']:
                return None  # No suitable entry found
    
    # Extract selected index from schema_path if present (e.g., "education[2].degree")
    selected_index = None
    if schema_path and '[' in schema_path:
        match = re.search(r'\[(\d+)\]', schema_path)
        if match:
            selected_index = int(match.group(1))
    
    # Build explainability metadata
    explainability = None
    if explain:
        explainability = {
            'field_name_normalization': match_explanation['normalization'] if match_explanation else None,
            'field_matching': match_explanation['matching'] if match_explanation else None,
            'confidence_calculation': {
                'raw_score': raw_score,
                'sensitivity_weight': sensitivity_weight,
                'sensitivity_category': (
                    'CRITICAL' if sensitivity_weight == 0.5 else
                    'HIGH' if sensitivity_weight == 0.7 else
                    'MEDIUM' if sensitivity_weight == 0.85 else
                    'STANDARD'
                ),
                'weighted_confidence': confidence,
                'threshold': fuzzy_threshold,
                'passed_threshold': confidence >= fuzzy_threshold,
                'reasoning': (
                    f'Confidence {confidence:.3f} calculated as raw_score ({raw_score:.3f}) '
                    f'× sensitivity_weight ({sensitivity_weight:.2f}). '
                    f'{"Passed" if confidence >= fuzzy_threshold else "Failed"} threshold check ({fuzzy_threshold}).'
                )
            },
            'selection': None,
            'human_readable_summary': None
        }
        
        # Add selection explainability for list fields
        field_str = canonical_field.value
        if '.' in field_str:
            category = field_str.split('.')[0]
            if category in ['education', 'experience', 'project']:
                list_data = resume_data.get(category, [])
                explainability['selection'] = {
                    'category': category,
                    'strategy': selection_strategy.value,
                    'total_entries': len(list_data),
                    'selected_index': selected_index,
                    'reasoning': _build_selection_reasoning(
                        category, list_data, selected_index, selection_strategy
                    )
                }
        
        # Build human-readable summary
        explainability['human_readable_summary'] = _build_human_readable_summary(
            ats_field_name,
            canonical_field.value,
            match_type,
            confidence,
            selected_index,
            selection_strategy.value if selected_index is not None else None
        )
    
    result = {
        'canonical_field': canonical_field.value,
        'schema_path': schema_path,
        'value': value,
        'match_type': match_type,
        'confidence': confidence,  # Weighted confidence (0.0-1.0)
        'raw_score': raw_score,    # Unweighted similarity score (0.0-1.0)
        'sensitivity_weight': sensitivity_weight,  # Applied sensitivity weight
        'selection_strategy': selection_strategy.value,  # Strategy used
        'selected_index': selected_index,  # Index of selected entry (if applicable)
        'ats_field_name': ats_field_name,
        'normalized_field_name': match_explanation['normalization']['normalized'] if match_explanation else None,
        'canonical_schema_version': CANONICAL_SCHEMA_VERSION  # Schema version for compatibility tracking
    }
    
    if explain:
        result['explainability'] = explainability
    
    return result


def map_multiple_fields(
    ats_field_names: List[str],
    resume_data: Dict[str, Any],
    selection_strategy: SelectionStrategy = SelectionStrategy.MOST_RECENT,
    fuzzy_threshold: float = 0.7,
    explain: bool = False
) -> Dict[str, Dict[str, Any]]:
    """
    Map multiple ATS field names to resume data values.
    
    Args:
        ats_field_names: List of ATS field names
        resume_data: Resume data dictionary
        selection_strategy: Strategy for selecting entries from list fields
                           (default: most_recent)
        fuzzy_threshold: Similarity threshold for fuzzy matching
        explain: If True, include detailed explainability metadata in results
        
    Returns:
        Dictionary mapping ATS field names to mapping results:
        {
            'ats_field_name': {
                'canonical_field': str,
                'schema_path': str,
                'value': Any,
                'match_type': str,
                'confidence': float,
                'selection_strategy': str,
                'selected_index': Optional[int],
                'canonical_schema_version': str
            },
            ...
        }
    """
    results = {}
    
    for field_name in ats_field_names:
        mapping = map_ats_field(
            field_name, resume_data,
            selection_strategy=selection_strategy,
            fuzzy_threshold=fuzzy_threshold,
            explain=explain
        )
        if mapping:
            results[field_name] = mapping
    
    return results


def get_canonical_fields() -> List[str]:
    """
    Get list of all canonical field names.
    
    Returns:
        List of canonical field name strings
    """
    return [field.value for field in CanonicalField]


def get_ats_field_variations(canonical_field: CanonicalField) -> List[str]:
    """
    Get all ATS field name variations for a canonical field.
    
    Args:
        canonical_field: Canonical field to get variations for
        
    Returns:
        List of ATS field name variations
    """
    variations = []
    for ats_field, canonical in ATS_FIELD_MAPPINGS.items():
        if canonical == canonical_field:
            variations.append(ats_field)
    return variations

