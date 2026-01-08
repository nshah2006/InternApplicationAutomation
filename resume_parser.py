#!/usr/bin/env python3
"""
Resume Parser - Extracts structured information from PDF and DOCX resume files.

This module provides functionality to parse resume files (PDF/DOCX) and extract
structured information into a canonical JSON schema.

PUBLIC API (FROZEN):
====================
The following public API is FROZEN and guaranteed stable:

Public Functions:
----------------
1. parse_resume(file_path: str) -> Dict[str, Any]
   - Main entry point for parsing resume files
   - CONTRACT FROZEN: Function signature, return structure, exception types
   - Input: Path to PDF or DOCX resume file (str)
   - Output: Dictionary matching RESUME_SCHEMA structure with all required fields
   - Raises: FileNotFoundError, ValueError (on schema validation failure)
   - Stability: Function signature stable. Return structure stable (backward compatible
     additions only). Breaking changes require MAJOR version bump.

Input Contract (FROZEN):
------------------------
- file_path: str - Path to resume file
  - Must be valid file path
  - Must be PDF (.pdf) or DOCX (.docx) format
  - File must exist and be readable

Output Contract (FROZEN):
-------------------------
Returns Dict[str, Any] matching RESUME_SCHEMA with structure:
{
    'name': Optional[str],           # Full name (extracted with confidence)
    'email': Optional[str],          # Email address
    'phone': Optional[str],          # Phone number
    'education': List[Dict],         # Education entries with:
        # Each entry: degree, institution, start_year, end_year, raw_date, year
    'skills': List[str],             # List of skills (normalized)
    'experience': List[Dict],        # Experience entries with:
        # Each entry: title, company, start_year, end_year, raw_date, duration, description
    'projects': List[Dict]           # Project entries with:
        # Each entry: name, description
}

All fields are guaranteed to exist (may be None or empty lists).
Schema validation ensures type correctness.

Stability Guarantees (FROZEN):
------------------------------
1. Function Signature: Stable - parameter names, types, defaults will not change
   without MAJOR version bump.

2. Return Structure: Stable - all current fields guaranteed to exist. New fields
   may be added (backward compatible) but existing fields will not be removed or
   have type changes without MAJOR version bump.

3. Exception Types: Stable - FileNotFoundError for missing files, ValueError for
   schema validation failures. New exception types may be added but existing ones
   will not be removed.

4. Behavior: Stable - parsing logic may improve but will not produce incompatible
   output structures. Extraction accuracy may improve but output schema remains stable.

5. Schema Definition: RESUME_SCHEMA constant is FROZEN - structure and field
   definitions are stable.

Internal Functions (NOT PUBLIC API):
------------------------------------
The following functions are internal implementation details and may change:
- read_resume_file, extract_text, extract_email, extract_phone, extract_name,
  extract_education, extract_skills, extract_experience, extract_projects,
  assemble_resume_data, normalize_to_schema, validate_schema, validate_json

These are not part of the public API contract and may be modified or removed.
"""

import re
import json
import sys
import argparse
from pathlib import Path
from typing import Dict, List, Optional, Any


# Canonical Resume Schema Definition
# Type constants for runtime type checking
TYPE_OPTIONAL_STR = 'optional_str'
TYPE_LIST_STR = 'list_str'
TYPE_LIST_DICT = 'list_dict'

RESUME_SCHEMA = {
    'name': {
        'type': TYPE_OPTIONAL_STR,
        'required': True,
        'default': None,
        'description': 'Full name of the candidate'
    },
    'email': {
        'type': TYPE_OPTIONAL_STR,
        'required': True,
        'default': None,
        'description': 'Email address'
    },
    'phone': {
        'type': TYPE_OPTIONAL_STR,
        'required': True,
        'default': None,
        'description': 'Phone number'
    },
    'education': {
        'type': TYPE_LIST_DICT,
        'required': True,
        'default': [],
        'description': 'List of education entries',
        'item_schema': {
            'degree': {'type': TYPE_OPTIONAL_STR, 'default': None},
            'institution': {'type': TYPE_OPTIONAL_STR, 'default': None},
            'year': {'type': TYPE_OPTIONAL_STR, 'default': None},
            'start_year': {'type': TYPE_OPTIONAL_STR, 'default': None},
            'end_year': {'type': TYPE_OPTIONAL_STR, 'default': None},
            'raw_date': {'type': TYPE_OPTIONAL_STR, 'default': None}
        }
    },
    'skills': {
        'type': TYPE_LIST_STR,
        'required': True,
        'default': [],
        'description': 'List of skills'
    },
    'experience': {
        'type': TYPE_LIST_DICT,
        'required': True,
        'default': [],
        'description': 'List of work experience entries',
        'item_schema': {
            'title': {'type': TYPE_OPTIONAL_STR, 'default': None},
            'company': {'type': TYPE_OPTIONAL_STR, 'default': None},
            'duration': {'type': TYPE_OPTIONAL_STR, 'default': None},
            'start_year': {'type': TYPE_OPTIONAL_STR, 'default': None},
            'end_year': {'type': TYPE_OPTIONAL_STR, 'default': None},
            'raw_date': {'type': TYPE_OPTIONAL_STR, 'default': None}
        }
    },
    'projects': {
        'type': TYPE_LIST_DICT,
        'required': True,
        'default': [],
        'description': 'List of project entries',
        'item_schema': {
            'name': {'type': TYPE_OPTIONAL_STR, 'default': None},
            'description': {'type': TYPE_OPTIONAL_STR, 'default': None}
        }
    }
}


