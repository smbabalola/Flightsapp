from fastapi import HTTPException, status

def upstream_error(provider: str, message: str):
    return HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail={"error": "upstream_error", "provider": provider, "message": message})
