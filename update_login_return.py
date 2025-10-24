from pathlib import Path

path = Path("app/auth/routes.py")
text = path.read_text()
old = "    return TokenResponse(\n        access_token=access_token,\n        refresh_token=refresh_token,\n        company_id=company_id,\n        company_role=company_role,\n        available_companies=available_companies,\n    )\n"
new = "    return TokenResponse(\n        access_token=access_token,\n        refresh_token=refresh_token,\n        company_id=company_id,\n        company_user_id=company_user_id,\n        company_role=company_role,\n        available_companies=available_companies,\n    )\n"
if old not in text:
    raise SystemExit('login return block not found')
text = text.replace(old, new)
old_refresh = "    company_id: Optional[int] = None\n    company_role: Optional[str] = None\n    if company_id_claim is not None:\n        selected_membership = next(\n            (row for row in active_memberships if row.company_id == company_id_claim),\n            None,\n        )\n        if not selected_membership:\n            raise HTTPException(\n                status_code=status.HTTP_401_UNAUTHORIZED,\n                detail=\"Tenant membership is no longer valid\",\n            )\n        company_id = int(selected_membership.company_id)\n        company_role = selected_membership.membership_role\n"
new_refresh = "    company_id: Optional[int] = None\n    company_user_id: Optional[int] = None\n    company_role: Optional[str] = None\n    if company_id_claim is not None:\n        selected_membership = next(\n            (row for row in active_memberships if row.company_id == company_id_claim),\n            None,\n        )\n        if not selected_membership:\n            raise HTTPException(\n                status_code=status.HTTP_401_UNAUTHORIZED,\n                detail=\"Tenant membership is no longer valid\",\n            )\n        company_id = int(selected_membership.company_id)\n        company_user_id = int(selected_membership.company_user_id)\n        company_role = selected_membership.membership_role\n"
if old_refresh not in text:
    raise SystemExit('refresh block not found')
text = text.replace(old_refresh, new_refresh)
old_refresh_ret = "    return TokenResponse(\n        access_token=access_token,\n        refresh_token=refresh_token,\n        company_id=company_id,\n        company_role=company_role,\n        available_companies=available_companies,\n    )\n"
new_refresh_ret = "    return TokenResponse(\n        access_token=access_token,\n        refresh_token=refresh_token,\n        company_id=company_id,\n        company_user_id=company_user_id,\n        company_role=company_role,\n        available_companies=available_companies,\n    )\n"
if old_refresh_ret not in text:
    raise SystemExit('refresh return not found')
text = text.replace(old_refresh_ret, new_refresh_ret)
path.write_text(text)
