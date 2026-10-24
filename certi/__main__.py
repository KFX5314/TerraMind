"""CLI: python -m certi <command>

  parse [--force]                        parse every regulation PDF in the index
  run --case dev-rear-lamp [--team T]    full main-goal pipeline (resumable with --run-id)
  export --run-id ID [--threshold X]     re-export a finished run with another threshold
  validate FILE [--requirements-old F]   organizer validator
  score --run-id ID [--judge]            local regulation/page score (+ LLM-judge requirement score) on dev
  subgoal --case subgoal-dev [--team T]  sub-goal change analysis
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys

from . import ingest, llm, paths


def _team(arg: str | None) -> str:
    return arg or os.environ.get("TEAM_ID", "team-XX")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="certi")
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("parse"); p.add_argument("--force", action="store_true")
    p = sub.add_parser("run")
    p.add_argument("--case", required=True); p.add_argument("--team"); p.add_argument("--run-id")
    p.add_argument("--audit", action="store_true", help="independent omission audit (measured: no gain on dev)")
    p.add_argument("--deep", action="store_true")
    p.add_argument("--threshold", type=float); p.add_argument("--only", nargs="*")
    p = sub.add_parser("export"); p.add_argument("--run-id", required=True); p.add_argument("--threshold", type=float, default=None)
    p.add_argument("--team")
    p = sub.add_parser("validate"); p.add_argument("file"); p.add_argument("--requirements-old")
    p = sub.add_parser("score"); p.add_argument("--run-id", required=True); p.add_argument("--judge", action="store_true")
    p = sub.add_parser("subgoal"); p.add_argument("--case", default="subgoal-dev"); p.add_argument("--team")
    p.add_argument("--run-id")
    a = ap.parse_args(argv)

    if a.cmd == "parse":
        ingest.parse_all(force=a.force)
    elif a.cmd == "run":
        from . import pipeline
        run = pipeline.Run(a.run_id or pipeline.new_run_id(a.case))
        inputs = pipeline.load_case_inputs(a.case)
        kw = {"threshold": a.threshold} if a.threshold is not None else {}
        llm.run(pipeline.run_pipeline(run, inputs, _team(a.team), deep_image=a.deep, audit=a.audit,
                                      only_regulations=a.only, **kw))
        print(run.dir / "submission.json")
        validate(run.dir / "submission.json")
    elif a.cmd == "export":
        from . import pipeline
        run = pipeline.Run(a.run_id)
        cands = run.read("candidates.json")
        inputs = run.read("inputs.json")
        thr = a.threshold if a.threshold is not None else inputs["config"]["threshold"]
        sub_ = pipeline.finalize(run, cands, _team(a.team), inputs["case_id"], thr)
        print(f"{len(sub_['requirements'])} requirements exported at threshold {thr}")
        validate(run.dir / "submission.json")
    elif a.cmd == "validate":
        return validate(a.file, a.requirements_old)
    elif a.cmd == "score":
        from . import evaluate
        evaluate.report(a.run_id, judge=a.judge)
    elif a.cmd == "subgoal":
        from . import subgoal
        subgoal.main(a.case, _team(a.team), a.run_id)
    return 0


def validate(file, requirements_old=None) -> int:
    cmd = [sys.executable, str(paths.PKG / "tools" / "validate.py"), str(file)]
    if requirements_old:
        cmd += ["--requirements-old", str(requirements_old)]
    r = subprocess.run(cmd, capture_output=True, text=True)
    print(r.stdout.strip() or r.stderr.strip())
    return r.returncode


if __name__ == "__main__":
    raise SystemExit(main())
