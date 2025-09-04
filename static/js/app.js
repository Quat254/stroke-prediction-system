/**
 * Enhanced Stroke Prediction System - Main JavaScript File
 * Provides interactive functionality and enhanced user experience
 */

// Global variables
let currentUser = null;
let assessmentData = {};
let chartInstance = null;

// Initialize application when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
});

/**
 * Initialize the application
 */
function initializeApp() {
    console.log('🚀 Initializing Enhanced Stroke Prediction System');
    
    // Initialize components
    initializeNavigation();
    initializeFormValidation();
    initializeCharts();
    initializeAnimations();
    initializeAccessibility();
    
    // Load user data if available
    loadUserData();
    
    console.log('✅ Application initialized successfully');
}

/**
 * Initialize navigation functionality
 */
function initializeNavigation() {
    // Add active class to current page
    const currentPath = window.location.pathname;
    const navLinks = document.querySelectorAll('nav a');
    
    navLinks.forEach(link => {
        if (link.getAttribute('href') === currentPath) {
            link.classList.add('active');
        }
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
}

/**
 * Initialize form validation
 */
function initializeFormValidation() {
    const forms = document.querySelectorAll('form');
    
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            if (!validateForm(this)) {
                e.preventDefault();
                showAlert('Please fill in all required fields correctly.', 'warning');
            }
        });
        
        // Add real-time validation
        const inputs = form.querySelectorAll('input, select, textarea');
        inputs.forEach(input => {
            input.addEventListener('blur', function() {
                validateField(this);
            });
            
            input.addEventListener('input', function() {
                clearFieldError(this);
            });
        });
    });
}

/**
 * Validate a form
 */
function validateForm(form) {
    let isValid = true;
    const requiredFields = form.querySelectorAll('[required]');
    
    requiredFields.forEach(field => {
        if (!validateField(field)) {
            isValid = false;
        }
    });
    
    return isValid;
}

/**
 * Validate a single field
 */
function validateField(field) {
    const value = field.value.trim();
    const fieldType = field.type;
    const fieldName = field.name;
    
    // Clear previous errors
    clearFieldError(field);
    
    // Check if required field is empty
    if (field.hasAttribute('required') && !value) {
        showFieldError(field, 'This field is required');
        return false;
    }
    
    // Type-specific validation
    switch (fieldType) {
        case 'email':
            if (value && !isValidEmail(value)) {
                showFieldError(field, 'Please enter a valid email address');
                return false;
            }
            break;
            
        case 'number':
            const min = parseFloat(field.getAttribute('min'));
            const max = parseFloat(field.getAttribute('max'));
            const numValue = parseFloat(value);
            
            if (value && isNaN(numValue)) {
                showFieldError(field, 'Please enter a valid number');
                return false;
            }
            
            if (!isNaN(min) && numValue < min) {
                showFieldError(field, `Value must be at least ${min}`);
                return false;
            }
            
            if (!isNaN(max) && numValue > max) {
                showFieldError(field, `Value must be no more than ${max}`);
                return false;
            }
            break;
            
        case 'password':
            if (value && value.length < 6) {
                showFieldError(field, 'Password must be at least 6 characters long');
                return false;
            }
            break;
    }
    
    // Field-specific validation
    if (fieldName === 'age' && value) {
        const age = parseInt(value);
        if (age < 0 || age > 120) {
            showFieldError(field, 'Please enter a valid age (0-120)');
            return false;
        }
    }
    
    if (fieldName === 'bmi' && value) {
        const bmi = parseFloat(value);
        if (bmi < 10 || bmi > 60) {
            showFieldError(field, 'Please enter a valid BMI (10-60)');
            return false;
        }
    }
    
    if (fieldName === 'avg_glucose_level' && value) {
        const glucose = parseFloat(value);
        if (glucose < 50 || glucose > 500) {
            showFieldError(field, 'Please enter a valid glucose level (50-500 mg/dL)');
            return false;
        }
    }
    
    return true;
}

/**
 * Show field error
 */
function showFieldError(field, message) {
    field.classList.add('error');
    
    // Remove existing error message
    const existingError = field.parentNode.querySelector('.error-message');
    if (existingError) {
        existingError.remove();
    }
    
    // Add new error message
    const errorDiv = document.createElement('div');
    errorDiv.className = 'error-message';
    errorDiv.style.color = '#dc3545';
    errorDiv.style.fontSize = '12px';
    errorDiv.style.marginTop = '5px';
    errorDiv.textContent = message;
    
    field.parentNode.appendChild(errorDiv);
}

