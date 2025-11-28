"""
Tests for configuration module.
"""

import os
import pytest
from src.config import Config, LinkedInAccount, DatabaseConfig


class TestLinkedInAccount:
    """Tests for LinkedInAccount dataclass."""
    
    def test_create_account(self):
        """Test creating a LinkedIn account."""
        account = LinkedInAccount(
            email="test@example.com",
            password="password123"
        )
        assert account.email == "test@example.com"
        assert account.password == "password123"
        assert account.is_active is True
    
    def test_account_with_cookies(self):
        """Test account with cookies file."""
        account = LinkedInAccount(
            email="test@example.com",
            password="pass",
            cookies_file="/path/to/cookies.json"
        )
        assert account.cookies_file == "/path/to/cookies.json"


class TestDatabaseConfig:
    """Tests for DatabaseConfig dataclass."""
    
    def test_default_values(self):
        """Test default database configuration values."""
        # Clear relevant environment variables for this test
        config = DatabaseConfig()
        assert config.port == 5432
        assert config.database == "alumni_db"
    
    def test_connection_string_with_url(self):
        """Test connection string when URL is provided."""
        config = DatabaseConfig(url="postgresql://user:pass@host:5432/db")
        assert config.get_connection_string() == "postgresql://user:pass@host:5432/db"
    
    def test_connection_string_without_url(self):
        """Test connection string built from components."""
        config = DatabaseConfig(
            url="",
            user="testuser",
            password="testpass",
            host="localhost",
            port=5432,
            database="testdb"
        )
        conn_str = config.get_connection_string()
        assert "testuser" in conn_str
        assert "testpass" in conn_str
        assert "localhost" in conn_str
        assert "testdb" in conn_str


class TestConfig:
    """Tests for main Config class."""
    
    def test_config_initialization(self):
        """Test Config class initialization."""
        config = Config()
        assert config.database is not None
        assert config.b2_storage is not None
        assert config.browser is not None
        assert config.scraper is not None
    
    def test_get_linkedin_accounts(self):
        """Test getting LinkedIn accounts."""
        config = Config()
        accounts = config.get_linkedin_accounts()
        assert isinstance(accounts, list)
    
    def test_validate_config(self):
        """Test configuration validation."""
        config = Config()
        issues = config.validate()
        assert isinstance(issues, list)
        # With no env vars set, there should be issues
        assert len(issues) > 0
