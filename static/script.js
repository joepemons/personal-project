let networkChart;
let currentRefreshInterval;
let refreshTimer;

document.addEventListener('DOMContentLoaded', function() {
    initializeChart();
    setupRefreshInterval();
    refreshData();
});

function initializeChart() {
    const ctx = document.getElementById('networkSpeedChart').getContext('2d');
    networkChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: [],
            datasets: [{
                label: 'Network Speed (KB/s)',
                data: [],
                borderColor: '#2196F3',
                tension: 0.4,
                fill: false
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: true
                }
            }
        }
    });
}

function updateChart(data) {
    networkChart.data.labels = data.map(item => item.timestamp);
    networkChart.data.datasets[0].data = data.map(item => item.value);
    networkChart.update();
}

function setupRefreshInterval() {
    const select = document.getElementById('refreshInterval');
    select.addEventListener('change', function() {
        if (refreshTimer) {
            clearInterval(refreshTimer);
        }
        currentRefreshInterval = parseInt(this.value);
        refreshTimer = setInterval(refreshData, currentRefreshInterval);
    });
    
    // Initialize with default value
    currentRefreshInterval = parseInt(select.value);
    refreshTimer = setInterval(refreshData, currentRefreshInterval);
}

function refreshData() {
    // Fetch metrics
    fetch('/get_current_metrics')
        .then(response => response.json())
        .then(updateMetrics)
        .catch(error => console.error('Error fetching metrics:', error));

    // Fetch network history
    fetch('/api/network-history')
        .then(response => response.json())
        .then(updateChart)
        .catch(error => console.error('Error fetching network history:', error));
}

function updateMetrics(data) {
    for (const [key, value] of Object.entries(data)) {
        const elements = document.querySelectorAll(`[data-metric="${key}"]`);
        elements.forEach(element => {
            if (element.classList.contains('value')) {
                element.textContent = `${value.state}${value.unit}`;
            } else if (element.classList.contains('timestamp')) {
                element.textContent = `Last Updated: ${value.last_updated}`;
            }
        });
    }

    // Update interface status indicators
    updateInterfaceStatus(data);
}

function updateInterfaceStatus(data) {
    const interfaces = ['lan', 'wan', 'opt1', 'opt2', 'opt3', 'opt4'];
    interfaces.forEach(iface => {
        const status = data[`${iface}_status`].state;
        const indicator = document.querySelector(`#${iface}-status`);
        if (indicator) {
            indicator.className = `status-indicator ${status === 'up' ? 'status-up' : 'status-down'}`;
        }
    });
}

function toggleService(service) {
    fetch(`/api/toggle/${service}`, {
        method: 'POST'
    })
    .then(response => response.json())
    .then(data => {
        const messageDiv = document.getElementById('serviceMessage');
        messageDiv.textContent = data.message;
        messageDiv.className = data.success ? 'success' : 'error';
        messageDiv.style.display = 'block';
        
        setTimeout(() => {
            messageDiv.style.display = 'none';
        }, 3000);
    })
    .catch(error => {
        console.error('Error:', error);
        const messageDiv = document.getElementById('serviceMessage');
        messageDiv.textContent = 'Error communicating with server';
        messageDiv.className = 'error';
        messageDiv.style.display = 'block';
    });
}

// Add data-metric attributes to HTML elements
document.addEventListener('DOMContentLoaded', function() {
    const metricElements = document.querySelectorAll('.value, .timestamp');
    metricElements.forEach(element => {
        const card = element.closest('.data-card');
        if (card) {
            const title = card.querySelector('h2').textContent.toLowerCase().replace(/\s+/g, '_');
            element.setAttribute('data-metric', title);
        }
    });
});