/**
 * Clear field error
 */
function clearFieldError(field) {
    field.classList.remove('error');
    const errorMessage = field.parentNode.querySelector('.error-message');
    if (errorMessage) {
        errorMessage.remove();
    }
}

/**
 * Check if email is valid
 */
function isValidEmail(email) {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
}

/**
 * Initialize charts and visualizations
 */
function initializeCharts() {
    // Initialize risk score chart if element exists
    const chartCanvas = document.getElementById('riskChart');
    if (chartCanvas) {
        initializeRiskChart();
    }
    
    // Initialize other charts as needed
    initializeProgressBars();
}

/**
 * Initialize risk score chart
 */
function initializeRiskChart() {
    console.log('📊 Initializing risk score chart');
    
    // Chart will be created by the dashboard template
    // This function can be extended for additional chart functionality
}

/**
 * Initialize progress bars
 */
function initializeProgressBars() {
    const progressBars = document.querySelectorAll('.progress-bar');
    
    progressBars.forEach(bar => {
        const fill = bar.querySelector('.progress-fill');
        const percentage = bar.getAttribute('data-percentage') || 0;
        
        // Animate progress bar
        setTimeout(() => {
            if (fill) {
                fill.style.width = percentage + '%';
            }
        }, 500);
    });
}

/**
 * Initialize animations
 */
function initializeAnimations() {
    // Intersection Observer for scroll animations
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };
    
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('animate-in');
            }
        });
    }, observerOptions);
    
    // Observe elements for animation
    document.querySelectorAll('.card, .risk-card, .stats-card').forEach(el => {
        observer.observe(el);
    });
}

/**
 * Initialize accessibility features
 */
function initializeAccessibility() {
    // Add keyboard navigation support
    document.addEventListener('keydown', function(e) {
        // Escape key to close modals/alerts
        if (e.key === 'Escape') {
            closeAllModals();
        }
        
        // Keyboard shortcuts
        if (e.ctrlKey || e.metaKey) {
            switch(e.key) {
                case 'h':
                    e.preventDefault();
                    window.location.href = '/history';
                    break;
                case 'n':
                    e.preventDefault();
                    window.location.href = '/assessment';
                    break;
                case 'd':
                    e.preventDefault();
                    window.location.href = '/dashboard';
                    break;
            }
        }
    });
    
    // Add focus indicators
    document.addEventListener('focusin', function(e) {
        e.target.classList.add('focused');
    });
    
    document.addEventListener('focusout', function(e) {
        e.target.classList.remove('focused');
    });
}

/**
 * Load user data
 */
function loadUserData() {
    // Check if user is logged in
    fetch('/get_user_info')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                currentUser = data;
                updateUserInterface();
            }
        })
        .catch(error => {
            console.log('User not logged in or error loading user data');
        });
}

/**
 * Update user interface based on user data
 */
function updateUserInterface() {
    if (currentUser) {
        // Update user-specific elements
        const userElements = document.querySelectorAll('[data-user-field]');
        userElements.forEach(element => {
            const field = element.getAttribute('data-user-field');
            if (currentUser[field]) {
                element.textContent = currentUser[field];
            }
        });
    }
}

/**
 * Show alert message
 */
function showAlert(message, type = 'info', duration = 5000) {
    // Remove existing alerts
    const existingAlerts = document.querySelectorAll('.alert-toast');
    existingAlerts.forEach(alert => alert.remove());
    
    // Create alert element
    const alert = document.createElement('div');
    alert.className = `alert alert-${type} alert-toast`;
    alert.style.position = 'fixed';
    alert.style.top = '20px';
    alert.style.right = '20px';
    alert.style.zIndex = '9999';
    alert.style.minWidth = '300px';
    alert.style.maxWidth = '500px';
    alert.style.borderRadius = '8px';
    alert.style.boxShadow = '0 4px 12px rgba(0, 0, 0, 0.15)';
    alert.style.transform = 'translateX(100%)';
    alert.style.transition = 'transform 0.3s ease';
    
    // Add icon based on type
    const icons = {
        success: '✅',
        warning: '⚠️',
        danger: '❌',
        info: 'ℹ️'
    };
    
    alert.innerHTML = `
        <div style="display: flex; align-items: center; gap: 10px;">
            <span style="font-size: 18px;">${icons[type] || icons.info}</span>
            <span>${message}</span>
            <button onclick="this.parentElement.parentElement.remove()" style="background: none; border: none; font-size: 18px; cursor: pointer; margin-left: auto;">×</button>
        </div>
    `;
    
    document.body.appendChild(alert);
    
    // Animate in
    setTimeout(() => {
        alert.style.transform = 'translateX(0)';
    }, 100);
    
    // Auto remove after duration
    if (duration > 0) {
        setTimeout(() => {
            alert.style.transform = 'translateX(100%)';
            setTimeout(() => {
                if (alert.parentNode) {
                    alert.remove();
                }
            }, 300);
        }, duration);
    }
}

