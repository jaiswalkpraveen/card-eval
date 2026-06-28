"""
report.py — turn an eval run + baseline into a self-contained HTML report.

Used by the on-demand CI workflow to publish results to GitHub Pages. Shows,
per prompt: baseline overall, current overall, the delta, the four sub-scores,
the generated card, and the judge's reasoning. Regressions (delta < -THRESHOLD)
are highlighted so you can see exactly where quality moved.

Usage:
    python report.py                      # latest run vs baseline -> site/index.html
    python report.py results/run-X.json   # specific run
    python report.py results/run-X.json out.html
"""

import html
import json
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).parent
RESULTS_DIR = ROOT / "results"
THRESHOLD = 0.5  # same gate as compare.py: drops beyond this are regressions


def _load(path: Path) -> dict:
    return json.loads(path.read_text())


def _latest_run() -> Path:
    runs = sorted(RESULTS_DIR.glob("run-*.json"))
    if not runs:
        sys.exit("No run-*.json found. Run: python run_eval.py")
    return runs[-1]


def _delta_class(delta: float) -> str:
    if delta < -THRESHOLD:
        return "regress"
    if delta > 0:
        return "up"
    if delta < 0:
        return "down"
    return "flat"


def _fmt_delta(delta: float) -> str:
    return f"{delta:+.2f}" if delta else "0.00"


def build_html(baseline: dict, current: dict) -> str:
    base_by_id = {r["id"]: r for r in baseline["results"]}
    rows_html = []
    regressions = 0

    for r in current["results"]:
        cid = r["id"]
        base = base_by_id.get(cid)
        base_overall = base["overall"] if base else None
        curr_overall = r["overall"]
        delta = round(curr_overall - base_overall, 2) if base_overall is not None else 0.0
        cls = _delta_class(delta) if base_overall is not None else "flat"
        if cls == "regress":
            regressions += 1

        s = r["scores"]
        base_cell = f"{base_overall:.2f}" if base_overall is not None else "—"
        rows_html.append(
            f"""
            <tr class="{cls}">
              <td class="id">{html.escape(cid)}</td>
              <td class="num">{base_cell}</td>
              <td class="num">{curr_overall:.2f}</td>
              <td class="num delta {cls}">{_fmt_delta(delta)}</td>
              <td class="num">{s['prompt_fidelity']}</td>
              <td class="num">{s['text_accuracy']}</td>
              <td class="num">{s['style_consistency']}</td>
              <td class="num">{s['aesthetic']}</td>
              <td class="card">{html.escape(r['card'])}</td>
              <td class="why">{html.escape(s.get('reasoning', ''))}</td>
            </tr>"""
        )

    base_avg = baseline.get("average_overall", 0)
    curr_avg = current.get("average_overall", 0)
    avg_delta = round(curr_avg - base_avg, 2)
    gate = "FAIL" if regressions else "PASS"
    gate_cls = "regress" if regressions else "up"

    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>card-eval report</title>
<style>
  :root {{ --fg:#1a1a2e; --muted:#6b7280; --line:#e5e7eb; --bg:#fafafa; }}
  * {{ box-sizing:border-box; }}
  body {{ font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;
         color:var(--fg); background:var(--bg); margin:0; padding:2rem; }}
  h1 {{ margin:0 0 .25rem; }}
  .sub {{ color:var(--muted); margin-bottom:1.5rem; font-size:.9rem; }}
  .cards {{ display:flex; gap:1rem; flex-wrap:wrap; margin-bottom:1.5rem; }}
  .stat {{ background:#fff; border:1px solid var(--line); border-radius:12px;
          padding:1rem 1.25rem; min-width:140px; }}
  .stat .k {{ color:var(--muted); font-size:.75rem; text-transform:uppercase; letter-spacing:.04em; }}
  .stat .v {{ font-size:1.6rem; font-weight:700; margin-top:.25rem; }}
  table {{ width:100%; border-collapse:collapse; background:#fff;
          border:1px solid var(--line); border-radius:12px; overflow:hidden; font-size:.85rem; }}
  th, td {{ padding:.6rem .7rem; text-align:left; border-bottom:1px solid var(--line); vertical-align:top; }}
  th {{ background:#f3f4f6; font-size:.7rem; text-transform:uppercase; letter-spacing:.03em; color:var(--muted); }}
  td.num {{ text-align:right; font-variant-numeric:tabular-nums; white-space:nowrap; }}
  td.id {{ font-weight:600; white-space:nowrap; }}
  td.card {{ max-width:320px; color:#374151; }}
  td.why {{ max-width:260px; color:var(--muted); font-style:italic; }}
  .delta.up, .v.up, .gate.up {{ color:#15803d; }}
  .delta.down {{ color:#b45309; }}
  .delta.regress {{ color:#b91c1c; font-weight:700; }}
  tr.regress {{ background:#fef2f2; }}
  tr.up {{ background:#f0fdf4; }}
  .badge {{ display:inline-block; padding:.2rem .6rem; border-radius:999px; font-weight:700; font-size:.8rem; }}
  .badge.up {{ background:#dcfce7; color:#15803d; }}
  .badge.regress {{ background:#fee2e2; color:#b91c1c; }}
</style>
</head>
<body>
  <h1>card-eval report</h1>
  <div class="sub">
    Baseline <code>{html.escape(str(baseline.get('generated_at','?')))}</code> ({baseline.get('mode','?')})
    &nbsp;vs&nbsp; run <code>{html.escape(str(current.get('generated_at','?')))}</code> ({current.get('mode','?')})
    &nbsp;·&nbsp; generated {datetime.now().strftime('%Y-%m-%d %H:%M')}
  </div>

  <div class="cards">
    <div class="stat"><div class="k">Baseline avg</div><div class="v">{base_avg:.2f}</div></div>
    <div class="stat"><div class="k">Current avg</div><div class="v">{curr_avg:.2f}</div></div>
    <div class="stat"><div class="k">Avg delta</div><div class="v {_delta_class(avg_delta)}">{_fmt_delta(avg_delta)}</div></div>
    <div class="stat"><div class="k">Regressions</div><div class="v">{regressions}</div></div>
    <div class="stat"><div class="k">Gate</div><div class="v"><span class="badge {gate_cls}">{gate}</span></div></div>
  </div>

  <table>
    <thead>
      <tr>
        <th>Prompt</th><th>Base</th><th>Curr</th><th>&Delta;</th>
        <th>Fid</th><th>Acc</th><th>Style</th><th>Aes</th>
        <th>Card</th><th>Judge reasoning</th>
      </tr>
    </thead>
    <tbody>{''.join(rows_html)}
    </tbody>
  </table>
</body>
</html>"""


def main() -> None:
    baseline_path = RESULTS_DIR / "baseline.json"
    if not baseline_path.exists():
        sys.exit("No baseline.json. Create one: python run_eval.py --baseline")

    run_path = Path(sys.argv[1]) if len(sys.argv) > 1 else _latest_run()
    out_path = Path(sys.argv[2]) if len(sys.argv) > 2 else (ROOT / "site" / "index.html")

    baseline = _load(baseline_path)
    current = _load(run_path)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(build_html(baseline, current))
    print(f"Report written: {out_path.relative_to(ROOT)}")
    print(f"Baseline: {baseline_path.name}  Run: {run_path.name}")


if __name__ == "__main__":
    main()
