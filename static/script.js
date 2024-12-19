let networkChart;
let currentRefreshInterval;
let refreshTimer;
let isPageVisible = true;

// Handle page visibility changes
document.addEventListener('visibilitychange', function() {
    if (document.hidden) {
        isPageVisible = false;
        // Clear existing refresh timer when page is hidden
        if (refreshTimer) {
            clearInterval(refreshTimer);
            refreshTimer = null;
        }
    } else {
        isPageVisible = true;
        // Immediately refresh data when page becomes visible
        refreshData();
        // Restart the refresh timer
        setupRefreshInterval();
    }
});

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
    if (!isPageVisible) return;  // Don't update if page isn't visible
    networkChart.data.labels = data.map(item => item.timestamp);
    networkChart.data.datasets[0].data = data.map(item => item.value);
    networkChart.update();
}

function setupRefreshInterval() {
    const select = document.getElementById('refreshInterval');
    if (refreshTimer) {
        clearInterval(refreshTimer);
    }
    currentRefreshInterval = parseInt(select.value);
    if (isPageVisible) {  // Only start refresh timer if page is visible
        refreshTimer = setInterval(() => {
            if (isPageVisible) {  // Double-check visibility before refreshing
                refreshData();
            }
        }, currentRefreshInterval);
    }
}

function refreshData() {
    if (!isPageVisible) return;  // Don't refresh if page isn't visible
    
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
    if (!isPageVisible) return;  // Don't update if page isn't visible
    
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
    if (!isPageVisible) return;  // Don't update if page isn't visible
    
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