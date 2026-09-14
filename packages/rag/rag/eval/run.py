from __future__ import annotations

import argparse
import asyncio
import json
import os
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from eval.corpus import ensure_m1_corpus_indexed
from eval.runner import compare_pipelines, run_pipeline_eval
from providers.registry import Settings


def _default_golden() -> Path:
    repo_root = Path(__file__).resolve().parents[4]
    return repo_root / "evals" / "m1" / "golden.jsonl"


def _async_database_url() -> str:
    return os.environ.get(
        "DATABASE_URL",
        "postgresql+asyncpg://rag:rag@localhost:15432/rag",
    )


async def _main_async(args: argparse.Namespace) -> None:
    golden_path = Path(args.golden)
    corpus_dir = golden_path.parent / "corpus"
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    settings = Settings(
        embedding_provider=os.environ.get("EMBEDDING_PROVIDER", "hash_stub"),
        embedding_dim=int(os.environ.get("EMBEDDING_DIM", "1024")),
        rerank_provider=os.environ.get("RERANK_PROVIDER", "stub"),
    )

    engine = create_async_engine(_async_database_url(), pool_pre_ping=True)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    try:
        kb_id, doc_map = await ensure_m1_corpus_indexed(
            session_factory,
            corpus_dir=corpus_dir,
            kb_name="m1-eval",
            settings=settings,
        )

        if args.compare:
            naive = await run_pipeline_eval(
                "naive",
                golden_path=golden_path,
                kb_id=kb_id,
                session_factory=session_factory,
                doc_map=doc_map,
                settings=settings,
            )
            hybrid = await run_pipeline_eval(
                "hybrid",
                golden_path=golden_path,
                kb_id=kb_id,
                session_factory=session_factory,
                doc_map=doc_map,
                settings=settings,
            )
            payload = {
                "comparison": compare_pipelines(naive, hybrid),
                "naive": naive.model_dump(),
                "hybrid": hybrid.model_dump(),
            }
        else:
            report = await run_pipeline_eval(
                args.pipeline,
                golden_path=golden_path,
                kb_id=kb_id,
                session_factory=session_factory,
                doc_map=doc_map,
                settings=settings,
            )
            payload = report.model_dump()

        out_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    finally:
        await engine.dispose()


def main() -> None:
    parser = argparse.ArgumentParser(description="Run M1 golden-set evaluation")
    parser.add_argument(
        "--pipeline",
        choices=("naive", "hybrid"),
        default="hybrid",
        help="Retrieval pipeline to evaluate",
    )
    parser.add_argument(
        "--golden",
        type=Path,
        default=_default_golden(),
        help="Path to golden.jsonl",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("reports/m1.json"),
        help="JSON report output path",
    )
    parser.add_argument(
        "--compare",
        action="store_true",
        help="Run naive and hybrid and include comparison",
    )
    args = parser.parse_args()
    asyncio.run(_main_async(args))


if __name__ == "__main__":
    main()
