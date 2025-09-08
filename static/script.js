// Blood Donation Management System - Enhanced JavaScript

document.addEventListener('DOMContentLoaded', function() {
    
    // Initialize tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Initialize popovers
    var popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    var popoverList = popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });

    // Enhanced form validation
    const forms = document.querySelectorAll('.needs-validation');
    Array.from(forms).forEach(form => {
        form.addEventListener('submit', event => {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            form.classList.add('was-validated');
        }, false);
    });

    // Auto-hide alerts after 5 seconds
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(alert => {
        setTimeout(() => {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        }, 5000);
    });

    // Enhanced search functionality
    const searchInputs = document.querySelectorAll('.search-input');
    searchInputs.forEach(input => {
        let searchTimeout;
        input.addEventListener('input', function() {
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(() => {
                performSearch(this.value, this.dataset.target);
            }, 300);
        });
    });

    // Delete confirmation
    const deleteButtons = document.querySelectorAll('.delete-btn');
    deleteButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            if (!confirm('Are you sure you want to delete this item? This action cannot be undone.')) {
                e.preventDefault();
            }
        });
    });

    // Table row highlighting
    const tableRows = document.querySelectorAll('tbody tr');
    tableRows.forEach(row => {
        row.addEventListener('click', function() {
            // Remove highlight from other rows
            tableRows.forEach(r => r.classList.remove('table-active'));
            // Add highlight to clicked row
            this.classList.add('table-active');
        });
    });

    // Blood group color coding
    const bloodGroupElements = document.querySelectorAll('.blood-group');
    bloodGroupElements.forEach(element => {
        const bloodGroup = element.textContent;
        element.className = 'blood-group badge ' + getBloodGroupClass(bloodGroup);
    });

    // Inventory status indicators
    updateInventoryStatus();

    // Real-time data updates
    if (document.querySelector('.dashboard-stats')) {
        setInterval(updateDashboardStats, 30000); // Update every 30 seconds
    }

    // Form enhancement - Auto-save draft
    const formInputs = document.querySelectorAll('form input, form select, form textarea');
    formInputs.forEach(input => {
        input.addEventListener('change', function() {
            saveFormDraft(this.closest('form'));
        });
    });

    // Load saved drafts
    loadFormDrafts();
});

// Search functionality
function performSearch(query, target) {
    if (query.length < 2) return;
    
    const searchResults = document.querySelectorAll(target);
    searchResults.forEach(result => {
        const text = result.textContent.toLowerCase();
        const isVisible = text.includes(query.toLowerCase());
        result.style.display = isVisible ? '' : 'none';
    });
}

// Blood group styling
function getBloodGroupClass(bloodGroup) {
    const bloodGroupClasses = {
        'A+': 'bg-danger',
        'A-': 'bg-danger',
        'B+': 'bg-primary',
        'B-': 'bg-primary',
        'AB+': 'bg-success',
        'AB-': 'bg-success',
        'O+': 'bg-warning',
        'O-': 'bg-warning'
    };
    return bloodGroupClasses[bloodGroup] || 'bg-secondary';
}

// Update inventory status
function updateInventoryStatus() {
    const inventoryItems = document.querySelectorAll('.inventory-item');
    inventoryItems.forEach(item => {
        const units = parseInt(item.dataset.units);
        if (units < 10) {
            item.classList.add('low');
        } else if (units < 20) {
            item.classList.add('medium');
        } else {
            item.classList.add('high');
        }
    });
}

// Dashboard stats update
function updateDashboardStats() {
    fetch('/api/stats')
        .then(response => response.json())
        .then(data => {
            updateStatDisplay('total-donors', data.total_donors);
            updateStatDisplay('total-recipients', data.total_recipients);
            updateStatDisplay('total-donations', data.total_donations);
            updateStatDisplay('total-requests', data.total_requests);
        })
        .catch(error => console.error('Error updating stats:', error));
}

function updateStatDisplay(elementId, value) {
    const element = document.getElementById(elementId);
    if (element) {
        element.textContent = value;
        // Add animation
        element.style.transform = 'scale(1.1)';
        setTimeout(() => {
            element.style.transform = 'scale(1)';
        }, 200);
    }
}

// Form draft functionality
function saveFormDraft(form) {
    const formData = new FormData(form);
    const draft = {};
    
    for (let [key, value] of formData.entries()) {
        draft[key] = value;
    }
    
    localStorage.setItem(`form_draft_${form.id || 'default'}`, JSON.stringify(draft));
}

