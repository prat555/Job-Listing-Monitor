"""
Job Scraper Module
Scrapes job listings from various job boards
"""

import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import time
from typing import List, Dict
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class JobScraper:
    """Base class for job scraping"""
    
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
    
    def scrape_jobs(self, search_term: str, location: str = "", max_pages: int = 5) -> List[Dict]:
        """Override this method in subclasses"""
        raise NotImplementedError


class IndeedScraper(JobScraper):
    """Scraper for Indeed.com"""
    
    def __init__(self):
        super().__init__()
        self.base_url = "https://www.indeed.com"
    
    def scrape_jobs(self, search_term: str, location: str = "", max_pages: int = 5) -> List[Dict]:
        """Scrape jobs from Indeed"""
        jobs = []
        
        try:
            for page in range(max_pages):
                start = page * 10
                url = f"{self.base_url}/jobs?q={search_term.replace(' ', '+')}&l={location.replace(' ', '+')}&start={start}"
                
                logger.info(f"Scraping Indeed page {page + 1}: {url}")
                response = requests.get(url, headers=self.headers, timeout=10)
                
                if response.status_code != 200:
                    logger.warning(f"Failed to fetch page {page + 1}, status: {response.status_code}")
                    continue
                
                soup = BeautifulSoup(response.content, 'html.parser')
                job_cards = soup.find_all('div', class_='job_seen_beacon')
                
                if not job_cards:
                    logger.info("No more jobs found")
                    break
                
                for card in job_cards:
                    try:
                        title_elem = card.find('h2', class_='jobTitle')
                        company_elem = card.find('span', {'data-testid': 'company-name'})
                        location_elem = card.find('div', {'data-testid': 'text-location'})
                        
                        if title_elem:
                            job_link = title_elem.find('a')
                            title = title_elem.get_text(strip=True)
                            job_id = job_link.get('data-jk', '') if job_link else ''
                            job_url = f"{self.base_url}/viewjob?jk={job_id}" if job_id else ""
                            
                            job = {
                                'title': title,
                                'company': company_elem.get_text(strip=True) if company_elem else "N/A",
                                'location': location_elem.get_text(strip=True) if location_elem else "N/A",
                                'url': job_url,
                                'source': 'Indeed',
                                'job_id': job_id,
                                'search_term': search_term
                            }
                            jobs.append(job)
                    except Exception as e:
                        logger.error(f"Error parsing job card: {e}")
                        continue
                
                time.sleep(2)  # Be respectful to the server
        
        except Exception as e:
            logger.error(f"Error scraping Indeed: {e}")
        
        logger.info(f"Found {len(jobs)} jobs on Indeed")
        return jobs


class LinkedInScraper(JobScraper):
    """Scraper for LinkedIn (requires Selenium due to dynamic content)"""
    
    def __init__(self):
        super().__init__()
        self.base_url = "https://www.linkedin.com"
    
    def _setup_driver(self):
        """Setup Chrome driver with headless option"""
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument(f'user-agent={self.headers["User-Agent"]}')
        
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        return driver
    
    def scrape_jobs(self, search_term: str, location: str = "", max_pages: int = 3) -> List[Dict]:
        """Scrape jobs from LinkedIn"""
        jobs = []
        driver = None
        
        try:
            driver = self._setup_driver()
            
            for page in range(max_pages):
                start = page * 25
                url = f"{self.base_url}/jobs/search/?keywords={search_term.replace(' ', '%20')}&location={location.replace(' ', '%20')}&start={start}"
                
                logger.info(f"Scraping LinkedIn page {page + 1}")
                driver.get(url)
                time.sleep(3)  # Wait for page to load
                
                # Scroll to load more jobs
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2)
                
                soup = BeautifulSoup(driver.page_source, 'html.parser')
                job_cards = soup.find_all('div', class_='base-card')
                
                if not job_cards:
                    logger.info("No more jobs found on LinkedIn")
                    break
                
                for card in job_cards:
                    try:
                        title_elem = card.find('h3', class_='base-search-card__title')
                        company_elem = card.find('h4', class_='base-search-card__subtitle')
                        location_elem = card.find('span', class_='job-search-card__location')
                        link_elem = card.find('a', class_='base-card__full-link')
                        
                        if title_elem and link_elem:
                            job_url = link_elem.get('href', '')
                            job_id = job_url.split('/')[-1].split('?')[0] if job_url else ''
                            
                            job = {
                                'title': title_elem.get_text(strip=True),
                                'company': company_elem.get_text(strip=True) if company_elem else "N/A",
                                'location': location_elem.get_text(strip=True) if location_elem else "N/A",
                                'url': job_url,
                                'source': 'LinkedIn',
                                'job_id': job_id,
                                'search_term': search_term
                            }
                            jobs.append(job)
                    except Exception as e:
                        logger.error(f"Error parsing LinkedIn job card: {e}")
                        continue
                
                time.sleep(3)  # Be respectful to the server
        
        except Exception as e:
            logger.error(f"Error scraping LinkedIn: {e}")
        finally:
            if driver:
                driver.quit()
        
        logger.info(f"Found {len(jobs)} jobs on LinkedIn")
        return jobs


class JobScraperManager:
    """Manager class to coordinate multiple scrapers"""
    
    def __init__(self):
        self.scrapers = {
            'indeed': IndeedScraper(),
            'linkedin': LinkedInScraper()
        }
    
    def scrape_all_sources(self, search_term: str, location: str = "", 
                          sources: List[str] = None, max_pages: int = 5) -> List[Dict]:
        """Scrape jobs from all specified sources"""
        if sources is None:
            sources = list(self.scrapers.keys())
        
        all_jobs = []
        
        for source in sources:
            if source in self.scrapers:
                logger.info(f"Starting scrape from {source}")
                try:
                    jobs = self.scrapers[source].scrape_jobs(search_term, location, max_pages)
                    all_jobs.extend(jobs)
                except Exception as e:
                    logger.error(f"Failed to scrape {source}: {e}")
            else:
                logger.warning(f"Unknown source: {source}")
        
        logger.info(f"Total jobs scraped: {len(all_jobs)}")
        return all_jobs


if __name__ == "__main__":
    # Test the scraper
    manager = JobScraperManager()
    jobs = manager.scrape_all_sources(
        search_term="python developer",
        location="remote",
        sources=['indeed'],  # Test with Indeed only
        max_pages=2
    )
    
    for job in jobs[:5]:  # Print first 5 jobs
        print(f"\nTitle: {job['title']}")
        print(f"Company: {job['company']}")
        print(f"Location: {job['location']}")
        print(f"Source: {job['source']}")
        print(f"URL: {job['url']}")
