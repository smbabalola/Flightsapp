from pathlib import Path

content = """<!DOCTYPE html>
<html lang=\"en\">
<head>
    <meta charset=\"UTF-8\">
    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">
    <title>Login - SureFlights</title>
    <link rel=\"stylesheet\" href=\"styles.css\">
</head>
<body class=\"theme-light\">
    <div class=\"auth-container\">
        <div class=\"auth-card\">
            <a href=\"/\" style=\"display: flex; align-items: center; justify-content: center; gap: 0.5rem; text-decoration: none; color: inherit; margin-bottom: 1.5rem;\">
                <img src=\"images/logo.png\" width=\"48\" height=\"48\" alt=\"SureFlights Logo\">
                <span style=\"font-size: 1.5rem; font-weight: 700;\">SureFlights</span>
            </a>

            <h2>Welcome Back</h2>
            <p class=\"partner-note\" style=\"margin-bottom: 1.5rem;\">Are you a travel manager? <a href=\"partner-signup.html\">Become a partner</a></p>

            <div id=\"error\" class=\"error-message\" style=\"display: none;\"></div>
            <div id=\"success\" class=\"success-message\" style=\"display: none;\"></div>

            <form id=\"loginForm\">
                <div class=\"form-group\">
                    <label for=\"email\">Email Address</label>
                    <input type=\"email\" id=\"email\" required placeholder=\"you@example.com\">
                </div>

                <div class=\"form-group\">
                    <label for=\"password\">Password</label>
                    <input type=\"password\" id=\"password\" required placeholder=\"Enter your password\">
                </div>

                <div style=\"text-align: right; margin-bottom: 1rem;\">
                    <a href=\"forgot-password.html\" style=\"color: var(--primary); text-decoration: none; font-size: 0.875rem;\">Forgot password?</a>
                </div>

                <button type=\"submit\" class=\"btn btn-primary btn-large\" id=\"submitBtn\">Sign In</button>
            </form>

            <div class=\"auth-links\">
                Don't have an account? <a href=\"signup.html\">Sign up</a>
            </div>
        </div>
    </div>

    <div class=\"modal-backdrop\" id=\"companyModal\" style=\"display:none;\">
        <div class=\"modal\">
            <div class=\"modal-header\">
                <h3>Select a Company</h3>
                <button type=\"button\" class=\"btn btn-link\" id=\"closeCompanyModal\">Cancel</button>
            </div>
            <p>Please choose the company you want to access.</p>
            <ul id=\"companyOptions\" class=\"company-list\"></ul>
        </div>
    </div>

    <script src=\"auth.js\"></script>
    <script>
        const errorDiv = document.getElementById('error');
        const successDiv = document.getElementById('success');
        const submitBtn = document.getElementById('submitBtn');
        const companyModal = document.getElementById('companyModal');
        const companyOptions = document.getElementById('companyOptions');
        const closeCompanyModal = document.getElementById('closeCompanyModal');
        const loginForm = document.getElementById('loginForm');
        let pendingLogin = null;

        if (isLoggedIn()) {
            const tenant = getTenantContext();
            if (tenant && tenant.company_id) {
                window.location.href = 'partner-dashboard.html';
            } else {
                window.location.href = 'dashboard.html';
            }
        }

        closeCompanyModal.addEventListener('click', () => {
            hideCompanySelection();
            submitBtn.disabled = false;
            submitBtn.textContent = 'Sign In';
        });

        loginForm.addEventListener('submit', async (event) => {
            event.preventDefault();
            const email = document.getElementById('email').value;
            const password = document.getElementById('password').value;
            await attemptLogin(email, password);
        });

        async function attemptLogin(email, password, options = {}) {
            errorDiv.style.display = 'none';
            successDiv.style.display = 'none';
            submitBtn.disabled = true;
            submitBtn.textContent = 'Signing in...';

            try {
                const result = await login(email, password, options);

                if (result.success) {
                    successDiv.textContent = 'Login successful! Redirecting...';
                    successDiv.style.display = 'block';
                    redirectAfterLogin();
                    return;
                }

                if (result.needsCompanySelection) {
                    pendingLogin = { email, password };
                    showCompanySelection(result.available_companies || []);
                    return;
                }

                errorDiv.textContent = result.error || 'Login failed';
                errorDiv.style.display = 'block';
            } catch (error) {
                console.error('Login error', error);
                errorDiv.textContent = 'Network error. Please try again.';
                errorDiv.style.display = 'block';
            }

            submitBtn.disabled = false;
            submitBtn.textContent = 'Sign In';
        }

        function redirectAfterLogin() {
            const tenant = getTenantContext();
            const returnUrl = new URLSearchParams(window.location.search).get('return');
            if (tenant && tenant.company_id) {
                window.location.href = returnUrl || 'partner-dashboard.html';
                return;
            }
            window.location.href = returnUrl || 'dashboard.html';
        }

        function showCompanySelection(companies) {
            companyOptions.innerHTML = '';
            if (!companies.length) {
                companyOptions.innerHTML = '<li>No active companies available for this account.</li>';
                return;
            }
            companies.forEach((company) => {
                const item = document.createElement('li');
                const button = document.createElement('button');
                button.className = 'company-option';
                button.type = 'button';
                button.dataset.companyId = company.id;
                button.dataset.companySlug = company.slug || '';
                button.innerHTML = `<strong>${company.name}</strong><span>${company.role} • ${company.status}</span>`;
                button.addEventListener('click', () => selectCompany(button.dataset.companyId, button.dataset.companySlug));
                item.appendChild(button);
                companyOptions.appendChild(item);
            });
            companyModal.style.display = 'flex';
        }

        function hideCompanySelection() {
            companyModal.style.display = 'none';
            companyOptions.innerHTML = '';
            pendingLogin = null;
        }

        async function selectCompany(companyId, companySlug) {
            if (!pendingLogin) return;
            submitBtn.textContent = 'Connecting...';
            try {
                const result = await login(pendingLogin.email, pendingLogin.password, { companyId: Number(companyId), companySlug: companySlug || undefined });
                if (result.success) {
                    hideCompanySelection();
                    redirectAfterLogin();
                    return;
                }
                throw new Error(result.error || 'Unable to switch company.');
            } catch (error) {
                console.error(error);
                errorDiv.textContent = error.message;
                errorDiv.style.display = 'block';
                hideCompanySelection();
                submitBtn.disabled = false;
                submitBtn.textContent = 'Sign In';
            }
        }
    </script>
</body>
</html>
"""

Path("static/login.html").write_text(content)
