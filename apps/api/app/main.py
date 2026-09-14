from fastapi import FastAPI

from app.api import api_router

app = FastAPI(title="AI RAG API")
app.include_router(api_router, prefix="/api/v1")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
