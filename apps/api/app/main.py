from fastapi import FastAPI

from app.api import api_router
from app.api.internal import router as internal_router

app = FastAPI(title="AI RAG API")
app.include_router(api_router, prefix="/api/v1")
app.include_router(internal_router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
