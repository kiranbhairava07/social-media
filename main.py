from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from routes import auth, public, qr

app = FastAPI(
    title="QR Code Manager",
    description="QR code management system with analytics",
    version="1.0.0"
)

# CORS middleware - Allow all origins for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router)
app.include_router(public.router)
app.include_router(qr.router)

# Serve static files (HTML pages)
@app.get("/")
async def root():
    return FileResponse("templates/index.html")

@app.get("/dashboard")
async def dashboard():
    return FileResponse("templates/dashboard.html")
@app.get("/analytics")
async def analytics():
    return FileResponse("templates/analytics.html")

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)