"""
Admin Dashboard Routes

Provides web UI for managing trips, bookings, fees, and viewing analytics.
"""
from fastapi import APIRouter, Request, Depends, HTTPException, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from typing import Optional
import secrets
from datetime import datetime, timedelta
from sqlalchemy import text, func
from app.integrations.email_notifier import send_welcome_email
import structlog

from app.core.settings import get_settings
from app.utils.cache import Cache
from app.db.session import SessionLocal
from app.services.promo_code_service import PromoCodeService
from app.models.models import PromoCode, PricingConfig
from app.auth.permissions import Role
from sqlalchemy import text

logger = structlog.get_logger(__name__)
router = APIRouter()
templates = Jinja2Templates(directory="templates")
security = HTTPBasic()


def verify_admin(credentials: HTTPBasicCredentials = Depends(security)):
    """Verify admin credentials using HTTP Basic Auth."""
    settings = get_settings()

    correct_username = secrets.compare_digest(
        credentials.username.encode("utf8"),
        (settings.admin_user or "admin").encode("utf8")
    )
    correct_password = secrets.compare_digest(
        credentials.password.encode("utf8"),
        (settings.admin_pass or "change_me").encode("utf8")
    )

    if not (correct_username and correct_password):
        raise HTTPException(
            status_code=401,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Basic"},
        )

    return credentials.username


@router.get("/", response_class=HTMLResponse)
async def dashboard_home(
    request: Request,
    admin: str = Depends(verify_admin)
):
    """Main dashboard page with analytics overview."""

    with SessionLocal() as db:
        # Get total bookings
        total_bookings = db.execute(
            text("SELECT COUNT(*) FROM quotes WHERE status != 'draft'")
        ).scalar() or 0

        # Get paid bookings
        paid_bookings = db.execute(
            text("SELECT COUNT(*) FROM quotes WHERE status = 'paid'")
        ).scalar() or 0

        # Get total revenue (from payments table)
        total_revenue = db.execute(
            text("""
                SELECT COALESCE(SUM(CAST(json_extract(raw, '$.data.amount') AS FLOAT)), 0) / 100
                FROM payments
                WHERE status = 'succeeded'
            """)
        ).scalar() or 0

        # Get recent bookings (last 10)
        recent_bookings = db.execute(
            text("""
                SELECT
                    id,
                    pnr,
                    status,
                    total_price_ngn,
                    created_at
                FROM quotes
                WHERE status != 'draft'
                ORDER BY created_at DESC
                LIMIT 10
            """)
        ).fetchall()

        # Get today's stats
        today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        today_bookings = db.execute(
            text("""
                SELECT COUNT(*) FROM quotes
                WHERE status != 'draft'
                AND created_at >= :today
            """),
            {"today": today_start.isoformat()}
        ).scalar() or 0

    return templates.TemplateResponse(
        "admin_dashboard.html",
        {
            "request": request,
            "admin_user": admin,
            "total_bookings": total_bookings,
            "paid_bookings": paid_bookings,
            "pending_bookings": total_bookings - paid_bookings,
            "total_revenue": total_revenue,
            "today_bookings": today_bookings,
            "recent_bookings": recent_bookings,
        }
    )


@router.get("/trips", response_class=HTMLResponse)
async def trips_list(
    request: Request,
    page: int = 1,
    limit: int = 20,
    status: Optional[str] = None,
    admin: str = Depends(verify_admin)
):
    """Trip/booking management page with search and filters."""

    offset = (page - 1) * limit

    with SessionLocal() as db:
        # Build query based on filters
        where_clause = "WHERE status != 'draft'"
        params = {"limit": limit, "offset": offset}

        if status:
            where_clause += " AND status = :status"
            params["status"] = status

        # Get trips
        trips = db.execute(
            text(f"""
                SELECT
                    id,
                    pnr,
                    offer_id,
                    status,
                    total_price_ngn,
                    currency,
                    route_summary,
                    paystack_reference,
                    created_at
                FROM quotes
                {where_clause}
                ORDER BY created_at DESC
                LIMIT :limit OFFSET :offset
            """),
            params
        ).fetchall()

        # Get total count
        total_count = db.execute(
            text(f"SELECT COUNT(*) FROM quotes {where_clause}"),
            {k: v for k, v in params.items() if k not in ['limit', 'offset']}
        ).scalar() or 0

    total_pages = (total_count + limit - 1) // limit

    return templates.TemplateResponse(
        "admin_trips.html",
        {
            "request": request,
            "admin_user": admin,
            "trips": trips,
            "page": page,
            "total_pages": total_pages,
            "status_filter": status,
        }
    )