# ============================================================================
# File Reading Functions
# ============================================================================

def read_resume_file(file_path: str) -> Path:
    """
    Read and validate resume file path.
    
    Args:
        file_path: Path to the resume file
        
    Returns:
        Path object for the resume file
        
    Raises:
        FileNotFoundError: If the file does not exist
    """
    file_path_obj = Path(file_path)
    
    if not file_path_obj.exists():
        raise FileNotFoundError(f"Resume file not found: {file_path}")
    
    return file_path_obj


# ============================================================================
# Text Extraction Functions
# ============================================================================

def _extract_text_from_pdf(pdf_path: str) -> str:
    """
    Extract text content from a PDF file.
    
    Args:
        pdf_path: Path to the PDF file
        
    Returns:
        Extracted text as a string
        
    Raises:
        ImportError: If PyPDF2 is not installed
    """
    try:
        import PyPDF2
    except ImportError:
        raise ImportError("PyPDF2 is required for PDF parsing. Install it with: pip install PyPDF2")
    
    text = ""
    with open(pdf_path, 'rb') as file:
        pdf_reader = PyPDF2.PdfReader(file)
        for page in pdf_reader.pages:
            text += page.extract_text() + "\n"
    return text


def _extract_text_from_docx(docx_path: str) -> str:
    """
    Extract text content from a DOCX file.
    
    Args:
        docx_path: Path to the DOCX file
        
    Returns:
        Extracted text as a string
        
    Raises:
        ImportError: If python-docx is not installed
    """
    try:
        from docx import Document
    except ImportError:
        raise ImportError("python-docx is required for DOCX parsing. Install it with: pip install python-docx")
    
    doc = Document(docx_path)
    text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
    return text


def extract_text(file_path: str) -> str:
    """
    Extract raw text from a resume file (PDF or DOCX).
    
    Args:
        file_path: Path to the resume file
        
    Returns:
        Extracted text as a string
        
    Raises:
        ValueError: If file format is not supported
        ImportError: If required library is not installed
    """
    file_path_lower = file_path.lower()
    
    if file_path_lower.endswith('.pdf'):
        return _extract_text_from_pdf(file_path)
    elif file_path_lower.endswith('.docx'):
        return _extract_text_from_docx(file_path)
    else:
        raise ValueError(f"Unsupported file format. Please provide a PDF or DOCX file.")


# ============================================================================
# Data Extraction Functions (Pure Functions)
# ============================================================================


# ============================================================================
# Individual Extraction Functions (Pure Functions)
# ============================================================================

def extract_email(text: str) -> Optional[str]:
    """
    Extract email address from text using regex.
    
    Args:
        text: Input text to search
        
    Returns:
        First email address found, or None
    """
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    matches = re.findall(email_pattern, text)
    return matches[0] if matches else None


def extract_phone(text: str) -> Optional[str]:
    """
    Extract phone number from text using regex.
    Supports various formats: (123) 456-7890, 123-456-7890, 123.456.7890, etc.
    
    Args:
        text: Input text to search
        
    Returns:
        First phone number found (formatted), or None
    """
    # Pattern matches common phone number formats
    phone_patterns = [
        r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}',  # (123) 456-7890 or 123-456-7890
        r'\+\d{1,3}[-.\s]?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}',  # +1 (123) 456-7890
        r'\d{10}',  # 1234567890
    ]
    
    for pattern in phone_patterns:
        matches = re.findall(pattern, text)
        if matches:
            # Clean up the phone number
            phone = re.sub(r'[^\d+]', '', matches[0])
            # Format as (XXX) XXX-XXXX if it's a 10-digit number
            if len(phone) == 10:
                return f"({phone[:3]}) {phone[3:6]}-{phone[6:]}"
            return matches[0]
    return None


def extract_name(text: str, max_lines: int = 10) -> Dict[str, Any]:
    """
    Extract candidate name from resume text with confidence score.
    Only considers the first N lines of the resume for better accuracy.
    
    Args:
        text: Input text to search
        max_lines: Maximum number of lines to consider (default: 10)
        
    Returns:
        Dictionary with 'name' (Optional[str]) and 'confidence' (float 0.0-1.0)
    """
    lines = text.split('\n')
    
    # Common keywords that indicate this is not a name line
    skip_keywords = [
        'resume', 'cv', 'curriculum', 'vitae', 'phone', 'email', 'address',
        'linkedin', 'github', 'portfolio', 'website', 'objective', 'summary',
        'experience', 'education', 'skills', 'projects', 'certifications'
    ]
    
    # Email pattern for rejection
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    
    # Number pattern (reject lines with digits)
    number_pattern = r'\d'
    
    best_candidate = None
    best_confidence = 0.0
    
    # Only consider first N lines
    for i, line in enumerate(lines[:max_lines]):
        line = line.strip()
        
        # Skip empty lines
        if not line:
            continue
        
        # Reject lines containing emails
        if re.search(email_pattern, line):
            continue
        
        # Reject lines containing numbers
        if re.search(number_pattern, line):
            continue
        
        # Reject lines containing common keywords
        line_lower = line.lower()
        if any(keyword in line_lower for keyword in skip_keywords):
            continue
        
        # Reject lines that are too short or too long
        if len(line) < 3 or len(line) > 100:
            continue
        
        # Split into words
        words = line.split()
        
        # Reject if not 2-4 words (typical name length)
        if not (2 <= len(words) <= 4):
            continue
        
        # Calculate confidence score based on multiple factors
        confidence = 0.0
        
        # Factor 1: Capitalization (0-0.4 points)
        capitalized_count = sum(1 for w in words if w and w[0].isupper())
        capitalization_ratio = capitalized_count / len(words)
        confidence += capitalization_ratio * 0.4
        
        # Factor 2: All words capitalized (0-0.2 points)
        if capitalization_ratio == 1.0:
            confidence += 0.2
        
        # Factor 3: Position in document (earlier = higher confidence, 0-0.2 points)
        position_score = max(0, (max_lines - i) / max_lines)
        confidence += position_score * 0.2
        
        # Factor 4: Word length appropriateness (0-0.1 points)
        # Names typically have 2-10 characters per word
        avg_word_length = sum(len(w) for w in words) / len(words)
        if 2 <= avg_word_length <= 10:
            confidence += 0.1
        
        # Factor 5: No special characters except hyphens/apostrophes (0-0.1 points)
        # Allow common name characters: letters, hyphens, apostrophes, spaces
        if re.match(r"^[A-Za-z\s'-]+$", line):
            confidence += 0.1
        
        # Only consider candidates with minimum confidence threshold
        if confidence > best_confidence and confidence >= 0.3:
            best_candidate = line
            best_confidence = confidence
    
    return {
        'name': best_candidate if best_candidate else None,
        'confidence': round(best_confidence, 3)
    }


