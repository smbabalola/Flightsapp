"""
Role-Based Permission System

Defines roles, permissions, and access control logic.
"""
from enum import Enum
from typing import Set, List
from dataclasses import dataclass, field


class Role(str, Enum):
    """System-level roles used by SureFlights operations."""
    CUSTOMER = "customer"
    AGENT = "agent"
    SUPERVISOR = "supervisor"
    FINANCE = "finance"
    FINANCE_ACCOUNTANT = "finance_accountant"
    CUSTOMER_SUPPORT = "customer_support"
    OPERATIONS = "operations"
    MARKETING = "marketing"
    ANALYST = "analyst"
    QA = "qa"
    CONTENT_EDITOR = "content_editor"
    ADMIN = "admin"


class Permission(str, Enum):
    """Granular system permissions."""
    # Trip/Quote permissions
    VIEW_TRIPS = "view_trips"
    MODIFY_TRIPS = "modify_trips"
    ADD_TRIP_NOTES = "add_trip_notes"

    # Financial permissions
    VIEW_PAYMENTS = "view_payments"
    PROCESS_REFUNDS = "process_refunds"
    EXPORT_FINANCIAL = "export_financial"

    # Configuration permissions
    MANAGE_FEES = "manage_fees"
    MANAGE_PROMOS = "manage_promos"
    MANAGE_TEMPLATES = "manage_templates"

    # User management
    VIEW_USERS = "view_users"
    MANAGE_USERS = "manage_users"
    ASSIGN_ROLES = "assign_roles"
    ASSIGN_ADMIN_ROLE = "assign_admin_role"  # Only admin can assign admin role

    # System permissions
    MANAGE_API_KEYS = "manage_api_keys"
    MANAGE_INTEGRATIONS = "manage_integrations"
    VIEW_SYSTEM_SETTINGS = "view_system_settings"
    MODIFY_SYSTEM_SETTINGS = "modify_system_settings"
    IMPERSONATE_USERS = "impersonate_users"

    # Operational permissions
    VIEW_NOTIFICATIONS = "view_notifications"
    SEND_NOTIFICATIONS = "send_notifications"
    RESOLVE_ESCALATIONS = "resolve_escalations"
    VIEW_AUDIT_LOGS = "view_audit_logs"


class CompanyRole(str, Enum):
    """Tenant-scoped roles for corporate customers."""
    ADMIN = "company_admin"
    MANAGER = "manager"
    EMPLOYEE = "employee"
    FINANCE = "finance"


class CompanyPermission(str, Enum):
    """Tenant-level permissions."""
    MANAGE_COMPANY = "manage_company"
    MANAGE_EMPLOYEES = "manage_employees"
    VIEW_EMPLOYEES = "view_employees"
    SUBMIT_REQUESTS = "submit_requests"
    APPROVE_LEVEL_ONE = "approve_level_one"
    APPROVE_FINANCE = "approve_finance"
    MANAGE_POLICIES = "manage_policies"
    MANAGE_BILLING = "manage_billing"
    VIEW_REPORTS = "view_reports"
    VIEW_AUDIT_LOGS = "view_audit_logs"


# System role to permission mapping (clean)
ROLE_PERMISSIONS: dict[Role, Set[Permission]] = {
    Role.CUSTOMER: set(),
    Role.AGENT: {
        Permission.VIEW_TRIPS,
        Permission.MODIFY_TRIPS,
        Permission.ADD_TRIP_NOTES,
        Permission.VIEW_NOTIFICATIONS,
        Permission.SEND_NOTIFICATIONS,
    },
    Role.SUPERVISOR: {
        Permission.VIEW_TRIPS,
        Permission.MODIFY_TRIPS,
        Permission.ADD_TRIP_NOTES,
        Permission.VIEW_NOTIFICATIONS,
        Permission.SEND_NOTIFICATIONS,
        Permission.MANAGE_FEES,
        Permission.MANAGE_PROMOS,
        Permission.MANAGE_TEMPLATES,
        Permission.VIEW_USERS,
        Permission.MANAGE_USERS,
        Permission.ASSIGN_ROLES,
        Permission.RESOLVE_ESCALATIONS,
        Permission.VIEW_AUDIT_LOGS,
    },
    Role.FINANCE: {
        Permission.VIEW_TRIPS,
        Permission.VIEW_PAYMENTS,
        Permission.PROCESS_REFUNDS,
        Permission.EXPORT_FINANCIAL,
    },
    Role.FINANCE_ACCOUNTANT: {
        Permission.VIEW_TRIPS,
        Permission.VIEW_PAYMENTS,
        Permission.EXPORT_FINANCIAL,
    },
    Role.CUSTOMER_SUPPORT: {
        Permission.VIEW_TRIPS,
        Permission.ADD_TRIP_NOTES,
        Permission.VIEW_USERS,
        Permission.VIEW_NOTIFICATIONS,
        Permission.SEND_NOTIFICATIONS,
    },
    Role.OPERATIONS: {
        Permission.VIEW_TRIPS,
        Permission.MODIFY_TRIPS,
        Permission.RESOLVE_ESCALATIONS,
        Permission.VIEW_AUDIT_LOGS,
    },
    Role.MARKETING: {
        Permission.MANAGE_TEMPLATES,
        Permission.SEND_NOTIFICATIONS,
    },
    Role.ANALYST: {
        Permission.VIEW_TRIPS,
        Permission.VIEW_PAYMENTS,
        Permission.EXPORT_FINANCIAL,
        Permission.VIEW_AUDIT_LOGS,
    },
    Role.QA: {
        Permission.VIEW_TRIPS,
        Permission.VIEW_USERS,
    },
    Role.CONTENT_EDITOR: {
        Permission.MANAGE_TEMPLATES,
    },
    Role.ADMIN: {
        Permission.VIEW_TRIPS,
        Permission.MODIFY_TRIPS,
        Permission.ADD_TRIP_NOTES,
        Permission.VIEW_PAYMENTS,
        Permission.PROCESS_REFUNDS,
        Permission.EXPORT_FINANCIAL,
        Permission.MANAGE_FEES,
        Permission.MANAGE_PROMOS,
        Permission.MANAGE_TEMPLATES,
        Permission.VIEW_USERS,
        Permission.MANAGE_USERS,
        Permission.ASSIGN_ROLES,
        Permission.ASSIGN_ADMIN_ROLE,
        Permission.MANAGE_API_KEYS,
        Permission.MANAGE_INTEGRATIONS,
        Permission.VIEW_SYSTEM_SETTINGS,
        Permission.MODIFY_SYSTEM_SETTINGS,
        Permission.IMPERSONATE_USERS,
        Permission.VIEW_NOTIFICATIONS,
        Permission.SEND_NOTIFICATIONS,
        Permission.RESOLVE_ESCALATIONS,
        Permission.VIEW_AUDIT_LOGS,
    },
}


