"""
Database repository module for Alumni Management System.
Provides CRUD operations and query methods.
"""

from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from sqlalchemy import or_, and_, func
from sqlalchemy.orm import Session
from .models import (
    Alumni, JobHistory, EducationHistory, Internship, 
    ScrapeLog, LinkedInCookie, ScrapingSession, Gender, AlumniStatus
)


class AlumniRepository:
    """Repository for Alumni CRUD operations."""
    
    def __init__(self, session: Session):
        self.session = session
    
    def create(self, alumni_data: Dict[str, Any]) -> Alumni:
        """Create a new alumni record."""
        alumni = Alumni(**alumni_data)
        self.session.add(alumni)
        self.session.commit()
        self.session.refresh(alumni)
        return alumni
    
    def get_by_id(self, alumni_id: int) -> Optional[Alumni]:
        """Get alumni by ID."""
        return self.session.query(Alumni).filter(Alumni.id == alumni_id).first()
    
    def get_by_linkedin_id(self, linkedin_id: str) -> Optional[Alumni]:
        """Get alumni by LinkedIn ID."""
        return self.session.query(Alumni).filter(Alumni.linkedin_id == linkedin_id).first()
    
    def get_by_roll_number(self, roll_number: str) -> Optional[Alumni]:
        """Get alumni by roll number."""
        return self.session.query(Alumni).filter(Alumni.roll_number == roll_number).first()
    
    def get_all(self, skip: int = 0, limit: int = 100) -> List[Alumni]:
        """Get all alumni with pagination."""
        return self.session.query(Alumni).offset(skip).limit(limit).all()
    
    def update(self, alumni_id: int, update_data: Dict[str, Any]) -> Optional[Alumni]:
        """Update alumni record."""
        alumni = self.get_by_id(alumni_id)
        if alumni:
            for key, value in update_data.items():
                if hasattr(alumni, key):
                    setattr(alumni, key, value)
            alumni.updated_at = datetime.now(timezone.utc)
            self.session.commit()
            self.session.refresh(alumni)
        return alumni
    
    def delete(self, alumni_id: int) -> bool:
        """Delete alumni record."""
        alumni = self.get_by_id(alumni_id)
        if alumni:
            self.session.delete(alumni)
            self.session.commit()
            return True
        return False
    
    def search(
        self,
        name: Optional[str] = None,
        batch: Optional[str] = None,
        company: Optional[str] = None,
        designation: Optional[str] = None,
        location: Optional[str] = None,
        status: Optional[AlumniStatus] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Alumni]:
        """Search alumni with multiple filters."""
        query = self.session.query(Alumni)
        
        if name:
            query = query.filter(Alumni.name.ilike(f"%{name}%"))
        if batch:
            query = query.filter(Alumni.batch == batch)
        if company:
            query = query.filter(Alumni.current_company.ilike(f"%{company}%"))
        if designation:
            query = query.filter(Alumni.current_designation.ilike(f"%{designation}%"))
        if location:
            query = query.filter(Alumni.current_location.ilike(f"%{location}%"))
        if status:
            query = query.filter(Alumni.status == status)
        
        return query.offset(skip).limit(limit).all()
    
    def get_batches(self) -> List[str]:
        """Get list of all unique batches."""
        batches = self.session.query(Alumni.batch).distinct().filter(Alumni.batch.isnot(None)).all()
        return [b[0] for b in batches if b[0]]
    
    def get_companies(self) -> List[str]:
        """Get list of all unique current companies."""
        companies = self.session.query(Alumni.current_company).distinct().filter(
            Alumni.current_company.isnot(None)
        ).all()
        return [c[0] for c in companies if c[0]]
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get alumni statistics."""
        total = self.session.query(func.count(Alumni.id)).scalar()
        by_batch = self.session.query(
            Alumni.batch, func.count(Alumni.id)
        ).group_by(Alumni.batch).all()
        by_company = self.session.query(
            Alumni.current_company, func.count(Alumni.id)
        ).group_by(Alumni.current_company).order_by(
            func.count(Alumni.id).desc()
        ).limit(10).all()
        
        return {
            'total_alumni': total,
            'by_batch': {b: c for b, c in by_batch if b},
            'top_companies': {c: n for c, n in by_company if c},
        }
    
    def upsert_from_linkedin(self, linkedin_id: str, data: Dict[str, Any]) -> Alumni:
        """Insert or update alumni from LinkedIn data."""
        existing = self.get_by_linkedin_id(linkedin_id)
        
        if existing:
            return self.update(existing.id, data)
        else:
            data['linkedin_id'] = linkedin_id
            return self.create(data)
    
    def get_alumni_needing_scrape(self, days_since_last_scrape: int = 180) -> List[Alumni]:
        """Get alumni that need to be re-scraped."""
        cutoff_date = datetime.now(timezone.utc)
        query = self.session.query(Alumni).filter(
            or_(
                Alumni.last_scraped_at.is_(None),
                Alumni.last_scraped_at < cutoff_date
            ),
            Alumni.linkedin_id.isnot(None)
        )
        return query.all()


class JobHistoryRepository:
    """Repository for JobHistory CRUD operations."""
    
    def __init__(self, session: Session):
        self.session = session
    
    def create(self, job_data: Dict[str, Any]) -> JobHistory:
        """Create a new job history record."""
        job = JobHistory(**job_data)
        self.session.add(job)
        self.session.commit()
        self.session.refresh(job)
        return job
    
    def get_by_alumni_id(self, alumni_id: int) -> List[JobHistory]:
        """Get all job history for an alumni."""
        return self.session.query(JobHistory).filter(
            JobHistory.alumni_id == alumni_id
        ).order_by(JobHistory.order_index).all()
    
    def delete_by_alumni_id(self, alumni_id: int) -> int:
        """Delete all job history for an alumni."""
        count = self.session.query(JobHistory).filter(
            JobHistory.alumni_id == alumni_id
        ).delete()
        self.session.commit()
        return count
    
    def bulk_create(self, alumni_id: int, jobs: List[Dict[str, Any]]) -> List[JobHistory]:
        """Bulk create job history records."""
        # First delete existing
        self.delete_by_alumni_id(alumni_id)
        
        created_jobs = []
        for i, job_data in enumerate(jobs):
            job_data['alumni_id'] = alumni_id
            job_data['order_index'] = i
            job = JobHistory(**job_data)
            self.session.add(job)
            created_jobs.append(job)
        
        self.session.commit()
        return created_jobs
    
    def search_by_company(self, company_name: str) -> List[JobHistory]:
        """Search job history by company name."""
        return self.session.query(JobHistory).filter(
            JobHistory.company_name.ilike(f"%{company_name}%")
        ).all()


class EducationHistoryRepository:
    """Repository for EducationHistory CRUD operations."""
    
    def __init__(self, session: Session):
        self.session = session
    
    def create(self, edu_data: Dict[str, Any]) -> EducationHistory:
        """Create a new education history record."""
        edu = EducationHistory(**edu_data)
        self.session.add(edu)
        self.session.commit()
        self.session.refresh(edu)
        return edu
    
    def get_by_alumni_id(self, alumni_id: int) -> List[EducationHistory]:
        """Get all education history for an alumni."""
        return self.session.query(EducationHistory).filter(
            EducationHistory.alumni_id == alumni_id
        ).all()
    
    def delete_by_alumni_id(self, alumni_id: int) -> int:
        """Delete all education history for an alumni."""
        count = self.session.query(EducationHistory).filter(
            EducationHistory.alumni_id == alumni_id
        ).delete()
        self.session.commit()
        return count
    
    def bulk_create(self, alumni_id: int, educations: List[Dict[str, Any]]) -> List[EducationHistory]:
        """Bulk create education history records."""
        self.delete_by_alumni_id(alumni_id)
        
        created_educations = []
        for edu_data in educations:
            edu_data['alumni_id'] = alumni_id
            edu = EducationHistory(**edu_data)
            self.session.add(edu)
            created_educations.append(edu)
        
        self.session.commit()
        return created_educations


class InternshipRepository:
    """Repository for Internship CRUD operations."""
    
    def __init__(self, session: Session):
        self.session = session
    
    def create(self, internship_data: Dict[str, Any]) -> Internship:
        """Create a new internship record."""
        internship = Internship(**internship_data)
        self.session.add(internship)
        self.session.commit()
        self.session.refresh(internship)
        return internship
    
    def get_by_alumni_id(self, alumni_id: int) -> List[Internship]:
        """Get all internships for an alumni."""
        return self.session.query(Internship).filter(
            Internship.alumni_id == alumni_id
        ).all()
    
    def delete_by_alumni_id(self, alumni_id: int) -> int:
        """Delete all internships for an alumni."""
        count = self.session.query(Internship).filter(
            Internship.alumni_id == alumni_id
        ).delete()
        self.session.commit()
        return count


class CookieRepository:
    """Repository for LinkedIn cookie management."""
    
    def __init__(self, session: Session):
        self.session = session
    
    def save_cookies(self, email: str, cookies: List[Dict[str, Any]]) -> LinkedInCookie:
        """Save or update cookies for an account."""
        existing = self.session.query(LinkedInCookie).filter(
            LinkedInCookie.account_email == email
        ).first()
        
        if existing:
            existing.cookies_data = cookies
            existing.is_valid = True
            existing.updated_at = datetime.now(timezone.utc)
            existing.last_validated_at = datetime.now(timezone.utc)
            self.session.commit()
            return existing
        else:
            cookie = LinkedInCookie(
                account_email=email,
                cookies_data=cookies,
                is_valid=True,
                last_validated_at=datetime.now(timezone.utc)
            )
            self.session.add(cookie)
            self.session.commit()
            self.session.refresh(cookie)
            return cookie
    
    def get_cookies(self, email: str) -> Optional[List[Dict[str, Any]]]:
        """Get cookies for an account."""
        cookie = self.session.query(LinkedInCookie).filter(
            LinkedInCookie.account_email == email,
            LinkedInCookie.is_valid == True
        ).first()
        return cookie.cookies_data if cookie else None
    
    def invalidate_cookies(self, email: str) -> bool:
        """Mark cookies as invalid."""
        cookie = self.session.query(LinkedInCookie).filter(
            LinkedInCookie.account_email == email
        ).first()
        if cookie:
            cookie.is_valid = False
            cookie.updated_at = datetime.now(timezone.utc)
            self.session.commit()
            return True
        return False


class ScrapeLogRepository:
    """Repository for scrape log operations."""
    
    def __init__(self, session: Session):
        self.session = session
    
    def create(self, log_data: Dict[str, Any]) -> ScrapeLog:
        """Create a new scrape log entry."""
        log = ScrapeLog(**log_data)
        self.session.add(log)
        self.session.commit()
        self.session.refresh(log)
        return log
    
    def get_recent_logs(self, limit: int = 100) -> List[ScrapeLog]:
        """Get recent scrape logs."""
        return self.session.query(ScrapeLog).order_by(
            ScrapeLog.created_at.desc()
        ).limit(limit).all()
    
    def get_logs_by_alumni(self, alumni_id: int) -> List[ScrapeLog]:
        """Get scrape logs for a specific alumni."""
        return self.session.query(ScrapeLog).filter(
            ScrapeLog.alumni_id == alumni_id
        ).order_by(ScrapeLog.created_at.desc()).all()
    
    def get_error_logs(self, limit: int = 50) -> List[ScrapeLog]:
        """Get recent error logs."""
        return self.session.query(ScrapeLog).filter(
            ScrapeLog.status == 'failed'
        ).order_by(ScrapeLog.created_at.desc()).limit(limit).all()


class ScrapingSessionRepository:
    """Repository for scraping session management."""
    
    def __init__(self, session: Session):
        self.session = session
    
    def create_session(self, session_id: str, email: str = None) -> ScrapingSession:
        """Create a new scraping session."""
        scraping_session = ScrapingSession(
            session_id=session_id,
            linkedin_account_email=email,
            status='running'
        )
        self.session.add(scraping_session)
        self.session.commit()
        self.session.refresh(scraping_session)
        return scraping_session
    
    def update_session(self, session_id: str, **kwargs) -> Optional[ScrapingSession]:
        """Update scraping session."""
        scraping_session = self.session.query(ScrapingSession).filter(
            ScrapingSession.session_id == session_id
        ).first()
        
        if scraping_session:
            for key, value in kwargs.items():
                if hasattr(scraping_session, key):
                    setattr(scraping_session, key, value)
            self.session.commit()
            self.session.refresh(scraping_session)
        return scraping_session
    
    def end_session(self, session_id: str, status: str = 'completed', error: str = None) -> Optional[ScrapingSession]:
        """Mark session as ended."""
        return self.update_session(
            session_id,
            status=status,
            ended_at=datetime.now(timezone.utc),
            error_message=error
        )
    
    def get_active_sessions(self) -> List[ScrapingSession]:
        """Get all active scraping sessions."""
        return self.session.query(ScrapingSession).filter(
            ScrapingSession.status == 'running'
        ).all()
