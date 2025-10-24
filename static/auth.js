// Theme helpers
function applyTheme(theme) {
    const body = document.body;
    body.classList.remove('theme-light', 'theme-dark');
    body.classList.add(theme === 'dark' ? 'theme-dark' : 'theme-light');
}

function initThemeToggle() {
    const toggle = document.getElementById('themeToggle');
    const saved = localStorage.getItem('theme') || 'light';
    applyTheme(saved);
    if (toggle) {
        toggle.textContent = saved === 'dark' ? 'Light Mode' : 'Dark Mode';
        toggle.addEventListener('click', () => {
            const next = document.body.classList.contains('theme-dark') ? 'light' : 'dark';
            applyTheme(next);
            localStorage.setItem('theme', next);
            toggle.textContent = next === 'dark' ? 'Light Mode' : 'Dark Mode';
        });
    }
}

// API base: use relative paths to avoid port/origin mismatches
const API_BASE = '';
const REFRESH_TOKEN_KEY = 'refreshToken';
const TENANT_CONTEXT_KEY = 'tenantContext';

function isLoggedIn() {
    return localStorage.getItem('authToken') !== null;
}

function getCurrentUser() {
    const value = localStorage.getItem('currentUser');
    return value ? JSON.parse(value) : null;
}

function getAuthToken() {
    return localStorage.getItem('authToken');
}

function getRefreshToken() {
    return localStorage.getItem(REFRESH_TOKEN_KEY);
}

function getTenantContext() {
    const value = localStorage.getItem(TENANT_CONTEXT_KEY);
    return value ? JSON.parse(value) : null;
}

function setTenantContext(context) {
    if (context && Object.keys(context).length) {
        localStorage.setItem(TENANT_CONTEXT_KEY, JSON.stringify(context));
    } else {
        localStorage.removeItem(TENANT_CONTEXT_KEY);
    }
}

function setAuthData(accessToken, user, tenantContext = null, refreshToken = null) {
    localStorage.setItem('authToken', accessToken);
    localStorage.setItem('currentUser', JSON.stringify(user));
    if (refreshToken) {
        localStorage.setItem(REFRESH_TOKEN_KEY, refreshToken);
    } else {
        localStorage.removeItem(REFRESH_TOKEN_KEY);
    }
    setTenantContext(tenantContext || null);
    updateNavigation();
}

function clearAuthData() {
    localStorage.removeItem('authToken');
    localStorage.removeItem('currentUser');
    localStorage.removeItem(REFRESH_TOKEN_KEY);
    localStorage.removeItem(TENANT_CONTEXT_KEY);
    updateNavigation();
}

function updateNavigation() {
    const loggedIn = isLoggedIn();
    const user = getCurrentUser();
    const tenant = getTenantContext();
    const hasTenant = tenant && tenant.company_id;

    const loginLink = document.getElementById('loginLink');
    const signupLink = document.getElementById('signupLink');
    const logoutLink = document.getElementById('logoutLink');
    const dashboardLink = document.getElementById('dashboardLink');
    const partnerLink = document.getElementById('partnerLink');
    const partnerDashboardLink = document.getElementById('partnerDashboardLink');

    if (loginLink) loginLink.style.display = loggedIn ? 'none' : 'inline';
    if (signupLink) signupLink.style.display = loggedIn ? 'none' : 'inline';
    if (logoutLink) logoutLink.style.display = loggedIn ? 'inline' : 'none';
    if (dashboardLink) dashboardLink.style.display = loggedIn ? 'inline' : 'none';
    if (partnerLink) partnerLink.style.display = hasTenant ? 'none' : 'inline';
    if (partnerDashboardLink) partnerDashboardLink.style.display = loggedIn && hasTenant ? 'inline' : 'none';

    const footerLogin = document.getElementById('footerLogin');
    const footerSignup = document.getElementById('footerSignup');
    const footerDashboard = document.getElementById('footerDashboard');
    const footerPartner = document.getElementById('footerPartner');

    if (footerLogin) footerLogin.style.display = loggedIn ? 'none' : 'block';
    if (footerSignup) footerSignup.style.display = loggedIn ? 'none' : 'block';
    if (footerDashboard) footerDashboard.style.display = loggedIn ? 'block' : 'none';
    if (footerPartner) footerPartner.style.display = hasTenant ? 'none' : 'block';

    const userGreeting = document.getElementById('userGreeting');
    if (userGreeting) {
        userGreeting.textContent = user ? `Welcome, ${user.email}!` : '';
    }
}

