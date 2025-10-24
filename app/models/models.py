from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Integer, Float, ForeignKey, JSON, DateTime, Text, Boolean, UniqueConstraint
from datetime import datetime
from app.db.session import Base

class Customer(Base):
    __tablename__ = "customers"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str | None] = mapped_column(String(255))
    phone: Mapped[str | None] = mapped_column(String(64))
    channel: Mapped[str | None] = mapped_column(String(32))
    external_id: Mapped[str | None] = mapped_column(String(128))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class Traveler(Base):
    __tablename__ = "travelers"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    customer_id: Mapped[int | None] = mapped_column(ForeignKey("customers.id"))
    title: Mapped[str | None] = mapped_column(String(16))
    first: Mapped[str] = mapped_column(String(100))
    last: Mapped[str] = mapped_column(String(100))
    dob: Mapped[str | None] = mapped_column(String(16))
    nationality: Mapped[str | None] = mapped_column(String(3))
    doc_hash: Mapped[str | None] = mapped_column(String(128))
    doc_last4: Mapped[str | None] = mapped_column(String(8))

class Quote(Base):
    __tablename__ = "quotes"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    offer_id: Mapped[str] = mapped_column(String(100))
    price_minor: Mapped[int] = mapped_column(Integer)
    currency: Mapped[str] = mapped_column(String(3))
    ngn_snapshot_rate: Mapped[str | None] = mapped_column(String(16))
    email: Mapped[str | None] = mapped_column(String(255))
    phone: Mapped[str | None] = mapped_column(String(64))
    channel: Mapped[str | None] = mapped_column(String(32))
    status: Mapped[str] = mapped_column(String(32))
    paystack_reference: Mapped[str | None] = mapped_column(String(100))
    raw_offer: Mapped[dict | None] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class Payment(Base):
    __tablename__ = "payments"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    quote_id: Mapped[int] = mapped_column(ForeignKey("quotes.id"))
    provider: Mapped[str] = mapped_column(String(32))
    reference: Mapped[str] = mapped_column(String(100))
    amount_minor: Mapped[int] = mapped_column(Integer)
    currency: Mapped[str] = mapped_column(String(3))
    method: Mapped[str | None] = mapped_column(String(32))
    status: Mapped[str] = mapped_column(String(32))
    raw: Mapped[dict | None] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class Trip(Base):
    __tablename__ = "trips"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    quote_id: Mapped[int] = mapped_column(ForeignKey("quotes.id"))
    supplier_order_id: Mapped[str | None] = mapped_column(String(100))
    pnr: Mapped[str | None] = mapped_column(String(16))
    etickets: Mapped[str | None] = mapped_column(Text)  # CSV fallback
    etickets_json: Mapped[list | None] = mapped_column(JSON)
    email: Mapped[str | None] = mapped_column(String(255))
    phone: Mapped[str | None] = mapped_column(String(64))
    status: Mapped[str | None] = mapped_column(String(32))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    raw_order: Mapped[dict | None] = mapped_column(JSON)

class Ancillary(Base):
    __tablename__ = "ancillaries"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    trip_id: Mapped[int] = mapped_column(ForeignKey("trips.id"))
    type: Mapped[str] = mapped_column(String(16))
    amount_minor: Mapped[int] = mapped_column(Integer)
    currency: Mapped[str] = mapped_column(String(3))
    details: Mapped[dict | None] = mapped_column(JSON)

class AuditLog(Base):
    __tablename__ = "audit_logs"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    event: Mapped[str] = mapped_column(String(64))
    actor: Mapped[str] = mapped_column(String(64))
    details: Mapped[dict | None] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class MessagingSettings(Base):
    __tablename__ = "messaging_settings"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    welcome_subject: Mapped[str | None] = mapped_column(String(255))
    welcome_body: Mapped[str | None] = mapped_column(Text)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class PricingConfig(Base):
    __tablename__ = "pricing_config"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    base_pricing_currency: Mapped[str] = mapped_column(String(3), default="USD")
    default_display_currency: Mapped[str] = mapped_column(String(3), default="NGN")
    markup_percentage: Mapped[float] = mapped_column(Float)  # e.g., 10 -> 10%
    booking_fee_fixed: Mapped[int] = mapped_column(Integer)
    payment_fee_percentage: Mapped[float] = mapped_column(Float)
    fx_safety_margin_pct: Mapped[float] = mapped_column(Float, default=4.0)
    supported_currencies: Mapped[list | None] = mapped_column(JSON)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class PricingAudit(Base):
    __tablename__ = "pricing_audit"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    event_date: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    base_currency: Mapped[str] = mapped_column(String(3))
    display_currency: Mapped[str] = mapped_column(String(3))
    raw_rate: Mapped[float] = mapped_column(Float)
    effective_rate: Mapped[float] = mapped_column(Float)
    margin_pct: Mapped[float] = mapped_column(Float)
    source: Mapped[str | None] = mapped_column(String(32))
    context: Mapped[dict | None] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(255))
    name: Mapped[str | None] = mapped_column(String(100))
    role: Mapped[str] = mapped_column(String(32))
    hash_password: Mapped[str] = mapped_column(String(255))
    status: Mapped[str] = mapped_column(String(32))


