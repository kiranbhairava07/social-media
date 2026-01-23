from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from contextlib import asynccontextmanager
import logging
import time

from routes import auth, public, qr
from database import close_db_connections, check_db_connection
from config import settings

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# OPTIMIZED: Lifespan context manager for startup/shutdown
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Startup and shutdown events.
    """
    # Startup
    logger.info(f"Starting QR Manager API - Environment: {settings.ENVIRONMENT}")
    
    # Check database connection
    if await check_db_connection():
        logger.info("✅ Database connection successful")
    else:
        logger.error("❌ Database connection failed")
    
    yield
    
    # Shutdown
    logger.info("Shutting down QR Manager API")
    await close_db_connections()
    logger.info("✅ All connections closed gracefully")


# OPTIMIZED: Create FastAPI app with lifespan
app = FastAPI(
    title="QR Code Manager",
    description="QR code management system with analytics",
    version="2.0.0",
    lifespan=lifespan,
    # docs_url="/api/docs" if settings.ENVIRONMENT != "production" else None,
    redoc_url="/api/redoc" if settings.ENVIRONMENT != "production" else None,
)


# OPTIMIZED: Request timing middleware
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """
    Add response time header to all requests.
    Useful for monitoring performance.
    """
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(round(process_time * 1000, 2))
    
    # Log slow requests
    if process_time > 1.0:
        logger.warning(f"Slow request: {request.method} {request.url.path} took {process_time:.2f}s")
    
    return response


# OPTIMIZED: Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    Catch all unhandled exceptions and return proper error response.
    """
    logger.error(f"Unhandled exception on {request.url.path}: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "path": str(request.url.path)
        }
    )


# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Process-Time"],  # Expose performance header
)

# Include routers
app.include_router(auth.router)
app.include_router(public.router)
app.include_router(qr.router)


# Serve static HTML files
@app.get("/")
async def root():
    return FileResponse("templates/index.html")


@app.get("/dashboard")
async def dashboard():
    return FileResponse("templates/dashboard.html")


@app.get("/analytics")
async def analytics():
    return FileResponse("templates/analytics.html")


# OPTIMIZED: Enhanced health check endpoint
@app.get("/health")
async def health_check():
    """
    Health check endpoint for monitoring.
    Returns database status and app version.
    """
    db_healthy = await check_db_connection()
    
    return {
        "status": "healthy" if db_healthy else "degraded",
        "version": "2.0.0",
        "environment": settings.ENVIRONMENT,
        "database": "connected" if db_healthy else "disconnected"
    }


# OPTIMIZED: Metrics endpoint (for monitoring tools)
@app.get("/metrics")
async def metrics():
    """
    Basic metrics endpoint.
    In production, use Prometheus or similar.
    """
    return {
        "app": "qr_manager",
        "version": "2.0.0",
        "environment": settings.ENVIRONMENT,
        # Add more metrics as needed
    }


if __name__ == "__main__":
    import uvicorn
    
    # OPTIMIZED: Production-ready Uvicorn config
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.ENVIRONMENT == "production",
        workers=4 if settings.ENVIRONMENT == "production" else 1,
        log_level=settings.LOG_LEVEL.lower(),
        access_log=True,
        use_colors=True,
    )