@router.get("/trips/{trip_id}", response_class=HTMLResponse)
async def trip_detail(
    request: Request,
    trip_id: int,
    admin: str = Depends(verify_admin)
):
    """Detailed view of a single trip/booking."""

    with SessionLocal() as db:
        # Get trip details
        trip = db.execute(
            text("""
                SELECT
                    id,
                    pnr,
                    offer_id,
                    status,
                    total_price_ngn,
                    currency,
                    route_summary,
                    passenger_info,
                    email as contact_email,
                    phone as contact_phone,
                    paystack_reference,
                    created_at,
                    updated_at
                FROM quotes
                WHERE id = :trip_id
            """),
            {"trip_id": trip_id}
        ).fetchone()

        if not trip:
            raise HTTPException(status_code=404, detail="Trip not found")

        # Get associated payment
        payment = db.execute(
            text("""
                SELECT
                    id,
                    reference,
                    amount_ngn,
                    status,
                    created_at
                FROM payments
                WHERE reference = :ref
            """),
            {"ref": trip.paystack_reference}
        ).fetchone()

    return templates.TemplateResponse(
        "admin_trip_detail.html",
        {
            "request": request,
            "admin_user": admin,
            "trip": trip,
            "payment": payment,
        }
    )


@router.get("/fees", response_class=HTMLResponse)
async def fees_config(
    request: Request,
    admin: str = Depends(verify_admin)
):
    """Fee configuration interface."""

    # Load current fees from database or config
    with SessionLocal() as db:
        cfg = db.query(PricingConfig).order_by(PricingConfig.id.asc()).first()
        if not cfg:
            cfg = PricingConfig(
                base_pricing_currency="USD",
                default_display_currency="NGN",
                markup_percentage=10.0,
                booking_fee_fixed=5000,
                payment_fee_percentage=1.5,
                fx_safety_margin_pct=4.0,
            )
            db.add(cfg)
            db.commit()
            db.refresh(cfg)

    return templates.TemplateResponse(
        "admin_fees.html",
        {
            "request": request,
            "admin_user": admin,
            "current_fees": {
                "base_pricing_currency": cfg.base_pricing_currency,
                "default_display_currency": cfg.default_display_currency,
                "markup_percentage": cfg.markup_percentage,
                "booking_fee_fixed": cfg.booking_fee_fixed,
                "payment_fee_percentage": cfg.payment_fee_percentage,
                "fx_safety_margin_pct": cfg.fx_safety_margin_pct,
            },
        }
    )


@router.post("/cache/purge-search")
async def purge_search_cache(admin: str = Depends(verify_admin)):
    """Purge all cached Duffel search results (keys with prefix duffel:offers:)."""
    settings = get_settings()
    cache = Cache(settings.redis_url)
    deleted = cache.delete_prefix("duffel:offers:")
    return {"message": "purged", "deleted": deleted}


@router.post("/fees", response_class=HTMLResponse)
async def update_fees(
    request: Request,
    base_pricing_currency: str = Form(...),
    default_display_currency: str = Form(...),
    markup_percentage: float = Form(...),
    booking_fee_fixed: int = Form(...),
    payment_fee_percentage: float = Form(...),
    fx_safety_margin_pct: float = Form(...),
    admin: str = Depends(verify_admin)
):
    """Update fee configuration."""

    with SessionLocal() as db:
        cfg = db.query(PricingConfig).order_by(PricingConfig.id.asc()).first()
        if not cfg:
            cfg = PricingConfig()
            db.add(cfg)

        cfg.base_pricing_currency = (base_pricing_currency or "USD").upper()
        cfg.default_display_currency = (default_display_currency or "NGN").upper()
        cfg.markup_percentage = float(markup_percentage)
        cfg.booking_fee_fixed = int(booking_fee_fixed)
        cfg.payment_fee_percentage = float(payment_fee_percentage)
        cfg.fx_safety_margin_pct = float(fx_safety_margin_pct)

        db.commit()

    logger.info(
        "fees_updated",
        admin=admin,
        cfg={
            "base_pricing_currency": base_pricing_currency,
            "default_display_currency": default_display_currency,
            "markup_percentage": markup_percentage,
            "booking_fee_fixed": booking_fee_fixed,
            "payment_fee_percentage": payment_fee_percentage,
            "fx_safety_margin_pct": fx_safety_margin_pct,
        }
    )

    return RedirectResponse(url="/admin/fees?updated=true", status_code=303)


