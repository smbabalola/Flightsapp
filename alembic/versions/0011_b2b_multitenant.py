"""add b2b multi-tenant tables

Revision ID: 0011_b2b_multitenant
Revises: 0010_loyalty_accounts
Create Date: 2025-10-05
"""

from alembic import op
import sqlalchemy as sa


revision = "0011_b2b_multitenant"
down_revision = "0010_loyalty_accounts"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "companies",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("slug", sa.String(length=120), nullable=False, unique=True),
        sa.Column("domain", sa.String(length=255), nullable=True),
        sa.Column("country", sa.String(length=2), nullable=True),
        sa.Column("currency", sa.String(length=3), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False, server_default=sa.text("'active'")),
        sa.Column("settings", sa.JSON(), nullable=True),
        sa.Column("payment_preferences", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_companies_status", "companies", ["status"])

    op.create_table(
        "company_departments",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("company_id", sa.Integer, sa.ForeignKey("companies.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(length=128), nullable=False),
        sa.Column("code", sa.String(length=64), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("company_id", "code", name="uq_department_code_per_company"),
    )
    op.create_index("ix_company_departments_company", "company_departments", ["company_id"])

    op.create_table(
        "company_users",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("company_id", sa.Integer, sa.ForeignKey("companies.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", sa.Integer, sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("role", sa.String(length=32), nullable=False),
        sa.Column("department_id", sa.Integer, sa.ForeignKey("company_departments.id"), nullable=True),
        sa.Column("title", sa.String(length=128), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False, server_default=sa.text("'active'")),
        sa.Column("locale", sa.String(length=8), nullable=True),
        sa.Column("cost_center_code", sa.String(length=64), nullable=True),
        sa.Column("invited_at", sa.DateTime(), nullable=True),
        sa.Column("joined_at", sa.DateTime(), nullable=True),
        sa.Column("last_seen_at", sa.DateTime(), nullable=True),
        sa.Column("metadata", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("company_id", "user_id", name="uq_company_user_membership"),
    )
    op.create_index("ix_company_users_company", "company_users", ["company_id"])
    op.create_index("ix_company_users_user", "company_users", ["user_id"])
    op.create_index("ix_company_users_role", "company_users", ["role"])

    op.create_table(
        "company_invitations",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("company_id", sa.Integer, sa.ForeignKey("companies.id", ondelete="CASCADE"), nullable=False),
        sa.Column("inviter_company_user_id", sa.Integer, sa.ForeignKey("company_users.id"), nullable=True),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("role", sa.String(length=32), nullable=False),
        sa.Column("department_id", sa.Integer, sa.ForeignKey("company_departments.id"), nullable=True),
        sa.Column("token", sa.String(length=120), nullable=False, unique=True),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False, server_default=sa.text("'pending'")),
        sa.Column("metadata", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_company_invitations_company", "company_invitations", ["company_id"])
    op.create_index("ix_company_invitations_status", "company_invitations", ["status"])
    op.create_index("ix_company_invitations_email", "company_invitations", ["email"])

    op.create_table(
        "travel_policies",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("company_id", sa.Integer, sa.ForeignKey("companies.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(length=150), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False, server_default=sa.text("'active'")),
        sa.Column("require_manager_approval", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("require_finance_approval", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("auto_ticketing_enabled", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("max_budget_minor", sa.Integer(), nullable=True),
        sa.Column("currency", sa.String(length=3), nullable=True),
        sa.Column("allowed_cabin_classes", sa.JSON(), nullable=True),
        sa.Column("restricted_routes", sa.JSON(), nullable=True),
        sa.Column("preferred_airlines", sa.JSON(), nullable=True),
        sa.Column("excluded_airlines", sa.JSON(), nullable=True),
        sa.Column("advance_purchase_days", sa.Integer(), nullable=True),
        sa.Column("rules", sa.JSON(), nullable=True),
        sa.Column("approval_flow", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("company_id", "name", name="uq_policy_name_per_company"),
    )
    op.create_index("ix_travel_policies_company", "travel_policies", ["company_id"])
    op.create_index("ix_travel_policies_status", "travel_policies", ["status"])

    op.create_table(
        "travel_requests",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("company_id", sa.Integer, sa.ForeignKey("companies.id", ondelete="CASCADE"), nullable=False),
        sa.Column("employee_company_user_id", sa.Integer, sa.ForeignKey("company_users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("policy_id", sa.Integer, sa.ForeignKey("travel_policies.id"), nullable=True),
        sa.Column("reference", sa.String(length=64), nullable=False, unique=True),
        sa.Column("status", sa.String(length=32), nullable=False, server_default=sa.text("'draft'")),
        sa.Column("trip_type", sa.String(length=32), nullable=True),
        sa.Column("origin", sa.String(length=8), nullable=True),
        sa.Column("destination", sa.String(length=8), nullable=True),
        sa.Column("departure_date", sa.DateTime(), nullable=True),
        sa.Column("return_date", sa.DateTime(), nullable=True),
        sa.Column("justification", sa.Text(), nullable=True),
        sa.Column("traveler_count", sa.Integer(), nullable=False, server_default=sa.text('1')),
        sa.Column("budget_minor", sa.Integer(), nullable=True),
        sa.Column("currency", sa.String(length=3), nullable=True),
        sa.Column("policy_snapshot", sa.JSON(), nullable=True),
        sa.Column("requested_itineraries", sa.JSON(), nullable=True),
        sa.Column("offer_snapshot", sa.JSON(), nullable=True),
        sa.Column("approval_state", sa.JSON(), nullable=True),
        sa.Column("metadata", sa.JSON(), nullable=True),
        sa.Column("submitted_at", sa.DateTime(), nullable=True),
        sa.Column("approved_at", sa.DateTime(), nullable=True),
        sa.Column("rejected_at", sa.DateTime(), nullable=True),
        sa.Column("cancelled_at", sa.DateTime(), nullable=True),
        sa.Column("booked_trip_id", sa.Integer(), sa.ForeignKey("trips.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_travel_requests_company", "travel_requests", ["company_id"])
    op.create_index("ix_travel_requests_status", "travel_requests", ["status"])
    op.create_index("ix_travel_requests_employee", "travel_requests", ["employee_company_user_id"])

    op.create_table(
        "travel_approvals",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("travel_request_id", sa.Integer, sa.ForeignKey("travel_requests.id", ondelete="CASCADE"), nullable=False),
        sa.Column("level", sa.Integer(), nullable=False),
        sa.Column("approver_company_user_id", sa.Integer, sa.ForeignKey("company_users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False, server_default=sa.text("'pending'")),
        sa.Column("decision", sa.String(length=32), nullable=True),
        sa.Column("decided_at", sa.DateTime(), nullable=True),
        sa.Column("comment", sa.Text(), nullable=True),
        sa.Column("metadata", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("travel_request_id", "level", "approver_company_user_id", name="uq_approval_unique"),
    )
    op.create_index("ix_travel_approvals_request", "travel_approvals", ["travel_request_id"])
    op.create_index("ix_travel_approvals_approver", "travel_approvals", ["approver_company_user_id"])
    op.create_index("ix_travel_approvals_status", "travel_approvals", ["status"])

    op.create_table(
        "travel_request_comments",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("travel_request_id", sa.Integer, sa.ForeignKey("travel_requests.id", ondelete="CASCADE"), nullable=False),
        sa.Column("author_company_user_id", sa.Integer, sa.ForeignKey("company_users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("visibility", sa.String(length=16), nullable=False, server_default=sa.text("'internal'")),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("metadata", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_travel_request_comments_request", "travel_request_comments", ["travel_request_id"])
    op.create_index("ix_travel_request_comments_author", "travel_request_comments", ["author_company_user_id"])


def downgrade():
    op.drop_index("ix_travel_request_comments_author", table_name="travel_request_comments")
    op.drop_index("ix_travel_request_comments_request", table_name="travel_request_comments")
    op.drop_table("travel_request_comments")

    op.drop_index("ix_travel_approvals_status", table_name="travel_approvals")
    op.drop_index("ix_travel_approvals_approver", table_name="travel_approvals")
    op.drop_index("ix_travel_approvals_request", table_name="travel_approvals")
    op.drop_table("travel_approvals")

    op.drop_index("ix_travel_requests_employee", table_name="travel_requests")
    op.drop_index("ix_travel_requests_status", table_name="travel_requests")
    op.drop_index("ix_travel_requests_company", table_name="travel_requests")
    op.drop_table("travel_requests")

    op.drop_index("ix_travel_policies_status", table_name="travel_policies")
    op.drop_index("ix_travel_policies_company", table_name="travel_policies")
    op.drop_table("travel_policies")

    op.drop_index("ix_company_invitations_email", table_name="company_invitations")
    op.drop_index("ix_company_invitations_status", table_name="company_invitations")
    op.drop_index("ix_company_invitations_company", table_name="company_invitations")
    op.drop_table("company_invitations")

    op.drop_index("ix_company_users_role", table_name="company_users")
    op.drop_index("ix_company_users_user", table_name="company_users")
    op.drop_index("ix_company_users_company", table_name="company_users")
    op.drop_table("company_users")

    op.drop_index("ix_company_departments_company", table_name="company_departments")
    op.drop_table("company_departments")

    op.drop_index("ix_companies_status", table_name="companies")
    op.drop_table("companies")
