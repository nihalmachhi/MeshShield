"""The demo must work from a clean, standard-library-only install."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_demo_runs_end_to_end_in_a_temporary_home(tmp_path: Path) -> None:
    environment = {
        **os.environ,
        "MESHSHIELD_HOME": str(tmp_path),
        "PYTHONPATH": str(PROJECT_ROOT / "src"),
        "PYTHONDONTWRITEBYTECODE": "1",
    }
    completed = subprocess.run(
        [sys.executable, "-m", "meshshield.cli", "demo"],
        cwd=PROJECT_ROOT,
        env=environment,
        capture_output=True,
        text=True,
        timeout=300,
    )
    assert completed.returncode == 0, completed.stderr

    report = json.loads(completed.stdout)
    assert report["dataset"]["transaction_count"] == 1600
    assert report["sync_simulation"]["accepted"] > 0
    assert (tmp_path / "data" / "generated" / "metrics.json").exists()


def test_generate_is_available_without_optional_extras(tmp_path: Path) -> None:
    environment = {
        **os.environ,
        "MESHSHIELD_HOME": str(tmp_path),
        "PYTHONPATH": str(PROJECT_ROOT / "src"),
        "PYTHONDONTWRITEBYTECODE": "1",
    }
    completed = subprocess.run(
        [sys.executable, "-m", "meshshield.cli", "generate", "--count", "150", "--seed", "9"],
        cwd=PROJECT_ROOT,
        env=environment,
        capture_output=True,
        text=True,
        timeout=300,
    )
    assert completed.returncode == 0, completed.stderr
    assert json.loads(completed.stdout)["seed"] == 9