/**
 * Close all modals
 */
function closeAllModals() {
    const modals = document.querySelectorAll('.modal, .alert-toast');
    modals.forEach(modal => {
        modal.remove();
    });
}

/**
 * Format number with commas
 */
function formatNumber(num) {
    return num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ',');
}

/**
 * Format date
 */
function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
    });
}

/**
 * Debounce function
 */
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

/**
 * Throttle function
 */
function throttle(func, limit) {
    let inThrottle;
    return function() {
        const args = arguments;
        const context = this;
        if (!inThrottle) {
            func.apply(context, args);
            inThrottle = true;
            setTimeout(() => inThrottle = false, limit);
        }
    };
}

/**
 * Copy text to clipboard
 */
function copyToClipboard(text) {
    if (navigator.clipboard) {
        navigator.clipboard.writeText(text).then(() => {
            showAlert('Copied to clipboard!', 'success', 2000);
        });
    } else {
        // Fallback for older browsers
        const textArea = document.createElement('textarea');
        textArea.value = text;
        document.body.appendChild(textArea);
        textArea.select();
        document.execCommand('copy');
        document.body.removeChild(textArea);
        showAlert('Copied to clipboard!', 'success', 2000);
    }
}

/**
 * Download data as JSON
 */
function downloadJSON(data, filename) {
    const blob = new Blob([JSON.stringify(data, null, 2)], {
        type: 'application/json'
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
}

/**
 * Print element
 */
function printElement(elementId) {
    const element = document.getElementById(elementId);
    if (element) {
        const printWindow = window.open('', '_blank');
        printWindow.document.write(`
            <html>
                <head>
                    <title>Print</title>
                    <link rel="stylesheet" href="/static/css/style.css">
                    <style>
                        body { margin: 20px; }
                        .no-print { display: none !important; }
                    </style>
                </head>
                <body>
                    ${element.outerHTML}
                </body>
            </html>
        `);
        printWindow.document.close();
        printWindow.print();
    }
}

/**
 * Check if device is mobile
 */
function isMobile() {
    return window.innerWidth <= 768;
}

/**
 * Get risk level color
 */
function getRiskLevelColor(level) {
    const colors = {
        'Very Low': '#28a745',
        'Low': '#17a2b8',
        'Moderate': '#ffc107',
        'High': '#fd7e14',
        'Very High': '#dc3545',
        'Critical': '#6f42c1'
    };
    return colors[level] || '#6c757d';
}

/**
 * Animate number counting
 */
function animateNumber(element, start, end, duration = 1000) {
    const startTime = performance.now();
    const difference = end - start;
    
    function updateNumber(currentTime) {
        const elapsed = currentTime - startTime;
        const progress = Math.min(elapsed / duration, 1);
        
        // Easing function
        const easeOutQuart = 1 - Math.pow(1 - progress, 4);
        const currentValue = start + (difference * easeOutQuart);
        
        if (element) {
            element.textContent = Math.round(currentValue);
        }
        
        if (progress < 1) {
            requestAnimationFrame(updateNumber);
        }
    }
    
    requestAnimationFrame(updateNumber);
}

// Export functions for global use
window.StrokePredictionApp = {
    showAlert,
    formatNumber,
    formatDate,
    copyToClipboard,
    downloadJSON,
    printElement,
    isMobile,
    getRiskLevelColor,
    animateNumber
};

console.log('📱 Enhanced Stroke Prediction System JavaScript loaded successfully');
