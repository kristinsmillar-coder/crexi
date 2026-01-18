# Usage Guide

This guide provides detailed instructions on how to use the Commercial Real Estate Scraper.

## Table of Contents

1. [Installation](#installation)
2. [Configuration](#configuration)
3. [Basic Usage](#basic-usage)
4. [Advanced Usage](#advanced-usage)
5. [Understanding the Output](#understanding-the-output)
6. [Troubleshooting](#troubleshooting)
7. [Best Practices](#best-practices)

## Installation

### Prerequisites

- Python 3.8 or higher
- pip (Python package installer)
- Virtual environment (recommended)

### Setup Steps

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd crexi
   ```

2. **Create a virtual environment** (recommended):
   ```bash
   # On macOS/Linux
   python3 -m venv venv
   source venv/bin/activate

   # On Windows
   python -m venv venv
   venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment**:
   ```bash
   cp .env.example .env
   # Edit .env with your preferences (optional)
   ```

## Configuration

The scraper can be configured using the `.env` file. Here are the available options:

```env
# Rate limiting (requests per minute)
RATE_LIMIT=30

# Request timeout (seconds)
REQUEST_TIMEOUT=30

# User agent (leave empty for random)
USER_AGENT=

# Output directory
OUTPUT_DIR=output

# Log level (DEBUG, INFO, WARNING, ERROR)
LOG_LEVEL=INFO

# Headless browser mode
HEADLESS=true

# Proxy (optional)
PROXY=
```

## Basic Usage

### Command Structure

```bash
python main.py --site <SITE> --location <LOCATION> [OPTIONS]
```

### Required Arguments

- `--site`: Target site (`loopnet`, `crexi`, or `all`)
- `--location`: Search location (e.g., "New York, NY" or "90210")

### Common Examples

**Scrape LoopNet for office properties**:
```bash
python main.py --site loopnet --location "New York, NY" --property-type office
```

**Scrape Crexi for retail properties with price range**:
```bash
python main.py --site crexi --location "Los Angeles, CA" --property-type retail --min-price 500000 --max-price 2000000
```

**Scrape all sites for industrial properties**:
```bash
python main.py --site all --location "Chicago, IL" --property-type industrial --max-results 100
```

**Scrape with size constraints**:
```bash
python main.py --site loopnet --location "Austin, TX" --min-size 5000 --max-size 50000
```

## Advanced Usage

### Custom Output Path

Specify a custom output file:

```bash
python main.py --site crexi --location "Miami, FL" --output my_miami_properties.csv
```

### Debugging

Enable debug logging to see detailed information:

```bash
python main.py --site loopnet --location "Boston, MA" --log-level DEBUG
```

### Multiple Property Types

To search for multiple property types, run separate commands:

```bash
# Office properties
python main.py --site all --location "Seattle, WA" --property-type office --output seattle_office.csv

# Retail properties
python main.py --site all --location "Seattle, WA" --property-type retail --output seattle_retail.csv
```

### Combining Results

You can merge CSV files using standard tools:

```bash
# On macOS/Linux
cat output/*.csv > combined_results.csv

# Or use Python
python -c "import pandas as pd; import glob; pd.concat([pd.read_csv(f) for f in glob.glob('output/*.csv')]).to_csv('combined.csv', index=False)"
```

## Understanding the Output

### CSV Columns

The output CSV file contains the following columns:

**Basic Information**:
- `property_id`: Unique identifier
- `source_site`: Source website (LoopNet, Crexi)
- `url`: Property listing URL
- `title`: Property title/name
- `property_type`: Type of property
- `address`, `city`, `state`, `zip_code`, `country`: Location details
- `description`: Property description

**Financial Details**:
- `price`: Asking price
- `price_per_sqft`: Price per square foot
- `cap_rate`: Capitalization rate (%)
- `noi`: Net Operating Income
- `gross_income`: Gross income
- `operating_expenses`: Operating expenses
- `cash_on_cash_return`: Cash-on-cash return (%)

**Property Features**:
- `building_size`: Building size (square feet)
- `lot_size`: Lot size (acres or square feet)
- `year_built`: Year constructed
- `number_of_units`: Number of units
- `number_of_stories`: Number of stories
- `parking_spaces`: Number of parking spaces
- `zoning`: Zoning classification
- `occupancy_rate`: Occupancy rate (%)

**Other**:
- `amenities`: Comma-separated amenities
- `features`: Comma-separated features
- `broker_name`, `broker_company`, `broker_phone`, `broker_email`: Contact info
- `images`: Comma-separated image URLs
- `scraped_at`: Timestamp of scraping

### Analyzing the Data

You can analyze the CSV data using tools like:

**Excel**: Open the CSV file directly in Microsoft Excel or Google Sheets

**Python/Pandas**:
```python
import pandas as pd

df = pd.read_csv('output/properties_20260118_120000.csv')

# View summary statistics
print(df.describe())

# Filter by price
expensive = df[df['price'] > 1000000]

# Group by property type
by_type = df.groupby('property_type')['price'].mean()
```

**SQL**: Import into SQLite or another database for advanced queries

## Troubleshooting

### Common Issues

**1. No results found**

- Verify the location is valid
- Try broadening your search criteria (remove price/size filters)
- Check if the site is accessible from your network

**2. Connection errors**

- Check your internet connection
- The site might be blocking automated requests
- Try reducing `RATE_LIMIT` in `.env`
- Check if you need to configure a proxy

**3. Import errors**

- Make sure you've installed all dependencies: `pip install -r requirements.txt`
- Activate your virtual environment
- Try upgrading pip: `pip install --upgrade pip`

**4. Parsing errors**

- Website structure may have changed
- Enable debug logging to see detailed errors: `--log-level DEBUG`
- Report issues on GitHub

### Getting Help

If you encounter issues:

1. Check the debug logs (`--log-level DEBUG`)
2. Review the [README.md](README.md)
3. Search existing GitHub issues
4. Create a new issue with:
   - Error message
   - Command you ran
   - Debug logs
   - Python version

## Best Practices

### Ethical Scraping

1. **Respect robots.txt**: Always check and respect robots.txt files
2. **Rate limiting**: Use appropriate delays between requests
3. **Terms of service**: Read and comply with site terms of service
4. **Attribution**: Give credit to data sources when using the data
5. **Privacy**: Don't scrape or share personal information

### Performance Tips

1. **Start small**: Begin with `--max-results 10` to test
2. **Be patient**: Scraping takes time due to rate limiting
3. **Off-peak hours**: Run scrapers during off-peak hours
4. **Incremental scraping**: Scrape in batches rather than all at once

### Data Quality

1. **Verify results**: Always manually verify a sample of results
2. **Check completeness**: Some fields may be empty if not available
3. **Update regularly**: Property data changes frequently
4. **Clean data**: Use data validation and cleaning tools

### Legal Compliance

1. **Know the law**: Understand data scraping laws in your jurisdiction
2. **Public data only**: Only scrape publicly available information
3. **Commercial use**: Be aware of restrictions on commercial use
4. **Data protection**: Comply with GDPR, CCPA, and other regulations
5. **Consult legal**: When in doubt, consult with legal counsel

## Examples by Use Case

### Investment Research

Find high-cap-rate properties:
```bash
python main.py --site all --location "Phoenix, AZ" --property-type multifamily --min-price 1000000
```

### Market Analysis

Collect data for a specific market:
```bash
python main.py --site all --location "Denver, CO" --max-results 200 --output denver_market_analysis.csv
```

### Property Comparison

Compare similar properties:
```bash
python main.py --site loopnet --location "Portland, OR" --property-type office --min-size 10000 --max-size 20000
```

---

For more information, see the [README.md](README.md) or visit the GitHub repository.
