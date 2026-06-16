from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path

from service.config import settings
from service.routers import projects, styles

ROOT_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = ROOT_DIR / "frontend"

app = FastAPI(title="PPT Master Service", version="1.0.0", docs_url="/api/docs")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(projects.router)
app.include_router(styles.router)

@app.get("/api/health")
def health():
    return {"status": "ok", "version": "1.0.0"}

# Mount static files LAST - API routes have priority
if FRONTEND_DIR.exists() and (FRONTEND_DIR / "index.html").exists():
    app.mount("/", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="frontend")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("service.main:app", host=settings.host, port=settings.port)