from __future__ import annotations

from fastapi import APIRouter

from app.api import auth, connectors, documents, jobs, knowledge_bases, me, query

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(me.router)
api_router.include_router(knowledge_bases.router)
api_router.include_router(connectors.router)
api_router.include_router(documents.router)
api_router.include_router(jobs.router)
api_router.include_router(query.router)
