# RBAC System Guide

## Overview

SureFlights implements a comprehensive Role-Based Access Control (RBAC) system that provides JWT-based authentication and granular permission management for operational staff.

## Features

- **JWT Authentication** - Secure token-based authentication with access and refresh tokens
- **Role-Based Permissions** - Four distinct roles with specific permission sets
- **Rate Limiting** - Protection against brute force attacks (5 attempts per 15 minutes)
- **Audit Logging** - Complete audit trail of all security-relevant events
- **Password Management** - Secure password hashing and self-service password changes

## User Roles

### 1. Agent
**Purpose:** Front-line customer service representatives

**Permissions:**
- View and modify trip details
- Add notes to customer trips
- View and send notifications
- Access customer contact information

**Restrictions:**
- Cannot view financial data
- Cannot manage users
- Cannot access system settings

### 2. Supervisor
**Purpose:** Team leads managing agents and operations

**All Agent permissions, plus:**
- Manage fees, promotions, and templates
- View and manage users (except admin role assignment)
- Assign roles to users (agent, supervisor, finance)
- Resolve escalations
- View audit logs

**Restrictions:**
- Cannot assign admin role
- Cannot view/export full financial reports

### 3. Finance
**Purpose:** Financial team managing payments and refunds

**Permissions:**
- View trip details (read-only)
- View all payment data
- Process refunds
- Export financial reports

**Restrictions:**
- Cannot modify trips or add notes
- Cannot manage users
- Cannot access system settings

### 4. Admin
**Purpose:** System administrators with full access

**All permissions:**
- Complete system access
- Assign any role including admin
- Manage API keys and integrations
- Modify system settings
- User impersonation capability

---

## Authentication Flow

### 1. Login
```bash
POST /auth/login
Content-Type: application/json

{
  "email": "user@sureflights.ng",
  "password": "password123"
}
```

**Response:**
```json
{
  "access_token": "eyJhbGc...",
  "refresh_token": "eyJhbGc...",
  "token_type": "bearer",
  "expires_in": 1800
}
```

### 2. Using Access Token
Include the access token in the `Authorization` header:

```bash
GET /auth/me
Authorization: Bearer eyJhbGc...
```

### 3. Refreshing Tokens
```bash
POST /auth/refresh
Content-Type: application/json

{
  "refresh_token": "eyJhbGc..."
}
```

### 4. Change Password
```bash
POST /auth/change-password
Authorization: Bearer eyJhbGc...
Content-Type: application/json

{
  "current_password": "oldpass123",
  "new_password": "newpass456"
}
```

---

## Security Features

### Rate Limiting
- **Failed Login Attempts:** Maximum 5 attempts per 15 minutes per IP
- **Lockout Duration:** 15 minutes after exceeding limit
- **Automatic Reset:** Successful login clears rate limit counter
- **IP-Based Tracking:** Prevents distributed attacks from being counted separately

### Audit Logging
All security-relevant events are logged:
- User logins and logouts
- Failed login attempts (with IP address)
- User creation and modification
- Role assignments
- Password changes
- Permission denials
- Financial exports
- Trip modifications

**View Audit Logs:** (Admin/Supervisor only)
```bash
GET /v1/ops/audit-logs?event=user_login&limit=50
Authorization: Bearer eyJhbGc...
```

---

## API Endpoints

### Authentication Endpoints (`/auth/*`)
- `POST /auth/login` - Authenticate and receive tokens
- `POST /auth/refresh` - Refresh access token
- `POST /auth/change-password` - Change password (requires auth)
- `GET /auth/me` - Get current user info (requires auth)

### User Management (`/v1/ops/users/*`)
- `GET /v1/ops/users` - List users (Supervisor, Admin)
- `POST /v1/ops/users` - Create user (Supervisor, Admin)
- `GET /v1/ops/users/{id}` - Get user details (Supervisor, Admin)
- `PATCH /v1/ops/users/{id}` - Update user (Supervisor, Admin)
- `PATCH /v1/ops/users/{id}/role` - Change user role (Supervisor, Admin)
- `PATCH /v1/ops/users/{id}/status` - Activate/deactivate user (Supervisor, Admin)

