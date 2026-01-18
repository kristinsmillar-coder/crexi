#!/usr/bin/env python3
"""Main CLI script for commercial real estate scraper."""

import argparse
import sys
import os
from typing import List

from scrapers.models import Property, SearchCriteria
from scrapers.loopnet import LoopNetScraper
from scrapers.crexi import CrexiScraper
from utils.csv_export import export_to_csv
from utils.helpers import setup_logging, load_config, validate_search_criteria, format_currency


SUPPORTED_SITES = {
    'loopnet': LoopNetScraper,
    'crexi': CrexiScraper,
}


def parse_arguments():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description='Commercial Real Estate Scraper',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  Scrape LoopNet for office properties:
    python main.py --site loopnet --location "New York, NY" --property-type office

  Scrape Crexi with price range:
    python main.py --site crexi --location "Los Angeles, CA" --min-price 500000 --max-price 2000000

  Scrape all supported sites:
    python main.py --site all --location "Chicago, IL" --max-results 50

Property types: office, retail, industrial, multifamily, land, hospitality, healthcare, special_purpose
        """
    )

    parser.add_argument(
        '--site',
        type=str,
        required=True,
        choices=list(SUPPORTED_SITES.keys()) + ['all'],
        help='Target site to scrape (or "all" for all supported sites)'
    )

    parser.add_argument(
        '--location',
        type=str,
        required=True,
        help='Search location (city, state or zip code)'
    )

    parser.add_argument(
        '--property-type',
        type=str,
        choices=['office', 'retail', 'industrial', 'multifamily', 'land', 'hospitality', 'healthcare', 'special_purpose'],
        help='Property type to search for'
    )

    parser.add_argument(
        '--min-price',
        type=float,
        help='Minimum price'
    )

    parser.add_argument(
        '--max-price',
        type=float,
        help='Maximum price'
    )

    parser.add_argument(
        '--min-size',
        type=float,
        help='Minimum building size (square feet)'
    )

    parser.add_argument(
        '--max-size',
        type=float,
        help='Maximum building size (square feet)'
    )

    parser.add_argument(
        '--max-results',
        type=int,
        default=50,
        help='Maximum number of results to scrape per site (default: 50)'
    )

    parser.add_argument(
        '--output',
        type=str,
        help='Output CSV file path (default: auto-generated in output/ directory)'
    )

    parser.add_argument(
        '--log-level',
        type=str,
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        default='INFO',
        help='Logging level (default: INFO)'
    )

    return parser.parse_args()


def scrape_site(site_name: str, scraper_class, criteria: SearchCriteria, config: dict) -> List[Property]:
    """
    Scrape a single site.

    Args:
        site_name: Name of the site
        scraper_class: Scraper class to use
        criteria: Search criteria
        config: Configuration dictionary

    Returns:
        List of Property objects
    """
    print(f"\n{'=' * 60}")
    print(f"Scraping {site_name.upper()}...")
    print(f"{'=' * 60}")

    scraper = scraper_class(
        rate_limit=config['rate_limit'],
        timeout=config['request_timeout']
    )

    try:
        properties = scraper.scrape(criteria)
        print(f"✓ Found {len(properties)} properties on {site_name}")

        # Display summary
        if properties:
            print(f"\nSample results:")
            for i, prop in enumerate(properties[:3], 1):
                print(f"\n  {i}. {prop.title or 'No title'}")
                if prop.address:
                    print(f"     Address: {prop.address}")
                if prop.city and prop.state:
                    print(f"     Location: {prop.city}, {prop.state}")
                if prop.price:
                    print(f"     Price: {format_currency(prop.price)}")
                if prop.building_size:
                    print(f"     Size: {prop.building_size:,.0f} SF")
                if prop.property_type:
                    print(f"     Type: {prop.property_type}")

        return properties

    except Exception as e:
        print(f"✗ Error scraping {site_name}: {e}")
        return []

    finally:
        scraper.close()


def main():
    """Main entry point."""
    args = parse_arguments()

    # Load configuration
    config = load_config()

    # Override log level if specified
    if args.log_level:
        config['log_level'] = args.log_level

    # Setup logging
    setup_logging(config['log_level'])

    # Validate search criteria
    if not validate_search_criteria(args.location, args.property_type):
        print("Error: Invalid search criteria")
        sys.exit(1)

    # Create search criteria
    criteria = SearchCriteria(
        location=args.location,
        property_type=args.property_type,
        min_price=args.min_price,
        max_price=args.max_price,
        min_size=args.min_size,
        max_size=args.max_size,
        max_results=args.max_results
    )

    print("\n" + "=" * 60)
    print("COMMERCIAL REAL ESTATE SCRAPER")
    print("=" * 60)
    print(f"\nSearch Criteria:")
    print(f"  Location: {criteria.location}")
    if criteria.property_type:
        print(f"  Property Type: {criteria.property_type}")
    if criteria.min_price:
        print(f"  Min Price: {format_currency(criteria.min_price)}")
    if criteria.max_price:
        print(f"  Max Price: {format_currency(criteria.max_price)}")
    if criteria.min_size:
        print(f"  Min Size: {criteria.min_size:,.0f} SF")
    if criteria.max_size:
        print(f"  Max Size: {criteria.max_size:,.0f} SF")
    print(f"  Max Results: {criteria.max_results}")

    # Determine which sites to scrape
    if args.site == 'all':
        sites_to_scrape = SUPPORTED_SITES.items()
    else:
        sites_to_scrape = [(args.site, SUPPORTED_SITES[args.site])]

    # Scrape sites
    all_properties = []
    for site_name, scraper_class in sites_to_scrape:
        properties = scrape_site(site_name, scraper_class, criteria, config)
        all_properties.extend(properties)

    # Export results
    if all_properties:
        print(f"\n{'=' * 60}")
        print(f"RESULTS SUMMARY")
        print(f"{'=' * 60}")
        print(f"Total properties scraped: {len(all_properties)}")

        try:
            output_path = export_to_csv(all_properties, args.output)
            print(f"\n✓ Results exported to: {output_path}")

            # Display export path with absolute path
            abs_path = os.path.abspath(output_path)
            print(f"  Full path: {abs_path}")

        except Exception as e:
            print(f"\n✗ Error exporting results: {e}")
            sys.exit(1)

    else:
        print(f"\n{'=' * 60}")
        print("No properties found matching your criteria.")
        print("Try adjusting your search parameters.")
        print(f"{'=' * 60}")
        sys.exit(1)

    print(f"\n{'=' * 60}")
    print("Scraping completed successfully!")
    print(f"{'=' * 60}\n")


if __name__ == '__main__':
    main()
