"""Filesystem locations. The organizer package lives in ./industrial-ai-hackathon (ignored by git)."""

from __future__ import annotations

import json
import os
from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PKG = Path(os.environ.get("CERTI_PACKAGE", ROOT / "industrial-ai-hackathon"))
DATA = ROOT / "data"
ARTIFACTS = ROOT / "artifacts"
PARSED = DATA / "parsed"
CACHE = DATA / "cache"
RUNS = ARTIFACTS / "runs"

for _d in (DATA, ARTIFACTS, PARSED, CACHE, RUNS):
    _d.mkdir(parents=True, exist_ok=True)


def slug(regulation: str) -> str:
    """Same folder naming as tools/fetch_regulations.py."""
    return "_".join(regulation.replace("/", " ").split())


@lru_cache(maxsize=1)
def index() -> list[dict]:
    return json.loads((PKG / "regulations" / "index.json").read_text(encoding="utf-8"))


def regulation_entry(regulation: str) -> dict:
    for entry in index():
        if entry["regulation"] == regulation:
            return entry
    raise KeyError(regulation)


def version_entry(regulation: str, role: str) -> dict | None:
    for v in regulation_entry(regulation).get("versions", []):
        if v.get("role") == role:
            return v
    return None


def pdf_path(regulation: str, role: str) -> Path:
    v = version_entry(regulation, role)
    if v is None:
        raise KeyError(f"{regulation} has no {role} version")
    return PKG / "regulations" / "pdf" / slug(regulation) / role / v["files"][0]["name"]


LOCAL_CASES = DATA / "cases"  # our own test products (not part of the organizer package)


def case_dir(case_id: str) -> Path:
    local = LOCAL_CASES / case_id
    return local if local.exists() else PKG / "cases" / case_id


def subgoal_dir(case_id: str) -> Path:
    # case ids look like "subgoal-dev" / "subgoal-heldout"; folders are subgoal/dev, subgoal/heldout
    name = case_id.removeprefix("subgoal-")
    return PKG / "subgoal" / name


def expected_path(case_id: str) -> Path:
    """Evaluation only. Inference code must never call this."""
    return case_dir(case_id) / "expected.json"
