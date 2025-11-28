# 🎓 Alumni Management System - IIM Ranchi

A comprehensive alumni management system featuring LinkedIn profile scraping, PostgreSQL database storage, Backblaze B2 cloud storage for PDFs, a Streamlit web interface, and an NLP chatbot for querying alumni data.

## ✨ Features

- **LinkedIn Scraping**: Automated profile scraping using Playwright with multi-account support and cookie persistence
- **Database Storage**: PostgreSQL database with SQLAlchemy ORM for storing alumni information, job history, and education
- **PDF Storage**: Backblaze B2 cloud storage for LinkedIn profile PDFs
- **Web Interface**: Streamlit-based frontend for searching, filtering, and exporting alumni data
- **Admin Panel**: Secure admin interface for manual data updates and imports
- **NLP Chatbot**: Natural language query interface using OpenAI API
- **Automation**: GitHub Actions workflow for scheduled scraping every 6 months

## 📁 Project Structure

```
alumni-management-system/
├── src/
│   ├── config.py           # Configuration management
│   ├── database/           # Database models and repositories
│   │   ├── models.py       # SQLAlchemy models
│   │   └── repository.py   # CRUD operations
│   ├── scraper/            # LinkedIn scraping
│   │   └── linkedin_scraper.py
│   ├── storage/            # Backblaze B2 integration
│   │   └── b2_storage.py
│   ├── frontend/           # Streamlit application
│   │   └── app.py
│   └── chatbot/            # NLP chatbot
│       └── nlp_chatbot.py
├── scripts/
│   ├── collect_cookies.py  # Cookie collection utility
│   └── run_scraper.py      # Scraper runner script
├── tests/                  # Unit tests
├── .github/
│   └── workflows/
│       └── scraper.yml     # GitHub Actions workflow
├── requirements.txt
├── pyproject.toml
└── .env.example
```

## 🚀 Quick Start

### Prerequisites

- Python 3.10+
- PostgreSQL 13+
- Backblaze B2 account (for PDF storage)
- OpenAI API key (optional, for chatbot)

### Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/im45145v/ARC-IIMR.git
   cd ARC-IIMR
   ```

2. **Create virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   playwright install chromium
   ```

4. **Configure environment variables**:
   ```bash
   cp .env.example .env
   # Edit .env with your credentials
   ```

5. **Initialize the database**:
   ```bash
   python -c "from src.database.models import init_db; init_db('your_database_url')"
   ```

### Running the Application

**Start the Streamlit frontend**:
```bash
streamlit run src/frontend/app.py
```

**Collect LinkedIn cookies**:
```bash
python scripts/collect_cookies.py --email your@email.com
```

**Run the scraper**:
```bash
python scripts/run_scraper.py --max-profiles 50
```

## ⚙️ Configuration

### Environment Variables

Create a `.env` file based on `.env.example`:

```env
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/alumni_db

# LinkedIn Accounts (JSON array or individual)
LINKEDIN_ACCOUNTS=[{"email": "account1@email.com", "password": "pass1"}]

# Backblaze B2
B2_KEY_ID=your_key_id
B2_APPLICATION_KEY=your_app_key
B2_BUCKET_NAME=alumni-pdfs

# OpenAI (optional)
OPENAI_API_KEY=your_openai_key

# Admin
ADMIN_PASSWORD=your_secure_password
```

### Multiple LinkedIn Accounts

The system supports multiple LinkedIn accounts for scalable scraping:

```env
# Option 1: JSON array
LINKEDIN_ACCOUNTS=[{"email": "acc1@email.com", "password": "pass1"}, {"email": "acc2@email.com", "password": "pass2"}]

# Option 2: Individual variables
LINKEDIN_EMAIL_1=account1@email.com
LINKEDIN_PASSWORD_1=password1
LINKEDIN_EMAIL_2=account2@email.com
LINKEDIN_PASSWORD_2=password2
```

## 📊 Database Schema

### Alumni Table
- Basic info: name, batch, roll number, gender
- Contact: emails, phone numbers
- LinkedIn: ID, URL, headline, summary
- Current position: company, designation, location
- Metadata: timestamps, scrape count

### Job History Table
- Company name, job title, location
- Start/end dates
- Order index for maintaining sequence

### Education History Table
- Institution name, degree, field of study
- Years attended
- Activities and description

## 🔄 Automation

The GitHub Actions workflow runs every 6 months (January 1 and July 1) to:

1. Initialize database
2. Load stored cookies
3. Scrape LinkedIn profiles
4. Upload PDFs to B2
5. Update database records
6. Create issue on failure

### Manual Trigger

You can manually trigger the workflow from GitHub Actions with parameters:
- `max_profiles`: Number of profiles to scrape
- `dry_run`: Test mode without database updates

## 🤖 Chatbot Usage

The NLP chatbot understands natural language queries:

```
"Who works at Google?"
"Find alumni from batch 2020"
"List software engineers in Bangalore"
"Show alumni at McKinsey"
```

With OpenAI API key configured, the chatbot provides more accurate responses.

## 🧪 Testing

Run the test suite:

```bash
pytest tests/ -v
```

Run with coverage:

```bash
pytest tests/ --cov=src --cov-report=html
```

## 📝 Data Import Format

The system supports CSV/Excel import with these columns:

| Column | Description |
|--------|-------------|
| Name | Full name (required) |
| Batch | Graduation year |
| Roll Number | Student ID |
| Gender | Male/Female/Other |
| WhatsApp Number | Phone number |
| College Email | Institute email |
| Personal Email | Personal email |
| LinkedIn ID | LinkedIn profile ID |
| Current Company | Current employer |
| Current Designation | Job title |
| Location | Current city |

## 🔒 Security Considerations

- All credentials stored in environment variables
- Cookie files excluded from version control
- Admin panel protected with password
- No sensitive data logged
- B2 storage for secure PDF storage

## 🛠️ Development

### Code Style

```bash
# Format code
black src/

# Lint
flake8 src/
```

### Adding New Features

1. Create feature branch
2. Implement changes
3. Add tests
4. Update documentation
5. Submit PR

## 📄 License

MIT License - see LICENSE file for details.

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Open a Pull Request

## 📧 Support

For issues and feature requests, please use the GitHub Issues page.

---

**Alumni Relations Committee - IIM Ranchi**
