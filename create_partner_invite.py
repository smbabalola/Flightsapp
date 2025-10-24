from pathlib import Path

content = """<!DOCTYPE html>
<html lang=\"en\">
<head>
    <meta charset=\"UTF-8\">
    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">
    <title>Accept Invitation - SureFlights Partner</title>
    <link rel=\"stylesheet\" href=\"styles.css\">
</head>
<body class=\"theme-light\">
    <div class=\"auth-container partner\">
        <div class=\"auth-card partner\">
            <a href=\"/\" class=\"partner-brand\">
                <img src=\"images/logo.png\" width=\"48\" height=\"48\" alt=\"SureFlights Logo\">
                <span>SureFlights Partner</span>
            </a>

            <h2>Accept Invitation</h2>
            <div id=\"inviteInfo\" class=\"invite-info\">Loading invitation details...</div>

            <div id=\"inviteError\" class=\"error-message\" style=\"display:none;\"></div>
            <div id=\"inviteSuccess\" class=\"success-message\" style=\"display:none;\"></div>

            <form id=\"inviteForm\" class=\"partner-form\" style=\"display:none;\">
                <div class=\"form-group\">
                    <label for=\"inviteName\">Full Name</label>
                    <input type=\"text\" id=\"inviteName\" required placeholder=\"Your name\">
                </div>
                <div class=\"form-group\">
                    <label for=\"invitePassword\">Set Password</label>
                    <input type=\"password\" id=\"invitePassword\" required minlength=\"8\">
                </div>
                <div class=\"form-group\">
                    <label for=\"invitePasswordConfirm\">Confirm Password</label>
                    <input type=\"password\" id=\"invitePasswordConfirm\" required minlength=\"8\">
                </div>
                <button type=\"submit\" class=\"btn btn-primary btn-large\" id=\"inviteSubmitBtn\">Join Company</button>
            </form>
        </div>
    </div>

    <script src=\"auth.js\"></script>
    <script>
        const params = new URLSearchParams(window.location.search);
        const token = params.get('token');
        const inviteInfo = document.getElementById('inviteInfo');
        const inviteForm = document.getElementById('inviteForm');
        const inviteError = document.getElementById('inviteError');
        const inviteSuccess = document.getElementById('inviteSuccess');
        const submitBtn = document.getElementById('inviteSubmitBtn');

        if (!token) {
            inviteInfo.textContent = 'Invitation token not provided.';
        } else {
            fetchInvitation();
        }

        async function fetchInvitation() {
            try {
                const response = await fetch(`${API_BASE}/b2b/invitations/${token}`);
                const data = await response.json();
                if (!response.ok) {
                    throw new Error(data.detail || 'Invitation not found');
                }
                inviteInfo.innerHTML = `<strong>${data.email}</strong> has been invited to join <strong>${data.company_id}</strong> as <strong>${data.role}</strong>.`;
                inviteForm.style.display = 'block';
            } catch (error) {
                inviteInfo.textContent = '';
                inviteError.textContent = error.message;
                inviteError.style.display = 'block';
            }
        }

        inviteForm.addEventListener('submit', async (event) => {
            event.preventDefault();
            inviteError.style.display = 'none';
            inviteSuccess.style.display = 'none';

            const password = document.getElementById('invitePassword').value;
            const confirm = document.getElementById('invitePasswordConfirm').value;
            if (password !== confirm) {
                inviteError.textContent = 'Passwords do not match.';
                inviteError.style.display = 'block';
                return;
            }

            submitBtn.disabled = true;
            submitBtn.textContent = 'Joining...';

            try {
                const response = await fetch(`${API_BASE}/b2b/invitations/${token}/accept`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        full_name: document.getElementById('inviteName').value.trim(),
                        password
                    })
                });
                const data = await response.json();
                if (!response.ok) {
                    throw new Error(data.detail || 'Could not accept invitation');
                }
                inviteSuccess.textContent = 'Invitation accepted! You can now log in.';
                inviteSuccess.style.display = 'block';
                setTimeout(() => window.location.href = 'login.html', 1200);
            } catch (error) {
                inviteError.textContent = error.message || 'Failed to accept invitation';
                inviteError.style.display = 'block';
                submitBtn.disabled = false;
                submitBtn.textContent = 'Join Company';
            }
        });
    </script>
</body>
</html>
"""

Path("static/partner-invite.html").write_text(content)
