from pathlib import Path

path = Path("app/auth/routes.py")
text = path.read_text()
old_query = """            SELECT
                c.id AS company_id,
                c.name AS company_name,
                c.slug AS company_slug,
                c.status AS company_status,
                cu.role AS membership_role,
                cu.status AS membership_status
            FROM company_users cu
            JOIN companies c ON c.id = cu.company_id
            WHERE cu.user_id = :user_id
            ORDER BY c.name
        """),
        {"user_id": user.id}
    ).fetchall()
"""
new_query = """            SELECT
                c.id AS company_id,
                c.name AS company_name,
                c.slug AS company_slug,
                c.status AS company_status,
                cu.role AS membership_role,
                cu.status AS membership_status,
                cu.id AS company_user_id
            FROM company_users cu
            JOIN companies c ON c.id = cu.company_id
            WHERE cu.user_id = :user_id
            ORDER BY c.name
        """),
        {"user_id": user.id}
    ).fetchall()
"""
if old_query not in text:
    raise SystemExit('query not found')
text = text.replace(old_query, new_query, 1)
old_query_refresh = """            SELECT
                c.id AS company_id,
                c.name AS company_name,
                c.slug AS company_slug,
                c.status AS company_status,
                cu.role AS membership_role,
                cu.status AS membership_status
            FROM company_users cu
            JOIN companies c ON c.id = cu.company_id
            WHERE cu.user_id = :user_id
            ORDER BY c.name
        """),
        {"user_id": user.id}
    ).fetchall()
"""
text = text.replace(old_query_refresh, new_query, 1)
old_list = """        {
            "id": int(row.company_id),
            "name": row.company_name,
            "slug": row.company_slug,
            "status": row.company_status,
            "membership_status": row.membership_status,
            "role": row.membership_role,
        }
"""
new_list = """        {
            "id": int(row.company_id),
            "name": row.company_name,
            "slug": row.company_slug,
            "status": row.company_status,
            "membership_status": row.membership_status,
            "role": row.membership_role,
            "company_user_id": int(row.company_user_id),
        }
"""
text = text.replace(old_list, new_list, 2)
old_vars = """    company_id: Optional[int] = None
    company_role: Optional[str] = None
    if company_id_claim is not None:
        selected_membership = next(
            (row for row in active_memberships if row.company_id == company_id_claim),
            None,
        )
        if not selected_membership:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Tenant membership is no longer valid",
            )
        company_id = int(selected_membership.company_id)
        company_role = selected_membership.membership_role
"""
new_vars = """    company_id: Optional[int] = None
    company_user_id: Optional[int] = None
    company_role: Optional[str] = None
    if company_id_claim is not None:
        selected_membership = next(
            (row for row in active_memberships if row.company_id == company_id_claim),
            None,
        )
        if not selected_membership:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Tenant membership is no longer valid",
            )
        company_id = int(selected_membership.company_id)
        company_user_id = int(selected_membership.company_user_id)
        company_role = selected_membership.membership_role
"""
text = text.replace(old_vars, new_vars, 1)
path.write_text(text)
