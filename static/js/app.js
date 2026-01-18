// Global variables
let currentJobId = null;
let statusCheckInterval = null;

// DOM elements
const searchForm = document.getElementById('searchForm');
const submitBtn = document.getElementById('submitBtn');
const progressSection = document.getElementById('progressSection');
const progressStatus = document.getElementById('progressStatus');
const resultsSection = document.getElementById('resultsSection');
const resultsSummary = document.getElementById('resultsSummary');
const resultsBody = document.getElementById('resultsBody');
const downloadBtn = document.getElementById('downloadBtn');

// Event listeners
searchForm.addEventListener('submit', handleFormSubmit);
downloadBtn.addEventListener('click', handleDownload);

// Handle form submission
async function handleFormSubmit(e) {
    e.preventDefault();

    // Get form data
    const formData = {
        site: document.getElementById('site').value,
        location: document.getElementById('location').value,
        property_type: document.getElementById('property_type').value || null,
        min_price: document.getElementById('min_price').value || null,
        max_price: document.getElementById('max_price').value || null,
        min_size: document.getElementById('min_size').value || null,
        max_size: document.getElementById('max_size').value || null,
        max_results: document.getElementById('max_results').value || 50
    };

    // Validate
    if (!formData.site || !formData.location) {
        alert('Please fill in all required fields (Site and Location)');
        return;
    }

    // Disable form
    submitBtn.disabled = true;
    submitBtn.classList.add('btn-loading');

    // Hide results, show progress
    resultsSection.style.display = 'none';
    progressSection.style.display = 'block';
    progressStatus.textContent = 'Starting scraper...';

    try {
        // Start scraping job
        const response = await fetch('/api/scrape', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(formData)
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Failed to start scraping');
        }

        const data = await response.json();
        currentJobId = data.job_id;

        // Start checking status
        checkStatus();

    } catch (error) {
        showError('Error starting scraper: ' + error.message);
        resetForm();
    }
}

// Check scraping status
async function checkStatus() {
    if (!currentJobId) return;

    try {
        const response = await fetch(`/api/status/${currentJobId}`);
        const data = await response.json();

        // Update progress
        updateProgress(data);

        // Check if completed
        if (data.status === 'completed') {
            clearInterval(statusCheckInterval);
            loadResults();
        } else if (data.status === 'failed') {
            clearInterval(statusCheckInterval);
            showError('Scraping failed: ' + (data.error || 'Unknown error'));
            resetForm();
        } else {
            // Continue checking
            statusCheckInterval = setTimeout(checkStatus, 2000);
        }

    } catch (error) {
        clearInterval(statusCheckInterval);
        showError('Error checking status: ' + error.message);
        resetForm();
    }
}

// Update progress display
function updateProgress(data) {
    const status = data.status;
    const properties = data.properties || 0;

    let message = '';
    if (status === 'starting') {
        message = 'Starting scraper...';
    } else if (status.startsWith('scraping')) {
        const site = status.replace('scraping ', '');
        message = `Scraping ${site}... (${properties} properties found so far)`;
    } else if (status === 'exporting') {
        message = `Exporting results... (${properties} properties)`;
    } else {
        message = status;
    }

    progressStatus.textContent = message;
}

// Load and display results
async function loadResults() {
    if (!currentJobId) return;

    try {
        const response = await fetch(`/api/results/${currentJobId}`);
        const data = await response.json();

        if (data.properties && data.properties.length > 0) {
            displayResults(data.properties);

            // Show download button if CSV is available
            if (data.csv_path) {
                downloadBtn.style.display = 'inline-block';
            }
        } else {
            showError('No properties found. Try adjusting your search criteria.');
        }

    } catch (error) {
        showError('Error loading results: ' + error.message);
    } finally {
        progressSection.style.display = 'none';
        resetForm();
    }
}

// Display results in table
function displayResults(properties) {
    // Show results section
    resultsSection.style.display = 'block';

    // Update summary
    resultsSummary.innerHTML = `
        <p><strong>Total Properties Found:</strong> ${properties.length}</p>
        <p><strong>Sources:</strong> ${getUniqueSources(properties).join(', ')}</p>
    `;

    // Clear existing results
    resultsBody.innerHTML = '';

    // Add rows
    properties.forEach(prop => {
        const row = createResultRow(prop);
        resultsBody.appendChild(row);
    });

    // Scroll to results
    resultsSection.scrollIntoView({ behavior: 'smooth' });
}

// Create table row for a property
function createResultRow(prop) {
    const row = document.createElement('tr');

    row.innerHTML = `
        <td>${prop.title || 'N/A'}</td>
        <td>${formatLocation(prop)}</td>
        <td>${prop.property_type || 'N/A'}</td>
        <td>${formatPrice(prop.price)}</td>
        <td>${formatNumber(prop.building_size)}</td>
        <td>${formatPercentage(prop.cap_rate)}</td>
        <td>${prop.source_site || 'N/A'}</td>
        <td>${prop.url ? `<a href="${prop.url}" target="_blank">View</a>` : 'N/A'}</td>
    `;

    return row;
}

// Format location
function formatLocation(prop) {
    const parts = [];
    if (prop.city) parts.push(prop.city);
    if (prop.state) parts.push(prop.state);
    return parts.length > 0 ? parts.join(', ') : (prop.address || 'N/A');
}

// Format price
function formatPrice(price) {
    if (!price) return 'N/A';

    if (price >= 1000000) {
        return `$${(price / 1000000).toFixed(2)}M`;
    } else if (price >= 1000) {
        return `$${(price / 1000).toFixed(0)}K`;
    } else {
        return `$${price.toLocaleString()}`;
    }
}

// Format number
function formatNumber(num) {
    if (!num) return 'N/A';
    return num.toLocaleString();
}

// Format percentage
function formatPercentage(pct) {
    if (!pct) return 'N/A';
    return `${pct}%`;
}

// Get unique sources
function getUniqueSources(properties) {
    const sources = properties.map(p => p.source_site).filter(s => s);
    return [...new Set(sources)];
}

// Handle CSV download
function handleDownload() {
    if (!currentJobId) return;

    window.location.href = `/api/download/${currentJobId}`;
}

// Show error message
function showError(message) {
    // Remove existing alerts
    const existingAlerts = document.querySelectorAll('.alert');
    existingAlerts.forEach(alert => alert.remove());

    // Create alert
    const alert = document.createElement('div');
    alert.className = 'alert alert-error';
    alert.textContent = message;

    // Insert after header
    const header = document.querySelector('.header');
    header.insertAdjacentElement('afterend', alert);

    // Auto-remove after 10 seconds
    setTimeout(() => alert.remove(), 10000);
}

// Reset form state
function resetForm() {
    submitBtn.disabled = false;
    submitBtn.classList.remove('btn-loading');
}

// Format helpers
function formatCurrency(amount) {
    if (amount === null || amount === undefined) return 'N/A';
    return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD',
        minimumFractionDigits: 0,
        maximumFractionDigits: 0
    }).format(amount);
}

// Clear results
function clearResults() {
    resultsBody.innerHTML = '';
    resultsSummary.innerHTML = '';
    resultsSection.style.display = 'none';
    downloadBtn.style.display = 'none';
}

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    console.log('Commercial Real Estate Scraper initialized');
});
