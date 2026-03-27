import time
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.config import get_settings
from app.database import init_db, AsyncSessionLocal
from app.models.models import MonitoringLog

# Routers
from app.routers.auth import router as auth_router
from app.routers.datasets import router as dataset_router
from app.routers.processing import router as processing_router
from app.routers.graph import router as graph_router
from app.routers.ai import router as ai_router
from app.routers.dashboard import router as dashboard_router
from app.routers.prediction import router as prediction_router
from app.routers.misc import (
    sim_router, anomaly_router, compare_router,
    history_router, export_router, admin_router,
    eval_router, monitor_router,
)

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await init_db()
    print("✅ Database initialized")
    yield
    # Shutdown
    from app.utils.neo4j_client import close_neo4j
    close_neo4j()
    print("✅ Connections closed")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="AI-powered Data Analytics SaaS — LangGraph + OpenRouter + Neo4j",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─── Monitoring Middleware ────────────────────────────────────────────────────
@app.middleware("http")
async def monitoring_middleware(request: Request, call_next):
    start = time.time()
    response = await call_next(request)
    latency_ms = (time.time() - start) * 1000

    # Log non-health requests
    if request.url.path not in ("/", "/health", "/docs", "/openapi.json"):
        try:
            async with AsyncSessionLocal() as db:
                log = MonitoringLog(
                    endpoint=str(request.url.path),
                    method=request.method,
                    status_code=response.status_code,
                    latency_ms=round(latency_ms, 2),
                )
                db.add(log)
                await db.commit()
        except Exception:
            pass  # Don't fail the request on logging errors

    return response


# ─── Include All Routers ──────────────────────────────────────────────────────
app.include_router(auth_router)
app.include_router(dataset_router)
app.include_router(processing_router)
app.include_router(graph_router)
app.include_router(ai_router)
app.include_router(dashboard_router)
app.include_router(prediction_router)
app.include_router(sim_router)
app.include_router(anomaly_router)
app.include_router(compare_router)
app.include_router(history_router)
app.include_router(export_router)
app.include_router(admin_router)
app.include_router(eval_router)
app.include_router(monitor_router)


# ─── Root Endpoints ───────────────────────────────────────────────────────────
@app.get("/", tags=["Root"])
async def root():
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "docs": "/docs",
        "status": "running 🚀",
    }


@app.get("/health", tags=["Root"])
async def health():
    return {"status": "healthy", "version": settings.APP_VERSION}
