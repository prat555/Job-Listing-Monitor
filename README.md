# Job Listing Monitor 🔍💼

A powerful Python-based web scraping tool to monitor job listings from multiple sources (Indeed, LinkedIn) and get notified when new positions matching your criteria are posted.

## Features ✨

- **Multi-Source Scraping**: Scrapes job listings from Indeed and LinkedIn
- **Intelligent Tracking**: SQLite database tracks all jobs and identifies new postings
- **Email Notifications**: Get beautiful HTML email alerts for new job opportunities
- **Scheduled Monitoring**: Automatic periodic checks at configurable intervals
- **Search Flexibility**: Monitor multiple search terms and locations simultaneously
- **Statistics Dashboard**: Track total jobs, new listings, and search history
- **Data Management**: Automatic cleanup of old job listings

## Project Structure 📁

```
job-listing-monitor/
├── main.py              # Main application and CLI
├── scraper.py           # Web scraping logic for job boards
├── database.py          # SQLite database management
├── notifier.py          # Email notification system
├── requirements.txt     # Python dependencies
├── .env.example         # Example environment configuration
├── .env                 # Your configuration (create from .env.example)
└── README.md           # This file
```

## Installation 🚀

### 1. Clone or Download the Project

```bash
cd "C:\Users\pc\OneDrive\Desktop\New folder"
```

### 2. Install Python Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Environment Variables

Copy `.env.example` to `.env` and fill in your details:

```bash
cp .env.example .env
```

Edit `.env` with your configuration:

```env
# Email Configuration (Gmail example)
EMAIL_SENDER=your_email@gmail.com
EMAIL_PASSWORD=your_app_password
EMAIL_RECIPIENT=recipient@email.com

# SMTP Configuration
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587

# Scraping Configuration
SEARCH_TERMS=python developer,data scientist,software engineer
LOCATION=remote
SOURCES=indeed,linkedin
CHECK_INTERVAL_MINUTES=60
MAX_PAGES_TO_SCRAPE=5
```

**Note for Gmail Users**: 
- You need to create an [App Password](https://support.google.com/accounts/answer/185833)
- Regular Gmail password won't work due to security restrictions

## Usage 📖

### Basic Commands

#### 1. Run Monitor Once (Single Check)
```bash
python main.py --mode run
```

#### 2. Run Scheduled Monitor (Continuous)
```bash
python main.py --mode schedule
```
This will run continuously and check for new jobs at the interval specified in your `.env` file.

#### 3. View Statistics
```bash
python main.py --mode stats
```

#### 4. View New Jobs
```bash
python main.py --mode new
```

To mark jobs as read after viewing:
```bash
python main.py --mode new --mark-read
```

#### 5. Test Email Configuration
```bash
python main.py --mode test-email
```

#### 6. Cleanup Old Jobs
```bash
python main.py --mode cleanup --cleanup-days 30
```

### Advanced Usage

#### Custom Search Parameters
```bash
python main.py --mode run --search "machine learning,AI engineer" --location "San Francisco"
```

#### Specify Sources
```bash
python main.py --mode run --sources "indeed,linkedin"
```

#### Combine Parameters
```bash
python main.py --mode schedule --search "python developer" --location "remote" --sources "indeed"
```