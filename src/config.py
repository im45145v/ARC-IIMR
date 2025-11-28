"""
Configuration module for Alumni Management System.
Handles loading and validating environment variables.
"""

import os
import json
import logging
from dataclasses import dataclass, field
from typing import List, Optional
from pathlib import Path

# Load environment variables from .env file if it exists
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


@dataclass
class LinkedInAccount:
    """Represents a LinkedIn account for scraping."""
    email: str
    password: str
    is_active: bool = True
    last_used: Optional[str] = None
    cookies_file: Optional[str] = None


@dataclass
class DatabaseConfig:
    """Database configuration settings."""
    url: str = field(default_factory=lambda: os.getenv("DATABASE_URL", ""))
    user: str = field(default_factory=lambda: os.getenv("POSTGRES_USER", "alumni_admin"))
    password: str = field(default_factory=lambda: os.getenv("POSTGRES_PASSWORD", ""))
    database: str = field(default_factory=lambda: os.getenv("POSTGRES_DB", "alumni_db"))
    host: str = field(default_factory=lambda: os.getenv("POSTGRES_HOST", "localhost"))
    port: int = field(default_factory=lambda: int(os.getenv("POSTGRES_PORT", "5432")))
    
    def get_connection_string(self) -> str:
        """Get PostgreSQL connection string."""
        if self.url:
            return self.url
        return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"


@dataclass
class B2StorageConfig:
    """Backblaze B2 storage configuration."""
    key_id: str = field(default_factory=lambda: os.getenv("B2_KEY_ID", ""))
    application_key: str = field(default_factory=lambda: os.getenv("B2_APPLICATION_KEY", ""))
    bucket_name: str = field(default_factory=lambda: os.getenv("B2_BUCKET_NAME", "alumni-pdfs"))
    bucket_id: str = field(default_factory=lambda: os.getenv("B2_BUCKET_ID", ""))


@dataclass
class BrowserConfig:
    """Browser automation configuration."""
    headless: bool = field(default_factory=lambda: os.getenv("BROWSER_HEADLESS", "true").lower() == "true")
    page_load_timeout: int = field(default_factory=lambda: int(os.getenv("PAGE_LOAD_TIMEOUT", "60000")))
    action_delay_min: int = field(default_factory=lambda: int(os.getenv("ACTION_DELAY_MIN", "3")))
    action_delay_max: int = field(default_factory=lambda: int(os.getenv("ACTION_DELAY_MAX", "7")))
    scroll_delay: int = field(default_factory=lambda: int(os.getenv("SCROLL_DELAY", "2")))


@dataclass
class ScraperConfig:
    """Scraper specific configuration."""
    max_profiles_per_session: int = field(default_factory=lambda: int(os.getenv("MAX_PROFILES_PER_SESSION", "50")))
    session_break_minutes: int = field(default_factory=lambda: int(os.getenv("SESSION_BREAK_MINUTES", "30")))
    rate_limit_delay: int = field(default_factory=lambda: int(os.getenv("RATE_LIMIT_DELAY", "5")))


@dataclass
class AdminConfig:
    """Admin interface configuration."""
    username: str = field(default_factory=lambda: os.getenv("ADMIN_USERNAME", "admin"))
    password: str = field(default_factory=lambda: os.getenv("ADMIN_PASSWORD", ""))
    secret_key: str = field(default_factory=lambda: os.getenv("STREAMLIT_SECRET_KEY", ""))


class Config:
    """Main configuration class for the Alumni Management System."""
    
    def __init__(self):
        self.database = DatabaseConfig()
        self.b2_storage = B2StorageConfig()
        self.browser = BrowserConfig()
        self.scraper = ScraperConfig()
        self.admin = AdminConfig()
        self.openai_api_key = os.getenv("OPENAI_API_KEY", "")
        self.log_level = os.getenv("LOG_LEVEL", "INFO")
        self.log_file = os.getenv("LOG_FILE", "logs/alumni_system.log")
        self._linkedin_accounts: List[LinkedInAccount] = []
        self._load_linkedin_accounts()
    
    def _load_linkedin_accounts(self):
        """Load LinkedIn accounts from environment variables."""
        # Try loading from JSON array first
        accounts_json = os.getenv("LINKEDIN_ACCOUNTS", "")
        if accounts_json:
            try:
                accounts_data = json.loads(accounts_json)
                for acc in accounts_data:
                    self._linkedin_accounts.append(
                        LinkedInAccount(
                            email=acc.get("email", ""),
                            password=acc.get("password", "")
                        )
                    )
                return
            except json.JSONDecodeError:
                logging.warning("Failed to parse LINKEDIN_ACCOUNTS JSON, falling back to individual accounts")
        
        # Fallback to individual account environment variables
        for i in range(1, 10):  # Support up to 10 accounts
            email = os.getenv(f"LINKEDIN_EMAIL_{i}", "")
            password = os.getenv(f"LINKEDIN_PASSWORD_{i}", "")
            if email and password:
                self._linkedin_accounts.append(
                    LinkedInAccount(email=email, password=password)
                )
    
    def get_linkedin_accounts(self) -> List[LinkedInAccount]:
        """Get all configured LinkedIn accounts."""
        return self._linkedin_accounts
    
    def get_active_linkedin_account(self) -> Optional[LinkedInAccount]:
        """Get the first active LinkedIn account."""
        for account in self._linkedin_accounts:
            if account.is_active:
                return account
        return None
    
    def setup_logging(self):
        """Configure logging for the application."""
        log_dir = Path(self.log_file).parent
        log_dir.mkdir(parents=True, exist_ok=True)
        
        logging.basicConfig(
            level=getattr(logging, self.log_level.upper()),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(self.log_file),
                logging.StreamHandler()
            ]
        )
    
    def validate(self) -> List[str]:
        """Validate configuration and return list of issues."""
        issues = []
        
        if not self._linkedin_accounts:
            issues.append("No LinkedIn accounts configured")
        
        if not self.database.password and not self.database.url:
            issues.append("Database password not set")
        
        if not self.b2_storage.key_id or not self.b2_storage.application_key:
            issues.append("Backblaze B2 credentials not set")
        
        if not self.admin.password:
            issues.append("Admin password not set")
        
        return issues


# Global configuration instance
config = Config()
