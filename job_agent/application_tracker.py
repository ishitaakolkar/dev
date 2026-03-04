import pandas as pd
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import hashlib
import logging

logger = logging.getLogger(__name__)

class ApplicationTracker:
    def __init__(self, excel_path: str):
        self.excel_path = excel_path
        self.columns = [
            'Company',
            'Role', 
            'Job_Link',
            'Match_Score',
            'Project_Used',
            'Email_Generated',
            'Email_Sent',
            'Date_Applied',
            'Status',
            'Notes',
            'Job_ID'
        ]
        self._initialize_excel()
    
    def _initialize_excel(self):
        """Initialize Excel file with headers if it doesn't exist"""
        try:
            if not os.path.exists(self.excel_path):
                df = pd.DataFrame(columns=self.columns)
                df.to_excel(self.excel_path, index=False)
                logger.info(f"Created new Excel tracker: {self.excel_path}")
        except Exception as e:
            logger.error(f"Error initializing Excel file: {e}")
    
    def generate_job_id(self, job: Dict) -> str:
        """Generate unique job ID"""
        content = f"{job.get('company', '')}{job.get('role', '')}{job.get('job_link', '')}"
        return hashlib.md5(content.encode()).hexdigest()[:16]
    
    def job_exists(self, job_id: str) -> bool:
        """Check if job already exists in tracker"""
        try:
            df = pd.read_excel(self.excel_path)
            return job_id in df['Job_ID'].values
        except Exception as e:
            logger.error(f"Error checking job existence: {e}")
            return False
    
    def add_application(self, job: Dict, project: Dict, email_generated: bool = False, 
                       email_sent: bool = False) -> bool:
        """Add new job application to tracker"""
        try:
            job_id = self.generate_job_id(job)
            
            # Check if already exists
            if self.job_exists(job_id):
                logger.info(f"Job {job_id} already exists in tracker")
                return False
            
            # Create new row
            new_row = {
                'Company': job.get('company', ''),
                'Role': job.get('role', ''),
                'Job_Link': job.get('job_link', ''),
                'Match_Score': job.get('match_score', 0),
                'Project_Used': project.get('name', ''),
                'Email_Generated': email_generated,
                'Email_Sent': email_sent,
                'Date_Applied': datetime.now().strftime('%Y-%m-%d') if email_sent else '',
                'Status': 'Applied' if email_sent else 'Pending',
                'Notes': '',
                'Job_ID': job_id
            }
            
            # Load existing data
            df = pd.read_excel(self.excel_path)
            
            # Add new row
            df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
            
            # Save back to Excel
            df.to_excel(self.excel_path, index=False)
            
            logger.info(f"Added application: {job.get('company')} - {job.get('role')}")
            return True
            
        except Exception as e:
            logger.error(f"Error adding application: {e}")
            return False
    
    def update_application_status(self, job_id: str, status: str, notes: str = '') -> bool:
        """Update application status and notes"""
        try:
            df = pd.read_excel(self.excel_path)
            
            # Find the row
            mask = df['Job_ID'] == job_id
            if not mask.any():
                logger.warning(f"Job ID {job_id} not found")
                return False
            
            # Update status and notes
            df.loc[mask, 'Status'] = status
            if notes:
                df.loc[mask, 'Notes'] = notes
            
            # Save back
            df.to_excel(self.excel_path, index=False)
            
            logger.info(f"Updated application {job_id} status to {status}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating application: {e}")
            return False
    
    def mark_email_sent(self, job_id: str, email_address: str = '') -> bool:
        """Mark email as sent for a job"""
        try:
            df = pd.read_excel(self.excel_path)
            
            mask = df['Job_ID'] == job_id
            if not mask.any():
                return False
            
            df.loc[mask, 'Email_Sent'] = True
            df.loc[mask, 'Date_Applied'] = datetime.now().strftime('%Y-%m-%d')
            df.loc[mask, 'Status'] = 'Applied'
            
            if email_address:
                current_notes = df.loc[mask, 'Notes'].iloc[0] or ''
                df.loc[mask, 'Notes'] = f"Email sent to: {email_address}. {current_notes}"
            
            df.to_excel(self.excel_path, index=False)
            
            logger.info(f"Marked email sent for job {job_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error marking email sent: {e}")
            return False
    
    def get_applications_for_followup(self, days_threshold: int = 5) -> List[Dict]:
        """Get applications that need follow-up"""
        try:
            df = pd.read_excel(self.excel_path)
            
            # Filter for applied applications older than threshold
            threshold_date = datetime.now() - timedelta(days=days_threshold)
            
            mask = (
                (df['Status'] == 'Applied') &
                (df['Email_Sent'] == True) &
                (df['Date_Applied'] != '')
            )
            
            followup_apps = []
            
            for _, row in df[mask].iterrows():
                try:
                    applied_date = pd.to_datetime(row['Date_Applied'])
                    if applied_date <= threshold_date:
                        followup_apps.append(row.to_dict())
                except:
                    continue
            
            logger.info(f"Found {len(followup_apps)} applications for follow-up")
            return followup_apps
            
        except Exception as e:
            logger.error(f"Error getting follow-up applications: {e}")
            return []
    
    def get_all_applications(self) -> List[Dict]:
        """Get all applications from tracker"""
        try:
            df = pd.read_excel(self.excel_path)
            return df.to_dict('records')
        except Exception as e:
            logger.error(f"Error getting all applications: {e}")
            return []
    
    def get_today_applications_count(self) -> int:
        """Count applications sent today"""
        try:
            df = pd.read_excel(self.excel_path)
            today = datetime.now().strftime('%Y-%m-%d')
            
            mask = (
                (df['Date_Applied'] == today) &
                (df['Email_Sent'] == True)
            )
            
            return len(df[mask])
            
        except Exception as e:
            logger.error(f"Error counting today's applications: {e}")
            return 0
    
    def get_statistics(self) -> Dict:
        """Get application statistics"""
        try:
            df = pd.read_excel(self.excel_path)
            
            stats = {
                'total_applications': len(df),
                'emails_sent': len(df[df['Email_Sent'] == True]),
                'pending_applications': len(df[df['Status'] == 'Pending']),
                'applied_applications': len(df[df['Status'] == 'Applied']),
                'today_sent': self.get_today_applications_count(),
                'average_match_score': df['Match_Score'].mean() if len(df) > 0 else 0
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting statistics: {e}")
            return {}
    
    def export_to_csv(self, output_path: str) -> bool:
        """Export applications to CSV"""
        try:
            df = pd.read_excel(self.excel_path)
            df.to_csv(output_path, index=False)
            logger.info(f"Exported applications to {output_path}")
            return True
        except Exception as e:
            logger.error(f"Error exporting to CSV: {e}")
            return False