function loadFormDrafts() {
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        const formId = form.id || 'default';
        const draft = localStorage.getItem(`form_draft_${formId}`);
        
        if (draft) {
            try {
                const draftData = JSON.parse(draft);
                Object.keys(draftData).forEach(key => {
                    const input = form.querySelector(`[name="${key}"]`);
                    if (input) {
                        input.value = draftData[key];
                    }
                });
                
                // Show draft loaded notification
                showNotification('Form draft loaded', 'info');
            } catch (error) {
                console.error('Error loading form draft:', error);
            }
        }
    });
}

// Clear form draft
function clearFormDraft(formId = 'default') {
    localStorage.removeItem(`form_draft_${formId}`);
    showNotification('Form draft cleared', 'success');
}

// Notification system
function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
    notification.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
    notification.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    document.body.appendChild(notification);
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
        if (notification.parentNode) {
            notification.remove();
        }
    }, 5000);
}

// Export functionality
function exportTableData(tableId, format = 'csv') {
    const table = document.getElementById(tableId);
    if (!table) return;
    
    let data = [];
    const headers = [];
    
    // Get headers
    table.querySelectorAll('thead th').forEach(th => {
        headers.push(th.textContent.trim());
    });
    
    // Get data
    table.querySelectorAll('tbody tr').forEach(row => {
        const rowData = [];
        row.querySelectorAll('td').forEach(cell => {
            rowData.push(cell.textContent.trim());
        });
        data.push(rowData);
    });
    
    if (format === 'csv') {
        exportToCSV(headers, data);
    } else if (format === 'json') {
        exportToJSON(headers, data);
    }
}

function exportToCSV(headers, data) {
    let csvContent = headers.join(',') + '\n';
    data.forEach(row => {
        csvContent += row.join(',') + '\n';
    });
    
    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'blood_donation_data.csv';
    a.click();
    window.URL.revokeObjectURL(url);
}

function exportToJSON(headers, data) {
    const jsonData = data.map(row => {
        const obj = {};
        headers.forEach((header, index) => {
            obj[header] = row[index];
        });
        return obj;
    });
    
    const blob = new Blob([JSON.stringify(jsonData, null, 2)], { type: 'application/json' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'blood_donation_data.json';
    a.click();
    window.URL.revokeObjectURL(url);
}

// Print functionality
function printPage() {
    window.print();
}

// Data validation helpers
function validateEmail(email) {
    const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return re.test(email);
}

function validatePhone(phone) {
    const re = /^[\+]?[1-9][\d]{0,15}$/;
    return re.test(phone.replace(/\s/g, ''));
}

function validateBloodGroup(bloodGroup) {
    const validGroups = ['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-'];
    return validGroups.includes(bloodGroup);
}

// Utility functions
function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
    });
}

function formatCurrency(amount) {
    return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD'
    }).format(amount);
}

// Chart.js integration (if available)
function createChart(canvasId, data, options = {}) {
    const canvas = document.getElementById(canvasId);
    if (!canvas) return null;
    
    const ctx = canvas.getContext('2d');
    
    // Default options
    const defaultOptions = {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            legend: {
                position: 'top',
            },
            title: {
                display: true,
                text: 'Blood Donation Statistics'
            }
        }
    };
    
    return new Chart(ctx, {
        type: 'bar',
        data: data,
        options: { ...defaultOptions, ...options }
    });
}

// Keyboard shortcuts
document.addEventListener('keydown', function(e) {
    // Ctrl/Cmd + S to save
    if ((e.ctrlKey || e.metaKey) && e.key === 's') {
        e.preventDefault();
        const activeForm = document.querySelector('form:focus-within');
        if (activeForm) {
            activeForm.dispatchEvent(new Event('submit'));
        }
    }
    
    // Ctrl/Cmd + F to focus search
    if ((e.ctrlKey || e.metaKey) && e.key === 'f') {
        e.preventDefault();
        const searchInput = document.querySelector('.search-input');
        if (searchInput) {
            searchInput.focus();
        }
    }
    
    // Escape to close modals
    if (e.key === 'Escape') {
        const modals = document.querySelectorAll('.modal.show');
        modals.forEach(modal => {
            const modalInstance = bootstrap.Modal.getInstance(modal);
            if (modalInstance) {
                modalInstance.hide();
            }
        });
    }
});

// Performance monitoring
const performanceObserver = new PerformanceObserver((list) => {
    for (const entry of list.getEntries()) {
        if (entry.entryType === 'navigation') {
            console.log('Page load time:', entry.loadEventEnd - entry.loadEventStart, 'ms');
        }
    }
});

performanceObserver.observe({ entryTypes: ['navigation'] });

// Service Worker registration (for PWA capabilities)
if ('serviceWorker' in navigator) {
    window.addEventListener('load', () => {
        navigator.serviceWorker.register('/sw.js')
            .then(registration => {
                console.log('SW registered: ', registration);
            })
            .catch(registrationError => {
                console.log('SW registration failed: ', registrationError);
            });
    });
}
