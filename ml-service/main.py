"""
AlphaWatch AI — ML Microservice (FastAPI Internal)
ASTRAQUANT X 2026

Runs internally on 127.0.0.1:8001.
Never exposed to the public internet or directly to the browser.
Exposes quantitative analytics, features, predictions, risk, and backtesting to the Node.js server.
"""

import sys
from pathlib import Path
from fastapi import FastAPI
from fastapi.responses import JSONResponse

# Add project root to sys.path to reuse existing src modules
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

app = FastAPI(
    title="AlphaWatch ML Microservice",
    description="Internal Quantitative Analytics & Machine Learning Engine",
    version="1.0.0",
    docs_url=None,
    redoc_url=None,
    openapi_url=None,
)

@app.get("/api/ml/health")
def health_check():
    return {
        "status": "healthy",
        "service": "alphawatch-ml-service",
        "python_version": sys.version,
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8001, reload=True)
