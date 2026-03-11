import os
from dataclasses import dataclass
from typing import List
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

@dataclass
class Config:
    # API Keys
    gemini_api_key: str = os.getenv("GEMINI_API_KEY", "")
    
    # Email Configuration
    gmail_email: str = os.getenv("GMAIL_EMAIL", "")
    gmail_app_password: str = os.getenv("GMAIL_APP_PASSWORD", "")
    
    # Current Company (to avoid applying to current employer)
    current_company: str = os.getenv("CURRENT_COMPANY", "")
    
    # Job Search Settings
    match_score_threshold: int = int(os.getenv("MATCH_SCORE_THRESHOLD", "70"))
    max_experience_years: int = int(os.getenv("MAX_EXPERIENCE_YEARS", "2"))
    max_emails_per_day: int = int(os.getenv("MAX_EMAILS_PER_DAY", "5"))
    job_search_interval_hours: int = int(os.getenv("JOB_SEARCH_INTERVAL_HOURS", "6"))
    
    # File Paths
    profile_path: str = "../data/profile.json"
    resume_path: str = "../data/resume.pdf"
    applications_path: str = "../data/applications.xlsx"
    emails_drafts_path: str = "../emails/drafts/"
    
    # Job Sources
    job_sources: List[str] = None
    
    def __post_init__(self):
        if self.job_sources is None:
            self.job_sources = [
                "https://www.wellfound.com/jobs",
                "https://www.ycombinator.com/jobs",
                "https://jobs.github.com"
            ]

config = Config()
