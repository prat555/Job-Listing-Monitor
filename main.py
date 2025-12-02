"""
Job Listing Monitor - Main Application
Coordinates scraping, database storage, and notifications
"""

import schedule
import time
import logging
from datetime import datetime
import os
from dotenv import load_dotenv
import argparse

from scraper import JobScraperManager
from database import JobDatabase
from notifier import NotificationManager

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('job_monitor.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class JobMonitor:
    """Main job monitoring application"""
    
    def __init__(self, config: dict = None):
        self.config = config or self._load_default_config()
        self.scraper = JobScraperManager()
        self.database = JobDatabase(self.config['db_path'])
        self.notifier = NotificationManager()
        
        logger.info("Job Monitor initialized")
        logger.info(f"Monitoring for: {self.config['search_terms']}")
    
    def _load_default_config(self) -> dict:
        """Load configuration from environment variables"""
        return {
            'db_path': 'jobs.db',
            'search_terms': os.getenv('SEARCH_TERMS', 'python developer').split(','),
            'location': os.getenv('LOCATION', 'remote'),
            'sources': os.getenv('SOURCES', 'indeed').split(','),
            'max_pages': int(os.getenv('MAX_PAGES_TO_SCRAPE', 5)),
            'check_interval': int(os.getenv('CHECK_INTERVAL_MINUTES', 60))
        }
    
    def check_for_jobs(self):
        """Main function to check for new job listings"""
        logger.info("=" * 60)
        logger.info(f"Starting job check at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info("=" * 60)
        
        total_new_jobs = 0
        all_new_jobs = []
        
        for search_term in self.config['search_terms']:
            search_term = search_term.strip()
            logger.info(f"\nSearching for: '{search_term}'")
            
            try:
                # Scrape jobs
                jobs = self.scraper.scrape_all_sources(
                    search_term=search_term,
                    location=self.config['location'],
                    sources=self.config['sources'],
                    max_pages=self.config['max_pages']
                )
                
                logger.info(f"Found {len(jobs)} total jobs for '{search_term}'")
                
                # Add jobs to database and count new ones
                new_count = 0
                for job in jobs:
                    if self.database.add_job(job):
                        new_count += 1
                        all_new_jobs.append(job)
                
                logger.info(f"New jobs for '{search_term}': {new_count}")
                total_new_jobs += new_count
                
                # Log search
                self.database.log_search(search_term, self.config['location'], len(jobs))
                
            except Exception as e:
                logger.error(f"Error processing search term '{search_term}': {e}")
        
        # Send notifications for all new jobs
        if all_new_jobs:
            logger.info(f"\n📧 Sending notifications for {total_new_jobs} new job(s)")
            self.notifier.notify(all_new_jobs)
        else:
            logger.info("\nNo new jobs found this time")
        
        # Display statistics
        stats = self.database.get_statistics()
        logger.info(f"\n📊 Database Statistics:")
        logger.info(f"   Total jobs tracked: {stats.get('total_jobs', 0)}")
        logger.info(f"   New jobs (unread): {stats.get('new_jobs', 0)}")
        logger.info(f"   Searches today: {stats.get('searches_today', 0)}")
        
        logger.info("\n" + "=" * 60)
        logger.info(f"Job check completed at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info("=" * 60 + "\n")
    
    def run_once(self):
        """Run the monitor once and exit"""
        logger.info("Running monitor in single-run mode")
        self.check_for_jobs()
    
    def run_scheduled(self):
        """Run the monitor on a schedule"""
        interval = self.config['check_interval']
        logger.info(f"Starting scheduled monitoring (every {interval} minutes)")
        logger.info("Press Ctrl+C to stop")
        
        # Run immediately
        self.check_for_jobs()
        
        # Schedule periodic checks
        schedule.every(interval).minutes.do(self.check_for_jobs)
        
        try:
            while True:
                schedule.run_pending()
                time.sleep(30)  # Check every 30 seconds
        except KeyboardInterrupt:
            logger.info("\nMonitor stopped by user")
    
    def show_statistics(self):
        """Display database statistics"""
        stats = self.database.get_statistics()
        
        print("\n" + "=" * 60)
        print("📊 JOB MONITOR STATISTICS")
        print("=" * 60)
        print(f"\nTotal jobs tracked: {stats.get('total_jobs', 0)}")
        print(f"New jobs (unread): {stats.get('new_jobs', 0)}")
        print(f"Searches today: {stats.get('searches_today', 0)}")
        
        jobs_by_source = stats.get('jobs_by_source', {})
        if jobs_by_source:
            print("\nJobs by source:")
            for source, count in jobs_by_source.items():
                print(f"  - {source}: {count}")
        
        print("=" * 60 + "\n")
    
    def show_new_jobs(self, mark_as_read: bool = False):
        """Display new jobs"""
        new_jobs = self.database.get_new_jobs(mark_as_read=mark_as_read)
        
        if not new_jobs:
            print("\nNo new jobs to display\n")
            return
        
        print("\n" + "=" * 60)
        print(f"📋 NEW JOB LISTINGS ({len(new_jobs)})")
        print("=" * 60 + "\n")
        
        for i, job in enumerate(new_jobs, 1):
            print(f"{i}. {job['title']}")
            print(f"   Company: {job['company']}")
            print(f"   Location: {job['location']}")
            print(f"   Source: {job['source']}")
            print(f"   First seen: {job['first_seen']}")
            if job['url']:
                print(f"   URL: {job['url']}")
            print()
        
        print("=" * 60 + "\n")
    
    def cleanup_old_jobs(self, days: int = 30):
        """Remove old job listings"""
        logger.info(f"Cleaning up jobs older than {days} days")
        deleted = self.database.clear_old_jobs(days)
        logger.info(f"Removed {deleted} old job listings")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Job Listing Monitor - Track job postings from multiple sources'
    )
    parser.add_argument(
        '--mode',
        choices=['run', 'schedule', 'stats', 'new', 'test-email', 'cleanup'],
        default='schedule',
        help='Operation mode (default: schedule)'
    )
    parser.add_argument(
        '--search',
        type=str,
        help='Job search terms (comma-separated)'
    )
    parser.add_argument(
        '--location',
        type=str,
        help='Job location'
    )
    parser.add_argument(
        '--sources',
        type=str,
        help='Job sources to scrape (comma-separated): indeed, linkedin'
    )
    parser.add_argument(
        '--mark-read',
        action='store_true',
        help='Mark jobs as read when displaying new jobs'
    )
    parser.add_argument(
        '--cleanup-days',
        type=int,
        default=30,
        help='Days to keep job listings (default: 30)'
    )
    
    args = parser.parse_args()
    
    # Build configuration
    config = {}
    if args.search:
        config['search_terms'] = [s.strip() for s in args.search.split(',')]
    if args.location:
        config['location'] = args.location
    if args.sources:
        config['sources'] = [s.strip() for s in args.sources.split(',')]
    
    # Initialize monitor
    monitor = JobMonitor(config if config else None)
    
    # Execute based on mode
    if args.mode == 'run':
        monitor.run_once()
    elif args.mode == 'schedule':
        monitor.run_scheduled()
    elif args.mode == 'stats':
        monitor.show_statistics()
    elif args.mode == 'new':
        monitor.show_new_jobs(mark_as_read=args.mark_read)
    elif args.mode == 'test-email':
        print("Testing email configuration...")
        if monitor.notifier.test_email():
            print("✅ Test email sent successfully!")
        else:
            print("❌ Failed to send test email. Check your configuration.")
    elif args.mode == 'cleanup':
        monitor.cleanup_old_jobs(args.cleanup_days)


if __name__ == "__main__":
    main()
