#!/usr/bin/env python3
"""
Script to collect LinkedIn cookies for authentication.
Run this script to set up LinkedIn authentication before running the scraper.

Usage:
    python -m scripts.collect_cookies
    
    Or with specific account:
    python -m scripts.collect_cookies --email your@email.com --password yourpassword
"""

import argparse
import asyncio
import os
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.scraper.linkedin_scraper import CookieCollector


async def main():
    parser = argparse.ArgumentParser(description="Collect LinkedIn cookies for authentication")
    parser.add_argument("--email", help="LinkedIn account email")
    parser.add_argument("--password", help="LinkedIn account password")
    parser.add_argument("--cookies-dir", default="cookies", help="Directory to store cookies")
    parser.add_argument("--validate", action="store_true", help="Validate existing cookies")
    
    args = parser.parse_args()
    
    collector = CookieCollector(cookies_dir=args.cookies_dir)
    
    if args.validate:
        # Validate existing cookies
        print("Validating existing cookies...")
        cookie_files = collector.list_available_cookies()
        
        if not cookie_files:
            print("No cookie files found.")
            return
        
        for cookie_file in cookie_files:
            print(f"  Checking {cookie_file}...", end=" ")
            is_valid = await collector.validate_cookies(cookie_file)
            print("✓ Valid" if is_valid else "✗ Invalid")
        
        return
    
    # Get credentials
    email = args.email or os.getenv("LINKEDIN_EMAIL_1") or input("Enter LinkedIn email: ")
    password = args.password or os.getenv("LINKEDIN_PASSWORD_1") or input("Enter LinkedIn password: ")
    
    if not email or not password:
        print("Error: Email and password are required")
        sys.exit(1)
    
    print(f"\nCollecting cookies for {email}...")
    print("Note: Browser will open. Complete any security verification if prompted.")
    
    success, cookie_path = await collector.collect_cookies(email, password)
    
    if success:
        print(f"\n✓ Success! Cookies saved to: {cookie_path}")
        print("\nYou can now use the scraper with these cookies.")
    else:
        print("\n✗ Failed to collect cookies. Check credentials and try again.")
        print("Tip: If there's a security challenge, you may need to verify manually.")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
