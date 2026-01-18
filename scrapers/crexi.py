"""Crexi commercial real estate scraper."""

import re
import json
from typing import List, Optional
from urllib.parse import urlencode, urljoin

from .base import BaseScraper
from .models import Property, SearchCriteria


class CrexiScraper(BaseScraper):
    """Scraper for Crexi commercial real estate listings."""

    BASE_URL = "https://www.crexi.com"
    SEARCH_URL = "https://www.crexi.com/properties"

    PROPERTY_TYPE_MAP = {
        'office': 'office',
        'retail': 'retail',
        'industrial': 'industrial',
        'multifamily': 'multifamily',
        'land': 'land',
        'hospitality': 'hospitality',
        'healthcare': 'healthcare',
        'special_purpose': 'special-purpose'
    }

    def _build_search_url(self, criteria: SearchCriteria) -> str:
        """
        Build Crexi search URL from criteria.

        Args:
            criteria: Search criteria

        Returns:
            Search URL
        """
        params = {}

        if criteria.location:
            params['q'] = criteria.location

        if criteria.property_type:
            prop_type = self.PROPERTY_TYPE_MAP.get(criteria.property_type.lower())
            if prop_type:
                params['propertyTypes'] = prop_type

        if criteria.min_price:
            params['minPrice'] = int(criteria.min_price)

        if criteria.max_price:
            params['maxPrice'] = int(criteria.max_price)

        if criteria.min_size:
            params['minSize'] = int(criteria.min_size)

        if criteria.max_size:
            params['maxSize'] = int(criteria.max_size)

        return f"{self.SEARCH_URL}?{urlencode(params)}" if params else self.SEARCH_URL

    def search(self, criteria: SearchCriteria) -> List[Property]:
        """
        Search for properties on Crexi.

        Args:
            criteria: Search criteria

        Returns:
            List of Property objects
        """
        properties = []
        search_url = self._build_search_url(criteria)

        self.logger.info(f"Searching Crexi: {search_url}")

        try:
            response = self._make_request(search_url)
            soup = self._parse_html(response.text)

            # Try to find JSON data embedded in the page (Crexi often uses this)
            script_tags = soup.find_all('script', type='application/json')
            for script in script_tags:
                try:
                    data = json.loads(script.string)
                    if 'properties' in data or 'listings' in data:
                        properties_data = data.get('properties', data.get('listings', []))
                        for prop_data in properties_data[:criteria.max_results]:
                            prop = self._parse_json_property(prop_data)
                            if prop:
                                properties.append(prop)
                        return properties
                except (json.JSONDecodeError, KeyError):
                    continue

            # Fallback to HTML parsing
            listings = soup.find_all(class_=re.compile(r'property-card|listing-card|property-item'))

            if not listings:
                # Try alternative selectors
                listings = soup.find_all('div', attrs={'data-property-id': True})
                if not listings:
                    listings = soup.find_all('article', class_=re.compile(r'property|listing'))

            self.logger.info(f"Found {len(listings)} listings on Crexi")

            for idx, listing in enumerate(listings[:criteria.max_results]):
                try:
                    prop = self._parse_listing_card(listing)
                    if prop:
                        properties.append(prop)

                        # Get detailed information if URL is available
                        if prop.url:
                            detailed_prop = self.get_property_details(prop.url)
                            if detailed_prop:
                                properties[-1] = detailed_prop

                except Exception as e:
                    self.logger.error(f"Error parsing listing {idx}: {e}")
                    continue

        except Exception as e:
            self.logger.error(f"Search failed: {e}", exc_info=True)

        return properties

    def _parse_json_property(self, data: dict) -> Optional[Property]:
        """
        Parse property from JSON data.

        Args:
            data: Property JSON data

        Returns:
            Property object or None
        """
        try:
            prop = Property(source_site='Crexi')

            # Basic information
            prop.property_id = f"crexi_{data.get('id', '')}"
            prop.title = data.get('name') or data.get('title')
            prop.url = urljoin(self.BASE_URL, data.get('url', ''))
            prop.description = data.get('description')
            prop.property_type = data.get('propertyType')

            # Address
            address = data.get('address', {})
            if isinstance(address, dict):
                prop.address = address.get('street')
                prop.city = address.get('city')
                prop.state = address.get('state')
                prop.zip_code = address.get('zipCode')
                prop.country = address.get('country', 'USA')

            # Pricing
            prop.price = data.get('price') or data.get('askingPrice')
            prop.price_per_sqft = data.get('pricePerSqFt')

            # Financial details
            prop.cap_rate = data.get('capRate')
            prop.noi = data.get('noi') or data.get('netOperatingIncome')
            prop.gross_income = data.get('grossIncome')

            # Property features
            prop.building_size = data.get('buildingSize') or data.get('squareFeet')
            prop.lot_size = data.get('lotSize')
            prop.year_built = data.get('yearBuilt')
            prop.number_of_units = data.get('numberOfUnits')
            prop.parking_spaces = data.get('parkingSpaces')
            prop.zoning = data.get('zoning')
            prop.occupancy_rate = data.get('occupancyRate')

            # Amenities
            if 'amenities' in data:
                prop.amenities = data.get('amenities', [])

            # Contact information
            broker = data.get('broker', {})
            if isinstance(broker, dict):
                prop.broker_name = broker.get('name')
                prop.broker_company = broker.get('company')
                prop.broker_phone = broker.get('phone')
                prop.broker_email = broker.get('email')

            # Images
            if 'images' in data:
                prop.images = data.get('images', [])

            return prop

        except Exception as e:
            self.logger.error(f"Error parsing JSON property: {e}")
            return None

    def _parse_listing_card(self, listing) -> Optional[Property]:
        """
        Parse a property listing card from search results.

        Args:
            listing: BeautifulSoup element

        Returns:
            Property object or None
        """
        try:
            prop = Property(source_site='Crexi')

            # Extract property ID
            prop_id = listing.get('data-property-id') or listing.get('id')
            if prop_id:
                prop.property_id = f"crexi_{prop_id}"

            # Extract URL
            link = listing.find('a', href=re.compile(r'/properties/|/listing/'))
            if link and link.get('href'):
                prop.url = urljoin(self.BASE_URL, link['href'])

            # Extract title
            title_elem = listing.find(['h2', 'h3', 'h4'], class_=re.compile(r'title|name|heading'))
            if not title_elem:
                title_elem = listing.find('a', class_=re.compile(r'title|name'))
            if title_elem:
                prop.title = self._clean_text(title_elem.get_text())

            # Extract address
            address_elem = listing.find(class_=re.compile(r'address|location'))
            if address_elem:
                address_text = self._clean_text(address_elem.get_text())
                self._parse_address(address_text, prop)

            # Extract price
            price_elem = listing.find(class_=re.compile(r'price|asking'))
            if price_elem:
                prop.price = self._parse_price(price_elem.get_text())

            # Extract property type
            type_elem = listing.find(class_=re.compile(r'property-type|type'))
            if type_elem:
                prop.property_type = self._clean_text(type_elem.get_text())

            # Extract building size
            size_elem = listing.find(text=re.compile(r'\d+[,\d]*\s*(SF|sq\s*ft)', re.I))
            if size_elem:
                match = re.search(r'([\d,]+)', size_elem)
                if match:
                    prop.building_size = self._parse_number(match.group(1))

            # Extract cap rate
            cap_elem = listing.find(text=re.compile(r'cap.*rate|CAP', re.I))
            if cap_elem:
                prop.cap_rate = self._parse_percentage(cap_elem)

            return prop

        except Exception as e:
            self.logger.error(f"Error parsing listing card: {e}")
            return None

    def get_property_details(self, url: str) -> Optional[Property]:
        """
        Get detailed information for a property.

        Args:
            url: Property listing URL

        Returns:
            Property object or None
        """
        self.logger.debug(f"Fetching details from: {url}")

        try:
            response = self._make_request(url)
            soup = self._parse_html(response.text)

            # Try to find JSON-LD structured data
            json_ld = soup.find('script', type='application/ld+json')
            if json_ld:
                try:
                    data = json.loads(json_ld.string)
                    if data.get('@type') == 'RealEstateListing':
                        return self._parse_json_ld(data, url)
                except json.JSONDecodeError:
                    pass

            # Fallback to HTML parsing
            prop = Property(source_site='Crexi', url=url)

            # Extract property ID
            match = re.search(r'/(\d+)', url)
            if match:
                prop.property_id = f"crexi_{match.group(1)}"

            # Extract title
            title = soup.find('h1', class_=re.compile(r'title|heading|property-name'))
            if title:
                prop.title = self._clean_text(title.get_text())

            # Extract description
            desc = soup.find(class_=re.compile(r'description|summary|about'))
            if desc:
                prop.description = self._clean_text(desc.get_text())

            # Extract details
            self._extract_financial_details(soup, prop)
            self._extract_property_features(soup, prop)
            self._extract_contact_info(soup, prop)
            self._extract_images(soup, prop)

            return prop

        except Exception as e:
            self.logger.error(f"Error getting property details: {e}", exc_info=True)
            return None

    def _parse_json_ld(self, data: dict, url: str) -> Optional[Property]:
        """Parse property from JSON-LD structured data."""
        try:
            prop = Property(source_site='Crexi', url=url)

            prop.title = data.get('name')
            prop.description = data.get('description')

            # Address
            address = data.get('address', {})
            if isinstance(address, dict):
                prop.address = address.get('streetAddress')
                prop.city = address.get('addressLocality')
                prop.state = address.get('addressRegion')
                prop.zip_code = address.get('postalCode')

            # Price
            offers = data.get('offers', {})
            if isinstance(offers, dict):
                prop.price = self._parse_price(str(offers.get('price', '')))

            return prop

        except Exception as e:
            self.logger.error(f"Error parsing JSON-LD: {e}")
            return None

    def _parse_address(self, address_text: str, prop: Property) -> None:
        """Parse address into components."""
        if not address_text:
            return

        parts = [p.strip() for p in address_text.split(',')]
        if len(parts) >= 1:
            prop.address = parts[0]
        if len(parts) >= 2:
            prop.city = parts[1]
        if len(parts) >= 3:
            state_zip = parts[2].split()
            prop.state = state_zip[0] if state_zip else None
            if len(state_zip) > 1:
                prop.zip_code = state_zip[1]

    def _extract_financial_details(self, soup, prop: Property) -> None:
        """Extract financial details from property page."""
        # Price
        price_elem = soup.find(class_=re.compile(r'price|asking|sale-price'))
        if price_elem:
            prop.price = self._parse_price(price_elem.get_text())

        # Find data table or details section
        details = soup.find_all(class_=re.compile(r'detail|info|spec|metric'))

        for detail in details:
            text = detail.get_text().lower()

            if 'cap rate' in text:
                prop.cap_rate = self._parse_percentage(detail.get_text())
            elif 'noi' in text or 'net operating income' in text:
                prop.noi = self._parse_price(detail.get_text())
            elif 'price/sf' in text or 'price per' in text:
                prop.price_per_sqft = self._parse_price(detail.get_text())
            elif 'gross income' in text:
                prop.gross_income = self._parse_price(detail.get_text())

    def _extract_property_features(self, soup, prop: Property) -> None:
        """Extract property features from property page."""
        details = soup.find_all(class_=re.compile(r'detail|info|spec|feature'))

        for detail in details:
            text = detail.get_text().lower()

            if 'building size' in text or 'square feet' in text or 'sf' in text:
                match = re.search(r'([\d,]+)', detail.get_text())
                if match:
                    prop.building_size = self._parse_number(match.group(1))

            elif 'lot size' in text or 'land area' in text:
                match = re.search(r'([\d,]+)', detail.get_text())
                if match:
                    prop.lot_size = self._parse_number(match.group(1))

            elif 'year built' in text or 'built in' in text:
                match = re.search(r'(19|20)\d{2}', detail.get_text())
                if match:
                    prop.year_built = int(match.group(0))

            elif 'units' in text:
                match = re.search(r'(\d+)', detail.get_text())
                if match:
                    prop.number_of_units = int(match.group(1))

            elif 'parking' in text:
                match = re.search(r'(\d+)', detail.get_text())
                if match:
                    prop.parking_spaces = int(match.group(1))

            elif 'zoning' in text:
                prop.zoning = self._clean_text(detail.get_text().replace('Zoning:', ''))

        # Extract amenities
        amenities = soup.find_all(class_=re.compile(r'amenity|feature-item'))
        prop.amenities = [self._clean_text(am.get_text()) for am in amenities if am.get_text().strip()]

    def _extract_contact_info(self, soup, prop: Property) -> None:
        """Extract contact information from property page."""
        # Broker information
        broker_section = soup.find(class_=re.compile(r'broker|agent|contact'))

        if broker_section:
            # Name
            name_elem = broker_section.find(class_=re.compile(r'name'))
            if name_elem:
                prop.broker_name = self._clean_text(name_elem.get_text())

            # Company
            company_elem = broker_section.find(class_=re.compile(r'company|firm'))
            if company_elem:
                prop.broker_company = self._clean_text(company_elem.get_text())

            # Phone
            phone_elem = broker_section.find(text=re.compile(r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}'))
            if phone_elem:
                match = re.search(r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}', phone_elem)
                if match:
                    prop.broker_phone = match.group(0)

            # Email
            email_elem = broker_section.find('a', href=re.compile(r'mailto:'))
            if email_elem:
                prop.broker_email = email_elem['href'].replace('mailto:', '')

    def _extract_images(self, soup, prop: Property) -> None:
        """Extract property images from property page."""
        # Find image gallery or slideshow
        gallery = soup.find(class_=re.compile(r'gallery|slideshow|photos|images'))

        if gallery:
            images = gallery.find_all('img')
        else:
            images = soup.find_all('img', class_=re.compile(r'property|listing|photo'))

        for img in images:
            src = img.get('src') or img.get('data-src') or img.get('data-lazy')
            if src and ('crexi' in src or src.startswith('/')):
                full_url = urljoin(self.BASE_URL, src)
                # Get high-resolution version if available
                high_res = full_url.replace('/thumb/', '/large/').replace('_thumb', '_large')
                if high_res not in prop.images:
                    prop.images.append(high_res)
