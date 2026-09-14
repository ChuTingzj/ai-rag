from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class GoldenCase(BaseModel):
    id: str
    question: str
    kb: str
    must_include_doc_ids: list[str] = Field(default_factory=list)
    forbidden_doc_ids: list[str] = Field(default_factory=list)


class EvalReport(BaseModel):
    pipeline: Literal["naive", "hybrid"]
    metrics: dict[str, float]
    cases: list[dict[str, Any]] = Field(default_factory=list)
