"""Data models for commercial real estate properties."""

from dataclasses import dataclass, field, asdict
from typing import Optional, List, Dict, Any
from datetime import datetime


@dataclass
class Property:
    """Commercial real estate property data model."""

    # Basic Information
    property_id: Optional[str] = None
    source_site: Optional[str] = None
    url: Optional[str] = None
    title: Optional[str] = None
    property_type: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None
    country: Optional[str] = None
    description: Optional[str] = None

    # Pricing & Financial Details
    price: Optional[float] = None
    price_per_sqft: Optional[float] = None
    cap_rate: Optional[float] = None
    noi: Optional[float] = None  # Net Operating Income
    gross_income: Optional[float] = None
    operating_expenses: Optional[float] = None
    cash_on_cash_return: Optional[float] = None

    # Property Features
    building_size: Optional[float] = None  # Square feet
    lot_size: Optional[float] = None  # Acres or square feet
    year_built: Optional[int] = None
    number_of_units: Optional[int] = None
    number_of_stories: Optional[int] = None
    parking_spaces: Optional[int] = None
    zoning: Optional[str] = None
    occupancy_rate: Optional[float] = None

    # Amenities & Features
    amenities: List[str] = field(default_factory=list)
    features: List[str] = field(default_factory=list)

    # Contact Information
    broker_name: Optional[str] = None
    broker_company: Optional[str] = None
    broker_phone: Optional[str] = None
    broker_email: Optional[str] = None

    # Images & Media
    images: List[str] = field(default_factory=list)

    # Metadata
    scraped_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """Convert property to dictionary."""
        data = asdict(self)
        # Convert datetime to string
        if isinstance(data['scraped_at'], datetime):
            data['scraped_at'] = data['scraped_at'].isoformat()
        # Convert lists to comma-separated strings for CSV compatibility
        if data['amenities']:
            data['amenities'] = ', '.join(data['amenities'])
        if data['features']:
            data['features'] = ', '.join(data['features'])
        if data['images']:
            data['images'] = ', '.join(data['images'])
        return data

    def to_csv_row(self) -> Dict[str, Any]:
        """Convert property to CSV-friendly format."""
        return self.to_dict()

    @classmethod
    def get_csv_headers(cls) -> List[str]:
        """Get CSV headers for property data."""
        return [
            'property_id', 'source_site', 'url', 'title', 'property_type',
            'address', 'city', 'state', 'zip_code', 'country', 'description',
            'price', 'price_per_sqft', 'cap_rate', 'noi', 'gross_income',
            'operating_expenses', 'cash_on_cash_return',
            'building_size', 'lot_size', 'year_built', 'number_of_units',
            'number_of_stories', 'parking_spaces', 'zoning', 'occupancy_rate',
            'amenities', 'features',
            'broker_name', 'broker_company', 'broker_phone', 'broker_email',
            'images', 'scraped_at'
        ]


@dataclass
class SearchCriteria:
    """Search criteria for scraping."""

    location: str
    property_type: Optional[str] = None
    min_price: Optional[float] = None
    max_price: Optional[float] = None
    min_size: Optional[float] = None
    max_size: Optional[float] = None
    max_results: int = 50

    def to_dict(self) -> Dict[str, Any]:
        """Convert search criteria to dictionary."""
        return asdict(self)
