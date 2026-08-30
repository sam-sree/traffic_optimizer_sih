import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from backend.app.api.routes import router

app = FastAPI(
    title="QuantumRoute API",
    description="Hybrid Quantum-Inspired Traffic Route Optimization Platform API",
    version="1.0.0"
)

# Configure CORS for React frontend dashboard
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API Router
app.include_router(router)

# Serve cached graphs and maps static directory
cached_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'data', 'cached_graphs'))
if os.path.exists(cached_dir):
    app.mount("/static", StaticFiles(directory=cached_dir), name="static")

@app.get("/")
def read_root():
    return {
        "title": "QuantumRoute API",
        "status": "ONLINE",
        "docs": "/docs",
        "version": "1.0.0"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app.api.main:app", host="0.0.0.0", port=8000, reload=True)
