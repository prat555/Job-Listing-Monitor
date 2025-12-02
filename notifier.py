"""
Notification Module
Handles email notifications for new job listings
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Dict
import logging
import os
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class EmailNotifier:
    """Send email notifications for new job listings"""
    
    def __init__(self):
        self.smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        self.smtp_port = int(os.getenv('SMTP_PORT', 587))
        self.sender_email = os.getenv('EMAIL_SENDER')
        self.sender_password = os.getenv('EMAIL_PASSWORD')
        self.recipient_email = os.getenv('EMAIL_RECIPIENT')
        
        if not all([self.sender_email, self.sender_password, self.recipient_email]):
            logger.warning("Email configuration incomplete. Notifications disabled.")
            self.enabled = False
        else:
            self.enabled = True
    
    def send_notification(self, jobs: List[Dict]) -> bool:
        """Send email notification with new job listings"""
        if not self.enabled:
            logger.warning("Email notifications are disabled")
            return False
        
        if not jobs:
            logger.info("No new jobs to notify")
            return False
        
        try:
            # Create email content
            subject = f"🔔 {len(jobs)} New Job Listing{'s' if len(jobs) > 1 else ''} Found!"
            body = self._format_email_body(jobs)
            
            # Create message
            message = MIMEMultipart("alternative")
            message["Subject"] = subject
            message["From"] = self.sender_email
            message["To"] = self.recipient_email
            
            # Add HTML content
            html_part = MIMEText(body, "html")
            message.attach(html_part)
            
            # Send email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.sender_email, self.sender_password)
                server.send_message(message)
            
            logger.info(f"Email notification sent successfully to {self.recipient_email}")
            return True
        
        except Exception as e:
            logger.error(f"Failed to send email notification: {e}")
            return False
    
    def _format_email_body(self, jobs: List[Dict]) -> str:
        """Format jobs list into HTML email body"""
        html = """
        <html>
        <head>
            <style>
                body {
                    font-family: Arial, sans-serif;
                    line-height: 1.6;
                    color: #333;
                }
                .container {
                    max-width: 800px;
                    margin: 0 auto;
                    padding: 20px;
                }
                .header {
                    background-color: #4CAF50;
                    color: white;
                    padding: 20px;
                    text-align: center;
                    border-radius: 5px;
                }
                .job-card {
                    border: 1px solid #ddd;
                    border-radius: 5px;
                    padding: 15px;
                    margin: 15px 0;
                    background-color: #f9f9f9;
                }
                .job-title {
                    font-size: 18px;
                    font-weight: bold;
                    color: #2196F3;
                    margin-bottom: 10px;
                }
                .job-details {
                    margin: 5px 0;
                }
                .company {
                    font-weight: bold;
                    color: #555;
                }
                .location {
                    color: #777;
                }
                .source-badge {
                    display: inline-block;
                    padding: 3px 8px;
                    background-color: #2196F3;
                    color: white;
                    border-radius: 3px;
                    font-size: 12px;
                    margin-top: 5px;
                }
                .apply-button {
                    display: inline-block;
                    padding: 10px 20px;
                    background-color: #4CAF50;
                    color: white;
                    text-decoration: none;
                    border-radius: 5px;
                    margin-top: 10px;
                }
                .footer {
                    text-align: center;
                    margin-top: 30px;
                    padding-top: 20px;
                    border-top: 1px solid #ddd;
                    color: #777;
                    font-size: 12px;
                }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🎯 New Job Opportunities!</h1>
                    <p>Found {count} new job listing{plural} matching your criteria</p>
                </div>
        """.format(count=len(jobs), plural='s' if len(jobs) > 1 else '')
        
        for job in jobs:
            html += f"""
                <div class="job-card">
                    <div class="job-title">{job.get('title', 'N/A')}</div>
                    <div class="job-details">
                        <span class="company">🏢 {job.get('company', 'N/A')}</span>
                    </div>
                    <div class="job-details">
                        <span class="location">📍 {job.get('location', 'N/A')}</span>
                    </div>
                    <span class="source-badge">{job.get('source', 'N/A')}</span>
            """
            
            if job.get('url'):
                html += f"""
                    <div>
                        <a href="{job['url']}" class="apply-button">View Job →</a>
                    </div>
                """
            
            html += """
                </div>
            """
        
        html += """
                <div class="footer">
                    <p>This is an automated notification from your Job Listing Monitor</p>
                    <p>Don't miss out on these opportunities!</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return html
    
    def send_test_email(self) -> bool:
        """Send a test email to verify configuration"""
        if not self.enabled:
            logger.error("Email configuration is incomplete")
            return False
        
        test_job = {
            'title': 'Test Job Notification',
            'company': 'Test Company',
            'location': 'Remote',
            'source': 'Test',
            'url': 'https://example.com'
        }
        
        return self.send_notification([test_job])


class ConsoleNotifier:
    """Print notifications to console (fallback when email is not configured)"""
    
    def send_notification(self, jobs: List[Dict]) -> bool:
        """Print job listings to console"""
        if not jobs:
            logger.info("No new jobs to notify")
            return False
        
        print("\n" + "="*70)
        print(f"🔔 NEW JOB LISTINGS FOUND: {len(jobs)}")
        print("="*70 + "\n")
        
        for i, job in enumerate(jobs, 1):
            print(f"{i}. {job.get('title', 'N/A')}")
            print(f"   Company: {job.get('company', 'N/A')}")
            print(f"   Location: {job.get('location', 'N/A')}")
            print(f"   Source: {job.get('source', 'N/A')}")
            if job.get('url'):
                print(f"   URL: {job['url']}")
            print()
        
        print("="*70 + "\n")
        return True


class NotificationManager:
    """Manage multiple notification methods"""
    
    def __init__(self):
        self.email_notifier = EmailNotifier()
        self.console_notifier = ConsoleNotifier()
    
    def notify(self, jobs: List[Dict]) -> bool:
        """Send notifications through all available channels"""
        if not jobs:
            return False
        
        results = []
        
        # Try email notification
        if self.email_notifier.enabled:
            results.append(self.email_notifier.send_notification(jobs))
        
        # Always show console notification
        results.append(self.console_notifier.send_notification(jobs))
        
        return any(results)
    
    def test_email(self) -> bool:
        """Test email configuration"""
        return self.email_notifier.send_test_email()


if __name__ == "__main__":
    # Test notifications
    notifier = NotificationManager()
    
    test_jobs = [
        {
            'title': 'Senior Python Developer',
            'company': 'Tech Corp',
            'location': 'Remote',
            'source': 'Indeed',
            'url': 'https://example.com/job1'
        },
        {
            'title': 'Full Stack Engineer',
            'company': 'Startup Inc',
            'location': 'San Francisco, CA',
            'source': 'LinkedIn',
            'url': 'https://example.com/job2'
        }
    ]
    
    print("Testing notification system...")
    notifier.notify(test_jobs)
