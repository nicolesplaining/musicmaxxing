// Last.fm Music Analytics - JavaScript utilities

// Global app state
const AppState = {
    currentUser: null,
    currentData: null,
    charts: {}
};

// Utility functions
const Utils = {
    // Format numbers with commas
    formatNumber: (num) => {
        return num.toLocaleString();
    },
    
    // Format percentage
    formatPercentage: (num, decimals = 1) => {
        return (num * 100).toFixed(decimals) + '%';
    },
    
    // Format date
    formatDate: (dateString) => {
        const date = new Date(dateString);
        return date.toLocaleDateString('en-US', {
            year: 'numeric',
            month: 'short',
            day: 'numeric'
        });
    },
    
    // Format date and time
    formatDateTime: (dateString) => {
        const date = new Date(dateString);
        return date.toLocaleString('en-US', {
            year: 'numeric',
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    },
    
    // Debounce function
    debounce: (func, wait) => {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    },
    
    // Show loading state
    showLoading: (elementId) => {
        const element = document.getElementById(elementId);
        if (element) {
            element.style.display = 'block';
        }
    },
    
    // Hide loading state
    hideLoading: (elementId) => {
        const element = document.getElementById(elementId);
        if (element) {
            element.style.display = 'none';
        }
    },
    
    // Show error message
    showError: (message, elementId = 'errorMessage') => {
        const errorElement = document.getElementById(elementId);
        const errorTextElement = document.getElementById('errorText');
        
        if (errorElement && errorTextElement) {
            errorTextElement.textContent = message;
            errorElement.style.display = 'block';
        } else {
            alert(message);
        }
    },
    
    // Hide error message
    hideError: (elementId = 'errorMessage') => {
        const errorElement = document.getElementById(elementId);
        if (errorElement) {
            errorElement.style.display = 'none';
        }
    },
    
    // Make API request with error handling
    apiRequest: async (url, options = {}) => {
        try {
            const response = await fetch(url, {
                headers: {
                    'Content-Type': 'application/json',
                    ...options.headers
                },
                ...options
            });
            
            const data = await response.json();
            
            if (!response.ok) {
                throw new Error(data.error || `HTTP ${response.status}`);
            }
            
            return data;
        } catch (error) {
            console.error('API request failed:', error);
            throw error;
        }
    }
};

// Chart utilities
const ChartUtils = {
    // Default chart colors
    colors: [
        '#1db954', '#1ed760', '#ff6b6b', '#4ecdc4', '#45b7d1',
        '#96ceb4', '#feca57', '#ff9ff3', '#54a0ff', '#5f27cd'
    ],
    
    // Create bar chart
    createBarChart: (canvasId, data, options = {}) => {
        const ctx = document.getElementById(canvasId);
        if (!ctx) return null;
        
        const defaultOptions = {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: true,
                    grid: {
                        color: 'rgba(0,0,0,0.1)'
                    }
                },
                x: {
                    grid: {
                        color: 'rgba(0,0,0,0.1)'
                    }
                }
            },
            plugins: {
                legend: {
                    display: false
                }
            }
        };
        
        return new Chart(ctx, {
            type: 'bar',
            data: {
                labels: data.labels,
                datasets: [{
                    label: data.label || 'Data',
                    data: data.values,
                    backgroundColor: data.colors || ChartUtils.colors[0],
                    borderColor: data.borderColor || ChartUtils.colors[0],
                    borderWidth: 1
                }]
            },
            options: { ...defaultOptions, ...options }
        });
    },
    
    // Create doughnut chart
    createDoughnutChart: (canvasId, data, options = {}) => {
        const ctx = document.getElementById(canvasId);
        if (!ctx) return null;
        
        const defaultOptions = {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: {
                        padding: 20,
                        usePointStyle: true
                    }
                }
            }
        };
        
        return new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: data.labels,
                datasets: [{
                    data: data.values,
                    backgroundColor: data.colors || ChartUtils.colors,
                    borderWidth: 2,
                    borderColor: '#fff'
                }]
            },
            options: { ...defaultOptions, ...options }
        });
    },
    
    // Create line chart
    createLineChart: (canvasId, data, options = {}) => {
        const ctx = document.getElementById(canvasId);
        if (!ctx) return null;
        
        const defaultOptions = {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: true,
                    grid: {
                        color: 'rgba(0,0,0,0.1)'
                    }
                },
                x: {
                    grid: {
                        color: 'rgba(0,0,0,0.1)'
                    }
                }
            },
            plugins: {
                legend: {
                    display: true
                }
            }
        };
        
        return new Chart(ctx, {
            type: 'line',
            data: {
                labels: data.labels,
                datasets: data.datasets.map((dataset, index) => ({
                    ...dataset,
                    backgroundColor: dataset.backgroundColor || ChartUtils.colors[index % ChartUtils.colors.length],
                    borderColor: dataset.borderColor || ChartUtils.colors[index % ChartUtils.colors.length],
                    borderWidth: 2,
                    fill: false,
                    tension: 0.4
                }))
            },
            options: { ...defaultOptions, ...options }
        });
    },
    
    // Destroy chart
    destroyChart: (chart) => {
        if (chart) {
            chart.destroy();
        }
    }
};

