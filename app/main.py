from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from .config import get_settings
from .models import HealthResponse
from .routes import chat, admin
from .services.session_store import init_session_store


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    init_session_store(ttl_seconds=settings.session_ttl_seconds)
    yield


def create_app() -> FastAPI:
    settings = get_settings()

    limiter = Limiter(key_func=get_remote_address, default_limits=["10/minute"])

    app = FastAPI(
        title="30DLC Customer Support Chatbot",
        version="1.0.0",
        lifespan=lifespan,
    )

    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

    # CORS
    origins = ["*"] if settings.allowed_origins == "*" else settings.allowed_origins.split(",")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Exception handlers
    @app.exception_handler(404)
    async def not_found_handler(request: Request, exc):
        return JSONResponse(status_code=404, content={"detail": "Not found"})

    @app.exception_handler(500)
    async def server_error_handler(request: Request, exc):
        return JSONResponse(status_code=500, content={"detail": "Internal server error"})

    # Health check (no auth)
    @app.get("/health", response_model=HealthResponse)
    async def health():
        s = get_settings()
        return HealthResponse(
            status="ok",
            model=s.model,
            vector_store_configured=bool(s.vector_store_id),
        )

    app.include_router(chat.router)
    app.include_router(admin.router)

    return app


app = create_app()