async function login(email, password, options = {}) {
    try {
        const payload = { email, password };
        if (options.companyId) payload.company_id = options.companyId;
        if (options.companySlug) payload.company_slug = options.companySlug;

        const response = await fetch(`${API_BASE}/auth/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        const data = await response.json();

        if (response.ok) {
            const tenantContext = {
                company_id: data.company_id || null,
                company_user_id: data.company_user_id || null,
                company_role: data.company_role || null,
                available_companies: data.available_companies || []
            };

            const needsSelection = !tenantContext.company_id && tenantContext.available_companies.length > 0 && !options.companyId && !options.companySlug;
            if (needsSelection) {
                return {
                    success: false,
                    needsCompanySelection: true,
                    available_companies: tenantContext.available_companies
                };
            }

            setAuthData(
                data.access_token,
                { email, id: data.user_id },
                tenantContext,
                data.refresh_token
            );
            return { success: true, tenantContext };
        }

        return { success: false, error: data.detail || 'Login failed', available_companies: data.available_companies || [] };
    } catch (error) {
        console.error('Login error:', error);
        return { success: false, error: 'Network error. Please try again.' };
    }
}

async function signup(email, password, fullName) {
    try {
        console.info('[signup] POST', `${API_BASE}/auth/register`);
        const response = await fetch(`${API_BASE}/auth/register`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email, password, full_name: fullName })
        });
        const raw = await response.text();
        let data = null;
        try { data = raw ? JSON.parse(raw) : null; } catch (e) {
            console.error('[signup] Non-JSON response', raw);
        }
        console.info('[signup] status', response.status, 'ok', response.ok);
        if (response.ok) {
            return { success: true };
        }
        const detail = (data && data.detail) ? data.detail : (raw || 'Registration failed');
        return { success: false, error: detail };
    } catch (error) {
        console.error('[signup] Network error:', error);
        return { success: false, error: 'Network error. Please try again.' };
    }
}

function logout() {
    clearAuthData();
    window.location.href = '/';
}

async function authFetch(url, options = {}) {
    const token = getAuthToken();
    if (!token) {
        throw new Error('Not authenticated');
    }
    const headers = {
        ...options.headers,
        'Authorization': `Bearer ${token}`
    };
    const response = await fetch(url, { ...options, headers });
    if (response.status === 401) {
        clearAuthData();
        window.location.href = '/login.html';
        throw new Error('Session expired');
    }
    return response;
}

function ensureLoggedIn(redirect = window.location.pathname) {
    if (!isLoggedIn()) {
        window.location.href = `/login.html?return=${encodeURIComponent(redirect)}`;
        return false;
    }
    return true;
}

function ensureTenantContext(redirect = window.location.pathname) {
    const tenant = getTenantContext();
    if (!tenant || !tenant.company_id) {
        window.location.href = `/login.html?return=${encodeURIComponent(redirect)}`;
        return false;
    }
    return true;
}

window.getTenantContext = getTenantContext;
window.setTenantContext = setTenantContext;
window.ensureLoggedIn = ensureLoggedIn;
window.ensureTenantContext = ensureTenantContext;
window.login = login;
window.signup = signup;
window.logout = logout;
window.authFetch = authFetch;
window.isLoggedIn = isLoggedIn;
window.getCurrentUser = getCurrentUser;
window.getAuthToken = getAuthToken;
window.getRefreshToken = getRefreshToken;

document.addEventListener('DOMContentLoaded', () => {
    try {
        initThemeToggle();
        updateNavigation();
        const logoutLink = document.getElementById('logoutLink');
        if (logoutLink) {
            logoutLink.addEventListener('click', (event) => {
                event.preventDefault();
                logout();
            });
        }
    } catch (error) {
        console.warn('Initialization error:', error);
    }
});