// Search functionality
const SearchUtils = {
    // Highlight search terms in text
    highlightSearchTerm: (text, searchTerm) => {
        if (!searchTerm) return text;
        
        const regex = new RegExp(`(${searchTerm})`, 'gi');
        return text.replace(regex, '<mark>$1</mark>');
    },
    
    // Create search suggestions
    createSuggestions: (containerId, suggestions) => {
        const container = document.getElementById(containerId);
        if (!container) return;
        
        container.innerHTML = '';
        
        suggestions.forEach(suggestion => {
            const item = document.createElement('div');
            item.className = 'suggestion-item p-2 border-bottom';
            item.style.cursor = 'pointer';
            item.textContent = suggestion;
            
            item.addEventListener('click', () => {
                const searchInput = document.getElementById('searchQuery');
                if (searchInput) {
                    searchInput.value = suggestion;
                    searchInput.dispatchEvent(new Event('input'));
                }
            });
            
            container.appendChild(item);
        });
    }
};

// Data visualization helpers
const DataViz = {
    // Create progress bar
    createProgressBar: (value, max, label) => {
        const percentage = (value / max) * 100;
        return `
            <div class="progress mb-2" style="height: 20px;">
                <div class="progress-bar" role="progressbar" 
                     style="width: ${percentage}%" 
                     aria-valuenow="${value}" 
                     aria-valuemin="0" 
                     aria-valuemax="${max}">
                    ${label}: ${Utils.formatNumber(value)}
                </div>
            </div>
        `;
    },
    
    // Create stats card
    createStatsCard: (title, value, icon, color = 'primary') => {
        return `
            <div class="col-md-3 mb-3">
                <div class="card border-0 shadow-sm bg-${color} text-white">
                    <div class="card-body text-center">
                        <i class="${icon} fa-2x mb-2"></i>
                        <h3 class="mb-0">${Utils.formatNumber(value)}</h3>
                        <small>${title}</small>
                    </div>
                </div>
            </div>
        `;
    },
    
    // Create list item
    createListItem: (title, subtitle, value, badge = null) => {
        return `
            <div class="list-group-item d-flex justify-content-between align-items-center">
                <div>
                    <div class="fw-bold">${title}</div>
                    <small class="text-muted">${subtitle}</small>
                </div>
                <div class="text-end">
                    ${badge ? `<span class="badge bg-primary rounded-pill me-2">${badge}</span>` : ''}
                    <span class="text-muted">${value}</span>
                </div>
            </div>
        `;
    }
};

// Initialize app when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    // Add fade-in animation to cards
    const cards = document.querySelectorAll('.card');
    cards.forEach((card, index) => {
        card.style.animationDelay = `${index * 0.1}s`;
        card.classList.add('fade-in');
    });
    
    // Add smooth scrolling to anchor links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });
    
    // Add tooltips to elements with data-bs-toggle="tooltip"
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
});

// Export utilities for global use
window.Utils = Utils;
window.ChartUtils = ChartUtils;
window.SearchUtils = SearchUtils;
window.DataViz = DataViz;
window.AppState = AppState;
