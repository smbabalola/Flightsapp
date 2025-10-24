(function () {
    const profileForm = document.getElementById('companyProfileForm');
    const profileFeedback = document.getElementById('profileFeedback');
    const teamTableBody = document.getElementById('teamTableBody');
    const inviteForm = document.getElementById('inviteForm');
    const inviteFeedback = document.getElementById('inviteFeedback');
    const requestsTableBody = document.getElementById('requestsTableBody');
    const approvalsTableBody = document.getElementById('approvalsTableBody');
    const requestForm = document.getElementById('travelRequestForm');
    const requestFeedback = document.getElementById('requestFeedback');
    const tenantChip = document.getElementById('tenantChip');

    function formatRoute(origin, destination) {
        const from = origin || '—';
        const to = destination || '—';
        return `${from} \u2192 ${to}`;
    }

    function formatEmployeeLabel(request, tenant) {
        if (tenant && tenant.company_user_id && request.employee_company_user_id === tenant.company_user_id) {
            return 'You';
        }
        return request.employee_name || request.employee_email || request.employee_company_user_email || request.employee_company_user_id || '—';
    }

    async function initialize() {
        if (!ensureLoggedIn('/partner-dashboard.html')) return;
        if (!ensureTenantContext('/partner-dashboard.html')) return;
        try {
            await Promise.all([
                loadCompanyProfile(),
                loadTeamMembers(),
                loadTravelRequests()
            ]);
        } catch (error) {
            console.error('Initialization error', error);
        }
    }

    function updateTenantChip(tenant, companyName) {
        if (!tenantChip) return;
        const roleLabel = tenant && tenant.company_role ? tenant.company_role.replace('_', ' ') : 'employee';
        tenantChip.textContent = companyName ? `${companyName} - ${roleLabel}` : roleLabel;
    }

    async function loadCompanyProfile() {
        try {
            const response = await authFetch(`${API_BASE}/b2b/companies/me`);
            const data = await response.json();
            document.getElementById('profileName').value = data.name || '';
            document.getElementById('profileSlug').value = data.slug || '';
            document.getElementById('profileDomain').value = data.domain || '';
            document.getElementById('profileCurrency').value = data.currency || '';
            document.getElementById('profileCountry').value = data.country || '';
            document.getElementById('profileStatus').value = data.status || '';
            updateTenantChip(getTenantContext(), data.name || '');
        } catch (error) {
            console.error('Failed to load company profile', error);
        }
    }

    async function updateCompanyProfile(event) {
        event.preventDefault();
        profileFeedback.textContent = '';
        profileFeedback.classList.remove('success');
        try {
            const payload = {
                name: document.getElementById('profileName').value.trim(),
                domain: document.getElementById('profileDomain').value.trim() || null,
                country: document.getElementById('profileCountry').value.trim() || null,
                currency: document.getElementById('profileCurrency').value.trim() || null
            };
            const response = await authFetch(`${API_BASE}/b2b/companies/me`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
            if (!response.ok) {
                const data = await response.json();
                throw new Error(data.detail || 'Failed to update company');
            }
            profileFeedback.textContent = 'Saved!';
            profileFeedback.classList.add('success');
            await loadCompanyProfile();
        } catch (error) {
            console.error(error);
            profileFeedback.textContent = error.message || 'Could not save changes';
            profileFeedback.classList.remove('success');
        }
    }

    async function loadTeamMembers() {
        try {
            const response = await authFetch(`${API_BASE}/b2b/members`);
            const members = await response.json();
            if (!Array.isArray(members) || members.length === 0) {
                teamTableBody.innerHTML = '<tr><td colspan="4">No team members yet.</td></tr>';
                return;
            }
            teamTableBody.innerHTML = members.map((member) => `
                <tr>
                    <td>${member.name || '—'}</td>
                    <td>${member.email}</td>
                    <td>${member.role}</td>
                    <td><span class="status-badge status-${member.status}">${member.status}</span></td>
                </tr>
            `).join('');
        } catch (error) {
            console.error('Failed to load members', error);
            teamTableBody.innerHTML = '<tr><td colspan="4">Unable to load team members.</td></tr>';
        }
    }

    async function sendInvitation(event) {
        event.preventDefault();
        inviteFeedback.textContent = '';
        inviteFeedback.classList.remove('success');
        try {
            const payload = {
                email: document.getElementById('inviteEmail').value.trim(),
                role: document.getElementById('inviteRole').value,
                expires_in_hours: Number(document.getElementById('inviteExpiry').value) || 72
            };
            const response = await authFetch(`${API_BASE}/b2b/members/invite`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
            if (!response.ok) {
                const data = await response.json();
                throw new Error(data.detail || 'Unable to send invitation');
            }
            inviteFeedback.textContent = 'Invitation sent!';
            inviteFeedback.classList.add('success');
            inviteForm.reset();
            await loadTeamMembers();
        } catch (error) {
            console.error(error);
            inviteFeedback.textContent = error.message || 'Could not send invitation';
            inviteFeedback.classList.remove('success');
        }
    }

    function buildRequestPayload() {
        const departureValue = document.getElementById('requestDepartDate').value;
        const returnValue = document.getElementById('requestReturnDate').value;
        const toIso = (value) => value ? new Date(`${value}T00:00:00`).toISOString() : null;
        return {
            policy_id: null,
            trip_type: returnValue ? 'round_trip' : 'one_way',
            origin: document.getElementById('requestOrigin').value.trim().toUpperCase(),
            destination: document.getElementById('requestDestination').value.trim().toUpperCase(),
            departure_date: toIso(departureValue),
            return_date: toIso(returnValue),
            justification: document.getElementById('requestJustification').value.trim() || null,
            traveler_count: Number(document.getElementById('requestTravelers').value) || 1,
            budget_minor: document.getElementById('requestBudget').value ? Number(document.getElementById('requestBudget').value) : null,
            currency: document.getElementById('requestCurrency').value.trim() || null,
            requested_itineraries: [],
            offer_snapshot: null,
            auto_submit: document.getElementById('requestAutoSubmit').checked
        };
    }

    async function createTravelRequest(event) {
        event.preventDefault();
        requestFeedback.textContent = '';
        requestFeedback.classList.remove('success');
        const payload = buildRequestPayload();
        try {
            const response = await authFetch(`${API_BASE}/b2b/travel-requests`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
            const data = await response.json();
            if (!response.ok) {
                throw new Error(data.detail || 'Unable to create travel request');
            }
            requestFeedback.textContent = payload.auto_submit ? 'Travel request submitted for approval.' : 'Travel request created as draft.';
            requestFeedback.classList.add('success');
            requestForm.reset();
            await loadTravelRequests();
        } catch (error) {
            console.error(error);
            requestFeedback.textContent = error.message || 'Could not create request';
            requestFeedback.classList.remove('success');
        }
    }

    async function loadTravelRequests() {
        try {
            const tenant = getTenantContext();
            const response = await authFetch(`${API_BASE}/b2b/travel-requests`);
            const requests = await response.json();
            renderRequests(requests, tenant);
            renderApprovals(requests, tenant);
        } catch (error) {
            console.error('Failed to load travel requests', error);
            requestsTableBody.innerHTML = '<tr><td colspan="4">Unable to load travel requests.</td></tr>';
            approvalsTableBody.innerHTML = '<tr><td colspan="5">Unable to load approvals.</td></tr>';
        }
    }

    function renderRequests(requests, tenant) {
        if (!Array.isArray(requests) || requests.length === 0) {
            requestsTableBody.innerHTML = '<tr><td colspan="4">No travel requests yet.</td></tr>';
            return;
        }
        const myRequests = tenant && tenant.company_user_id ? requests.filter((r) => r.employee_company_user_id === tenant.company_user_id) : requests;
        if (myRequests.length === 0) {
            requestsTableBody.innerHTML = '<tr><td colspan="4">No travel requests submitted yet.</td></tr>';
            return;
        }
        requestsTableBody.innerHTML = myRequests.map((req) => `
            <tr>
                <td>${req.reference}</td>
                <td>${formatRoute(req.origin, req.destination)}</td>
                <td><span class="status-badge status-${req.status}">${req.status}</span></td>
                <td>${req.submitted_at ? new Date(req.submitted_at).toLocaleDateString() : '—'}</td>
            </tr>
        `).join('');
    }

    function renderApprovals(requests, tenant) {
        if (!tenant || !tenant.company_user_id) {
            approvalsTableBody.innerHTML = '<tr><td colspan="5">No approvals pending.</td></tr>';
            return;
        }
        const actionable = (requests || []).filter((req) => {
            if (req.status !== 'pending_approval') return false;
            const state = req.approval_state || {};
            const levels = Array.isArray(state.levels) ? state.levels : [];
            return levels.some((level) => level.status === 'pending' && Array.isArray(level.approver_ids) && level.approver_ids.includes(tenant.company_user_id));
        });
        if (actionable.length === 0) {
            approvalsTableBody.innerHTML = '<tr><td colspan="5">No requests awaiting your approval.</td></tr>';
            return;
        }
        approvalsTableBody.innerHTML = actionable.map((req) => `
            <tr>
                <td>${req.reference}</td>
                <td>${formatEmployeeLabel(req, tenant)}</td>
                <td>${formatRoute(req.origin, req.destination)}</td>
                <td><span class="status-badge status-${req.status}">${req.status}</span></td>
                <td class="action-cell">
                    <button class="btn btn-secondary btn-sm" data-action="approve" data-id="${req.id}">Approve</button>
                    <button class="btn btn-outline btn-sm" data-action="reject" data-id="${req.id}">Reject</button>
                </td>
            </tr>
        `).join('');
    }

    async function handleApproval(action, id) {
        try {
            const response = await authFetch(`${API_BASE}/b2b/travel-requests/${id}/${action}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ comment: '' })
            });
            if (!response.ok) {
                const data = await response.json();
                throw new Error(data.detail || 'Unable to update approval');
            }
            await loadTravelRequests();
        } catch (error) {
            console.error(error);
            alert(error.message || 'Failed to update approval');
        }
    }

    if (approvalsTableBody) {
        approvalsTableBody.addEventListener('click', (event) => {
            const button = event.target.closest('button[data-action]');
            if (!button) return;
            const id = button.getAttribute('data-id');
            const action = button.getAttribute('data-action');
            handleApproval(action === 'approve' ? 'approve' : 'reject', id);
        });
    }

    if (profileForm) {
        profileForm.addEventListener('submit', updateCompanyProfile);
    }

    if (inviteForm) {
        inviteForm.addEventListener('submit', sendInvitation);
    }

    if (requestForm) {
        requestForm.addEventListener('submit', createTravelRequest);
    }

    initialize();
})();









