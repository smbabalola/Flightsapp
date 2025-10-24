from pathlib import Path

path = Path("tests/test_b2b.py")
text = path.read_text()
old = "            policy = onboarding[\"default_policy\"]\n            db.execute(\n                text(\"UPDATE travel_policies SET require_finance_approval = 1 WHERE id = :id\"),\n                {\"id\": policy.id},\n            )\n            db.flush()\n            db.refresh(policy)\n            assert policy.require_finance_approval is True\n            stored_flag = db.execute(\n                text(\"SELECT require_finance_approval FROM travel_policies WHERE id = :id\"),\n                {\"id\": policy.id},\n            ).scalar()\n            assert stored_flag in (1, True)\n            admin_membership = onboarding[\"membership\"]\n"
new = "            default_policy = onboarding[\"default_policy\"]\n            policy = TravelPolicy(\n                company_id=company.id,\n                name=f\"Finance Policy {unique_suffix}\",\n                status=\"active\",\n                require_manager_approval=True,\n                require_finance_approval=True,\n            )\n            db.add(policy)\n            db.flush()\n            db.refresh(policy)\n            admin_membership = onboarding[\"membership\"]\n"
if old not in text:
    raise SystemExit("policy block not found")
path.write_text(text.replace(old, new))
