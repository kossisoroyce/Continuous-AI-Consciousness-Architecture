"""
HMT Research Platform API
Human-Machine Teaming backend with persistent brain storage.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from contextlib import asynccontextmanager

# Load environment variables
load_dotenv()

# Import routers
from routers import system, nurture, experience, control, hmt, brain, vision
from routers import cognitive, audit, auth, sensors

# Database initialization
from database import init_db

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    init_db()
    yield
    # Shutdown
    pass

# Initialize FastAPI app
app = FastAPI(
    title="HMT Research Platform API",
    description="Human-Machine Teaming Research - Brain persistence and collaboration metrics",
    version="0.2.0",
    lifespan=lifespan
)

# CORS middleware for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(brain.router, tags=["brain"])
app.include_router(system.router, tags=["system"])
app.include_router(nurture.router, tags=["nurture"])
app.include_router(experience.router, tags=["experience"])
app.include_router(control.router, tags=["control"])
app.include_router(hmt.router, tags=["hmt"])
app.include_router(vision.router, tags=["vision"])
app.include_router(cognitive.router, tags=["cognitive"])
app.include_router(audit.router, tags=["audit"])
app.include_router(auth.router, tags=["auth"])
app.include_router(sensors.router, tags=["sensors"])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
