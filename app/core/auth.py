from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from app.core.settings import get_settings
import secrets

security = HTTPBasic()


def require_admin(credentials: HTTPBasicCredentials = Depends(security)):
    settings = get_settings()
    user_ok = settings.admin_user
    pass_ok = settings.admin_pass
    if not user_ok or not pass_ok:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Admin auth not configured")
    if not (secrets.compare_digest(credentials.username, user_ok) and secrets.compare_digest(credentials.password, pass_ok)):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials", headers={"WWW-Authenticate": "Basic"})
    return True