# ============================================================================
# Date Normalization Functions
# ============================================================================

def normalize_date_range(date_string: str) -> Dict[str, Any]:
    """
    Parse and normalize date range strings to start_year and end_year.
    Handles various date formats commonly found in resumes.
    
    Args:
        date_string: Raw date string (e.g., "Jan 2020 - Present", "2020-2023", "2020")
        
    Returns:
        Dictionary with 'start_year', 'end_year' (int or None), and 'raw_date' (str)
    """
    if not date_string or not date_string.strip():
        return {
            'start_year': None,
            'end_year': None,
            'raw_date': date_string if date_string else None
        }
    
    raw_date = date_string.strip()
    date_lower = raw_date.lower()
    
    # Month names mapping
    month_map = {
        'january': 1, 'jan': 1,
        'february': 2, 'feb': 2,
        'march': 3, 'mar': 3,
        'april': 4, 'apr': 4,
        'may': 5,
        'june': 6, 'jun': 6,
        'july': 7, 'jul': 7,
        'august': 8, 'aug': 8,
        'september': 9, 'sep': 9, 'sept': 9,
        'october': 10, 'oct': 10,
        'november': 11, 'nov': 11,
        'december': 12, 'dec': 12
    }
    
    # Check for "Present", "Current", "Now", etc.
    present_keywords = ['present', 'current', 'now', 'ongoing', 'till date', 'to date']
    is_present = any(keyword in date_lower for keyword in present_keywords)
    
    # Pattern 1: Range with separator (e.g., "2020 - 2023", "Jan 2020 - Present")
    range_patterns = [
        r'(\w+\s+\d{4}|\d{4})\s*[-–—]\s*(\w+\s+\d{4}|\d{4}|present|current|now)',
        r'(\d{1,2}[/-]\d{4})\s*[-–—]\s*(\d{1,2}[/-]\d{4}|present|current|now)',
        r'(\d{4})\s*[-–—]\s*(\d{4}|present|current|now)',
    ]
    
    start_year = None
    end_year = None
    
    for pattern in range_patterns:
        match = re.search(pattern, raw_date, re.IGNORECASE)
        if match:
            start_part = match.group(1).strip()
            end_part = match.group(2).strip().lower()
            
            # Parse start year
            start_year_match = re.search(r'\b(19|20)\d{2}\b', start_part)
            if start_year_match:
                start_year = int(start_year_match.group())
            else:
                # Try month year format
                month_year_match = re.search(r'(\w+)\s+(\d{4})', start_part, re.IGNORECASE)
                if month_year_match:
                    year = int(month_year_match.group(2))
                    start_year = year
            
            # Parse end year
            if is_present or end_part in present_keywords:
                end_year = None
            else:
                end_year_match = re.search(r'\b(19|20)\d{2}\b', end_part)
                if end_year_match:
                    end_year = int(end_year_match.group())
                else:
                    month_year_match = re.search(r'(\w+)\s+(\d{4})', end_part, re.IGNORECASE)
                    if month_year_match:
                        year = int(month_year_match.group(2))
                        end_year = year
            
            break
    
    # Pattern 2: Single year (e.g., "2020", "Graduated 2020")
    if start_year is None:
        year_match = re.search(r'\b(19|20)\d{2}\b', raw_date)
        if year_match:
            start_year = int(year_match.group())
            end_year = start_year  # Same year for single year entries
    
    # Pattern 3: Month/Year format (e.g., "Jan 2020")
    if start_year is None:
        month_year_match = re.search(r'(\w+)\s+(\d{4})', raw_date, re.IGNORECASE)
        if month_year_match:
            year = int(month_year_match.group(2))
            start_year = year
            end_year = year
    
    # Pattern 4: MM/YYYY format (e.g., "01/2020")
    if start_year is None:
        mm_yyyy_match = re.search(r'(\d{1,2})[/-](\d{4})', raw_date)
        if mm_yyyy_match:
            year = int(mm_yyyy_match.group(2))
            start_year = year
            end_year = year
    
    return {
        'start_year': start_year,
        'end_year': end_year,
        'raw_date': raw_date
    }


