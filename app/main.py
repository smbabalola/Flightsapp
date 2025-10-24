from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.core.logging import RequestIDMiddleware
from app.api.v1 import router as api_v1_router
from app.webhooks.routes import router as webhooks_router
from app.api.health import router as health_router
from app.api.root import router as root_router
from app.api.metrics import router as metrics_router
from app.admin.routes import router as admin_router
from app.api.cancellations import router as cancellations_router
from app.api.promo_codes import router as promo_codes_router
from app.auth.routes import router as auth_router
from app.api.users import router as users_router
from app.api.loyalty import router as loyalty_router
from app.api.ops import router as ops_router
from app.twitter.routes import router as twitter_router
from app.voice.routes import router as voice_router
from app.chat.routes import router as chat_router
from app.core.settings import get_settings
from app.core.sentry import init_sentry


def create_app() -> FastAPI:
    app = FastAPI(title="SureFlights API", version="0.1.0")
    init_sentry()
    app.add_middleware(RequestIDMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://127.0.0.1:8000","http://localhost:8000","http://127.0.0.1:8001","http://localhost:8001"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    get_settings().validate_startup()
    app.include_router(root_router)
    app.include_router(metrics_router)
    app.include_router(health_router)
    # Authentication
    app.include_router(auth_router, prefix="/auth", tags=["Authentication"])
    # Public customer API
    app.include_router(api_v1_router, prefix="/v1")
    app.include_router(cancellations_router)
    app.include_router(promo_codes_router)
    # Operational endpoints (require JWT auth)
    app.include_router(ops_router, prefix="/v1/ops", tags=["Operations"])
    app.include_router(users_router, prefix="/v1/ops", tags=["User Management"])
    app.include_router(loyalty_router, prefix="/v1/ops", tags=["Loyalty"])
    # Webhooks
    app.include_router(webhooks_router, prefix="/webhooks")
    app.include_router(twitter_router, prefix="/webhooks")
    app.include_router(voice_router, prefix="/webhooks")
    # Web Chat
    app.include_router(chat_router)
    # Admin dashboard (still supports Basic Auth for backward compatibility)
    app.include_router(admin_router, prefix="/admin")
    # Mount static files for web interface
    app.mount("/", StaticFiles(directory="static", html=True), name="static")
    return app

app = create_app()
