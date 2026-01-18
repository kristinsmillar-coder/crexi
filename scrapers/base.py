"""Base scraper class with common functionality."""

import time
import logging
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from datetime import datetime

import requests
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
from tenacity import retry, stop_after_attempt, wait_exponential

from .models import Property, SearchCriteria


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


class BaseScraper(ABC):
    """Base class for commercial real estate scrapers."""

    def __init__(self, rate_limit: int = 30, timeout: int = 30):
        """
        Initialize base scraper.

        Args:
            rate_limit: Maximum requests per minute
            timeout: Request timeout in seconds
        """
        self.rate_limit = rate_limit
        self.timeout = timeout
        self.logger = logging.getLogger(self.__class__.__name__)
        self.ua = UserAgent()
        self.session = self._create_session()
        self.last_request_time = 0

    def _create_session(self) -> requests.Session:
        """Create and configure requests session."""
        session = requests.Session()
        session.headers.update({
            'User-Agent': self.ua.random,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        })
        return session

    def _rate_limit(self):
        """Implement rate limiting between requests."""
        if self.rate_limit > 0:
            min_interval = 60.0 / self.rate_limit
            elapsed = time.time() - self.last_request_time
            if elapsed < min_interval:
                time.sleep(min_interval - elapsed)
        self.last_request_time = time.time()

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True
    )
    def _make_request(self, url: str, method: str = 'GET', **kwargs) -> requests.Response:
        """
        Make HTTP request with retry logic.

        Args:
            url: URL to request
            method: HTTP method (GET, POST, etc.)
            **kwargs: Additional arguments for requests

        Returns:
            Response object
        """
        self._rate_limit()

        self.logger.debug(f"Making {method} request to: {url}")

        try:
            response = self.session.request(
                method=method,
                url=url,
                timeout=self.timeout,
                **kwargs
            )
            response.raise_for_status()
            return response

        except requests.exceptions.RequestException as e:
            self.logger.error(f"Request failed: {e}")
            raise

    def _parse_html(self, html: str) -> BeautifulSoup:
        """
        Parse HTML content.

        Args:
            html: HTML string

        Returns:
            BeautifulSoup object
        """
        return BeautifulSoup(html, 'lxml')

    def _clean_text(self, text: Optional[str]) -> Optional[str]:
        """
        Clean and normalize text.

        Args:
            text: Raw text

        Returns:
            Cleaned text or None
        """
        if not text:
            return None
        return ' '.join(text.split()).strip()

    def _parse_price(self, price_str: Optional[str]) -> Optional[float]:
        """
        Parse price string to float.

        Args:
            price_str: Price string (e.g., "$1,500,000")

        Returns:
            Price as float or None
        """
        if not price_str:
            return None

        try:
            # Remove currency symbols, commas, and whitespace
            cleaned = price_str.replace('$', '').replace(',', '').replace(' ', '')
            # Handle "M" for millions
            if 'M' in cleaned.upper():
                cleaned = cleaned.upper().replace('M', '')
                return float(cleaned) * 1_000_000
            # Handle "K" for thousands
            if 'K' in cleaned.upper():
                cleaned = cleaned.upper().replace('K', '')
                return float(cleaned) * 1_000
            return float(cleaned)
        except (ValueError, AttributeError):
            return None

    def _parse_number(self, num_str: Optional[str]) -> Optional[float]:
        """
        Parse number string to float.

        Args:
            num_str: Number string

        Returns:
            Number as float or None
        """
        if not num_str:
            return None

        try:
            cleaned = num_str.replace(',', '').replace(' ', '')
            return float(cleaned)
        except (ValueError, AttributeError):
            return None

    def _parse_percentage(self, pct_str: Optional[str]) -> Optional[float]:
        """
        Parse percentage string to float.

        Args:
            pct_str: Percentage string (e.g., "5.5%")

        Returns:
            Percentage as float or None
        """
        if not pct_str:
            return None

        try:
            cleaned = pct_str.replace('%', '').replace(' ', '')
            return float(cleaned)
        except (ValueError, AttributeError):
            return None

    @abstractmethod
    def search(self, criteria: SearchCriteria) -> List[Property]:
        """
        Search for properties based on criteria.

        Args:
            criteria: Search criteria

        Returns:
            List of Property objects
        """
        pass

    @abstractmethod
    def get_property_details(self, url: str) -> Optional[Property]:
        """
        Get detailed information for a single property.

        Args:
            url: Property listing URL

        Returns:
            Property object or None
        """
        pass

    @abstractmethod
    def _build_search_url(self, criteria: SearchCriteria) -> str:
        """
        Build search URL from criteria.

        Args:
            criteria: Search criteria

        Returns:
            Search URL
        """
        pass

    def scrape(self, criteria: SearchCriteria) -> List[Property]:
        """
        Main scraping method.

        Args:
            criteria: Search criteria

        Returns:
            List of Property objects
        """
        self.logger.info(f"Starting scrape with criteria: {criteria.to_dict()}")

        try:
            properties = self.search(criteria)
            self.logger.info(f"Successfully scraped {len(properties)} properties")
            return properties

        except Exception as e:
            self.logger.error(f"Scraping failed: {e}", exc_info=True)
            return []

    def close(self):
        """Close the scraper and cleanup resources."""
        if self.session:
            self.session.close()
