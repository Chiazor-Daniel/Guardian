from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import asyncio
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from app.services.router import AssetRouter
from app.services.ai_core import AICore
from app.models.schemas import AnalysisRequest, AnalysisResponse


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize and cleanup resources."""
    app.state.ai_core = AICore()
    app.state.router = AssetRouter()
    yield
    # Cleanup
    await app.state.router.cleanup()


app = FastAPI(
    title="Guardian LPU",
    description="Multi-Asset Agentic Fraud Detection System",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    return {"message": "Guardian LPU - Agentic Fraud Detection Shield", "status": "active"}


@app.post("/analyze", response_model=AnalysisResponse)
async def analyze_assets(
    urls: str = Form(""),
    user_prompt: str = Form(""),
    files: list[UploadFile] = File(default_factory=list)
):
    """
    Analyze URLs and/or uploaded files for fraud detection.

    - **urls**: Comma-separated list of URLs to analyze
    - **user_prompt**: Optional custom prompt for analysis
    - **files**: PDF, image, or document files to analyze
    """
    try:
        router: AssetRouter = app.state.router
        ai_core: AICore = app.state.ai_core

        # Parse URLs
        url_list = [u.strip() for u in urls.split(",") if u.strip()] if urls else []

        # Process all assets in parallel
        asset_data = await router.process_assets(url_list, files)

        # Run AI analysis
        result = await ai_core.analyze(asset_data, user_prompt or None)

        return AnalysisResponse(**result)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "Guardian LPU"}


# Serve static files (frontend) - only if static directory exists
static_dir = os.path.join(os.path.dirname(__file__), "..", "static")
if os.path.exists(static_dir):
    app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")
