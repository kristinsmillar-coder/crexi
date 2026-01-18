"""CSV export functionality for property data."""

import csv
import os
from typing import List
from datetime import datetime

from scrapers.models import Property


def export_to_csv(properties: List[Property], output_path: str = None) -> str:
    """
    Export properties to CSV file.

    Args:
        properties: List of Property objects
        output_path: Path to output CSV file (optional)

    Returns:
        Path to created CSV file
    """
    if not properties:
        raise ValueError("No properties to export")

    # Generate default filename if not provided
    if not output_path:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = "output"
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, f"properties_{timestamp}.csv")

    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path) or '.', exist_ok=True)

    # Write to CSV
    headers = Property.get_csv_headers()

    with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=headers)
        writer.writeheader()

        for prop in properties:
            writer.writerow(prop.to_csv_row())

    return output_path
