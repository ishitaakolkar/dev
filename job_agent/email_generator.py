import json
import re
import os
from typing import Dict, Optional
import google.generativeai as genai
import logging

logger = logging.getLogger(__name__)

class EmailGenerator:
    def __init__(self, gemini_api_key: str):
        genai.configure(api_key=gemini_api_key)
        self.model = genai.GenerativeModel('gemini-pro')
    
    def load_profile(self, profile_path: str) -> Dict:
        """Load user profile from JSON file"""
        try:
            with open(profile_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading profile: {e}")
            return {}
    
    def find_recruiter_email(self, job: Dict) -> Optional[str]:
        """Try to find recruiter email from job description or page"""
        job_description = job.get('job_description', '')
        
        # Look for email patterns in job description
        email_patterns = [
            r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        ]
        
        for pattern in email_patterns:
            matches = re.findall(pattern, job_description)
            if matches:
                # Return the first email found
                return matches[0]
        
        return None
    
    def generate_company_emails(self, company: str) -> list:
        """Generate common company HR emails"""
        company_domain = company.lower().replace(' ', '').replace('.', '')
        company_domain = re.sub(r'[^a-z0-9]', '', company_domain)
        
        if '.' not in company_domain:
            company_domain += '.com'
        
        common_formats = [
            f"hr@{company_domain}",
            f"careers@{company_domain}",
            f"jobs@{company_domain}",
            f"recruitment@{company_domain}",
            f"talent@{company_domain}"
        ]
        
        return common_formats
    
    def generate_application_email(self, job: Dict, project: Dict, profile_path: str) -> Dict:
        """Generate a personalized application email"""
        profile = self.load_profile(profile_path)
        if not profile:
            logger.error("No profile found")
            return {}
        
        name = profile.get('name', 'Applicant')
        company = job.get('company', 'Company')
        role = job.get('role', 'Role')
        project_summary = project.get('summary', 'my recent project')
        matching_skills = project.get('matching_skills', [])
        
        prompt = f"""
        Generate a professional and concise job application email with the following details:

        APPLICANT:
        Name: {name}
        Skills: {', '.join(profile.get('skills', []))}
        
        JOB:
        Company: {company}
        Role: {role}
        Description: {job.get('job_description', '')[:500]}
        
        PROJECT:
        {project_summary}
        Relevant Skills: {', '.join(matching_skills)}
        
        Requirements:
        - Keep it under 150 words
        - Professional but friendly tone
        - Mention the specific role and company
        - Reference the selected project and its impact
        - Include relevant skills naturally
        - End with a clear call to action
        
        Return JSON format:
        {{
            "subject": "Brief, professional subject line",
            "body": "Complete email body"
        }}
        """
        
        try:
            response = self.model.generate_content(prompt)
            result_text = response.text
            
            # Extract JSON from response
            json_match = re.search(r'\{.*\}', result_text, re.DOTALL)
            if json_match:
                email_content = json.loads(json_match.group())
                return email_content
            else:
                # Fallback email
                subject = f"Application for {role} at {company}"
                body = f"""Hi,

I came across the {role} opening at {company} and it strongly aligns with my recent work.

In one of my projects I built {project_summary}. This involved working with {', '.join(matching_skills[:3]) if matching_skills else 'various technologies'}.

I would love to explore how I could contribute to your team.

Best,
{name}"""
                
                return {"subject": subject, "body": body}
                
        except Exception as e:
            logger.error(f"Error generating email: {e}")
            return {}
    
    def generate_followup_email(self, job: Dict, profile_path: str) -> Dict:
        """Generate a follow-up email"""
        profile = self.load_profile(profile_path)
        if not profile:
            return {}
        
        name = profile.get('name', 'Applicant')
        company = job.get('company', 'Company')
        role = job.get('role', 'Role')
        
        prompt = f"""
        Generate a professional follow-up email for a job application sent 5+ days ago.

        APPLICANT: {name}
        COMPANY: {company}
        ROLE: {role}

        Requirements:
        - Polite and professional tone
        - Brief reminder of the application
        - Express continued interest
        - Ask about next steps
        - Under 100 words
        
        Return JSON format:
        {{
            "subject": "Follow-up: Application for {role}",
            "body": "Complete email body"
        }}
        """
        
        try:
            response = self.model.generate_content(prompt)
            result_text = response.text
            
            json_match = re.search(r'\{.*\}', result_text, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            else:
                # Fallback
                subject = f"Follow-up: Application for {role}"
                body = f"""Hi,

I hope you're doing well. I applied for the {role} position at {company} last week and wanted to follow up on my application.

I remain very interested in this opportunity and would love to learn about the next steps in the hiring process.

Best regards,
{name}"""
                
                return {"subject": subject, "body": body}
                
        except Exception as e:
            logger.error(f"Error generating follow-up: {e}")
            return {}
    
    def generate_linkedin_message(self, job: Dict, profile_path: str, recruiter_name: str = "") -> Dict:
        """Generate LinkedIn outreach message"""
        profile = self.load_profile(profile_path)
        if not profile:
            return {}
        
        name = profile.get('name', 'Applicant')
        company = job.get('company', 'Company')
        role = job.get('role', 'Role')
        
        prompt = f"""
        Generate a concise LinkedIn message for reaching out to someone at the company.

        APPLICANT: {name}
        COMPANY: {company}
        ROLE: {role}
        RECRUITER: {recruiter_name}

        Requirements:
        - Professional but conversational tone
        - Under 80 words
        - Mention the role application
        - Ask about team/work culture
        - No sales pressure
        
        Return JSON format:
        {{
            "message": "Complete LinkedIn message"
        }}
        """
        
        try:
            response = self.model.generate_content(prompt)
            result_text = response.text
            
            json_match = re.search(r'\{.*\}', result_text, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            else:
                # Fallback
                greeting = f"Hi {recruiter_name}" if recruiter_name else "Hi"
                message = f"""{greeting},

I noticed you work at {company}. I recently applied for the {role} position and would love to learn more about the team and the work being done there.

Would you be open to a brief chat about your experience at {company}?

Thanks,
{name}"""
                
                return {"message": message}
                
        except Exception as e:
            logger.error(f"Error generating LinkedIn message: {e}")
            return {}
    
    def save_email_draft(self, job: Dict, email_content: Dict, drafts_path: str) -> str:
        """Save email draft to file"""
        try:
            company = job.get('company', 'company').replace(' ', '_').replace('/', '_')
            filename = f"{company}_email.txt"
            filepath = os.path.join(drafts_path, filename)
            
            os.makedirs(drafts_path, exist_ok=True)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(f"Subject: {email_content.get('subject', '')}\n\n")
                f.write(email_content.get('body', ''))
            
            logger.info(f"Email draft saved: {filepath}")
            return filepath
            
        except Exception as e:
            logger.error(f"Error saving email draft: {e}")
            return ""
