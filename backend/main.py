
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from wind_service import get_wind_analysis

app = FastAPI(title="WindWise API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:5175",
    "http://127.0.0.1:5175",
    "https://windwise-sooty.vercel.app",
],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    return {
        "message": "WindWise API is running",
        "docs": "/docs",
    }


@app.get("/api/health")
async def health():
    return {"status": "healthy"}


@app.get("/api/wind")
async def wind(
    start_date: str = Query(default="2026-01-15"),
    end_date: str = Query(default="2026-01-15"),
):
    try:
        return await get_wind_analysis(start_date, end_date)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Unable to retrieve wind data: {exc}",
        )
