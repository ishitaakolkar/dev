import json
import os
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)

class ProfileManager:
    def __init__(self, profile_path: str):
        self.profile_path = profile_path
        self._ensure_profile_exists()
    
    def _ensure_profile_exists(self):
        """Create profile file if it doesn't exist"""
        if not os.path.exists(self.profile_path):
            default_profile = {
                "name": "",
                "email": "",
                "linkedin_url": "",
                "preferred_roles": [],
                "preferred_locations": [],
                "skills": [],
                "projects": [],
                "achievements": [],
                "target_companies": [],
                "current_company": ""
            }
            self.save_profile(default_profile)
            logger.info(f"Created new profile: {self.profile_path}")
    
    def load_profile(self) -> Dict:
        """Load user profile from JSON file"""
        try:
            with open(self.profile_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading profile: {e}")
            return {}
    
    def save_profile(self, profile: Dict) -> bool:
        """Save user profile to JSON file"""
        try:
            os.makedirs(os.path.dirname(self.profile_path), exist_ok=True)
            with open(self.profile_path, 'w', encoding='utf-8') as f:
                json.dump(profile, f, indent=2, ensure_ascii=False)
            logger.info("Profile saved successfully")
            return True
        except Exception as e:
            logger.error(f"Error saving profile: {e}")
            return False
    
    def update_profile_field(self, field: str, value) -> bool:
        """Update a single field in the profile"""
        try:
            profile = self.load_profile()
            profile[field] = value
            return self.save_profile(profile)
        except Exception as e:
            logger.error(f"Error updating profile field: {e}")
            return False
    
    def add_skill(self, skill: str) -> bool:
        """Add a skill to the profile"""
        try:
            profile = self.load_profile()
            skills = profile.get('skills', [])
            
            if skill not in skills:
                skills.append(skill)
                profile['skills'] = skills
                return self.save_profile(profile)
            
            return True
        except Exception as e:
            logger.error(f"Error adding skill: {e}")
            return False
    
    def remove_skill(self, skill: str) -> bool:
        """Remove a skill from the profile"""
        try:
            profile = self.load_profile()
            skills = profile.get('skills', [])
            
            if skill in skills:
                skills.remove(skill)
                profile['skills'] = skills
                return self.save_profile(profile)
            
            return True
        except Exception as e:
            logger.error(f"Error removing skill: {e}")
            return False
    
    def add_project(self, project: Dict) -> bool:
        """Add a project to the profile"""
        try:
            profile = self.load_profile()
            projects = profile.get('projects', [])
            
            # Ensure project has required fields
            if 'name' not in project:
                project['name'] = 'Untitled Project'
            if 'description' not in project:
                project['description'] = ''
            if 'technologies' not in project:
                project['technologies'] = []
            
            projects.append(project)
            profile['projects'] = projects
            return self.save_profile(profile)
        except Exception as e:
            logger.error(f"Error adding project: {e}")
            return False
    
    def remove_project(self, project_index: int) -> bool:
        """Remove a project by index"""
        try:
            profile = self.load_profile()
            projects = profile.get('projects', [])
            
            if 0 <= project_index < len(projects):
                projects.pop(project_index)
                profile['projects'] = projects
                return self.save_profile(profile)
            
            return False
        except Exception as e:
            logger.error(f"Error removing project: {e}")
            return False
    
    def add_preferred_role(self, role: str) -> bool:
        """Add a preferred job role"""
        try:
            profile = self.load_profile()
            roles = profile.get('preferred_roles', [])
            
            if role not in roles:
                roles.append(role)
                profile['preferred_roles'] = roles
                return self.save_profile(profile)
            
            return True
        except Exception as e:
            logger.error(f"Error adding preferred role: {e}")
            return False
    
    def add_preferred_location(self, location: str) -> bool:
        """Add a preferred location"""
        try:
            profile = self.load_profile()
            locations = profile.get('preferred_locations', [])
            
            if location not in locations:
                locations.append(location)
                profile['preferred_locations'] = locations
                return self.save_profile(profile)
            
            return True
        except Exception as e:
            logger.error(f"Error adding preferred location: {e}")
            return False
    
    def validate_profile(self) -> List[str]:
        """Validate profile and return list of missing fields"""
        try:
            profile = self.load_profile()
            missing_fields = []
            
            required_fields = [
                ('name', 'Name'),
                ('email', 'Email'),
                ('preferred_roles', 'Preferred Roles'),
                ('preferred_locations', 'Preferred Locations'),
                ('skills', 'Skills'),
                ('projects', 'Projects')
            ]
            
            for field, display_name in required_fields:
                value = profile.get(field)
                if not value or (isinstance(value, list) and len(value) == 0):
                    missing_fields.append(display_name)
            
            return missing_fields
            
        except Exception as e:
            logger.error(f"Error validating profile: {e}")
            return []
    
    def get_profile_completion_percentage(self) -> int:
        """Get profile completion percentage"""
        try:
            profile = self.load_profile()
            
            fields = [
                'name', 'email', 'linkedin_url', 'preferred_roles', 
                'preferred_locations', 'skills', 'projects', 'achievements', 'target_companies'
            ]
            
            completed = 0
            for field in fields:
                value = profile.get(field)
                if value and (not isinstance(value, list) or len(value) > 0):
                    completed += 1
            
            return int((completed / len(fields)) * 100)
            
        except Exception as e:
            logger.error(f"Error calculating completion percentage: {e}")
            return 0
    
    def export_profile(self, output_path: str) -> bool:
        """Export profile to a different file"""
        try:
            profile = self.load_profile()
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(profile, f, indent=2, ensure_ascii=False)
            logger.info(f"Profile exported to {output_path}")
            return True
        except Exception as e:
            logger.error(f"Error exporting profile: {e}")
            return False
    
    def import_profile(self, import_path: str) -> bool:
        """Import profile from a different file"""
        try:
            with open(import_path, 'r', encoding='utf-8') as f:
                profile = json.load(f)
            return self.save_profile(profile)
        except Exception as e:
            logger.error(f"Error importing profile: {e}")
            return False