def extract_education(text: str) -> List[Dict[str, str]]:
    """
    Extract education information from resume text.
    Looks for common education keywords and patterns.
    
    Args:
        text: Input text to search
        
    Returns:
        List of education entries with degree, institution, and year
    """
    education = []
    lines = text.split('\n')
    
    # Keywords that indicate education section
    education_keywords = ['education', 'academic', 'degree', 'university', 'college', 'bachelor', 'master', 'phd', 'diploma']
    
    in_education_section = False
    current_entry = {}
    
    for i, line in enumerate(lines):
        line_lower = line.lower().strip()
        
        # Detect education section
        if any(keyword in line_lower for keyword in education_keywords) and len(line.strip()) < 50:
            in_education_section = True
            continue
        
        if in_education_section:
            # Look for degree patterns
            degree_patterns = [
                r'\b(B\.?S\.?|B\.?A\.?|B\.?E\.?|B\.?Tech|Bachelor|BS|BA|BE)\b',
                r'\b(M\.?S\.?|M\.?A\.?|M\.?E\.?|M\.?Tech|Master|MS|MA|ME|MBA)\b',
                r'\b(Ph\.?D\.?|Doctorate|PhD)\b',
                r'\b(Associate|Diploma|Certificate)\b',
            ]
            
            line_stripped = line.strip()
            if not line_stripped:
                if current_entry:
                    education.append(current_entry)
                    current_entry = {}
                continue
            
            # Check for degree
            for pattern in degree_patterns:
                if re.search(pattern, line_stripped, re.IGNORECASE):
                    if current_entry:
                        education.append(current_entry)
                    current_entry = {'degree': line_stripped}
                    break
            
            # Check for institution (often contains "University", "College", "Institute")
            if re.search(r'\b(University|College|Institute|School|Academy)\b', line_stripped, re.IGNORECASE):
                if 'institution' not in current_entry:
                    current_entry['institution'] = line_stripped
            
            # Check for date patterns (year or date range)
            # Pattern 1: Date range (e.g., "2020 - 2024", "Jan 2020 - Dec 2024")
            date_range_pattern = r'(\w+\s+\d{4}|\d{4})\s*[-–—]\s*(\w+\s+\d{4}|\d{4}|present|current)'
            date_range_match = re.search(date_range_pattern, line_stripped, re.IGNORECASE)
            if date_range_match:
                date_normalized = normalize_date_range(line_stripped)
                current_entry['year'] = line_stripped  # Keep original for backward compatibility
                current_entry['start_year'] = str(date_normalized['start_year']) if date_normalized['start_year'] else None
                current_entry['end_year'] = str(date_normalized['end_year']) if date_normalized['end_year'] else None
                current_entry['raw_date'] = date_normalized['raw_date']
            else:
                # Pattern 2: Single year (e.g., "2020", "Graduated 2020")
                year_match = re.search(r'\b(19|20)\d{2}\b', line_stripped)
                if year_match:
                    year_str = year_match.group()
                    current_entry['year'] = year_str  # Keep original for backward compatibility
                    date_normalized = normalize_date_range(year_str)
                    current_entry['start_year'] = str(date_normalized['start_year']) if date_normalized['start_year'] else None
                    current_entry['end_year'] = str(date_normalized['end_year']) if date_normalized['end_year'] else None
                    current_entry['raw_date'] = date_normalized['raw_date']
            
            # Stop if we hit another major section
            if i < len(lines) - 1:
                next_line = lines[i + 1].strip().lower()
                if any(keyword in next_line for keyword in ['experience', 'work', 'skills', 'projects', 'certifications']):
                    if current_entry:
                        education.append(current_entry)
                    break
    
    if current_entry:
        education.append(current_entry)
    
    return education


