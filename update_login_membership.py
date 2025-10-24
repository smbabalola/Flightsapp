from pathlib import Path

path = Path("app/auth/routes.py")
text = path.read_text()
text = text.replace(
"            SELECT\n                c.id AS company_id,\n                c.name AS company_name,\n                c.slug AS company_slug,\n                c.status AS company_status,\n                cu.role AS membership_role,\n                cu.status AS membership_status\n",
"            SELECT\n                c.id AS company_id,\n                c.name AS company_name,\n                c.slug AS company_slug,\n                c.status AS company_status,\n                cu.role AS membership_role,\n                cu.status AS membership_status,\n                cu.id AS company_user_id\n",
)
text = text.replace(
"            \"role\": row.membership_role,\n        }\n",
"            \"role\": row.membership_role,\n            \"company_user_id\": int(row.company_user_id),\n        }\n",
)
path.write_text(text)
