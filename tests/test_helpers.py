"""
Tests for utility helper functions.
"""

import pytest
from src.utils.helpers import (
    sanitize_linkedin_url,
    extract_linkedin_id,
    format_phone_number,
    validate_email,
    parse_name,
    normalize_company_name
)


class TestSanitizeLinkedInUrl:
    """Tests for sanitize_linkedin_url function."""
    
    def test_full_url(self):
        """Test with full LinkedIn URL."""
        url = "https://www.linkedin.com/in/johndoe"
        result = sanitize_linkedin_url(url)
        assert result == "https://www.linkedin.com/in/johndoe"
    
    def test_url_with_trailing_slash(self):
        """Test URL with trailing slash."""
        url = "https://www.linkedin.com/in/johndoe/"
        result = sanitize_linkedin_url(url)
        assert result == "https://www.linkedin.com/in/johndoe"
    
    def test_url_without_https(self):
        """Test URL without https."""
        url = "linkedin.com/in/johndoe"
        result = sanitize_linkedin_url(url)
        assert result == "https://www.linkedin.com/in/johndoe"
    
    def test_just_id(self):
        """Test with just LinkedIn ID."""
        url = "johndoe"
        result = sanitize_linkedin_url(url)
        assert result == "https://www.linkedin.com/in/johndoe"
    
    def test_empty_url(self):
        """Test with empty URL."""
        assert sanitize_linkedin_url("") is None
        assert sanitize_linkedin_url(None) is None


class TestExtractLinkedInId:
    """Tests for extract_linkedin_id function."""
    
    def test_extract_from_full_url(self):
        """Test extracting ID from full URL."""
        url = "https://www.linkedin.com/in/johndoe"
        assert extract_linkedin_id(url) == "johndoe"
    
    def test_extract_from_url_with_params(self):
        """Test extracting ID from URL with query parameters."""
        url = "https://www.linkedin.com/in/johndoe?trk=something"
        assert extract_linkedin_id(url) == "johndoe"
    
    def test_extract_just_id(self):
        """Test with just the ID."""
        assert extract_linkedin_id("johndoe") == "johndoe"
    
    def test_id_with_numbers(self):
        """Test ID with numbers."""
        url = "https://www.linkedin.com/in/john-doe-123"
        assert extract_linkedin_id(url) == "john-doe-123"


class TestFormatPhoneNumber:
    """Tests for format_phone_number function."""
    
    def test_10_digit_number(self):
        """Test formatting 10 digit number."""
        phone = "9876543210"
        result = format_phone_number(phone)
        assert result == "+919876543210"
    
    def test_number_with_spaces(self):
        """Test number with spaces."""
        phone = "98765 43210"
        result = format_phone_number(phone)
        assert result == "+919876543210"
    
    def test_number_with_country_code(self):
        """Test number already with country code."""
        phone = "919876543210"
        result = format_phone_number(phone)
        assert result == "+919876543210"
    
    def test_number_with_plus(self):
        """Test number with plus sign."""
        phone = "+919876543210"
        result = format_phone_number(phone)
        assert result == "+919876543210"
    
    def test_empty_phone(self):
        """Test empty phone number."""
        assert format_phone_number("") is None
        assert format_phone_number(None) is None


class TestValidateEmail:
    """Tests for validate_email function."""
    
    def test_valid_email(self):
        """Test valid email addresses."""
        assert validate_email("test@example.com") is True
        assert validate_email("user.name@domain.co.in") is True
        assert validate_email("user+tag@example.org") is True
    
    def test_invalid_email(self):
        """Test invalid email addresses."""
        assert validate_email("invalid") is False
        assert validate_email("missing@domain") is False
        assert validate_email("@nodomain.com") is False
    
    def test_empty_email(self):
        """Test empty email."""
        assert validate_email("") is False
        assert validate_email(None) is False


class TestParseName:
    """Tests for parse_name function."""
    
    def test_full_name(self):
        """Test parsing full name."""
        result = parse_name("John Michael Doe")
        assert result['first_name'] == "John"
        assert result['last_name'] == "Doe"
        assert result['middle_name'] == "Michael"
    
    def test_two_part_name(self):
        """Test parsing two-part name."""
        result = parse_name("John Doe")
        assert result['first_name'] == "John"
        assert result['last_name'] == "Doe"
        assert result['middle_name'] == ""
    
    def test_single_name(self):
        """Test parsing single name."""
        result = parse_name("John")
        assert result['first_name'] == "John"
        assert result['last_name'] == ""


class TestNormalizeCompanyName:
    """Tests for normalize_company_name function."""
    
    def test_remove_pvt_ltd(self):
        """Test removing Pvt. Ltd."""
        assert normalize_company_name("Google Pvt. Ltd.") == "Google"
    
    def test_remove_inc(self):
        """Test removing Inc."""
        assert normalize_company_name("Apple Inc.") == "Apple"
    
    def test_no_suffix(self):
        """Test company without suffix."""
        assert normalize_company_name("Microsoft") == "Microsoft"
    
    def test_empty_company(self):
        """Test empty company name."""
        assert normalize_company_name("") == ""
        assert normalize_company_name(None) == ""
