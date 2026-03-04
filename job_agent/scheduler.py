import time
import logging
from datetime import datetime, timedelta
import os
import sys

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import config
from job_scraper import JobScraper
from job_matcher import JobMatcher
from project_matcher import ProjectMatcher
from email_generator import EmailGenerator
from email_sender import EmailSender
from application_tracker import ApplicationTracker

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('job_agent.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class JobScheduler:
    def __init__(self):
        self.scraper = JobScraper()
        self.matcher = JobMatcher(config.gemini_api_key) if config.gemini_api_key else None
        self.project_matcher = ProjectMatcher(config.gemini_api_key) if config.gemini_api_key else None
        self.email_generator = EmailGenerator(config.gemini_api_key) if config.gemini_api_key else None
        self.email_sender = EmailSender(config.gmail_email, config.gmail_app_password) if config.gmail_email else None
        self.tracker = ApplicationTracker(config.applications_path)
        
        logger.info("Job Scheduler initialized")
    
    def run_pipeline(self, auto_send_emails: bool = False):
        """Run the complete job application pipeline"""
        logger.info("=" * 50)
        logger.info("Starting job application pipeline")
        logger.info(f"Timestamp: {datetime.now()}")
        
        try:
            # Step 1: Discover jobs
            logger.info("Step 1: Discovering jobs...")
            jobs = self.scraper.discover_jobs(limit=50)
            logger.info(f"Jobs discovered: {len(jobs)}")
            
            if not jobs:
                logger.warning("No jobs discovered, ending pipeline")
                return
            
            # Step 2: Filter and match jobs
            if not self.matcher:
                logger.error("Gemini API key not configured, cannot match jobs")
                return
                
            logger.info("Step 2: Matching jobs with profile...")
            matched_jobs = self.matcher.match_jobs(
                jobs, 
                config.profile_path,
                config.match_score_threshold,
                config.max_experience_years
            )
            logger.info(f"Relevant jobs found: {len(matched_jobs)}")
            
            if not matched_jobs:
                logger.warning("No jobs matched the criteria")
                return
            
            # Step 3: Process each matched job
            processed_count = 0
            for job in matched_jobs:
                try:
                    # Check if already exists
                    if self.tracker.job_exists(job['job_id']):
                        logger.info(f"Job already exists: {job['company']} - {job['role']}")
                        continue
                    
                    # Step 4: Select best project
                    logger.info(f"Step 4: Selecting project for {job['company']} - {job['role']}")
                    project = self.project_matcher.select_best_project(job, config.profile_path)
                    
                    if not project:
                        logger.warning(f"No project found for job: {job['company']}")
                        continue
                    
                    # Step 5: Add to tracker
                    self.tracker.add_application(job, project, email_generated=False, email_sent=False)
                    
                    # Step 6: Generate email
                    logger.info(f"Step 6: Generating email for {job['company']}")
                    email_content = self.email_generator.generate_application_email(job, project, config.profile_path)
                    
                    if not email_content:
                        logger.warning(f"Failed to generate email for {job['company']}")
                        continue
                    
                    # Save email draft
                    draft_path = self.email_generator.save_email_draft(job, email_content, config.emails_drafts_path)
                    
                    # Update tracker
                    self.tracker.update_application_status(job['job_id'], 'Email Generated', f"Draft: {draft_path}")
                    
                    # Step 7: Send email (if auto-send is enabled)
                    if auto_send_emails and self.email_sender:
                        # Check daily limit
                        today_count = self.tracker.get_today_applications_count()
                        if today_count >= config.max_emails_per_day:
                            logger.info(f"Daily email limit reached ({config.max_emails_per_day})")
                            break
                        
                        logger.info(f"Step 7: Sending email to {job['company']}")
                        
                        resume_path = config.resume_path if os.path.exists(config.resume_path) else None
                        result = self.email_sender.send_application_email(job, email_content, resume_path)
                        
                        if result['sent']:
                            self.tracker.mark_email_sent(job['job_id'], result['email_sent'])
                            logger.info(f"Email sent successfully to {result['email_sent']}")
                            processed_count += 1
                        else:
                            logger.error(f"Failed to send email: {result['error']}")
                    else:
                        logger.info(f"Email generated but not sent (auto-send disabled)")
                        processed_count += 1
                    
                    # Small delay between processing jobs
                    time.sleep(2)
                    
                except Exception as e:
                    logger.error(f"Error processing job {job.get('company', 'Unknown')}: {e}")
                    continue
            
            # Step 8: Check for follow-ups
            logger.info("Step 8: Checking for follow-ups...")
            followup_apps = self.tracker.get_applications_for_followup()
            logger.info(f"Applications needing follow-up: {len(followup_apps)}")
            
            # Generate follow-up emails (but don't send automatically)
            for app in followup_apps:
                try:
                    followup_email = self.email_generator.generate_followup_email(
                        {
                            'company': app['Company'],
                            'role': app['Role']
                        },
                        config.profile_path
                    )
                    
                    if followup_email:
                        # Save follow-up draft
                        followup_path = os.path.join(config.emails_drafts_path, f"followup_{app['Job_ID']}.txt")
                        os.makedirs(config.emails_drafts_path, exist_ok=True)
                        
                        with open(followup_path, 'w') as f:
                            f.write(f"Subject: {followup_email.get('subject', '')}\n\n")
                            f.write(followup_email.get('body', ''))
                        
                        logger.info(f"Follow-up email generated: {followup_path}")
                        
                except Exception as e:
                    logger.error(f"Error generating follow-up for {app['Company']}: {e}")
            
            # Summary
            logger.info("=" * 50)
            logger.info("Pipeline completed successfully")
            logger.info(f"Jobs processed: {processed_count}")
            logger.info(f"Follow-ups generated: {len(followup_apps)}")
            
            # Get final statistics
            stats = self.tracker.get_statistics()
            logger.info(f"Total applications in tracker: {stats.get('total_applications', 0)}")
            logger.info(f"Emails sent: {stats.get('emails_sent', 0)}")
            logger.info(f"Today's applications: {stats.get('today_sent', 0)}")
            
        except Exception as e:
            logger.error(f"Pipeline failed: {e}")
    
    def run_scheduler(self, auto_send_emails: bool = False):
        """Run the scheduler continuously"""
        logger.info("Starting continuous job scheduler")
        logger.info(f"Search interval: {config.job_search_interval_hours} hours")
        
        while True:
            try:
                logger.info(f"Running scheduled job search at {datetime.now()}")
                self.run_pipeline(auto_send_emails)
                
                # Wait for next run
                logger.info(f"Waiting {config.job_search_interval_hours} hours for next run...")
                time.sleep(config.job_search_interval_hours * 3600)
                
            except KeyboardInterrupt:
                logger.info("Scheduler stopped by user")
                break
            except Exception as e:
                logger.error(f"Scheduler error: {e}")
                logger.info("Retrying in 1 hour...")
                time.sleep(3600)

def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Job Application Assistant Scheduler')
    parser.add_argument('--auto-send', action='store_true', 
                       help='Automatically send emails (use with caution)')
    parser.add_argument('--run-once', action='store_true',
                       help='Run pipeline once instead of continuously')
    parser.add_argument('--test', action='store_true',
                       help='Test configuration and exit')
    
    args = parser.parse_args()
    
    # Test configuration
    if args.test:
        logger.info("Testing configuration...")
        
        # Check required files
        if not os.path.exists(config.profile_path):
            logger.error(f"Profile file not found: {config.profile_path}")
        else:
            logger.info("✓ Profile file exists")
        
        # Check API keys
        if not config.gemini_api_key:
            logger.warning("⚠️ Gemini API key not configured")
        else:
            logger.info("✓ Gemini API key configured")
        
        if not config.gmail_email:
            logger.warning("⚠️ Gmail email not configured")
        else:
            logger.info("✓ Gmail configured")
        
        # Test email connection if configured
        if config.gmail_email and config.gmail_app_password:
            try:
                sender = EmailSender(config.gmail_email, config.gmail_app_password)
                if sender.test_connection():
                    logger.info("✓ Email connection successful")
                else:
                    logger.error("✗ Email connection failed")
            except Exception as e:
                logger.error(f"✗ Email connection error: {e}")
        
        return
    
    # Create scheduler
    scheduler = JobScheduler()
    
    if args.run_once:
        logger.info("Running pipeline once...")
        scheduler.run_pipeline(auto_send_emails=args.auto_send)
    else:
        logger.info("Starting continuous scheduler...")
        scheduler.run_scheduler(auto_send_emails=args.auto_send)

if __name__ == "__main__":
    main()
