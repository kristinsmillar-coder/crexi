"""LoopNet commercial real estate scraper."""

import re
from typing import List, Optional
from urllib.parse import urlencode, urljoin

from .base import BaseScraper
from .models import Property, SearchCriteria


class LoopNetScraper(BaseScraper):
    """Scraper for LoopNet commercial real estate listings."""

    BASE_URL = "https://www.loopnet.com"
    SEARCH_URL = "https://www.loopnet.com/search"

    PROPERTY_TYPE_MAP = {
        'office': 'Office',
        'retail': 'Retail',
        'industrial': 'Industrial',
        'multifamily': 'Multi-Family',
        'land': 'Land',
        'hospitality': 'Hospitality',
        'healthcare': 'Healthcare',
        'special_purpose': 'SpecialPurpose'
    }

    def _build_search_url(self, criteria: SearchCriteria) -> str:
        """
        Build LoopNet search URL from criteria.

        Args:
            criteria: Search criteria

        Returns:
            Search URL
        """
        params = {
            'sk': criteria.location,
        }

        if criteria.property_type:
            prop_type = self.PROPERTY_TYPE_MAP.get(criteria.property_type.lower())
            if prop_type:
                params['bb'] = prop_type

        if criteria.min_price:
            params['pmin'] = int(criteria.min_price)

        if criteria.max_price:
            params['pmax'] = int(criteria.max_price)

        return f"{self.SEARCH_URL}?{urlencode(params)}"

    def search(self, criteria: SearchCriteria) -> List[Property]:
        """
        Search for properties on LoopNet.

        Args:
            criteria: Search criteria

        Returns:
            List of Property objects
        """
        properties = []
        search_url = self._build_search_url(criteria)

        self.logger.info(f"Searching LoopNet: {search_url}")

        try:
            response = self._make_request(search_url)
            soup = self._parse_html(response.text)

            # Find property listing cards
            # Note: LoopNet's structure may change, this is a template implementation
            listings = soup.find_all('article', class_=re.compile(r'placard|listing-card|property-card'))

            if not listings:
                # Try alternative selectors
                listings = soup.find_all('div', class_=re.compile(r'property|listing'))

            self.logger.info(f"Found {len(listings)} listings on LoopNet")

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

    def _parse_listing_card(self, listing) -> Optional[Property]:
        """
        Parse a property listing card from search results.

        Args:
            listing: BeautifulSoup element

        Returns:
            Property object or None
        """
        try:
            prop = Property(source_site='LoopNet')

            # Extract URL
            link = listing.find('a', href=re.compile(r'/for-sale/|/listing/'))
            if link and link.get('href'):
                prop.url = urljoin(self.BASE_URL, link['href'])
                # Extract property ID from URL
                match = re.search(r'/(\d+)/', prop.url)
                if match:
                    prop.property_id = f"loopnet_{match.group(1)}"

            # Extract title
            title_elem = listing.find(['h2', 'h3', 'h4'], class_=re.compile(r'title|heading|property-name'))
            if not title_elem:
                title_elem = listing.find('a', class_=re.compile(r'title|heading'))
            if title_elem:
                prop.title = self._clean_text(title_elem.get_text())

            # Extract address
            address_elem = listing.find(class_=re.compile(r'address|location'))
            if address_elem:
                address_text = self._clean_text(address_elem.get_text())
                prop.address = address_text
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
                prop.building_size = self._parse_number(
                    re.search(r'([\d,]+)', size_elem).group(1)
                )

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

            prop = Property(source_site='LoopNet', url=url)

            # Extract property ID
            match = re.search(r'/(\d+)/', url)
            if match:
                prop.property_id = f"loopnet_{match.group(1)}"

            # Extract title
            title = soup.find('h1', class_=re.compile(r'title|heading|property-name'))
            if title:
                prop.title = self._clean_text(title.get_text())

            # Extract description
            desc = soup.find(class_=re.compile(r'description|summary|details'))
            if desc:
                prop.description = self._clean_text(desc.get_text())

            # Extract financial details
            self._extract_financial_details(soup, prop)

            # Extract property features
            self._extract_property_features(soup, prop)

            # Extract contact information
            self._extract_contact_info(soup, prop)

            # Extract images
            self._extract_images(soup, prop)

            return prop

        except Exception as e:
            self.logger.error(f"Error getting property details: {e}", exc_info=True)
            return None

    def _parse_address(self, address_text: str, prop: Property) -> None:
        """Parse address into components."""
        if not address_text:
            return

        # Simple parsing - can be enhanced
        parts = address_text.split(',')
        if len(parts) >= 2:
            prop.address = parts[0].strip()
            prop.city = parts[1].strip() if len(parts) > 1 else None

            if len(parts) >= 3:
                state_zip = parts[2].strip().split()
                prop.state = state_zip[0] if state_zip else None
                if len(state_zip) > 1:
                    prop.zip_code = state_zip[1]

    def _extract_financial_details(self, soup, prop: Property) -> None:
        """Extract financial details from property page."""
        # Price
        price_elem = soup.find(class_=re.compile(r'price|asking|sale-price'))
        if price_elem:
            prop.price = self._parse_price(price_elem.get_text())

        # Price per square foot
        psf_elem = soup.find(text=re.compile(r'price.*per.*sf|psf', re.I))
        if psf_elem:
            prop.price_per_sqft = self._parse_price(psf_elem)

        # Cap rate
        cap_elem = soup.find(text=re.compile(r'cap\s*rate', re.I))
        if cap_elem:
            # Find the next element or parent that contains the value
            parent = cap_elem.parent
            if parent:
                prop.cap_rate = self._parse_percentage(parent.get_text())

        # NOI
        noi_elem = soup.find(text=re.compile(r'NOI|net.*operating.*income', re.I))
        if noi_elem:
            parent = noi_elem.parent
            if parent:
                prop.noi = self._parse_price(parent.get_text())

    def _extract_property_features(self, soup, prop: Property) -> None:
        """Extract property features from property page."""
        # Building size
        size_elem = soup.find(text=re.compile(r'building.*size|square.*feet|sq.*ft', re.I))
        if size_elem:
            match = re.search(r'([\d,]+)', size_elem.parent.get_text() if size_elem.parent else size_elem)
            if match:
                prop.building_size = self._parse_number(match.group(1))

        # Lot size
        lot_elem = soup.find(text=re.compile(r'lot.*size|land.*area', re.I))
        if lot_elem:
            match = re.search(r'([\d,]+)', lot_elem.parent.get_text() if lot_elem.parent else lot_elem)
            if match:
                prop.lot_size = self._parse_number(match.group(1))

        # Year built
        year_elem = soup.find(text=re.compile(r'year.*built|built.*in', re.I))
        if year_elem:
            match = re.search(r'(19|20)\d{2}', year_elem.parent.get_text() if year_elem.parent else year_elem)
            if match:
                prop.year_built = int(match.group(0))

        # Extract amenities
        amenities = soup.find_all(class_=re.compile(r'amenity|feature'))
        prop.amenities = [self._clean_text(am.get_text()) for am in amenities if am.get_text().strip()]

    def _extract_contact_info(self, soup, prop: Property) -> None:
        """Extract contact information from property page."""
        # Broker name
        broker_elem = soup.find(class_=re.compile(r'broker|agent|contact-name'))
        if broker_elem:
            prop.broker_name = self._clean_text(broker_elem.get_text())

        # Broker company
        company_elem = soup.find(class_=re.compile(r'company|brokerage|firm'))
        if company_elem:
            prop.broker_company = self._clean_text(company_elem.get_text())

        # Phone number
        phone_elem = soup.find(text=re.compile(r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}'))
        if phone_elem:
            match = re.search(r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}', phone_elem)
            if match:
                prop.broker_phone = match.group(0)

        # Email
        email_elem = soup.find('a', href=re.compile(r'mailto:'))
        if email_elem:
            prop.broker_email = email_elem['href'].replace('mailto:', '')

    def _extract_images(self, soup, prop: Property) -> None:
        """Extract property images from property page."""
        # Find all image elements
        images = soup.find_all('img', class_=re.compile(r'property|listing|photo'))

        for img in images:
            src = img.get('src') or img.get('data-src')
            if src and 'loopnet' in src:
                # Get full-size image URL
                full_url = urljoin(self.BASE_URL, src)
                if full_url not in prop.images:
                    prop.images.append(full_url)