@router.get("/promo-codes", response_class=HTMLResponse)
async def promo_codes_list(
    request: Request,
    admin: str = Depends(verify_admin)
):
    """Promo code management page."""

    with SessionLocal() as db:
        # Get all promo codes
        promo_codes = db.query(PromoCode).order_by(PromoCode.created_at.desc()).all()

        return templates.TemplateResponse(
            "admin_promo_codes.html",
            {
                "request": request,
                "admin_user": admin,
                "promo_codes": promo_codes,
            }
        )


@router.post("/promo-codes", response_class=HTMLResponse)
async def create_promo_code(
    request: Request,
    code: str = Form(...),
    description: Optional[str] = Form(None),
    discount_type: str = Form(...),
    discount_value: float = Form(...),
    currency: Optional[str] = Form(None),
    max_uses: Optional[int] = Form(None),
    min_purchase_amount: Optional[float] = Form(None),
    valid_until: Optional[str] = Form(None),
    admin: str = Depends(verify_admin)
):
    """Create a new promo code."""

    with SessionLocal() as db:
        try:
            # Parse valid_until if provided
            valid_until_dt = None
            if valid_until:
                try:
                    valid_until_dt = datetime.fromisoformat(valid_until)
                except ValueError:
                    pass

            # Create promo code
            promo = PromoCodeService.create_promo_code(
                db=db,
                code=code,
                description=description,
                discount_type=discount_type,
                discount_value=discount_value,
                currency=currency if discount_type == "fixed" else None,
                max_uses=max_uses,
                min_purchase_amount=min_purchase_amount,
                valid_until=valid_until_dt,
                created_by=admin
            )

            logger.info(
                "promo_code_created",
                admin=admin,
                code=promo.code,
                discount_type=discount_type,
                discount_value=discount_value
            )

            return RedirectResponse(url="/admin/promo-codes?created=true", status_code=303)

        except Exception as e:
            logger.error("promo_code_creation_failed", error=str(e))
            raise HTTPException(status_code=400, detail=str(e))


@router.post("/promo-codes/{code}/deactivate")
async def deactivate_promo_code(
    code: str,
    admin: str = Depends(verify_admin)
):
    """Deactivate a promo code."""

    with SessionLocal() as db:
        success = PromoCodeService.deactivate_promo_code(db, code)

        if not success:
            raise HTTPException(status_code=404, detail="Promo code not found")

        logger.info("promo_code_deactivated", admin=admin, code=code)

    return RedirectResponse(url="/admin/promo-codes", status_code=303)


@router.get("/messaging", response_class=HTMLResponse)
async def messaging_get(
    request: Request,
    admin: str = Depends(verify_admin)
):
    with SessionLocal() as db:
        row = db.execute(text("SELECT id, welcome_subject, welcome_body FROM messaging_settings ORDER BY id ASC LIMIT 1")).fetchone()
        settings = {
            "welcome_subject": (row.welcome_subject if row else "Welcome to {{APP_NAME}}!"),
            "welcome_body": (row.welcome_body if row else ""),
        }
    return templates.TemplateResponse("admin_messaging.html", {"request": request, "admin_user": admin, "settings": settings})


@router.post("/messaging", response_class=HTMLResponse)
async def messaging_post(
    request: Request,
    welcome_subject: str = Form(...),
    welcome_body: str = Form(...),
    admin: str = Depends(verify_admin)
):
    with SessionLocal() as db:
        row = db.execute(text("SELECT id FROM messaging_settings ORDER BY id ASC LIMIT 1")).fetchone()
        if row:
            db.execute(text("UPDATE messaging_settings SET welcome_subject=:s, welcome_body=:b, updated_at=CURRENT_TIMESTAMP WHERE id=:id"), {"s": welcome_subject, "b": welcome_body, "id": row.id})
        else:
            db.execute(text("INSERT INTO messaging_settings (welcome_subject, welcome_body) VALUES (:s,:b)"), {"s": welcome_subject, "b": welcome_body})
        db.commit()
    return RedirectResponse(url="/admin/messaging?updated=true", status_code=303)


