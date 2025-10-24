from pathlib import Path

path = Path("app/auth/routes.py")
lines = path.read_text().splitlines()
result = []
for line in lines:
    result.append(line)
    if 'cu.status AS membership_status' in line:
        # avoid duplicate insertion
        if not result or 'cu.id AS company_user_id' not in line:
            result.append('                cu.id AS company_user_id')
    if '"role": row.membership_role,' in line:
        result.append('            "company_user_id": int(row.company_user_id),')

# Post-process to prevent duplicate entries
cleaned = []
for line in result:
    if line == '                cu.id AS company_user_id' and cleaned and cleaned[-1] == '                cu.id AS company_user_id':
        continue
    if line == '            "company_user_id": int(row.company_user_id),' and cleaned and cleaned[-1] == line:
        continue
    cleaned.append(line)

text = "\n".join(cleaned) + "\n"
path.write_text(text)
