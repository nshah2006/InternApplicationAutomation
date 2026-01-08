"""
Pytest tests for resume_parser module.
Tests PDF/DOCX parsing, schema validation, and core functionality.
"""

import pytest
import json
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, patch, mock_open
import sys

# Add parent directory to path to import resume_parser
sys.path.insert(0, str(Path(__file__).parent.parent))

from resume_parser import (
    extract_text,
    read_resume_file,
    validate_schema,
    normalize_to_schema,
    assemble_resume_data,
    extract_name,
    extract_email,
    extract_phone,
    normalize_date_range,
    RESUME_SCHEMA
)


class TestPDFParsing:
    """Tests for PDF file parsing."""
    
    def test_extract_text_from_pdf_file_not_found(self):
        """Test that PDF extraction raises FileNotFoundError for non-existent file."""
        with pytest.raises(FileNotFoundError):
            extract_text("nonexistent.pdf")
    
    def test_extract_text_from_pdf_invalid_format(self):
        """Test that PDF extraction raises ValueError for invalid file format."""
        with pytest.raises(ValueError, match="Unsupported file format"):
            extract_text("test.txt")
    
    @patch('resume_parser._extract_text_from_pdf')
    def test_extract_text_calls_pdf_extractor(self, mock_pdf_extract):
        """Test that extract_text calls PDF extractor for .pdf files."""
        mock_pdf_extract.return_value = "Sample PDF text"
        
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp_file:
            tmp_path = tmp_file.name
        
        try:
            # Mock the file existence check
            with patch('pathlib.Path.exists', return_value=True):
                result = extract_text(tmp_path)
                assert result == "Sample PDF text"
                mock_pdf_extract.assert_called_once_with(tmp_path)
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
    
    @patch('resume_parser.PyPDF2')
    def test_pdf_extraction_with_mock(self, mock_pypdf2):
        """Test PDF extraction with mocked PyPDF2."""
        # Setup mock
        mock_reader = Mock()
        mock_page = Mock()
        mock_page.extract_text.return_value = "Page 1 text\n"
        mock_reader.pages = [mock_page]
        mock_pypdf2.PdfReader.return_value = mock_reader
        
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp_file:
            tmp_path = tmp_file.name
        
        try:
            with patch('pathlib.Path.exists', return_value=True):
                with patch('builtins.open', mock_open(read_data=b'PDF content')):
                    from resume_parser import _extract_text_from_pdf
                    result = _extract_text_from_pdf(tmp_path)
                    assert "Page 1 text" in result
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
    
    def test_pdf_extraction_missing_library(self):
        """Test that PDF extraction raises ImportError when PyPDF2 is missing."""
        with patch('builtins.__import__', side_effect=ImportError("No module named 'PyPDF2'")):
            with pytest.raises(ImportError, match="PyPDF2 is required"):
                from resume_parser import _extract_text_from_pdf
                _extract_text_from_pdf("test.pdf")


class TestDOCXParsing:
    """Tests for DOCX file parsing."""
    
    def test_extract_text_from_docx_file_not_found(self):
        """Test that DOCX extraction raises FileNotFoundError for non-existent file."""
        with pytest.raises(FileNotFoundError):
            extract_text("nonexistent.docx")
    
    @patch('resume_parser._extract_text_from_docx')
    def test_extract_text_calls_docx_extractor(self, mock_docx_extract):
        """Test that extract_text calls DOCX extractor for .docx files."""
        mock_docx_extract.return_value = "Sample DOCX text"
        
        with tempfile.NamedTemporaryFile(suffix='.docx', delete=False) as tmp_file:
            tmp_path = tmp_file.name
        
        try:
            with patch('pathlib.Path.exists', return_value=True):
                result = extract_text(tmp_path)
                assert result == "Sample DOCX text"
                mock_docx_extract.assert_called_once_with(tmp_path)
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
    
    @patch('resume_parser.Document')
    def test_docx_extraction_with_mock(self, mock_document):
        """Test DOCX extraction with mocked python-docx."""
        # Setup mock
        mock_doc = Mock()
        mock_para1 = Mock()
        mock_para1.text = "Paragraph 1"
        mock_para2 = Mock()
        mock_para2.text = "Paragraph 2"
        mock_doc.paragraphs = [mock_para1, mock_para2]
        mock_document.return_value = mock_doc
        
        with tempfile.NamedTemporaryFile(suffix='.docx', delete=False) as tmp_file:
            tmp_path = tmp_file.name
        
        try:
            with patch('pathlib.Path.exists', return_value=True):
                from resume_parser import _extract_text_from_docx
                result = _extract_text_from_docx(tmp_path)
                assert "Paragraph 1" in result
                assert "Paragraph 2" in result
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
    
    def test_docx_extraction_missing_library(self):
        """Test that DOCX extraction raises ImportError when python-docx is missing."""
        with patch('builtins.__import__', side_effect=ImportError("No module named 'docx'")):
            with pytest.raises(ImportError, match="python-docx is required"):
                from resume_parser import _extract_text_from_docx
                _extract_text_from_docx("test.docx")


