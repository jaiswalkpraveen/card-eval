"""
Phase 5: Playwright (Python) e2e test that links rendering to evaluation.

The full story in one test:
  1. generate_card()  -> produce card text (mock mode by default: free + deterministic)
  2. web/card.html    -> render that text in a REAL browser, like a customer sees it
  3. E2E assertions   -> does it actually RENDER? (visible, non-empty, sane length)
  4. EVAL assertion   -> is it actually GOOD? judge_card() score >= threshold

Run with:
    pytest e2e/ -v

By default this runs in MOCK mode (no network, deterministic), so anyone can
clone the repo and run it with zero API key. Flip to real by setting MOCK=0
in .env (the same switch the Python eval pipeline uses).
"""

import sys
import json
import urllib.parse
from pathlib import Path

import pytest

# Make the project root importable so we can reuse the eval code directly.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from generate import generate_card  # noqa: E402
from judge import judge_card  # noqa: E402

CARD_HTML = (PROJECT_ROOT / "web" / "card.html").as_uri()
PROMPTS_PATH = PROJECT_ROOT / "prompts.json"

# Eval gate: a rendered card must score at least this overall to pass.
EVAL_THRESHOLD = 3.5


def _load_first_prompt():
    data = json.loads(PROMPTS_PATH.read_text())
    return data["prompts"][0]


def _card_url(text: str) -> str:
    return f"{CARD_HTML}?text={urllib.parse.quote(text)}"


def test_card_renders_and_passes_eval(page):
    """A generated card renders in the browser AND passes the LLM-as-judge eval."""
    prompt_obj = _load_first_prompt()

    # 1. Generate the card (mock by default).
    card_text = generate_card(prompt_obj)
    assert card_text and card_text.strip(), "generate_card returned empty text"

    # 2. Render it in a real browser.
    page.goto(_card_url(card_text))
    card = page.locator("#card")

    # 3. E2E assertions: does it RENDER correctly?
    card.wait_for(state="visible")
    assert card.get_attribute("data-state") == "ok", "card rendered in error state"
    rendered = card.inner_text().strip()
    assert rendered, "rendered card text is empty"
    assert rendered == card_text.strip(), "rendered text does not match generated text"
    assert 10 <= len(rendered) <= 600, f"card length out of range: {len(rendered)}"

    # 4. EVAL assertion: is the rendered card GOOD?
    score = judge_card(prompt_obj, rendered)
    assert score.overall() >= EVAL_THRESHOLD, (
        f"card failed eval: overall={score.overall()} "
        f"(< {EVAL_THRESHOLD})\nreasoning: {score.reasoning}"
    )


def test_empty_card_shows_error_state(page):
    """Guard test: an empty card must surface a visible error state, not blank."""
    page.goto(_card_url(""))
    card = page.locator("#card")
    card.wait_for(state="visible")
    assert card.get_attribute("data-state") == "error"
    assert card.inner_text().strip(), "error state should still show a message"
