import os
import sys
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from api.routes import router as api_router
from api.v1.router import v1_router

app = FastAPI(
    title="GeoCadastral AI API",
    description="AI-Assisted Cadastral Mapping & Land Intelligence Enterprise Platform",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount sample images static folder
sample_images_dir = os.path.join(BASE_DIR, "..", "data", "sample_images")
os.makedirs(sample_images_dir, exist_ok=True)
app.mount("/api/sample_images", StaticFiles(directory=sample_images_dir), name="sample_images")

app.include_router(api_router)
app.include_router(v1_router)


@app.get("/")
def read_root():
    return {
        "message": "Welcome to GeoCadastral AI API",
        "documentation": "/docs",
        "health_check": "/api/health"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