### Operational Endpoints (`/v1/ops/*`)
- `GET /v1/ops/trips` - List trips (Agent, Supervisor, Finance, Admin)
- `POST /v1/ops/trips/{id}/notes` - Add trip note (Agent, Supervisor, Admin)
- `GET /v1/ops/payments` - List payments (Finance, Admin)
- `GET /v1/ops/financial-export` - Export financial data (Finance, Admin)
- `GET /v1/ops/audit-logs` - View audit logs (Supervisor, Admin)

---

## Getting Started

### 1. Initial Setup
A default admin user is created during database migration:

```
Email: admin@sureflights.ng
Password: admin123
```

**⚠️ IMPORTANT:** Change the default admin password immediately after first login!

### 2. Create Users
Use the admin account to create operational users:

```bash
POST /v1/ops/users
Authorization: Bearer {admin_token}
Content-Type: application/json

{
  "email": "agent@sureflights.ng",
  "name": "Customer Service Agent",
  "password": "secure_password",
  "role": "agent",
  "status": "active"
}
```

### 3. Test Access
Run the comprehensive test script:

```bash
python test_rbac.py
```

This script validates:
- Authentication flow
- Permission enforcement
- User management
- Role restrictions
- Password changes

---

## Permission Matrix

| Permission | Agent | Supervisor | Finance | Admin |
|------------|-------|------------|---------|-------|
| View Trips | ✅ | ✅ | ✅ | ✅ |
| Modify Trips | ✅ | ✅ | ❌ | ✅ |
| Add Trip Notes | ✅ | ✅ | ❌ | ✅ |
| View Payments | ❌ | ❌ | ✅ | ✅ |
| Process Refunds | ❌ | ❌ | ✅ | ✅ |
| Export Financial | ❌ | ❌ | ✅ | ✅ |
| Manage Fees | ❌ | ✅ | ❌ | ✅ |
| View Users | ❌ | ✅ | ❌ | ✅ |
| Manage Users | ❌ | ✅ | ❌ | ✅ |
| Assign Roles | ❌ | ✅* | ❌ | ✅ |
| Assign Admin Role | ❌ | ❌ | ❌ | ✅ |
| View Audit Logs | ❌ | ✅ | ❌ | ✅ |
| Manage API Keys | ❌ | ❌ | ❌ | ✅ |
| System Settings | ❌ | ❌ | ❌ | ✅ |

*Supervisor can assign agent, supervisor, and finance roles, but not admin.

---

## Security Best Practices

1. **Change Default Credentials** - Immediately change the default admin password
2. **Strong Passwords** - Enforce minimum password complexity requirements
3. **Principle of Least Privilege** - Assign the minimum role necessary for each user
4. **Regular Audits** - Review audit logs regularly for suspicious activity
5. **Token Expiration** - Access tokens expire after 30 minutes; refresh tokens after 7 days
6. **HTTPS Only** - Always use HTTPS in production to protect tokens in transit
7. **Monitor Failed Logins** - Set up alerts for repeated failed login attempts
8. **User Deactivation** - Deactivate users instead of deleting when they leave the organization

---

## Troubleshooting

### "Too many failed attempts"
- **Cause:** More than 5 failed login attempts from your IP in 15 minutes
- **Solution:** Wait 15 minutes or contact an admin to clear the lockout

### "Permission denied"
- **Cause:** Your role lacks the required permission
- **Solution:** Contact your supervisor or admin to request appropriate role assignment

### "Invalid refresh token"
- **Cause:** Refresh token has expired or is malformed
- **Solution:** Re-authenticate using `/auth/login`

### "User account is inactive"
- **Cause:** Account has been deactivated
- **Solution:** Contact an admin to reactivate your account

---

## API Documentation

Interactive API documentation is available at:
- **Swagger UI:** http://localhost:8001/docs
- **ReDoc:** http://localhost:8001/redoc

## Support

For issues or questions about the RBAC system:
1. Check the audit logs for security events
2. Review this documentation
3. Contact the system administrator
4. Refer to the API documentation at `/docs`
