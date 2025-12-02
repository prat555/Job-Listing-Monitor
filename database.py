"""
Database Module
Handles storage and retrieval of job listings using SQLite
"""

import sqlite3
import logging
from datetime import datetime
from typing import List, Dict, Optional
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class JobDatabase:
    """SQLite database manager for job listings"""
    
    def __init__(self, db_path: str = "jobs.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize the database with required tables"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Create jobs table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS jobs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    job_id TEXT NOT NULL,
                    title TEXT NOT NULL,
                    company TEXT,
                    location TEXT,
                    url TEXT,
                    source TEXT NOT NULL,
                    search_term TEXT,
                    first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_new BOOLEAN DEFAULT 1,
                    UNIQUE(job_id, source)
                )
            ''')
            
            # Create search history table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS search_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    search_term TEXT NOT NULL,
                    location TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    jobs_found INTEGER DEFAULT 0
                )
            ''')
            
            # Create index for faster queries
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_job_id_source 
                ON jobs(job_id, source)
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_is_new 
                ON jobs(is_new)
            ''')
            
            conn.commit()
            conn.close()
            logger.info("Database initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing database: {e}")
            raise
    
    def add_job(self, job: Dict) -> bool:
        """
        Add a job to the database or update if it already exists
        Returns True if job is new, False if it already existed
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Check if job already exists
            cursor.execute(
                "SELECT id FROM jobs WHERE job_id = ? AND source = ?",
                (job['job_id'], job['source'])
            )
            existing = cursor.fetchone()
            
            if existing:
                # Update last_seen timestamp
                cursor.execute(
                    "UPDATE jobs SET last_seen = CURRENT_TIMESTAMP WHERE id = ?",
                    (existing[0],)
                )
                conn.commit()
                conn.close()
                return False
            else:
                # Insert new job
                cursor.execute('''
                    INSERT INTO jobs (job_id, title, company, location, url, source, search_term)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    job['job_id'],
                    job['title'],
                    job.get('company', 'N/A'),
                    job.get('location', 'N/A'),
                    job.get('url', ''),
                    job['source'],
                    job.get('search_term', '')
                ))
                conn.commit()
                conn.close()
                logger.info(f"Added new job: {job['title']} at {job['company']}")
                return True
        except Exception as e:
            logger.error(f"Error adding job to database: {e}")
            return False
    
    def add_jobs_batch(self, jobs: List[Dict]) -> int:
        """
        Add multiple jobs to database
        Returns count of new jobs added
        """
        new_jobs_count = 0
        for job in jobs:
            if self.add_job(job):
                new_jobs_count += 1
        return new_jobs_count
    
    def get_new_jobs(self, mark_as_read: bool = False) -> List[Dict]:
        """Get all jobs that haven't been notified yet"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT * FROM jobs 
                WHERE is_new = 1 
                ORDER BY first_seen DESC
            ''')
            
            rows = cursor.fetchall()
            jobs = [dict(row) for row in rows]
            
            if mark_as_read:
                cursor.execute("UPDATE jobs SET is_new = 0 WHERE is_new = 1")
                conn.commit()
            
            conn.close()
            return jobs
        except Exception as e:
            logger.error(f"Error getting new jobs: {e}")
            return []
    
    def get_all_jobs(self, limit: int = 100) -> List[Dict]:
        """Get all jobs from database"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT * FROM jobs 
                ORDER BY first_seen DESC 
                LIMIT ?
            ''', (limit,))
            
            rows = cursor.fetchall()
            jobs = [dict(row) for row in rows]
            
            conn.close()
            return jobs
        except Exception as e:
            logger.error(f"Error getting jobs: {e}")
            return []
    
    def get_jobs_by_search(self, search_term: str) -> List[Dict]:
        """Get jobs by search term"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT * FROM jobs 
                WHERE search_term LIKE ? 
                ORDER BY first_seen DESC
            ''', (f'%{search_term}%',))
            
            rows = cursor.fetchall()
            jobs = [dict(row) for row in rows]
            
            conn.close()
            return jobs
        except Exception as e:
            logger.error(f"Error getting jobs by search: {e}")
            return []
    
    def log_search(self, search_term: str, location: str, jobs_found: int):
        """Log a search operation"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO search_history (search_term, location, jobs_found)
                VALUES (?, ?, ?)
            ''', (search_term, location, jobs_found))
            
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"Error logging search: {e}")
    
    def get_statistics(self) -> Dict:
        """Get database statistics"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Total jobs
            cursor.execute("SELECT COUNT(*) FROM jobs")
            total_jobs = cursor.fetchone()[0]
            
            # New jobs
            cursor.execute("SELECT COUNT(*) FROM jobs WHERE is_new = 1")
            new_jobs = cursor.fetchone()[0]
            
            # Jobs by source
            cursor.execute('''
                SELECT source, COUNT(*) as count 
                FROM jobs 
                GROUP BY source
            ''')
            jobs_by_source = dict(cursor.fetchall())
            
            # Recent searches
            cursor.execute('''
                SELECT COUNT(*) FROM search_history 
                WHERE timestamp > datetime('now', '-24 hours')
            ''')
            searches_today = cursor.fetchone()[0]
            
            conn.close()
            
            return {
                'total_jobs': total_jobs,
                'new_jobs': new_jobs,
                'jobs_by_source': jobs_by_source,
                'searches_today': searches_today
            }
        except Exception as e:
            logger.error(f"Error getting statistics: {e}")
            return {}
    
    def clear_old_jobs(self, days: int = 30):
        """Remove jobs older than specified days"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                DELETE FROM jobs 
                WHERE last_seen < datetime('now', '-' || ? || ' days')
            ''', (days,))
            
            deleted = cursor.rowcount
            conn.commit()
            conn.close()
            
            logger.info(f"Deleted {deleted} old job listings")
            return deleted
        except Exception as e:
            logger.error(f"Error clearing old jobs: {e}")
            return 0


if __name__ == "__main__":
    # Test the database
    db = JobDatabase("test_jobs.db")
    
    # Test adding a job
    test_job = {
        'job_id': 'test123',
        'title': 'Senior Python Developer',
        'company': 'Tech Corp',
        'location': 'Remote',
        'url': 'https://example.com/job/test123',
        'source': 'Indeed',
        'search_term': 'python developer'
    }
    
    is_new = db.add_job(test_job)
    print(f"Job added (new: {is_new})")
    
    # Get statistics
    stats = db.get_statistics()
    print(f"\nDatabase Statistics:")
    print(f"Total jobs: {stats['total_jobs']}")
    print(f"New jobs: {stats['new_jobs']}")
    print(f"Jobs by source: {stats['jobs_by_source']}")
    
    # Clean up test database
    if os.path.exists("test_jobs.db"):
        os.remove("test_jobs.db")
        print("\nTest database cleaned up")
