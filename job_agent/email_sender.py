import smtplib
import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from typing import Dict, Optional
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class EmailSender:
    def __init__(self, gmail_email: str, gmail_app_password: str):
        self.gmail_email = gmail_email
        self.gmail_app_password = gmail_app_password
        self.smtp_server = "smtp.gmail.com"
        self.smtp_port = 587
    
    def send_email(self, recipient_email: str, subject: str, body: str, 
                   resume_path: Optional[str] = None) -> bool:
        """Send email with optional resume attachment"""
        try:
            # Create message
            msg = MIMEMultipart()
            msg['From'] = self.gmail_email
            msg['To'] = recipient_email
            msg['Subject'] = subject
            
            # Add body
            msg.attach(MIMEText(body, 'plain'))
            
            # Add resume attachment if provided
            if resume_path and os.path.exists(resume_path):
                self._attach_file(msg, resume_path)
            
            # Send email
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.gmail_email, self.gmail_app_password)
            text = msg.as_string()
            server.sendmail(self.gmail_email, recipient_email, text)
            server.quit()
            
            logger.info(f"Email sent successfully to {recipient_email}")
            return True
            
        except Exception as e:
            logger.error(f"Error sending email: {e}")
            return False
    
    def _attach_file(self, msg: MIMEMultipart, file_path: str):
        """Attach file to email"""
        try:
            with open(file_path, "rb") as attachment:
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(attachment.read())
            
            encoders.encode_base64(part)
            
            filename = os.path.basename(file_path)
            part.add_header(
                'Content-Disposition',
                f'attachment; filename= {filename}'
            )
            
            msg.attach(part)
            
        except Exception as e:
            logger.error(f"Error attaching file: {e}")
    
    def send_application_email(self, job: Dict, email_content: Dict, 
                              resume_path: Optional[str] = None) -> Dict:
        """Send application email to job"""
        results = {
            'sent': False,
            'email_sent': '',
            'error': '',
            'timestamp': datetime.now().isoformat()
        }
        
        try:
            # Try to find recruiter email first
            company = job.get('company', '')
            
            # For demo purposes, we'll use generated emails
            # In production, you might want to verify these first
            from .email_generator import EmailGenerator
            generator = EmailGenerator("")  # We don't need API key for email generation
            
            company_emails = generator.generate_company_emails(company)
            
            # Try each email format
            for email in company_emails:
                success = self.send_email(
                    recipient_email=email,
                    subject=email_content.get('subject', ''),
                    body=email_content.get('body', ''),
                    resume_path=resume_path
                )
                
                if success:
                    results['sent'] = True
                    results['email_sent'] = email
                    logger.info(f"Application sent to {email}")
                    break
                else:
                    logger.warning(f"Failed to send to {email}, trying next...")
            
            if not results['sent']:
                results['error'] = "Failed to send to any generated email addresses"
                
        except Exception as e:
            results['error'] = str(e)
            logger.error(f"Error in send_application_email: {e}")
        
        return results
    
    def send_followup_email(self, job: Dict, email_content: Dict) -> Dict:
        """Send follow-up email"""
        results = {
            'sent': False,
            'email_sent': '',
            'error': '',
            'timestamp': datetime.now().isoformat()
        }
        
        try:
            # This would typically use the same email that received the original application
            # For now, we'll use the same logic as application email
            company = job.get('company', '')
            
            from .email_generator import EmailGenerator
            generator = EmailGenerator("")
            company_emails = generator.generate_company_emails(company)
            
            for email in company_emails:
                success = self.send_email(
                    recipient_email=email,
                    subject=email_content.get('subject', ''),
                    body=email_content.get('body', '')
                )
                
                if success:
                    results['sent'] = True
                    results['email_sent'] = email
                    break
            
            if not results['sent']:
                results['error'] = "Failed to send follow-up"
                
        except Exception as e:
            results['error'] = str(e)
            logger.error(f"Error sending follow-up: {e}")
        
        return results
    
    def test_connection(self) -> bool:
        """Test SMTP connection"""
        try:
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.gmail_email, self.gmail_app_password)
            server.quit()
            logger.info("SMTP connection test successful")
            return True
        except Exception as e:
            logger.error(f"SMTP connection test failed: {e}")
            return False
