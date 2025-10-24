from pathlib import Path

path = Path("app/api/b2b/travel_requests.py")
text = path.read_text()
text = text.replace(
    "@router.post(\n    \"/travel-requests/{request_id}/approve\",\n    response_model=ApprovalResponse,\n    dependencies=[Depends(require_company_permission(CompanyPermission.APPROVE_LEVEL_ONE))]\n)\nasync def approve_travel_request(",
    "@router.post(\n    \"/travel-requests/{request_id}/approve\",\n    response_model=ApprovalResponse\n)\nasync def approve_travel_request("
)
text = text.replace(
    "@router.post(\n    \"/travel-requests/{request_id}/reject\",\n    response_model=ApprovalResponse,\n    dependencies=[Depends(require_company_permission(CompanyPermission.APPROVE_LEVEL_ONE))]\n)\nasync def reject_travel_request(",
    "@router.post(\n    \"/travel-requests/{request_id}/reject\",\n    response_model=ApprovalResponse\n)\nasync def reject_travel_request("
)
path.write_text(text)
