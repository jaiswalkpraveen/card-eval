"""
compare.py — the regression gate.

Compares the newest run against results/baseline.json. If any card's overall
score dropped by more than THRESHOLD, it prints a table and exits with code 1
(so CI can fail the build). Otherwise exits 0.

Usage:
    python compare.py                  # compares latest run-*.json to baseline
    python compare.py results/run-X.json
"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).parent
RESULTS_DIR = ROOT / "results"
THRESHOLD = 0.5  # allowed wobble before we call it a regression


def _load(path: Path) -> dict:
    return json.loads(path.read_text())


def _latest_run() -> Path:
    runs = sorted(RESULTS_DIR.glob("run-*.json"))
    if not runs:
        sys.exit("No run-*.json found. Run: python run_eval.py")
    return runs[-1]


def main() -> None:
    baseline_path = RESULTS_DIR / "baseline.json"
    if not baseline_path.exists():
        sys.exit("No baseline.json. Create one: python run_eval.py --baseline")

    run_path = Path(sys.argv[1]) if len(sys.argv) > 1 else _latest_run()

    baseline = {r["id"]: r["overall"] for r in _load(baseline_path)["results"]}
    current = {r["id"]: r["overall"] for r in _load(run_path)["results"]}

    print(f"Baseline: {baseline_path.name}")
    print(f"Current:  {run_path.name}\n")
    print(f"{'id':24s} {'base':>6s} {'curr':>6s} {'delta':>7s}")
    print("-" * 46)

    regressions = []
    for cid, base in baseline.items():
        curr = current.get(cid)
        if curr is None:
            continue
        delta = round(curr - base, 2)
        flag = "  <-- REGRESSION" if delta < -THRESHOLD else ""
        if flag:
            regressions.append(cid)
        print(f"{cid:24s} {base:6.2f} {curr:6.2f} {delta:+7.2f}{flag}")

    if regressions:
        print(f"\n{len(regressions)} regression(s): {', '.join(regressions)}")
        sys.exit(1)
    print("\nNo regressions. All within threshold.")


if __name__ == "__main__":
    main()