class TestSchemaValidation:
    """Tests for JSON schema validation."""
    
    def test_validate_schema_valid_data(self):
        """Test schema validation with valid resume data."""
        valid_data = {
            'name': 'John Doe',
            'email': 'john@example.com',
            'phone': '(123) 456-7890',
            'education': [
                {
                    'degree': 'BS Computer Science',
                    'institution': 'University of Test',
                    'year': '2020',
                    'start_year': '2020',
                    'end_year': '2020',
                    'raw_date': '2020'
                }
            ],
            'skills': ['Python', 'Java'],
            'experience': [
                {
                    'title': 'Software Engineer',
                    'company': 'Test Corp',
                    'duration': '2020 - Present',
                    'start_year': '2020',
                    'end_year': None,
                    'raw_date': '2020 - Present'
                }
            ],
            'projects': [
                {
                    'name': 'Test Project',
                    'description': 'A test project'
                }
            ]
        }
        
        # Should not raise any exception
        validate_schema(valid_data)
    
    def test_validate_schema_missing_required_field(self):
        """Test schema validation fails when required field is missing."""
        invalid_data = {
            'name': 'John Doe',
            # Missing email
            'phone': '(123) 456-7890',
            'education': [],
            'skills': [],
            'experience': [],
            'projects': []
        }
        
        with pytest.raises(ValueError, match="Missing required field"):
            validate_schema(invalid_data)
    
    def test_validate_schema_wrong_type(self):
        """Test schema validation fails when field has wrong type."""
        invalid_data = {
            'name': 'John Doe',
            'email': 'john@example.com',
            'phone': '(123) 456-7890',
            'education': [],
            'skills': 'not a list',  # Should be a list
            'experience': [],
            'projects': []
        }
        
        with pytest.raises(ValueError, match="expected List\[str\]"):
            validate_schema(invalid_data)
    
    def test_validate_schema_invalid_education_item(self):
        """Test schema validation fails when education item has wrong structure."""
        invalid_data = {
            'name': 'John Doe',
            'email': 'john@example.com',
            'phone': '(123) 456-7890',
            'education': [
                'not a dict'  # Should be a dict
            ],
            'skills': [],
            'experience': [],
            'projects': []
        }
        
        with pytest.raises(ValueError, match="expected Dict\[str, str\]"):
            validate_schema(invalid_data)
    
    def test_validate_schema_skills_not_strings(self):
        """Test schema validation fails when skills list contains non-strings."""
        invalid_data = {
            'name': 'John Doe',
            'email': 'john@example.com',
            'phone': '(123) 456-7890',
            'education': [],
            'skills': ['Python', 123],  # Contains non-string
            'experience': [],
            'projects': []
        }
        
        with pytest.raises(ValueError, match="expected str"):
            validate_schema(invalid_data)
    
    def test_normalize_to_schema_adds_missing_fields(self):
        """Test that normalize_to_schema adds missing fields with defaults."""
        incomplete_data = {
            'name': 'John Doe',
            'email': 'john@example.com'
            # Missing other fields
        }
        
        normalized = normalize_to_schema(incomplete_data)
        
        assert normalized['name'] == 'John Doe'
        assert normalized['email'] == 'john@example.com'
        assert normalized['phone'] is None
        assert normalized['education'] == []
        assert normalized['skills'] == []
        assert normalized['experience'] == []
        assert normalized['projects'] == []
    
    def test_normalize_to_schema_normalizes_education_items(self):
        """Test that normalize_to_schema normalizes education items."""
        data = {
            'name': 'John Doe',
            'email': 'john@example.com',
            'phone': None,
            'education': [
                {
                    'degree': 'BS Computer Science'
                    # Missing other fields
                }
            ],
            'skills': [],
            'experience': [],
            'projects': []
        }
        
        normalized = normalize_to_schema(data)
        
        assert len(normalized['education']) == 1
        edu = normalized['education'][0]
        assert edu['degree'] == 'BS Computer Science'
        assert edu['institution'] is None
        assert edu['year'] is None
        assert edu['start_year'] is None
        assert edu['end_year'] is None
        assert edu['raw_date'] is None


