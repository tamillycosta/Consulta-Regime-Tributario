import os
import sys

# Dynamically add the parent 'api' directory to sys.path so imports like 'from app...' never fail
APP_DIR = os.path.dirname(os.path.abspath(__file__))
API_DIR = os.path.dirname(APP_DIR)
if API_DIR not in sys.path:
    sys.path.insert(0, API_DIR)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from app.routers.consulta import router as consulta_router
from app.services.cache_service import init_db

app = FastAPI(
    title="API Consulta Regime Tributário - Simples Nacional & MEI",
    description="Serviço para processamento em lote de CNPJs e verificação de opção pelo Simples Nacional e MEI",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def startup_event():
    init_db()

app.include_router(consulta_router)

# Mount React static frontend if built
BASE_DIR = os.path.dirname(API_DIR)
FRONTEND_DIST = os.path.join(BASE_DIR, "frontend", "dist")

if os.path.exists(FRONTEND_DIST):
    assets_dir = os.path.join(FRONTEND_DIST, "assets")
    if os.path.exists(assets_dir):
        app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        if full_path.startswith("api"):
            return None
        file_path = os.path.join(FRONTEND_DIST, full_path)
        if os.path.exists(file_path) and os.path.isfile(file_path):
            return FileResponse(file_path)
        return FileResponse(os.path.join(FRONTEND_DIST, "index.html"))
else:
    @app.get("/")
    def root():
        return {
            "status": "online",
            "service": "Consulta Regime Tributário (Simples Nacional & MEI)",
            "docs": "/docs"
        }

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("app.main:app", host="0.0.0.0", port=port, reload=False)