class LoyaltyAccount(Base):
    __tablename__ = "loyalty_accounts"
    __table_args__ = (UniqueConstraint("user_id", "airline_iata_code", name="uq_loyalty_user_airline"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    airline_iata_code: Mapped[str] = mapped_column(String(8), nullable=False)
    programme_name: Mapped[str | None] = mapped_column(String(128))
    loyalty_programme_id: Mapped[str | None] = mapped_column(String(64))
    account_number_encrypted: Mapped[str] = mapped_column(Text, nullable=False)
    account_number_last4: Mapped[str] = mapped_column(String(8), nullable=False)
    loyalty_tier: Mapped[str | None] = mapped_column(String(64))
    perks_snapshot: Mapped[dict | None] = mapped_column(JSON)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Fee(Base):
    __tablename__ = "fees"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    rule: Mapped[dict | None] = mapped_column(JSON)
    flat_minor: Mapped[int | None] = mapped_column(Integer)
    percent: Mapped[float | None] = mapped_column()

class Cancellation(Base):
    __tablename__ = "cancellations"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    trip_id: Mapped[int] = mapped_column(ForeignKey("trips.id"))
    quote_id: Mapped[int] = mapped_column(ForeignKey("quotes.id"))
    reason: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(32))
    refund_amount_minor: Mapped[int | None] = mapped_column(Integer)
    refund_currency: Mapped[str | None] = mapped_column(String(3))
    refund_status: Mapped[str | None] = mapped_column(String(32))
    refund_reference: Mapped[str | None] = mapped_column(String(100))
    supplier_cancellation_id: Mapped[str | None] = mapped_column(String(100))
    cancelled_by: Mapped[str | None] = mapped_column(String(64))
    raw_cancellation: Mapped[dict | None] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime)