class TestDataExtraction:
    """Tests for data extraction functions."""
    
    def test_extract_email_valid(self):
        """Test email extraction from text."""
        text = "Contact me at john.doe@example.com for more info"
        result = extract_email(text)
        assert result == "john.doe@example.com"
    
    def test_extract_email_not_found(self):
        """Test email extraction when no email is present."""
        text = "This text has no email address"
        result = extract_email(text)
        assert result is None
    
    def test_extract_phone_valid(self):
        """Test phone extraction from text."""
        text = "Call me at (123) 456-7890"
        result = extract_phone(text)
        assert result == "(123) 456-7890"
    
    def test_extract_phone_not_found(self):
        """Test phone extraction when no phone is present."""
        text = "This text has no phone number"
        result = extract_phone(text)
        assert result is None
    
    def test_extract_name_with_confidence(self):
        """Test name extraction returns name and confidence."""
        text = "John Doe\nSoftware Engineer\nEmail: john@example.com"
        result = extract_name(text)
        
        assert isinstance(result, dict)
        assert 'name' in result
        assert 'confidence' in result
        assert result['name'] == "John Doe"
        assert 0.0 <= result['confidence'] <= 1.0
    
    def test_assemble_resume_data(self):
        """Test that assemble_resume_data creates proper structure."""
        text = """
        John Doe
        john.doe@example.com
        (123) 456-7890
        
        Skills: Python, Java
        
        Experience:
        2020 - Present: Software Engineer at Test Corp
        """
        
        result = assemble_resume_data(text)
        
        assert 'name' in result
        assert 'email' in result
        assert 'phone' in result
        assert 'education' in result
        assert 'skills' in result
        assert 'experience' in result
        assert 'projects' in result


class TestDateNormalization:
    """Tests for date normalization."""
    
    def test_normalize_date_range_present(self):
        """Test date normalization with Present end date."""
        result = normalize_date_range("2020 - Present")
        assert result['start_year'] == 2020
        assert result['end_year'] is None
        assert result['raw_date'] == "2020 - Present"
    
    def test_normalize_date_range_complete(self):
        """Test date normalization with complete date range."""
        result = normalize_date_range("2020 - 2023")
        assert result['start_year'] == 2020
        assert result['end_year'] == 2023
        assert result['raw_date'] == "2020 - 2023"
    
    def test_normalize_date_range_month_year(self):
        """Test date normalization with month/year format."""
        result = normalize_date_range("Jan 2020 - Dec 2023")
        assert result['start_year'] == 2020
        assert result['end_year'] == 2023
        assert result['raw_date'] == "Jan 2020 - Dec 2023"
    
    def test_normalize_date_range_single_year(self):
        """Test date normalization with single year."""
        result = normalize_date_range("2020")
        assert result['start_year'] == 2020
        assert result['end_year'] == 2020
        assert result['raw_date'] == "2020"
    
    def test_normalize_date_range_empty(self):
        """Test date normalization with empty string."""
        result = normalize_date_range("")
        assert result['start_year'] is None
        assert result['end_year'] is None
        assert result['raw_date'] is None
    
    def test_normalize_date_range_current(self):
        """Test date normalization with Current keyword."""
        result = normalize_date_range("2020 - Current")
        assert result['start_year'] == 2020
        assert result['end_year'] is None
        assert result['raw_date'] == "2020 - Current"


class TestFileReading:
    """Tests for file reading functions."""
    
    def test_read_resume_file_exists(self):
        """Test reading an existing file."""
        with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
            tmp_path = tmp_file.name
        
        try:
            result = read_resume_file(tmp_path)
            assert isinstance(result, Path)
            assert str(result) == tmp_path
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
    
    def test_read_resume_file_not_found(self):
        """Test reading a non-existent file raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            read_resume_file("nonexistent_file.pdf")


class TestParseResume:
    """Tests for the main parse_resume function."""
    
    @patch('resume_parser.extract_text')
    @patch('resume_parser.read_resume_file')
    def test_parse_resume_integration(self, mock_read_file, mock_extract_text):
        """Test the full parse_resume workflow."""
        # Setup mocks
        mock_read_file.return_value = Path("test.pdf")
        mock_extract_text.return_value = """
        John Doe
        john.doe@example.com
        (123) 456-7890
        
        Education:
        BS Computer Science
        University of Test
        2020
        
        Skills: Python, Java
        
        Experience:
        2020 - Present: Software Engineer at Test Corp
        """
        
        from resume_parser import parse_resume
        
        result = parse_resume("test.pdf")
        
        # Verify structure
        assert 'name' in result
        assert 'email' in result
        assert 'phone' in result
        assert 'education' in result
        assert 'skills' in result
        assert 'experience' in result
        assert 'projects' in result
        
        # Verify mocks were called
        mock_read_file.assert_called_once_with("test.pdf")
        mock_extract_text.assert_called_once_with("test.pdf")
    
    def test_parse_resume_file_not_found(self):
        """Test parse_resume raises FileNotFoundError for non-existent file."""
        from resume_parser import parse_resume
        
        with pytest.raises(FileNotFoundError):
            parse_resume("nonexistent.pdf")

