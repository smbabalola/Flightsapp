"""Tests for B2B multi-tenant workflows."""
import uuid

from app.db.session import SessionLocal, Base, engine
from app.services.company_service import CompanyService
from app.services.travel_request_service import TravelRequestService
from app.repositories.company_repo import CompanyRepository
from app.repositories.travel_request_repo import TravelRequestRepository
from app.models.models import TravelPolicy
from sqlalchemy import text
from sqlalchemy import text

Base.metadata.create_all(bind=engine)


class TestCompanyService:
    def test_onboard_company_creates_default_policy(self):
        db = SessionLocal()
        company_service = CompanyService(db)
        unique_suffix = uuid.uuid4().hex[:6]
        try:
            result = company_service.create_company_with_admin(
                name=f"Test Corp {unique_suffix}",
                slug=None,
                domain="testcorp.example",
                country="NG",
                currency="NGN",
                admin_email=f"admin_{unique_suffix}@example.com",
                admin_name="Test Admin",
                admin_password="SecurePass123",
            )
            company = result["company"]
            policy = result["default_policy"]

            assert company.id is not None
            assert company.slug.startswith("test-corp")
            assert policy.company_id == company.id
            assert policy.require_manager_approval is True
        finally:
            db.rollback()
            db.close()


class TestTravelRequestWorkflow:
    def test_multi_level_approval(self):
        db = SessionLocal()
        company_service = CompanyService(db)
        company_repo = CompanyRepository(db)
        unique_suffix = uuid.uuid4().hex[:6]
        try:
            onboarding = company_service.create_company_with_admin(
                name=f"Traveler Co {unique_suffix}",
                slug=None,
                domain="travelers.example",
                country="NG",
                currency="NGN",
                admin_email=f"owner_{unique_suffix}@example.com",
                admin_name="Owner Name",
                admin_password="StrongPass123",
            )
            company = onboarding["company"]
            default_policy = onboarding["default_policy"]
            policy = TravelPolicy(
                company_id=company.id,
                name=f"Finance Policy {unique_suffix}",
                status="active",
                require_manager_approval=True,
                require_finance_approval=True,
            )
            db.add(policy)
            db.flush()
            db.refresh(policy)
            admin_membership = onboarding["membership"]

            manager_user_id = company_service._create_user(
                email=f"manager_{unique_suffix}@example.com",
                name="Manager",
                password="AnotherPass123",
            )
            manager_membership = company_repo.create_company_user(
                company_id=company.id,
                user_id=manager_user_id,
                role="manager",
            )

            finance_user_id = company_service._create_user(
                email=f"finance_{unique_suffix}@example.com",
                name="Finance",
                password="AnotherPass123",
            )
            finance_membership = company_repo.create_company_user(
                company_id=company.id,
                user_id=finance_user_id,
                role="finance",
            )

            members = company_repo.list_company_members(company.id)
            roles = {row["role"] for row in members}
            assert "finance" in roles
            assert "manager" in roles


            travel_service = TravelRequestService(db)
            travel_request = travel_service.create_request(
                company_id=company.id,
                employee_company_user_id=admin_membership.id,
                policy_id=policy.id,
                trip_type="one_way",
                origin="LOS",
                destination="ABV",
                departure_date=None,
                return_date=None,
                justification="Client meeting",
                traveler_count=1,
                budget_minor=150000,
                currency="NGN",
                requested_itineraries=[],
                offer_snapshot={},
            )

            travel_service.submit_request(
                company_id=company.id,
                request_id=travel_request.id,
                submitter_company_user_id=admin_membership.id,
            )

            repo = TravelRequestRepository(db)
            resolved_policy = travel_service._resolve_policy(company.id, policy.id)
            assert resolved_policy.require_finance_approval is True
            approvals = repo.list_approvals(travel_request.id)
            approver_ids = {approval.approver_company_user_id for approval in approvals}
            approval_snapshot = [(approval.approver_company_user_id, approval.level) for approval in approvals]
            assert any(level == 2 for _, level in approval_snapshot), approval_snapshot

            approver_ids = {approval.approver_company_user_id for approval in approvals}
            assert manager_membership.id in approver_ids
            assert finance_membership.id in approver_ids

            db.refresh(travel_request)
            assert travel_request.status == "pending_approval"

            travel_service.approve_request(
                company_id=company.id,
                request_id=travel_request.id,
                approver_company_user_id=manager_membership.id,
                comment="Looks good",
            )
            travel_service.approve_request(
                company_id=company.id,
                request_id=travel_request.id,
                approver_company_user_id=finance_membership.id,
                comment="Budget available",
            )
            db.refresh(travel_request)
            assert travel_request.status == "approved"
            assert travel_request.approved_at is not None
        finally:
            db.rollback()
            db.close()
