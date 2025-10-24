# RBAC Specification

## Overview
SureFlights uses role-based access control (RBAC) to protect customer data, payment workflows, and administrative capabilities. Roles are assigned to internal users via the admin console and enforced by the FastAPI backend.

## Roles
- **Agent**
  - Handles day-to-day bookings and customer support.
  - Can search trips, view quotes, manage notifications, and add notes.
  - Cannot modify pricing rules, fees, or user roles.
- **Supervisor**
  - Includes all Agent permissions.
  - Manages service fees, promos, templates, and user role assignments (except Admin).
  - Resolves escalations such as schedule changes or duplicate PNRs.
- **Finance**
  - Views payments, settlements, and refund requests.
  - Initiates refunds/voids; exports financial reports.
  - Cannot alter pricing or operational templates.
- **Admin**
  - Full access to system settings, user management, API keys, and feature flags.
  - Can impersonate lower roles for troubleshooting and approve privileged actions.

## Permission Matrix
| Capability | Agent | Supervisor | Finance | Admin |
| --- | --- | --- | --- | --- |
| View trips/quotes | ✅ | ✅ | ✅ | ✅ |
| Modify trips/notes | ✅ | ✅ | ❌ | ✅ |
| Manage fees/promos/templates | ❌ | ✅ | ❌ | ✅ |
| Run financial exports | ❌ | ❌ | ✅ | ✅ |
| Process refunds/voids | ❌ | ❌ | ✅ | ✅ |
| Manage users & roles | ❌ | ✅ (except Admin) | ❌ | ✅ |
| Configure integrations/API keys | ❌ | ❌ | ❌ | ✅ |

## Enforcement Hooks
- /v1/ops/* endpoints require Basic auth (transitioning to OAuth2 with role claims).
- Admin-only routes apply equire_admin dependency.
- Future: JWT bearer tokens with role claim, middleware to map to scopes, and ownership checks for customer data.

## Audit & Logging
- Every privileged action (fees changes, refunds, user modifications) writes to udit_logs with user ID, role, and timestamp.
- Structured logs include equest_id and ctor_role fields to support investigations.

## Next Steps
- Migrate from Basic auth to OAuth2 client + session management.
- Implement least-privilege tokens for webhook processors.
- Add self-service scoped API keys under the Admin role for automation partners.
