"""
Tests for database models and repository.
"""

import pytest
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.database.models import (
    Base, Alumni, JobHistory, EducationHistory, 
    Gender, AlumniStatus, init_db
)
from src.database.repository import (
    AlumniRepository, JobHistoryRepository, EducationHistoryRepository
)


@pytest.fixture
def db_engine():
    """Create an in-memory SQLite database for testing."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return engine


@pytest.fixture
def db_session(db_engine):
    """Create a database session for testing."""
    Session = sessionmaker(bind=db_engine)
    session = Session()
    yield session
    session.close()


@pytest.fixture
def alumni_repo(db_session):
    """Create an AlumniRepository for testing."""
    return AlumniRepository(db_session)


@pytest.fixture
def job_repo(db_session):
    """Create a JobHistoryRepository for testing."""
    return JobHistoryRepository(db_session)


@pytest.fixture
def edu_repo(db_session):
    """Create an EducationHistoryRepository for testing."""
    return EducationHistoryRepository(db_session)


class TestAlumniModel:
    """Tests for Alumni model."""
    
    def test_create_alumni(self, db_session):
        """Test creating a new alumni record."""
        alumni = Alumni(
            name="John Doe",
            batch="2020",
            roll_number="2020MBA001",
            gender=Gender.MALE,
            current_company="Google",
            current_designation="Software Engineer"
        )
        db_session.add(alumni)
        db_session.commit()
        
        assert alumni.id is not None
        assert alumni.name == "John Doe"
        assert alumni.batch == "2020"
        assert alumni.gender == Gender.MALE
    
    def test_alumni_to_dict(self, db_session):
        """Test alumni to_dict method."""
        alumni = Alumni(
            name="Jane Doe",
            batch="2021",
            current_company="Microsoft"
        )
        db_session.add(alumni)
        db_session.commit()
        
        data = alumni.to_dict()
        assert data['name'] == "Jane Doe"
        assert data['batch'] == "2021"
        assert data['current_company'] == "Microsoft"
    
    def test_alumni_relationships(self, db_session):
        """Test alumni relationships with job history and education."""
        alumni = Alumni(name="Test User")
        job = JobHistory(company_name="TestCorp", job_title="Manager")
        edu = EducationHistory(institution_name="Test University", degree="MBA")
        
        alumni.job_history.append(job)
        alumni.education_history.append(edu)
        
        db_session.add(alumni)
        db_session.commit()
        
        assert len(alumni.job_history) == 1
        assert len(alumni.education_history) == 1
        assert alumni.job_history[0].company_name == "TestCorp"


class TestAlumniRepository:
    """Tests for AlumniRepository."""
    
    def test_create_alumni(self, alumni_repo):
        """Test creating alumni through repository."""
        data = {
            'name': 'John Smith',
            'batch': '2022',
            'current_company': 'Amazon'
        }
        
        alumni = alumni_repo.create(data)
        
        assert alumni.id is not None
        assert alumni.name == 'John Smith'
    
    def test_get_by_id(self, alumni_repo):
        """Test getting alumni by ID."""
        alumni = alumni_repo.create({'name': 'Test User'})
        
        found = alumni_repo.get_by_id(alumni.id)
        
        assert found is not None
        assert found.name == 'Test User'
    
    def test_get_by_linkedin_id(self, alumni_repo):
        """Test getting alumni by LinkedIn ID."""
        alumni_repo.create({
            'name': 'LinkedIn User',
            'linkedin_id': 'linkedinuser123'
        })
        
        found = alumni_repo.get_by_linkedin_id('linkedinuser123')
        
        assert found is not None
        assert found.name == 'LinkedIn User'
    
    def test_search_by_name(self, alumni_repo):
        """Test searching alumni by name."""
        alumni_repo.create({'name': 'Alice Johnson', 'batch': '2020'})
        alumni_repo.create({'name': 'Bob Smith', 'batch': '2021'})
        alumni_repo.create({'name': 'Alice Smith', 'batch': '2022'})
        
        results = alumni_repo.search(name='Alice')
        
        assert len(results) == 2
    
    def test_search_by_company(self, alumni_repo):
        """Test searching alumni by company."""
        alumni_repo.create({'name': 'User 1', 'current_company': 'Google'})
        alumni_repo.create({'name': 'User 2', 'current_company': 'Microsoft'})
        alumni_repo.create({'name': 'User 3', 'current_company': 'Google India'})
        
        results = alumni_repo.search(company='Google')
        
        assert len(results) == 2
    
    def test_search_by_batch(self, alumni_repo):
        """Test searching alumni by batch."""
        alumni_repo.create({'name': 'User 1', 'batch': '2020'})
        alumni_repo.create({'name': 'User 2', 'batch': '2021'})
        alumni_repo.create({'name': 'User 3', 'batch': '2020'})
        
        results = alumni_repo.search(batch='2020')
        
        assert len(results) == 2
    
    def test_update_alumni(self, alumni_repo):
        """Test updating alumni record."""
        alumni = alumni_repo.create({
            'name': 'Update Test',
            'current_company': 'Old Company'
        })
        
        alumni_repo.update(alumni.id, {'current_company': 'New Company'})
        
        updated = alumni_repo.get_by_id(alumni.id)
        assert updated.current_company == 'New Company'
    
    def test_delete_alumni(self, alumni_repo):
        """Test deleting alumni record."""
        alumni = alumni_repo.create({'name': 'Delete Test'})
        alumni_id = alumni.id
        
        result = alumni_repo.delete(alumni_id)
        
        assert result is True
        assert alumni_repo.get_by_id(alumni_id) is None
    
    def test_get_batches(self, alumni_repo):
        """Test getting unique batches."""
        alumni_repo.create({'name': 'User 1', 'batch': '2020'})
        alumni_repo.create({'name': 'User 2', 'batch': '2021'})
        alumni_repo.create({'name': 'User 3', 'batch': '2020'})
        
        batches = alumni_repo.get_batches()
        
        assert '2020' in batches
        assert '2021' in batches
        assert len(batches) == 2
    
    def test_get_statistics(self, alumni_repo):
        """Test getting alumni statistics."""
        alumni_repo.create({'name': 'User 1', 'batch': '2020', 'current_company': 'Google'})
        alumni_repo.create({'name': 'User 2', 'batch': '2020', 'current_company': 'Microsoft'})
        alumni_repo.create({'name': 'User 3', 'batch': '2021', 'current_company': 'Google'})
        
        stats = alumni_repo.get_statistics()
        
        assert stats['total_alumni'] == 3
        assert stats['by_batch']['2020'] == 2
        assert stats['by_batch']['2021'] == 1


class TestJobHistoryRepository:
    """Tests for JobHistoryRepository."""
    
    def test_bulk_create_jobs(self, job_repo, alumni_repo):
        """Test bulk creating job history."""
        alumni = alumni_repo.create({'name': 'Test User'})
        
        jobs = [
            {'company_name': 'Company A', 'job_title': 'Engineer'},
            {'company_name': 'Company B', 'job_title': 'Manager'},
        ]
        
        created = job_repo.bulk_create(alumni.id, jobs)
        
        assert len(created) == 2
        assert created[0].order_index == 0
        assert created[1].order_index == 1
    
    def test_get_jobs_by_alumni(self, job_repo, alumni_repo):
        """Test getting jobs by alumni ID."""
        alumni = alumni_repo.create({'name': 'Test User'})
        job_repo.bulk_create(alumni.id, [
            {'company_name': 'Company A'},
            {'company_name': 'Company B'},
        ])
        
        jobs = job_repo.get_by_alumni_id(alumni.id)
        
        assert len(jobs) == 2


class TestEducationHistoryRepository:
    """Tests for EducationHistoryRepository."""
    
    def test_bulk_create_education(self, edu_repo, alumni_repo):
        """Test bulk creating education history."""
        alumni = alumni_repo.create({'name': 'Test User'})
        
        educations = [
            {'institution_name': 'University A', 'degree': 'MBA'},
            {'institution_name': 'University B', 'degree': 'B.Tech'},
        ]
        
        created = edu_repo.bulk_create(alumni.id, educations)
        
        assert len(created) == 2
    
    def test_get_education_by_alumni(self, edu_repo, alumni_repo):
        """Test getting education by alumni ID."""
        alumni = alumni_repo.create({'name': 'Test User'})
        edu_repo.bulk_create(alumni.id, [
            {'institution_name': 'University A'},
            {'institution_name': 'University B'},
        ])
        
        educations = edu_repo.get_by_alumni_id(alumni.id)
        
        assert len(educations) == 2
