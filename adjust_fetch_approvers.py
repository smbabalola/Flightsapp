from pathlib import Path

path = Path("app/services/travel_request_service.py")
text = path.read_text()
old = "    def _fetch_approvers(self, *, company_id: int, roles: Sequence[str]) -> list[int]:\n        stmt = text(\n            \"\"\"\n            SELECT\n                id\n            FROM company_users\n            WHERE company_id = :company_id\n              AND role = ANY(:roles)\n              AND status = 'active'\n            \"\"\"\n        )\n        rows = self.db.execute(stmt, {\"company_id\": company_id, \"roles\": roles}).fetchall()\n        return [row[0] for row in rows]\n"
new = "    def _fetch_approvers(self, *, company_id: int, roles: Sequence[str]) -> list[int]:\n        stmt = (\n            select(CompanyUser.id)\n            .where(CompanyUser.company_id == company_id)\n            .where(CompanyUser.role.in_(roles))\n            .where(CompanyUser.status == \"active\")\n        )\n        return list(self.db.execute(stmt).scalars().all())\n"
if old not in text:
    raise SystemExit("_fetch_approvers definition not found")
path.write_text(text.replace(old, new))
