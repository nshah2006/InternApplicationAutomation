# Resume Parser Tests

This directory contains pytest-based tests for the resume parser module.

## Running Tests

To run all tests:
```bash
pytest
```

To run with verbose output:
```bash
pytest -v
```

To run a specific test file:
```bash
pytest tests/test_resume_parser.py
```

To run a specific test class:
```bash
pytest tests/test_resume_parser.py::TestPDFParsing
```

To run a specific test:
```bash
pytest tests/test_resume_parser.py::TestPDFParsing::test_extract_text_from_pdf_file_not_found
```

## Test Coverage

The test suite includes:

- **PDF Parsing Tests**: Tests for PDF file text extraction
- **DOCX Parsing Tests**: Tests for DOCX file text extraction
- **Schema Validation Tests**: Tests for JSON schema validation and normalization
- **Data Extraction Tests**: Tests for individual extraction functions (email, phone, name)
- **Date Normalization Tests**: Tests for date range parsing and normalization
- **File Reading Tests**: Tests for file validation
- **Integration Tests**: Tests for the full parse_resume workflow

## Requirements

Install test dependencies:
```bash
pip install -r requirements.txt
```

This will install:
- pytest (for testing framework)
- PyPDF2 (for PDF parsing)
- python-docx (for DOCX parsing)

