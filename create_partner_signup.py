from pathlib import Path

content = """<!DOCTYPE html>
<html lang=\"en\">
<head>
    <meta charset=\"UTF-8\">
    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">
    <title>Become a Partner - SureFlights</title>
    <link rel=\"stylesheet\" href=\"styles.css\">
</head>
<body class=\"theme-light\">
    <div class=\"auth-container partner\">
        <div class=\"auth-card partner\">
            <a href=\"/\" class=\"partner-brand\">
                <img src=\"images/logo.png\" width=\"48\" height=\"48\" alt=\"SureFlights Logo\">
                <span>SureFlights Partner</span>
            </a>

            <h2>Set Up Your Company Account</h2>
            <p class=\"partner-subtitle\">Centralize travel management for your organization in a few quick steps.</p>

            <div id=\"partnerError\" class=\"error-message\" style=\"display:none;\"></div>
            <div id=\"partnerSuccess\" class=\"success-message\" style=\"display:none;\"></div>

            <form id=\"partnerSignupForm\" class=\"partner-form\">
                <div class=\"form-grid\">
                    <div class=\"form-group\">
                        <label for=\"companyName\">Company Name</label>
                        <input type=\"text\" id=\"companyName\" required placeholder=\"Acme Corporation\">
                    </div>
                    <div class=\"form-group\">
                        <label for=\"companyDomain\">Company Domain</label>
                        <input type=\"text\" id=\"companyDomain\" placeholder=\"acme.com\">
                    </div>
                </div>

                <div class=\"form-grid\">
                    <div class=\"form-group\">
                        <label for=\"companyCountry\">Country</label>
                        <select id=\"companyCountry\" required>
                            <option value=\"\">Select country</option>
                            <option value=\"NG\">Nigeria</option>
                            <option value=\"US\">United States</option>
                            <option value=\"GB\">United Kingdom</option>
                            <option value=\"CA\">Canada</option>
                            <option value=\"AE\">United Arab Emirates</option>
                            <option value=\"ZA\">South Africa</option>
                        </select>
                    </div>
                    <div class=\"form-group\">
                        <label for=\"companyCurrency\">Preferred Currency</label>
                        <select id=\"companyCurrency\" required>
                            <option value=\"\">Select currency</option>
                            <option value=\"NGN\">NGN - Nigerian Naira</option>
                            <option value=\"USD\">USD - US Dollar</option>
                            <option value=\"GBP\">GBP - British Pound</option>
                            <option value=\"EUR\">EUR - Euro</option>
                            <option value=\"ZAR\">ZAR - South African Rand</option>
                        </select>
                    </div>
                </div>

                <div class=\"form-group\">
                    <label for=\"companySlug\">Company Slug (optional)</label>
                    <input type=\"text\" id=\"companySlug\" placeholder=\"acme-travel\">
                    <small class=\"helper-text\">Used in URLs. Leave blank to auto-generate.</small>
                </div>

                <hr class=\"form-divider\">

                <h3>Company Admin</h3>
                <div class=\"form-grid\">
                    <div class=\"form-group\">
                        <label for=\"adminName\">Full Name</label>
                        <input type=\"text\" id=\"adminName\" required placeholder=\"Jane Doe\">
                    </div>
                    <div class=\"form-group\">
                        <label for=\"adminEmail\">Work Email</label>
                        <input type=\"email\" id=\"adminEmail\" required placeholder=\"jane.doe@acme.com\">
                    </div>
                </div>

                <div class=\"form-grid\">
                    <div class=\"form-group\">
                        <label for=\"adminPassword\">Password</label>
                        <input type=\"password\" id=\"adminPassword\" required minlength=\"8\" placeholder=\"Create a strong password\">
                    </div>
                    <div class=\"form-group\">
                        <label for=\"adminPasswordConfirm\">Confirm Password</label>
                        <input type=\"password\" id=\"adminPasswordConfirm\" required minlength=\"8\" placeholder=\"Re-enter password\">
                    </div>
                </div>

                <button type=\"submit\" class=\"btn btn-primary btn-large\" id=\"partnerSubmitBtn\">Create Partner Account</button>
            </form>

            <p class=\"partner-note\">Already managing travel with SureFlights Partner? <a href=\"login.html\">Log in</a></p>
        </div>
    </div>

    <script src=\"auth.js\"></script>
    <script>
        const partnerForm = document.getElementById('partnerSignupForm');
        const errorDiv = document.getElementById('partnerError');
        const successDiv = document.getElementById('partnerSuccess');
        const submitBtn = document.getElementById('partnerSubmitBtn');

        document.addEventListener('DOMContentLoaded', () => {
            const tenant = getTenantContext();
            if (isLoggedIn() && tenant && tenant.company_id) {
                window.location.href = 'partner-dashboard.html';
            }
        });

        partnerForm.addEventListener('submit', async (event) => {
            event.preventDefault();
            errorDiv.style.display = 'none';
            successDiv.style.display = 'none';

            const password = document.getElementById('adminPassword').value;
            const confirmPassword = document.getElementById('adminPasswordConfirm').value;
            if (password !== confirmPassword) {
                errorDiv.textContent = 'Passwords do not match.';
                errorDiv.style.display = 'block';
                return;
            }

            const payload = {
                company_name: document.getElementById('companyName').value.trim(),
                slug: document.getElementById('companySlug').value.trim() || null,
                domain: document.getElementById('companyDomain').value.trim() || null,
                country: document.getElementById('companyCountry').value,
                currency: document.getElementById('companyCurrency').value,
                admin_email: document.getElementById('adminEmail').value.trim(),
                admin_name: document.getElementById('adminName').value.trim(),
                admin_password: password
            };

            submitBtn.disabled = true;
            submitBtn.textContent = 'Creating account...';

            try {
                const response = await fetch(`${API_BASE}/b2b/companies`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });

                const data = await response.json();
                if (!response.ok) {
                    throw new Error(data.detail || 'Unable to create partner account');
                }

                successDiv.textContent = 'Account created! Signing you in...';
                successDiv.style.display = 'block';

                const loginResult = await login(payload.admin_email, payload.admin_password);
                if (loginResult.success) {
                    window.location.href = 'partner-dashboard.html';
                    return;
                }

                if (loginResult.needsCompanySelection) {
                    const created = loginResult.available_companies.find((c) => c.id === data.company_id);
                    const companyId = created ? created.id : (loginResult.available_companies[0] && loginResult.available_companies[0].id);
                    if (companyId) {
                        const retry = await login(payload.admin_email, payload.admin_password, { companyId });
                        if (retry.success) {
                            window.location.href = 'partner-dashboard.html';
                            return;
                        }
                    }
                }

                window.location.href = 'login.html';
            } catch (err) {
                console.error(err);
                errorDiv.textContent = err.message || 'An unexpected error occurred.';
                errorDiv.style.display = 'block';
                submitBtn.disabled = false;
                submitBtn.textContent = 'Create Partner Account';
            }
        });
    </script>
</body>
</html>
"""

Path("static/partner-signup.html").write_text(content)
