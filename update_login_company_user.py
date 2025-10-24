from pathlib import Path

path = Path("app/auth/routes.py")
text = path.read_text()
old = "    company_id: Optional[int] = None\n    company_role: Optional[str] = None\n    if selected_membership:\n        company_id = int(selected_membership.company_id)\n        company_role = selected_membership.membership_role\n        token_data[\"company_id\"] = company_id\n        token_data[\"company_role\"] = company_role\n"
new = "    company_id: Optional[int] = None\n    company_user_id: Optional[int] = None\n    company_role: Optional[str] = None\n    if selected_membership:\n        company_id = int(selected_membership.company_id)\n        company_user_id = int(selected_membership.company_user_id)
        company_role = selected_membership.membership_role\n        token_data[\"company_id\"] = company_id\n        token_data[\"company_user_id\"] = company_user_id\n        token_data[\"company_role\"] = company_role\n"
if old not in text:
    raise SystemExit('login block not found')
path.write_text(text.replace(old, new))
