"""
LinkedIn Scraper using Playwright.
Handles profile scraping, PDF downloads, and cookie management.
"""

import asyncio
import json
import logging
import os
import random
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

from playwright.async_api import async_playwright, Page, Browser, BrowserContext

logger = logging.getLogger(__name__)


class LinkedInScraper:
    """
    LinkedIn profile scraper using Playwright.
    Supports multiple accounts, cookie persistence, and PDF downloads.
    """
    
    def __init__(
        self,
        headless: bool = True,
        action_delay_min: int = 3,
        action_delay_max: int = 7,
        scroll_delay: int = 2,
        page_load_timeout: int = 60000,
        download_dir: str = "downloads"
    ):
        self.headless = headless
        self.action_delay_min = action_delay_min
        self.action_delay_max = action_delay_max
        self.scroll_delay = scroll_delay
        self.page_load_timeout = page_load_timeout
        self.download_dir = Path(download_dir)
        self.download_dir.mkdir(parents=True, exist_ok=True)
        
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self.current_account_email: Optional[str] = None
        self.playwright = None
        
    async def _random_delay(self, min_seconds: int = None, max_seconds: int = None):
        """Add random delay between actions to appear human-like."""
        min_s = min_seconds or self.action_delay_min
        max_s = max_seconds or self.action_delay_max
        delay = random.uniform(min_s, max_s)
        logger.debug(f"Waiting {delay:.2f} seconds...")
        await asyncio.sleep(delay)
    
    async def _scroll_page(self):
        """Scroll the page to load dynamic content."""
        if not self.page:
            return
        
        # Get page height
        page_height = await self.page.evaluate("document.body.scrollHeight")
        viewport_height = await self.page.evaluate("window.innerHeight")
        
        current_position = 0
        while current_position < page_height:
            scroll_amount = random.randint(200, 400)
            current_position += scroll_amount
            await self.page.evaluate(f"window.scrollTo(0, {current_position})")
            await asyncio.sleep(self.scroll_delay + random.uniform(0, 1))
        
        # Scroll back to top
        await self.page.evaluate("window.scrollTo(0, 0)")
        await asyncio.sleep(1)
    
    async def start(self) -> bool:
        """Initialize Playwright and browser."""
        try:
            self.playwright = await async_playwright().start()
            self.browser = await self.playwright.chromium.launch(
                headless=self.headless,
                args=[
                    '--disable-blink-features=AutomationControlled',
                    '--disable-dev-shm-usage',
                    '--no-sandbox',
                ]
            )
            logger.info("Browser started successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to start browser: {e}")
            return False
    
    async def stop(self):
        """Close browser and cleanup."""
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
        logger.info("Browser stopped")
    
    async def _create_context(self, cookies: List[Dict] = None) -> BrowserContext:
        """Create a new browser context with optional cookies."""
        context = await self.browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            locale='en-US',
            timezone_id='America/New_York',
            accept_downloads=True
        )
        
        if cookies:
            await context.add_cookies(cookies)
            logger.info(f"Loaded {len(cookies)} cookies")
        
        return context
    
    async def login(self, email: str, password: str) -> Tuple[bool, List[Dict]]:
        """
        Login to LinkedIn and return session cookies.
        
        Returns:
            Tuple of (success: bool, cookies: List[Dict])
        """
        try:
            self.context = await self._create_context()
            self.page = await self.context.new_page()
            self.page.set_default_timeout(self.page_load_timeout)
            
            # Navigate to LinkedIn login page
            logger.info("Navigating to LinkedIn login page...")
            await self.page.goto("https://www.linkedin.com/login")
            await self._random_delay(2, 4)
            
            # Fill in credentials
            logger.info("Entering credentials...")
            await self.page.fill('input#username', email)
            await self._random_delay(1, 2)
            await self.page.fill('input#password', password)
            await self._random_delay(1, 2)
            
            # Click login button
            await self.page.click('button[type="submit"]')
            
            # Wait for navigation
            logger.info("Waiting for login to complete...")
            await self._random_delay(5, 8)
            
            # Check if login was successful
            current_url = self.page.url
            if "feed" in current_url or "mynetwork" in current_url:
                logger.info("Login successful!")
                self.current_account_email = email
                
                # Get cookies
                cookies = await self.context.cookies()
                return True, cookies
            elif "checkpoint" in current_url or "challenge" in current_url:
                logger.warning("Security checkpoint detected. Manual verification may be required.")
                return False, []
            else:
                logger.error(f"Login failed. Current URL: {current_url}")
                return False, []
                
        except Exception as e:
            logger.error(f"Login error: {e}")
            return False, []
    
    async def login_with_cookies(self, cookies: List[Dict]) -> bool:
        """Login using existing cookies."""
        try:
            self.context = await self._create_context(cookies)
            self.page = await self.context.new_page()
            self.page.set_default_timeout(self.page_load_timeout)
            
            # Navigate to LinkedIn feed to verify session
            logger.info("Verifying cookie session...")
            await self.page.goto("https://www.linkedin.com/feed/")
            await self._random_delay(3, 5)
            
            current_url = self.page.url
            if "feed" in current_url:
                logger.info("Cookie login successful!")
                return True
            else:
                logger.warning("Cookie session invalid")
                return False
                
        except Exception as e:
            logger.error(f"Cookie login error: {e}")
            return False
    
    async def scrape_profile(self, profile_url: str) -> Dict[str, Any]:
        """
        Scrape a LinkedIn profile and extract information.
        
        Returns:
            Dict containing profile data
        """
        if not self.page:
            raise RuntimeError("Browser not initialized. Call login first.")
        
        result = {
            'linkedin_url': profile_url,
            'scraped_at': datetime.utcnow().isoformat(),
            'success': False,
            'error': None,
            'data': {}
        }
        
        try:
            logger.info(f"Scraping profile: {profile_url}")
            
            # Navigate to profile
            await self.page.goto(profile_url)
            await self._random_delay(4, 6)
            
            # Check for profile not found
            if "Page not found" in await self.page.content():
                result['error'] = "Profile not found"
                return result
            
            # Scroll to load all content
            await self._scroll_page()
            await self._random_delay(2, 3)
            
            # Extract profile data
            data = await self._extract_profile_data()
            result['data'] = data
            result['success'] = True
            
            logger.info(f"Successfully scraped profile: {data.get('name', 'Unknown')}")
            
        except Exception as e:
            logger.error(f"Error scraping profile {profile_url}: {e}")
            result['error'] = str(e)
        
        return result
    
    async def _extract_profile_data(self) -> Dict[str, Any]:
        """Extract all available data from the current profile page."""
        data = {}
        
        try:
            # Extract name
            name_elem = await self.page.query_selector('h1.text-heading-xlarge')
            if name_elem:
                data['name'] = await name_elem.inner_text()
            
            # Extract headline
            headline_elem = await self.page.query_selector('div.text-body-medium')
            if headline_elem:
                data['headline'] = await headline_elem.inner_text()
            
            # Extract location
            location_elem = await self.page.query_selector('span.text-body-small.inline')
            if location_elem:
                data['location'] = await location_elem.inner_text()
            
            # Extract LinkedIn ID from URL
            current_url = self.page.url
            if '/in/' in current_url:
                linkedin_id = current_url.split('/in/')[-1].split('/')[0].split('?')[0]
                data['linkedin_id'] = linkedin_id
            
            # Extract about/summary section
            about_section = await self.page.query_selector('section.pv-about-section')
            if about_section:
                about_text = await about_section.query_selector('div.inline-show-more-text')
                if about_text:
                    data['summary'] = await about_text.inner_text()
            
            # Extract experience
            data['experience'] = await self._extract_experience()
            
            # Extract education
            data['education'] = await self._extract_education()
            
            # Extract current company and designation from experience
            if data.get('experience') and len(data['experience']) > 0:
                current_job = data['experience'][0]
                if current_job.get('is_current', True):
                    data['current_company'] = current_job.get('company_name')
                    data['current_designation'] = current_job.get('job_title')
            
        except Exception as e:
            logger.error(f"Error extracting profile data: {e}")
        
        return data
    
    async def _extract_experience(self) -> List[Dict[str, Any]]:
        """Extract work experience from profile."""
        experience = []
        
        try:
            # Try to expand "Show all experience" if available
            show_all_btn = await self.page.query_selector('a[id*="navigation-index-see-all-experience"]')
            if show_all_btn:
                await show_all_btn.click()
                await self._random_delay(2, 3)
            
            # Find experience section
            exp_items = await self.page.query_selector_all('li.artdeco-list__item.pvs-list__item--line-separated')
            
            for i, item in enumerate(exp_items[:10]):  # Limit to 10 items
                try:
                    job = {'order_index': i}
                    
                    # Try to get company name
                    company_elem = await item.query_selector('span.t-14.t-normal')
                    if company_elem:
                        job['company_name'] = await company_elem.inner_text()
                    
                    # Try to get job title
                    title_elem = await item.query_selector('span.t-bold')
                    if title_elem:
                        title_text = await title_elem.inner_text()
                        job['job_title'] = title_text.split('\n')[0].strip()
                    
                    # Try to get date range
                    date_elem = await item.query_selector('span.t-14.t-normal.t-black--light')
                    if date_elem:
                        date_text = await date_elem.inner_text()
                        job['date_range'] = date_text
                        if 'Present' in date_text:
                            job['is_current'] = True
                        else:
                            job['is_current'] = False
                    
                    if job.get('company_name') or job.get('job_title'):
                        experience.append(job)
                        
                except Exception as e:
                    logger.debug(f"Error extracting experience item: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"Error extracting experience: {e}")
        
        return experience
    
    async def _extract_education(self) -> List[Dict[str, Any]]:
        """Extract education history from profile."""
        education = []
        
        try:
            # Find education section
            edu_section = await self.page.query_selector('section[id*="education"]')
            if not edu_section:
                return education
            
            edu_items = await edu_section.query_selector_all('li.artdeco-list__item')
            
            for item in edu_items[:5]:  # Limit to 5 items
                try:
                    edu = {}
                    
                    # Institution name
                    inst_elem = await item.query_selector('span.t-bold span')
                    if inst_elem:
                        edu['institution_name'] = await inst_elem.inner_text()
                    
                    # Degree
                    degree_elem = await item.query_selector('span.t-14.t-normal span')
                    if degree_elem:
                        edu['degree'] = await degree_elem.inner_text()
                    
                    if edu.get('institution_name'):
                        education.append(edu)
                        
                except Exception as e:
                    logger.debug(f"Error extracting education item: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"Error extracting education: {e}")
        
        return education
    
    async def download_profile_pdf(self, profile_url: str) -> Optional[str]:
        """
        Download LinkedIn profile as PDF.
        Uses the "Save to PDF" feature from the More menu.
        
        Returns:
            Path to downloaded PDF file, or None if failed
        """
        if not self.page:
            raise RuntimeError("Browser not initialized. Call login first.")
        
        try:
            # Navigate to profile if not already there
            if self.page.url != profile_url:
                await self.page.goto(profile_url)
                await self._random_delay(4, 6)
            
            # Click the "More" button
            more_btn = await self.page.query_selector('button.artdeco-dropdown__trigger--placement-bottom')
            if not more_btn:
                more_btn = await self.page.query_selector('button:has-text("More")')
            
            if more_btn:
                await more_btn.click()
                await self._random_delay(2, 3)
                
                # Look for "Save to PDF" option
                save_pdf_btn = await self.page.query_selector('div[data-control-name="save_to_pdf"]')
                if not save_pdf_btn:
                    save_pdf_btn = await self.page.query_selector('span:has-text("Save to PDF")')
                
                if save_pdf_btn:
                    # Set up download handler
                    async with self.page.expect_download() as download_info:
                        await save_pdf_btn.click()
                    
                    download = await download_info.value
                    
                    # Generate unique filename
                    linkedin_id = profile_url.split('/in/')[-1].split('/')[0].split('?')[0]
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                    filename = f"{linkedin_id}_{timestamp}.pdf"
                    filepath = self.download_dir / filename
                    
                    # Save the file
                    await download.save_as(str(filepath))
                    logger.info(f"PDF downloaded: {filepath}")
                    
                    return str(filepath)
                else:
                    logger.warning("Save to PDF option not found in menu")
            else:
                logger.warning("More button not found on profile page")
                
        except Exception as e:
            logger.error(f"Error downloading PDF: {e}")
        
        return None
    
    async def get_cookies(self) -> List[Dict]:
        """Get current session cookies."""
        if self.context:
            return await self.context.cookies()
        return []
    
    async def save_cookies_to_file(self, filepath: str):
        """Save current cookies to a JSON file."""
        cookies = await self.get_cookies()
        Path(filepath).parent.mkdir(parents=True, exist_ok=True)
        with open(filepath, 'w') as f:
            json.dump(cookies, f, indent=2)
        logger.info(f"Cookies saved to {filepath}")
    
    @staticmethod
    def load_cookies_from_file(filepath: str) -> List[Dict]:
        """Load cookies from a JSON file."""
        try:
            with open(filepath, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.warning(f"Cookie file not found: {filepath}")
            return []
        except json.JSONDecodeError:
            logger.error(f"Invalid JSON in cookie file: {filepath}")
            return []


class CookieCollector:
    """
    Utility class to collect and validate LinkedIn cookies.
    Can be run standalone to set up authentication.
    """
    
    def __init__(self, cookies_dir: str = "cookies"):
        self.cookies_dir = Path(cookies_dir)
        self.cookies_dir.mkdir(parents=True, exist_ok=True)
    
    async def collect_cookies(self, email: str, password: str) -> Tuple[bool, str]:
        """
        Login to LinkedIn and save cookies to file.
        
        Returns:
            Tuple of (success: bool, cookie_filepath: str)
        """
        scraper = LinkedInScraper(headless=False)  # Non-headless for manual verification if needed
        
        try:
            await scraper.start()
            success, cookies = await scraper.login(email, password)
            
            if success:
                # Generate filename from email
                safe_email = email.replace('@', '_at_').replace('.', '_')
                cookie_file = self.cookies_dir / f"{safe_email}.json"
                
                await scraper.save_cookies_to_file(str(cookie_file))
                return True, str(cookie_file)
            else:
                return False, ""
                
        finally:
            await scraper.stop()
    
    async def validate_cookies(self, cookie_filepath: str) -> bool:
        """Validate that stored cookies are still valid."""
        cookies = LinkedInScraper.load_cookies_from_file(cookie_filepath)
        if not cookies:
            return False
        
        scraper = LinkedInScraper(headless=True)
        
        try:
            await scraper.start()
            valid = await scraper.login_with_cookies(cookies)
            return valid
        finally:
            await scraper.stop()
    
    def list_available_cookies(self) -> List[str]:
        """List all available cookie files."""
        return [str(f) for f in self.cookies_dir.glob("*.json")]


class MultiAccountScraper:
    """
    Manages multiple LinkedIn accounts for scalable scraping.
    Rotates accounts to avoid rate limiting.
    """
    
    def __init__(
        self,
        accounts: List[Dict[str, str]],
        cookies_dir: str = "cookies",
        max_profiles_per_account: int = 50,
        cooldown_minutes: int = 30
    ):
        self.accounts = accounts
        self.cookies_dir = Path(cookies_dir)
        self.max_profiles_per_account = max_profiles_per_account
        self.cooldown_minutes = cooldown_minutes
        
        self.account_usage: Dict[str, Dict] = {
            acc['email']: {
                'profiles_scraped': 0,
                'last_used': None,
                'is_available': True
            }
            for acc in accounts
        }
        
        self.current_scraper: Optional[LinkedInScraper] = None
        self.current_account: Optional[str] = None
    
    def _get_available_account(self) -> Optional[Dict[str, str]]:
        """Get the next available account for scraping."""
        now = datetime.utcnow()
        
        for account in self.accounts:
            email = account['email']
            usage = self.account_usage[email]
            
            # Check if account is on cooldown
            if usage['last_used']:
                minutes_since_use = (now - usage['last_used']).total_seconds() / 60
                if minutes_since_use < self.cooldown_minutes and usage['profiles_scraped'] >= self.max_profiles_per_account:
                    continue
            
            # Reset counter if cooldown has passed
            if usage['last_used']:
                minutes_since_use = (now - usage['last_used']).total_seconds() / 60
                if minutes_since_use >= self.cooldown_minutes:
                    usage['profiles_scraped'] = 0
            
            if usage['profiles_scraped'] < self.max_profiles_per_account and usage['is_available']:
                return account
        
        return None
    
    async def initialize_account(self, email: str, password: str) -> bool:
        """Initialize and login with a specific account."""
        self.current_scraper = LinkedInScraper()
        await self.current_scraper.start()
        
        # Try cookies first
        cookie_file = self.cookies_dir / f"{email.replace('@', '_at_').replace('.', '_')}.json"
        if cookie_file.exists():
            cookies = LinkedInScraper.load_cookies_from_file(str(cookie_file))
            if await self.current_scraper.login_with_cookies(cookies):
                self.current_account = email
                return True
        
        # Fall back to username/password login
        success, cookies = await self.current_scraper.login(email, password)
        if success:
            await self.current_scraper.save_cookies_to_file(str(cookie_file))
            self.current_account = email
            return True
        
        return False
    
    async def scrape_profiles(self, profile_urls: List[str]) -> List[Dict[str, Any]]:
        """
        Scrape multiple profiles using account rotation.
        
        Returns:
            List of scrape results
        """
        results = []
        
        for profile_url in profile_urls:
            # Check if we need to switch accounts
            if self.current_account:
                usage = self.account_usage[self.current_account]
                if usage['profiles_scraped'] >= self.max_profiles_per_account:
                    logger.info(f"Account {self.current_account} reached limit, switching...")
                    if self.current_scraper:
                        await self.current_scraper.stop()
                    self.current_scraper = None
                    self.current_account = None
            
            # Get a new account if needed
            if not self.current_account:
                account = self._get_available_account()
                if not account:
                    logger.warning("No available accounts. All on cooldown.")
                    # Wait for cooldown
                    await asyncio.sleep(self.cooldown_minutes * 60)
                    account = self._get_available_account()
                
                if account:
                    success = await self.initialize_account(account['email'], account['password'])
                    if not success:
                        self.account_usage[account['email']]['is_available'] = False
                        continue
                else:
                    logger.error("No accounts available for scraping")
                    break
            
            # Scrape the profile
            result = await self.current_scraper.scrape_profile(profile_url)
            results.append(result)
            
            # Update usage stats
            if self.current_account:
                self.account_usage[self.current_account]['profiles_scraped'] += 1
                self.account_usage[self.current_account]['last_used'] = datetime.utcnow()
            
            # Random delay between profiles
            await asyncio.sleep(random.uniform(5, 10))
        
        # Cleanup
        if self.current_scraper:
            await self.current_scraper.stop()
        
        return results
