from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.api import funds, predictions, clusters, anomalies

app = FastAPI(
    title="Vantage . API",
    description="Intelligent Mutual Fund Analysis - ML-Powered REST API",
    version="1.0.0"
)

# CORS configuration (allows React frontend to communicate)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(funds.router, prefix="/api/funds", tags=["Funds"])
app.include_router(predictions.router, prefix="/api/predictions", tags=["Predictions"])
app.include_router(clusters.router, prefix="/api/clusters", tags=["Clusters"])
app.include_router(anomalies.router, prefix="/api/anomalies", tags=["Anomalies"])

@app.get("/")
def root():
    """Root endpoint - API status"""
    return {
        "message": "Vantage . API is running",
        "version": "1.0.0",
        "docs": "/docs",
        "endpoints": {
            "funds": "/api/funds",
            "predictions": "/api/predictions",
            "clusters": "/api/clusters",
            "anomalies": "/api/anomalies"
        }
    }

@app.get("/api/health")
def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "Vantage . API"}