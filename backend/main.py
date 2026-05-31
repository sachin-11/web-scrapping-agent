import os
import sys
import asyncio

# Set Windows ProactorEventLoopPolicy to support Playwright subprocesses (SelectorEventLoop does not support subprocesses on Windows)
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
from routes.scraper_routes import router as scraper_router

# Load environment variables
load_dotenv()

app = FastAPI(
    title="Web Scraper Agent API",
    description="Backend API for the Web Scraper Agent powered by Playwright and OpenAI",
    version="1.0.0"
)

# Configure CORS
origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Ensure outputs directory exists
backend_dir = os.path.dirname(os.path.abspath(__file__))
outputs_dir = os.path.join(backend_dir, "outputs")
os.makedirs(outputs_dir, exist_ok=True)

# Mount outputs directory as static files
app.mount("/outputs", StaticFiles(directory=outputs_dir), name="outputs")

# Register routes
app.include_router(scraper_router, prefix="/api")

@app.get("/")
async def root():
    return {
        "status": "online",
        "message": "Web Scraper Agent API is running",
        "docs": "/docs",
        "health": "/api/status"
    }
