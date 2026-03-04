import os
import json
import re
from typing import Dict, List, Optional
import google.generativeai as genai
import logging
from PyPDF2 import PdfReader

logger = logging.getLogger(__name__)

class ResumeParser:
    def __init__(self, gemini_api_key: str):
        genai.configure(api_key=gemini_api_key)
        self.model = genai.GenerativeModel('gemini-pro')
    
    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """Extract text from PDF file"""
        try:
            with open(pdf_path, 'rb') as file:
                reader = PdfReader(file)
                text = ""
                for page in reader.pages:
                    text += page.extract_text() + "\n"
                return text
        except Exception as e:
            logger.error(f"Error extracting text from PDF: {e}")
            return ""
    
    def extract_email(self, text: str) -> Optional[str]:
        """Extract email address from text"""
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        matches = re.findall(email_pattern, text)
        return matches[0] if matches else None
    
    def extract_phone(self, text: str) -> Optional[str]:
        """Extract phone number from text"""
        phone_patterns = [
            r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',
            r'\+\d{1,3}[-.]?\d{3}[-.]?\d{3}[-.]?\d{4}',
            r'\(\d{3}\)\s*\d{3}[-.]?\d{4}'
        ]
        
        for pattern in phone_patterns:
            matches = re.findall(pattern, text)
            if matches:
                return matches[0]
        return None
    
    def extract_links(self, text: str) -> Dict[str, str]:
        """Extract LinkedIn and GitHub links"""
        links = {'linkedin': '', 'github': ''}
        
        # LinkedIn patterns
        linkedin_patterns = [
            r'linkedin\.com/in/[\w-]+',
            r'linkedin\.in/in/[\w-]+'
        ]
        
        for pattern in linkedin_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                links['linkedin'] = f"https://{matches[0]}"
                break
        
        # GitHub patterns
        github_patterns = [
            r'github\.com/[\w-]+',
            r'github\.com/[\w-]+/[\w-]+'
        ]
        
        for pattern in github_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                links['github'] = f"https://{matches[0]}"
                break
        
        return links
    
    def parse_with_ai(self, resume_text: str) -> Dict:
        """Use AI to parse resume into structured data"""
        prompt = f"""
        Parse this resume and extract the following information in JSON format:
        
        {{
            "name": "Full name",
            "email": "Email address",
            "phone": "Phone number",
            "linkedin_url": "LinkedIn profile URL",
            "skills": ["skill1", "skill2", "skill3"],
            "projects": [
                {{
                    "name": "Project Name",
                    "description": "Brief project description",
                    "technologies": ["tech1", "tech2"]
                }}
            ],
            "experience": [
                {{
                    "company": "Company Name",
                    "role": "Role/Position",
                    "duration": "Duration",
                    "description": "Brief description"
                }}
            ],
            "education": [
                {{
                    "degree": "Degree",
                    "institution": "Institution",
                    "year": "Year"
                }}
            ],
            "achievements": ["achievement1", "achievement2"],
            "preferred_roles": ["role1", "role2"],
            "preferred_locations": ["location1", "location2"]
        }}
        
        Resume Text:
        {resume_text[:8000]}  # Limit to first 8000 chars
        
        Return only valid JSON. If information is not found, use empty strings or empty arrays.
        """
        
        try:
            response = self.model.generate_content(prompt)
            result_text = response.text
            
            # Extract JSON from response
            json_match = re.search(r'\{.*\}', result_text, re.DOTALL)
            if json_match:
                parsed_data = json.loads(json_match.group())
                return parsed_data
            else:
                logger.warning("Could not extract JSON from AI response")
                return {}
                
        except Exception as e:
            logger.error(f"Error parsing resume with AI: {e}")
            return {}
    
    def parse_resume(self, pdf_path: str) -> Dict:
        """Main method to parse resume PDF"""
        logger.info(f"Parsing resume: {pdf_path}")
        
        # Extract text from PDF
        resume_text = self.extract_text_from_pdf(pdf_path)
        if not resume_text:
            logger.error("No text extracted from resume")
            return {}
        
        # Parse with AI
        parsed_data = self.parse_with_ai(resume_text)
        
        # Fallback manual extraction for critical fields
        if not parsed_data.get('email'):
            email = self.extract_email(resume_text)
            if email:
                parsed_data['email'] = email
        
        # Extract links
        links = self.extract_links(resume_text)
        if links['linkedin'] and not parsed_data.get('linkedin_url'):
            parsed_data['linkedin_url'] = links['linkedin']
        
        # Clean and standardize data
        parsed_data = self._clean_parsed_data(parsed_data)
        
        logger.info("Resume parsing completed")
        return parsed_data
    
    def _clean_parsed_data(self, data: Dict) -> Dict:
        """Clean and standardize parsed data"""
        cleaned = {}
        
        # Basic fields
        cleaned['name'] = data.get('name', '').strip()
        cleaned['email'] = data.get('email', '').strip()
        cleaned['phone'] = data.get('phone', '').strip()
        cleaned['linkedin_url'] = data.get('linkedin_url', '').strip()
        
        # Lists - ensure they are lists and clean items
        cleaned['skills'] = [skill.strip() for skill in data.get('skills', []) if skill.strip()]
        cleaned['achievements'] = [ach.strip() for ach in data.get('achievements', []) if ach.strip()]
        cleaned['preferred_roles'] = [role.strip() for role in data.get('preferred_roles', []) if role.strip()]
        cleaned['preferred_locations'] = [loc.strip() for loc in data.get('preferred_locations', []) if loc.strip()]
        
        # Projects - ensure proper structure
        projects = data.get('projects', [])
        cleaned_projects = []
        for project in projects:
            if isinstance(project, dict):
                cleaned_project = {
                    'name': project.get('name', '').strip(),
                    'description': project.get('description', '').strip(),
                    'technologies': [tech.strip() for tech in project.get('technologies', []) if tech.strip()]
                }
                if cleaned_project['name']:
                    cleaned_projects.append(cleaned_project)
        cleaned['projects'] = cleaned_projects
        
        # Target companies (extract from experience if available)
        experience = data.get('experience', [])
        target_companies = []
        for exp in experience:
            if isinstance(exp, dict) and exp.get('company'):
                target_companies.append(exp['company'].strip())
        cleaned['target_companies'] = target_companies
        
        return cleaned
    
    def generate_profile_from_resume(self, pdf_path: str, profile_path: str) -> bool:
        """Generate complete profile from resume"""
        try:
            parsed_data = self.parse_resume(pdf_path)
            
            if not parsed_data:
                logger.error("No data parsed from resume")
                return False
            
            # Load existing profile to preserve any manual additions
            from .profile_manager import ProfileManager
            profile_manager = ProfileManager(profile_path)
            existing_profile = profile_manager.load_profile()
            
            # Merge parsed data with existing profile
            merged_profile = existing_profile.copy()
            
            # Update with parsed data (only if fields are empty)
            for key, value in parsed_data.items():
                if not merged_profile.get(key) or key in ['skills', 'projects', 'achievements']:
                    if key in ['skills', 'projects', 'achievements']:
                        # Merge lists, avoiding duplicates
                        existing_list = merged_profile.get(key, [])
                        new_list = [item for item in value if item not in existing_list]
                        merged_profile[key] = existing_list + new_list
                    else:
                        merged_profile[key] = value
            
            # Save merged profile
            success = profile_manager.save_profile(merged_profile)
            
            if success:
                logger.info("Profile successfully generated from resume")
                return True
            else:
                logger.error("Failed to save generated profile")
                return False
                
        except Exception as e:
            logger.error(f"Error generating profile from resume: {e}")
            return False
