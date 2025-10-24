from pathlib import Path

content = """<!DOCTYPE html>
<html lang=\"en\">
<head>
    <meta charset=\"UTF-8\">
    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">
    <title>Partner Dashboard - SureFlights</title>
    <link rel=\"stylesheet\" href=\"styles.css\">
</head>
<body class=\"theme-light\">
    <nav class=\"navbar\">
        <div class=\"container\">
            <div class=\"nav-brand\">
                <a href=\"/\" style=\"display: flex; align-items: center; gap: 0.5rem; text-decoration: none; color: inherit;\">
                    <img src=\"images/logo.png\" width=\"36\" height=\"36\" alt=\"SureFlights Logo\">
                    <span>SureFlights Partner</span>
                </a>
            </div>
            <div class=\"nav-links\">
                <button type=\"button\" id=\"themeToggle\" class=\"btn btn-secondary btn-sm\">Toggle Theme</button>
                <a href=\"partner-dashboard.html\" id=\"partnerDashboardLink\">Dashboard</a>
                <a href=\"dashboard.html\" id=\"dashboardLink\" style=\"display:none;\">Traveler Portal</a>
                <a href=\"#\" id=\"logoutLink\">Logout</a>
            </div>
        </div>
    </nav>

    <main class=\"partner-dashboard\">
        <aside class=\"partner-sidebar\">
            <div class=\"tenant-chip\" id=\"tenantChip\">Loading...</div>
            <nav class=\"partner-menu\">
                <a href=\"#profile\" class=\"partner-menu-item\">Company Profile</a>
                <a href=\"#team\" class=\"partner-menu-item\">Team & Invitations</a>
                <a href=\"#requests\" class=\"partner-menu-item\">Travel Requests</a>
                <a href=\"#approvals\" class=\"partner-menu-item\">Approvals</a>
            </nav>
        </aside>

        <section class=\"partner-content\">
            <section id=\"profile\" class=\"partner-section\">
                <header class=\"section-header\">
                    <h2>Company Profile</h2>
                    <p>Update contact details, policies, and preferences.</p>
                </header>
                <div class=\"card\" id=\"companyProfileCard\">
                    <form id=\"companyProfileForm\" class=\"profile-form\">
                        <div class=\"form-grid\">
                            <div class=\"form-group\">
                                <label for=\"profileName\">Company Name</label>
                                <input type=\"text\" id=\"profileName\" required>
                            </div>
                            <div class=\"form-group\">
                                <label for=\"profileSlug\">Slug</label>
                                <input type=\"text\" id=\"profileSlug\" disabled>
                            </div>
                        </div>
                        <div class=\"form-grid\">
                            <div class=\"form-group\">
                                <label for=\"profileDomain\">Domain</label>
                                <input type=\"text\" id=\"profileDomain\">
                            </div>
                            <div class=\"form-group\">
                                <label for=\"profileCurrency\">Currency</label>
                                <input type=\"text\" id=\"profileCurrency\" required>
                            </div>
                        </div>
                        <div class=\"form-grid\">
                            <div class=\"form-group\">
                                <label for=\"profileCountry\">Country</label>
                                <input type=\"text\" id=\"profileCountry\" required>
                            </div>
                            <div class=\"form-group\">
                                <label for=\"profileStatus\">Status</label>
                                <input type=\"text\" id=\"profileStatus\" disabled>
                            </div>
                        </div>
                        <div class=\"form-actions\">
                            <button type=\"submit\" class=\"btn btn-primary\">Save Changes</button>
                            <span class=\"form-feedback\" id=\"profileFeedback\"></span>
                        </div>
                    </form>
                </div>
            </section>

            <section id=\"team\" class=\"partner-section\">
                <header class=\"section-header\">
                    <h2>Team & Invitations</h2>
                    <p>Manage employees, managers, and finance approvers on your account.</p>
                </header>
                <div class=\"card\">
                    <h3>Invite Team Member</h3>
                    <form id=\"inviteForm\" class=\"form-inline\">
                        <input type=\"email\" id=\"inviteEmail\" placeholder=\"colleague@company.com\" required>
                        <select id=\"inviteRole\" required>
                            <option value=\"manager\">Manager</option>
                            <option value=\"employee\">Employee</option>
                            <option value=\"finance\">Finance</option>
                            <option value=\"company_admin\">Company Admin</option>
                        </select>
                        <input type=\"number\" id=\"inviteExpiry\" value=\"72\" min=\"1\" max=\"336\" required>
                        <button type=\"submit\" class=\"btn btn-primary\">Send Invite</button>
                        <span class=\"form-feedback\" id=\"inviteFeedback\"></span>
                    </form>
                    <div class=\"table-wrapper\">
                        <table class=\"partner-table\">
                            <thead>
                                <tr>
                                    <th>Name</th>
                                    <th>Email</th>
                                    <th>Role</th>
                                    <th>Status</th>
                                </tr>
                            </thead>
                            <tbody id=\"teamTableBody\">
                                <tr><td colspan=\"4\">Loading team...</td></tr>
                            </tbody>
                        </table>
                    </div>
                </div>
            </section>

            <section id=\"requests\" class=\"partner-section\">
                <header class=\"section-header\">
                    <h2>Travel Requests</h2>
                    <p>Track requests submitted by your employees and create new ones.</p>
                </header>
                <div class=\"card\">
                    <h3>New Travel Request</h3>
                    <form id=\"travelRequestForm\" class=\"travel-form\">
                        <div class=\"form-grid\">
                            <div class=\"form-group\">
                                <label for=\"requestOrigin\">Origin</label>
                                <input type=\"text\" id=\"requestOrigin\" placeholder=\"LOS\" maxlength=\"3\" required>
                            </div>
                            <div class=\"form-group\">
                                <label for=\"requestDestination\">Destination</label>
                                <input type=\"text\" id=\"requestDestination\" placeholder=\"ABV\" maxlength=\"3\" required>
                            </div>
                            <div class=\"form-group\">
                                <label for=\"requestDepartDate\">Departure</label>
                                <input type=\"date\" id=\"requestDepartDate\" required>
                            </div>
                            <div class=\"form-group\">
                                <label for=\"requestReturnDate\">Return</label>
                                <input type=\"date\" id=\"requestReturnDate\">
                            </div>
                        </div>
                        <div class=\"form-grid\">
                            <div class=\"form-group\">
                                <label for=\"requestBudget\">Budget (minor units)</label>
                                <input type=\"number\" id=\"requestBudget\" placeholder=\"150000\">
                            </div>
                            <div class=\"form-group\">
                                <label for=\"requestCurrency\">Currency</label>
                                <input type=\"text\" id=\"requestCurrency\" value=\"NGN\" maxlength=\"3\">
                            </div>
                            <div class=\"form-group\">
                                <label for=\"requestTravelers\">Travellers</label>
                                <input type=\"number\" id=\"requestTravelers\" value=\"1\" min=\"1\">
                            </div>
                            <div class=\"form-group\">
                                <label>Auto Submit</label>
                                <label class=\"switch\">
                                    <input type=\"checkbox\" id=\"requestAutoSubmit\" checked>
                                    <span class=\"slider\"></span>
                                </label>
                            </div>
                        </div>
                        <div class=\"form-group\">
                            <label for=\"requestJustification\">Business Justification</label>
                            <textarea id=\"requestJustification\" rows=\"3\" placeholder=\"Purpose of travel\"></textarea>
                        </div>
                        <div class=\"form-actions\">
                            <button type=\"submit\" class=\"btn btn-primary\">Create Request</button>
                            <span class=\"form-feedback\" id=\"requestFeedback\"></span>
                        </div>
                    </form>
                </div>

                <div class=\"card\">
                    <h3>Recent Requests</h3>
                    <div class=\"table-wrapper\">
                        <table class=\"partner-table\">
                            <thead>
                                <tr>
                                    <th>Reference</th>
                                    <th>Route</th>
                                    <th>Status</th>
                                    <th>Submitted</th>
                                </tr>
                            </thead>
                            <tbody id=\"requestsTableBody\">
                                <tr><td colspan=\"4\">Loading travel requests...</td></tr>
                            </tbody>
                        </table>
                    </div>
                </div>
            </section>

            <section id=\"approvals\" class=\"partner-section\">
                <header class=\"section-header\">
                    <h2>Approvals Queue</h2>
                    <p>Review requests awaiting your approval.</p>
                </header>
                <div class=\"card\">
                    <div class=\"table-wrapper\">
                        <table class=\"partner-table\">
                            <thead>
                                <tr>
                                    <th>Reference</th>
                                    <th>Employee</th>
                                    <th>Route</th>
                                    <th>Status</th>
                                    <th>Actions</th>
                                </tr>
                            </thead>
                            <tbody id=\"approvalsTableBody\">
                                <tr><td colspan=\"5\">Loading approvals...</td></tr>
                            </tbody>
                        </table>
                    </div>
                </div>
            </section>
        </section>
    </main>

    <footer class=\"footer\">
        <div class=\"container\">
            <div class=\"footer-bottom\">
                <p>&copy; 2025 SureFlights Partner. All rights reserved.</p>
            </div>
        </div>
    </footer>

    <script src=\"auth.js\"></script>
    <script src=\"partner.js\"></script>
</body>
</html>
"""

Path("static/partner-dashboard.html").write_text(content)