class PasswordResetToken(Base):
    __tablename__ = "password_reset_tokens"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    token: Mapped[str] = mapped_column(String(255))
    expires_at: Mapped[datetime] = mapped_column(DateTime)
    used: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class PromoCode(Base):
    __tablename__ = "promo_codes"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    code: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    description: Mapped[str | None] = mapped_column(String(255))
    discount_type: Mapped[str] = mapped_column(String(20))  # 'percentage' or 'fixed'
    discount_value: Mapped[float] = mapped_column()  # percentage (e.g., 10 for 10%) or fixed amount
    currency: Mapped[str | None] = mapped_column(String(3))  # for fixed discounts
    max_uses: Mapped[int | None] = mapped_column(Integer)  # null = unlimited
    times_used: Mapped[int] = mapped_column(Integer, default=0)
    min_purchase_amount: Mapped[float | None] = mapped_column()  # minimum booking amount
    valid_from: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    valid_until: Mapped[datetime | None] = mapped_column(DateTime)
    is_active: Mapped[bool] = mapped_column(default=True)
    created_by: Mapped[str | None] = mapped_column(String(100))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class PromoCodeUsage(Base):
    __tablename__ = "promo_code_usage"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    promo_code_id: Mapped[int] = mapped_column(ForeignKey("promo_codes.id"))
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    trip_id: Mapped[int | None] = mapped_column(ForeignKey("trips.id"))
    discount_amount: Mapped[float] = mapped_column()
    original_amount: Mapped[float] = mapped_column()
    final_amount: Mapped[float] = mapped_column()
    used_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class Company(Base):
    __tablename__ = "companies"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    slug: Mapped[str] = mapped_column(String(120), unique=True)
    domain: Mapped[str | None] = mapped_column(String(255))
    country: Mapped[str | None] = mapped_column(String(2))
    currency: Mapped[str | None] = mapped_column(String(3))
    status: Mapped[str] = mapped_column(String(32), default="active")
    settings: Mapped[dict | None] = mapped_column(JSON)
    payment_preferences: Mapped[dict | None] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class CompanyUser(Base):
    __tablename__ = "company_users"
    __table_args__ = (
        UniqueConstraint("company_id", "user_id", name="uq_company_user_membership"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id", ondelete="CASCADE"))
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    role: Mapped[str] = mapped_column(String(32))
    department_id: Mapped[int | None] = mapped_column(ForeignKey("company_departments.id"))
    title: Mapped[str | None] = mapped_column(String(128))
    status: Mapped[str] = mapped_column(String(32), default="active")
    locale: Mapped[str | None] = mapped_column(String(8))
    cost_center_code: Mapped[str | None] = mapped_column(String(64))
    invited_at: Mapped[datetime | None] = mapped_column(DateTime)
    joined_at: Mapped[datetime | None] = mapped_column(DateTime)
    last_seen_at: Mapped[datetime | None] = mapped_column(DateTime)
    extra: Mapped[dict | None] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class CompanyDepartment(Base):
    __tablename__ = "company_departments"
    __table_args__ = (
        UniqueConstraint("company_id", "code", name="uq_department_code_per_company"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(String(128))
    code: Mapped[str | None] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class CompanyInvitation(Base):
    __tablename__ = "company_invitations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id", ondelete="CASCADE"))
    inviter_company_user_id: Mapped[int | None] = mapped_column(ForeignKey("company_users.id"))
    email: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(32))
    department_id: Mapped[int | None] = mapped_column(ForeignKey("company_departments.id"))
    token: Mapped[str] = mapped_column(String(120), unique=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime)
    status: Mapped[str] = mapped_column(String(32), default="pending")
    payload: Mapped[dict | None] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class TravelPolicy(Base):
    __tablename__ = "travel_policies"
    __table_args__ = (
        UniqueConstraint("company_id", "name", name="uq_policy_name_per_company"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(String(150))
    description: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(32), default="active")
    require_manager_approval: Mapped[bool] = mapped_column(Boolean, default=True)
    require_finance_approval: Mapped[bool] = mapped_column(Boolean, default=False)
    auto_ticketing_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    max_budget_minor: Mapped[int | None] = mapped_column(Integer)
    currency: Mapped[str | None] = mapped_column(String(3))
    allowed_cabin_classes: Mapped[list | None] = mapped_column(JSON)
    restricted_routes: Mapped[list | None] = mapped_column(JSON)
    preferred_airlines: Mapped[list | None] = mapped_column(JSON)
    excluded_airlines: Mapped[list | None] = mapped_column(JSON)
    advance_purchase_days: Mapped[int | None] = mapped_column(Integer)
    rules: Mapped[dict | None] = mapped_column(JSON)
    approval_flow: Mapped[list | None] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class TravelRequest(Base):
    __tablename__ = "travel_requests"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id", ondelete="CASCADE"))
    employee_company_user_id: Mapped[int] = mapped_column(ForeignKey("company_users.id", ondelete="CASCADE"))
    policy_id: Mapped[int | None] = mapped_column(ForeignKey("travel_policies.id"))
    reference: Mapped[str] = mapped_column(String(64), unique=True)
    status: Mapped[str] = mapped_column(String(32), default="draft")
    trip_type: Mapped[str | None] = mapped_column(String(32))
    origin: Mapped[str | None] = mapped_column(String(8))
    destination: Mapped[str | None] = mapped_column(String(8))
    departure_date: Mapped[datetime | None] = mapped_column(DateTime)
    return_date: Mapped[datetime | None] = mapped_column(DateTime)
    justification: Mapped[str | None] = mapped_column(Text)
    traveler_count: Mapped[int] = mapped_column(Integer, default=1)
    budget_minor: Mapped[int | None] = mapped_column(Integer)
    currency: Mapped[str | None] = mapped_column(String(3))
    policy_snapshot: Mapped[dict | None] = mapped_column(JSON)
    requested_itineraries: Mapped[list | None] = mapped_column(JSON)
    offer_snapshot: Mapped[dict | None] = mapped_column(JSON)
    approval_state: Mapped[dict | None] = mapped_column(JSON)
    custom_fields: Mapped[dict | None] = mapped_column(JSON)
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime)
    approved_at: Mapped[datetime | None] = mapped_column(DateTime)
    rejected_at: Mapped[datetime | None] = mapped_column(DateTime)
    cancelled_at: Mapped[datetime | None] = mapped_column(DateTime)
    booked_trip_id: Mapped[int | None] = mapped_column(ForeignKey("trips.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class TravelApproval(Base):
    __tablename__ = "travel_approvals"
    __table_args__ = (
        UniqueConstraint("travel_request_id", "level", "approver_company_user_id", name="uq_approval_unique"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    travel_request_id: Mapped[int] = mapped_column(ForeignKey("travel_requests.id", ondelete="CASCADE"))
    level: Mapped[int] = mapped_column(Integer)
    approver_company_user_id: Mapped[int] = mapped_column(ForeignKey("company_users.id", ondelete="CASCADE"))
    status: Mapped[str] = mapped_column(String(32), default="pending")
    decision: Mapped[str | None] = mapped_column(String(32))
    decided_at: Mapped[datetime | None] = mapped_column(DateTime)
    comment: Mapped[str | None] = mapped_column(Text)
    context: Mapped[dict | None] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class TravelRequestComment(Base):
    __tablename__ = "travel_request_comments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    travel_request_id: Mapped[int] = mapped_column(ForeignKey("travel_requests.id", ondelete="CASCADE"))
    author_company_user_id: Mapped[int] = mapped_column(ForeignKey("company_users.id", ondelete="CASCADE"))
    visibility: Mapped[str] = mapped_column(String(16), default="internal")
    body: Mapped[str] = mapped_column(Text)
    extra: Mapped[dict | None] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
