#!/usr/bin/env python3
"""
Script to run the LinkedIn scraper for alumni data collection.

Usage:
    python scripts/run_scraper.py [options]

Options:
    --max-profiles N    Maximum number of profiles to scrape (default: 100)
    --dry-run          Don't update the database
    --cookies-dir DIR  Directory containing cookie files
"""

import argparse
import asyncio
import logging
import os
import sys
from datetime import datetime
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config import config
from src.database.models import init_db, get_session
from src.database.repository import AlumniRepository, CookieRepository, ScrapeLogRepository
from src.scraper.linkedin_scraper import LinkedInScraper, MultiAccountScraper
from src.storage.b2_storage import B2Storage

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/scraper.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


async def run_scraper(
    max_profiles: int = 100,
    dry_run: bool = False,
    cookies_dir: str = "cookies"
):
    """
    Run the alumni scraper.
    
    Args:
        max_profiles: Maximum number of profiles to scrape
        dry_run: If True, don't update the database
        cookies_dir: Directory containing cookie files
    """
    logger.info(f"Starting scraper run at {datetime.utcnow().isoformat()}")
    logger.info(f"Max profiles: {max_profiles}, Dry run: {dry_run}")
    
    # Initialize database
    db_url = config.database.get_connection_string()
    engine = init_db(db_url)
    session = get_session(engine)
    
    alumni_repo = AlumniRepository(session)
    cookie_repo = CookieRepository(session)
    log_repo = ScrapeLogRepository(session)
    
    # Initialize B2 storage
    b2_storage = B2Storage()
    b2_initialized = b2_storage.initialize()
    
    if not b2_initialized:
        logger.warning("B2 storage not initialized. PDFs will be stored locally only.")
    
    # Get LinkedIn accounts
    accounts = config.get_linkedin_accounts()
    
    if not accounts:
        logger.error("No LinkedIn accounts configured!")
        return
    
    logger.info(f"Found {len(accounts)} LinkedIn account(s)")
    
    # Load cookies from files if available
    cookies_path = Path(cookies_dir)
    if cookies_path.exists():
        for cookie_file in cookies_path.glob("*.json"):
            logger.info(f"Found cookie file: {cookie_file}")
    
    # Get alumni that need scraping
    alumni_to_scrape = alumni_repo.get_alumni_needing_scrape(days_since_last_scrape=180)
    
    if not alumni_to_scrape:
        logger.info("No alumni need scraping at this time.")
        return
    
    logger.info(f"Found {len(alumni_to_scrape)} alumni needing scrape")
    
    # Limit to max_profiles
    alumni_to_scrape = alumni_to_scrape[:max_profiles]
    
    # Prepare profile URLs
    profile_urls = []
    for alum in alumni_to_scrape:
        if alum.linkedin_url:
            profile_urls.append(alum.linkedin_url)
        elif alum.linkedin_id:
            profile_urls.append(f"https://www.linkedin.com/in/{alum.linkedin_id}")
    
    if not profile_urls:
        logger.warning("No valid LinkedIn URLs found")
        return
    
    logger.info(f"Will scrape {len(profile_urls)} profiles")
    
    # Initialize multi-account scraper
    account_configs = [
        {'email': acc.email, 'password': acc.password}
        for acc in accounts
    ]
    
    scraper = MultiAccountScraper(
        accounts=account_configs,
        cookies_dir=cookies_dir,
        max_profiles_per_account=config.scraper.max_profiles_per_session,
        cooldown_minutes=config.scraper.session_break_minutes
    )
    
    # Run scraper
    results = await scraper.scrape_profiles(profile_urls)
    
    # Process results
    success_count = 0
    error_count = 0
    
    for i, result in enumerate(results):
        try:
            if result['success']:
                data = result['data']
                linkedin_id = data.get('linkedin_id')
                
                if not linkedin_id:
                    continue
                
                # Find the corresponding alumni
                alumni = alumni_repo.get_by_linkedin_id(linkedin_id)
                
                if alumni and not dry_run:
                    # Update alumni record
                    update_data = {
                        'linkedin_headline': data.get('headline'),
                        'linkedin_summary': data.get('summary'),
                        'current_company': data.get('current_company'),
                        'current_designation': data.get('current_designation'),
                        'current_location': data.get('location'),
                        'last_scraped_at': datetime.utcnow(),
                        'scrape_count': (alumni.scrape_count or 0) + 1,
                        'raw_data': data
                    }
                    
                    alumni_repo.update(alumni.id, update_data)
                    
                    # Log successful scrape
                    log_repo.create({
                        'alumni_id': alumni.id,
                        'status': 'success',
                        'data_extracted': data
                    })
                    
                    success_count += 1
                    logger.info(f"Updated alumni: {alumni.name}")
                
            else:
                error_count += 1
                logger.error(f"Failed to scrape: {result.get('error')}")
                
                # Log failed scrape
                if not dry_run:
                    log_repo.create({
                        'status': 'failed',
                        'error_message': result.get('error')
                    })
                    
        except Exception as e:
            error_count += 1
            logger.error(f"Error processing result {i}: {e}")
    
    logger.info(f"Scraper run complete. Success: {success_count}, Errors: {error_count}")
    
    # Close session
    session.close()


def main():
    parser = argparse.ArgumentParser(description="Run LinkedIn alumni scraper")
    parser.add_argument(
        "--max-profiles",
        type=int,
        default=100,
        help="Maximum number of profiles to scrape"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Don't update the database"
    )
    parser.add_argument(
        "--cookies-dir",
        default="cookies",
        help="Directory containing cookie files"
    )
    
    args = parser.parse_args()
    
    # Create logs directory
    Path("logs").mkdir(exist_ok=True)
    
    # Run scraper
    asyncio.run(run_scraper(
        max_profiles=args.max_profiles,
        dry_run=args.dry_run,
        cookies_dir=args.cookies_dir
    ))


if __name__ == "__main__":
    main()
