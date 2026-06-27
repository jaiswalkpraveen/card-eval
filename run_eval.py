"""
run_eval.py — THE CONDUCTOR. This is the script you actually run.

Flow (per the diagram), repeated for all prompts in prompts.json:
    prompts.json -> generate_card() -> judge_card() -> save JSON

Usage:
    python run_eval.py                 # writes results/run-<timestamp>.json
    python run_eval.py --baseline      # writes results/baseline.json instead
"""

import json
import sys
from datetime import datetime
from pathlib import Path

from generate import generate_card
from judge import judge_card
from llm import is_mock

ROOT = Path(__file__).parent
PROMPTS_PATH = ROOT / "prompts.json"
RESULTS_DIR = ROOT / "results"


def run() -> dict:
    prompts = json.loads(PROMPTS_PATH.read_text())["prompts"]
    rows = []

    print(f"Mode: {'MOCK (fake LLM)' if is_mock() else 'REAL LLM'}")
    print(f"Evaluating {len(prompts)} prompts...\n")

    for p in prompts:
        card = generate_card(p)        # step 1
        score = judge_card(p, card)    # step 2
        rows.append(
            {
                "id": p["id"],
                "prompt": p["prompt"],
                "card": card,
                "scores": score.model_dump(),
                "overall": score.overall(),
            }
        )
        print(f"  {p['id']:24s} overall={score.overall()}")

    avg = round(sum(r["overall"] for r in rows) / len(rows), 2)
    print(f"\nAverage overall: {avg}")

    return {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "mode": "mock" if is_mock() else "real",
        "average_overall": avg,
        "results": rows,
    }


def main() -> None:
    RESULTS_DIR.mkdir(exist_ok=True)
    report = run()

    if "--baseline" in sys.argv:
        out = RESULTS_DIR / "baseline.json"
    else:
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        out = RESULTS_DIR / f"run-{stamp}.json"

    out.write_text(json.dumps(report, indent=2))
    print(f"\nSaved: {out.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
