"""
Database models for Alumni Management System.
Uses SQLAlchemy for ORM with PostgreSQL.
"""

from datetime import datetime, timezone
from typing import Optional, List
from sqlalchemy import (
    create_engine, Column, Integer, String, Text, DateTime, 
    Boolean, ForeignKey, JSON, Enum as SQLEnum, Index
)
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
import enum

Base = declarative_base()


class Gender(enum.Enum):
    MALE = "male"
    FEMALE = "female"
    OTHER = "other"
    NOT_SPECIFIED = "not_specified"


class AlumniStatus(enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    UNKNOWN = "unknown"


class Alumni(Base):
    """Main alumni table storing core information."""
    __tablename__ = 'alumni'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Basic Information
    serial_number = Column(Integer, nullable=True)
    batch = Column(String(50), nullable=True, index=True)
    roll_number = Column(String(50), nullable=True, unique=True)
    name = Column(String(255), nullable=False, index=True)
    gender = Column(SQLEnum(Gender), default=Gender.NOT_SPECIFIED)
    
    # Contact Information
    whatsapp_number = Column(String(20), nullable=True)
    mobile_number = Column(String(20), nullable=True)
    college_email = Column(String(255), nullable=True)
    personal_email = Column(String(255), nullable=True)
    corporate_email = Column(String(255), nullable=True)
    
    # LinkedIn Information
    linkedin_id = Column(String(255), nullable=True, unique=True, index=True)
    linkedin_url = Column(String(500), nullable=True)
    linkedin_headline = Column(Text, nullable=True)
    linkedin_summary = Column(Text, nullable=True)
    linkedin_profile_pdf_url = Column(String(500), nullable=True)  # B2 storage URL
    linkedin_profile_pdf_key = Column(String(255), nullable=True)  # B2 storage key
    
    # Current Position
    current_company = Column(String(255), nullable=True, index=True)
    current_designation = Column(String(255), nullable=True, index=True)
    current_location = Column(String(255), nullable=True, index=True)
    
    # Additional Info
    position_of_responsibility = Column(Text, nullable=True)  # POR
    higher_studies = Column(Text, nullable=True)
    closest_city = Column(String(100), nullable=True)
    
    # Metadata
    status = Column(SQLEnum(AlumniStatus), default=AlumniStatus.ACTIVE)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_scraped_at = Column(DateTime, nullable=True)
    scrape_count = Column(Integer, default=0)
    raw_data = Column(JSON, nullable=True)  # Store original scraped data
    
    # Relationships
    job_history = relationship("JobHistory", back_populates="alumni", cascade="all, delete-orphan")
    education_history = relationship("EducationHistory", back_populates="alumni", cascade="all, delete-orphan")
    internships = relationship("Internship", back_populates="alumni", cascade="all, delete-orphan")
    scrape_logs = relationship("ScrapeLog", back_populates="alumni", cascade="all, delete-orphan")
    
    # Indexes
    __table_args__ = (
        Index('idx_alumni_batch_name', 'batch', 'name'),
        Index('idx_alumni_company_designation', 'current_company', 'current_designation'),
    )
    
    def __repr__(self):
        return f"<Alumni(id={self.id}, name='{self.name}', batch='{self.batch}')>"
    
    def to_dict(self):
        """Convert to dictionary for JSON serialization."""
        return {
            'id': self.id,
            'serial_number': self.serial_number,
            'batch': self.batch,
            'roll_number': self.roll_number,
            'name': self.name,
            'gender': self.gender.value if self.gender else None,
            'whatsapp_number': self.whatsapp_number,
            'mobile_number': self.mobile_number,
            'college_email': self.college_email,
            'personal_email': self.personal_email,
            'corporate_email': self.corporate_email,
            'linkedin_id': self.linkedin_id,
            'linkedin_url': self.linkedin_url,
            'linkedin_headline': self.linkedin_headline,
            'current_company': self.current_company,
            'current_designation': self.current_designation,
            'current_location': self.current_location,
            'position_of_responsibility': self.position_of_responsibility,
            'higher_studies': self.higher_studies,
            'closest_city': self.closest_city,
            'status': self.status.value if self.status else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'last_scraped_at': self.last_scraped_at.isoformat() if self.last_scraped_at else None,
        }


class JobHistory(Base):
    """Job history for each alumni."""
    __tablename__ = 'job_history'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    alumni_id = Column(Integer, ForeignKey('alumni.id', ondelete='CASCADE'), nullable=False, index=True)
    
    company_name = Column(String(255), nullable=False, index=True)
    job_title = Column(String(255), nullable=True, index=True)
    location = Column(String(255), nullable=True)
    start_date = Column(String(50), nullable=True)  # String to handle various formats
    end_date = Column(String(50), nullable=True)
    is_current = Column(Boolean, default=False)
    description = Column(Text, nullable=True)
    order_index = Column(Integer, default=0)  # To maintain order (1 = previous company 1, etc.)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    alumni = relationship("Alumni", back_populates="job_history")
    
    __table_args__ = (
        Index('idx_job_company_title', 'company_name', 'job_title'),
    )
    
    def __repr__(self):
        return f"<JobHistory(company='{self.company_name}', title='{self.job_title}')>"
    
    def to_dict(self):
        return {
            'id': self.id,
            'alumni_id': self.alumni_id,
            'company_name': self.company_name,
            'job_title': self.job_title,
            'location': self.location,
            'start_date': self.start_date,
            'end_date': self.end_date,
            'is_current': self.is_current,
            'description': self.description,
            'order_index': self.order_index,
        }


class EducationHistory(Base):
    """Education history for each alumni."""
    __tablename__ = 'education_history'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    alumni_id = Column(Integer, ForeignKey('alumni.id', ondelete='CASCADE'), nullable=False, index=True)
    
    institution_name = Column(String(255), nullable=False, index=True)
    degree = Column(String(255), nullable=True)
    field_of_study = Column(String(255), nullable=True)
    start_year = Column(String(10), nullable=True)
    end_year = Column(String(10), nullable=True)
    grade = Column(String(50), nullable=True)
    activities = Column(Text, nullable=True)
    description = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    alumni = relationship("Alumni", back_populates="education_history")
    
    def __repr__(self):
        return f"<EducationHistory(institution='{self.institution_name}', degree='{self.degree}')>"
    
    def to_dict(self):
        return {
            'id': self.id,
            'alumni_id': self.alumni_id,
            'institution_name': self.institution_name,
            'degree': self.degree,
            'field_of_study': self.field_of_study,
            'start_year': self.start_year,
            'end_year': self.end_year,
            'grade': self.grade,
            'activities': self.activities,
            'description': self.description,
        }


class Internship(Base):
    """Internship records for alumni."""
    __tablename__ = 'internships'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    alumni_id = Column(Integer, ForeignKey('alumni.id', ondelete='CASCADE'), nullable=False, index=True)
    
    company_name = Column(String(255), nullable=False, index=True)
    role = Column(String(255), nullable=True)
    location = Column(String(255), nullable=True)
    start_date = Column(String(50), nullable=True)
    end_date = Column(String(50), nullable=True)
    description = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    alumni = relationship("Alumni", back_populates="internships")
    
    def __repr__(self):
        return f"<Internship(company='{self.company_name}', role='{self.role}')>"
    
    def to_dict(self):
        return {
            'id': self.id,
            'alumni_id': self.alumni_id,
            'company_name': self.company_name,
            'role': self.role,
            'location': self.location,
            'start_date': self.start_date,
            'end_date': self.end_date,
            'description': self.description,
        }


class ScrapeLog(Base):
    """Log of scraping activities for auditing."""
    __tablename__ = 'scrape_logs'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    alumni_id = Column(Integer, ForeignKey('alumni.id', ondelete='CASCADE'), nullable=True, index=True)
    
    linkedin_account_used = Column(String(255), nullable=True)
    status = Column(String(50), nullable=False)  # success, failed, partial
    error_message = Column(Text, nullable=True)
    pdf_downloaded = Column(Boolean, default=False)
    pdf_storage_key = Column(String(255), nullable=True)
    data_extracted = Column(JSON, nullable=True)
    duration_seconds = Column(Integer, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    alumni = relationship("Alumni", back_populates="scrape_logs")
    
    def __repr__(self):
        return f"<ScrapeLog(id={self.id}, status='{self.status}')>"


class LinkedInCookie(Base):
    """Store LinkedIn cookies for session persistence."""
    __tablename__ = 'linkedin_cookies'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    account_email = Column(String(255), nullable=False, unique=True, index=True)
    cookies_data = Column(JSON, nullable=False)
    is_valid = Column(Boolean, default=True)
    last_validated_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<LinkedInCookie(email='{self.account_email}', valid={self.is_valid})>"


class ScrapingSession(Base):
    """Track scraping sessions for rate limiting and monitoring."""
    __tablename__ = 'scraping_sessions'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(100), nullable=False, unique=True)
    linkedin_account_email = Column(String(255), nullable=True)
    status = Column(String(50), nullable=False)  # running, completed, failed, paused
    profiles_scraped = Column(Integer, default=0)
    profiles_failed = Column(Integer, default=0)
    started_at = Column(DateTime, default=datetime.utcnow)
    ended_at = Column(DateTime, nullable=True)
    error_message = Column(Text, nullable=True)
    
    def __repr__(self):
        return f"<ScrapingSession(id={self.session_id}, status='{self.status}')>"


# Database initialization function
def init_db(database_url: str):
    """Initialize the database and create all tables."""
    engine = create_engine(database_url, echo=False)
    Base.metadata.create_all(engine)
    return engine


def get_session(engine):
    """Create a new database session."""
    Session = sessionmaker(bind=engine)
    return Session()
