from __future__ import annotations

from pathlib import Path

from rag.eval.run import _default_golden


def test_default_golden_path_under_repo():
    repo_root = Path(__file__).resolve().parents[2]
    golden = _default_golden()

    assert golden.name == "golden.jsonl"
    assert golden.as_posix().endswith("evals/m1/golden.jsonl")
    try:
        golden.relative_to(repo_root)
    except ValueError as exc:
        raise AssertionError(f"default golden {golden} is not under repo root {repo_root}") from exc
    assert golden.is_file()
