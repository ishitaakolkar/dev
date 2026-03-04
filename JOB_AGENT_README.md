# AI Job Application Assistant

A minimal personal AI job application assistant that helps you automatically discover relevant jobs, prepare tailored applications, and track them without manual effort.

## Features

- **Job Discovery**: Automatically scrapes jobs from multiple sources (Wellfound, YC Jobs, etc.)
- **Smart Matching**: Uses AI to match jobs with your profile and skills
- **Project Selection**: Intelligently selects your most relevant project for each application
- **Email Generation**: Creates personalized application emails
- **Application Tracking**: Tracks all applications in Excel
- **LinkedIn Outreach**: Generates LinkedIn messages for networking
- **Follow-up System**: Automatically generates follow-up emails
- **Streamlit Dashboard**: Easy-to-use web interface

## Quick Start

### 1. Installation

```bash
# Clone or download the project
cd job_agent

# Install dependencies
pip install -r requirements.txt
```

### 2. Configuration

Create a `.env` file based on the example:

```bash
# Copy the example file
cp .env.example .env

# Edit the .env file with your credentials
notepad .env  # or use your preferred editor
```

Set up environment variables in your `.env` file:

```bash
# Required for AI features
GEMINI_API_KEY=your_gemini_api_key

# Required for email sending
GMAIL_EMAIL=your_email@gmail.com
GMAIL_APP_PASSWORD=your_gmail_app_password
```

### 3. Run the Application

```bash
# Start the Streamlit dashboard
streamlit run job_agent/app.py
```

The application will open in your browser at `http://localhost:8501`

## Usage

### 1. Setup Your Profile

- Navigate to the **Profile** page
- **Upload your resume (PDF)** - The system can automatically extract:
  - Personal information (name, email, phone)
  - Skills and technologies
  - Projects and experience
  - Achievements and education
  - LinkedIn and GitHub profiles
- Review and edit the extracted information
- Add preferred job roles and locations
- Fine-tune your profile as needed

### 2. Discover Jobs

- Go to the **Jobs** page
- Click "Discover New Jobs" to find relevant opportunities
- Review matched jobs with their scores
- Generate personalized emails with one click
- Send emails directly (limited to 5 per day)

### 3. Track Applications

- View all applications in the **Applications** page
- See statistics and export data
- Generate follow-up emails for older applications

## Project Structure

```
job_agent/
├── app.py                 # Main Streamlit application
├── scheduler.py           # Automated job discovery scheduler
├── config.py             # Configuration settings
├── job_scraper.py        # Job discovery from multiple sources
├── job_matcher.py        # AI-powered job matching
├── project_matcher.py    # Project selection logic
├── email_generator.py    # Email and LinkedIn message generation
├── email_sender.py       # SMTP email sending
├── profile_manager.py    # User profile management
└── application_tracker.py # Excel-based application tracking

data/
├── profile.json          # User profile data
├── resume.pdf           # User resume
└── applications.xlsx    # Application tracking

emails/
└── drafts/              # Generated email drafts
```

## Scheduler (Automated Mode)

Run the scheduler for automated job discovery:

```bash
# Run once
python job_agent/scheduler.py --run-once

# Run continuously (every 6 hours)
python job_agent/scheduler.py

# Auto-send emails (use with caution)
python job_agent/scheduler.py --auto-send

# Test configuration
python job_agent/scheduler.py --test
```

## Configuration Options

Edit `job_agent/config.py` to customize:

- `match_score_threshold`: Minimum job match score (default: 70)
- `max_experience_years`: Maximum experience requirement (default: 2)
- `max_emails_per_day`: Daily email limit (default: 5)
- `job_search_interval_hours`: Scheduler interval (default: 6)

## Email Setup

1. Enable 2-factor authentication on your Gmail account
2. Generate an App Password:
   - Go to Google Account settings
   - Security → 2-Step Verification → App passwords
   - Generate a new app password for "Job Agent"
3. Use the app password in `GMAIL_APP_PASSWORD`

## Safety Features

- **Rate Limiting**: Maximum 5 emails per day
- **Duplicate Prevention**: Checks existing applications before processing
- **Manual Review**: Emails are generated as drafts first
- **Error Handling**: Continues processing even if individual jobs fail

## Data Privacy

- All data is stored locally on your machine
- No external databases or cloud services
- Profile and applications stored in local files
- Emails sent directly from your Gmail account

## Troubleshooting

### Common Issues

1. **Gemini API errors**: Make sure your API key is valid and has quota
2. **Email sending fails**: Check Gmail app password and SMTP settings
3. **No jobs found**: Job sites may have changed their structure
4. **Profile not loading**: Check `data/profile.json` exists and is valid JSON

### Debug Mode

Enable detailed logging:

```bash
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
python -c "
import logging
logging.basicConfig(level=logging.DEBUG)
from job_agent.scheduler import JobScheduler
scheduler = JobScheduler()
scheduler.run_pipeline()
"
```

## Contributing

This is a personal tool designed for simplicity and speed. Features are intentionally minimal to avoid overengineering.

## License

MIT License - feel free to use and modify for personal use.
