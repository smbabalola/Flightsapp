"""
Operational Endpoints

Internal operational endpoints for Agents, Supervisors, and Finance teams.
Requires JWT authentication and role-based permissions.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from typing import Optional, List
from sqlalchemy import text
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import structlog

from app.auth.dependencies import (
    get_db,
    get_current_user,
    require_permission,
    require_any_role,
)
from app.auth.permissions import User, Role, Permission
from app.models.models import AuditLog

logger = structlog.get_logger(__name__)
router = APIRouter()


class TripNoteRequest(BaseModel):
    """Add note to trip."""
    note: str


class TripResponse(BaseModel):
    """Trip response for ops."""
    trip_id: int
    pnr: str
    status: str
    customer_email: str
    customer_phone: Optional[str]
    total_amount: float
    created_at: str


@router.get(
    "/trips",
    response_model=List[TripResponse],
    dependencies=[Depends(require_permission(Permission.VIEW_TRIPS))]
)
async def list_trips(
    status: Optional[str] = None,
    pnr: Optional[str] = None,
    email: Optional[str] = None,
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
    limit: int = Query(50, le=200),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    List trips with filtering for operational staff.

    **Query Parameters:**
    - `status`: Filter by trip status
    - `pnr`: Filter by PNR
    - `email`: Filter by customer email
    - `from_date`: Filter trips created after this date
    - `to_date`: Filter trips created before this date
    - `limit`: Number of results (max 200)
    - `offset`: Offset for pagination

    **Authorization:** Requires `VIEW_TRIPS` permission (Agent, Supervisor, Finance, Admin)
    """
    where_clauses = []
    params = {"limit": limit, "offset": offset}

    if status:
        where_clauses.append("t.status = :status")
        params["status"] = status

    if pnr:
        where_clauses.append("t.pnr LIKE :pnr")
        params["pnr"] = f"%{pnr}%"

    if email:
        where_clauses.append("q.email LIKE :email")
        params["email"] = f"%{email}%"

    if from_date:
        where_clauses.append("t.created_at >= :from_date")
        params["from_date"] = from_date

    if to_date:
        where_clauses.append("t.created_at <= :to_date")
        params["to_date"] = to_date

    where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"

    trips = db.execute(
        text(f"""
            SELECT
                t.id as trip_id,
                t.pnr,
                t.status,
                q.email as customer_email,
                q.phone as customer_phone,
                q.total_price_ngn as total_amount,
                t.created_at
            FROM trips t
            JOIN quotes q ON t.quote_id = q.id
            WHERE {where_sql}
            ORDER BY t.created_at DESC
            LIMIT :limit OFFSET :offset
        """),
        params
    ).fetchall()

    logger.info(
        "ops_trips_listed",
        actor=current_user.email,
        actor_role=current_user.role.value,
        count=len(trips),
        filters={k: v for k, v in params.items() if k not in ['limit', 'offset']}
    )

    return [
        TripResponse(
            trip_id=t.trip_id,
            pnr=t.pnr or "",
            status=t.status or "unknown",
            customer_email=t.customer_email or "",
            customer_phone=t.customer_phone,
            total_amount=t.total_amount or 0.0,
            created_at=str(t.created_at) if t.created_at else ""
        )
        for t in trips
    ]