COMPANY_ROLE_PERMISSIONS: dict[CompanyRole, Set[CompanyPermission]] = {
    CompanyRole.ADMIN: {
        CompanyPermission.MANAGE_COMPANY,
        CompanyPermission.MANAGE_EMPLOYEES,
        CompanyPermission.VIEW_EMPLOYEES,
        CompanyPermission.SUBMIT_REQUESTS,
        CompanyPermission.APPROVE_LEVEL_ONE,
        CompanyPermission.APPROVE_FINANCE,
        CompanyPermission.MANAGE_POLICIES,
        CompanyPermission.MANAGE_BILLING,
        CompanyPermission.VIEW_REPORTS,
        CompanyPermission.VIEW_AUDIT_LOGS,
    },
    CompanyRole.MANAGER: {
        CompanyPermission.VIEW_EMPLOYEES,
        CompanyPermission.SUBMIT_REQUESTS,
        CompanyPermission.APPROVE_LEVEL_ONE,
        CompanyPermission.VIEW_REPORTS,
    },
    CompanyRole.FINANCE: {
        CompanyPermission.VIEW_EMPLOYEES,
        CompanyPermission.APPROVE_FINANCE,
        CompanyPermission.MANAGE_BILLING,
        CompanyPermission.VIEW_REPORTS,
        CompanyPermission.VIEW_AUDIT_LOGS,
    },
    CompanyRole.EMPLOYEE: {
        CompanyPermission.SUBMIT_REQUESTS,
    },
}


@dataclass
class User:
    """Authenticated user context."""
    id: int
    email: str
    name: str
    role: Role
    status: str
    company_id: int | None = None
    company_user_id: int | None = None
    company_role: CompanyRole | None = None
    permissions: Set[Permission] = field(default_factory=set)
    company_permissions: Set[CompanyPermission] = field(default_factory=set)


def get_role_permissions(role: Role | None) -> Set[Permission]:
    """Get all system permissions for a role."""
    if role is None:
        return set()
    return ROLE_PERMISSIONS.get(role, set())


def has_permission(user_role: Role, permission: Permission) -> bool:
    """Check if a system role has a specific permission."""
    return permission in ROLE_PERMISSIONS.get(user_role, set())


def has_any_permission(user_role: Role, permissions: List[Permission]) -> bool:
    """Check if a system role has any of the specified permissions."""
    role_perms = ROLE_PERMISSIONS.get(user_role, set())
    return any(perm in role_perms for perm in permissions)


def has_all_permissions(user_role: Role, permissions: List[Permission]) -> bool:
    """Check if a system role has all of the specified permissions."""
    role_perms = ROLE_PERMISSIONS.get(user_role, set())
    return all(perm in role_perms for perm in permissions)


def can_assign_role(assigner_role: Role, target_role: Role) -> bool:
    """Check if a user with assigner_role can assign target_role."""
    if assigner_role == Role.ADMIN:
        return True
    if assigner_role == Role.SUPERVISOR:
        return target_role != Role.ADMIN
    return False


def get_company_role_permissions(role: CompanyRole | None) -> Set[CompanyPermission]:
    """Get permissions granted to a company role."""
    if role is None:
        return set()
    return COMPANY_ROLE_PERMISSIONS.get(role, set())


def has_company_permission(role: CompanyRole | None, permission: CompanyPermission) -> bool:
    """Check if a company role has a specific permission."""
    if role is None:
        return False
    return permission in COMPANY_ROLE_PERMISSIONS.get(role, set())


def has_any_company_permission(role: CompanyRole | None, permissions: List[CompanyPermission]) -> bool:
    """Check if a company role has any of the specified permissions."""
    if role is None:
        return False
    role_perms = COMPANY_ROLE_PERMISSIONS.get(role, set())
    return any(perm in role_perms for perm in permissions)


def has_all_company_permissions(role: CompanyRole | None, permissions: List[CompanyPermission]) -> bool:
    """Check if a company role has all specified permissions."""
    if role is None:
        return False
    role_perms = COMPANY_ROLE_PERMISSIONS.get(role, set())
    return all(perm in role_perms for perm in permissions)

