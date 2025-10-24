from pathlib import Path

path = Path("app/auth/routes.py")
text = path.read_text()
login_old = "    company_id: Optional[int] = None\n    company_role: Optional[str] = None\n    if selected_membership:\n        company_id = int(selected_membership.company_id)\n        company_role = selected_membership.membership_role\n"
login_new = "    company_id: Optional[int] = None\n    company_user_id: Optional[int] = None\n    company_role: Optional[str] = None\n    if selected_membership:\n        company_id = int(selected_membership.company_id)\n        company_user_id = int(selected_membership.company_user_id)\n        company_role = selected_membership.membership_role\n"
if login_old not in text:
    raise SystemExit('login block not found')
text = text.replace(login_old, login_new, 1)
refresh_old = "    company_id: Optional[int] = None\n    company_role: Optional[str] = None\n    if company_id_claim is not None:\n        selected_membership = next(\n            (row for row in active_memberships if row.company_id == company_id_claim),\n            None,\n        )\n        if not selected_membership:\n            raise HTTPException(\n                status_code=status.HTTP_401_UNAUTHORIZED,\n                detail=\"Tenant membership is no longer valid\",\n            )\n        company_id = int(selected_membership.company_id)\n        company_role = selected_membership.membership_role\n"
refresh_new = "    company_id: Optional[int] = None\n    company_user_id: Optional[int] = None\n    company_role: Optional[str] = None\n    if company_id_claim is not None:\n        selected_membership = next(\n            (row for row in active_memberships if row.company_id == company_id_claim),\n            None,\n        )\n        if not selected_membership:\n            raise HTTPException(\n                status_code=status.HTTP_401_UNAUTHORIZED,\n                detail=\"Tenant membership is no longer valid\",\n            )\n        company_id = int(selected_membership.company_id)\n        company_user_id = int(selected_membership.company_user_id)\n        company_role = selected_membership.membership_role\n"
if refresh_old not in text:
    raise SystemExit('refresh block not found')
text = text.replace(refresh_old, refresh_new, 1)
path.write_text(text)