# Canonical list of known technical skills for normalization and fallback extraction
# Maps lowercase skill names to their canonical display forms
CANONICAL_SKILLS_MAP = {
    # Programming Languages
    'python': 'Python',
    'java': 'Java',
    'javascript': 'JavaScript', 'js': 'JavaScript',
    'typescript': 'TypeScript', 'ts': 'TypeScript',
    'c++': 'C++',
    'c#': 'C#',
    'c': 'C',
    'go': 'Go', 'golang': 'Go',
    'rust': 'Rust',
    'ruby': 'Ruby',
    'php': 'PHP',
    'swift': 'Swift',
    'kotlin': 'Kotlin',
    'scala': 'Scala',
    'r': 'R',
    'matlab': 'MATLAB',
    'perl': 'Perl',
    'dart': 'Dart',
    'lua': 'Lua',
    'shell': 'Shell',
    'bash': 'Bash',
    'powershell': 'PowerShell',
    
    # Web Technologies
    'html': 'HTML',
    'css': 'CSS',
    'sass': 'SASS',
    'scss': 'SCSS',
    'less': 'Less',
    'bootstrap': 'Bootstrap',
    'tailwind': 'Tailwind CSS',
    'react': 'React',
    'angular': 'Angular',
    'vue': 'Vue.js', 'vue.js': 'Vue.js',
    'svelte': 'Svelte',
    'next.js': 'Next.js',
    'nuxt.js': 'Nuxt.js',
    'gatsby': 'Gatsby',
    'node.js': 'Node.js',
    'express': 'Express.js',
    'django': 'Django',
    'flask': 'Flask',
    'fastapi': 'FastAPI',
    'spring': 'Spring',
    'spring boot': 'Spring Boot',
    'laravel': 'Laravel',
    'symfony': 'Symfony',
    'rails': 'Ruby on Rails', 'ruby on rails': 'Ruby on Rails',
    'asp.net': 'ASP.NET',
    '.net': '.NET', 'dotnet': '.NET',
    'jquery': 'jQuery',
    'webpack': 'Webpack',
    'vite': 'Vite',
    'npm': 'npm',
    'yarn': 'Yarn',
    'pnpm': 'pnpm',
    
    # Databases
    'sql': 'SQL',
    'mysql': 'MySQL',
    'postgresql': 'PostgreSQL', 'postgres': 'PostgreSQL',
    'mongodb': 'MongoDB',
    'redis': 'Redis',
    'cassandra': 'Cassandra',
    'oracle': 'Oracle',
    'sqlite': 'SQLite',
    'dynamodb': 'DynamoDB',
    'elasticsearch': 'Elasticsearch',
    'neo4j': 'Neo4j',
    'couchdb': 'CouchDB',
    'mariadb': 'MariaDB',
    'firebase': 'Firebase',
    'supabase': 'Supabase',
    
    # Cloud & DevOps
    'aws': 'AWS', 'amazon web services': 'AWS',
    'azure': 'Azure',
    'gcp': 'GCP', 'google cloud': 'GCP',
    'docker': 'Docker',
    'kubernetes': 'Kubernetes', 'k8s': 'Kubernetes',
    'terraform': 'Terraform',
    'ansible': 'Ansible',
    'jenkins': 'Jenkins',
    'ci/cd': 'CI/CD', 'cicd': 'CI/CD',
    'git': 'Git',
    'github': 'GitHub',
    'gitlab': 'GitLab',
    'bitbucket': 'Bitbucket',
    'linux': 'Linux',
    'unix': 'Unix',
    'bash scripting': 'Bash Scripting',
    'nginx': 'Nginx',
    'apache': 'Apache',
    'cloudformation': 'CloudFormation',
    'serverless': 'Serverless',
    'lambda': 'AWS Lambda',
    
    # Data Science & ML
    'machine learning': 'Machine Learning', 'ml': 'Machine Learning',
    'deep learning': 'Deep Learning', 'dl': 'Deep Learning',
    'data science': 'Data Science', 'ds': 'Data Science',
    'data analysis': 'Data Analysis',
    'tensorflow': 'TensorFlow',
    'pytorch': 'PyTorch',
    'keras': 'Keras',
    'scikit-learn': 'Scikit-learn', 'scikit learn': 'Scikit-learn',
    'pandas': 'Pandas',
    'numpy': 'NumPy',
    'matplotlib': 'Matplotlib',
    'seaborn': 'Seaborn',
    'jupyter': 'Jupyter',
    'spark': 'Apache Spark', 'apache spark': 'Apache Spark',
    'hadoop': 'Hadoop',
    'tableau': 'Tableau',
    'power bi': 'Power BI',
    'statistics': 'Statistics',
    'nlp': 'NLP', 'natural language processing': 'NLP',
    
    # Mobile Development
    'ios': 'iOS',
    'android': 'Android',
    'react native': 'React Native',
    'flutter': 'Flutter',
    'xamarin': 'Xamarin',
    'ionic': 'Ionic',
    'objective-c': 'Objective-C', 'objective c': 'Objective-C',
    
    # Other Technologies
    'graphql': 'GraphQL',
    'rest api': 'REST API', 'rest': 'REST API',
    'soap': 'SOAP',
    'microservices': 'Microservices',
    'api development': 'API Development',
    'agile': 'Agile',
    'scrum': 'Scrum',
    'kanban': 'Kanban',
    'devops': 'DevOps',
    'tdd': 'TDD', 'test driven development': 'TDD',
    'unit testing': 'Unit Testing',
    'integration testing': 'Integration Testing',
    'selenium': 'Selenium',
    'cypress': 'Cypress',
    'jest': 'Jest',
    'mocha': 'Mocha',
    'chai': 'Chai',
    'pytest': 'pytest',
    'junit': 'JUnit',
    'version control': 'Version Control',
    'project management': 'Project Management',
    'jira': 'Jira',
    'confluence': 'Confluence',
    'slack': 'Slack',
    'trello': 'Trello',
    'blockchain': 'Blockchain',
    'ethereum': 'Ethereum',
    'solidity': 'Solidity',
    'web3': 'Web3',
    'smart contracts': 'Smart Contracts',
}

# Set of all canonical skill names (lowercase) for quick lookup
CANONICAL_SKILLS = set(CANONICAL_SKILLS_MAP.keys())


