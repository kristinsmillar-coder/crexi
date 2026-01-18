"""Helper functions and utilities."""

import os
import logging
from typing import Dict, Any
from dotenv import load_dotenv


def load_config() -> Dict[str, Any]:
    """
    Load configuration from environment variables.

    Returns:
        Configuration dictionary
    """
    load_dotenv()

    return {
        'rate_limit': int(os.getenv('RATE_LIMIT', '30')),
        'request_timeout': int(os.getenv('REQUEST_TIMEOUT', '30')),
        'user_agent': os.getenv('USER_AGENT', ''),
        'output_dir': os.getenv('OUTPUT_DIR', 'output'),
        'log_level': os.getenv('LOG_LEVEL', 'INFO'),
        'headless': os.getenv('HEADLESS', 'true').lower() == 'true',
        'proxy': os.getenv('PROXY', ''),
    }


def setup_logging(log_level: str = 'INFO') -> None:
    """
    Configure logging for the application.

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
    """
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)

    logging.basicConfig(
        level=numeric_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )


def format_currency(amount: float) -> str:
    """
    Format number as currency.

    Args:
        amount: Amount to format

    Returns:
        Formatted currency string
    """
    if amount is None:
        return "N/A"

    if amount >= 1_000_000:
        return f"${amount / 1_000_000:.2f}M"
    elif amount >= 1_000:
        return f"${amount / 1_000:.0f}K"
    else:
        return f"${amount:,.2f}"


def format_sqft(sqft: float) -> str:
    """
    Format square footage.

    Args:
        sqft: Square footage

    Returns:
        Formatted string
    """
    if sqft is None:
        return "N/A"

    return f"{sqft:,.0f} SF"


def validate_search_criteria(location: str, property_type: str = None) -> bool:
    """
    Validate search criteria.

    Args:
        location: Search location
        property_type: Property type

    Returns:
        True if valid, False otherwise
    """
    if not location or len(location.strip()) < 2:
        return False

    valid_property_types = [
        'office', 'retail', 'industrial', 'multifamily',
        'land', 'hospitality', 'healthcare', 'special_purpose',
        None  # Allow None for all property types
    ]

    if property_type and property_type.lower() not in [pt for pt in valid_property_types if pt]:
        return False

    return True