@router.get("/users", response_class=HTMLResponse)
async def admin_users(
    request: Request,
    q: Optional[str] = None,
    admin: str = Depends(verify_admin)
):
    """List users and allow role assignment."""
    where = ""
    params = {}
    if q:
        where = "WHERE email LIKE :q OR COALESCE(name,'') LIKE :q"
        params["q"] = f"%{q}%"
    with SessionLocal() as db:
        rows = db.execute(
            text(f"""
                SELECT id, email, COALESCE(name,'') AS name, role, status
                FROM users
                {where}
                ORDER BY created_at DESC
                LIMIT 200
            """),
            params
        ).fetchall()
        users = [
            {"id": r.id, "email": r.email, "name": r.name, "role": r.role, "status": r.status}
            for r in rows
        ]
        roles = [r.value for r in Role]
    return templates.TemplateResponse(
        "admin_users.html",
        {"request": request, "admin_user": admin, "users": users, "roles": roles, "q": q or ""}
    )


@router.post("/users/{user_id}/role")
async def update_user_role(
    user_id: int,
    role: str = Form(...),
    admin: str = Depends(verify_admin)
):
    """Update a user's system role."""
    try:
        new_role = Role(role)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid role: {role}")
    with SessionLocal() as db:
        row = db.execute(text("SELECT id FROM users WHERE id = :id"), {"id": user_id}).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="User not found")
        db.execute(text("UPDATE users SET role = :r WHERE id = :id"), {"r": new_role.value, "id": user_id})
        db.commit()
    logger.info("admin_user_role_updated", user_id=user_id, role=new_role.value, admin=admin)
    return RedirectResponse(url=f"/admin/users", status_code=303)


@router.post("/messaging/test", response_class=HTMLResponse)
async def messaging_test(
    request: Request,
    email: str = Form(...),
    admin: str = Depends(verify_admin)
):
    """Send a test welcome email to the specified address."""
    try:
        ok = send_welcome_email(email, first_name="Test")
        logger.info("welcome_email_test_sent", email=email, ok=ok)
        return RedirectResponse(url=f"/admin/messaging?test={'ok' if ok else 'fail'}", status_code=303)
    except Exception as e:
        logger.error("welcome_email_test_failed", email=email, error=str(e))
        return RedirectResponse(url=f"/admin/messaging?test=error", status_code=303)


@router.get("/cancellations", response_class=HTMLResponse)
async def cancellations_list(
    request: Request,
    page: int = 1,
    limit: int = 20,
    status: Optional[str] = None,
    admin: str = Depends(verify_admin)
):
    """Cancellation management page."""

    offset = (page - 1) * limit

    with SessionLocal() as db:
        # Build query based on filters
        where_clause = "WHERE 1=1"
        params = {"limit": limit, "offset": offset}

        if status:
            where_clause += " AND c.status = :status"
            params["status"] = status

        # Get cancellations
        cancellations = db.execute(
            text(f"""
                SELECT
                    c.id,
                    c.trip_id,
                    c.status,
                    c.refund_amount_minor,
                    c.refund_currency,
                    c.reason,
                    c.cancelled_by,
                    c.created_at,
                    t.pnr,
                    q.email,
                    q.total_price_ngn
                FROM cancellations c
                JOIN trips t ON c.trip_id = t.id
                JOIN quotes q ON c.quote_id = q.id
                {where_clause}
                ORDER BY c.created_at DESC
                LIMIT :limit OFFSET :offset
            """),
            params
        ).fetchall()

        # Get total count
        total_count = db.execute(
            text(f"SELECT COUNT(*) FROM cancellations c {where_clause}"),
            {k: v for k, v in params.items() if k not in ['limit', 'offset']}
        ).scalar() or 0

    total_pages = (total_count + limit - 1) // limit

    return templates.TemplateResponse(
        "admin_cancellations.html",
        {
            "request": request,
            "admin_user": admin,
            "cancellations": cancellations,
            "page": page,
            "total_pages": total_pages,
            "status_filter": status,
        }
    )