def _normalize_skill(skill: str) -> str:
    """
    Normalize a skill string to match canonical form.
    
    Args:
        skill: Raw skill string
        
    Returns:
        Normalized skill string matching canonical form, or original with basic formatting if not found
    """
    skill_lower = skill.lower().strip()
    
    # Direct match in canonical skills map
    if skill_lower in CANONICAL_SKILLS_MAP:
        return CANONICAL_SKILLS_MAP[skill_lower]
    
    # Try normalizing separators (underscores, hyphens to spaces)
    skill_normalized = skill_lower.replace('_', ' ').replace('-', ' ')
    if skill_normalized in CANONICAL_SKILLS_MAP:
        return CANONICAL_SKILLS_MAP[skill_normalized]
    
    # Try with extra spaces normalized
    skill_normalized = re.sub(r'\s+', ' ', skill_normalized).strip()
    if skill_normalized in CANONICAL_SKILLS_MAP:
        return CANONICAL_SKILLS_MAP[skill_normalized]
    
    # Return original with basic normalization (strip, title case for multi-word)
    skill_cleaned = skill.strip()
    if ' ' in skill_cleaned or '-' in skill_cleaned:
        # Title case for multi-word skills
        return ' '.join(word.capitalize() for word in re.split(r'[\s-]+', skill_cleaned))
    else:
        # Capitalize single words
        return skill_cleaned.capitalize()


def extract_skills(text: str) -> List[str]:
    """
    Extract skills from resume text.
    Prioritizes Skills section extraction, falls back to global scan if section missing.
    Returns deduplicated, normalized, and alphabetically sorted skills.
    
    Args:
        text: Input text to search
        
    Returns:
        List of normalized skills, sorted alphabetically
    """
    skills = []
    lines = text.split('\n')
    
    # Keywords that indicate skills section
    skills_keywords = [
        'skills', 'technical skills', 'core competencies', 'competencies',
        'expertise', 'proficiencies', 'technologies', 'tools & technologies',
        'tools and technologies', 'technical expertise'
    ]
    
    # Keywords that indicate end of skills section
    section_end_keywords = [
        'experience', 'work experience', 'employment', 'education',
        'projects', 'certifications', 'awards', 'publications', 'references'
    ]
    
    in_skills_section = False
    skills_section_found = False
    
    # First pass: Try to extract from Skills section
    for i, line in enumerate(lines):
        line_lower = line.lower().strip()
        line_stripped = line.strip()
        
        # Detect skills section header
        if any(keyword in line_lower for keyword in skills_keywords) and len(line_stripped) < 80:
            in_skills_section = True
            skills_section_found = True
            continue
        
        if in_skills_section:
            # Empty line might indicate end of skills section (if we already found skills)
            if not line_stripped:
                if skills:
                    break
                continue
            
            # Stop if we hit another major section
            if any(keyword in line_lower for keyword in section_end_keywords):
                break
            
            # Extract skills from line (split by common delimiters)
            skill_items = re.split(r'[,;•·|/]', line_stripped)
            for item in skill_items:
                skill = item.strip()
                # Filter out very short items and common non-skill words
                if skill and len(skill) > 1:
                    # Skip common non-skill words
                    skip_words = ['and', 'or', 'with', 'including', 'such as', 'etc', 'etc.']
                    if skill.lower() not in skip_words:
                        skills.append(skill)
    
    # Second pass: Fallback to global scan only if Skills section was not found
    if not skills_section_found:
        text_lower = text.lower()
        
        # Scan for canonical skills in entire text
        for skill_key, canonical_form in CANONICAL_SKILLS_MAP.items():
            # Use word boundary matching to avoid partial matches
            # Handle special characters in skill names
            escaped_key = re.escape(skill_key)
            pattern = r'\b' + escaped_key + r'\b'
            if re.search(pattern, text_lower):
                skills.append(canonical_form)
    
    # Normalize all extracted skills
    normalized_skills = [_normalize_skill(skill) for skill in skills]
    
    # Deduplicate (case-insensitive)
    seen = set()
    unique_skills = []
    for skill in normalized_skills:
        skill_lower = skill.lower()
        if skill_lower not in seen:
            seen.add(skill_lower)
            unique_skills.append(skill)
    
    # Sort alphabetically (case-insensitive)
    unique_skills.sort(key=lambda x: x.lower())
    
    return unique_skills


def extract_experience(text: str) -> List[Dict[str, str]]:
    """
    Extract work experience from resume text.
    Looks for experience/work section and extracts job titles, companies, and dates.
    
    Args:
        text: Input text to search
        
    Returns:
        List of experience entries
    """
    experience = []
    lines = text.split('\n')
    
    # Keywords that indicate experience section
    experience_keywords = ['experience', 'work experience', 'employment', 'professional experience', 'career']
    
    in_experience_section = False
    current_entry = {}
    
    for i, line in enumerate(lines):
        line_lower = line.lower().strip()
        
        # Detect experience section
        if any(keyword in line_lower for keyword in experience_keywords) and len(line.strip()) < 50:
            in_experience_section = True
            continue
        
        if in_experience_section:
            line_stripped = line.strip()
            if not line_stripped:
                if current_entry:
                    experience.append(current_entry)
                    current_entry = {}
                continue
            
            # Check for date patterns (e.g., "Jan 2020 - Present", "2020-2023")
            date_pattern = r'(\w+\s+\d{4}|\d{4})\s*[-–—]\s*(\w+\s+\d{4}|\d{4}|Present|Current)'
            date_match = re.search(date_pattern, line_stripped, re.IGNORECASE)
            if date_match:
                if current_entry:
                    experience.append(current_entry)
                # Normalize the date range
                date_normalized = normalize_date_range(line_stripped)
                current_entry = {
                    'duration': line_stripped,  # Keep original for backward compatibility
                    'start_year': str(date_normalized['start_year']) if date_normalized['start_year'] else None,
                    'end_year': str(date_normalized['end_year']) if date_normalized['end_year'] else None,
                    'raw_date': date_normalized['raw_date']
                }
                continue
            
            # Check for job title (often appears before company)
            if not current_entry.get('title'):
                # Look for common job title indicators
                title_indicators = ['Engineer', 'Developer', 'Manager', 'Analyst', 'Specialist', 
                                  'Consultant', 'Director', 'Lead', 'Senior', 'Junior', 'Intern']
                if any(indicator in line_stripped for indicator in title_indicators):
                    current_entry['title'] = line_stripped
                    continue
            
            # Check for company name (often contains "Inc", "LLC", "Corp", or is standalone)
            if not current_entry.get('company'):
                if re.search(r'\b(Inc|LLC|Corp|Ltd|Company|Technologies|Solutions)\b', line_stripped, re.IGNORECASE):
                    current_entry['company'] = line_stripped
                elif current_entry.get('title') and len(line_stripped) > 3:
                    # Company might be on next line after title
                    current_entry['company'] = line_stripped
            
            # Stop if we hit another major section
            if i < len(lines) - 1:
                next_line = lines[i + 1].strip().lower()
                if any(keyword in next_line for keyword in ['education', 'skills', 'projects', 'certifications']):
                    if current_entry:
                        experience.append(current_entry)
                    break
    
    if current_entry:
        experience.append(current_entry)
    
    return experience


