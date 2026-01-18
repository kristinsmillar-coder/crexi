#!/usr/bin/env python3
"""Flask web application for commercial real estate scraper."""

import os
import json
import threading
from datetime import datetime
from flask import Flask, render_template, request, jsonify, send_file
from werkzeug.utils import secure_filename

from scrapers.models import Property, SearchCriteria
from scrapers.loopnet import LoopNetScraper
from scrapers.crexi import CrexiScraper
from utils.csv_export import export_to_csv
from utils.helpers import load_config, setup_logging

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here-change-in-production'
app.config['OUTPUT_FOLDER'] = 'output'

# Store active scraping jobs
active_jobs = {}

SUPPORTED_SITES = {
    'loopnet': LoopNetScraper,
    'crexi': CrexiScraper,
}

# Setup logging
setup_logging('INFO')


@app.route('/')
def index():
    """Render the main page."""
    return render_template('index.html')


@app.route('/api/scrape', methods=['POST'])
def scrape():
    """Start a scraping job."""
    data = request.get_json()

    # Validate input
    if not data.get('location'):
        return jsonify({'error': 'Location is required'}), 400

    if not data.get('site'):
        return jsonify({'error': 'Site selection is required'}), 400

    # Create search criteria
    criteria = SearchCriteria(
        location=data['location'],
        property_type=data.get('property_type'),
        min_price=float(data['min_price']) if data.get('min_price') else None,
        max_price=float(data['max_price']) if data.get('max_price') else None,
        min_size=float(data['min_size']) if data.get('min_size') else None,
        max_size=float(data['max_size']) if data.get('max_size') else None,
        max_results=int(data.get('max_results', 50))
    )

    # Generate job ID
    job_id = f"job_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    # Initialize job status
    active_jobs[job_id] = {
        'status': 'starting',
        'progress': 0,
        'total': 0,
        'properties': [],
        'error': None,
        'csv_path': None
    }

    # Determine which sites to scrape
    site_selection = data['site']
    if site_selection == 'all':
        sites_to_scrape = list(SUPPORTED_SITES.items())
    else:
        sites_to_scrape = [(site_selection, SUPPORTED_SITES[site_selection])]

    # Start scraping in background thread
    thread = threading.Thread(
        target=run_scraping_job,
        args=(job_id, sites_to_scrape, criteria)
    )
    thread.daemon = True
    thread.start()

    return jsonify({'job_id': job_id})


@app.route('/api/status/<job_id>', methods=['GET'])
def get_status(job_id):
    """Get status of a scraping job."""
    if job_id not in active_jobs:
        return jsonify({'error': 'Job not found'}), 404

    job = active_jobs[job_id]

    return jsonify({
        'status': job['status'],
        'progress': job['progress'],
        'total': job['total'],
        'properties': len(job['properties']),
        'error': job['error'],
        'csv_path': job['csv_path']
    })


@app.route('/api/results/<job_id>', methods=['GET'])
def get_results(job_id):
    """Get results of a scraping job."""
    if job_id not in active_jobs:
        return jsonify({'error': 'Job not found'}), 404

    job = active_jobs[job_id]

    # Convert properties to dictionaries
    properties_data = [prop.to_dict() for prop in job['properties']]

    return jsonify({
        'status': job['status'],
        'properties': properties_data,
        'total': len(properties_data),
        'csv_path': job['csv_path']
    })


@app.route('/api/download/<job_id>', methods=['GET'])
def download_csv(job_id):
    """Download CSV file for a job."""
    if job_id not in active_jobs:
        return jsonify({'error': 'Job not found'}), 404

    job = active_jobs[job_id]

    if not job['csv_path'] or not os.path.exists(job['csv_path']):
        return jsonify({'error': 'CSV file not available'}), 404

    return send_file(
        job['csv_path'],
        as_attachment=True,
        download_name=os.path.basename(job['csv_path']),
        mimetype='text/csv'
    )


def run_scraping_job(job_id, sites_to_scrape, criteria):
    """Run the scraping job in background."""
    config = load_config()

    try:
        active_jobs[job_id]['status'] = 'running'
        all_properties = []

        for site_name, scraper_class in sites_to_scrape:
            try:
                active_jobs[job_id]['status'] = f'scraping {site_name}'

                scraper = scraper_class(
                    rate_limit=config['rate_limit'],
                    timeout=config['request_timeout']
                )

                properties = scraper.scrape(criteria)
                all_properties.extend(properties)

                active_jobs[job_id]['properties'] = all_properties
                active_jobs[job_id]['total'] = len(all_properties)

                scraper.close()

            except Exception as e:
                app.logger.error(f"Error scraping {site_name}: {e}")
                continue

        if all_properties:
            # Export to CSV
            active_jobs[job_id]['status'] = 'exporting'
            csv_path = export_to_csv(
                all_properties,
                os.path.join(app.config['OUTPUT_FOLDER'], f'{job_id}.csv')
            )
            active_jobs[job_id]['csv_path'] = csv_path
            active_jobs[job_id]['status'] = 'completed'
        else:
            active_jobs[job_id]['status'] = 'completed'
            active_jobs[job_id]['error'] = 'No properties found'

    except Exception as e:
        active_jobs[job_id]['status'] = 'failed'
        active_jobs[job_id]['error'] = str(e)
        app.logger.error(f"Job {job_id} failed: {e}", exc_info=True)


if __name__ == '__main__':
    # Create output directory
    os.makedirs(app.config['OUTPUT_FOLDER'], exist_ok=True)

    # Run the app
    print("\n" + "=" * 60)
    print("🏢 COMMERCIAL REAL ESTATE SCRAPER WEB APP")
    print("=" * 60)
    print("\n✅ Server is running!")
    print("\n🌐 Open your browser and go to:")
    print("\n   http://localhost:5000")
    print("\n📝 To stop the server, press CTRL+C")
    print("\n" + "=" * 60 + "\n")

    app.run(debug=True, host='0.0.0.0', port=5000)
