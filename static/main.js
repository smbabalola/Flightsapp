// API Configuration (declared in auth.js)
// const API_BASE is already declared in auth.js

// Initialize search form on index page
document.addEventListener('DOMContentLoaded', () => {
        const setCurrencyOptionLabels = (sel) => {
            const labels = { NGN: 'NGN (Ã¢â€šÂ¦)', USD: 'USD ($)', GBP: 'GBP (Ã‚Â£)', EUR: 'EUR (Ã¢â€šÂ¬)', ZAR: 'ZAR (R)' };
            Array.from(sel.options).forEach(o => { const v = String(o.value).toUpperCase(); if (labels[v]) { o.textContent = labels[v]; } });
        };
    // Set minimum date to today
    const today = new Date().toISOString().split('T')[0];
    const departDateInput = document.getElementById('departDate');
    const returnDateInput = document.getElementById('returnDate');

    if (departDateInput) {
        departDateInput.min = today;

        // Update return date minimum when depart date changes
        departDateInput.addEventListener('change', () => {
            if (returnDateInput) {
                returnDateInput.min = departDateInput.value;
            }
        });
    }

    if (returnDateInput) {
        returnDateInput.min = today;
    }

    // Handle trip type toggle
    const tripTypeInputs = document.querySelectorAll('input[name="tripType"]');
    const returnDateGroup = document.getElementById('returnDateGroup');

    tripTypeInputs.forEach(input => {
        input.addEventListener('change', (e) => {
            if (e.target.value === 'round-trip') {
                returnDateGroup.style.display = 'block';
                returnDateInput.required = true;
            } else {
                returnDateGroup.style.display = 'none';
                returnDateInput.required = false;
            }
        });
    });

    // Handle search form submission
    if (typeof initThemeToggle === 'function') {
        initThemeToggle();
    }

    const searchForm = document.getElementById('searchForm');
    if (searchForm) {
        searchForm.addEventListener('submit', handleSearchSubmit);
    }

    // Prefill navbar currency selector for guests using backend hint
    try {
        const navCurrency2 = document.getElementById('currencySelect');
        if (navCurrency2) {
            setCurrencyOptionLabels(navCurrency2);
            // non-blocking attempt to get backend default currency
            fetch(`${API_BASE}/v1/currency/default`).then(res => res.json()).then(j => {
                if (j && j.currency && !navCurrency2.value) navCurrency2.value = j.currency;
            }).catch(()=>{});
        }
    } catch (e) { console.error(e); }

    // end of DOMContentLoaded handler
});

// Handle search form submission
async function handleSearchSubmit(e) {
    e.preventDefault();

    const form = e.target;
    const loadingDiv = document.getElementById('loading');
    const errorDiv = document.getElementById('error');
    const submitButton = form.querySelector('button[type="submit"]');

    // Get form data
    const tripType = form.querySelector('input[name="tripType"]:checked').value;
    const from = document.getElementById('from').value;
    const to = document.getElementById('to').value;
    const departDate = document.getElementById('departDate').value;
    const returnDate = document.getElementById('returnDate').value;
    const adults = parseInt(document.getElementById('adults').value);
    const children = parseInt(document.getElementById('children').value);
    const infants = parseInt(document.getElementById('infants').value);
    const cabin = document.getElementById('cabin').value;

    // Build slices array
    const slices = [{
        from_: from,
        to: to,
        date: departDate
    }];

    if (tripType === 'round-trip' && returnDate) {
        slices.push({
            from_: to,
            to: from,
            date: returnDate
        });
    }

    const searchData = {
        slices,
        adults,
        children,
        infants
    };

    // Attach user display currency preference when available
    if (isLoggedIn()) {
        try {
            const prefRes = await authFetch('/v1/ops/preferences');
            if (prefRes.ok) {
                const prefs = await prefRes.json();
                if (prefs && prefs.preferred_currency) {
                    searchData.display_currency = prefs.preferred_currency;
                }
            }
        } catch {}
    }

    // Currency selection from navbar (non-persistent)
    try {
        const navCurrency = document.getElementById('currencySelect');
        if (navCurrency && navCurrency.value) {
            searchData.display_currency = navCurrency.value;
        } else if (!searchData.display_currency) {
            // Fallback to backend default
            try {
                const res = await fetch(`${API_BASE}/v1/currency/default`);
                if (res.ok) {
                    const j = await res.json();
                    if (j && j.currency) searchData.display_currency = j.currency;
                }
            } catch {}
        }
    } catch {}

    // Show loading
    loadingDiv.style.display = 'block';
    errorDiv.style.display = 'none';
    submitButton.disabled = true;

    try {
        const response = await fetch(`${API_BASE}/v1/search?page=1&page_size=10`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(searchData)
        });

        const data = await response.json();

        if (response.ok) {
            // Store search params and results
            sessionStorage.setItem('searchParams', JSON.stringify(searchData));
            sessionStorage.setItem('searchResults', JSON.stringify(data));

            // Redirect to results page
            window.location.href = 'results.html';
        } else {
            showError(errorDiv, data.detail || 'Search failed. Please try again.');
        }
    } catch (error) {
        console.error('Search error:', error);
        showError(errorDiv, 'Network error. Please check your connection and try again.');
    } finally {
        loadingDiv.style.display = 'none';
        submitButton.disabled = false;
    }
}