def extract_projects(text: str) -> List[Dict[str, str]]:
    """
    Extract projects from resume text.
    Looks for projects section and extracts project names and descriptions.
    
    Args:
        text: Input text to search
        
    Returns:
        List of project entries
    """
    projects = []
    lines = text.split('\n')
    
    # Keywords that indicate projects section
    project_keywords = ['projects', 'project', 'portfolio', 'personal projects']
    
    in_projects_section = False
    current_project = {}
    
    for i, line in enumerate(lines):
        line_lower = line.lower().strip()
        
        # Detect projects section
        if any(keyword in line_lower for keyword in project_keywords) and len(line.strip()) < 50:
            in_projects_section = True
            continue
        
        if in_projects_section:
            line_stripped = line.strip()
            if not line_stripped:
                if current_project:
                    projects.append(current_project)
                    current_project = {}
                continue
            
            # Stop if we hit another major section
            if any(keyword in line_lower for keyword in ['experience', 'education', 'skills', 'certifications', 'work']):
                if current_project:
                    projects.append(current_project)
                break
            
            # Project name is often the first non-empty line or a line with specific formatting
            if not current_project.get('name'):
                # Check if line looks like a project name (short, might be bold/heading)
                if len(line_stripped) < 100 and not line_stripped[0].isdigit():
                    current_project['name'] = line_stripped
            else:
                # Subsequent lines are likely description
                if 'description' not in current_project:
                    current_project['description'] = line_stripped
                else:
                    current_project['description'] += ' ' + line_stripped
    
    if current_project:
        projects.append(current_project)
    
    return projects


# ============================================================================
# Resume Assembly Function
# ============================================================================

def assemble_resume_data(text: str) -> Dict[str, Any]:
    """
    Assemble resume data dictionary by extracting all information from text.
    This is a pure function that takes text and returns structured data.
    
    Args:
        text: Raw text content from the resume
        
    Returns:
        Dictionary containing extracted resume information
    """
    # Extract name with confidence score
    name_result = extract_name(text)
    
    return {
        'name': name_result['name'],
        'email': extract_email(text),
        'phone': extract_phone(text),
        'education': extract_education(text),
        'skills': extract_skills(text),
        'experience': extract_experience(text),
        'projects': extract_projects(text)
    }


# ============================================================================
# Schema Normalization and Validation Functions
# ============================================================================