@router.post(
    "/trips/{trip_id}/notes",
    dependencies=[Depends(require_permission(Permission.ADD_TRIP_NOTES))]
)
async def add_trip_note(
    trip_id: int,
    request: TripNoteRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Add a note to a trip.

    **Path Parameters:**
    - `trip_id`: Trip ID

    **Request Body:**
    - `note`: Note text

    **Authorization:** Requires `ADD_TRIP_NOTES` permission (Agent, Supervisor, Admin)
    """
    # Verify trip exists
    trip = db.execute(
        text("SELECT id, pnr FROM trips WHERE id = :trip_id"),
        {"trip_id": trip_id}
    ).fetchone()

    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")

    # Log note in audit log
    audit_log = AuditLog(
        event="trip_note_added",
        actor=current_user.email,
        details={
            "trip_id": trip_id,
            "pnr": trip.pnr,
            "note": request.note,
            "actor_role": current_user.role.value,
        }
    )
    db.add(audit_log)
    db.commit()

    logger.info(
        "trip_note_added",
        actor=current_user.email,
        actor_role=current_user.role.value,
        trip_id=trip_id,
        pnr=trip.pnr
    )

    return {"message": "Note added successfully", "trip_id": trip_id}


@router.get(
    "/payments",
    dependencies=[Depends(require_permission(Permission.VIEW_PAYMENTS))]
)
async def list_payments(
    status: Optional[str] = None,
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
    limit: int = Query(50, le=200),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    List payments for finance team.

    **Query Parameters:**
    - `status`: Filter by payment status
    - `from_date`: Filter payments after this date
    - `to_date`: Filter payments before this date
    - `limit`: Number of results (max 200)
    - `offset`: Offset for pagination

    **Authorization:** Requires `VIEW_PAYMENTS` permission (Finance, Admin)
    """
    where_clauses = []
    params = {"limit": limit, "offset": offset}

    if status:
        where_clauses.append("status = :status")
        params["status"] = status

    if from_date:
        where_clauses.append("created_at >= :from_date")
        params["from_date"] = from_date

    if to_date:
        where_clauses.append("created_at <= :to_date")
        params["to_date"] = to_date

    where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"

    payments = db.execute(
        text(f"""
            SELECT
                id,
                quote_id,
                provider,
                reference,
                amount_minor,
                currency,
                status,
                created_at
            FROM payments
            WHERE {where_sql}
            ORDER BY created_at DESC
            LIMIT :limit OFFSET :offset
        """),
        params
    ).fetchall()

    logger.info(
        "ops_payments_listed",
        actor=current_user.email,
        actor_role=current_user.role.value,
        count=len(payments)
    )

    return [
        {
            "id": p.id,
            "quote_id": p.quote_id,
            "provider": p.provider,
            "reference": p.reference,
            "amount": p.amount_minor / 100,
            "currency": p.currency,
            "status": p.status,
            "created_at": str(p.created_at) if p.created_at else None
        }
        for p in payments
    ]


@router.get(
    "/financial-export",
    dependencies=[Depends(require_permission(Permission.EXPORT_FINANCIAL))]
)
async def export_financial_data(
    from_date: str = Query(..., description="Start date (YYYY-MM-DD)"),
    to_date: str = Query(..., description="End date (YYYY-MM-DD)"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Export financial data for reporting.

    **Query Parameters:**
    - `from_date`: Start date (required)
    - `to_date`: End date (required)

    **Authorization:** Requires `EXPORT_FINANCIAL` permission (Finance, Admin)

    **Returns:** Financial summary for the date range
    """
    # Get payments summary
    payments_summary = db.execute(
        text("""
            SELECT
                COUNT(*) as total_transactions,
                SUM(amount_minor) as total_amount_minor,
                currency,
                status
            FROM payments
            WHERE created_at >= :from_date
              AND created_at <= :to_date
            GROUP BY currency, status
        """),
        {"from_date": from_date, "to_date": to_date}
    ).fetchall()

    # Get refunds summary
    refunds_summary = db.execute(
        text("""
            SELECT
                COUNT(*) as total_refunds,
                SUM(refund_amount_minor) as total_refund_minor,
                refund_currency as currency
            FROM cancellations
            WHERE status = 'confirmed'
              AND created_at >= :from_date
              AND created_at <= :to_date
            GROUP BY refund_currency
        """),
        {"from_date": from_date, "to_date": to_date}
    ).fetchall()

    # Log export
    audit_log = AuditLog(
        event="financial_export",
        actor=current_user.email,
        details={
            "from_date": from_date,
            "to_date": to_date,
            "actor_role": current_user.role.value,
        }
    )
    db.add(audit_log)
    db.commit()

    logger.info(
        "financial_export",
        actor=current_user.email,
        actor_role=current_user.role.value,
        from_date=from_date,
        to_date=to_date
    )

    return {
        "from_date": from_date,
        "to_date": to_date,
        "payments": [
            {
                "currency": p.currency,
                "status": p.status,
                "total_transactions": p.total_transactions,
                "total_amount": (p.total_amount_minor or 0) / 100,
            }
            for p in payments_summary
        ],
        "refunds": [
            {
                "currency": r.currency,
                "total_refunds": r.total_refunds,
                "total_refund_amount": (r.total_refund_minor or 0) / 100,
            }
            for r in refunds_summary
        ],
        "exported_by": current_user.email,
        "exported_at": datetime.utcnow().isoformat(),
    }


@router.get(
    "/audit-logs",
    dependencies=[Depends(require_permission(Permission.VIEW_AUDIT_LOGS))]
)
async def list_audit_logs(
    event: Optional[str] = None,
    actor: Optional[str] = None,
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
    limit: int = Query(50, le=200),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    List audit logs for security monitoring.

    **Query Parameters:**
    - `event`: Filter by event type (e.g., 'user_login', 'user_created')
    - `actor`: Filter by actor email
    - `from_date`: Filter logs after this date
    - `to_date`: Filter logs before this date
    - `limit`: Number of results (max 200)
    - `offset`: Offset for pagination

    **Authorization:** Requires `VIEW_AUDIT_LOGS` permission (Supervisor, Admin)
    """
    where_clauses = []
    params = {"limit": limit, "offset": offset}

    if event:
        where_clauses.append("event = :event")
        params["event"] = event

    if actor:
        where_clauses.append("actor LIKE :actor")
        params["actor"] = f"%{actor}%"

    if from_date:
        where_clauses.append("created_at >= :from_date")
        params["from_date"] = from_date

    if to_date:
        where_clauses.append("created_at <= :to_date")
        params["to_date"] = to_date

    where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"

    logs = db.execute(
        text(f"""
            SELECT
                id,
                event,
                actor,
                details,
                created_at
            FROM audit_logs
            WHERE {where_sql}
            ORDER BY created_at DESC
            LIMIT :limit OFFSET :offset
        """),
        params
    ).fetchall()

    logger.info(
        "audit_logs_viewed",
        actor=current_user.email,
        actor_role=current_user.role.value,
        count=len(logs),
        filters={k: v for k, v in params.items() if k not in ['limit', 'offset']}
    )

    return [
        {
            "id": log.id,
            "event": log.event,
            "actor": log.actor,
            "details": log.details or {},
            "created_at": str(log.created_at) if log.created_at else None
        }
        for log in logs
    ]
