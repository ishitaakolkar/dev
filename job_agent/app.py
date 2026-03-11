import streamlit as st
import os
import sys
import pandas as pd
from datetime import datetime
import json

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import config
from profile_manager import ProfileManager
from application_tracker import ApplicationTracker
from job_scraper import JobScraper
from job_matcher import JobMatcher
from project_matcher import ProjectMatcher
from email_generator import EmailGenerator
from email_sender import EmailSender
from resume_parser import ResumeParser

# Page configuration
st.set_page_config(
    page_title="AI Job Application Assistant",
    page_icon="💼",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if 'page' not in st.session_state:
    st.session_state.page = 'Profile'

# Initialize managers
@st.cache_resource
def init_managers():
    profile_manager = ProfileManager(config.profile_path)
    tracker = ApplicationTracker(config.applications_path)
    return profile_manager, tracker

profile_manager, tracker = init_managers()

# Sidebar navigation
def sidebar():
    st.sidebar.title("🎯 Job Assistant")
    
    pages = ['Profile', 'Jobs', 'Applications']
    selected_page = st.sidebar.selectbox("Navigate", pages, index=pages.index(st.session_state.page))
    st.session_state.page = selected_page
    
    # Profile completion indicator
    completion = profile_manager.get_profile_completion_percentage()
    st.sidebar.metric("Profile Completion", f"{completion}%")
    
    # Quick stats
    stats = tracker.get_statistics()
    st.sidebar.metric("Total Applications", stats.get('total_applications', 0))
    st.sidebar.metric("Emails Sent", stats.get('emails_sent', 0))
    st.sidebar.metric("Today's Applications", stats.get('today_sent', 0))

# Profile Page
def profile_page():
    st.title("👤 Profile Setup")
    
    profile = profile_manager.load_profile()
    
    # Basic Information
    st.subheader("Basic Information")
    col1, col2 = st.columns(2)
    
    with col1:
        name = st.text_input("Name", value=profile.get('name', ''))
        email = st.text_input("Email", value=profile.get('email', ''))
        linkedin_url = st.text_input("LinkedIn URL", value=profile.get('linkedin_url', ''))
        current_company = st.text_input("Current Company (to avoid accidental applications)", 
                                     value=profile.get('current_company', ''))
    
    with col2:
        # Resume upload and parsing
        if os.path.exists(config.resume_path):
            st.success("✅ Resume uploaded")
            if st.button("Remove Resume"):
                try:
                    os.remove(config.resume_path)
                    st.rerun()
                except:
                    pass
            
            # Parse resume button
            if config.gemini_api_key and st.button("📄 Extract Profile from Resume"):
                with st.spinner("Extracting information from resume..."):
                    try:
                        parser = ResumeParser(config.gemini_api_key)
                        success = parser.generate_profile_from_resume(config.resume_path, config.profile_path)
                        
                        if success:
                            st.success("✅ Profile extracted successfully from resume!")
                            st.rerun()
                        else:
                            st.error("❌ Failed to extract profile from resume")
                    except Exception as e:
                        st.error(f"Error parsing resume: {e}")
        else:
            uploaded_file = st.file_uploader("Upload Resume (PDF)", type=['pdf'])
            if uploaded_file:
                with open(config.resume_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                st.success("Resume uploaded successfully!")
                st.rerun()
    
    # Preferred Roles
    st.subheader("Job Preferences")
    col1, col2 = st.columns(2)
    
    with col1:
        preferred_roles = st.text_area("Preferred Roles (one per line)", 
                                     value='\n'.join(profile.get('preferred_roles', [])))
        preferred_locations = st.text_area("Preferred Locations (one per line)", 
                                          value='\n'.join(profile.get('preferred_locations', [])))
    
    with col2:
        target_companies = st.text_area("Target Companies (one per line)", 
                                      value='\n'.join(profile.get('target_companies', [])))
    
    # Skills
    st.subheader("Skills")
    skills = st.text_area("Skills (comma-separated)", 
                         value=', '.join(profile.get('skills', [])))
    
    # Projects
    st.subheader("Projects")
    projects = profile.get('projects', [])
    
    if st.button("Add Project"):
        if 'new_project' not in st.session_state:
            st.session_state.new_project = True
    
    if st.session_state.get('new_project', False):
        with st.expander("New Project", expanded=True):
            project_name = st.text_input("Project Name")
            project_desc = st.text_area("Project Description")
            project_tech = st.text_area("Technologies Used (comma-separated)")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Save Project"):
                    if project_name:
                        new_project = {
                            'name': project_name,
                            'description': project_desc,
                            'technologies': [tech.strip() for tech in project_tech.split(',') if tech.strip()]
                        }
                        profile_manager.add_project(new_project)
                        st.session_state.new_project = False
                        st.rerun()
            
            with col2:
                if st.button("Cancel"):
                    st.session_state.new_project = False
                    st.rerun()
    
    # Display existing projects
    for i, project in enumerate(projects):
        with st.expander(f"📁 {project.get('name', 'Untitled')}"):
            st.write(f"**Description:** {project.get('description', 'No description')}")
            st.write(f"**Technologies:** {', '.join(project.get('technologies', []))}")
            if st.button(f"Delete Project {i}", key=f"del_{i}"):
                profile_manager.remove_project(i)
                st.rerun()
    
    # Achievements
    st.subheader("Achievements")
    achievements = st.text_area("Achievements (one per line)", 
                              value='\n'.join(profile.get('achievements', [])))
    
    # Save button
    if st.button("💾 Save Profile", type="primary"):
        updated_profile = {
                'name': name,
                'email': email,
                'linkedin_url': linkedin_url,
                'current_company': current_company,
                'preferred_roles': [role.strip() for role in preferred_roles.split('\n') if role.strip()],
                'preferred_locations': [loc.strip() for loc in preferred_locations.split('\n') if loc.strip()],
                'target_companies': [comp.strip() for comp in target_companies.split('\n') if comp.strip()],
                'skills': [skill.strip() for skill in skills.split(',') if skill.strip()],
                'projects': profile.get('projects', []),  # Keep existing projects
                'achievements': [achievement.strip() for achievement in achievements.split('\n') if achievement.strip()]
            }      
        if profile_manager.save_profile(updated_profile):
            st.success("Profile saved successfully!")
            st.rerun()
        else:
            st.error("Error saving profile")
    

# Jobs Page
def jobs_page():
    st.title("🔍 Job Discovery")
    
    # Current Company Warning
    if config.current_company:
        st.warning(f"⚠️ **Current Company Filter Active**: Jobs from '{config.current_company}' will be automatically skipped to avoid accidental applications.")
    else:
        st.info("💡 **Tip**: Set your current company in profile or .env file to avoid accidental applications to your current employer.")
    # Check if profile is complete
    missing_fields = profile_manager.validate_profile()
    if missing_fields:
        st.warning(f"⚠️ Please complete your profile first. Missing: {', '.join(missing_fields)}")
        return
    
    # Job discovery controls
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        if st.button("🔍 Discover New Jobs", type="primary"):
            with st.spinner("Discovering jobs..."):
                try:
                    scraper = JobScraper()
                    jobs = scraper.discover_jobs(limit=20)
                    
                    if config.gemini_api_key:
                        matcher = JobMatcher(config.gemini_api_key)
                        matched_jobs = matcher.match_jobs(
                            jobs, 
                            config.profile_path, 
                            config.match_score_threshold, 
                            config.max_experience_years,
                            config.current_company
                        )
                        
                        # Add to tracker
                        project_matcher = ProjectMatcher(config.gemini_api_key)
                        
                        for job in matched_jobs:
                            if not tracker.job_exists(job['job_id']):
                                project = project_matcher.select_best_project(job, config.profile_path)
                                tracker.add_application(job, project)
                        
                        st.success(f"Found {len(matched_jobs)} relevant jobs!")
                        st.rerun()
                    else:
                        st.error("Please set GEMINI_API_KEY in your environment")
                        
                except Exception as e:
                    st.error(f"Error discovering jobs: {e}")
    
    with col2:
        st.metric("Jobs Found", len(tracker.get_all_applications()))
    
    with col3:
        st.metric("Pending", len([app for app in tracker.get_all_applications() if app['Status'] == 'Pending']))
    
    # Display jobs
    applications = tracker.get_all_applications()
    
    if not applications:
        st.info("No jobs found yet. Click 'Discover New Jobs' to get started.")
        return
    
    st.subheader("Discovered Jobs")
    
    for app in applications:
        with st.expander(f"🏢 {app['Company']} - {app['Role']} (Score: {app['Match_Score']})"):
            col1, col2 = st.columns([3, 1])
            
            with col1:
                st.write(f"**Company:** {app['Company']}")
                st.write(f"**Role:** {app['Role']}")
                st.write(f"**Location:** [Job Link]({app['Job_Link']})")
                st.write(f"**Match Score:** {app['Match_Score']}/100")
                st.write(f"**Project Used:** {app['Project_Used']}")
                st.write(f"**Status:** {app['Status']}")
                
                if app['Notes']:
                    st.write(f"**Notes:** {app['Notes']}")
            
            with col2:
                # Generate email button
                if not app['Email_Generated'] and config.gemini_api_key:
                    if st.button("📧 Generate Email", key=f"gen_{app['Job_ID']}"):
                        with st.spinner("Generating email..."):
                            try:
                                # Get job details
                                job = {
                                    'company': app['Company'],
                                    'role': app['Role'],
                                    'job_description': 'Job description would be here',
                                    'job_link': app['Job_Link']
                                }
                                
                                # Get project
                                project_matcher = ProjectMatcher(config.gemini_api_key)
                                project = project_matcher.select_best_project(job, config.profile_path)
                                
                                # Generate email
                                email_gen = EmailGenerator(config.gemini_api_key)
                                email_content = email_gen.generate_application_email(job, project, config.profile_path)
                                
                                # Save draft
                                draft_path = email_gen.save_email_draft(job, email_content, config.emails_drafts_path)
                                
                                # Update tracker
                                tracker.update_application_status(app['Job_ID'], 'Email Generated', f"Draft saved: {draft_path}")
                                
                                st.success("Email generated successfully!")
                                st.rerun()
                                
                            except Exception as e:
                                st.error(f"Error generating email: {e}")
                
                # Send email button
                if app['Email_Generated'] and not app['Email_Sent'] and config.gmail_email:
                    if st.button("📤 Send Email", key=f"send_{app['Job_ID']}"):
                        with st.spinner("Sending email..."):
                            try:
                                # Check daily limit
                                today_count = tracker.get_today_applications_count()
                                if today_count >= config.max_emails_per_day:
                                    st.error(f"Daily limit reached ({config.max_emails_per_day} emails)")
                                    continue
                                
                                sender = EmailSender(config.gmail_email, config.gmail_app_password)
                                
                                # This would load the actual email content
                                email_content = {
                                    'subject': f"Application for {app['Role']}",
                                    'body': "Generated email content would be here"
                                }
                                
                                result = sender.send_application_email(
                                    {'company': app['Company'], 'role': app['Role']},
                                    email_content,
                                    config.resume_path if os.path.exists(config.resume_path) else None
                                )
                                
                                if result['sent']:
                                    tracker.mark_email_sent(app['Job_ID'], result['email_sent'])
                                    st.success("Email sent successfully!")
                                    st.rerun()
                                else:
                                    st.error(f"Failed to send email: {result['error']}")
                                    
                            except Exception as e:
                                st.error(f"Error sending email: {e}")
                
                # LinkedIn message button
                if config.gemini_api_key:
                    if st.button("💬 LinkedIn Message", key=f"linkedin_{app['Job_ID']}"):
                        with st.spinner("Generating LinkedIn message..."):
                            try:
                                email_gen = EmailGenerator(config.gemini_api_key)
                                linkedin_msg = email_gen.generate_linkedin_message(
                                    {'company': app['Company'], 'role': app['Role']},
                                    config.profile_path
                                )
                                
                                st.text_area("LinkedIn Message (copy this):", 
                                           value=linkedin_msg.get('message', ''), 
                                           height=100, 
                                           disabled=True)
                                
                            except Exception as e:
                                st.error(f"Error generating LinkedIn message: {e}")

# Applications Page
def applications_page():
    st.title("📊 Application Tracker")
    
    # Statistics
    stats = tracker.get_statistics()
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Applications", stats.get('total_applications', 0))
    with col2:
        st.metric("Emails Sent", stats.get('emails_sent', 0))
    with col3:
        st.metric("Pending", stats.get('pending_applications', 0))
    with col4:
        st.metric("Applied", stats.get('applied_applications', 0))
    
    # Applications table
    applications = tracker.get_all_applications()
    
    if applications:
        st.subheader("Application History")
        
        # Convert to DataFrame for better display
        df = pd.DataFrame(applications)
        
        # Format the dataframe for display
        display_columns = ['Company', 'Role', 'Match_Score', 'Project_Used', 'Status', 'Date_Applied']
        if all(col in df.columns for col in display_columns):
            st.dataframe(df[display_columns], use_container_width=True)
        
        # Export functionality
        col1, col2 = st.columns(2)
        with col1:
            if st.button("📥 Export to CSV"):
                try:
                    tracker.export_to_csv("applications_export.csv")
                    st.success("Exported to applications_export.csv")
                except Exception as e:
                    st.error(f"Error exporting: {e}")
        
        with col2:
            if st.button("🔄 Refresh"):
                st.rerun()
        
        # Follow-up section
        followup_apps = tracker.get_applications_for_followup()
        
        if followup_apps:
            st.subheader("📬 Follow-up Required")
            
            for app in followup_apps:
                with st.expander(f"Follow-up: {app['Company']} - {app['Role']}"):
                    st.write(f"**Applied on:** {app['Date_Applied']}")
                    st.write(f"**Days since application:** {(datetime.now() - pd.to_datetime(app['Date_Applied'])).days}")
                    
                    if st.button(f"Generate Follow-up Email", key=f"followup_{app['Job_ID']}"):
                        with st.spinner("Generating follow-up..."):
                            try:
                                if config.gemini_api_key:
                                    email_gen = EmailGenerator(config.gemini_api_key)
                                    followup_email = email_gen.generate_followup_email(
                                        {
                                            'company': app['Company'],
                                            'role': app['Role']
                                        },
                                        config.profile_path
                                    )
                                    
                                    st.text_area("Follow-up Email:", 
                                               value=f"Subject: {followup_email.get('subject', '')}\n\n{followup_email.get('body', '')}", 
                                               height=150, 
                                               disabled=True)
                                else:
                                    st.error("Please set GEMINI_API_KEY")
                                    
                            except Exception as e:
                                st.error(f"Error generating follow-up: {e}")
    else:
        st.info("No applications yet. Go to the Jobs page to discover and apply for jobs.")

# Main app
def main():
    sidebar()
    
    if st.session_state.page == 'Profile':
        profile_page()
    elif st.session_state.page == 'Jobs':
        jobs_page()
    elif st.session_state.page == 'Applications':
        applications_page()

if __name__ == "__main__":
    main()
