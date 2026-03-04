import requests
import json
import re
from typing import List, Dict, Optional
from bs4 import BeautifulSoup
import time
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class JobScraper:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def scrape_wellfound_jobs(self, limit: int = 20) -> List[Dict]:
        """Simple scraper for Wellfound (AngelList) jobs"""
        jobs = []
        try:
            url = "https://wellfound.com/role/software-engineer"
            response = self.session.get(url, timeout=10)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Simple extraction - this is a basic implementation
            job_cards = soup.find_all('div', class_='job-card')[:limit]
            
            for card in job_cards:
                try:
                    company = card.find('h3', class_='company-name')
                    role = card.find('h2', class_='role-title')
                    location = card.find('div', class_='location')
                    link = card.find('a', href=True)
                    
                    if all([company, role, location, link]):
                        jobs.append({
                            'company': company.get_text().strip(),
                            'role': role.get_text().strip(),
                            'location': location.get_text().strip(),
                            'job_link': f"https://wellfound.com{link['href']}",
                            'source': 'wellfound'
                        })
                except Exception as e:
                    logger.warning(f"Error parsing job card: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"Error scraping Wellfound: {e}")
        
        return jobs
    
    def scrape_yc_jobs(self, limit: int = 20) -> List[Dict]:
        """Simple scraper for YC Jobs"""
        jobs = []
        try:
            url = "https://www.ycombinator.com/jobs"
            response = self.session.get(url, timeout=10)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Look for job listings
            job_listings = soup.find_all('div', class_='job')[:limit]
            
            for listing in job_listings:
                try:
                    company_elem = listing.find('span', class_='company')
                    title_elem = listing.find('span', class_='title')
                    location_elem = listing.find('span', class_='location')
                    link_elem = listing.find('a', href=True)
                    
                    if all([company_elem, title_elem, link_elem]):
                        jobs.append({
                            'company': company_elem.get_text().strip(),
                            'role': title_elem.get_text().strip(),
                            'location': location_elem.get_text().strip() if location_elem else 'Remote',
                            'job_link': f"https://www.ycombinator.com{link_elem['href']}",
                            'source': 'yc'
                        })
                except Exception as e:
                    logger.warning(f"Error parsing YC job: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"Error scraping YC Jobs: {e}")
        
        return jobs
    
    def generate_sample_jobs(self) -> List[Dict]:
        """Generate sample jobs for testing when scraping fails"""
        return [
            {
                'company': 'TechStartup Inc',
                'role': 'Software Engineer',
                'location': 'San Francisco, CA',
                'job_link': 'https://example.com/job1',
                'source': 'sample',
                'job_description': 'We are looking for a talented software engineer to join our team. Experience with Python, React, and cloud technologies required.'
            },
            {
                'company': 'AI Solutions',
                'role': 'Junior Developer',
                'location': 'Remote',
                'job_link': 'https://example.com/job2',
                'source': 'sample',
                'job_description': 'Join our AI team! Looking for developers with experience in machine learning, Python, and data processing.'
            },
            {
                'company': 'WebDev Agency',
                'role': 'Frontend Developer',
                'location': 'New York, NY',
                'job_link': 'https://example.com/job3',
                'source': 'sample',
                'job_description': 'Frontend developer needed with React, TypeScript, and modern web development skills.'
            }
        ]
    
    def discover_jobs(self, limit: int = 50) -> List[Dict]:
        """Discover jobs from multiple sources"""
        logger.info("Starting job discovery...")
        
        all_jobs = []
        
        # Try to scrape from different sources
        try:
            wellfound_jobs = self.scrape_wellfound_jobs(limit // 2)
            all_jobs.extend(wellfound_jobs)
            logger.info(f"Found {len(wellfound_jobs)} jobs from Wellfound")
        except Exception as e:
            logger.warning(f"Wellfound scraping failed: {e}")
        
        try:
            yc_jobs = self.scrape_yc_jobs(limit // 2)
            all_jobs.extend(yc_jobs)
            logger.info(f"Found {len(yc_jobs)} jobs from YC")
        except Exception as e:
            logger.warning(f"YC scraping failed: {e}")
        
        # If no jobs found, use sample data
        if not all_jobs:
            logger.info("No jobs found from scraping, using sample data")
            all_jobs = self.generate_sample_jobs()
        
        # Remove duplicates based on company + role
        unique_jobs = []
        seen = set()
        
        for job in all_jobs:
            key = f"{job['company'].lower()}_{job['role'].lower()}"
            if key not in seen:
                seen.add(key)
                unique_jobs.append(job)
        
        logger.info(f"Total unique jobs discovered: {len(unique_jobs)}")
        return unique_jobs[:limit]
