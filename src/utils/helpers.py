"""
Helper utility functions for Alumni Management System.
"""

import re
from typing import Optional


def sanitize_linkedin_url(url: str) -> Optional[str]:
    """
    Sanitize and normalize LinkedIn profile URL.
    
    Args:
        url: Raw LinkedIn URL
        
    Returns:
        Normalized LinkedIn URL or None if invalid
    """
    if not url:
        return None
    
    url = url.strip()
    
    # Handle common formats
    patterns = [
        r'https?://(?:www\.)?linkedin\.com/in/([a-zA-Z0-9_-]+)',
        r'linkedin\.com/in/([a-zA-Z0-9_-]+)',
        r'^([a-zA-Z0-9_-]+)$'  # Just the ID
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            linkedin_id = match.group(1).rstrip('/')
            return f"https://www.linkedin.com/in/{linkedin_id}"
    
    return None


def extract_linkedin_id(url: str) -> Optional[str]:
    """
    Extract LinkedIn ID from URL.
    
    Args:
        url: LinkedIn URL or ID
        
    Returns:
        LinkedIn ID or None if not found
    """
    if not url:
        return None
    
    url = url.strip()
    
    # Remove trailing slashes and query params
    url = url.rstrip('/').split('?')[0]
    
    # Try to extract ID
    match = re.search(r'linkedin\.com/in/([a-zA-Z0-9_-]+)', url)
    if match:
        return match.group(1)
    
    # If it looks like just an ID
    if re.match(r'^[a-zA-Z0-9_-]+$', url):
        return url
    
    return None


def format_phone_number(phone: str) -> Optional[str]:
    """
    Format phone number to a consistent format.
    
    Args:
        phone: Raw phone number
        
    Returns:
        Formatted phone number or None if invalid
    """
    if not phone:
        return None
    
    # Remove all non-digit characters except +
    cleaned = re.sub(r'[^\d+]', '', phone.strip())
    
    if not cleaned:
        return None
    
    # Add country code if missing (assuming India +91)
    if len(cleaned) == 10 and cleaned[0] in '6789':
        cleaned = '+91' + cleaned
    elif len(cleaned) == 12 and cleaned.startswith('91'):
        cleaned = '+' + cleaned
    
    return cleaned


def validate_email(email: str) -> bool:
    """
    Validate email address format.
    
    Args:
        email: Email address to validate
        
    Returns:
        True if valid, False otherwise
    """
    if not email:
        return False
    
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email.strip()))


def parse_name(full_name: str) -> dict:
    """
    Parse full name into components.
    
    Args:
        full_name: Full name string
        
    Returns:
        Dictionary with first_name, last_name, middle_name
    """
    if not full_name:
        return {'first_name': '', 'last_name': '', 'middle_name': ''}
    
    parts = full_name.strip().split()
    
    if len(parts) == 1:
        return {'first_name': parts[0], 'last_name': '', 'middle_name': ''}
    elif len(parts) == 2:
        return {'first_name': parts[0], 'last_name': parts[1], 'middle_name': ''}
    else:
        return {
            'first_name': parts[0],
            'last_name': parts[-1],
            'middle_name': ' '.join(parts[1:-1])
        }


def normalize_company_name(company: str) -> str:
    """
    Normalize company name for consistent storage and searching.
    
    Args:
        company: Raw company name
        
    Returns:
        Normalized company name
    """
    if not company:
        return ""
    
    company = company.strip()
    
    # Remove common suffixes
    suffixes = [
        ' Pvt. Ltd.', ' Pvt Ltd', ' Private Limited', ' Ltd.', ' Ltd',
        ' Inc.', ' Inc', ' LLC', ' LLP', ' Corp.', ' Corp', ' Co.'
    ]
    
    for suffix in suffixes:
        if company.endswith(suffix):
            company = company[:-len(suffix)]
    
    return company.strip()


def batch_from_year(year: int) -> str:
    """
    Convert graduation year to batch format.
    
    Args:
        year: Graduation year (e.g., 2020)
        
    Returns:
        Batch string (e.g., "2020")
    """
    return str(year)


def calculate_experience_years(jobs: list) -> int:
    """
    Calculate total years of experience from job history.
    
    Args:
        jobs: List of job dictionaries with start_date and end_date
        
    Returns:
        Total years of experience (approximate)
    """
    from datetime import datetime
    
    total_months = 0
    
    for job in jobs:
        start = job.get('start_date', '')
        end = job.get('end_date', 'Present')
        
        try:
            # Try to parse dates (simplified)
            if 'Present' in end or not end:
                end_date = datetime.now()
            else:
                # Try common formats
                for fmt in ['%Y-%m', '%b %Y', '%Y']:
                    try:
                        end_date = datetime.strptime(end, fmt)
                        break
                    except ValueError:
                        continue
                else:
                    continue
            
            for fmt in ['%Y-%m', '%b %Y', '%Y']:
                try:
                    start_date = datetime.strptime(start, fmt)
                    break
                except ValueError:
                    continue
            else:
                continue
            
            months = (end_date.year - start_date.year) * 12 + (end_date.month - start_date.month)
            total_months += max(0, months)
            
        except (ValueError, TypeError):
            continue
    
    return total_months // 12
