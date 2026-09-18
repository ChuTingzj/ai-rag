from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from app import cli


def test_worker_runs_with_repo_root_cwd(monkeypatch) -> None:
    calls: list[dict[str, object]] = []

    def fake_call(cmd: list[str], cwd: Path | str | None = None) -> int:
        calls.append({"cmd": cmd, "cwd": Path(cwd) if cwd is not None else None})
        return 0

    monkeypatch.setattr(subprocess, "call", fake_call)

    with pytest.raises(SystemExit) as exc:
        cli.worker()

    assert exc.value.code == 0
    assert len(calls) == 1
    assert calls[0]["cwd"] == cli._REPO_ROOT
