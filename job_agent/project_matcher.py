import json
import re
from typing import Dict, List, Tuple
import google.generativeai as genai
import logging

logger = logging.getLogger(__name__)

class ProjectMatcher:
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
    
    def extract_job_skills(self, job_description: str) -> List[str]:
        """Extract key skills from job description using LLM"""
        if not job_description:
            return []
        
        prompt = f"""
        Extract the key technical skills and technologies mentioned in this job description.
        Return only a JSON array of skill names.

        Job Description:
        {job_description}

        Example response:
        ["Python", "React", "AWS", "PostgreSQL", "Docker"]
        """
        
        try:
            response = self.model.generate_content(prompt)
            result_text = response.text
            
            # Extract JSON array from response
            json_match = re.search(r'\[.*?\]', result_text, re.DOTALL)
            if json_match:
                skills = json.loads(json_match.group())
                return [skill.strip() for skill in skills if skill.strip()]
            else:
                # Fallback: extract common tech terms
                common_tech = ['python', 'javascript', 'react', 'node', 'aws', 'docker', 'sql', 'mongodb', 
                              'typescript', 'java', 'c++', 'git', 'kubernetes', 'terraform', 'azure']
                found_skills = []
                for tech in common_tech:
                    if tech.lower() in job_description.lower():
                        found_skills.append(tech.title())
                return found_skills
                
        except Exception as e:
            logger.error(f"Error extracting skills: {e}")
            return []
    
    def calculate_project_overlap(self, job_skills: List[str], project: Dict) -> Tuple[int, List[str]]:
        """Calculate skill overlap between job and project"""
        project_desc = project.get('description', '').lower()
        project_tech = project.get('technologies', [])
        
        # Convert to lowercase for comparison
        job_skills_lower = [skill.lower() for skill in job_skills]
        project_tech_lower = [tech.lower() for tech in project_tech]
        
        # Find matching skills
        matching_skills = []
        for job_skill in job_skills_lower:
            if job_skill in project_tech_lower or job_skill in project_desc:
                matching_skills.append(job_skill.title())
        
        # Calculate overlap percentage
        overlap_score = 0
        if job_skills:
            overlap_score = (len(matching_skills) / len(job_skills)) * 100
        
        return int(overlap_score), matching_skills
    
    def select_best_project(self, job: Dict, profile_path: str) -> Dict:
        """Select the most relevant project for a job"""
        profile = self.load_profile(profile_path)
        if not profile:
            return {}
        
        projects = profile.get('projects', [])
        if not projects:
            logger.warning("No projects found in profile")
            return {}
        
        job_description = job.get('job_description', '')
        job_skills = self.extract_job_skills(job_description)
        
        if not job_skills:
            logger.warning("No skills extracted from job description")
            return projects[0] if projects else {}
        
        best_project = {}
        best_score = 0
        best_matching_skills = []
        
        for project in projects:
            if isinstance(project, str):
                # Convert string project to dict
                project = {
                    'name': project,
                    'description': project,
                    'technologies': []
                }
            
            overlap_score, matching_skills = self.calculate_project_overlap(job_skills, project)
            
            if overlap_score > best_score:
                best_score = overlap_score
                best_project = project
                best_matching_skills = matching_skills
        
        # Add matching info to the selected project
        if best_project:
            best_project['match_score'] = best_score
            best_project['matching_skills'] = best_matching_skills
            best_project['summary'] = self.generate_project_summary(best_project, job_skills)
        
        logger.info(f"Selected project: {best_project.get('name', 'Unknown')} (Score: {best_score})")
        return best_project
    
    def generate_project_summary(self, project: Dict, job_skills: List[str]) -> str:
        """Generate a concise project summary highlighting relevant aspects"""
        project_name = project.get('name', 'Project')
        project_desc = project.get('description', '')
        project_tech = project.get('technologies', [])
        matching_skills = project.get('matching_skills', [])
        
        # Create a focused summary
        summary = f"{project_name}: "
        
        if matching_skills:
            summary += f"Built using {', '.join(matching_skills[:3])}"
            if len(matching_skills) > 3:
                summary += " and other technologies"
        else:
            summary += f"Built using {', '.join(project_tech[:3])}" if project_tech else "Various technologies"
        
        # Add brief description if available
        if project_desc and len(project_desc) < 100:
            summary += f". {project_desc}"
        
        return summary
    
    def match_project_for_job(self, job: Dict, profile_path: str) -> Dict:
        """Main method to match project for a job"""
        try:
            return self.select_best_project(job, profile_path)
        except Exception as e:
            logger.error(f"Error matching project: {e}")
            return {}
