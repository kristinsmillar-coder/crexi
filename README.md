# Commercial Real Estate Scraper

A flexible, multi-site web scraper for commercial real estate listings. Extract property data from multiple platforms including LoopNet, Crexi, and more.

## 🚀 Two Ways to Use

### 🌐 Web App (No Coding Required!)
Use the beautiful web interface - just click buttons and fill in forms!

**Quick Start:**
```bash
# Mac/Linux
./start_webapp.sh

# Windows
start_webapp.bat
```

Then open http://localhost:5000 in your browser.

👉 **See [WEB_APP_GUIDE.md](WEB_APP_GUIDE.md) for detailed web app instructions**

### 💻 Command Line (For Developers)
Use the CLI for automation and scripting.

```bash
python main.py --site loopnet --location "New York, NY" --property-type office
```

👉 **See [USAGE_GUIDE.md](USAGE_GUIDE.md) for detailed CLI instructions**

## Features

- **Multi-site support**: Scrape from LoopNet, Crexi, and other commercial real estate platforms
- **Comprehensive data extraction**:
  - Basic info (property type, address, price, size, description)
  - Financial details (cap rate, NOI, price per sq ft, operating expenses)
  - Property features (amenities, year built, parking, zoning)
  - Contact information (broker/agent details)
- **CSV export**: Easy-to-use CSV output format
- **Rate limiting**: Respectful scraping with configurable delays
- **Error handling**: Robust retry logic and error recovery
- **Configurable**: Environment-based configuration

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd crexi
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up configuration:
```bash
cp .env.example .env
# Edit .env with your preferences
```

## Usage

### Basic Usage

Scrape LoopNet listings:
```bash
python main.py --site loopnet --location "New York, NY" --property-type office
```

Scrape Crexi listings:
```bash
python main.py --site crexi --location "Los Angeles, CA" --property-type retail
```

### Advanced Usage

Scrape multiple sites:
```bash
python main.py --site all --location "Chicago, IL" --max-results 100
```

Specify output file:
```bash
python main.py --site loopnet --location "Austin, TX" --output my_listings.csv
```

### Command-line Options

- `--site`: Target site (loopnet, crexi, all)
- `--location`: Search location (city, state or zip code)
- `--property-type`: Property type (office, retail, industrial, multifamily, land, etc.)
- `--min-price`: Minimum price
- `--max-price`: Maximum price
- `--max-results`: Maximum number of results to scrape
- `--output`: Output CSV file path

## Project Structure

```
crexi/
├── scrapers/
│   ├── __init__.py
│   ├── base.py          # Base scraper class
│   ├── loopnet.py       # LoopNet scraper
│   ├── crexi.py         # Crexi scraper
│   └── models.py        # Data models
├── utils/
│   ├── __init__.py
│   ├── csv_export.py    # CSV export functionality
│   └── helpers.py       # Helper functions
├── main.py              # Main CLI script
├── requirements.txt     # Python dependencies
├── .env.example         # Example configuration
└── README.md           # This file
```

## Legal and Ethical Considerations

- Always respect robots.txt and terms of service
- Use reasonable rate limiting to avoid overwhelming servers
- Only scrape publicly available data
- Be aware of and comply with data protection regulations (GDPR, CCPA, etc.)
- This tool is for educational and research purposes

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

MIT License - see LICENSE file for details
