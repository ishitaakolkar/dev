import json
import re
import hashlib
from typing import Dict, List, Optional, Tuple
import google.generativeai as genai
import logging

logger = logging.getLogger(__name__)

class JobMatcher:
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
    
    def extract_experience_requirement(self, job_description: str) -> int:
        """Extract years of experience required from job description"""
        if not job_description:
            return 0
        
        # Look for patterns like "0-2 years", "2+ years", "entry level", etc.
        patterns = [
            r'(\d+)-(\d+)\s*years?',
            r'(\d+)\+?\s*years?',
            r'entry level',
            r'junior',
            r'associate',
            r'mid-level',
            r'senior'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, job_description.lower())
            if match:
                if 'entry' in pattern or 'junior' in pattern or 'associate' in pattern:
                    return 1
                elif 'senior' in pattern or 'mid' in pattern:
                    return 5
                elif match.groups():
                    return int(match.group(1))
        
        return 2  # Default assumption
    
    def filter_by_location(self, job: Dict, preferred_locations: List[str]) -> bool:
        """Check if job location matches preferences"""
        job_location = job.get('location', '').lower()
        
        # Allow remote jobs
        if 'remote' in job_location:
            return True
        
        # Check if any preferred location is in job location
        for pref_loc in preferred_locations:
            if pref_loc.lower() in job_location:
                return True
        
        return False
    
    def filter_by_experience(self, job: Dict, max_experience: int) -> bool:
        """Check if job experience requirement is within limits"""
        job_desc = job.get('job_description', '')
        required_exp = self.extract_experience_requirement(job_desc)
        return required_exp <= max_experience
    
    def calculate_match_score(self, profile: Dict, job: Dict) -> Tuple[int, Dict]:
        """Use LLM to calculate job match score and provide analysis"""
        prompt = f"""
        You are a career advisor analyzing job matches. Please evaluate this job against the candidate's profile.

        CANDIDATE PROFILE:
        Name: {profile.get('name', 'N/A')}
        Email: {profile.get('email', 'N/A')}
        Preferred Roles: {', '.join(profile.get('preferred_roles', []))}
        Preferred Locations: {', '.join(profile.get('preferred_locations', []))}
        Skills: {', '.join(profile.get('skills', []))}
        Projects: {', '.join(profile.get('projects', []))}
        Achievements: {', '.join(profile.get('achievements', []))}
        Target Companies: {', '.join(profile.get('target_companies', []))}

        JOB DETAILS:
        Company: {job.get('company', 'N/A')}
        Role: {job.get('role', 'N/A')}
        Location: {job.get('location', 'N/A')}
        Description: {job.get('job_description', 'N/A')}

        Please analyze and return a JSON response with:
        {{
            "match_score": 0-100,
            "reason": "Brief explanation of why this job matches or doesn't match",
            "relevant_skills": ["skill1", "skill2"],
            "missing_skills": ["skill1", "skill2"]
        }}

        Consider:
        - Role alignment with preferred roles
        - Skill overlap
        - Experience level match
        - Company fit (if in target companies)
        - Location preference
        """
        
        try:
            response = self.model.generate_content(prompt)
            result_text = response.text
            
            # Extract JSON from response
            json_match = re.search(r'\{.*\}', result_text, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())
                return result.get('match_score', 0), result
            else:
                logger.warning("Could not extract JSON from LLM response")
                return 50, {"reason": "Unable to analyze properly", "relevant_skills": [], "missing_skills": []}
                
        except Exception as e:
            logger.error(f"Error in LLM matching: {e}")
            return 30, {"reason": "Error in analysis", "relevant_skills": [], "missing_skills": []}
    
    def generate_job_id(self, job: Dict) -> str:
        """Generate unique job ID"""
        content = f"{job.get('company', '')}{job.get('role', '')}{job.get('job_link', '')}"
        return hashlib.md5(content.encode()).hexdigest()[:16]
    
    def match_jobs(self, jobs: List[Dict], profile_path: str, 
                   match_threshold: int = 70, max_experience: int = 2) -> List[Dict]:
        """Filter and score jobs based on profile"""
        profile = self.load_profile(profile_path)
        if not profile:
            logger.error("No profile found")
            return []
        
        preferred_locations = profile.get('preferred_locations', [])
        matched_jobs = []
        
        for job in jobs:
            try:
                # Apply basic filters first
                if not self.filter_by_location(job, preferred_locations):
                    continue
                
                if not self.filter_by_experience(job, max_experience):
                    continue
                
                # Calculate match score
                match_score, analysis = self.calculate_match_score(profile, job)
                
                if match_score >= match_threshold:
                    job['match_score'] = match_score
                    job['match_reason'] = analysis.get('reason', '')
                    job['relevant_skills'] = analysis.get('relevant_skills', [])
                    job['missing_skills'] = analysis.get('missing_skills', [])
                    job['job_id'] = self.generate_job_id(job)
                    
                    matched_jobs.append(job)
                    logger.info(f"Matched job: {job['company']} - {job['role']} (Score: {match_score})")
                
            except Exception as e:
                logger.error(f"Error processing job {job.get('company', 'Unknown')}: {e}")
                continue
        
        logger.info(f"Total matched jobs: {len(matched_jobs)}")
        return matched_jobs