// Show error message
function showError(errorDiv, message) {
    errorDiv.textContent = message;
    errorDiv.style.display = 'block';
    window.scrollTo({ top: 0, behavior: 'smooth' });
}

// Format currency
function formatCurrency(amount, currency = 'NGN') {
    const value = Number(amount || 0);
    const curr = String(currency || 'USD').toUpperCase();
    const symbols = { NGN: '₦', USD: '$', GBP: '£', EUR: '€', ZAR: 'R', JPY: '¥', CNY: '¥', CAD: '$', AUD: '$' };
    const symbol = symbols[curr];
    if (symbol) {
        if (curr === 'NGN') return symbol + parseInt(value).toLocaleString();
        return symbol + value.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 });
    }
    return curr + ' ' + value.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

// Format date
function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
        weekday: 'short',
        year: 'numeric',
        month: 'short',
        day: 'numeric'
    });
}

// Format time
function formatTime(dateString) {
    const date = new Date(dateString);
    return date.toLocaleTimeString('en-US', {
        hour: '2-digit',
        minute: '2-digit'
    });
}

// Calculate flight duration
function calculateDuration(departTime, arriveTime) {
    const diff = new Date(arriveTime) - new Date(departTime);
    const hours = Math.floor(diff / (1000 * 60 * 60));
    const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));
    return `${hours}h ${minutes}m`;
}

// Helper to get query parameter
function getQueryParam(name) {
    const urlParams = new URLSearchParams(window.location.search);
    return urlParams.get(name);
}

// Inline Validation Utilities
function validateEmail(email) {
    const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return re.test(email);
}

function validatePhone(phone) {
    // International phone number format
    const re = /^\+?[1-9]\d{1,14}$/;
    return re.test(phone.replace(/[\s-]/g, ''));
}

function validatePassportNumber(passport) {
    // Basic passport validation (alphanumeric, 6-9 characters)
    return passport && passport.length >= 6 && passport.length <= 9;
}

function validateDate(dateString) {
    const date = new Date(dateString);
    return date instanceof Date && !isNaN(date) && date > new Date();
}

function validateRequired(value) {
    return value && value.trim() !== '';
}

function showFieldError(fieldElement, message) {
    const formGroup = fieldElement.closest('.form-group');
    if (!formGroup) return;

    // Remove any existing error/success states
    formGroup.classList.remove('has-success', 'has-error');
    formGroup.classList.add('has-error');

    // Find or create error message element
    let errorElement = formGroup.querySelector('.form-error');
    if (!errorElement) {
        errorElement = document.createElement('div');
        errorElement.className = 'form-error';
        fieldElement.parentNode.insertBefore(errorElement, fieldElement.nextSibling);
    }

    errorElement.textContent = message;
    fieldElement.setAttribute('aria-invalid', 'true');
}