@router.post("/cancellations/{cancellation_id}/process")
async def process_cancellation(
    cancellation_id: int,
    admin: str = Depends(verify_admin)
):
    """Process a pending cancellation."""

    from app.services.cancellation_service import get_cancellation_service

    with SessionLocal() as db:
        try:
            service = get_cancellation_service(db)
            result = service.process_cancellation(
                cancellation_id=cancellation_id,
                admin_user=admin
            )

            logger.info(
                "cancellation_processed_by_admin",
                cancellation_id=cancellation_id,
                admin=admin,
                result=result
            )

            return RedirectResponse(
                url=f"/admin/cancellations?processed={cancellation_id}",
                status_code=303
            )

        except Exception as e:
            logger.error(
                "admin_cancellation_processing_failed",
                cancellation_id=cancellation_id,
                admin=admin,
                error=str(e)
            )
            return RedirectResponse(
                url=f"/admin/cancellations?error={str(e)}",
                status_code=303
            )


@router.get("/smtp", response_class=HTMLResponse)
async def smtp_get(request: Request, admin: str = Depends(verify_admin)):
    with SessionLocal() as db:
        row = db.execute(text("SELECT id, host, port, user, password, from_email, from_name, use_tls FROM smtp_settings ORDER BY id ASC LIMIT 1")).fetchone()
        s = {
            "host": row.host if row else None,
            "port": row.port if row else 587,
            "user": row.user if row else None,
            "password": row.password if row else None,
            "from_email": row.from_email if row else None,
            "from_name": row.from_name if row else None,
            "use_tls": bool(row.use_tls) if row else True,
        }
    return templates.TemplateResponse("admin_smtp.html", {"request": request, "admin_user": admin, "s": s})


@router.post("/smtp", response_class=HTMLResponse)
async def smtp_post(
    request: Request,
    host: str = Form(...),
    port: int = Form(...),
    user: str = Form(...),
    password: str = Form(...),
    from_email: str = Form(...),
    from_name: str = Form(...),
    use_tls: str | None = Form(None),
    admin: str = Depends(verify_admin)
):
    with SessionLocal() as db:
        row = db.execute(text("SELECT id FROM smtp_settings ORDER BY id ASC LIMIT 1")).fetchone()
        payload = {"host": host, "port": port, "user": user, "password": password, "from_email": from_email, "from_name": from_name, "use_tls": 1 if (use_tls is not None) else 0}
        if row:
            db.execute(text("UPDATE smtp_settings SET host=:host, port=:port, user=:user, password=:password, from_email=:from_email, from_name=:from_name, use_tls=:use_tls, updated_at=CURRENT_TIMESTAMP WHERE id=:id"), {**payload, "id": row.id})
        else:
            db.execute(text("INSERT INTO smtp_settings (host, port, user, password, from_email, from_name, use_tls) VALUES (:host,:port,:user,:password,:from_email,:from_name,:use_tls)"), payload)
        db.commit()
    return RedirectResponse(url="/admin/smtp?updated=true", status_code=303)


@router.get("/features", response_class=HTMLResponse)
async def features_get(request: Request, admin: str = Depends(verify_admin)):
    with SessionLocal() as db:
        def getv(k, d):
            row = db.execute(text("SELECT value FROM app_config WHERE key=:k"), {"k": k}).fetchone()
            return (row.value if row else d)
        flags = {
            "IGNORE_DOMESTIC_ROUTES": getv("IGNORE_DOMESTIC_ROUTES", "false"),
        }
    return templates.TemplateResponse("admin_features.html", {"request": request, "admin_user": admin, "flags": flags})


@router.post("/features", response_class=HTMLResponse)
async def features_post(request: Request, ignore_domestic_routes: str | None = Form(None), admin: str = Depends(verify_admin)):
    with SessionLocal() as db:
        val = "true" if ignore_domestic_routes is not None else "false"
        row = db.execute(text("SELECT key FROM app_config WHERE key='IGNORE_DOMESTIC_ROUTES'" )).fetchone()
        if row:
            db.execute(text("UPDATE app_config SET value=:v, updated_at=CURRENT_TIMESTAMP WHERE key='IGNORE_DOMESTIC_ROUTES'"), {"v": val})
        else:
            db.execute(text("INSERT INTO app_config(key,value) VALUES('IGNORE_DOMESTIC_ROUTES', :v)"), {"v": val})
        db.commit()
    return RedirectResponse(url="/admin/features?updated=true", status_code=303)