def normalize_to_schema(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalize extracted data to match the canonical ResumeSchema structure.
    Ensures all required fields exist with appropriate defaults.
    
    Args:
        data: Raw extracted resume data
        
    Returns:
        Normalized resume data matching the schema
    """
    normalized = {}
    
    # Ensure all top-level fields exist
    for field_name, field_spec in RESUME_SCHEMA.items():
        if field_name in data:
            value = data[field_name]
        else:
            value = field_spec['default']
        
        field_type = field_spec['type']
        
        # Normalize list of dictionaries fields
        if field_type == TYPE_LIST_DICT:
            if not isinstance(value, list):
                value = []
            
            # Normalize each item in the list
            item_schema = field_spec.get('item_schema', {})
            normalized_items = []
            for item in value:
                if not isinstance(item, dict):
                    continue
                
                normalized_item = {}
                for item_field, item_spec in item_schema.items():
                    if item_field in item:
                        item_value = item[item_field]
                        # Ensure string or None for optional string fields
                        if item_spec['type'] == TYPE_OPTIONAL_STR:
                            normalized_item[item_field] = str(item_value) if item_value is not None else None
                        else:
                            normalized_item[item_field] = item_value
                    else:
                        normalized_item[item_field] = item_spec['default']
                normalized_items.append(normalized_item)
            
            normalized[field_name] = normalized_items
        
        # Normalize list of strings
        elif field_type == TYPE_LIST_STR:
            if not isinstance(value, list):
                value = []
            # Ensure all items are strings
            normalized[field_name] = [str(item) for item in value if item is not None]
        
        # Normalize optional string fields
        elif field_type == TYPE_OPTIONAL_STR:
            if value is None:
                normalized[field_name] = None
            else:
                normalized[field_name] = str(value)
        
        else:
            normalized[field_name] = value
    
    return normalized


def validate_schema(data: Dict[str, Any]) -> None:
    """
    Validate that the data structure matches the ResumeSchema and all types are correct.
    Raises ValueError with clear error messages if validation fails.
    
    Args:
        data: Resume data dictionary to validate
        
    Raises:
        ValueError: If schema validation fails with detailed error message
    """
    errors = []
    
    # Check that all required fields exist
    for field_name, field_spec in RESUME_SCHEMA.items():
        if field_name not in data:
            errors.append(f"Missing required field: '{field_name}' ({field_spec['description']})")
            continue
        
        value = data[field_name]
        expected_type = field_spec['type']
        
        # Validate type using isinstance checks
        # Check for Optional[str] (can be None or str)
        if expected_type == TYPE_OPTIONAL_STR:
            if value is not None and not isinstance(value, str):
                errors.append(
                    f"Field '{field_name}': expected Optional[str] (None or str), got {type(value).__name__}"
                )
        
        # Check for List[str]
        elif expected_type == TYPE_LIST_STR:
            if not isinstance(value, list):
                errors.append(
                    f"Field '{field_name}': expected List[str], got {type(value).__name__}"
                )
            else:
                # Validate list items
                for i, item in enumerate(value):
                    if not isinstance(item, str):
                        errors.append(
                            f"Field '{field_name}[{i}]': expected str, got {type(item).__name__}"
                        )
        
        # Check for List[Dict[str, str]]
        elif expected_type == TYPE_LIST_DICT:
            if not isinstance(value, list):
                errors.append(
                    f"Field '{field_name}': expected List[Dict[str, str]], got {type(value).__name__}"
                )
            else:
                # Validate list items
                item_schema = field_spec.get('item_schema', {})
                for i, item in enumerate(value):
                    if not isinstance(item, dict):
                        errors.append(
                            f"Field '{field_name}[{i}]': expected Dict[str, str], got {type(item).__name__}"
                        )
                        continue
                    
                    # Validate item fields exist and have correct types
                    for item_field, item_spec in item_schema.items():
                        if item_field not in item:
                            errors.append(
                                f"Field '{field_name}[{i}].{item_field}': missing required field"
                            )
                        else:
                            item_value = item[item_field]
                            item_type = item_spec['type']
                            # Check for Optional[str] in item schema
                            if item_type == TYPE_OPTIONAL_STR:
                                if item_value is not None and not isinstance(item_value, str):
                                    errors.append(
                                        f"Field '{field_name}[{i}].{item_field}': expected Optional[str] "
                                        f"(None or str), got {type(item_value).__name__}"
                                    )
    
    if errors:
        error_message = "Schema validation failed:\n" + "\n".join(f"  - {error}" for error in errors)
        raise ValueError(error_message)


def validate_json(data: Dict[str, Any]) -> bool:
    """
    Validate that the extracted data matches the ResumeSchema and can be serialized to JSON.
    This function performs both schema validation and JSON serialization validation.
    
    Args:
        data: Dictionary to validate
        
    Returns:
        True if valid, raises exception otherwise
        
    Raises:
        ValueError: If schema validation fails
        TypeError: If JSON serialization fails
    """
    # First validate schema structure and types
    validate_schema(data)
    
    # Then validate JSON serialization
    try:
        json.dumps(data, indent=2)
        return True
    except (TypeError, ValueError) as e:
        raise ValueError(f"JSON serialization failed: {e}")


# ============================================================================
# Main Parsing Function
# ============================================================================

def parse_resume(file_path: str) -> Dict[str, Any]:
    """
    Main function to parse a resume file and extract structured information.
    Orchestrates file reading, text extraction, data assembly, and normalization.
    
    Args:
        file_path: Path to the resume file (PDF or DOCX)
        
    Returns:
        Dictionary containing extracted and normalized resume information
    """
    # Read and validate file
    read_resume_file(file_path)
    
    # Extract raw text from file
    text = extract_text(file_path)
    
    # Assemble resume data from text
    resume_data = assemble_resume_data(text)
    
    # Normalize to schema to ensure all fields exist with proper structure
    normalized_data = normalize_to_schema(resume_data)
    
    return normalized_data


# ============================================================================
# CLI Entry Point
# ============================================================================

def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(
        description='Extract structured information from PDF or DOCX resume files'
    )
    parser.add_argument(
        'resume_file',
        type=str,
        help='Path to the resume file (PDF or DOCX)'
    )
    parser.add_argument(
        '-o', '--output',
        type=str,
        default='resume.json',
        help='Output JSON file path (default: resume.json)'
    )
    
    args = parser.parse_args()
    
    try:
        # Parse the resume
        print(f"Parsing resume: {args.resume_file}")
        resume_data = parse_resume(args.resume_file)
        
        # Validate JSON
        validate_json(resume_data)
        
        # Write to output file
        output_path = Path(args.output)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(resume_data, f, indent=2, ensure_ascii=False)
        
        print(f"Successfully extracted resume data to {output_path}")
        print(f"\nExtracted Information:")
        print(f"  Name: {resume_data.get('name', 'Not found')}")
        print(f"  Email: {resume_data.get('email', 'Not found')}")
        print(f"  Phone: {resume_data.get('phone', 'Not found')}")
        print(f"  Education entries: {len(resume_data.get('education', []))}")
        print(f"  Skills: {len(resume_data.get('skills', []))}")
        print(f"  Experience entries: {len(resume_data.get('experience', []))}")
        print(f"  Projects: {len(resume_data.get('projects', []))}")
        
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()