function clearFieldError(fieldElement) {
    const formGroup = fieldElement.closest('.form-group');
    if (!formGroup) return;

    formGroup.classList.remove('has-error');
    formGroup.classList.add('has-success');

    const errorElement = formGroup.querySelector('.form-error');
    if (errorElement) {
        errorElement.textContent = '';
    }

    fieldElement.removeAttribute('aria-invalid');
}

function clearAllErrors(formElement) {
    const errorFields = formElement.querySelectorAll('.form-group.has-error, .form-group.has-success');
    errorFields.forEach(group => {
        group.classList.remove('has-error', 'has-success');
        const errorElement = group.querySelector('.form-error');
        if (errorElement) {
            errorElement.textContent = '';
        }
    });

    const invalidFields = formElement.querySelectorAll('[aria-invalid="true"]');
    invalidFields.forEach(field => {
        field.removeAttribute('aria-invalid');
    });
}

function validateField(fieldElement) {
    const value = fieldElement.value.trim();
    const type = fieldElement.type;
    const id = fieldElement.id;
    const required = fieldElement.required;

    // Clear previous error
    clearFieldError(fieldElement);

    // Check required fields
    if (required && !validateRequired(value)) {
        showFieldError(fieldElement, 'This field is required');
        return false;
    }

    // Skip validation if field is empty and not required
    if (!value && !required) {
        return true;
    }

    // Type-specific validation
    switch (type) {
        case 'email':
            if (!validateEmail(value)) {
                showFieldError(fieldElement, 'Please enter a valid email address');
                return false;
            }
            break;

        case 'tel':
            if (!validatePhone(value)) {
                showFieldError(fieldElement, 'Please enter a valid phone number (e.g., +2348012345678)');
                return false;
            }
            break;

        case 'date':
            const date = new Date(value);
            const today = new Date();
            today.setHours(0, 0, 0, 0);

            if (date < today) {
                showFieldError(fieldElement, 'Date must be in the future');
                return false;
            }
            break;
    }

    // Custom validations based on class or ID
    if (fieldElement.classList.contains('passenger-passport')) {
        if (!validatePassportNumber(value)) {
            showFieldError(fieldElement, 'Passport number must be 6-9 alphanumeric characters');
            return false;
        }
    }

    if (fieldElement.classList.contains('passenger-expiry')) {
        const expiryDate = new Date(value);
        const sixMonthsFromNow = new Date();
        sixMonthsFromNow.setMonth(sixMonthsFromNow.getMonth() + 6);

        if (expiryDate < sixMonthsFromNow) {
            showFieldError(fieldElement, 'Passport must be valid for at least 6 months');
            return false;
        }
    }

    return true;
}

function enableRealTimeValidation(formElement) {
    const inputs = formElement.querySelectorAll('input, select, textarea');

    inputs.forEach(input => {
        // Validate on blur (when field loses focus)
        input.addEventListener('blur', () => {
            validateField(input);
        });

        // Clear error on input (as user types)
        input.addEventListener('input', () => {
            if (input.closest('.form-group').classList.contains('has-error')) {
                clearFieldError(input);
            }
        });
    });
}

function validateForm(formElement) {
    clearAllErrors(formElement);

    const inputs = formElement.querySelectorAll('input[required], select[required], textarea[required]');
    let isValid = true;
    let firstInvalidField = null;

    inputs.forEach(input => {
        if (!validateField(input)) {
            isValid = false;
            if (!firstInvalidField) {
                firstInvalidField = input;
            }
        }
    });

    // Scroll to first error
    if (!isValid && firstInvalidField) {
        firstInvalidField.scrollIntoView({ behavior: 'smooth', block: 'center' });
        firstInvalidField.focus();
    }

    return isValid;
}

function formatCabinName(cabin) {
    const cabinMap = {
        'economy': 'Economy',
        'premium_economy': 'Premium Economy',
        'business': 'Business Class',
        'first': 'First Class'
    };
    return cabinMap[cabin] || cabin;
}

